import streamlit as st
import geopandas as gpd
import os
import time
import tempfile
import fiona
from zipfile import ZipFile
import io
import re
import platform
import sys
import subprocess
import shutil
import requests

# Configuração da página
st.set_page_config(page_title="🛰️ App ABIF Interdictus Intelligence", layout="wide")
st.title("🛰️ App ABIF Interdictus Intelligence")
st.markdown("Verifica se áreas do KML estão em zonas de plantio restritas de acordo com camadas geoespaciais oficiais do território brasileiro.")

# Configurações de download
SHAREPOINT_URL = "https://investseguradora.sharepoint.com/:u:/r/sites/File-Server-Ext/Documentos%20Compartilhados/Cotacoes_Liberty_Re/Mapa%20de%20analise%20%C3%A1reas%20de%20plantio/mapas_restritivos_completo.gpkg?csf=1&web=1&e=jbgLrx"

# Usar tempfile para obter diretório temporário multiplataforma
TEMP_DIR = tempfile.gettempdir()
LOCAL_GPKG = os.path.join(TEMP_DIR, "mapas_restritivos_completo.gpkg")

# Informações do sistema para diagnóstico
system_info = f"Sistema: {platform.system()} {platform.release()}, Python: {platform.python_version()}"
st.sidebar.info(f"Informações do sistema:\n{system_info}")
st.sidebar.info(f"Diretório temporário: {TEMP_DIR}")

