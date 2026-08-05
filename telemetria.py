import time
import psutil
import requests

URL = "https://testejr.onrender.com/api/telemetria"

while True:
    try:
        cpu = f"{psutil.cpu_percent(interval=1)}%"
        ram = f"{psutil.virtual_memory().percent}%"
        requests.post(URL, json={"cpu": cpu, "ram": ram})
    except Exception as e:
        print("Erro ao enviar telemetria:", e)
    time.sleep(3)