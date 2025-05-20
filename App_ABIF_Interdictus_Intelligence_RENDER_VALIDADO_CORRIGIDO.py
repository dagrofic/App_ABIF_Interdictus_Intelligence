
import streamlit as st
import geopandas as gpd
import shapely
from shapely.geometry import shape
import zipfile
import tempfile
import os
import gdown
import fiona
from fastkml import kml

st.set_page_config(page_title="App ABIF Interdictus Intelligence")

# Caminho para o GPKG
GPKG_URL = "https://drive.google.com/uc?id=1b-dZoffPF6lv3XsVAjx-1EZUT7AKVQ2o"
GPKG_LOCAL_PATH = "mapas_restritivos_completo.gpkg"

@st.cache_data
def baixar_arquivo_restritivo():
    if not os.path.exists(GPKG_LOCAL_PATH):
        gdown.download(GPKG_URL, GPKG_LOCAL_PATH, quiet=False)

def carregar_kml(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8")
        k = kml.KML()
        k.from_string(content.encode("utf-8"))
        features = list(k.features())
        placemarks = list(features[0].features())
        geometries = [shape(pm.geometry.__geo_interface__) for pm in placemarks]
        return gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None

def nome_padronizado(original):
    original = original.lower()
    if "quilombola" in original:
        return "Áreas de Quilombolas"
    if "indígena" in original or "terra indígena" in original or "tis" in original:
        return "Terra Indígena"
    if "assentamento" in original:
        return "Assentamento"
    if "embargo" in original:
        return "Área Embargada"
    if "unidade" in original and "conservação" in original:
        return "Unidade de Conservação Federal"
    if "cnfp" in original:
        sigla = original.split()[-1].upper()
        return f"Cadastro Nacional de Florestas Públicas ({sigla})"
    return original

def analisar_intersecoes(gdf_kml, gpkg_path):
    resultados = []
    layers = fiona.listlayers(gpkg_path)
    for camada in layers:
        try:
            gdf_layer = gpd.read_file(gpkg_path, layer=camada).to_crs("EPSG:4326")
            if gdf_kml.intersects(gdf_layer.unary_union).any():
                resultados.append(nome_padronizado(camada))
        except Exception as e:
            st.warning(f"Erro ao analisar a camada {camada}: {e}")
    return resultados

# Interface Streamlit
st.title("🛰️ App ABIF Interdictus Intelligence")
st.caption("Verifica se áreas do KML estão em zonas de plantio restritas de acordo com camadas geoespaciais oficiais do território brasileiro.")

baixar_arquivo_restritivo()
st.success("🗺️ Mapa restritivo já disponível localmente")

uploaded_file = st.file_uploader("📁 Upload do Arquivo KML ou KMZ", type=["kml", "kmz"], label_visibility="visible")
if uploaded_file:
    gdf_kml = carregar_kml(uploaded_file)
    if gdf_kml is not None:
        if st.button("🔎 Rodar Análise"):
            resultado = analisar_intersecoes(gdf_kml, GPKG_LOCAL_PATH)
            if resultado:
                st.error("⚠️ ALERTA – Restrição de Plantio Identificada")
                for item in resultado:
                    st.write(f"• {item}")
            else:
                st.success("✅ Nenhuma interseção com áreas restritivas encontrada")
