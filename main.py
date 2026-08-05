import os
import io
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = FastAPI()

clientes_conectados = []

# Configuração do Google Drive e ID da sua pasta
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PASTA_ID = "1Zy3Hn3QuTQdOSKP0RMhc7isr-xBWQnGf"

def obter_servico_drive():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('drive', 'v3', credentials=creds)

@app.post("/alerta_movimento")
async def receber_video(video: UploadFile = File(...)):
    try:
        conteudo = await video.read()
        servico = obter_servico_drive()
        
        # Aqui o Python recebe a instrução exata de onde salvar o arquivo
        file_metadata = {
            'name': video.filename,
            'parents': [PASTA_ID]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(conteudo), mimetype=video.content_type, resumable=True)
        arquivo = servico.files().create(body=file_metadata, media_body=media, fields='id').execute()
        
        return {"mensagem": "Vídeo salvo com sucesso na pasta", "id": arquivo.get("id")}
    except Exception as e:
        return {"erro": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clientes_conectados.append(websocket)
    try:
        while True:
            dados = await websocket.receive_text()
            for cliente in clientes_conectados:
                if cliente != websocket:
                    await cliente.send_text(dados)
    except WebSocketDisconnect:
        clientes_conectados.remove(websocket)

@app.get("/camera")
async def renderizar_camera():
    with open("camera.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/monitor")
async def renderizar_monitor():
    with open("monitor.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)