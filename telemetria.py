import time
import psutil
import requests

URL = "https://testejr.onrender.com/api/telemetria"
# Copie e cole aqui o nome exato que foi gerado na tela da sua câmera
NOME_AMBIENTE = "Câmera 1234" 

while True:
    try:
        cpu = f"{psutil.cpu_percent(interval=1)}%"
        ram = f"{psutil.virtual_memory().percent}%"
        requests.post(URL, json={"id": NOME_AMBIENTE, "cpu": cpu, "ram": ram})
    except Exception as e:
        print("Erro ao enviar telemetria:", e)
    time.sleep(3)