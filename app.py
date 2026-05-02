from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "2a962fb071252f38d97cafb2f3a84c80c49568ebb87bc1b1"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# =========================
# GOOGLE AUTH
# =========================
oauth = OAuth(app)
google = oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# =========================
# BANCO DE DADOS
# =========================
def connectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="servicos"
    )

# =========================
# GOOGLE LOGIN
# =========================
@app.route("/login-google")
def login_google():
    redirect_uri = "http://127.0.0.1:5000/callback"
    return google.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info:
        return render_template("login.html", erro="Erro ao obter dados do Google.")

    nome     = user_info.get("given_name", "")
    sobrenome = user_info.get("family_name", "")
    email    = user_info.get("email")

    conn   = connectar()
    cursor = conn.cursor(dictionary=True)

    # Verifica se já existe como prestador
    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email = %s", (email,))
    prestador = cursor.fetchone()

    if prestador:
        session["usuario_logado"] = email
        session["tipo_usuario"]   = "prestador"
        session["usuario_nome"]   = prestador["nome"] + " " + prestador["sobrenome"]
        cursor.close()
        conn.close()
        return redirect(url_for("servicos"))

    # Verifica se já existe como cliente
    cursor.execute("SELECT * FROM cadastro_clientes WHERE email = %s", (email,))
    cliente = cursor.fetchone()

    if not cliente:
        # Novo usuário: cria conta de cliente
        try:
            cursor.execute(
                "INSERT INTO cadastro_clientes (nome, sobrenome, email) VALUES (%s, %s, %s)",
                (nome, sobrenome, email)
            )
            conn.commit()
        except Exception as e:
            print("Erro ao criar conta Google:", e)

    cursor.close()
    conn.close()

    session["usuario_logado"] = email
    session["tipo_usuario"]   = "cliente"
    session["usuario_nome"]   = nome + " " + sobrenome
    return redirect(url_for("servicos"))

# =========================
# PÁGINAS
# =========================
@app.route("/")
def index():
    return render_template("principal.html")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/servicos")
def servicos():
    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, p.nome, p.sobrenome, p.areas_atuacao
        FROM servicos_anunciados s
        JOIN cadastro_prestadores p ON s.prestador_email = p.email
        ORDER BY s.id DESC
    """)
    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("servicos.html", servicos=lista)

@app.route("/perfil")
def perfil():
    return render_template("cliente.html")

@app.route("/prestador")
def prestador():
    return render_template("prestador.html")

@app.route("/orcamento")
def orcamento():
    return render_template("orcamentos.html")

@app.route("/painel")
def painel():
    return render_template("painel.html")

@app.route("/formulario")
def formulario():
    return render_template("formulario.html")

@app.route("/agendamentos")
def agendamentos():
    return render_template("agendamento.html")

# =========================
# AUTENTICAÇÃO
# =========================
@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form["email"]
    senha = request.form["senha"]

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    # prestador
    cursor.execute(
        "SELECT * FROM cadastro_prestadores WHERE email=%s AND senha=%s",
        (email, senha)
    )
    prestador = cursor.fetchone()

    if prestador:
        session["usuario_logado"] = email
        session["tipo_usuario"] = "prestador"
        session["usuario_nome"] = prestador["nome"] + " " + prestador["sobrenome"]
        cursor.close()
        conn.close()
        return redirect(url_for("servicos"))

    # cliente
    cursor.execute(
        "SELECT * FROM cadastro_clientes WHERE email=%s AND senha=%s",
        (email, senha)
    )
    cliente = cursor.fetchone()

    cursor.close()
    conn.close()

    if cliente:
        session["usuario_logado"] = email
        session["tipo_usuario"] = "cliente"
        session["usuario_nome"] = cliente["nome"] + " " + cliente["sobrenome"]
        return redirect(url_for("servicos"))

    return render_template("login.html", erro="E-mail ou senha inválidos")

# =========================
# CADASTRO CLIENTE
# =========================
@app.route("/salvar", methods=["POST"])
def salvar():
    dados = (
        request.form["nome"],
        request.form["sobrenome"],
        request.form["data_nascimento"],
        request.form["sexo"],
        request.form["email"],
        request.form["senha"]
    )

    conn = connectar()
    cursor = conn.cursor()

    sql = """
    INSERT INTO cadastro_clientes
    (nome, sobrenome, data_nascimento, sexo, email, senha)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, dados)
        conn.commit()
        return redirect(url_for("index"))
    except Exception as e:
        return render_template("cadastro.html", erro=str(e))
    finally:
        cursor.close()
        conn.close()

