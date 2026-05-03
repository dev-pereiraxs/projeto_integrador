from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
import bcrypt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

# =========================
# EMAIL via Brevo SMTP
# =========================
BREVO_SMTP_HOST  = "smtp-relay.brevo.com"
BREVO_SMTP_PORT  = 587
BREVO_SMTP_LOGIN = os.getenv("BREVO_SMTP_LOGIN")   # email da SUA CONTA no Brevo
BREVO_SMTP_PASS  = os.getenv("BREVO_API_KEY")       # xsmtpsib-...
EMAIL_REMETENTE  = os.getenv("EMAIL_REMETENTE")     # agendafacilintegrador@gmail.com

def enviar_email(destinatario, assunto, corpo_html):
    print(f"[EMAIL] ── TENTATIVA ──────────────────────")
    print(f"[EMAIL] Para    : {destinatario}")
    print(f"[EMAIL] Assunto : {assunto}")
    print(f"[EMAIL] Login   : {BREVO_SMTP_LOGIN}")
    print(f"[EMAIL] From    : {EMAIL_REMETENTE}")

    if not destinatario or not BREVO_SMTP_PASS or not BREVO_SMTP_LOGIN:
        print("[EMAIL] ⚠️  BREVO_SMTP_LOGIN, BREVO_API_KEY ou destinatário ausente no .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = f"Agenda Fácil <{EMAIL_REMETENTE}>"
        msg["To"]      = destinatario
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        with smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(BREVO_SMTP_LOGIN, BREVO_SMTP_PASS)  # login = conta Brevo
            smtp.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())

        print("[EMAIL] ✅ Enviado com sucesso!")
        return True

    except Exception as e:
        print(f"[EMAIL] ❌ {type(e).__name__}: {e}")
        return False

app = Flask(__name__)
app.secret_key = "2a962fb071252f38d97cafb2f3a84c80c49568ebb87bc1b1"

CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# =========================
# GOOGLE AUTH
# =========================
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
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

    nome      = user_info.get("given_name", "")
    sobrenome = user_info.get("family_name", "")
    email     = user_info.get("email")
    foto      = user_info.get("picture", "")   # ← foto do Google

    conn   = connectar()
    cursor = conn.cursor(dictionary=True)

    # Verifica se já existe como prestador
    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email = %s", (email,))
    prestador = cursor.fetchone()

    if prestador:
        # Atualiza foto se tiver
        if foto:
            cursor.execute("UPDATE cadastro_prestadores SET foto_url = %s WHERE email = %s", (foto, email))
            conn.commit()
        session["usuario_logado"] = email
        session["tipo_usuario"]   = "prestador"
        session["usuario_nome"]   = prestador["nome"] + " " + prestador["sobrenome"]
        session["usuario_foto"]   = foto
        cursor.close()
        conn.close()
        return redirect(url_for("servicos"))

    # Verifica se já existe como cliente
    cursor.execute("SELECT * FROM cadastro_clientes WHERE email = %s", (email,))
    cliente = cursor.fetchone()

    if not cliente:
        try:
            cursor.execute(
                "INSERT INTO cadastro_clientes (nome, sobrenome, email, foto_url) VALUES (%s, %s, %s, %s)",
                (nome, sobrenome, email, foto)
            )
            conn.commit()
        except Exception as e:
            print("Erro ao criar conta Google:", e)
    else:
        # Atualiza foto se tiver
        if foto:
            cursor.execute("UPDATE cadastro_clientes SET foto_url = %s WHERE email = %s", (foto, email))
            conn.commit()

    cursor.close()
    conn.close()

    session["usuario_logado"] = email
    session["tipo_usuario"]   = "cliente"
    session["usuario_nome"]   = nome + " " + sobrenome
    session["usuario_foto"]   = foto
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
def verificar_senha(senha_bytes, hash_salvo):
    """Verifica bcrypt com proteção contra hash inválido/corrompido."""
    try:
        if isinstance(hash_salvo, str):
            hash_salvo = hash_salvo.encode("utf-8")
        if not hash_salvo.startswith(b"$2b$") and not hash_salvo.startswith(b"$2a$"):
            return False
        return bcrypt.checkpw(senha_bytes, hash_salvo)
    except Exception:
        return False

@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form["email"]
    senha = request.form["senha"].encode("utf-8")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    # prestador
    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email=%s", (email,))
    prestador = cursor.fetchone()

    if prestador and prestador["senha"] and verificar_senha(senha, prestador["senha"]):
        session["usuario_logado"] = email
        session["tipo_usuario"]   = "prestador"
        session["usuario_nome"]   = prestador["nome"] + " " + prestador["sobrenome"]
        session["usuario_foto"]   = prestador.get("foto_url", "")
        cursor.close()
        conn.close()
        return redirect(url_for("servicos"))

    # cliente
    cursor.execute("SELECT * FROM cadastro_clientes WHERE email=%s", (email,))
    cliente = cursor.fetchone()

    if cliente and cliente["senha"] and verificar_senha(senha, cliente["senha"]):
        session["usuario_logado"] = email
        session["tipo_usuario"]   = "cliente"
        session["usuario_nome"]   = cliente["nome"] + " " + cliente["sobrenome"]
        session["usuario_foto"]   = cliente.get("foto_url", "")
        cursor.close()
        conn.close()
        return redirect(url_for("servicos"))

    cursor.close()
    conn.close()
    return render_template("login.html", erro="E-mail ou senha inválidos")

