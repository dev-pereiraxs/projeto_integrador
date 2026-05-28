from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Blueprint
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
import pathlib
import requests as http_requests
from datetime import datetime, timedelta
from urllib.parse import urlencode
import resend
from itsdangerous import URLSafeTimedSerializer
import bcrypt
from functools import wraps
from collections import defaultdict

# Carrega as variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = "2a962fb071252f38d97cafb2f3a84c80c49568ebb87bc1b1"

# Configura a chave da API do Resend
resend.api_key = os.getenv("RESEND_API_KEY")

# Configuração para o "Lembrar de Mim" durar 30 dias na sessão permanente
app.permanent_session_lifetime = timedelta(days=30)

# Gerador de tokens seguros com expiração para a senha
serializer = URLSafeTimedSerializer(app.secret_key)

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
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
        "scope": "openid email profile https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
    },
)

# =========================
# BANCO DE DADOS
# =========================
def connectar():
    if os.getenv("DB_HOST"):
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            ssl_disabled=False
        )
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='servicos'
    )

# =========================
# DECORADORES AUXILIARES ADMIN
# =========================
def is_admin_logged_in():
    return session.get("tipo_usuario") == "admin" and bool(session.get("usuario_logado"))

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_admin_logged_in():
            return redirect(url_for("admin_login_page"))
        return fn(*args, **kwargs)
    return wrapper

# =========================
# FUNÇÃO TRANSMISSORA DO RESEND
# =========================
def enviar_email_recuperacao(destinatario, link_recuperacao):
    remetente = "onboarding@resend.dev"
    html_conteudo = f"""
    <html>
      <body style="font-family: 'DM Sans', Arial, sans-serif; color: #1a2340; padding: 20px; line-height: 1.6;">
        <h2 style="color: #2563eb; font-family: 'Sora', sans-serif;">Agenda Fácil</h2>
        <p>Olá,</p>
        <p>Recebemos uma solicitação para redefinir a senha vinculada ao seu e-mail.</p>
        <p>Para escolher uma nova senha e recuperar o acesso, clique no botão abaixo:</p>
        <div style="margin: 24px 0;">
          <a href="{link_recuperacao}" style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold;">Redefinir Minha Senha</a>
        </div>
        <p style="font-size: 12px; color: #64748b;">Se você não solicitou, ignore. Expira em 1 hora.</p>
      </body>
    </html>
    """
    try:
        resend.Emails.send({
            "from": remetente, "to": destinatario,
            "subject": "Recuperação de Senha - Agenda Fácil", "html": html_conteudo
        })
        return True
    except Exception as e:
        print(f"[Resend Erro]: {e}")
        return False

# =========================
# HELPER — GOOGLE CALENDAR
# =========================
def gerar_url_google_agenda(titulo, data_str, horario, duracao_horas, prestador_nome, obs=""):
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=float(duracao_horas or 1))
        params = {
            "action": "TEMPLATE", "text": f"Agendamento: {titulo}",
            "dates": f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}",
            "details": f"Prestador: {prestador_nome}\nObservações: {obs or '—'}",
            "ctz": "America/Sao_Paulo",
        }
        return "https://calendar.google.com/calendar/render?" + urlencode(params)
    except:
        return None

def criar_evento_google_calendar(access_token, titulo, data_str, horario, duracao_horas, prestador_nome, cliente_email, prestador_email, obs=""):
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=float(duracao_horas or 1))
        evento = {
            "summary": f"Agendamento: {titulo}",
            "description": f"Prestador: {prestador_nome}\nObservações: {obs or '—'}",
            "start": {"dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "America/Sao_Paulo"},
            "attendees": [{"email": cliente_email}, {"email": prestador_email}],
        }
        res = http_requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events?sendUpdates=all",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=evento, timeout=8,
        )
        return res.status_code in (200, 201), res.json().get("htmlLink") if res.status_code in (200, 201) else None
    except:
        return False, None

def criar_notificacao(prestador_email, tipo, mensagem, agendamento_id=None):
    try:
        conn = connectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notificacoes (prestador_email, tipo, mensagem, agendamento_id) VALUES (%s, %s, %s, %s)",
                       (prestador_email, tipo, mensagem, agendamento_id))
        conn.commit()
    except Exception as e:
        print(f"[Notificações] Erro: {e}")
    finally:
        try: cursor.close(); conn.close()
        except: pass

