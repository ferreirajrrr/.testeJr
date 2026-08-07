from flask import Flask, Response
from flask_cors import CORS
import cv2

app = Flask(__name__)
CORS(app)

# Utilizando o seu IP Público conforme solicitado
URL_DA_CAMERA = "rtsp://admin:Drogo9024@177.100.120.180:554/onvif1"

def gerar_quadros():
    camera = cv2.VideoCapture(URL_DA_CAMERA)
    while True:
        sucesso, quadro = camera.read()
        if not sucesso:
            camera = cv2.VideoCapture(URL_DA_CAMERA)
            continue
        
        quadro_redimensionado = cv2.resize(quadro, (640, 360))
        ret, buffer = cv2.imencode('.jpg', quadro_redimensionado)
        quadro_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + quadro_bytes + b'\r\n')

@app.route('/stream')
def stream_video():
    return Response(gerar_quadros(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    print("Gateway da Câmera IP rodando na porta 5000...")
    app.run(host='127.0.0.1', port=5000, threaded=True)