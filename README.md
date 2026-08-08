# Sistema de Monitoramento Inteligente (Monitor da Babá)

Plataforma de vigilância em tempo real baseada em arquitetura web distribuída. O sistema transforma qualquer dispositivo com um navegador e uma webcam em um nó de monitoramento inteligente, utilizando Inteligência Artificial na borda (Edge Computing) para detectar pessoas e animais, gravar eventos na nuvem e alertar o usuário remotamente.

## Arquitetura do Projeto

O sistema foi desenhado para contornar bloqueios de hardware (vendor lock-in de câmeras IP) utilizando o navegador web como motor nativo de captura. 

A arquitetura é dividida em duas frentes:

* **Backend (FastAPI / Python):** Atua como um Hub central no Render, gerenciando conexões WebSocket, roteamento de áudio/vídeo e autenticação com a API do Google Drive.
* **Frontend (HTML / JS):** Nós de transmissão (câmeras) e painéis de controle (monitores) que rodam nativamente no lado do cliente.

## Recursos Principais

* **Visão Computacional:** Detecção de objetos em tempo real utilizando TensorFlow.js (modelo COCO-SSD) rodando diretamente no navegador da câmera.
* **Gravação Automática:** Quando a IA detecta uma ameaça, o sistema grava um clipe e faz o upload automático para uma pasta segura no Google Drive.
* **Alertas Push:** Integração com Ntfy para enviar notificações instantâneas para dispositivos móveis no momento da detecção.
* **Áudio Bidirecional:** Possibilidade de enviar comandos de voz do painel de monitoramento diretamente para as caixas de som do dispositivo que está filmando.
* **Telemetria Integrada:** O dashboard exibe informações de hardware (núcleos de CPU), localização geográfica e temperatura local (Open-Meteo) de cada nó conectado.
* **Escalabilidade Plug-and-Play:** Não há necessidade de configurar IPs ou portas. Basta abrir o arquivo da câmera em múltiplos computadores ou tablets e o painel de monitoramento organizará os fluxos automaticamente em um grid.

## Tecnologias Utilizadas

* Python 3
* FastAPI e Uvicorn
* WebSockets
* Google Drive API (google-api-python-client)
* TensorFlow.js
* MediaRecorder API (HTML5)

## Segurança: variáveis de ambiente obrigatórias

Antes de colocar em produção, configure estas variáveis de ambiente no Render
(Settings > Environment):

* `SENHA_ADMIN`: senha para acessar o painel `/monitor`. Escolha uma senha forte,
  não use o valor padrão do código.
* `CHAVE_DISPOSITIVOS`: chave compartilhada usada pelas câmeras (`camera.html`)
  e pelo script `telemetria.py` para se autenticarem no servidor. Gere um valor
  longo e aleatório e use o **mesmo valor** nos três lugares: na variável de
  ambiente do servidor, na constante `CHAVE_DISPOSITIVO` dentro de `camera.html`,
  e na constante `CHAVE_DISPOSITIVO` dentro de `telemetria.py`.

Sem essas variáveis definidas, o servidor sobe com valores padrão inseguros
(e avisa isso no log) só para não quebrar em ambiente de teste local.

Além disso, dentro de `camera.html` existe a constante `NTFY_TOPICO` — troque
por um valor longo e aleatório também, já que tópicos do ntfy.sh são públicos
por padrão (qualquer pessoa que souber o nome pode se inscrever nos alertas).

**Nunca** commite `credentials.json` ou `token.json` no Git — o `.gitignore`
já está configurado para ignorá-los.

## Manter o servidor sempre acordado (grátis)

O plano gratuito do Render "dorme" o serviço depois de um tempo sem receber
requisições. Existe uma rota `/health` (sem autenticação, resposta leve) feita
justamente para isso: cadastre a URL `https://SEU-APP.onrender.com/health` em
um serviço gratuito de ping, como o [UptimeRobot](https://uptimerobot.com) ou o
[cron-job.org](https://cron-job.org), configurado para checar a cada 5-10 minutos.
Isso mantém o servidor acordado sem custo nenhum.

## Como Executar o Projeto

### 1. Configurando o Servidor (Backend)

Certifique-se de ter as credenciais do Google Drive (arquivo `token.json`) na raiz do projeto.
Instale as dependências do Python:

```bash
pip install -r requirements.txt
```

Inicie o servidor principal:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Ativando as Câmeras (Nós de Transmissão)

Em qualquer dispositivo com câmera e microfone, acesse o servidor ou abra o arquivo localmente:
`/camera` (ou abra o arquivo `camera.html` direto no navegador).

Conceda as permissões de vídeo e áudio solicitadas pelo navegador. A IA será carregada e a transmissão para o servidor central começará automaticamente.

### 3. Acessando o Monitor (Painel de Controle)

Para visualizar todas as câmeras conectadas, acesse:
`/monitor` (ou abra o arquivo `monitor.html`).

Digite a senha administrativa para liberar o painel. O grid será montado automaticamente com base na quantidade de câmeras ativas na rede.