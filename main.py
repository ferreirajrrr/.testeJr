import os
import io
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = FastAPI()

clientes_conectados = []

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
PASTA_ID = "1Zy3Hn3QuTQdOSKP0RMhc7isr-xBWQnGf"
SENHA_ADMIN = "admin123" 

def obter_servico_drive():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('drive', 'v3', credentials=creds)

async def reciclar_videos_antigos():
    while True:
        try:
            servico = obter_servico_drive()
            tempo_limite = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
            
            query = f"'{PASTA_ID}' in parents and createdTime < '{tempo_limite}' and trashed = false"
            resultados = servico.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            arquivos = resultados.get('files', [])
            
            for arquivo in arquivos:
                servico.files().delete(fileId=arquivo['id']).execute()
                
        except Exception as e:
            print("Erro na reciclagem de videos:", str(e))
            
        await asyncio.sleep(3600)

@app.on_event("startup")
async def iniciar_rotinas():
    asyncio.create_task(reciclar_videos_antigos())

@app.post("/alerta_movimento")
async def receber_video(video: UploadFile = File(...)):
    try:
        conteudo = await video.read()
        servico = obter_servico_drive()
        file_metadata = {'name': video.filename, 'parents': [PASTA_ID]}
        media = MediaIoBaseUpload(io.BytesIO(conteudo), mimetype=video.content_type, resumable=True)
        arquivo = servico.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return {"mensagem": "Vídeo salvo com sucesso na pasta", "id": arquivo.get("id")}
    except Exception as e:
        return {"erro": str(e)}

@app.post("/api/login")
async def fazer_login(request: Request):
    dados = await request.json()
    if dados.get("senha") == SENHA_ADMIN:
        return {"sucesso": True}
    return {"sucesso": False}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clientes_conectados.append(websocket)
    try:
        while True:
            dados = await websocket.receive_text()
            for cliente in clientes_conectados.copy():
                if cliente != websocket:
                    try:
                        await cliente.send_text(dados)
                    except Exception:
                        if cliente in clientes_conectados:
                            clientes_conectados.remove(cliente)
    except Exception:
        pass
    finally:
        if websocket in clientes_conectados:
            clientes_conectados.remove(websocket)

@app.get("/")
async def renderizar_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/camera")
async def renderizar_camera():
    with open("camera.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/monitor")
async def renderizar_monitor():
    with open("monitor.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/manifest.json")
async def entregar_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def entregar_sw():
    return FileResponse("sw.js")

@app.get("/icone.png")
async def entregar_icone():
    return FileResponse("icone.png")

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)