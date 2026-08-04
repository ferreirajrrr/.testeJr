print("Passo 1: Carregando módulos do sistema e do Google...")

import os
import uvicorn
import webbrowser
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse
from typing import List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

print("Passo 2: Construindo o servidor e preparando rotas...")
app = FastAPI()

# --- INTEGRAÇÃO COM O GOOGLE DRIVE ---
def fazer_upload_drive(caminho_video):
    print(f"\nIniciando o envio do arquivo {caminho_video} para o Drive...")
    
    if not os.path.exists('token.json'):
        print("Erro: Arquivo token.json não encontrado. O upload foi cancelado.")
        return

    try:
        # Carrega o carimbo de acesso permanente
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.file'])
        
        # Conecta com a sua conta do Drive
        servico = build('drive', 'v3', credentials=creds)

        # Prepara o pacote de vídeo
        nome_arquivo = os.path.basename(caminho_video)
        metadados_arquivo = {'name': nome_arquivo}
        midia = MediaFileUpload(caminho_video, mimetype='video/mp4', resumable=True)

        # Executa a transferência
        print("Transferindo para a nuvem...")
        arquivo = servico.files().create(body=metadados_arquivo, media_body=midia, fields='id').execute()
        print(f"Sucesso absoluto! Vídeo salvo no seu Google Drive (ID: {arquivo.get('id')})\n")
        
    except Exception as e:
        print(f"Falha na comunicação com o Google Drive: {e}\n")
# ----------------------------------------

class GerenciadorConexao:
    def __init__(self):
        self.conexoes_ativas: List[WebSocket] = []

    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.conexoes_ativas.append(websocket)

    def desconectar(self, websocket: WebSocket):
        self.conexoes_ativas.remove(websocket)

    async def enviar_mensagem(self, mensagem: str, remetente: WebSocket):
        for conexao in self.conexoes_ativas:
            if conexao != remetente:
                await conexao.send_text(mensagem)

gerenciador = GerenciadorConexao()

def obter_caminho_html():
    caminho_atual = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(caminho_atual, 'index.html')

@app.get("/")
async def ler_interface():
    caminho = obter_caminho_html()
    with open(caminho, "r", encoding="utf-8") as arquivo:
        conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)

# Nova porta de entrada para os alertas da câmera
@app.post("/alerta_movimento")
async def receber_alerta(video: UploadFile = File(...)):
    print("\nAlerta recebido! Salvando o registro de movimento...")
    
    # Salva o arquivo temporariamente no seu disco local
    caminho_local = f"alerta_{video.filename}"
    with open(caminho_local, "wb") as buffer:
        buffer.write(await video.read())
        
    # Manda para o Google Drive trabalhando em segundo plano para não travar o sistema
    threading.Thread(target=fazer_upload_drive, args=(caminho_local,)).start()
    
    return {"mensagem": "Vídeo recebido e envio iniciado"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await gerenciador.conectar(websocket)
    try:
        while True:
            dados = await websocket.receive_text()
            await gerenciador.enviar_mensagem(dados, websocket)
    except WebSocketDisconnect:
        gerenciador.desconectar(websocket)

def iniciar_servidor():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("==================================================")
    print("Passo 3: Ligando o motor da Baba Eletronica!")
    print("==================================================")
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8000")).start()
    iniciar_servidor()