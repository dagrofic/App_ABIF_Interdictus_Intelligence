# App ABIF Interdictus Intelligence

Aplicativo para verificaÃ§Ã£o de Ã¡reas agrÃ­colas em zonas de plantio restritas, de acordo com camadas geoespaciais oficiais do territÃ³rio brasileiro.

## Sobre o Aplicativo

O App ABIF Interdictus Intelligence permite verificar se Ã¡reas definidas em arquivos KML/KMZ se sobrepÃµem a Ã¡reas restritivas como:

- Unidades de ConservaÃ§Ã£o Federal
- Terras IndÃ­genas
- Ãreas de Quilombolas
- Assentamentos
- Ãreas Embargadas
- Cadastro Nacional de Florestas PÃºblicas

## Funcionalidades

- Upload de arquivos KML/KMZ com delimitaÃ§Ã£o de Ã¡reas agrÃ­colas
- Download automÃ¡tico do arquivo GPKG com mapas restritivos (aproximadamente 650 MB)
- AnÃ¡lise de intersecÃ§Ã£o entre a Ã¡rea agrÃ­cola e as camadas restritivas
- ExibiÃ§Ã£o de alertas para Ã¡reas com restriÃ§Ãµes identificadas

## Requisitos TÃ©cnicos

- Python 3.9+
- Streamlit
- GeoPandas
- Fiona
- Shapely
- Requests
- gdown

## InstruÃ§Ãµes de Deploy

Para instruÃ§Ãµes detalhadas sobre como hospedar este aplicativo no Render, consulte o arquivo [GUIA_DEPLOY_RENDER.md](GUIA_DEPLOY_RENDER.md).

## Estrutura do Projeto

- `app.py` - CÃ³digo principal do aplicativo Streamlit
- `requirements.txt` - DependÃªncias necessÃ¡rias para execuÃ§Ã£o
- `GUIA_DEPLOY_RENDER.md` - InstruÃ§Ãµes detalhadas para deploy no Render

## ExecuÃ§Ã£o Local

Para executar o aplicativo localmente:

1. Instale as dependÃªncias:
   ```
   pip install -r requirements.txt
   ```

2. Execute o aplicativo:
   ```
   streamlit run app.py
   ```

## Notas Importantes

- O aplicativo baixa automaticamente um arquivo GPKG de aproximadamente 650 MB
- O primeiro carregamento pode ser lento devido ao download do arquivo
- Arquivos KML/KMZ muito grandes podem causar problemas de memÃ³ria

## Suporte

Em caso de problemas, verifique as soluÃ§Ãµes comuns no guia de deploy ou entre em contato com o suporte tÃ©cnico.