# =========================
# GOOGLE LOGIN
# =========================
@app.route("/login-google")
def login_google():
    redirect_uri = "https://projeto-integrador-4aw2.onrender.com/callback" if os.getenv("DB_HOST") else "http://127.0.0.1:5000/callback"
    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        return render_template("login.html", erro="Erro ao obter dados do Google.")

    nome, sobrenome, email = user_info.get("given_name", ""), user_info.get("family_name", ""), user_info.get("email")
    session["google_token"] = token.get("access_token")

    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email = %s", (email,))
    prestador = cursor.fetchone()

    if prestador:
        session.update({"usuario_logado": email, "tipo_usuario": "prestador", "usuario_nome": f"{prestador['nome']} {prestador['sobrenome']}", "usuario_foto": prestador.get("foto") or ""})
        cursor.close(); conn.close()
        return redirect(url_for("servicos"))

    cursor.execute("SELECT * FROM cadastro_clientes WHERE email = %s", (email,))
    cliente = cursor.fetchone()

    if not cliente:
        try:
            cursor.execute("INSERT INTO cadastro_clientes (nome, sobrenome, email) VALUES (%s, %s, %s)", (nome, sobrenome, email))
            conn.commit()
        except Exception as e:
            print("Erro ao criar conta Google:", e)

    cursor.close(); conn.close()
    session.update({"usuario_logado": email, "tipo_usuario": "cliente", "usuario_nome": f"{nome} {sobrenome}", "usuario_foto": (cliente or {}).get("foto") or ""})
    return redirect(url_for("servicos"))

# =========================
# PÁGINAS PÚBLICAS
# =========================
@app.route("/")
def index():
    cadastro_ok = request.args.get("cadastro", "")
    tipo = request.args.get("tipo", "")
    return render_template("principal.html", cadastro_ok_tipo="" if cadastro_ok != "ok" else tipo)

@app.route("/cadastro")
def cadastro(): return render_template("cadastro.html")

@app.route("/login")
def login():
    if request.args.get('next'): session['next_url'] = request.args.get('next')
    return render_template("login.html")

