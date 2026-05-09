from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
import pathlib
import requests as http_requests          # ← para chamar a API do Google Calendar
from datetime import datetime, timedelta
from urllib.parse import urlencode        # ← para gerar URL universal do Google Agenda

load_dotenv()

app = Flask(__name__)
app.secret_key = "2a962fb071252f38d97cafb2f3a84c80c49568ebb87bc1b1"

CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# =========================
# GOOGLE AUTH
# =========================
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        # ← ALTERADO: adicionado calendar.events ao scope
        "scope": "openid email profile https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",   # ← garante refresh_token (opcional mas recomendado)
        "prompt": "consent",        # ← força re-autorização para obter o token de calendar
    },
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
# ← NOVO: HELPER — CRIA EVENTO NO GOOGLE CALENDAR
# =========================
def gerar_url_google_agenda(titulo, data_str, horario, duracao_horas, prestador_nome, obs=""):
    """
    Gera a URL universal 'Adicionar ao Google Agenda' — funciona sem OAuth,
    qualquer usuário pode clicar e adicionar o evento à própria conta.
    """
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt   = start_dt + timedelta(hours=float(duracao_horas or 1))

        params = {
            "action" : "TEMPLATE",
            "text"   : f"Agendamento: {titulo}",
            "dates"  : f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}",
            "details": f"Prestador: {prestador_nome}\nObservações: {obs or '—'}\n\nAgendado via Agenda Fácil",
            "ctz"    : "America/Sao_Paulo",
        }
        return "https://calendar.google.com/calendar/render?" + urlencode(params)
    except Exception as e:
        print(f"[Calendar URL] Erro ao gerar URL: {e}")
        return None


def criar_evento_google_calendar(access_token, titulo, data_str, horario,
                                  duracao_horas, prestador_nome,
                                  cliente_email, prestador_email, obs=""):
    """
    Cria um evento no Google Calendar do usuário via API OAuth e envia
    convite automático para o e-mail do prestador.
    """
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt   = start_dt + timedelta(hours=float(duracao_horas or 1))

        evento = {
            "summary": f"Agendamento: {titulo}",
            "description": (
                f"Prestador: {prestador_nome}\n"
                f"Observações: {obs or '—'}\n\n"
                "Agendado via Agenda Fácil"
            ),
            "start": {
                "dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "America/Sao_Paulo",
            },
            "end": {
                "dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "America/Sao_Paulo",
            },
            # ← Envia convite para o prestador automaticamente
            "attendees": [
                {"email": cliente_email,   "displayName": "Cliente"},
                {"email": prestador_email, "displayName": prestador_nome},
            ],
            "guestsCanModify"     : False,
            "guestsCanSeeOtherGuests": True,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 1440},  # 24h antes
                    {"method": "popup",  "minutes": 60},    # 1h antes
                ],
            },
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        res = http_requests.post(
            # sendUpdates=all → Google envia e-mail de convite para os attendees
            "https://www.googleapis.com/calendar/v3/calendars/primary/events?sendUpdates=all",
            headers=headers,
            json=evento,
            timeout=8,
        )

        if res.status_code in (200, 201):
            print(f"[Calendar] Evento criado: {res.json().get('id')}")
            return True, res.json().get("htmlLink")
        else:
            print(f"[Calendar] Erro {res.status_code}: {res.text}")
            return False, None

    except Exception as e:
        print(f"[Calendar] Exceção ao criar evento: {e}")
        return False, None

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

    nome      = user_info.get("given_name", "")
    sobrenome = user_info.get("family_name", "")
    email     = user_info.get("email")

    # ← NOVO: guarda o access_token na sessão para usar no Calendar
    session["google_token"] = token.get("access_token")

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

