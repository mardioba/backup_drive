import os
import shutil
import logging
from datetime import datetime
from drive_utils import authenticate_drive, create_backup_folder, create_subfolder, upload_file, download_file
from db_utils import registrar_backup

# Diretórios a serem excluídos do backup full (são do sistema e não devem ser copiados)
EXCLUDE_DIRS = ['/proc', '/sys', '/dev', '/run', '/tmp', '/mnt', '/media', '/lost+found']

# Verifica se o caminho está na lista de exclusão
def is_excluded(path):
    return any(path.startswith(ex) for ex in EXCLUDE_DIRS)

# Realiza backup personalizado de arquivos e diretórios selecionados pelo usuário
def backup_personalizado(paths, progress_callback=None):
    service = authenticate_drive()
    # Cria pasta de backup com data/hora
    folder_name = 'Backups ' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder_id = create_backup_folder(service, folder_name)
    for path in paths:
        if os.path.isfile(path):
            try:
                file_id, tamanho = upload_file(service, path, backup_folder_id, progress_callback)
                registrar_backup(os.path.basename(path), os.path.abspath(path), file_id, tamanho, 'personalizado')
                logging.info(f'Backup personalizado: {path}')
            except Exception as e:
                logging.error(f'Erro ao fazer backup de {path}: {e}')
        elif os.path.isdir(path):
            # Cria subpasta com o nome do diretório selecionado
            dir_name = os.path.basename(os.path.normpath(path))
            dir_folder_id = create_subfolder(service, dir_name, backup_folder_id)
            for root, dirs, files in os.walk(path):
                # Calcula o caminho relativo para manter a estrutura
                rel_root = os.path.relpath(root, path)
                # Cria subpastas intermediárias se necessário
                if rel_root != '.':
                    subfolder_id = dir_folder_id
                    parts = rel_root.split(os.sep)
                    for part in parts:
                        # Cria subpasta dentro da subpasta
                        subfolder_id = create_subfolder(service, part, subfolder_id)
                else:
                    subfolder_id = dir_folder_id
                dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_id, tamanho = upload_file(service, file_path, subfolder_id, progress_callback)
                        registrar_backup(file, os.path.abspath(file_path), file_id, tamanho, 'personalizado')
                        logging.info(f'Backup personalizado: {file_path}')
                    except Exception as e:
                        logging.error(f'Erro ao fazer backup de {file_path}: {e}')

# Realiza backup completo do sistema (exceto diretórios excluídos)
def backup_full(progress_callback=None):
    service = authenticate_drive()
    folder_name = 'Backups ' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_folder_id = create_backup_folder(service, folder_name)
    for root, dirs, files in os.walk('/'):
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
        # Cria subpasta correspondente à estrutura do sistema
        rel_root = os.path.relpath(root, '/')
        if rel_root == '.':
            parent_id = backup_folder_id
        else:
            # Cria subpastas recursivamente
            parent_id = backup_folder_id
            for part in rel_root.split(os.sep):
                if part:
                    parent_id = create_subfolder(service, part, parent_id)
        for file in files:
            file_path = os.path.join(root, file)
            if not is_excluded(file_path):
                try:
                    file_id, tamanho = upload_file(service, file_path, parent_id, progress_callback)
                    registrar_backup(file, os.path.abspath(file_path), file_id, tamanho, 'full')
                    logging.info(f'Backup full: {file_path}')
                except Exception as e:
                    logging.error(f'Erro ao fazer backup full de {file_path}: {e}')
                    continue

# Restaura um arquivo específico do Drive para o destino local
def restaurar_arquivo(file_id, destino, progress_callback=None):
    service = authenticate_drive()
    try:
        download_file(service, file_id, destino, progress_callback)
        logging.info(f'Restaurado arquivo: {destino}')
    except Exception as e:
        logging.error(f'Erro ao restaurar arquivo {file_id}: {e}')

# Restaura todos os arquivos de um backup completo para o destino local
def restaurar_backup_completo(destino, modo_backup='full', progress_callback=None):
    from db_utils import listar_todos_backups
    service = authenticate_drive()
    backups = listar_todos_backups()
    for b in backups:
        if b[6] == modo_backup:  # Verifica se o modo é 'full'
            nome_arquivo = b[1]
            file_id = b[4]
            caminho_destino = os.path.join(destino, nome_arquivo)
            try:
                download_file(service, file_id, caminho_destino, progress_callback)
                logging.info(f'Restaurado arquivo: {caminho_destino}')
            except Exception as e:
                logging.error(f'Erro ao restaurar arquivo {file_id}: {e}') 