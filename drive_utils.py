import os
import logging

# Garante que o diretório de logs existe antes de configurar o logging
os.makedirs('logs', exist_ok=True)

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# Configuração de logging
logging.basicConfig(filename='logs/backup.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Escopo de permissões para acessar o Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'client_secret.json'  # Arquivo de credenciais do Google
TOKEN_PICKLE = 'token.pickle'  # Arquivo para armazenar o token de autenticação

BACKUP_FOLDER_NAME = 'Backups_Python'  # Nome da pasta de backup no Drive

# Autentica e retorna o serviço do Google Drive

def authenticate_drive():
    creds = None
    # Tenta carregar o token salvo
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    # Se não houver token válido, faz o fluxo de autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Salva o token para reutilização
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    return service

# Busca ou cria a pasta de backup no Google Drive

def get_or_create_backup_folder(service):
    query = f"name='{BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']  # Retorna o ID da pasta existente
    # Cria a pasta se não existir
    file_metadata = {
        'name': BACKUP_FOLDER_NAME,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

# Cria uma pasta de backup com nome dinâmico (ex: Backups 2024-05-30_21-15-00)
def create_backup_folder(service, folder_name):
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

# Cria uma subpasta dentro de uma pasta pai no Google Drive
def create_subfolder(service, subfolder_name, parent_id):
    file_metadata = {
        'name': subfolder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

# Faz upload de um arquivo para a pasta de backup no Drive, com callback de progresso
# O callback deve receber a fração (0 a 1) do progresso

def upload_file(service, file_path, folder_id, progress_callback=None):
    import io
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    request = service.files().create(body=file_metadata, media_body=media, fields='id, size')
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and progress_callback:
            progress_callback(status.progress())
    logging.info(f'Arquivo enviado: {file_path} (ID: {response["id"]})')
    return response['id'], int(response.get('size', 0))  # Retorna o ID e tamanho do arquivo

# Faz download de um arquivo do Drive para o destino local, com callback de progresso
# O callback deve receber a fração (0 a 1) do progresso

def download_file(service, file_id, destination_path, progress_callback=None):
    request = service.files().get_media(fileId=file_id)
    with open(destination_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status and progress_callback:
                progress_callback(status.progress())
    logging.info(f'Arquivo baixado: {destination_path} (ID: {file_id})')
    return destination_path 