@app.route("/orcamentos")
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
# AGENDAMENTO
# =========================
@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    dados = request.get_json()

    cliente_email   = session["usuario_logado"]
    prestador_email = dados.get("prestador_email")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nome, sobrenome FROM cadastro_clientes WHERE email = %s", (cliente_email,))
    cliente = cursor.fetchone()

    cursor.execute("SELECT nome, sobrenome, areas_atuacao FROM cadastro_prestadores WHERE email = %s", (prestador_email,))
    prestador_row = cursor.fetchone()

    # ← NOVO: busca duração do serviço para calcular fim do evento
    cursor.execute(
        "SELECT duracao FROM servicos_anunciados WHERE titulo = %s AND prestador_email = %s LIMIT 1",
        (dados.get("servico"), prestador_email)
    )
    servico_row = cursor.fetchone()
    duracao_horas = servico_row["duracao"] if servico_row else 1

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
        nome_prestador = f"{prestador_row['nome']} {prestador_row['sobrenome']}" if prestador_row else prestador_email

        # ── Gera URL universal (funciona para todos os usuários) ──
        calendar_url = gerar_url_google_agenda(
            titulo         = dados.get("servico", "Serviço"),
            data_str       = dados.get("data"),
            horario        = dados.get("horario"),
            duracao_horas  = duracao_horas,
            prestador_nome = nome_prestador,
            obs            = dados.get("obs", ""),
        )

        # ── Cria evento via API e envia convite ao prestador (login Google) ──
        google_token = session.get("google_token")
        if google_token:
            ok, api_link = criar_evento_google_calendar(
                access_token   = google_token,
                titulo         = dados.get("servico", "Serviço"),
                data_str       = dados.get("data"),
                horario        = dados.get("horario"),
                duracao_horas  = duracao_horas,
                prestador_nome = nome_prestador,
                cliente_email  = cliente_email,
                prestador_email= prestador_email,
                obs            = dados.get("obs", ""),
            )
            if not ok:
                print("[Calendar] Evento API não criado, mas URL universal gerada.")
        else:
            print("[Calendar] Login por senha — usando URL universal.")

        return jsonify({
            "mensagem"      : "Agendamento salvo!",
            "id"            : agendamento_id,
            "nome_cliente"  : nome_cliente,
            "nome_prestador": nome_prestador,
            "email_cliente" : cliente_email,
            "calendar_url"  : calendar_url,   # ← URL universal do Google Agenda
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

    return redirect(url_for("sucesso_servico", id=ag_id))

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
        "perfil-prestador.html",
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

    return render_template("perfil-cliente.html", cliente=cliente, agendamentos=agendamentos)

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
# API: HORÁRIOS BLOQUEADOS
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

    dados = request.get_json() or {}
    novo_status = dados.get("status")

    status_validos = ["pendente", "confirmado", "em_andamento", "concluido", "cancelado"]
    if novo_status not in status_validos:
        return jsonify({"erro": "Status inválido"}), 400

# =========================
# API: PRESTADORES POR CATEGORIA
# =========================
@app.route("/api/prestadores_por_categoria")
def prestadores_por_categoria():
    categoria = request.args.get("categoria", "").lower()
    if not categoria:
        return jsonify([])

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT nome, sobrenome, email
        FROM cadastro_prestadores
        WHERE LOWER(areas_atuacao) LIKE %s
    """, (f"%{categoria}%",))

    dados = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(dados)

# =========================
# UPLOAD DE FOTO DE PERFIL
# =========================
UPLOAD_FOLDER = os.path.join("static", "uploads", "fotos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/salvar_foto", methods=["POST"])
def salvar_foto():
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    file = request.files.get("foto")
    if not file or not allowed_file(file.filename):
        return jsonify({"erro": "Arquivo inválido. Use PNG, JPG ou WEBP."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    email_safe = session["usuario_logado"].replace("@", "_").replace(".", "_")
    filename = f"{email_safe}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    url = "/" + filepath.replace("\\", "/")

    conn = connectar()
    cursor = conn.cursor()
    tipo = session.get("tipo_usuario", "cliente")

    if tipo == "prestador":
        cursor.execute("UPDATE cadastro_prestadores SET foto = %s WHERE email = %s",
                       (url, session["usuario_logado"]))
    else:
        cursor.execute("UPDATE cadastro_clientes SET foto = %s WHERE email = %s",
                       (url, session["usuario_logado"]))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"mensagem": "Foto salva!", "url": url})

# =========================
# UPLOAD DE CERTIFICADO (PRESTADOR)
# =========================
CERT_FOLDER = os.path.join("static", "uploads", "certificados")
os.makedirs(CERT_FOLDER, exist_ok=True)
ALLOWED_CERT = {"pdf", "png", "jpg", "jpeg"}

@app.route("/salvar_certificado", methods=["POST"])
def salvar_certificado():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    file = request.files.get("certificado")
    if not file:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_CERT:
        return jsonify({"erro": "Use PDF, PNG ou JPG"}), 400

    import time
    email_safe = session["usuario_logado"].replace("@", "_").replace(".", "_")
    filename = f"{email_safe}_{int(time.time())}.{ext}"
    filepath = os.path.join(CERT_FOLDER, filename)
    file.save(filepath)

    url = "/" + filepath.replace("\\", "/")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT certificados FROM cadastro_prestadores WHERE email = %s",
                   (session["usuario_logado"],))
    row = cursor.fetchone()
    existentes = row["certificados"] or "" if row else ""
    novos = (existentes + "," + url).strip(",")

    cursor.execute("UPDATE cadastro_prestadores SET certificados = %s WHERE email = %s",
                   (novos, session["usuario_logado"]))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"mensagem": "Certificado salvo!", "url": url})

# =========================
# EDITAR PERFIL CLIENTE
# =========================
@app.route("/editar_perfil_cliente", methods=["POST"])
def editar_perfil_cliente():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "cliente":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json()
    nome      = dados.get("nome", "").strip()
    sobrenome = dados.get("sobrenome", "").strip()
    telefone  = dados.get("telefone", "").strip()
    cidade    = dados.get("cidade", "").strip()
    sexo      = dados.get("sexo", "").strip()

    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cadastro_clientes
        SET nome = %s, sobrenome = %s, telefone = %s, cidade = %s, sexo = %s
        WHERE email = %s
    """, (nome, sobrenome, telefone, cidade, sexo, session["usuario_logado"]))
    conn.commit()
    cursor.close()
    conn.close()

    session["usuario_nome"] = nome + " " + sobrenome
    return jsonify({"mensagem": "Perfil atualizado!"})

# =========================
# EDITAR PERFIL PRESTADOR
# =========================
@app.route("/editar_perfil_prestador", methods=["POST"])
def editar_perfil_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json()
    nome      = dados.get("nome", "").strip()
    sobrenome = dados.get("sobrenome", "").strip()
    telefone  = dados.get("telefone", "").strip()
    cidade    = dados.get("cidade", "").strip()
    bio       = dados.get("bio", "").strip()
    sexo      = dados.get("sexo", "").strip()

    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cadastro_prestadores
        SET nome = %s, sobrenome = %s, telefone = %s, cidade = %s, bio = %s, sexo = %s
        WHERE email = %s
    """, (nome, sobrenome, telefone, cidade, bio, sexo, session["usuario_logado"]))
    conn.commit()
    cursor.close()
    conn.close()

    session["usuario_nome"] = nome + " " + sobrenome
    return jsonify({"mensagem": "Perfil atualizado!"})

load_dotenv(dotenv_path=pathlib.Path(__file__).parent / ".env", override=True)

@app.route("/sucesso-agendamento")
def sucesso_servico():
    return render_template("sucesso.html")

@app.route("/sucesso-conclusao")
def sucesso_conclusao():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))
    return render_template("sucesso_conclusao.html")


# =========================
if __name__ == "__main__":
    app.run(debug=True)