import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2

# CONFIGURAÇÕES DO BANCO
DB_NAME = "CARONA"      
DB_USER = "paulo"        
DB_PASSWORD = "5678"       
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def motoristas_com_nota_maior(nota_min):
    conn = get_connection()
    query = """
        SELECT m.CPF, u.Nome, u.Nota_media
        FROM Motorista m
        JOIN Usuario u ON u.CPF = m.CPF
        WHERE u.Nota_media > %s;
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (nota_min,))
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def usuarios_em_todas_viagens_rota(id_rota):
    conn = get_connection()
    query = """
        SELECT upv.CPF, u.Nome
        FROM Usuario_participa_viagem upv
        JOIN Usuario u ON u.CPF = upv.CPF
        WHERE upv.ID_Viagem IN (
            SELECT v.ID_Viagem FROM Viagem v WHERE v.ID_rota = %s
        )
        AND upv.CPF != (
            SELECT r.CPF FROM Rota r WHERE r.ID_rota = %s
        )
        GROUP BY upv.CPF, u.Nome
        HAVING COUNT(DISTINCT upv.ID_Viagem) = (
            SELECT COUNT(*) FROM Viagem v WHERE v.ID_rota = %s
        );
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (id_rota, id_rota, id_rota))
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def ofertas_por_status(status):
    conn = get_connection()
    query = """
        SELECT o.ID_oferta, o.Valor, o.Inicio, o.Fim, o.Status, u.Nome AS Motorista
        FROM Oferta o
        JOIN Viagem v ON v.ID_Viagem = o.ID_Viagem
        JOIN Rota r ON r.ID_rota = v.ID_rota
        JOIN Motorista m ON m.CPF = o.CPF
        JOIN Usuario u ON u.CPF = m.CPF
        WHERE o.Status = %s
        ORDER BY o.id_oferta;
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (status,))
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def usuarios_com_mais_de_n_avaliacoes(n):
    conn = get_connection()
    query = """
        SELECT u.CPF, u.Nome, ROUND(AVG(a.Nota),2) AS media_avaliacao, COUNT(*) AS qtd_avaliacoes
        FROM Usuario u
        JOIN Avaliacao a ON a.cpf_avaliado = u.CPF
        GROUP BY u.CPF, u.Nome
        HAVING COUNT(*) > %s
        ORDER BY media_avaliacao DESC;
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (n,))
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def motoristas_para_destino_e_nota(destino, nota_min):
    conn = get_connection()
    query = """
        SELECT
            u.Nome AS Nome_Motorista,
            u.Nota_media,
            m.Modelo_Carro,
            r.local_inicio,
            r.horario_inicio
        FROM Usuario u
        INNER JOIN Motorista m ON u.CPF = m.CPF
        INNER JOIN Rota r ON m.CPF = r.CPF
        WHERE
            r.local_fim = %s
            AND u.Nota_media > %s
            AND r.Tipo = 'periodica'
        ORDER BY nota_media DESC;
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (destino, nota_min))
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def consultar_visao_motorista():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM vw_motorista_avaliacoes")
        colnames = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        return colnames, dados
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return [], []
    finally:
        conn.close()

def inserir_avaliacao(data, nota, cpf_avaliador, cpf_avaliado, id_viagem):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Avaliacao(data, nota, cpf_avaliador, cpf_avaliado, id_viagem) VALUES (%s, %s, %s, %s, %s)",
            (data, nota, cpf_avaliador, cpf_avaliado, id_viagem)
        )
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return False
    finally:
        conn.close()

def remover_usuario(cpf):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Motorista WHERE CPF = %s", (cpf,))
        cur.execute("DELETE FROM Usuario WHERE CPF = %s", (cpf,))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        return False
    finally:
        conn.close()

def adicionar_motorista(cpf, nome, nota_media, modelo_carro, placa_carro, ano_carro):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"CALL adicionar_motorista('{cpf}', '{nome}', {nota_media}, '{modelo_carro}', '{placa_carro}', {ano_carro})", )
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        print(str(e))
        return False
    finally:
        conn.close()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão de Viagens - Consultas Dinâmicas")
        self.geometry("1000x720")
        self.create_widgets()

    def create_widgets(self):
        self.tabs = ttk.Notebook(self)
        self.tab_consultas = ttk.Frame(self.tabs)
        self.tab_inserir = ttk.Frame(self.tabs)
        self.tab_remover = ttk.Frame(self.tabs)
        self.tab_visao = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_consultas, text="Consultas Dinâmicas")
        self.tabs.add(self.tab_inserir, text="Inserir")
        self.tabs.add(self.tab_remover, text="Remover Usuário")
        self.tabs.add(self.tab_visao, text="Visão Motoristas")
        self.tabs.pack(expand=1, fill="both")

        # CONSULTAS DINÂMICAS
        self.consulta_tipo = ttk.Combobox(
            self.tab_consultas,
            values=[
                "Motoristas com nota acima de X",
                "Usuários em todas viagens de uma rota",
                "Ofertas por status",
                "Usuários avaliados mais de N vezes",
                "Motoristas para destino com nota mínima"
            ],
            width=60
        )
        self.consulta_tipo.pack(pady=10)
        self.param_frame = tk.Frame(self.tab_consultas)
        self.param_frame.pack()
        self.btn_param = tk.Button(self.tab_consultas, text="Gerar parâmetros", command=self.gerar_parametros)
        self.btn_param.pack(pady=5)
        self.btn_consultar = tk.Button(self.tab_consultas, text="Consultar", command=self.consultar_dinamica)
        self.btn_consultar.pack(pady=10)
        self.result_tree = ttk.Treeview(self.tab_consultas)
        self.result_tree.pack(expand=1, fill="both", pady=20)

        # Inserir avaliação
        tk.Label(self.tab_inserir, text="Inserir Avaliação").pack()
        self.form_frame = tk.Frame(self.tab_inserir)
        self.form_frame.pack(pady=10)
        self.inserir_campos = {}
        for i, rotulo in enumerate(["Data (YYYY-MM-DD)", "Nota", "CPF Avaliador", "CPF Avaliado", "ID Viagem"]):
            lbl = tk.Label(self.form_frame, text=rotulo)
            lbl.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            ent = tk.Entry(self.form_frame)
            ent.grid(row=i, column=1, padx=5, pady=5)
            self.inserir_campos[rotulo] = ent
        self.btn_inserir_avaliacao = tk.Button(self.form_frame, text="Inserir Avaliação", command=self.inserir_avaliacao)
        self.btn_inserir_avaliacao.grid(row=5, column=0, columnspan=2, pady=10)

        # Inserir Motorista
        tk.Label(self.tab_inserir, text="Inserir Motorista (Procedure)").pack()
        self.form_motorista = tk.Frame(self.tab_inserir)
        self.form_motorista.pack(pady=10)
        self.motorista_campos = {}
        motorista_labels = ["CPF", "Nome", "Nota Média", "Modelo Carro", "Placa Carro", "Ano Carro"]
        for i, rotulo in enumerate(motorista_labels):
            lbl = tk.Label(self.form_motorista, text=rotulo)
            lbl.grid(row=i, column=0, sticky="e", padx=5, pady=5)
            ent = tk.Entry(self.form_motorista)
            ent.grid(row=i, column=1, padx=5, pady=5)
            self.motorista_campos[rotulo] = ent
        self.btn_inserir_motorista = tk.Button(self.form_motorista, text="Inserir Motorista", command=self.inserir_motorista)
        self.btn_inserir_motorista.grid(row=6, column=0, columnspan=2, pady=10)

        # Remover usuário
        tk.Label(self.tab_remover, text="Remover Usuário por CPF").pack(pady=10)
        self.cpf_entry = tk.Entry(self.tab_remover, width=30)
        self.cpf_entry.pack(pady=5)
        self.btn_remover = tk.Button(self.tab_remover, text="Remover", command=self.remover_usuario)
        self.btn_remover.pack(pady=10)

        # Visão de Motoristas
        tk.Label(self.tab_visao, text="vw_motorista_avaliacoes").pack(pady=10)
        self.btn_visao = tk.Button(self.tab_visao, text="Consultar Visão", command=self.consultar_visao)
        self.btn_visao.pack()
        self.result_tree_visao = ttk.Treeview(self.tab_visao)
        self.result_tree_visao.pack(expand=1, fill="both", pady=20)

    def gerar_parametros(self):
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        tipo = self.consulta_tipo.get()
        self.param_inputs = {}
        if tipo == "Motoristas com nota acima de X":
            tk.Label(self.param_frame, text="Nota mínima:").pack(side="left")
            ent = tk.Entry(self.param_frame)
            ent.pack(side="left")
            self.param_inputs["nota_min"] = ent
        elif tipo == "Usuários em todas viagens de uma rota":
            tk.Label(self.param_frame, text="ID da rota:").pack(side="left")
            ent = tk.Entry(self.param_frame)
            ent.pack(side="left")
            self.param_inputs["id_rota"] = ent
        elif tipo == "Ofertas por status":
            tk.Label(self.param_frame, text="Status (Aberta/Fechada/Cancelada):").pack(side="left")
            ent = tk.Entry(self.param_frame)
            ent.pack(side="left")
            self.param_inputs["status"] = ent
        elif tipo == "Usuários avaliados mais de N vezes":
            tk.Label(self.param_frame, text="Quantidade N:").pack(side="left")
            ent = tk.Entry(self.param_frame)
            ent.pack(side="left")
            self.param_inputs["n"] = ent
        elif tipo == "Motoristas para destino com nota mínima":
            tk.Label(self.param_frame, text="Destino:").pack(side="left")
            ent_dest = tk.Entry(self.param_frame)
            ent_dest.pack(side="left")
            self.param_inputs["destino"] = ent_dest
            tk.Label(self.param_frame, text="Nota mínima:").pack(side="left")
            ent_nota = tk.Entry(self.param_frame)
            ent_nota.pack(side="left")
            self.param_inputs["nota_min"] = ent_nota

    def consultar_dinamica(self):
        tipo = self.consulta_tipo.get()
        if tipo == "Motoristas com nota acima de X":
            nota_min = self.param_inputs["nota_min"].get()
            colnames, dados = motoristas_com_nota_maior(float(nota_min))
        elif tipo == "Usuários em todas viagens de uma rota":
            id_rota = self.param_inputs["id_rota"].get()
            colnames, dados = usuarios_em_todas_viagens_rota(int(id_rota))
        elif tipo == "Ofertas por status":
            status = self.param_inputs["status"].get()
            colnames, dados = ofertas_por_status(status)
        elif tipo == "Usuários avaliados mais de N vezes":
            n = self.param_inputs["n"].get()
            colnames, dados = usuarios_com_mais_de_n_avaliacoes(int(n))
        elif tipo == "Motoristas para destino com nota mínima":
            destino = self.param_inputs["destino"].get()
            nota_min = self.param_inputs["nota_min"].get()
            colnames, dados = motoristas_para_destino_e_nota(destino, float(nota_min))
        else:
            messagebox.showwarning("Atenção", "Selecione uma consulta.")
            return
        self.result_tree.delete(*self.result_tree.get_children())
        self.result_tree["columns"] = colnames
        self.result_tree["show"] = "headings"
        for col in colnames:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=130)
        for row in dados:
            self.result_tree.insert("", "end", values=row)

    def inserir_avaliacao(self):
        vals = [self.inserir_campos[campo].get() for campo in self.inserir_campos]
        if inserir_avaliacao(*vals):
            messagebox.showinfo("Sucesso", "Avaliação inserida com sucesso!")

    def inserir_motorista(self):
        vals = [self.motorista_campos[campo].get() for campo in self.motorista_campos]
        if adicionar_motorista(*vals):
            messagebox.showinfo("Sucesso", "Motorista inserido com sucesso!")

    def remover_usuario(self):
        cpf = self.cpf_entry.get()
        if remover_usuario(cpf):
            messagebox.showinfo("Sucesso", "Usuário removido com sucesso!")
        else:
            messagebox.showwarning("Erro", "Usuário não encontrado ou não pôde ser removido.")

    def consultar_visao(self):
        colnames, dados = consultar_visao_motorista()
        self.result_tree_visao.delete(*self.result_tree_visao.get_children())
        self.result_tree_visao["columns"] = colnames
        self.result_tree_visao["show"] = "headings"
        for col in colnames:
            self.result_tree_visao.heading(col, text=col, anchor='center')
            self.result_tree_visao.column(col, width=130, anchor='center')
        for row in dados:
            self.result_tree_visao.insert("", 'end', values=row)

if __name__ == "__main__":
    app = App()
    app.mainloop()
