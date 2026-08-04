import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Permissão exclusiva para criar e gerenciar arquivos no seu Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def autenticar_google():
    creds = None
    
    # Verifica se já temos o carimbo de acesso salvo
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Se não tiver, vamos pedir permissão no navegador
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva o carimbo para os próximos acessos
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    print("Sucesso absoluto! O Python agora tem acesso ao seu Google Drive.")

if __name__ == '__main__':
    print("Iniciando o teste de conexao com o Google...")
    autenticar_google()