import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.ttk import *
from tkinter import *
import threading
import os
import shutil
from db_utils import init_db, buscar_backups_por_nome, listar_todos_backups
from backup_utils import backup_personalizado, backup_full, restaurar_arquivo, restaurar_backup_completo
from PIL import Image, ImageTk

# Inicializa o banco de dados ao iniciar o sistema
init_db()

# Função utilitária para executar tarefas demoradas em uma thread separada
def run_in_thread(target, *args):
    t = threading.Thread(target=target, args=args)
    t.start()

# Classe principal da interface gráfica do sistema de backup
class BackupApp:
    def __init__(self, root):
        self.root = root
        # self.root.config(bg='lightblue')
        self.root.title('Sistema de Backup para Google Drive')
        largura = root.winfo_screenwidth()
        self.root.geometry(f'{largura}x700')  # Aumenta largura e altura

        # Lista de caminhos selecionados para backup personalizado
        self.paths_selecionados = []

        # Carrega ícones
        try:
            self.icon_add_file = tk.PhotoImage(file='icones/criar_arquivo-100.png')
        except:
            self.icon_add_file = None
            
        try:
            self.icon_add_folder = tk.PhotoImage(file='icones/adicionar_pasta_100.png')
        except:
            self.icon_add_folder = None
            
        try:
            self.icon_remove = tk.PhotoImage(file='icones/lixeira-100.png')
        except:
            self.icon_remove = None
            
        try:
            self.icon_backup = tk.PhotoImage(file='icones/upload-100.png')
        except:
            self.icon_backup = None
            
        try:
            self.icon_backup_full = tk.PhotoImage(file='icones/backup-100.png')
        except:
            self.icon_backup_full = None
            
        try:
            self.icon_search = tk.PhotoImage(file='icones/lupa-100.png')
        except:
            self.icon_search = None
            
        try:
            self.icon_restore = tk.PhotoImage(file='icones/download-100.png')
        except:
            self.icon_restore = None
            
        try:
            self.icon_config = tk.PhotoImage(file='icones/engrenagem-100.png')
        except:
            self.icon_config = None

        # Frame superior para os botões de ação
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(fill=tk.X, padx=10, pady=5)

        # Botão para adicionar arquivos
        btn_add_arquivos = tk.Button(frame_botoes, text='Add arq.', image=self.icon_add_file, compound=tk.LEFT, command=self.adicionar_arquivos)
        btn_add_arquivos.pack(side=tk.LEFT, padx=5)

        # Botão para adicionar diretórios
        btn_add_dirs = tk.Button(frame_botoes, text='Add dir.', image=self.icon_add_folder, compound=tk.LEFT, command=self.adicionar_diretorios)
        btn_add_dirs.pack(side=tk.LEFT, padx=5)

        # Botão para remover seleção
        btn_remover = tk.Button(frame_botoes, text='Del sel.', image=self.icon_remove, compound=tk.LEFT, command=self.remover_selecionado)
        btn_remover.pack(side=tk.LEFT, padx=5)

        # Botão para iniciar backup dos selecionados
        btn_backup_sel = tk.Button(frame_botoes, text='Fazer bkp dos sel.', image=self.icon_backup, compound=tk.LEFT, command=self.backup_selecionados)
        btn_backup_sel.pack(side=tk.LEFT, padx=5)

        # Botão para backup full (backup completo do sistema)
        btn_full = tk.Button(frame_botoes, text='Bkp Full', image=self.icon_backup_full, compound=tk.LEFT, command=self.backup_full)
        btn_full.pack(side=tk.LEFT, padx=5)

        # Botão para pesquisar arquivo pelo nome
        btn_pesq = tk.Button(frame_botoes, text='Pesq. arq.', image=self.icon_search, compound=tk.LEFT, command=self.pesquisar_arquivo)
        btn_pesq.pack(side=tk.LEFT, padx=5)

        # Botão para restaurar todos os arquivos de um backup completo
        btn_rest_full = tk.Button(frame_botoes, text='Restaurar bkp full', image=self.icon_restore, compound=tk.LEFT, command=self.restaurar_full)
        btn_rest_full.pack(side=tk.LEFT, padx=5)

        # Botão para abrir janela de configuração
        btn_config = tk.Button(frame_botoes, text='Config.', image=self.icon_config, compound=tk.LEFT, command=self.abrir_configuracoes)
        btn_config.pack(side=tk.LEFT, padx=5)

        # Campo de entrada para pesquisa de arquivos
        self.entry_pesquisa = tk.Entry(frame_botoes, width=30)
        self.entry_pesquisa.pack(side=tk.LEFT, padx=5)

        # Listbox para exibir arquivos/diretórios selecionados
        frame_lista = tk.Frame(root)
        frame_lista.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame_lista, text='Arquivos/Diretórios selecionados para backup:').pack(anchor='w')
        self.listbox = tk.Listbox(frame_lista, selectmode=tk.SINGLE, width=160, height=4)  # Aumenta largura
        self.listbox.pack(fill=tk.X, padx=5)

        # Barra de progresso
        self.progress = ttk.Progressbar(root, orient='horizontal', length=600, mode='determinate')
        self.progress.pack(pady=5)
        self.progress['value'] = 0
        self.progress_label = tk.Label(root, text='')
        self.progress_label.pack()

        # Treeview para exibir os arquivos/diretórios backupeados
        self.tree = ttk.Treeview(root, columns=('nome', 'data', 'tamanho', 'modo', 'restaurar'), show='headings')
        self.tree.heading('nome', text='Nome do Arquivo')
        self.tree.heading('data', text='Data do Backup')
        self.tree.heading('tamanho', text='Tamanho (bytes)')
        self.tree.heading('modo', text='Modo')
        self.tree.heading('restaurar', text='Restaurar')
        self.tree.column('nome', width=350)
        self.tree.column('data', width=200)
        self.tree.column('tamanho', width=120)
        self.tree.column('modo', width=120)
        self.tree.column('restaurar', width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Permite restaurar arquivo individual ao dar duplo clique na linha
        self.tree.bind('<Double-1>', self.on_tree_double_click)

        # Carrega todos os backups registrados ao iniciar a interface
        self.carregar_backups()

    # Atualiza a barra de progresso
    def atualizar_progresso(self, fracao, label=''):
        self.progress['value'] = fracao * 100
        self.progress_label.config(text=label)
        self.root.update_idletasks()

    # Reseta a barra de progresso
    def resetar_progresso(self):
        self.progress['value'] = 0
        self.progress_label.config(text='')
        self.root.update_idletasks()

    # Abre diálogo para o usuário selecionar arquivos/diretórios para backup personalizado
    def adicionar_arquivos(self):
        arquivos = filedialog.askopenfilenames(title='Selecione arquivos', initialdir=os.path.expanduser('~'))
        for arq in arquivos:
            if arq not in self.paths_selecionados:
                self.paths_selecionados.append(arq)
                self.listbox.insert(tk.END, arq)

    def adicionar_diretorios(self):
        while True:
            dir_path = filedialog.askdirectory(title='Selecione um diretório (cancelar para parar)',initialdir=os.path.expanduser('~'))
            if not dir_path:
                break
            if dir_path not in self.paths_selecionados:
                self.paths_selecionados.append(dir_path)
                self.listbox.insert(tk.END, dir_path)

    def remover_selecionado(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.listbox.delete(idx)
            del self.paths_selecionados[idx]

    def backup_selecionados(self):
        if not self.paths_selecionados:
            messagebox.showwarning('Atenção', 'Nenhum arquivo ou diretório selecionado!')
            return
        run_in_thread(self._backup_personalizado, list(self.paths_selecionados))

    # Executa o backup personalizado em thread separada
    def _backup_personalizado(self, paths):
        try:
            def progresso(fracao):
                self.atualizar_progresso(fracao, 'Enviando arquivo...')
            backup_personalizado(paths, progress_callback=progresso)
            self.resetar_progresso()
            messagebox.showinfo('Sucesso', 'Backup personalizado concluído!')
            self.carregar_backups()
        except Exception as e:
            self.resetar_progresso()
            messagebox.showerror('Erro', f'Erro no backup personalizado: {e}')

    # Inicia o backup full (com confirmação do usuário)
    def backup_full(self):
        if not messagebox.askyesno('Confirmação', 'Deseja realmente fazer backup completo do sistema?'):
            return
        run_in_thread(self._backup_full)

    # Executa o backup full em thread separada
    def _backup_full(self):
        try:
            def progresso(fracao):
                self.atualizar_progresso(fracao, 'Enviando arquivo (full)...')
            backup_full(progress_callback=progresso)
            self.resetar_progresso()
            messagebox.showinfo('Sucesso', 'Backup full concluído!')
            self.carregar_backups()
        except Exception as e:
            self.resetar_progresso()
            messagebox.showerror('Erro', f'Erro no backup full: {e}')

    # Pesquisa arquivos pelo nome ou parte do nome
    def pesquisar_arquivo(self):
        termo = self.entry_pesquisa.get().strip()
        if not termo:
            messagebox.showwarning('Atenção', 'Digite um nome para pesquisar.')
            return
        resultados = buscar_backups_por_nome(termo)
        self.carregar_backups(resultados)

    # Abre diálogo para selecionar pasta de destino e inicia restauração completa
    def restaurar_full(self):
        pasta = filedialog.askdirectory(title='Selecione a pasta para restaurar o backup completo')
        if not pasta:
            return
        run_in_thread(self._restaurar_full, pasta)

    # Executa a restauração completa em thread separada
    def _restaurar_full(self, pasta):
        try:
            def progresso(fracao):
                self.atualizar_progresso(fracao, 'Baixando arquivo (full)...')
            restaurar_backup_completo(pasta, progress_callback=progresso)
            self.resetar_progresso()
            messagebox.showinfo('Sucesso', 'Backup completo restaurado!')
        except Exception as e:
            self.resetar_progresso()
            messagebox.showerror('Erro', f'Erro ao restaurar backup completo: {e}')

    # Ao dar duplo clique em uma linha da Treeview, permite restaurar arquivo individual
    def on_tree_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        item = item[0]
        values = self.tree.item(item, 'values')
        nome_arquivo = values[0]
        id_drive = self.tree.set(item, '#5')  # O id_drive está oculto, mas pode ser adicionado se necessário
        # Solicita ao usuário onde salvar o arquivo restaurado
        destino = filedialog.asksaveasfilename(title=f'Restaurar {nome_arquivo} como', initialfile=nome_arquivo)
        if not destino:
            return
        # Busca o id_drive correto no banco (caso haja duplicidade)
        backups = buscar_backups_por_nome(nome_arquivo)
        for b in backups:
            if b[1] == nome_arquivo:
                id_drive = b[4]
                break
        run_in_thread(self._restaurar_arquivo, id_drive, destino)

    # Executa a restauração individual em thread separada
    def _restaurar_arquivo(self, id_drive, destino):
        try:
            def progresso(fracao):
                self.atualizar_progresso(fracao, 'Baixando arquivo...')
            restaurar_arquivo(id_drive, destino, progress_callback=progresso)
            self.resetar_progresso()
            messagebox.showinfo('Sucesso', f'Arquivo restaurado em: {destino}')
        except Exception as e:
            self.resetar_progresso()
            messagebox.showerror('Erro', f'Erro ao restaurar arquivo: {e}')

    # Carrega os backups na Treeview (pode receber uma lista de backups ou buscar todos)
    def carregar_backups(self, backups=None):
        # Limpa a Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Busca todos os backups se não for passado uma lista
        if backups is None:
            backups = listar_todos_backups()
        # Insere cada backup como uma linha na Treeview
        for b in backups:
            # b = (id, nome_arquivo, caminho_original, data_backup, id_drive, tamanho, modo_backup)
            self.tree.insert('', 'end', values=(b[1], b[3], b[5], b[6], b[4]))

    # Abre a janela de configurações
    def abrir_configuracoes(self):
        config_win = tk.Toplevel(self.root)
        config_win.title('Configurações')
        config_win.geometry('350x180')
        tk.Label(config_win, text='Configurações do Google Drive', font=('Arial', 12, 'bold')).pack(pady=10)
        # Status do token
        token_path = 'token.pickle'
        if os.path.exists(token_path):
            tk.Label(config_win, text='Token de autenticação: OK', fg='green').pack()
        else:
            tk.Label(config_win, text='Token de autenticação: NÃO ENCONTRADO', fg='red').pack()
        # Botão para resetar token
        def resetar_token():
            if os.path.exists(token_path):
                os.remove(token_path)
                messagebox.showinfo('Token', 'Token removido. Será solicitado novo login no próximo backup/restauração.')
                config_win.destroy()
            else:
                messagebox.showinfo('Token', 'Token já não existe.')
        btn_reset = tk.Button(config_win, text='Resetar token do Google Drive', command=resetar_token)
        btn_reset.pack(pady=10)
        # Botão para abrir pasta de logs
        def abrir_logs():
            logs_dir = os.path.abspath('logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            os.system(f'xdg-open "{logs_dir}"' if os.name == 'posix' else f'start {logs_dir}')
        btn_logs = tk.Button(config_win, text='Abrir pasta de logs', command=abrir_logs)
        btn_logs.pack(pady=5)

# Função principal para rodar o app
def main():
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()