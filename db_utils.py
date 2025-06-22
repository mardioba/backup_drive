import sqlite3
from datetime import datetime

DB_NAME = 'backups.db'  # Nome do arquivo do banco de dados SQLite

# Inicializa o banco de dados e cria a tabela de backups, se não existir

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL,
            caminho_original TEXT NOT NULL,
            data_backup TEXT NOT NULL,
            id_drive TEXT NOT NULL,
            tamanho INTEGER NOT NULL,
            modo_backup TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Registra um novo backup no banco de dados

def registrar_backup(nome_arquivo, caminho_original, id_drive, tamanho, modo_backup):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    data_backup = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Data e hora do backup
    c.execute('''
        INSERT INTO backups (nome_arquivo, caminho_original, data_backup, id_drive, tamanho, modo_backup)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome_arquivo, caminho_original, data_backup, id_drive, tamanho, modo_backup))
    conn.commit()
    conn.close()

# Busca backups pelo nome ou parte do nome do arquivo

def buscar_backups_por_nome(parte_nome):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT * FROM backups WHERE nome_arquivo LIKE ?
    ''', (f'%{parte_nome}%',))
    resultados = c.fetchall()
    conn.close()
    return resultados

# Lista todos os backups registrados, ordenados pela data

def listar_todos_backups():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM backups ORDER BY data_backup DESC')
    resultados = c.fetchall()
    conn.close()
    return resultados 