import os
import uvicorn
import webbrowser
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()

def fazer_upload_drive(caminho_video):
    if not os.path.exists('token.json'):
        print("Erro: token.json não encontrado.")
        return

    try:
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/drive.file'])
        servico = build('drive', 'v3', credentials=creds)

        nome_arquivo = os.path.basename(caminho_video)
        metadados_arquivo = {'name': nome_arquivo}
        midia = MediaFileUpload(caminho_video, mimetype='video/webm', resumable=True)

        servico.files().create(body=metadados_arquivo, media_body=midia, fields='id').execute()
        print(f"Sucesso absoluto! Vídeo salvo no Google Drive.")
        
    except Exception as e:
        print(f"Falha na comunicação com o Google Drive: {e}")

class GerenciadorConexao:
    def __init__(self):
        self.conexoes_ativas: List[WebSocket] = []

    async def conectar(self, websocket: WebSocket):
        await websocket.accept()
        self.conexoes_ativas.append(websocket)

    def desconectar(self, websocket: WebSocket):
        if websocket in self.conexoes_ativas:
            self.conexoes_ativas.remove(websocket)

    async def enviar_mensagem(self, mensagem: str, remetente: WebSocket):
        for conexao in self.conexoes_ativas:
            if conexao != remetente:
                try:
                    await conexao.send_text(mensagem)
                except:
                    pass

gerenciador = GerenciadorConexao()

@app.get("/")
async def raiz():
    return RedirectResponse(url="/camera")

@app.get("/camera")
async def ler_camera():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'camera.html')
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return HTMLResponse(content=arquivo.read(), status_code=200)

@app.get("/monitor")
async def ler_monitor():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitor.html')
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return HTMLResponse(content=arquivo.read(), status_code=200)

@app.post("/alerta_movimento")
async def receber_alerta(video: UploadFile = File(...)):
    caminho_local = f"alerta_{video.filename}"
    with open(caminho_local, "wb") as buffer:
        buffer.write(await video.read())
        
    threading.Thread(target=fazer_upload_drive, args=(caminho_local,)).start()
    return {"mensagem": "Recebido"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await gerenciador.conectar(websocket)
    try:
        while True:
            dados = await websocket.receive_text()
            await gerenciador.enviar_mensagem(dados, websocket)
    except WebSocketDisconnect:
        gerenciador.desconectar(websocket)

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)