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

@st.cache_resource
def carregar_camadas():
    baixar_mapa()
    gdf = gpd.read_file(MAPA_PATH, layer=None)
    return gdf

def ler_kml(uploaded_file):
    k = fastkml.KML()
    kml_bytes = uploaded_file.read()
    k.from_string(kml_bytes)
    features = list(k.features())
    placemarks = []
    def parse_features(features):
        for f in features:
            if hasattr(f, 'features'):
                parse_features(list(f.features()))
            else:
                placemarks.append(f)
    parse_features(features)
    geoms = [gpd.GeoSeries.from_wkt([p.geometry.wkt]) for p in placemarks if hasattr(p, 'geometry') and p.geometry]
    gdf = gpd.GeoDataFrame(geometry=pd.concat(geoms, ignore_index=True))
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

st.title("ABIF Interdictus Intelligence – Verificação de Áreas Restritivas")

st.write("Faça upload do seu arquivo KML para identificar interseções com áreas restritivas agrícolas, ambientais, indígenas ou outras camadas oficiais no território nacional.")

uploaded_file = st.file_uploader("Upload do arquivo KML", type=["kml", "kmz"])

if uploaded_file:
    gdf_kml = ler_kml(uploaded_file)
    st.info(f"Arquivo recebido: {uploaded_file.name}")
    gdf_camadas = carregar_camadas()
    # Realiza overlay/interseção
    intersec = gpd.overlay(gdf_kml, gdf_camadas, how='intersection')
    if not intersec.empty:
        # Alerta conforme premissa do usuário
        intersec["alerta"] = (
            "ALERTA – " + intersec["NOME_CAMADA"].astype(str) +
            " (" + intersec["UF"].astype(str) + ")"
        )
        # Converter geometry para WKT apenas para visualização textual
        intersec["wkt"] = intersec.geometry.apply(lambda g: g.wkt if g is not None else None)
        st.dataframe(intersec[["alerta", "wkt"]])
        st.success("Interseções restritivas encontradas e exibidas acima")
    else:
        st.info("Não foram encontradas interseções restritivas para os polígonos enviados")
