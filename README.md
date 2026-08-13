# Sistema de Monitoramento Inteligente (Monitor da Babá)

Plataforma de vigilância em tempo real baseada em arquitetura web distribuída. O sistema transforma qualquer dispositivo com um navegador, uma webcam e um microfone em um nó de monitoramento inteligente, utilizando Inteligência Artificial na borda (Edge Computing) para detectar pessoas, animais e sons de emergência, gravar eventos na nuvem e alertar o usuário remotamente.

## Arquitetura do Projeto

O sistema foi desenhado para contornar bloqueios de hardware (vendor lock-in de câmeras IP) utilizando o navegador web como motor nativo de captura.

A arquitetura é dividida em duas frentes:

* **Backend (FastAPI / Python):** Atua como um Hub central no Render, gerenciando conexões WebSocket autenticadas, roteamento de áudio/vídeo e upload dos vídeos de alerta para o Google Drive.
* **Frontend (HTML / JS):** Nós de transmissão (câmeras) e painéis de controle (monitores) que rodam nativamente no lado do cliente, incluindo toda a inteligência artificial de visão e de áudio.

## Recursos Principais

* **Visão Computacional:** Detecção de pessoas e animais em tempo real utilizando TensorFlow.js (modelo COCO-SSD) rodando diretamente no navegador da câmera.
* **Detecção de Som:** Reconhecimento de choro de bebê, latido de cachorro, miado de gato, gritos e sons altos não identificados, usando o modelo de áudio YAMNet (também via TensorFlow.js, direto no navegador — sem custo de servidor).
* **Gravação Automática:** Quando a IA (de vídeo ou de áudio) detecta uma ameaça, o sistema grava um clipe com vídeo e áudio e faz o upload automático para uma pasta segura no Google Drive.
* **Alertas Push Diferenciados:** Integração com Ntfy para notificações instantâneas no celular. Alertas de vídeo e de som chegam com título e ícone diferentes (📷 vigilância vs. 👶/🐶/🐱/😱/🔊 conforme o som identificado).
* **Painel com Alerta Visual Diferenciado:** No `/monitor`, alertas de vídeo aparecem em vermelho e alertas de som em roxo, cada um com seu próprio ícone — dá para saber o tipo de alerta sem precisar ler o texto.
* **Áudio Bidirecional:** Possibilidade de enviar comandos de voz do painel de monitoramento diretamente para as caixas de som do dispositivo que está filmando.
* **Localização do Nó:** O dashboard exibe a localização geográfica e a temperatura local (Open-Meteo) de cada câmera conectada.
* **Escalabilidade Plug-and-Play:** Não há necessidade de configurar IPs ou portas. Basta abrir o arquivo da câmera em múltiplos dispositivos e o painel de monitoramento organizará os fluxos automaticamente em um grid.
* **Autenticação de Verdade:** Login com sessão por token, chave própria para os dispositivos de câmera, e proteção contra tentativas repetidas de senha — nada de tela de login "decorativa".

## Tecnologias Utilizadas

* Python 3 / FastAPI / Uvicorn
* WebSockets (com autenticação por token)
* Google Drive API (google-api-python-client), com escopo restrito a `drive.file`
* TensorFlow.js — COCO-SSD (visão) e YAMNet (áudio)
* MediaRecorder API e Web Audio API (HTML5)
* Pydantic (validação automática dos dados recebidos pela API)

## Segurança: variáveis de ambiente obrigatórias

Antes de colocar em produção, configure estas variáveis de ambiente no Render
(Settings > Environment):

* `SENHA_ADMIN`: senha para acessar o painel `/monitor`. Escolha uma senha forte,
  não use o valor padrão do código.
* `CHAVE_DISPOSITIVOS`: chave compartilhada usada pela câmera (`camera.html`)
  para se autenticar no servidor. Gere um valor longo e aleatório e use o
  **mesmo valor** nos dois lugares: na variável de ambiente do servidor e na
  constante `CHAVE_DISPOSITIVO` dentro de `camera.html`.

