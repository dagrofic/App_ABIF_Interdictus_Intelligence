
# App ABIF Interdictus Intelligence

Este aplicativo verifica se áreas de um arquivo KML ou KMZ estão sobre zonas de restrição geoespacial no Brasil (ex: terras indígenas, áreas embargadas, unidades de conservação, etc.).

## Como utilizar

### Instalação local

```bash
pip install -r requirements.txt
streamlit run App_ABIF_Interdictus_Intelligence_RESTAURADO_COMERCIAL_V3.py
```

### Hospedagem no Render

1. Crie um repositório no GitHub e envie todos os arquivos deste projeto
2. Acesse [https://render.com](https://render.com)
3. Clique em "New" → "Web Service"
4. Conecte seu GitHub e selecione este repositório
5. Configure:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run App_ABIF_Interdictus_Intelligence_RESTAURADO_COMERCIAL_V3.py`
   - Runtime: `web`

6. Clique em Deploy

O Render fará o build automático e publicará a URL do app

## Licença

Uso privado e restrito ao projeto ABIF/Chronos Intelligence
