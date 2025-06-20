import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopo de acesso (modifique se quiser acesso somente leitura, etc.)
SCOPES = ['https://www.googleapis.com/auth/drive']

# Caminho para as credenciais baixadas do Google Cloud
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def autenticar_google_drive():
    creds = None

    # Verifica se já existe token salvo
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # Se não tiver credenciais válidas, faça login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Salva o token para futuras execuções
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    # Cria o serviço do Google Drive
    service = build('drive', 'v3', credentials=creds)
    return service

# Exemplo de uso: listar os 10 primeiros arquivos no Drive
if __name__ == '__main__':
    service = autenticar_google_drive()
    results = service.files().list(
        pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('Nenhum arquivo encontrado.')
    else:
        print('Arquivos:')
        for item in items:
            print(f"{item['name']} ({item['id']})")