Sem essas variáveis definidas, o servidor sobe com valores padrão inseguros
(e avisa isso no log) só para não quebrar em ambiente de teste local.

Além disso, dentro de `camera.html` existe a constante `NTFY_TOPICO` — troque
por um valor longo e aleatório também, já que tópicos do ntfy.sh são públicos
por padrão (qualquer pessoa que souber o nome pode se inscrever nos alertas).

**Nunca** commite `credentials.json` ou `token.json` no Git — o `.gitignore`
já está configurado para ignorá-los, junto com os ambientes virtuais Python
(`.venv/`, `ambiente_baba/`), a build do PyInstaller (`build/`, `dist/`) e a
pasta de configurações do editor (`.vscode/`).

## Manter o servidor sempre acordado (grátis)

O plano gratuito do Render "dorme" o serviço depois de um tempo sem receber
requisições. Existe uma rota `/health` (sem autenticação, resposta leve) feita
justamente para isso: cadastre a URL `https://SEU-APP.onrender.com/health` em
um serviço gratuito de ping, como o [UptimeRobot](https://uptimerobot.com) ou o
[cron-job.org](https://cron-job.org), configurado para checar a cada 5-10 minutos.
Isso mantém o servidor acordado sem custo nenhum.

## Detecção de Som: como funciona e como calibrar

O `camera.html` carrega o modelo **YAMNet** (Google, via TensorFlow.js) assim
que a câmera liga, junto com a lista oficial de classes de som do modelo.
A cada 1 segundo, analisa o último trecho de áudio captado pelo microfone e
verifica a pontuação de 4 categorias: **choro de bebê**, **latido**, **miado**
e **grito**. Se nenhuma delas for identificada mas o volume estiver muito alto
mesmo assim, o sistema dispara como **"som alto não identificado"**.

Qualquer detecção reaproveita o mesmo fluxo de alerta já usado pela visão
computacional: grava um clipe de vídeo com áudio, envia para o Google Drive,
notifica o painel `/monitor` e manda um push pelo ntfy.

Dois números em `camera.html` controlam a sensibilidade e podem precisar de
ajuste depois de testar com o ambiente real (ruído de fundo, distância do
microfone):

* `LIMIAR_CLASSE_AUDIO` (padrão `0.3`): confiança mínima para aceitar um som
  específico (choro, latido, miado, grito). Baixe se sons reais não estiverem
  disparando alerta; suba se estiver disparando à toa.
* `LIMIAR_SOM_ALTO` (padrão `0.18`): volume mínimo para o alerta genérico de
  "som alto não identificado". Mesma lógica de ajuste.

## Como Executar o Projeto

### 1. Configurando o Servidor (Backend)

Certifique-se de ter as credenciais do Google Drive (arquivo `token.json`) na
raiz do projeto — use o script `gerar_token.py` para gerar esse arquivo caso
não tenha um (veja as instruções dentro do próprio script).

Instale as dependências do Python:

```bash
pip install -r requirements.txt
```

Inicie o servidor principal:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Ativando as Câmeras (Nós de Transmissão)

Em qualquer dispositivo com câmera e microfone, acesse o servidor:
`/camera` (a URL completa do seu servidor, por exemplo `https://SEU-APP.onrender.com/camera`).

Conceda as permissões de vídeo e áudio solicitadas pelo navegador. As IAs de
visão e de áudio serão carregadas e a transmissão para o servidor central
começará automaticamente.

### 3. Acessando o Monitor (Painel de Controle)

Para visualizar todas as câmeras conectadas, acesse:
`/monitor` (por exemplo `https://SEU-APP.onrender.com/monitor`).

Digite a senha administrativa (`SENHA_ADMIN`) para liberar o painel. O grid
será montado automaticamente com base na quantidade de câmeras ativas.