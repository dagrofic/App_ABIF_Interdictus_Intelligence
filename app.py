import streamlit as st
import geopandas as gpd
import pandas as pd
import fastkml
import gdown
import os

st.set_page_config(layout="wide")

MAPA_URL = "https://drive.google.com/uc?id=1b-dZoffPF6lv3XsVAjx-1EZUT7AKVQ2o"
MAPA_PATH = "/tmp/mapas_restritivos_completo.gpkg"

def baixar_mapa():
    if not os.path.exists(MAPA_PATH) or os.path.getsize(MAPA_PATH) < 100_000_000:
        gdown.download(MAPA_URL, MAPA_PATH, quiet=False)

@st.cache_data(show_spinner=False)
def carregar_areas_restritivas():
    layers = gpd.io.file.fiona.listlayers(MAPA_PATH)
    dfs = []
    for layer in layers:
        df = gpd.read_file(MAPA_PATH, layer=layer)
        if "NOME_CAMADA" not in df.columns:
            df["NOME_CAMADA"] = layer
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def analisar_kml(uploaded_file, areas_restritivas):
    from fastkml import kml
    k = kml.KML()
    k.from_string(uploaded_file.read())
    features = list(k.features())
    subfeatures = list(features[0].features())
    geoms = []
    for f in subfeatures:
        for g in f.geometry.geoms if hasattr(f.geometry, 'geoms') else [f.geometry]:
            geoms.append(g)
    gdf = gpd.GeoDataFrame(geometry=[gpd.GeoSeries.from_wkt(g.wkt)[0] for g in geoms], crs=areas_restritivas.crs)
    intersec = gpd.overlay(gdf, areas_restritivas, how="intersection")
    if "NOME_CAMADA" not in intersec.columns:
        intersec["NOME_CAMADA"] = "Sem identificação"
    return intersec

baixar_mapa()
areas_restritivas = carregar_areas_restritivas()

st.title("ABIF Interdictus Intelligence – Verificação de Áreas Restritivas")
st.write("Faça upload do seu arquivo KML para identificar interseções com áreas restritivas agrícolas, ambientais, indígenas ou outras camadas oficiais no território nacional.")

uploaded_file = st.file_uploader("Upload do arquivo KML", type=["kml", "kmz"])
if uploaded_file:
    st.info(f"Arquivo recebido: {uploaded_file.name}")
    try:
        intersec = analisar_kml(uploaded_file, areas_restritivas)
        if not intersec.empty:
            intersec["alerta"] = "ALERTA – " + intersec["NOME_CAMADA"].astype(str)
            st.dataframe(intersec[["alerta", "geometry"]])
        else:
            st.success("Não foram encontradas interseções restritivas para os polígonos enviados")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