@app.route("/servicos")
def servicos():
    try:
        conn = connectar(); cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome, p.areas_atuacao, p.telefone,
            (SELECT COALESCE(ROUND(AVG(nota), 1), NULL) FROM avaliacoes_prestadores WHERE prestador_email = s.prestador_email) AS media_nota,
            (SELECT COUNT(*) FROM avaliacoes_prestadores WHERE prestador_email = s.prestador_email) AS total_avaliacoes
            FROM servicos_anunciados s INNER JOIN cadastro_prestadores p ON s.prestador_email = p.email ORDER BY s.id DESC
        """)
        lista = cursor.fetchall()
        cursor.close(); conn.close()
        return render_template("servicos.html", servicos=lista)
    except Exception as e:
        return f"<h3>Erro:</h3><p>{str(e)}</p>", 500

@app.route("/perfil")
def perfil():
    if "usuario_logado" not in session: return redirect(url_for("login"))
    if session.get("tipo_usuario") == "prestador": return redirect(url_for("perfil_prestador", email=session["usuario_logado"]))
    return redirect(url_for("perfil_cliente"))

@app.route("/prestador")
def prestador(): return render_template("prestador.html")

@app.route("/orcamentos")
def orcamento(): return render_template("orcamentos.html")

@app.route("/painel")
def painel(): return render_template("painel.html")

@app.route("/formulario")
def formulario():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador": return redirect(url_for("login"))
    try:
        conn = connectar(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT areas_atuacao FROM cadastro_prestadores WHERE email = %s", (session["usuario_logado"],))
        prestador = cursor.fetchone()
        area = str(prestador.get("areas_atuacao") or "").strip().lower()
        if area in ["mecânica", "elétrica", "hidráulica", "hydraulica"]:
            area = area.replace("mecânica", "mecanica").replace("elétrica", "eletrica").replace("hidráulica", "hidraulica").replace("hydraulica", "hidraulica")
        session["usuario_area"] = area
    except:
        session["usuario_area"] = ""
    finally:
        cursor.close(); conn.close()
    return render_template("formulario.html")

@app.route("/agendamentos")
def agendamentos(): return render_template("agendamento.html")

@app.route("/sucesso-agendamento")
def sucesso_servico(): return render_template("sucessoservico.html")

@app.route("/sucesso-orcamento")
def sucesso_orcamento(): return render_template("sucesso_orcamento.html")

@app.route("/sucesso-conclusao")
def sucesso_conclusao():
    if "usuario_logado" not in session: return redirect(url_for("login"))
    return render_template("sucesso_conclusao.html")

# =========================
# AUTENTICAÇÃO / CADASTRO
# =========================
@app.route("/autenticar", methods=["POST"])
def autenticar():
    email, senha, lembrar = request.form["email"], request.form["senha"], request.form.get("lembrar")
    conn = connectar(); cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email=%s AND senha=%s", (email, senha))
    prestador = cursor.fetchone()
    if prestador:
        session.update({"permanent": bool(lembrar), "usuario_logado": email, "tipo_usuario": "prestador", "usuario_nome": f"{prestador['nome']} {prestador['sobrenome']}", "usuario_area": str(prestador.get("areas_atuacao") or "").strip().lower()})
        cursor.close(); conn.close()
        return redirect(session.pop('next_url', url_for("servicos")))

    cursor.execute("SELECT * FROM cadastro_clientes WHERE email=%s AND senha=%s", (email, senha))
    cliente = cursor.fetchone()
    cursor.close(); conn.close()
    if cliente:
        session.update({"permanent": bool(lembrar), "usuario_logado": email, "tipo_usuario": "cliente", "usuario_nome": f"{cliente['nome']} {cliente['sobrenome']}"})
        return redirect(session.pop('next_url', url_for("avaliar")))

    return render_template("login.html", erro="E-mail ou senha inválidos")

@app.route("/salvar", methods=["POST"])
def salvar():
    dados = (request.form["nome"], request.form["sobrenome"], request.form["data_nascimento"], request.form["sexo"], request.form["email"].strip().lower(), request.form["senha"])
    try:
        conn = connectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO cadastro_clientes (nome,sobrenome,data_nascimento,sexo,email,senha) VALUES (%s,%s,%s,%s,%s,%s)", dados)
        conn.commit()
        session.update({"permanent": bool(request.form.get("lembrar")), "usuario_logado": dados[4], "tipo_usuario": "cliente", "usuario_nome": f"{dados[0]} {dados[1]}"})
        return redirect(url_for("index", cadastro="ok", tipo="cliente"))
    except Exception:
        return render_template("cadastro.html", erro="Erro ao cadastrar. O e-mail já existe.")
    finally:
        cursor.close(); conn.close()

@app.route("/salvar_prestador", methods=["POST"])
def salvar_prestador():
    dados = (request.form["nome"], request.form["sobrenome"], request.form["data_nascimento"], request.form["sexo"], request.form["email"].strip().lower(), request.form["senha"], request.form["areas_atuacao"], request.form["telefone"])
    try:
        conn = connectar(); cursor = conn.cursor()
        cursor.execute("INSERT INTO cadastro_prestadores (nome,sobrenome,data_nascimento,sexo,email,senha,areas_atuacao,telefone) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", dados)
        conn.commit()
        session.update({"permanent": bool(request.form.get("lembrar")), "usuario_logado": dados[4], "tipo_usuario": "prestador", "usuario_nome": f"{dados[0]} {dados[1]}"})
        return redirect(url_for("index", cadastro="ok", tipo="prestador"))
    except Exception as e:
        return render_template("prestador.html", erro=str(e))
    finally:
        cursor.close(); conn.close()

# =========================
# APIs PRINCIPAIS (Agendamentos e Serviços)
# =========================
@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    if "usuario_logado" not in session: return jsonify({"erro": "Não logado"}), 401
    dados = request.get_json()
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT nome, sobrenome FROM cadastro_clientes WHERE email=%s", (session["usuario_logado"],))
        cliente = cursor.fetchone()
        cursor.execute("SELECT nome, sobrenome FROM cadastro_prestadores WHERE email=%s", (dados.get("prestador_email"),))
        prestador_row = cursor.fetchone()
        cursor.execute("SELECT duracao FROM servicos_anunciados WHERE titulo=%s AND prestador_email=%s LIMIT 1", (dados.get("servico"), dados.get("prestador_email")))
        duracao_horas = (cursor.fetchone() or {}).get("duracao", 1)

        cursor.execute("INSERT INTO agendamentos (cliente_email,prestador_email,servico,preco,data_servico,horario,observacoes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (session["usuario_logado"], dados.get("prestador_email"), dados.get("servico"), dados.get("preco"), dados.get("data"), dados.get("horario"), dados.get("obs", "")))
        conn.commit()
        ag_id = cursor.lastrowid

        nome_cl = f"{cliente['nome']} {cliente['sobrenome']}" if cliente else session["usuario_logado"]
        nome_pr = f"{prestador_row['nome']} {prestador_row['sobrenome']}" if prestador_row else dados.get("prestador_email")

        criar_notificacao(dados.get("prestador_email"), "novo_agendamento", f"Novo agendamento de {nome_cl} — {dados.get('servico')} em {dados.get('data')} às {dados.get('horario')}", ag_id)
        calendar_url = gerar_url_google_agenda(dados.get("servico"), dados.get("data"), dados.get("horario"), duracao_horas, nome_pr, dados.get("obs"))
        return jsonify({"mensagem": "Agendamento salvo!", "calendar_url": calendar_url}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        cursor.close(); conn.close()

@app.route("/salvar_servico_prestador", methods=["POST"])
def salvar_servico_prestador():
    if session.get("tipo_usuario") != "prestador": return jsonify({"erro": "Acesso negado"}), 401
    dados = request.get_json()
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT areas_atuacao FROM cadastro_prestadores WHERE email=%s", (session["usuario_logado"],))
        area = (cursor.fetchone() or {}).get("areas_atuacao")
        if not area: return jsonify({"erro": "Sem área definida"}), 400
        cursor.execute("INSERT INTO servicos_anunciados (prestador_email,titulo,descricao,preco,area_atuacao,duracao) VALUES (%s,%s,%s,%s,%s,%s)",
            (session["usuario_logado"], dados.get("titulo"), dados.get("descricao"), dados.get("preco"), area, dados.get("duracao")))
        conn.commit()
        return jsonify({"mensagem": "Sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)})
    finally:
        cursor.close(); conn.close()

@app.route("/api/listar_servicos")
def listar_servicos():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome, p.telefone,
        COALESCE(ROUND(AVG(av.nota), 1), NULL) AS media_nota FROM servicos_anunciados s
        JOIN cadastro_prestadores p ON s.prestador_email = p.email
        LEFT JOIN agendamentos a ON a.prestador_email = p.email AND a.status = 'concluido'
        LEFT JOIN avaliacoes_prestadores av ON av.agendamento_id = a.id
        GROUP BY s.id ORDER BY s.id DESC
    """)
    dados = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(dados)