# =========================
# CADASTRO CLIENTE
# =========================
@app.route("/salvar", methods=["POST"])
def salvar():
    senha_hash = bcrypt.hashpw(
        request.form["senha"].encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    dados = (
        request.form["nome"],
        request.form["sobrenome"],
        request.form["data_nascimento"],
        request.form["sexo"],
        request.form["email"],
        senha_hash
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
    senha_hash = bcrypt.hashpw(
        request.form["senha"].encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    dados = (
        request.form["nome"],
        request.form["sobrenome"],
        request.form["data_nascimento"],
        request.form["sexo"],
        request.form["email"],
        senha_hash,
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
# AGENDAMENTO COM EMAIL
# =========================
@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    dados = request.get_json()

    cliente_email   = session["usuario_logado"]
    prestador_email = dados.get("prestador_email")

    conn   = connectar()
    cursor = conn.cursor(dictionary=True)

    # Busca cliente (pode estar em clientes ou só ter email da sessão via Google)
    cursor.execute("SELECT nome, sobrenome, email FROM cadastro_clientes WHERE email = %s", (cliente_email,))
    cliente = cursor.fetchone()
    if not cliente:
        # fallback: usa email da sessão diretamente
        nome_session = session.get("usuario_nome", cliente_email)
        cliente = {"nome": nome_session.split(" ")[0], "sobrenome": " ".join(nome_session.split(" ")[1:]), "email": cliente_email}
        print(f"[AGENDAMENTO] Cliente não encontrado na tabela, usando sessão: {cliente}")

    cursor.execute("SELECT nome, sobrenome, email FROM cadastro_prestadores WHERE email = %s", (prestador_email,))
    prestador = cursor.fetchone()

    print(f"[AGENDAMENTO] cliente={cliente}, prestador={prestador}, prestador_email={prestador_email}")

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

        nome_cliente   = f"{cliente['nome']} {cliente['sobrenome']}".strip()   if cliente   else cliente_email
        nome_prestador = f"{prestador['nome']} {prestador['sobrenome']}".strip() if prestador else prestador_email

        print(f"[AGENDAMENTO] Agendamento #{agendamento_id} salvo. Enviando emails...")
        print(f"[AGENDAMENTO] Email cliente: {cliente.get('email') if cliente else 'N/A'}")
        print(f"[AGENDAMENTO] Email prestador: {prestador.get('email') if prestador else 'N/A'}")

        servico_nm  = dados.get("servico", "")
        data_fmt    = dados.get("data", "")
        horario_fmt = dados.get("horario", "")
        preco_raw   = dados.get("preco", 0)
        preco_fmt   = f"R$ {float(preco_raw):.2f}".replace(".", ",")
        obs_txt     = dados.get("obs", "") or "Nenhuma"

        # ── EMAIL PARA O CLIENTE ──────────────────────────────────
        if cliente and cliente.get("email"):
            html_cliente = f"""
            <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
              <div style="background:#2563eb;padding:24px 28px;">
                <h1 style="color:#fff;margin:0;font-size:20px;">&#10003; Agendamento Confirmado</h1>
              </div>
              <div style="padding:28px;">
                <p style="color:#374151;">Olá, <strong>{nome_cliente}</strong>!</p>
                <p style="color:#374151;margin-bottom:16px;">Seu agendamento foi realizado com sucesso. Veja os detalhes:</p>
                <table style="width:100%;border-collapse:collapse;">
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;width:120px;">Serviço</td>
                    <td style="padding:10px 14px;font-weight:600;">{servico_nm}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Profissional</td>
                    <td style="padding:10px 14px;font-weight:600;">{nome_prestador}</td>
                  </tr>
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Data</td>
                    <td style="padding:10px 14px;font-weight:600;">{data_fmt}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Horário</td>
                    <td style="padding:10px 14px;font-weight:600;">{horario_fmt}</td>
                  </tr>
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Valor</td>
                    <td style="padding:10px 14px;font-weight:600;color:#2563eb;">{preco_fmt}</td>
                  </tr>
                </table>
                <p style="color:#6b7280;font-size:13px;margin-top:16px;">Em caso de dúvidas, entre em contato com o profissional.</p>
                <a href="http://127.0.0.1:5000/agendamento_confirmado?id={agendamento_id}"
                   style="display:inline-block;margin-top:16px;background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">
                  Ver Agendamento
                </a>
              </div>
            </div>"""
            enviar_email(cliente["email"], f"✅ Agendamento confirmado — {servico_nm}", html_cliente)

        # ── EMAIL PARA O PRESTADOR ────────────────────────────────
        if prestador and prestador.get("email"):
            html_prestador = f"""
            <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
              <div style="background:#1d4ed8;padding:24px 28px;">
                <h1 style="color:#fff;margin:0;font-size:20px;">&#128197; Novo Agendamento Recebido</h1>
              </div>
              <div style="padding:28px;">
                <p style="color:#374151;">Olá, <strong>{nome_prestador}</strong>!</p>
                <p style="color:#374151;margin-bottom:16px;">Você recebeu um novo agendamento:</p>
                <table style="width:100%;border-collapse:collapse;">
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;width:120px;">Cliente</td>
                    <td style="padding:10px 14px;font-weight:600;">{nome_cliente}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Serviço</td>
                    <td style="padding:10px 14px;font-weight:600;">{servico_nm}</td>
                  </tr>
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Data</td>
                    <td style="padding:10px 14px;font-weight:600;">{data_fmt}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Horário</td>
                    <td style="padding:10px 14px;font-weight:600;">{horario_fmt}</td>
                  </tr>
                  <tr style="background:#f3f4f6;">
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Valor</td>
                    <td style="padding:10px 14px;font-weight:600;color:#1d4ed8;">{preco_fmt}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;color:#6b7280;font-size:13px;">Observações</td>
                    <td style="padding:10px 14px;">{obs_txt}</td>
                  </tr>
                </table>
                <a href="http://127.0.0.1:5000/painel"
                   style="display:inline-block;margin-top:16px;background:#1d4ed8;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">
                  Ver no Painel
                </a>
              </div>
            </div>"""
            enviar_email(prestador["email"], f"📅 Novo agendamento de {nome_cliente}", html_prestador)

        return jsonify({
            "mensagem": "Agendamento salvo!",
            "id":             agendamento_id,
            "nome_cliente":   nome_cliente,
            "nome_prestador": nome_prestador,
            "email_cliente":  cliente_email,
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
# TROCAR SENHA
# =========================
@app.route("/trocar_senha", methods=["POST"])
def trocar_senha():
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    dados = request.get_json()
    senha_atual  = dados.get("senha_atual", "").encode("utf-8")
    senha_nova   = dados.get("senha_nova", "")
    senha_conf   = dados.get("senha_confirmacao", "")

    if senha_nova != senha_conf:
        return jsonify({"erro": "As senhas novas não coincidem"}), 400

    if len(senha_nova) < 6:
        return jsonify({"erro": "A senha nova deve ter pelo menos 6 caracteres"}), 400

    email = session["usuario_logado"]
    tipo  = session.get("tipo_usuario")
    tabela = "cadastro_prestadores" if tipo == "prestador" else "cadastro_clientes"

    conn   = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(f"SELECT senha FROM {tabela} WHERE email = %s", (email,))
    row = cursor.fetchone()

    if not row or not row["senha"]:
        cursor.close()
        conn.close()
        return jsonify({"erro": "Conta sem senha (login pelo Google). Defina uma senha primeiro."}), 400

    hash_salvo = row["senha"]
    if isinstance(hash_salvo, str):
        hash_salvo = hash_salvo.encode("utf-8")

    if not bcrypt.checkpw(senha_atual, hash_salvo):
        cursor.close()
        conn.close()
        return jsonify({"erro": "Senha atual incorreta"}), 400

    novo_hash = bcrypt.hashpw(senha_nova.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor.execute(f"UPDATE {tabela} SET senha = %s WHERE email = %s", (novo_hash, email))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"mensagem": "Senha alterada com sucesso!"})

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
# API: PRESTADORES POR CATEGORIA (para orçamentos)
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
    nome     = dados.get("nome", "").strip()
    sobrenome = dados.get("sobrenome", "").strip()
    telefone = dados.get("telefone", "").strip()
    cidade   = dados.get("cidade", "").strip()

    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cadastro_clientes
        SET nome = %s, sobrenome = %s, telefone = %s, cidade = %s
        WHERE email = %s
    """, (nome, sobrenome, telefone, cidade, session["usuario_logado"]))
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

    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cadastro_prestadores
        SET nome = %s, sobrenome = %s, telefone = %s, cidade = %s, bio = %s
        WHERE email = %s
    """, (nome, sobrenome, telefone, cidade, bio, session["usuario_logado"]))
    conn.commit()
    cursor.close()
    conn.close()

    session["usuario_nome"] = nome + " " + sobrenome
    return jsonify({"mensagem": "Perfil atualizado!"})

# =========================

if __name__ == "__main__":
    app.run(debug=True)