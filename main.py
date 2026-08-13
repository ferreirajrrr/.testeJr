import os
import io
import json
import time
import hmac
import secrets
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("monitor")

app = FastAPI()

# CORS liberado para permitir qualquer dispositivo/navegador se conectar,
# mas sem credenciais de cookie (não usamos cookies, então isso é seguro).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

clientes_conectados = []

cache_geo = {}

# ============================================================
# CONFIGURAÇÃO - tudo sensível vem de variáveis de ambiente.
# No Render: Settings > Environment > Add Environment Variable
# ============================================================

# Apenas acesso aos arquivos criados pelo próprio app (não ao Drive inteiro)
SCOPES = ['https://www.googleapis.com/auth/drive.file']
PASTA_ID = os.environ.get("PASTA_ID", "1Zy3Hn3QuTQdOSKP0RMhc7isr-xBWQnGf")

SENHA_ADMIN = os.environ.get("SENHA_ADMIN")
if not SENHA_ADMIN:
    SENHA_ADMIN = "troque-esta-senha-agora"
    log.warning(
        "ATENCAO: variavel de ambiente SENHA_ADMIN nao definida. "
        "Usando senha padrao INSEGURA. Configure SENHA_ADMIN no ambiente."
    )

# Chave compartilhada usada pela câmera (camera.html) para autenticar
# no /ws e nos endpoints de escrita. É separada da senha do painel
# administrativo: se essa chave vazar, quem a tiver só consegue
# TRANSMITIR como câmera, não ver o painel todo.
CHAVE_DISPOSITIVOS = os.environ.get("CHAVE_DISPOSITIVOS")
if not CHAVE_DISPOSITIVOS:
    CHAVE_DISPOSITIVOS = "troque-esta-chave-de-dispositivo"
    log.warning(
        "ATENCAO: variavel de ambiente CHAVE_DISPOSITIVOS nao definida. "
        "Usando chave padrao INSEGURA. Configure CHAVE_DISPOSITIVOS no ambiente."
    )

# ============================================================
# SESSÕES (tokens de login do painel /monitor)
# ============================================================
SESSOES_VALIDAS = {}  # token -> timestamp de expiração
DURACAO_SESSAO_SEGUNDOS = 24 * 3600

def gerar_token_sessao():
    token = secrets.token_urlsafe(32)
    SESSOES_VALIDAS[token] = time.time() + DURACAO_SESSAO_SEGUNDOS
    return token

def token_valido(token):
    """Aceita tanto um token de sessão do painel quanto a chave fixa dos dispositivos."""
    if not token:
        return False
    if hmac.compare_digest(token, CHAVE_DISPOSITIVOS):
        return True
    expira = SESSOES_VALIDAS.get(token)
    if expira is None:
        return False
    if time.time() > expira:
        SESSOES_VALIDAS.pop(token, None)
        return False
    return True

def limpar_sessoes_expiradas():
    agora = time.time()
    expirados = [t for t, exp in SESSOES_VALIDAS.items() if exp < agora]
    for t in expirados:
        SESSOES_VALIDAS.pop(t, None)

# ============================================================
# PROTEÇÃO CONTRA FORÇA BRUTA NO LOGIN
# ============================================================
tentativas_login = {}  # ip -> {"falhas": int, "bloqueado_ate": timestamp}
MAX_TENTATIVAS = 5
BLOQUEIO_SEGUNDOS = 300  # 5 minutos

def obter_servico_drive():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('drive', 'v3', credentials=creds)

# ============================================================
# FORMATOS DE DADOS ESPERADOS (validados automaticamente pelo FastAPI)
# ============================================================
class LoginRequest(BaseModel):
    senha: str

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
            log.error("Erro na reciclagem de videos: %s", e)

        limpar_sessoes_expiradas()
        await asyncio.sleep(3600)

@app.on_event("startup")
async def iniciar_rotinas():
    asyncio.create_task(reciclar_videos_antigos())

@app.post("/alerta_movimento")
async def receber_video(token: str = Query(...), video: UploadFile = File(...)):
    if not token_valido(token):
        return {"erro": "Nao autorizado."}
    try:
        conteudo = await video.read()
        servico = obter_servico_drive()
        file_metadata = {'name': video.filename, 'parents': [PASTA_ID]}
        media = MediaIoBaseUpload(io.BytesIO(conteudo), mimetype=video.content_type, resumable=True)
        arquivo = servico.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return {"mensagem": "Video salvo com sucesso na pasta", "id": arquivo.get("id")}
    except Exception as e:
        log.error("Erro ao salvar video: %s", e)
        return {"erro": "Falha ao salvar o video."}

@app.post("/api/login")
async def fazer_login(dados: LoginRequest, request: Request):
    ip = request.client.host if request.client else "desconhecido"
    agora = time.time()
    registro = tentativas_login.get(ip)

    if registro and registro["bloqueado_ate"] > agora:
        return {"sucesso": False, "erro": "Muitas tentativas. Tente novamente em alguns minutos."}

    if hmac.compare_digest(dados.senha, SENHA_ADMIN):
        tentativas_login.pop(ip, None)
        token = gerar_token_sessao()
        return {"sucesso": True, "token": token}

    falhas = (registro["falhas"] + 1) if registro else 1
    bloqueado_ate = agora + BLOQUEIO_SEGUNDOS if falhas >= MAX_TENTATIVAS else 0
    tentativas_login[ip] = {"falhas": falhas, "bloqueado_ate": bloqueado_ate}
    return {"sucesso": False}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    global cache_geo

    if not token_valido(token):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    clientes_conectados.append(websocket)
    log.info("Cliente conectado ao WebSocket (%d ativos)", len(clientes_conectados))

    for cam_id, geo in cache_geo.items():
        try: await websocket.send_text(json.dumps({"id": cam_id, "tipo": "GEO", "dados": geo}))
        except Exception: pass

    try:
        while True:
            texto_recebido = await websocket.receive_text()
            try:
                pacote = json.loads(texto_recebido)
                cam_id = pacote.get("id", "Desconhecida")
                if pacote.get("tipo") == "GEO":
                    cache_geo[cam_id] = pacote.get("dados")
            except Exception:
                pass

            for cliente in clientes_conectados.copy():
                if cliente != websocket:
                    try:
                        await cliente.send_text(texto_recebido)
                    except Exception:
                        if cliente in clientes_conectados:
                            clientes_conectados.remove(cliente)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.error("Erro no WebSocket: %s", e)
    finally:
        if websocket in clientes_conectados:
            clientes_conectados.remove(websocket)
        log.info("Cliente desconectado (%d ativos)", len(clientes_conectados))

@app.get("/health")
async def verificar_saude():
    # Endpoint leve, sem autenticação, só para serviços de "ping" (tipo
    # UptimeRobot ou cron-job.org) manterem o servidor acordado no plano
    # gratuito do Render. Não consulta o Google Drive nem nada pesado.
    return {"status": "ok"}

@app.get("/")
async def renderizar_index():
    with open("index.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())

@app.get("/camera")
async def renderizar_camera():
    with open("camera.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())

@app.get("/monitor")
async def renderizar_monitor():
    with open("monitor.html", "r", encoding="utf-8") as f: return HTMLResponse(content=f.read())

@app.get("/manifest.json")
async def entregar_manifest(): return FileResponse("manifest.json")

@app.get("/sw.js")
async def entregar_sw(): return FileResponse("sw.js")

@app.get("/icone.png")
async def entregar_icone(): return FileResponse("icone.png")

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)
