from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def ler_interface():
    with open("index.html", "r", encoding="utf-8") as arquivo:
        conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)