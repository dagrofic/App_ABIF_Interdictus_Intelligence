# Guia de Deploy do App ABIF Interdictus Intelligence no Render

Este guia apresenta o passo a passo para hospedar o App ABIF Interdictus Intelligence no Render, uma plataforma de hospedagem gratuita que suporta aplicativos Streamlit.

## Pré-requisitos

- Uma conta no [GitHub](https://github.com/) (gratuita)
- Uma conta no [Render](https://render.com/) (gratuita)

## Parte 1: Preparando o Repositório no GitHub

1. **Criar um novo repositório no GitHub**

   - Acesse [GitHub](https://github.com/) e faça login
   - Clique no botão "+" no canto superior direito e selecione "New repository"
   - Nome do repositório: `app-abif-interdictus`
   - Descrição (opcional): `App ABIF Interdictus Intelligence para análise de áreas restritas`
   - Escolha "Public" (repositório público)
   - Marque a opção "Add a README file"
   - Clique em "Create repository"

2. **Fazer upload dos arquivos para o GitHub**

   - No seu novo repositório, clique no botão "Add file" e selecione "Upload files"
   - Arraste ou selecione os arquivos `app.py` e `requirements.txt` do seu computador
   - Adicione uma mensagem de commit: "Upload inicial dos arquivos do aplicativo"
   - Clique em "Commit changes"

## Parte 2: Deploy no Render

1. **Criar uma nova conta no Render (se ainda não tiver)**

   - Acesse [Render](https://render.com/)
   - Clique em "Sign Up" e crie uma conta (pode usar sua conta GitHub para agilizar)

2. **Criar um novo Web Service**

   - No dashboard do Render, clique em "New +" e selecione "Web Service"
   - Conecte sua conta GitHub se ainda não estiver conectada
   - Selecione o repositório `app-abif-interdictus` que você acabou de criar
   - Clique em "Connect"

3. **Configurar o Web Service**

   - **Nome**: `app-abif-interdictus` (ou outro nome de sua preferência)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Plano**: `Free`

4. **Configurações Avançadas (importante!)**

   - Clique em "Advanced" para expandir as opções avançadas
   - Em "Auto-Deploy", selecione "No" (para evitar deploys automáticos que possam interromper o aplicativo funcionando)
   - Em "Instance Type", confirme que está selecionado "Free"

5. **Criar o Web Service**

   - Clique no botão "Create Web Service"
   - O Render iniciará o processo de build e deploy, que pode levar alguns minutos (seja paciente!)

## Parte 3: Monitoramento e Solução de Problemas

1. **Acompanhar o processo de build**

   - O Render mostrará os logs do processo de build e deploy
   - O download do arquivo GPKG (650 MB) pode levar alguns minutos
   - **IMPORTANTE**: O build pode falhar na primeira tentativa devido ao timeout durante o download do arquivo grande

2. **Se o build falhar**

   - Clique em "Manual Deploy" e selecione "Clear build cache & deploy"
   - Isso iniciará um novo build com cache limpo
   - Pode ser necessário tentar 2-3 vezes até que o download do GPKG seja concluído com sucesso

3. **Quando o deploy for bem-sucedido**

   - O Render fornecerá uma URL para seu aplicativo (algo como `https://app-abif-interdictus.onrender.com`)
   - Clique na URL para acessar seu aplicativo

## Parte 4: Uso e Manutenção

1. **Testando o aplicativo**

   - Faça upload de um arquivo KML/KMZ para testar a funcionalidade
   - O primeiro acesso pode ser lento, pois o aplicativo precisa baixar o arquivo GPKG

2. **Manutenção**

   - O aplicativo permanecerá online enquanto sua conta no Render estiver ativa
   - Aplicativos gratuitos no Render ficam inativos após 15 minutos sem uso
   - O primeiro acesso após inatividade pode levar mais tempo para carregar

## Solução de Problemas Comuns

### Erro "Build timeout"

**Problema**: O build falha com erro de timeout durante o download do arquivo GPKG.

**Solução**: 
- Tente novamente usando "Clear build cache & deploy"
- O Render tem um limite de 20 minutos para o build, e o download do arquivo grande pode exceder esse tempo em conexões lentas

### Erro "Memory limit exceeded"

**Problema**: O build falha com erro de memória durante o processamento do GPKG.

**Solução**:
- Tente novamente usando "Clear build cache & deploy"
- O aplicativo foi otimizado para usar o mínimo de memória possível, mas ocasionalmente pode exceder os limites

### Aplicativo lento ou travando

**Problema**: O aplicativo está muito lento ou trava durante o uso.

**Solução**:
- Aguarde o download completo do GPKG (mostrado na barra de progresso)
- Arquivos KML/KMZ muito grandes podem causar problemas de memória
- Tente com arquivos KML menores se necessário

## Notas Importantes

- O aplicativo usa o diretório temporário do sistema para armazenar o arquivo GPKG
- Este diretório é temporário e pode ser limpo periodicamente
- Quando isso acontecer, o aplicativo baixará o arquivo novamente automaticamente
- O download inicial do GPKG pode levar alguns minutos, dependendo da velocidade da conexão

## Suporte

Se encontrar problemas que não consegue resolver, entre em contato com o suporte técnico fornecendo:

1. Screenshots dos erros
2. Logs do Render (disponíveis na página do seu Web Service)
3. Detalhes sobre o arquivo KML/KMZ que está tentando processar
