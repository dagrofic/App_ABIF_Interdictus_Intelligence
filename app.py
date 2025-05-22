import streamlit as st
import geopandas as gpd
import os
import time
import requests
import tempfile
import fiona
from zipfile import ZipFile
import io
import re

# ConfiguraÃ§Ã£o da pÃ¡gina
st.set_page_config(page_title="ðŸ›°ï¸ App ABIF Interdictus Intelligence", layout="wide")
st.title("ðŸ›°ï¸ App ABIF Interdictus Intelligence")
st.markdown("Verifica se Ã¡reas do KML estÃ£o em zonas de plantio restritas de acordo com camadas geoespaciais oficiais do territÃ³rio brasileiro.")

# ConfiguraÃ§Ãµes de download
GPKG_URL = "https://drive.google.com/uc?id=1b-dZoffPF6lv3XsVAjx-1EZUT7AKVQ2o"
TEMP_DIR = "/tmp"  # DiretÃ³rio temporÃ¡rio no Render
LOCAL_GPKG = os.path.join(TEMP_DIR, "mapas_restritivos_completo.gpkg")

# FunÃ§Ã£o robusta para download do GPKG
@st.cache_resource(show_spinner=False)
def download_gpkg_with_retry(url=GPKG_URL, output_path=LOCAL_GPKG, max_retries=3, chunk_size=1024*1024):
    """
    FunÃ§Ã£o robusta para download do arquivo GPKG com retry e monitoramento
    """
    # Verificar se o diretÃ³rio temporÃ¡rio existe
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Verificar se o arquivo jÃ¡ existe e tem tamanho adequado
    if os.path.exists(output_path) and os.path.getsize(output_path) > 100*1024*1024:
        st.success(f"âœ… Arquivo GPKG jÃ¡ disponÃ­vel ({os.path.getsize(output_path)/1024/1024:.1f} MB)")
        return True
    
    # Remover arquivo existente para garantir download limpo
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception as e:
            st.warning(f"NÃ£o foi possÃ­vel remover arquivo existente: {e}")
    
    # Mostrar progresso
    progress_text = "Baixando arquivo de mapas restritivos (aproximadamente 650 MB)..."
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Tentar download com retry
    for attempt in range(max_retries):
        try:
            status_text.text(f"{progress_text} (Tentativa {attempt+1}/{max_retries})")
            
            # MÃ©todo 1: Usando gdown (especÃ­fico para Google Drive)
            try:
                import gdown
                
                # FunÃ§Ã£o para atualizar progresso durante download
                def hook(t):
                    if t[0] == 'download':
                        progress = min(t[1] / t[2], 1.0) if t[2] > 0 else 0
                        progress_bar.progress(progress)
                        status_text.text(f"{progress_text} ({t[1]/1024/1024:.1f} MB / {t[2]/1024/1024:.1f} MB)")
                
                # Tentar download com gdown
                output = gdown.download(url, output_path, quiet=False, use_cookies=False, progress=True, postprocess=hook)
                
                # Verificar se o download foi bem-sucedido
                if output is None or not os.path.exists(output_path):
                    raise Exception("Arquivo nÃ£o foi baixado corretamente")
                
                # Verificar tamanho do arquivo
                file_size = os.path.getsize(output_path)
                
                if file_size < 100*1024*1024:  # Menos de 100MB indica erro
                    raise Exception(f"Arquivo baixado Ã© muito pequeno ({file_size/1024/1024:.1f} MB)")
                
                progress_bar.progress(1.0)
                status_text.text(f"âœ… Download concluÃ­do! ({file_size/1024/1024:.1f} MB)")
                return True
                
            except Exception as e:
                st.warning(f"Erro no download com gdown: {e}")
                st.info("Tentando mÃ©todo alternativo...")
                
                # MÃ©todo 2: Usando requests com streaming (fallback)
                try:
                    # Obter ID do Google Drive da URL
                    file_id = url.split('=')[1].split('&')[0]
                    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    
                    session = requests.Session()
                    response = session.get(download_url, stream=True)
                    
                    # Verificar se hÃ¡ redirecionamento para pÃ¡gina de confirmaÃ§Ã£o
                    if "NID" in response.cookies:
                        params = {'id': file_id, 'confirm': 't'}
                        response = session.get(download_url, params=params, stream=True)
                    
                    # Obter tamanho total se disponÃ­vel
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # Download em chunks para evitar problemas de memÃ³ria
                    with open(output_path, 'wb') as f:
                        downloaded_size = 0
                        start_time = time.time()
                        
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # Atualizar progresso
                                if total_size > 0:
                                    progress = min(downloaded_size / total_size, 1.0)
                                    progress_bar.progress(progress)
                                
                                # Atualizar status a cada chunk
                                elapsed = time.time() - start_time
                                speed = downloaded_size / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                                status_text.text(f"{progress_text} ({downloaded_size/1024/1024:.1f} MB, {speed:.1f} MB/s)")
                    
                    # Verificar tamanho do arquivo
                    file_size = os.path.getsize(output_path)
                    
                    if file_size < 100*1024*1024:  # Menos de 100MB indica erro
                        raise Exception(f"Arquivo baixado Ã© muito pequeno ({file_size/1024/1024:.1f} MB)")
                    
                    progress_bar.progress(1.0)
                    status_text.text(f"âœ… Download concluÃ­do! ({file_size/1024/1024:.1f} MB)")
                    return True
                    
                except Exception as e:
                    st.error(f"Erro no download com requests: {e}")
                    raise
        
        except Exception as e:
            st.error(f"Falha na tentativa {attempt+1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # Backoff linear
                status_text.text(f"Aguardando {wait_time} segundos antes da prÃ³xima tentativa...")
                time.sleep(wait_time)
            else:
                st.error("âŒ Todas as tentativas de download falharam")
                return False
    
    return False

def traduzir_nome(nome_camada):
    """
    Traduz o nome tÃ©cnico da camada para um nome amigÃ¡vel
    """
    nome = nome_camada.lower().replace("-", "_").replace("__", "_").strip()

    # Identificar UF se houver
    uf_match = re.search(r"_([a-z]{2})$", nome)
    uf = uf_match.group(1).upper() if uf_match else ""

    if "embargos" in nome and "icmbio" in nome:
        return "Ãrea Embargada (ICMBio)"
    if "assentamento" in nome:
        return "Assentamento"
    if "quilombo" in nome:
        return "Ãreas de Quilombolas"
    if any(ti in nome for ti in ["terra_indigena", "ti_", "tis", "indigena"]):
        return "Terra IndÃ­gena"
    if "uc" in nome and "federal" in nome:
        return "Unidade de ConservaÃ§Ã£o Federal"
    if "uc_federal_limite" in nome or "limite" in nome:
        return "Local no Limite de Unidade de ConservaÃ§Ã£o Federal"
    if "cnfp" in nome:
        return f"Cadastro Nacional de Florestas PÃºblicas ({uf})" if uf else "Cadastro Nacional de Florestas PÃºblicas"

    return nome_camada.replace("_", " ").title()

def carregar_kml_kmz(uploaded_file):
    """
    Carrega arquivo KML ou KMZ e retorna GeoDataFrame
    """
    try:
        with st.spinner("Processando arquivo..."):
            if uploaded_file.name.endswith(".kmz"):
                kmz = ZipFile(uploaded_file)
                kml_filename = [f for f in kmz.namelist() if f.endswith(".kml")][0]
                kml_content = kmz.read(kml_filename)
                gdf = gpd.read_file(io.BytesIO(kml_content), driver="KML")
            else:
                gdf = gpd.read_file(uploaded_file, driver="KML")
            
            # Garantir projeÃ§Ã£o correta e geometrias vÃ¡lidas
            gdf = gdf.to_crs("EPSG:4326")
            gdf = gdf[gdf.is_valid]
            
            return gdf
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

def analisar_intersecao(gdf_kml):
    """
    Analisa intersecÃ§Ãµes entre o KML e as camadas do GPKG
    """
    intersecoes = []
    
    try:
        # Listar camadas disponÃ­veis no GPKG
        layers = fiona.listlayers(LOCAL_GPKG)
        
        # Barra de progresso para anÃ¡lise
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
                
                # Filtrar geometrias vÃ¡lidas e do tipo polÃ­gono
                gdf_layer = gdf_layer[gdf_layer.is_valid]
                gdf_layer = gdf_layer[gdf_layer.geometry.type.isin(["Polygon", "MultiPolygon"])]
                
                # Filtrar geometrias vÃ¡lidas do KML
                gdf_kml_clean = gdf_kml[gdf_kml.geometry.type.isin(["Polygon", "MultiPolygon"])]

                # Pular se algum dos GeoDataFrames estiver vazio
                if gdf_kml_clean.empty or gdf_layer.empty:
                    continue

                # Verificar intersecÃ§Ã£o
                joined = gpd.sjoin(gdf_kml_clean, gdf_layer, how="inner", predicate="intersects")
                if not joined.empty:
                    intersecoes.append(traduzir_nome(layer))
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
    # Verificar espaÃ§o em disco
    try:
        disk_space = os.statvfs(TEMP_DIR).f_bavail * os.statvfs(TEMP_DIR).f_frsize / (1024 * 1024 * 1024)
        if disk_space < 1.0:
            st.warning(f"âš ï¸ Pouco espaÃ§o em disco disponÃ­vel: {disk_space:.2f} GB")
    except:
        pass
    
    # Iniciar download do GPKG se necessÃ¡rio
    download_success = download_gpkg_with_retry()

# Se o download foi bem-sucedido, mostrar interface de upload
if download_success:
    st.markdown("### ðŸ“ Upload do Arquivo KML ou KMZ")
    uploaded_file = st.file_uploader("Envie o arquivo de delimitaÃ§Ã£o da Ã¡rea agrÃ­cola", type=["kml", "kmz"])

    if uploaded_file:
        # Carregar e processar o arquivo KML/KMZ
        gdf_area = carregar_kml_kmz(uploaded_file)
        
        if gdf_area is not None:
            # Analisar intersecÃ§Ãµes
            with st.spinner("Analisando intersecÃ§Ãµes com Ã¡reas restritivas..."):
                intersecoes = analisar_intersecao(gdf_area)
            
            # Mostrar resultados
            if intersecoes:
                st.subheader("âš ï¸ ALERTA RESTRIÃ‡ÃƒO LOCAL DE PLANTIO IDENTIFICADA")
                st.markdown("**O KML fornecido intersecta as seguintes camadas restritivas:**")
                for item in sorted(set(intersecoes)):
                    st.markdown(f"- {item}")
            else:
                st.success("âœ… Nenhuma interseÃ§Ã£o com Ã¡reas restritivas foi identificada.")
        else:
            st.error("âŒ Erro ao processar o arquivo KML/KMZ.")
    else:
        st.info("â„¹ï¸ Aguardando envio de arquivo .kml ou .kmz para iniciar verificaÃ§Ã£o.")
else:
    st.error("âŒ NÃ£o foi possÃ­vel baixar o arquivo de mapas restritivos. Por favor, tente novamente mais tarde.")
    st.info("â„¹ï¸ Se o problema persistir, entre em contato com o suporte tÃ©cnico.")