# =========================
# CADASTRO PRESTADOR
# =========================
@app.route("/salvar_prestador", methods=["POST"])
def salvar_prestador():
    dados = (
        request.form["nome"],
        request.form["sobrenome"],
        request.form["data_nascimento"],
        request.form["sexo"],
        request.form["email"],
        request.form["senha"],
        request.form["areas_atuacao"]
    )

    conn = connectar()
    cursor = conn.cursor()

    sql = """
    INSERT INTO cadastro_prestadores
    (nome, sobrenome, data_nascimento, sexo, email, senha, areas_atuacao)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, dados)
        conn.commit()
        return redirect(url_for("index"))
    except Exception as e:
        return render_template("prestador.html", erro=str(e))
    finally:
        cursor.close()
        conn.close()

# =========================
# AGENDAMENTO (CORRIGIDO)
# =========================
@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    dados = request.get_json()

    cliente_email = session["usuario_logado"]
    prestador_email = dados.get("prestador_email")

    # Busca nome do cliente e do prestador para o email
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nome, sobrenome FROM cadastro_clientes WHERE email = %s", (cliente_email,))
    cliente = cursor.fetchone()

    cursor.execute("SELECT nome, sobrenome FROM cadastro_prestadores WHERE email = %s", (prestador_email,))
    prestador = cursor.fetchone()

    valores = (
        cliente_email,
        prestador_email,
        dados.get("servico"),
        dados.get("preco"),
        dados.get("data"),
        dados.get("horario"),
        dados.get("obs", ""),
    )

    sql = """
    INSERT INTO agendamentos
    (cliente_email, prestador_email, servico, preco, data_servico, horario, observacoes)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, valores)
        conn.commit()
        agendamento_id = cursor.lastrowid

        nome_cliente   = f"{cliente['nome']} {cliente['sobrenome']}" if cliente else cliente_email
        nome_prestador = f"{prestador['nome']} {prestador['sobrenome']}" if prestador else prestador_email

        return jsonify({
            "mensagem": "Agendamento salvo!",
            "id": agendamento_id,
            "nome_cliente": nome_cliente,
            "nome_prestador": nome_prestador,
            "email_cliente": cliente_email,
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# SERVIÇOS PRESTADOR
# =========================
@app.route("/salvar_servico_prestador", methods=["POST"])
def salvar_servico_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json()

    valores = (
        session["usuario_logado"],
        dados.get("titulo"),
        dados.get("descricao"),
        dados.get("preco"),
        dados.get("categoria"),
        dados.get("duracao")
    )

    conn = connectar()
    cursor = conn.cursor()

    sql = """
    INSERT INTO servicos_anunciados
    (prestador_email, titulo, descricao, preco, area_atuacao, duracao)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, valores)
        conn.commit()
        return jsonify({"mensagem": "Serviço criado!"})
    except Exception as e:
        return jsonify({"erro": str(e)})
    finally:
        cursor.close()
        conn.close()

# =========================
# API SERVIÇOS
# =========================
@app.route("/api/listar_servicos")
def listar_servicos():
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.*, p.nome, p.sobrenome, p.areas_atuacao
        FROM servicos_anunciados s
        JOIN cadastro_prestadores p
        ON s.prestador_email = p.email
        ORDER BY s.id DESC
    """)

    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(dados)

# =========================
# MEUS SERVIÇOS
# =========================
@app.route("/api/meus_servicos")
def meus_servicos():
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM servicos_anunciados WHERE prestador_email=%s",
        (session["usuario_logado"],)
    )

    dados = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(dados)

# =========================
# EXCLUIR SERVIÇO
# =========================
@app.route("/api/excluir_servico/<int:id>", methods=["DELETE"])
def excluir_servico(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    conn = connectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM servicos_anunciados WHERE id=%s AND prestador_email=%s",
        (id, session["usuario_logado"])
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"mensagem": "ok"})