@app.route("/api/meus_servicos")
def meus_servicos():
    if "usuario_logado" not in session: return jsonify([]), 401
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servicos_anunciados WHERE prestador_email=%s", (session["usuario_logado"],))
    dados = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(dados)

@app.route("/api/excluir_servico/<int:id>", methods=["DELETE"])
def excluir_servico(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("DELETE FROM servicos_anunciados WHERE id=%s AND prestador_email=%s", (id, session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "ok"})

@app.route("/api/horarios_bloqueados")
def horarios_bloqueados():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT horario FROM agendamentos WHERE data_servico=%s AND prestador_email=%s AND status NOT IN ('cancelado')", (request.args.get("data"), request.args.get("prestador_email")))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify([r["horario"] for r in rows])

@app.route("/api/prestadores_por_categoria")
def prestadores_por_categoria():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nome, sobrenome, email FROM cadastro_prestadores WHERE LOWER(areas_atuacao) LIKE %s", (f"%{request.args.get('categoria', '')}%",))
    dados = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(dados)

@app.route("/api/cancelar_agendamento/<int:id>", methods=["PATCH"])
def cancelar_agendamento(id):
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE agendamentos SET status='cancelado' WHERE id=%s AND cliente_email=%s", (id, session["usuario_logado"]))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({"mensagem": "Agendamento cancelado"})

@app.route("/api/atualizar_status/<int:id>", methods=["PATCH"])
def atualizar_status(id):
    novo_status = (request.get_json() or {}).get("status")
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE agendamentos SET status=%s WHERE id=%s", (novo_status, id))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Status updated"})

