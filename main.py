
from flask import Flask, render_template, request
import geopandas as gpd
import os
import tempfile
import requests

app = Flask(__name__)

SHAREPOINT_URL = "https://investseguradora.sharepoint.com/:f:/r/sites/File-Server-Ext/Documentos%20Compartilhados/Cotacoes_Liberty_Re/Mapa%20de%20analise%20%C3%A1reas%20de%20plantio?csf=1&web=1&e=lKe7eL"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["kmlfile"]
        if file.filename.endswith(".kml"):
            temp_dir = tempfile.mkdtemp()
            kml_path = os.path.join(temp_dir, file.filename)
            file.save(kml_path)

            # Dummy processing
            result = f"Arquivo recebido: {file.filename} — processamento simulado."

            return render_template("resultado.html", resultado=result)
        else:
            return render_template("index.html", erro="Formato inválido. Envie um arquivo .kml")
    return render_template("index.html")

@app.route("/sharepoint")
def sharepoint():
    return f"Para obter os mapas, acesse: <a href='{SHAREPOINT_URL}' target='_blank'>SharePoint</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
