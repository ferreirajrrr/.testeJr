from flask import Flask, Response, send_file
from flask_cors import CORS
import cv2

app = Flask(__name__)
CORS(app)

# Retornamos para o IP da rede interna com a senha atualizada
URL_DA_CAMERA = "rtsp://admin:Drogo9024@192.168.0.103:554/live/ch00_1"

def gerar_quadros():
    camera = cv2.VideoCapture(URL_DA_CAMERA)
    while True:
        sucesso, quadro = camera.read()
        if not sucesso:
            camera = cv2.VideoCapture(URL_DA_CAMERA)
            continue
        
        # Reduzindo um pouco a imagem para o navegador não engasgar
        quadro_redimensionado = cv2.resize(quadro, (640, 360))
        ret, buffer = cv2.imencode('.jpg', quadro_redimensionado)
        quadro_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + quadro_bytes + b'\r\n')

@app.route('/stream')
def stream_video():
    return Response(gerar_quadros(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def hospedar_camera():
    # O Python agora entrega a página web
    return send_file('camera.html')

if __name__ == "__main__":
    print("Servidor Gateway rodando! Abra no navegador do Asus: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True)