@app.route("/api/recusar_agendamento/<int:id>", methods=["PATCH"])
def recusar_agendamento(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET status='recusado' WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Recusado"})

@app.route("/api/meus_agendamentos")
def meus_agendamentos():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome FROM agendamentos a LEFT JOIN cadastro_prestadores p ON a.prestador_email=p.email WHERE a.cliente_email=%s ORDER BY a.data_servico DESC", (session.get("usuario_logado"),))
    dados = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(dados)

@app.route("/api/agendamentos_prestador")
def agendamentos_prestador():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.*, c.nome AS cliente_nome, c.sobrenome AS cliente_sobrenome FROM agendamentos a LEFT JOIN cadastro_clientes c ON a.cliente_email=c.email WHERE a.prestador_email=%s ORDER BY a.data_servico DESC", (session.get("usuario_logado"),))
    dados = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(dados)

@app.route("/api/notificacoes")
def listar_notificacoes():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notificacoes WHERE prestador_email=%s ORDER BY criada_em DESC LIMIT 50", (session.get("usuario_logado"),))
    notifs = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS t FROM notificacoes WHERE prestador_email=%s AND lida=0", (session.get("usuario_logado"),))
    nao_lidas = cursor.fetchone()["t"]
    cursor.close(); conn.close()
    return jsonify({"notificacoes": notifs, "nao_lidas": nao_lidas})

@app.route("/api/notificacoes/marcar_lida/<int:id>", methods=["PATCH"])
def marcar_notificacao_lida(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE notificacoes SET lida=1 WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Ok"})

@app.route("/api/notificacoes/marcar_todas_lidas", methods=["PATCH"])
def marcar_todas_lidas():
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE notificacoes SET lida=1 WHERE prestador_email=%s", (session.get("usuario_logado"),))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Ok"})

# =========================
# PERFIS E UPLOADS
# =========================
@app.route("/perfil_prestador/<email>")
def perfil_prestador(email):
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email=%s", (email,))
    prestador = cursor.fetchone()
    cursor.execute("SELECT * FROM servicos_anunciados WHERE prestador_email=%s ORDER BY id DESC", (email,))
    servicos = cursor.fetchall()
    cursor.execute("SELECT a.*, c.nome AS cliente_nome, c.sobrenome AS cliente_sobrenome FROM agendamentos a LEFT JOIN cadastro_clientes c ON a.cliente_email=c.email WHERE a.prestador_email=%s", (email,))
    todos_agendamentos = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS total FROM agendamentos WHERE prestador_email=%s AND status='concluido'", (email,))
    agendamentos_count = cursor.fetchone()["total"]
    cursor.close(); conn.close()
    return render_template("perfil-prestador.html", prestador=prestador, servicos=servicos, todos_agendamentos=todos_agendamentos, agendamentos_count=agendamentos_count)

@app.route("/perfil_cliente")
def perfil_cliente():
    if "usuario_logado" not in session: return redirect(url_for("login"))
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cadastro_clientes WHERE email=%s", (session["usuario_logado"],))
    cliente = cursor.fetchone()
    cursor.execute("SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome FROM agendamentos a LEFT JOIN cadastro_prestadores p ON a.prestador_email=p.email WHERE a.cliente_email=%s ORDER BY a.data_servico DESC", (session["usuario_logado"],))
    agendamentos = cursor.fetchall()
    cursor.execute("SELECT * FROM solicitacoes_orcamento WHERE cliente_email=%s ORDER BY id DESC", (session["usuario_logado"],))
    orcamentos = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template("perfil-cliente.html", cliente=cliente, agendamentos=agendamentos, orcamentos=orcamentos)

@app.route("/meu_perfil")
def meu_perfil():
    return redirect(url_for("perfil_prestador", email=session["usuario_logado"]) if session.get("tipo_usuario") == "prestador" else url_for("perfil_cliente"))

