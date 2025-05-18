
import os
import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import Polygon
import io
from zipfile import ZipFile

def carregar_kml_kmz(uploaded_file):
    try:
        if uploaded_file.name.endswith(".kmz"):
            kmz = ZipFile(uploaded_file)
            kml_filename = [f for f in kmz.namelist() if f.endswith(".kml")][0]
            kml_content = kmz.read(kml_filename)
            gdf = gpd.read_file(io.BytesIO(kml_content), driver="KML")
        else:
            gdf = gpd.read_file(uploaded_file, driver="KML")
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        else:
            gdf = gdf.to_crs("EPSG:4326")
        return gdf
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

def listar_shps_recursivamente(pasta_base):
    arquivos_shp = []
    for raiz, _, arquivos in os.walk(pasta_base):
        for arq in arquivos:
            if arq.endswith(".shp"):
                arquivos_shp.append(os.path.join(raiz, arq))
    return arquivos_shp

def nome_comercial(path):
    nome = os.path.splitext(os.path.basename(path))[0].lower()
    nome = nome.replace("_", " ").replace("-", " ")

    if "icmbio" in nome:
        return "Embargos Áreas Embargadas ICMBio"
    if "assentamento brasil" in nome:
        return "Assentamentos Rurais"
    if "quilombolas" in nome:
        return "Áreas de Quilombolas"
    if "ucs" in nome or "unidades de conservação federais" in nome:
        return "Unidades de Conservação Federais"
    if "terras indígenas" in nome or "tis" in nome:
        return "Terras Indígenas"
    if "cnfp" in nome or "cadastro nacional de florestas públicas" in nome:
        partes = nome.split()
        uf = partes[-1].upper() if len(partes) > 1 else ""
        return f"Cadastro Nacional de Florestas Públicas ({uf})"

    return nome.title()

def verificar_intersecoes(gdf_input, pasta_shps):
    if gdf_input is None or gdf_input.empty:
        return pd.DataFrame(columns=["Área Restrita", "Status"])

    geometria_base = gdf_input.geometry.unary_union
    arquivos_shp = listar_shps_recursivamente(pasta_shps)
    if not arquivos_shp:
        st.warning("Nenhum arquivo .shp encontrado nas subpastas.")

    resultados_normais = []
    resultados_cnfp = []

    for caminho in arquivos_shp:
        nome_restricao = nome_comercial(caminho)
        try:
            gdf_restricao = gpd.read_file(caminho, encoding="latin1")
            gdf_restricao = gdf_restricao.to_crs("EPSG:4326")
            intersecao = gdf_restricao[gdf_restricao.intersects(geometria_base)]
            status = "ALERTA RESTRIÇÃO LOCAL DE PLANTIO ❗" if not intersecao.empty else "CERTO ✅"
        except Exception as e:
            status = f"Erro: {str(e)}"

        if "Cadastro Nacional de Florestas Públicas" in nome_restricao:
            resultados_cnfp.append((nome_restricao, status))
        else:
            resultados_normais.append((nome_restricao, status))

    resultado_final = resultados_normais + sorted(resultados_cnfp)
    return pd.DataFrame(resultado_final, columns=["Área Restrita", "Status"])

# Interface Streamlit
st.set_page_config(page_title="App ABIF Interdictus Intelligence", layout="wide")
st.title("App ABIF Interdictus Intelligence")

uploaded_file = st.file_uploader("📁 Envie um arquivo .kml ou .kmz da área agrícola", type=["kml", "kmz"])
pasta_mapas_restritos = "mapas_restritos"

if uploaded_file:
    gdf_area = carregar_kml_kmz(uploaded_file)
    if gdf_area is not None:
        st.success("Arquivo carregado com sucesso")

        if st.button("▶️ Rodar Análise"):
            if not os.path.exists(pasta_mapas_restritos):
                st.error(f"Pasta de mapas restritos '{pasta_mapas_restritos}' não encontrada. Crie esta pasta e adicione os arquivos SHP.")
            else:
                df_resultado = verificar_intersecoes(gdf_area, pasta_mapas_restritos)
                st.subheader("Resultado da Verificação")
                st.dataframe(df_resultado, use_container_width=True)
    else:
        st.error("Erro ao processar o arquivo")
else:
    st.info("Aguardando envio de arquivo .kml ou .kmz para iniciar verificação")
