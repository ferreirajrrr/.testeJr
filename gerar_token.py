"""
Rode este script UMA VEZ no seu computador para gerar um novo token.json.

O que ele faz:
1. Abre uma janela do navegador pedindo para você logar com a conta Google
   que tem acesso à pasta do Drive usada pelo projeto.
2. Depois de você aceitar, cria o arquivo token.json na mesma pasta.

Antes de rodar:
- Coloque o arquivo credentials.json (baixado do Google Cloud Console) na
  mesma pasta deste script.
- Instale a dependência que falta, se necessário:
    pip install google-auth-oauthlib

Como rodar:
    python gerar_token.py
"""

from google_auth_oauthlib.flow import InstalledAppFlow

# Mesmo escopo reduzido usado no main.py (só arquivos criados pelo próprio app)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as f:
        f.write(creds.to_json())

    print("Pronto! O arquivo token.json foi criado/atualizado nesta pasta.")

if __name__ == '__main__':
    main()