# =========================
# CONFIRMAÇÃO DE AGENDAMENTO
# =========================
@app.route("/agendamento_confirmado")
def agendamento_confirmado():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    ag_id = request.args.get("id")
    if not ag_id:
        return redirect(url_for("servicos"))

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome,
               c.nome AS cliente_nome, c.sobrenome AS cliente_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_prestadores p ON a.prestador_email = p.email
        LEFT JOIN cadastro_clientes c ON a.cliente_email = c.email
        WHERE a.id = %s AND a.cliente_email = %s
    """, (ag_id, session["usuario_logado"]))

    ag = cursor.fetchone()
    cursor.close()
    conn.close()

    if not ag:
        return redirect(url_for("servicos"))

    return render_template("agendamento_confirmado.html", ag=ag)

# =========================
# PERFIL DO PRESTADOR
# =========================
@app.route("/perfil_prestador/<email>")
def perfil_prestador(email):
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email = %s", (email,))
    prestador = cursor.fetchone()

    if not prestador:
        cursor.close()
        conn.close()
        return "Prestador não encontrado", 404

    cursor.execute(
        "SELECT * FROM servicos_anunciados WHERE prestador_email = %s ORDER BY id DESC",
        (email,)
    )
    servicos = cursor.fetchall()

    cursor.execute("""
        SELECT a.*, c.nome AS cliente_nome, c.sobrenome AS cliente_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_clientes c ON a.cliente_email = c.email
        WHERE a.prestador_email = %s AND a.status NOT IN ('cancelado','concluido')
        ORDER BY a.data_servico ASC, a.horario ASC
    """, (email,))
    agendamentos_pendentes = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM agendamentos WHERE prestador_email = %s AND status = 'concluido'",
        (email,)
    )
    row = cursor.fetchone()
    agendamentos_count = row["total"] if row else 0

    cursor.close()
    conn.close()

    return render_template(
        "perfil_prestador.html",
        prestador=prestador,
        servicos=servicos,
        agendamentos_pendentes=agendamentos_pendentes,
        agendamentos_count=agendamentos_count
    )

# =========================
# PERFIL DO CLIENTE
# =========================
@app.route("/perfil_cliente")
def perfil_cliente():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM cadastro_clientes WHERE email = %s",
        (session["usuario_logado"],)
    )
    cliente = cursor.fetchone()

    cursor.execute("""
        SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_prestadores p ON a.prestador_email = p.email
        WHERE a.cliente_email = %s
        ORDER BY a.data_servico DESC
    """, (session["usuario_logado"],))
    agendamentos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("perfil_cliente.html", cliente=cliente, agendamentos=agendamentos)

# =========================
# PERFIL DO PRESTADOR LOGADO
# =========================
@app.route("/meu_perfil")
def meu_perfil():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))

    if session.get("tipo_usuario") == "prestador":
        return redirect(url_for("perfil_prestador", email=session["usuario_logado"]))
    else:
        return redirect(url_for("perfil_cliente"))

# =========================
# API: HORÁRIOS BLOQUEADOS POR DATA E PRESTADOR
# =========================
@app.route("/api/horarios_bloqueados")
def horarios_bloqueados():
    data = request.args.get("data")
    prestador_email = request.args.get("prestador_email")

    if not data or not prestador_email:
        return jsonify([])

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT horario FROM agendamentos
        WHERE data_servico = %s
        AND prestador_email = %s
        AND status NOT IN ('cancelado')
    """, (data, prestador_email))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    horarios = [r["horario"] for r in rows]
    return jsonify(horarios)

# =========================
# CANCELAR AGENDAMENTO (CLIENTE)
# =========================
@app.route("/api/cancelar_agendamento/<int:id>", methods=["PATCH"])
def cancelar_agendamento(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    conn = connectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agendamentos SET status = 'cancelado'
        WHERE id = %s AND cliente_email = %s
    """, (id, session["usuario_logado"]))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"mensagem": "Agendamento cancelado"})

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# =========================
# AGENDAMENTOS DO CLIENTE
# =========================
@app.route("/api/meus_agendamentos")
def meus_agendamentos():
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_prestadores p ON a.prestador_email = p.email
        WHERE a.cliente_email = %s
        ORDER BY a.data_servico DESC, a.horario DESC
    """, (session["usuario_logado"],))

    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(dados)

# =========================
# AGENDAMENTOS DO PRESTADOR
# =========================
@app.route("/api/agendamentos_prestador")
def agendamentos_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.*, c.nome AS cliente_nome, c.sobrenome AS cliente_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_clientes c ON a.cliente_email = c.email
        WHERE a.prestador_email = %s
        ORDER BY a.data_servico DESC, a.horario DESC
    """, (session["usuario_logado"],))

    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(dados)

# =========================
# ATUALIZAR STATUS DO AGENDAMENTO
# =========================
@app.route("/api/atualizar_status/<int:id>", methods=["PATCH"])
def atualizar_status(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    dados = request.get_json()
    novo_status = dados.get("status")

    status_validos = ["pendente", "confirmado", "em_andamento", "concluido", "cancelado"]
    if novo_status not in status_validos:
        return jsonify({"erro": "Status inválido"}), 400

    conn = connectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agendamentos SET status = %s
        WHERE id = %s AND prestador_email = %s
    """, (novo_status, id, session["usuario_logado"]))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"mensagem": "Status atualizado!"})

# =========================
if __name__ == "__main__":
    app.run(debug=True)