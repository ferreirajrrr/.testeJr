import time
import psutil
import requests

URL = "https://testejr.onrender.com/api/telemetria"
# Copie e cole aqui o nome exato que foi gerado na tela da sua câmera
NOME_AMBIENTE = "Câmera 1234"

# Precisa ser IGUAL ao valor da variável de ambiente CHAVE_DISPOSITIVOS no servidor
CHAVE_DISPOSITIVO = "VQbQwo-_9K7S0GvSbAlPvibU7SYfRwUo-_2caiYBQXI"

while True:
    try:
        cpu = f"{psutil.cpu_percent(interval=1)}%"
        ram = f"{psutil.virtual_memory().percent}%"
        requests.post(
            URL,
            params={"token": CHAVE_DISPOSITIVO},
            json={"id": NOME_AMBIENTE, "cpu": cpu, "ram": ram},
        )
    except Exception as e:
        print("Erro ao enviar telemetria:", e)
    time.sleep(3)