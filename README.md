# App ABIF Interdictus Intelligence

O App ABIF Interdictus Intelligence é uma ferramenta para verificação de áreas agrícolas em relação a zonas de plantio restritas, de acordo com camadas geoespaciais oficiais do território brasileiro.

## Funcionalidades

- Upload de arquivos KML/KMZ de delimitação de áreas agrícolas
- Análise automática de intersecções com áreas restritivas
- Identificação de restrições como Unidades de Conservação, Terras Indígenas, Áreas Quilombolas, etc.
- Interface amigável e resultados claros

## Requisitos Técnicos

- Python 3.8 ou superior
- Streamlit 1.32.0 ou superior
- GeoPandas 0.14.1 ou superior
- Acesso à internet para download do arquivo GPKG (aproximadamente 650 MB)
- Espaço em disco de pelo menos 1 GB para armazenamento temporário

## Instalação Local

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o aplicativo:
   ```
   streamlit run app.py
   ```

## Deploy no Render

Consulte o arquivo [GUIA_DEPLOY_RENDER.md](GUIA_DEPLOY_RENDER.md) para instruções detalhadas sobre como hospedar o aplicativo no Render.

## Solução de Problemas

Consulte o arquivo [SOLUCAO_PROBLEMAS.md](SOLUCAO_PROBLEMAS.md) para orientações sobre como resolver problemas comuns.

## Compatibilidade

O aplicativo foi projetado para funcionar em múltiplas plataformas:
- Windows
- macOS
- Linux
- Render (hospedagem na nuvem)

## Notas Importantes

- O aplicativo baixa um arquivo GPKG grande (aproximadamente 650 MB) na primeira execução
- Este download pode levar alguns minutos, dependendo da velocidade da conexão
- O arquivo é armazenado temporariamente e pode ser baixado novamente se necessário
- Arquivos KML/KMZ muito grandes ou complexos podem exigir mais recursos do sistema

## Suporte

Se encontrar problemas que não consegue resolver com a documentação fornecida, entre em contato com o suporte técnico.
