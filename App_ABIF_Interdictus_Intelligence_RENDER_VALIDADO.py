
import streamlit as st
import geopandas as gpd
import os
import tempfile
import fiona
import gdown
from zipfile import ZipFile
import io
import re
from fastkml import kml
from shapely.geometry import shape

st.set_page_config(page_title="🛰️ App ABIF Interdictus Intelligence", layout="wide")
st.title("🛰️ App ABIF Interdictus Intelligence")
st.markdown("🛰️ Aplicativo iniciado com sucesso. Aguardando upload de KML/KMZ...")
st.markdown("Verifica se áreas do KML estão em zonas de plantio restritas de acordo com camadas geoespaciais oficiais do território brasileiro.")

GPKG_URL = "https://drive.google.com/uc?id=1b-dZoffPF6lv3XsVAjx-1EZUT7AKVQ2o"
LOCAL_GPKG = "mapas_restritivos_completo.gpkg"

def download_gpkg():
    if not os.path.exists(LOCAL_GPKG):
        with st.spinner("Baixando o arquivo de mapas restritivos (GPKG)..."):
            gdown.download(GPKG_URL, LOCAL_GPKG, quiet=False)

def traduzir_nome(nome_camada):
    nome = nome_camada.lower().replace("-", "_").replace("__", "_").strip()
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
    try:
        if uploaded_file.name.endswith(".kmz"):
            kmz = ZipFile(uploaded_file)
            kml_filename = [f for f in kmz.namelist() if f.endswith(".kml")][0]
            kml_content = kmz.read(kml_filename).decode("utf-8")
        else:
            kml_content = uploaded_file.read().decode("utf-8")

        k = kml.KML()
        k.from_string(kml_content.encode("utf-8"))

        placemarks = []
        def extract_features(feature):
            if hasattr(feature, "features"):
                for f in feature.features():
                    extract_features(f)
            else:
                if hasattr(feature, "geometry"):
                    placemarks.append({"geometry": feature.geometry})

        for f in k.features():
            extract_features(f)

        geometries = [shape(p["geometry"]) for p in placemarks]
        gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
        gdf = gdf[gdf.is_valid]
        return gdf
    except Exception as e:
        st.error(f"Erro ao carregar o KML/KMZ: {e}")
        return None

def analisar_intersecao(gdf_kml):
    intersecoes = []
    try:
        layers = fiona.listlayers(LOCAL_GPKG)
    except Exception as e:
        st.error(f"Erro ao listar camadas do GPKG: {e}")
        return []

    for layer in layers:
        try:
            gdf_layer = gpd.read_file(LOCAL_GPKG, layer=layer).to_crs("EPSG:4326")
            gdf_layer = gdf_layer[gdf_layer.is_valid]
            gdf_layer = gdf_layer[gdf_layer.geometry.type.isin(["Polygon", "MultiPolygon"])]
            gdf_kml_clean = gdf_kml[gdf_kml.geometry.type.isin(["Polygon", "MultiPolygon"])]

            if gdf_kml_clean.empty or gdf_layer.empty:
                continue

            joined = gpd.sjoin(gdf_kml_clean, gdf_layer, how="inner", predicate="intersects")
            if not joined.empty:
                intersecoes.append(traduzir_nome(layer))
        except Exception as e:
            st.warning(f"Erro ao processar camada {layer}: {e}")
    return intersecoes

download_gpkg()

st.markdown("### 📁 Upload do Arquivo KML ou KMZ")
uploaded_file = st.file_uploader("Envie o arquivo de delimitação da área agrícola", type=["kml", "kmz"])

if uploaded_file:
    gdf_area = carregar_kml_kmz(uploaded_file)
    if gdf_area is not None:
        intersecoes = analisar_intersecao(gdf_area)
        if intersecoes:
            st.subheader("⚠️ ALERTA RESTRIÇÃO LOCAL DE PLANTIO IDENTIFICADA")
            st.markdown("**O KML fornecido intersecta as seguintes camadas restritivas:**")
            for item in sorted(set(intersecoes)):
                st.markdown(f"- {item}")
        else:
            st.success("✅ Nenhuma interseção com áreas restritivas foi identificada.")
    else:
        st.error("Erro ao processar o arquivo KML/KMZ.")
else:
    st.info("Aguardando envio de arquivo .kml ou .kmz para iniciar verificação.")
