# Sistema de Monitoramento com Inteligência Artificial (Babá Eletrônica)

Uma aplicação web completa de vigilância em tempo real com processamento de visão computacional na borda (Edge Computing), comunicação de baixa latência e integração automatizada com nuvem. O projeto transforma qualquer dispositivo com navegador e câmera em um terminal de segurança inteligente.

## Visão Geral da Arquitetura

O sistema opera em uma arquitetura Cliente-Servidor utilizando WebSockets para garantir a menor latência possível na transmissão de quadros de vídeo e pacotes de áudio. O servidor atua como um roteador de mensagens e gerenciador de armazenamento, enquanto o processamento pesado de Inteligência Artificial ocorre localmente no dispositivo da câmera, poupando recursos de nuvem.

## Funcionalidades Implementadas

* **Transmissão ao Vivo de Baixa Latência:** Uso de WebSockets para tráfego contínuo de quadros de vídeo entre a câmera e o painel de monitoramento.
* **Inteligência Artificial Integrada:** Aplicação do modelo neural COCO-SSD via TensorFlow.js para análise de quadros em tempo real. O sistema é capaz de diferenciar e identificar pessoas e animais, disparando gatilhos de segurança com alta precisão.
* **Armazenamento Automático em Nuvem:** Integração nativa com a API do Google Drive (via Service Account credentials). Quando a IA detecta uma ameaça, a câmera grava o evento e o backend realiza o upload imediato e silencioso para uma pasta restrita.
* **Reciclagem Inteligente de Arquivos:** Rotina assíncrona programada no backend (Python) que varre a pasta de armazenamento a cada hora e exclui permanentemente registros com mais de 72 horas de criação, garantindo que o espaço do Drive não seja esgotado.
* **Progressive Web App (PWA):** O sistema é empacotado com um arquivo Manifest e Service Worker, permitindo a instalação nativa em dispositivos iOS, Android, Windows e macOS, rodando em tela cheia sem interface de navegador.
* **Comunicação Bidirecional (Call):** Interface de áudio no painel do monitor com captação de microfone e gráfico de modulação visual. O áudio é convertido e enviado via pacote WebSocket para ser reproduzido no ambiente da câmera.
* **Alertas Push Externos:** Integração com o serviço ntfy, enviando notificações push instantâneas para dispositivos móveis contendo o relatório exato do que a IA detectou.
* **Rastreamento Geográfico e Status de Rede:** A câmera utiliza a API do OpenStreetMap e do navegador para fornecer sua localização aproximada, status do IP, qualidade da conexão e horário local direto no painel do administrador.
* **Autenticação e Segurança:** Proteção da rota de monitoramento através de uma camada de login, impedindo o acesso não autorizado ao painel de controle e ao feed da câmera.
* **Resiliência de Conexão:** Mecanismos de reconexão automática (auto-healing) tanto no cliente quanto no servidor. O Python ignora conexões fantasmas para evitar quedas, e o HTML reconecta o fluxo de vídeo caso haja oscilação na internet.

## Tecnologias e Bibliotecas

**Backend:**
* Python 3
* FastAPI e Uvicorn (Servidor assíncrono)
* WebSockets (Protocolo de comunicação em tempo real)
* Google API Python Client e Google Auth (Autenticação e armazenamento)
* Asyncio (Rotinas de background)

**Frontend:**
* HTML5, CSS3 e JavaScript Vanilla
* Design Pattern Glassmorphism
* TensorFlow.js e COCO-SSD Model (Visão Computacional)
* MediaRecorder API (Gravação e captura de mídia)
* Geolocation API (Rastreamento)

## Estrutura de Arquivos

* `main.py`: Motor central em Python que gerencia as rotas, os WebSockets e a API do Google Drive.
* `index.html`: Landing page do sistema com interface de roteamento.
* `camera.html`: Cliente de captura de vídeo com IA embutida e motor de gravação.
* `monitor.html`: Painel de controle administrativo com feed de vídeo, informações telemétricas e interface de áudio.
* `manifest.json`: Arquivo de configuração que define as propriedades do PWA.
* `sw.js`: Service worker minimalista para habilitar a instalação nativa.
* `icone.png`: Identidade visual para instalação do aplicativo na tela inicial.
* `requirements.txt`: Mapeamento de dependências para deploy em provedores de nuvem.
* `credentials.json` e `token.json`: Chaves de acesso ao cofre do Google Drive.

## Como Executar o Projeto

1. Instale as dependências executando: `pip install -r requirements.txt`
2. Certifique-se de ter os arquivos `credentials.json` e `token.json` válidos na raiz do projeto para o Google Drive funcionar.
3. Inicie o servidor localmente com: `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Acesse `http://localhost:8000` no seu navegador.