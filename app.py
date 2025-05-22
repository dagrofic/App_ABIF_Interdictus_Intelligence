import streamlit as st
import geopandas as gpd
import pandas as pd
import fastkml
import gdown
import os

st.set_page_config(layout="wide")

MAPA_URL = "https://drive.google.com/uc?id=1b-dZoffPF6lv3XsVAjx-1EZUT7AKVQ2o"
MAPA_PATH = "/tmp/mapas_restritivos_completo.gpkg"
CRS_PADRAO = "EPSG:4674"

def baixar_mapa():
    if not os.path.exists(MAPA_PATH) or os.path.getsize(MAPA_PATH) < 100_000_000:
        gdown.download(url=MAPA_URL, output=MAPA_PATH, quiet=False, fuzzy=True)

def carregar_geodados():
    if not os.path.exists(MAPA_PATH):
        baixar_mapa()
    gdf = gpd.read_file(MAPA_PATH)
    gdf = gdf.to_crs(CRS_PADRAO)
    return gdf

def ler_kml(uploaded_file):
    kml = uploaded_file.read().decode("utf-8")
    k = fastkml.KML()
    k.from_string(kml.encode("utf-8"))
    polys = []
    for f in k.features():
        for p in f.features():
            geom = p.geometry
            if geom:
                polys.append(geom)
    return polys

def verificar_intersecao(poligonos_usuario, gdf_restritivo):
    inters = []
    for geom in poligonos_usuario:
        gdf_poly = gpd.GeoDataFrame(geometry=[geom], crs=CRS_PADRAO)
        sobreposicoes = gpd.overlay(gdf_poly, gdf_restritivo, how="intersection")
        if not sobreposicoes.empty:
            inters.append(sobreposicoes)
    if inters:
        return pd.concat(inters, ignore_index=True)
    return pd.DataFrame()

def campo_alerta(resultado):
    campos = resultado.columns
    if "NOME_CAMADA" in campos:
        return resultado["NOME_CAMADA"].astype(str)
    if "NOME" in campos:
        return resultado["NOME"].astype(str)
    if "DESCRICAO" in campos:
        return resultado["DESCRICAO"].astype(str)
    if "CAMADA" in campos:
        return resultado["CAMADA"].astype(str)
    return pd.Series(["Camada não identificada"] * len(resultado))

st.title("ABIF Interdictus Intelligence – Verificação de Áreas Restritivas")

st.markdown(
    "Faça upload do seu arquivo KML para identificar interseções com áreas restritivas agrícolas, ambientais, indígenas ou outras camadas oficiais no território nacional."
)

uploaded_file = st.file_uploader(
    "Upload do arquivo KML", type=["kml", "kmz"]
)

if uploaded_file:
    with st.spinner("Processando arquivo e carregando mapas restritivos..."):
        baixar_mapa()
        gdf_restritivo = carregar_geodados()
        poligonos_usuario = ler_kml(uploaded_file)
        resultado = verificar_intersecao(poligonos_usuario, gdf_restritivo)
    if not resultado.empty:
        st.subheader("Áreas Restritivas Intersectadas")
        alerta = campo_alerta(resultado)
        uf = resultado["UF"].astype(str) if "UF" in resultado.columns else "UF não identificada"
        resultado["alerta"] = "ALERTA – " + alerta + " (" + uf + ")"
        st.dataframe(resultado[["alerta", "geometry"]])
        st.success("Foram encontradas interseções restritivas no(s) polígono(s) enviado(s)")
    else:
        st.info("Não foram encontradas interseções restritivas para os polígonos enviados")

st.caption("© Kovr Seguradora – Todos os direitos reservados")