# Função robusta para download do GPKG do SharePoint
@st.cache_resource(show_spinner=False)
def download_gpkg_from_sharepoint(url=SHAREPOINT_URL, output_path=LOCAL_GPKG, max_retries=3):
    """
    Função robusta para download do arquivo GPKG do SharePoint
    """
    # Verificar se o diretório temporário existe e tem permissões
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        # Testar permissões de escrita
        test_file = os.path.join(TEMP_DIR, "test_write.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        st.error(f"❌ Erro de permissão no diretório temporário: {e}")
        st.info(f"Tentando usar diretório alternativo...")
        
        # Tentar diretório alternativo
        try:
            alt_temp = os.path.join(os.path.expanduser("~"), ".temp_app_abif")
            os.makedirs(alt_temp, exist_ok=True)
            # Usar variáveis locais em vez de globais
            temp_dir = alt_temp
            output_path = os.path.join(temp_dir, "mapas_restritivos_completo.gpkg")
            st.sidebar.success(f"Usando diretório alternativo: {temp_dir}")
        except Exception as e2:
            st.error(f"❌ Não foi possível criar diretório temporário alternativo: {e2}")
            return False
    
    # Verificar se o arquivo já existe e tem tamanho adequado
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100*1024*1024:
        st.success(f"✅ Arquivo GPKG já disponível ({os.path.getsize(output_path)/1024/1024:.1f} MB)")
        return True
    
    # Remover arquivo existente para garantir download limpo
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception as e:
            st.warning(f"Não foi possível remover arquivo existente: {e}")
    
    # Mostrar progresso
    progress_text = "Baixando arquivo de mapas restritivos (aproximadamente 650 MB)..."
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Tentar download com retry
    for attempt in range(max_retries):
        try:
            status_text.text(f"{progress_text} (Tentativa {attempt+1}/{max_retries})")
            
            # Método 1: Download direto do SharePoint com Python requests
            try:
                status_text.text(f"{progress_text} Iniciando download do SharePoint...")
                
                # Obter o link direto de download do SharePoint
                session = requests.Session()
                
                # Primeiro, obter a página que contém o link direto
                response = session.get(url, allow_redirects=True)
                
                # Verificar se a resposta foi bem-sucedida
                if response.status_code != 200:
                    raise Exception(f"Falha ao acessar o SharePoint: {response.status_code}")
                
                # Extrair o link direto de download da resposta
                # O SharePoint geralmente redireciona para o arquivo real
                direct_url = response.url
                
                # Se ainda estiver na página de visualização, tentar extrair o link direto
                if "web=1" in direct_url:
                    # Tentar extrair o link direto da página
                    # Isso pode variar dependendo da configuração do SharePoint
                    # Tentar algumas abordagens comuns
                    
                    # Abordagem 1: Substituir parâmetros na URL
                    direct_url = direct_url.replace("web=1", "download=1")
                    
                    # Abordagem 2: Se a primeira abordagem falhar, tentar outra URL
                    if "download=1" not in direct_url:
                        # Construir URL alternativa baseada no padrão do SharePoint
                        base_url = direct_url.split("?")[0]
                        direct_url = f"{base_url}?download=1"
                
                status_text.text(f"{progress_text} Obteve link direto, iniciando download...")
                
                # Baixar o arquivo usando o link direto
                response = session.get(direct_url, stream=True)
                
                # Verificar se a resposta foi bem-sucedida
                if response.status_code != 200:
                    raise Exception(f"Falha ao baixar o arquivo: {response.status_code}")
                
                # Obter o tamanho total do arquivo, se disponível
                total_size = int(response.headers.get('content-length', 0))
                
                # Baixar o arquivo em chunks para evitar problemas de memória
                downloaded_size = 0
                start_time = time.time()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Atualizar progresso
                            if total_size > 0:
                                progress = min(downloaded_size / total_size, 0.99)
                                progress_bar.progress(progress)
                            else:
                                # Se o tamanho total não estiver disponível, usar uma estimativa
                                progress = min(downloaded_size / (700 * 1024 * 1024), 0.99)
                                progress_bar.progress(progress)
                            
                            # Atualizar status
                            elapsed = time.time() - start_time
                            speed = downloaded_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                            status_text.text(f"{progress_text} ({downloaded_size/1024/1024:.1f} MB, {speed:.1f} MB/s)")
                
                # Verificar tamanho do arquivo baixado
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    
                    if file_size < 100*1024*1024:  # Menos de 100MB indica erro
                        raise Exception(f"Arquivo baixado é muito pequeno ({file_size/1024/1024:.1f} MB)")
                    
                    progress_bar.progress(1.0)
                    status_text.text(f"✅ Download concluído! ({file_size/1024/1024:.1f} MB)")
                    return True
                else:
                    raise Exception("Arquivo não foi baixado")
                
            except Exception as e:
                st.warning(f"Erro no download direto do SharePoint: {e}")
                
                # Método 2: Usando curl (alternativa)
                try:
                    status_text.text(f"{progress_text} Tentando com curl...")
                    
                    # Criar script temporário para download com curl
                    script_path = os.path.join(TEMP_DIR, "download_script.sh")
                    with open(script_path, "w") as f:
                        f.write(f"""#!/bin/bash
# Script para download de arquivo do SharePoint usando curl
URL="{url}"
OUTPUT="{output_path}"

# Baixar o arquivo
curl -L -o "$OUTPUT" "$URL"
""")
                    
                    # Tornar o script executável
                    os.chmod(script_path, 0o755)
                    
                    # Executar o script
                    process = subprocess.Popen(
                        script_path,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    # Monitorar progresso
                    start_time = time.time()
                    while process.poll() is None:
                        time.sleep(1)
                        if os.path.exists(output_path):
                            file_size = os.path.getsize(output_path)
                            elapsed = time.time() - start_time
                            speed = file_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                            progress_bar.progress(min(file_size / (700 * 1024 * 1024), 0.99))
                            status_text.text(f"{progress_text} ({file_size/1024/1024:.1f} MB, {speed:.1f} MB/s)")
                    
                    # Verificar resultado
                    stdout, stderr = process.communicate()
                    if process.returncode != 0:
                        st.warning(f"Erro no curl: {stderr}")
                        raise Exception(f"curl falhou com código {process.returncode}")
                    
                    # Limpar script temporário
                    try:
                        os.remove(script_path)
                    except:
                        pass
                    
                    # Verificar tamanho do arquivo
                    if os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        
                        if file_size < 100*1024*1024:  # Menos de 100MB indica erro
                            raise Exception(f"Arquivo baixado é muito pequeno ({file_size/1024/1024:.1f} MB)")
                        
                        progress_bar.progress(1.0)
                        status_text.text(f"✅ Download concluído! ({file_size/1024/1024:.1f} MB)")
                        return True
                    else:
                        raise Exception("Arquivo não foi baixado")
                    
                except Exception as e:
                    st.error(f"Erro no download com curl: {e}")
                    
                    # Método 3: Usando wget (última alternativa)
                    try:
                        status_text.text(f"{progress_text} Tentando com wget...")
                        
                        # Criar script temporário para download com wget
                        script_path = os.path.join(TEMP_DIR, "download_script.sh")
                        with open(script_path, "w") as f:
                            f.write(f"""#!/bin/bash
# Script para download de arquivo do SharePoint usando wget
URL="{url}"
OUTPUT="{output_path}"

# Baixar o arquivo
wget -O "$OUTPUT" "$URL"
""")
                        
                        # Tornar o script executável
                        os.chmod(script_path, 0o755)
                        
                        # Executar o script
                        process = subprocess.Popen(
                            script_path,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        
                        # Monitorar progresso
                        start_time = time.time()
                        while process.poll() is None:
                            time.sleep(1)
                            if os.path.exists(output_path):
                                file_size = os.path.getsize(output_path)
                                elapsed = time.time() - start_time
                                speed = file_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                                progress_bar.progress(min(file_size / (700 * 1024 * 1024), 0.99))
                                status_text.text(f"{progress_text} ({file_size/1024/1024:.1f} MB, {speed:.1f} MB/s)")
                        
                        # Verificar resultado
                        stdout, stderr = process.communicate()
                        if process.returncode != 0:
                            st.warning(f"Erro no wget: {stderr}")
                            raise Exception(f"wget falhou com código {process.returncode}")
                        
                        # Limpar script temporário
                        try:
                            os.remove(script_path)
                        except:
                            pass
                        
                        # Verificar tamanho do arquivo
                        if os.path.exists(output_path):
                            file_size = os.path.getsize(output_path)
                            
                            if file_size < 100*1024*1024:  # Menos de 100MB indica erro
                                raise Exception(f"Arquivo baixado é muito pequeno ({file_size/1024/1024:.1f} MB)")
                            
                            progress_bar.progress(1.0)
                            status_text.text(f"✅ Download concluído! ({file_size/1024/1024:.1f} MB)")
                            return True
                        else:
                            raise Exception("Arquivo não foi baixado")
                        
                    except Exception as e:
                        st.error(f"Erro no download com wget: {e}")
                        raise
        
        except Exception as e:
            st.error(f"Falha na tentativa {attempt+1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # Backoff linear
                status_text.text(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                time.sleep(wait_time)
            else:
                st.error("❌ Todas as tentativas de download falharam")
                return False
    
    return False

def traduzir_nome(nome_camada):
    """
    Traduz o nome técnico da camada para um nome amigável
    """
    nome = nome_camada.lower().replace("-", "_").replace("__", "_").strip()

    # Identificar UF se houver
    uf_match = re.search(r"_([a-z]{2})$", nome)
    uf = uf_match.group(1).upper() if uf_match else ""

    if "embargos" in nome and "icmbio" in nome:
        return "Área Embargada (ICMBio)"
    if "assentamento" in nome:
        return "Assentamento"
    if "quilombo" in nome:
        return "Áreas de Quilombolas"
    if any(ti in nome for ti in ["terra_indigena", "ti_", "tis", "indigena"]):
        return "Terra Indígena"
    if "uc" in nome and "federal" in nome:
        return "Unidade de Conservação Federal"
    if "uc_federal_limite" in nome or "limite" in nome:
        return "Local no Limite de Unidade de Conservação Federal"
    if "cnfp" in nome:
        return f"Cadastro Nacional de Florestas Públicas ({uf})" if uf else "Cadastro Nacional de Florestas Públicas"

    return nome_camada.replace("_", " ").title()

def carregar_kml_kmz(uploaded_file):
    """
    Carrega arquivo KML ou KMZ e retorna GeoDataFrame
    """
    try:
        with st.spinner("Processando arquivo..."):
            # Salvar o arquivo temporariamente para evitar problemas de memória
            temp_file = os.path.join(TEMP_DIR, uploaded_file.name)
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if uploaded_file.name.endswith(".kmz"):
                kmz = ZipFile(temp_file)
                kml_filename = [f for f in kmz.namelist() if f.endswith(".kml")][0]
                kml_content = kmz.read(kml_filename)
                gdf = gpd.read_file(io.BytesIO(kml_content), driver="KML")
            else:
                gdf = gpd.read_file(temp_file, driver="KML")
            
            # Limpar arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
            
            # Garantir projeção correta e geometrias válidas
            gdf = gdf.to_crs("EPSG:4326")
            gdf = gdf[gdf.is_valid]
            
            return gdf
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

def analisar_intersecao(gdf_kml):
    """
    Analisa intersecções entre o KML e as camadas do GPKG
    """
    intersecoes = []
    
    try:
        # Listar camadas disponíveis no GPKG
        layers = fiona.listlayers(LOCAL_GPKG)
        
        # Barra de progresso para análise
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, layer in enumerate(layers):
            try:
                # Atualizar progresso
                progress = (i + 1) / len(layers)
                progress_bar.progress(progress)
                status_text.text(f"Analisando camada {i+1}/{len(layers)}: {traduzir_nome(layer)}")
                
                # Carregar camada do GPKG
                gdf_layer = gpd.read_file(LOCAL_GPKG, layer=layer).to_crs("EPSG:4326")
                
                # Filtrar geometrias válidas e do tipo polígono
                gdf_layer = gdf_layer[gdf_layer.is_valid]
                gdf_layer = gdf_layer[gdf_layer.geometry.type.isin(["Polygon", "MultiPolygon"])]
                
                # Filtrar geometrias válidas do KML
                gdf_kml_clean = gdf_kml[gdf_kml.geometry.type.isin(["Polygon", "MultiPolygon"])]

                # Pular se algum dos GeoDataFrames estiver vazio
                if gdf_kml_clean.empty or gdf_layer.empty:
                    continue

                # Verificar intersecção
                joined = gpd.sjoin(gdf_kml_clean, gdf_layer, how="inner", predicate="intersects")
                if not joined.empty:
                    intersecoes.append(traduzir_nome(layer))
                
                # Liberar memória
                del gdf_layer
                if 'joined' in locals():
                    del joined
            except Exception as e:
                st.warning(f"Erro ao processar camada {layer}: {e}")
        
        # Limpar barra de progresso e status
        progress_bar.empty()
        status_text.empty()
        
        return intersecoes
    except Exception as e:
        st.error(f"Erro ao listar camadas do GPKG: {e}")
        return []

# Interface principal
with st.spinner("Verificando disponibilidade do arquivo de mapas..."):
    # Verificar espaço em disco
    try:
        if platform.system() == "Windows":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(TEMP_DIR), None, None, ctypes.pointer(free_bytes))
            disk_space = free_bytes.value / (1024 * 1024 * 1024)
        else:
            disk_space = os.statvfs(TEMP_DIR).f_bavail * os.statvfs(TEMP_DIR).f_frsize / (1024 * 1024 * 1024)
        
        if disk_space < 1.0:
            st.warning(f"⚠️ Pouco espaço em disco disponível: {disk_space:.2f} GB")
    except Exception as e:
        st.warning(f"Não foi possível verificar espaço em disco: {e}")
    
    # Iniciar download do GPKG se necessário
    download_success = download_gpkg_from_sharepoint()

# Se o download foi bem-sucedido, mostrar interface de upload
if download_success:
    st.markdown("### 📁 Upload do Arquivo KML ou KMZ")
    uploaded_file = st.file_uploader("Envie o arquivo de delimitação da área agrícola", type=["kml", "kmz"])

    if uploaded_file:
        # Carregar e processar o arquivo KML/KMZ
        gdf_area = carregar_kml_kmz(uploaded_file)
        
        if gdf_area is not None:
            # Analisar intersecções
            with st.spinner("Analisando intersecções com áreas restritivas..."):
                intersecoes = analisar_intersecao(gdf_area)
            
            # Mostrar resultados
            if intersecoes:
                st.subheader("⚠️ ALERTA RESTRIÇÃO LOCAL DE PLANTIO IDENTIFICADA")
                st.markdown("**O KML fornecido intersecta as seguintes camadas restritivas:**")
                for item in sorted(set(intersecoes)):
                    st.markdown(f"- {item}")
            else:
                st.success("✅ Nenhuma interseção com áreas restritivas foi identificada.")
        else:
            st.error("❌ Erro ao processar o arquivo KML/KMZ.")
    else:
        st.info("ℹ️ Aguardando envio de arquivo .kml ou .kmz para iniciar verificação.")
else:
    st.error("❌ Não foi possível baixar o arquivo de mapas restritivos. Por favor, tente novamente mais tarde.")
    st.info("ℹ️ Se o problema persistir, entre em contato com o suporte técnico.")
