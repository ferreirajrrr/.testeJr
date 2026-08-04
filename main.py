from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

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

@app.get("/")
async def ler_interface():
    with open("index.html", "r", encoding="utf-8") as arquivo:
        conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await gerenciador.conectar(websocket)
    try:
        while True:
            dados = await websocket.receive_text()
            await gerenciador.enviar_mensagem(dados, websocket)
    except WebSocketDisconnect:
        gerenciador.desconectar(websocket)