@app.route("/salvar_foto", methods=["POST"])
def salvar_foto():
    file = request.files.get("foto")
    if not file: return jsonify({"erro": "Sem arquivo"}), 400
    ext = file.filename.rsplit(".", 1)[1].lower()
    path = os.path.join("static", "uploads", "fotos", f"{session['usuario_logado'].replace('@', '_').replace('.', '_')}.{ext}")
    file.save(path)
    url = "/" + path.replace("\\", "/")
    conn = connectar(); cursor = conn.cursor()
    table = "cadastro_prestadores" if session.get("tipo_usuario") == "prestador" else "cadastro_clientes"
    cursor.execute(f"UPDATE {table} SET foto=%s WHERE email=%s", (url, session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    session["usuario_foto"] = url
    return jsonify({"url": url})

@app.route("/salvar_certificado", methods=["POST"])
def salvar_certificado():
    file = request.files.get("certificado")
    ext = file.filename.rsplit(".", 1)[1].lower()
    import time
    path = os.path.join("static", "uploads", "certificados", f"{session['usuario_logado'].replace('@', '_').replace('.', '_')}_{int(time.time())}.{ext}")
    file.save(path)
    url = "/" + path.replace("\\", "/")
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT certificados FROM cadastro_prestadores WHERE email=%s", (session["usuario_logado"],))
    cert = ((cursor.fetchone() or {}).get("certificados") or "") + "," + url
    cursor.execute("UPDATE cadastro_prestadores SET certificados=%s WHERE email=%s", (cert.strip(","), session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"url": url})

@app.route("/editar_perfil_cliente", methods=["POST"])
def editar_perfil_cliente():
    d = request.get_json()
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE cadastro_clientes SET nome=%s, sobrenome=%s, telefone=%s, cidade=%s, sexo=%s WHERE email=%s",
                   (d.get("nome"), d.get("sobrenome"), d.get("telefone"), d.get("cidade"), d.get("sexo"), session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    session["usuario_nome"] = f"{d.get('nome')} {d.get('sobrenome')}"
    return jsonify({"mensagem": "ok"})

@app.route("/editar_perfil_prestador", methods=["POST"])
def editar_perfil_prestador():
    d = request.get_json()
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE cadastro_prestadores SET nome=%s, sobrenome=%s, telefone=%s, sexo=%s WHERE email=%s",
                   (d.get("nome"), d.get("sobrenome"), d.get("telefone"), d.get("sexo"), session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    session["usuario_nome"] = f"{d.get('nome')} {d.get('sobrenome')}"
    return jsonify({"mensagem": "ok"})

# =========================
# ORÇAMENTOS E AVALIAÇÕES
# =========================
@app.route('/api/solicitar-orcamento', methods=['POST'])
def solicitar_orcamento():
    d = request.get_json()
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("INSERT INTO solicitacoes_orcamento (nome, telefone, email, categoria, descricao, cliente_email) VALUES (%s, %s, %s, %s, %s, %s)",
                   (d.get('nome'), d.get('telefone'), d.get('email'), d.get('categoria'), d.get('descricao'), session.get("usuario_logado")))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"success": True})

@app.route("/api/cancelar_orcamento/<int:id>", methods=["PATCH"])
def cancelar_orcamento_cliente(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE solicitacoes_orcamento SET status='cancelado' WHERE id=%s AND cliente_email=%s", (id, session["usuario_logado"]))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "ok"})

@app.route("/api/checar_alerta_orcamento")
def checar_alerta_orcamento():
    if not session.get("usuario_logado"): return jsonify({"alerta": None})
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, categoria, status, COALESCE(motivo_recusa, '') AS motivo_recusa FROM solicitacoes_orcamento WHERE cliente_email=%s AND alerta_visto=0 AND status IN ('erro', 'cancelado') ORDER BY id DESC LIMIT 1", (session["usuario_logado"],))
    al = cursor.fetchone()
    cursor.close(); conn.close()
    return jsonify({"alerta": al})

@app.route("/api/marcar_alerta_orcamento_visto/<int:id>", methods=["PATCH"])
def marcar_alerta_orcamento_visto(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE solicitacoes_orcamento SET alerta_visto=1 WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "ok"})

@app.route("/avaliar")
def avaliar():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.id, a.servico, p.nome AS prestador_nome FROM agendamentos a 
        LEFT JOIN cadastro_prestadores p ON a.prestador_email = p.email 
        LEFT JOIN avaliacoes_prestadores av ON av.agendamento_id = a.id 
        WHERE a.cliente_email=%s AND a.status='concluido' AND av.id IS NULL LIMIT 1
    """, (session.get("usuario_logado"),))
    p = cursor.fetchone()
    cursor.close(); conn.close()
    if not p: return redirect(url_for("servicos"))
    return render_template("avaliar.html", pendente=p)

@app.route("/api/avaliacoes_pendentes")
def avaliacoes_pendentes():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.id, a.servico FROM agendamentos a LEFT JOIN avaliacoes_prestadores av ON av.agendamento_id = a.id WHERE a.cliente_email=%s AND a.status='concluido' AND av.id IS NULL LIMIT 1", (session.get("usuario_logado"),))
    p = cursor.fetchone()
    cursor.close(); conn.close()
    return jsonify({"pendente": p})

@app.route("/api/salvar_avaliacao", methods=["POST"])
def salvar_avaliacao():
    d = request.get_json()
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT prestador_email FROM agendamentos WHERE id=%s", (d.get("agendamento_id"),))
    ag = cursor.fetchone()
    cursor.execute("INSERT INTO avaliacoes_prestadores (prestador_email, cliente_email, agendamento_id, nota, comentario) VALUES (%s, %s, %s, %s, %s)",
                   (ag["prestador_email"], session["usuario_logado"], d.get("agendamento_id"), d.get("nota"), d.get("comentario")))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "ok"})

@app.route("/api/stats_prestador/<email>")
def stats_prestador(email):
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total, COALESCE(AVG(nota), 0) AS media, SUM(CASE WHEN nota=5 THEN 1 ELSE 0 END) AS cinco, SUM(CASE WHEN nota=4 THEN 1 ELSE 0 END) AS quatro, SUM(CASE WHEN nota=3 THEN 1 ELSE 0 END) AS tres, SUM(CASE WHEN nota=2 THEN 1 ELSE 0 END) AS dois, SUM(CASE WHEN nota=1 THEN 1 ELSE 0 END) AS um FROM avaliacoes_prestadores WHERE prestador_email=%s", (email,))
    st = cursor.fetchone()
    cursor.execute("SELECT av.nota, av.comentario, c.nome AS cliente_nome FROM avaliacoes_prestadores av LEFT JOIN cadastro_clientes c ON av.cliente_email=c.email WHERE av.prestador_email=%s ORDER BY av.criado_em DESC", (email,))
    avs = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"total": st["total"], "media": st["media"], "distribuicao": {"5": st["cinco"], "4": st["quatro"], "3": st["tres"], "2": st["dois"], "1": st["um"]}, "avaliacoes": avs})

@app.route("/api/checar_recusados_cliente")
def checar_recusados_cliente():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, servico FROM agendamentos WHERE cliente_email=%s AND status='recusado' AND alerta_visto=0 LIMIT 1", (session.get("usuario_logado"),))
    r = cursor.fetchone()
    cursor.close(); conn.close()
    return jsonify({"recusado": r})

@app.route("/api/marcar_alerta_visto/<int:id>", methods=["PATCH"])
def marcar_alerta_visto(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET alerta_visto=1 WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "ok"})

@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "GET": return render_template("esqueci_senha.html")
    email = request.form.get("email")
    enviar_email_recuperacao(email, url_for('resetar_senha', token=serializer.dumps(email, salt='reset-senha'), _external=True))
    return render_template("esqueci_senha.html", sucesso="Instruções enviadas se e-mail existir.")

@app.route("/resetar_senha/<token>", methods=["GET", "POST"])
def resetar_senha(token):
    try: email = serializer.loads(token, salt='reset-senha', max_age=900)
    except: return "Link inválido ou expirado.", 400
    if request.method == "GET": return render_template("resetar_senha.html", token=token)
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE cadastro_clientes SET senha=%s WHERE email=%s", (request.form.get("nova_senha"), email))
    cursor.execute("UPDATE cadastro_prestadores SET senha=%s WHERE email=%s", (request.form.get("nova_senha"), email))
    conn.commit(); cursor.close(); conn.close()
    return redirect(url_for("login", mensagem="Senha atualizada!"))

# =========================
# ADMIN AUTH E DASHBOARD
# =========================
@app.route("/admin/login", methods=["GET"])
def admin_login_page():
    return render_template("admin/login.html", erro=None)

@app.route("/admin/autenticar", methods=["GET", "POST"])
def admin_autenticar():
    if request.method == "GET":
        return redirect(url_for("admin_login_page"))

    try:
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        conn = connectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE email=%s", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if not admin or not admin.get("ativo"):
            return render_template("admin/login.html", erro="Credenciais inválidas")

        senha_banco = admin.get("senha_hash") or admin.get("senha")
        senha_valida = False

        if senha_banco:
            if senha_banco.startswith("$2b$") or senha_banco.startswith("$2a$"):
                import bcrypt
                senha_valida = bcrypt.checkpw(senha.encode("utf-8"), senha_banco.encode("utf-8"))
            else:
                senha_valida = (senha == senha_banco)

        if not senha_valida:
            return render_template("admin/login.html", erro="Credenciais inválidas")

        session.update({"usuario_logado": admin["email"], "tipo_usuario": "admin", "usuario_nome": admin["email"]})
        return redirect(url_for("admin_dashboard"))

    except Exception as e:
        return f"<div style='padding:40px;text-align:center;'><h2 style='color:#ef4444;'>Erro (Render)</h2><code>{str(e)}</code></div>", 500

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard(): return render_template("admin/dashboard.html")

@app.route("/admin/api/metrics", methods=["GET"])
@admin_required
def admin_metrics():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS c FROM cadastro_clientes")
    cli = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) AS p FROM cadastro_prestadores")
    pre = cursor.fetchone()["p"]
    cursor.execute("SELECT COUNT(*) AS t FROM agendamentos WHERE data_servico=CURDATE()")
    hj = cursor.fetchone()["t"]
    cursor.close(); conn.close()
    return jsonify({"total_clients": cli, "total_providers": pre, "services_requested_today": hj, "status_counts": {}, "solicitations_last_7": {"labels":[],"values":[]}, "top_prestadores": [], "total_concluidos": 0})

# =========================
# ADMIN LISTAGENS (BLUEPRINTS/APIs)
# =========================
@app.route("/admin/clientes")
@admin_required
def admin_clientes(): return render_template("admin/clientes.html")

@app.route("/admin/prestadores")
@admin_required
def admin_prestadores(): return render_template("admin/prestadores.html")

@app.route("/admin/notificacoes")
@admin_required
def admin_notificacoes(): return render_template("admin/notificacoes.html")

@app.route("/admin/api/clientes", methods=["GET"])
@admin_required
def admin_api_clientes():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cadastro_clientes ORDER BY id DESC LIMIT 25")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"clientes": rows, "total": len(rows), "page": 1, "per_page": 25})

@app.route("/admin/api/prestadores", methods=["GET"])
@admin_required
def admin_api_prestadores():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cadastro_prestadores ORDER BY id DESC LIMIT 25")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"prestadores": rows, "total": len(rows), "page": 1, "per_page": 25})

@app.route("/admin/solicitacoes")
@admin_required
def admin_solicitacoes(): return redirect(url_for("admin_dashboard"))

@app.route("/admin/api/orcamentos", methods=["GET"])
@admin_required
def admin_api_orcamentos():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solicitacoes_orcamento ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"solicitacoes": rows, "total": len(rows), "pendente": 0, "enviado": 0, "erro": 0, "timeline": [], "por_categoria": []})

admin_sol_bp = Blueprint("admin_sol", __name__)
@admin_sol_bp.route("/admin/api/solicitacoes", methods=["GET"])
def listar_solicitacoes():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM agendamentos ORDER BY id DESC LIMIT 25")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"solicitacoes": rows})

@admin_sol_bp.route("/admin/api/solicitacoes/<int:id>/aprovar", methods=["PATCH"])
def aprovar_solicitacao(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET status='confirmado' WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Aprovado"})

@admin_sol_bp.route("/admin/api/solicitacoes/<int:id>/rejeitar", methods=["PATCH"])
def rejeitar_solicitacao(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET status='recusado' WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Rejeitado"})

app.register_blueprint(admin_sol_bp)

@app.route("/admin/api/solicitacoes-orcamento", methods=["GET"])
@admin_required
def admin_listar_solicitacoes_orcamento():
    conn = connectar(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM solicitacoes_orcamento ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify({"solicitacoes": rows})

@app.route("/admin/api/solicitacoes-orcamento/<int:id>/aprovar", methods=["PATCH"])
@admin_required
def admin_aprovar_orcamento(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE solicitacoes_orcamento SET status='enviado' WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Aprovado"})

@app.route("/admin/api/solicitacoes-orcamento/<int:id>/rejeitar", methods=["PATCH"])
@admin_required
def admin_rejeitar_orcamento(id):
    conn = connectar(); cursor = conn.cursor()
    cursor.execute("UPDATE solicitacoes_orcamento SET status='erro' WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    return jsonify({"mensagem": "Rejeitado"})

@app.route("/agendamento_confirmado")
def agendamento_confirmado(): return redirect(url_for("sucesso_servico"))

if __name__ == "__main__":
    app.run(debug=True)