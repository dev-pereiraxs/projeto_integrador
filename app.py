from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    else:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="servicos"
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
    """Dispara o e-mail de redefinição usando a API oficial da Resend."""
    remetente = "onboarding@resend.dev"

    html_conteudo = f"""
    <html>
      <body style="font-family: 'DM Sans', Arial, sans-serif; color: #1a2340; padding: 20px; line-height: 1.6;">
        <h2 style="color: #2563eb; font-family: 'Sora', sans-serif;">Agenda Fácil</h2>
        <p>Olá,</p>
        <p>Recebemos uma solicitação para redefinir a senha vinculada ao seu e-mail.</p>
        <p>Para escolher uma nova senha e recuperar o acesso, clique no botão abaixo:</p>
        <div style="margin: 24px 0;">
          <a href="{link_recuperacao}" style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);">Redefinir Minha Senha</a>
        </div>
        <p style="font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 24px;">
          Se você não solicitou essa alteração, pode ignorar este e-mail com segurança. O link expira em 1 hora.
        </p>
      </body>
    </html>
    """

    try:
        params = {
            "from": remetente,
            "to": destinatario,
            "subject": "Recuperação de Senha - Agenda Fácil",
            "html": html_conteudo
        }
        resend.Emails.send(params)
        print(f"[Resend] E-mail enviado com sucesso para {destinatario}")
        return True
    except Exception as e:
        print(f"[Resend Erro] Falha crítica ao disparar API: {e}")
        return False


# =========================
# HELPER — GOOGLE CALENDAR
# =========================
def gerar_url_google_agenda(titulo, data_str, horario, duracao_horas, prestador_nome, obs=""):
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=float(duracao_horas or 1))

        params = {
            "action": "TEMPLATE",
            "text": f"Agendamento: {titulo}",
            "dates": f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}",
            "details": f"Prestador: {prestador_nome}\nObservações: {obs or '—'}\n\nAgendado via Agenda Fácil",
            "ctz": "America/Sao_Paulo",
        }
        return "https://calendar.google.com/calendar/render?" + urlencode(params)
    except Exception as e:
        print(f"[Calendar URL] Erro ao gerar URL: {e}")
        return None


def criar_evento_google_calendar(access_token, titulo, data_str, horario,
                                 duracao_horas, prestador_nome,
                                 cliente_email, prestador_email, obs=""):
    try:
        start_dt = datetime.strptime(f"{data_str} {horario}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=float(duracao_horas or 1))

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
            "attendees": [
                {"email": cliente_email, "displayName": "Cliente"},
                {"email": prestador_email, "displayName": prestador_nome},
            ],
            "guestsCanModify": False,
            "guestsCanSeeOtherGuests": True,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},
                    {"method": "popup", "minutes": 60},
                ],
            },
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        res = http_requests.post(
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
# NOTIFICAÇÕES — HELPER
# =========================
def criar_notificacao(prestador_email, tipo, mensagem, agendamento_id=None):
    try:
        conn = connectar()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO notificacoes (prestador_email, tipo, mensagem, agendamento_id)
               VALUES (%s, %s, %s, %s)""",
            (prestador_email, tipo, mensagem, agendamento_id)
        )
        conn.commit()
    except Exception as e:
        print(f"[Notificações] Erro ao criar: {e}")
    finally:
        try:
            cursor.close(); conn.close()
        except:
            pass


# =========================
# GOOGLE LOGIN
# =========================
@app.route("/login-google")
def login_google():
    if os.getenv("DB_HOST"):
        redirect_uri = "https://projeto-integrador-4aw2.onrender.com/callback"
    else:
        redirect_uri = "http://127.0.0.1:5000/callback"

    return google.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info:
        return render_template("login.html", erro="Erro ao obter dados do Google.")

    nome = user_info.get("given_name", "")
    sobrenome = user_info.get("family_name", "")
    email = user_info.get("email")

    session["google_token"] = token.get("access_token")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email = %s", (email,))
    prestador = cursor.fetchone()

    if prestador:
        session["usuario_logado"] = email
        session["tipo_usuario"] = "prestador"
        session["usuario_nome"] = prestador["nome"] + " " + prestador["sobrenome"]
        session["usuario_foto"] = prestador.get("foto") or ""
        cursor.close();
        conn.close()
        return redirect(url_for("servicos"))

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

    cursor.close();
    conn.close()

    session["usuario_logado"] = email
    session["tipo_usuario"] = "cliente"
    session["usuario_nome"] = nome + " " + sobrenome
    session["usuario_foto"] = (cliente or {}).get("foto") or ""
    return redirect(url_for("servicos"))

# =========================
# PÁGINAS PÚBLICAS
# =========================
@app.route("/")
def index():
    cadastro_ok = request.args.get("cadastro", "")
    tipo = request.args.get("tipo", "")
    cadastro_ok_tipo = "" if cadastro_ok != "ok" else tipo
    return render_template("principal.html", cadastro_ok_tipo=cadastro_ok_tipo)


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/login")
def login():
    next_url = request.args.get('next', '')
    if next_url:
        session['next_url'] = next_url
    return render_template("login.html")


# =========================
# PÁGINAS PÚBLICAS — SERVIÇOS
# =========================
@app.route("/servicos")
# =========================
# PÁGINAS PÚBLICAS — SERVIÇOS (VERSÃO DEFINITIVA)
# =========================
@app.route("/servicos")
def servicos():
    try:
        conn = connectar()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                s.*, 
                p.nome, 
                p.sobrenome, 
                p.areas_atuacao, 
                p.telefone
            FROM servicos_anunciados s
            INNER JOIN cadastro_prestadores p ON s.prestador_email = p.email
            ORDER BY s.id DESC
        """)
        lista = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template("servicos.html", servicos=lista)

    except Exception as e:
        return f"<h3>Erro de Conexão com o Banco:</h3><p>{str(e)}</p>", 500


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
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return redirect(url_for("login"))

    email_prestador = session["usuario_logado"]

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT areas_atuacao FROM cadastro_prestadores WHERE email = %s", (email_prestador,))
        prestador = cursor.fetchone()

        area_oficial = str(prestador.get("areas_atuacao") or "").strip().lower()

        if area_oficial == "mecânica": area_oficial = "mecanica"
        if area_oficial == "elétrica": area_oficial = "eletrica"
        if area_oficial == "hidráulica" or area_oficial == "hydraulica": area_oficial = "hidraulica"

        session["usuario_area"] = area_oficial
        print(f"[Agenda Fácil Debug] Área do prestador carregada com sucesso: {area_oficial}")

    except Exception as e:
        print(f"[Agenda Fácil Erro no formulário]: {e}")
        session["usuario_area"] = ""
    finally:
        cursor.close()
        conn.close()

    return render_template("formulario.html")


@app.route("/agendamentos")
def agendamentos():
    return render_template("agendamento.html")


@app.route("/sucesso-agendamento")
def sucesso_servico():
    return render_template("sucessoservico.html")


@app.route("/sucesso-orcamento")
def sucesso_orcamento():
    return render_template("sucesso_orcamento.html")


@app.route("/sucesso-conclusao")
def sucesso_conclusao():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))
    return render_template("sucesso_conclusao.html")


# =========================
# AUTENTICAÇÃO
# =========================
@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form["email"]
    senha = request.form["senha"]
    lembrar = request.form.get("lembrar")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cadastro_prestadores WHERE email=%s AND senha=%s", (email, senha))
    prestador = cursor.fetchone()

    if prestador:
        session.permanent = True if lembrar else False
        session["usuario_logado"] = email
        session["tipo_usuario"] = "prestador"
        session["usuario_nome"] = prestador["nome"] + " " + prestador["sobrenome"]

        # 🔑 força a conversão para string limpa e remove espaços
        session["usuario_area"] = str(prestador.get("areas_atuacao") or "").strip().lower()
        session["usuario_foto"] = prestador.get("foto") or ""

        cursor.close();
        conn.close()
        next_url = session.pop('next_url', None)
        return redirect(next_url if next_url else url_for("servicos"))
# =========================
# CADASTRO CLIENTE
# =========================
@app.route("/salvar", methods=["POST"])
def salvar():
    dados = (
        request.form["nome"], request.form["sobrenome"],
        request.form["data_nascimento"], request.form["sexo"],
        request.form["email"], request.form["senha"],
    )
    conn = connectar()
    cursor = conn.cursor()
    email_cadastro = request.form["email"].strip().lower()
    nome_cadastro = request.form["nome"].strip()
    sobrenome_cadastro = request.form["sobrenome"].strip()
    try:
        cursor.execute(
            "INSERT INTO cadastro_clientes (nome,sobrenome,data_nascimento,sexo,email,senha) VALUES (%s,%s,%s,%s,%s,%s)",
            dados
        )
        conn.commit()

        # ✅ após cadastro, já loga o usuário (cliente)
        session.permanent = True if request.form.get("lembrar") else False
        session["usuario_logado"] = email_cadastro
        session["tipo_usuario"] = "cliente"
        session["usuario_nome"] = f"{nome_cadastro} {sobrenome_cadastro}".strip()

        # Mensagem para modal pós-cadastro
        return redirect(url_for("index", cadastro="ok", tipo="cliente"))
    except Exception as e:
        return render_template("cadastro.html", erro=str(e))
    finally:
        cursor.close();
        conn.close()


# =========================
# CADASTRO PRESTADOR
# =========================
@app.route("/salvar_prestador", methods=["POST"])
def salvar_prestador():
    dados = (
        request.form["nome"], request.form["sobrenome"],
        request.form["data_nascimento"], request.form["sexo"],
        request.form["email"], request.form["senha"],
        request.form["areas_atuacao"], request.form["telefone"],
    )
    conn   = connectar()
    cursor = conn.cursor()
    email_cadastro = request.form["email"].strip().lower()
    nome_cadastro = request.form["nome"].strip()
    sobrenome_cadastro = request.form["sobrenome"].strip()
    try:
        cursor.execute(
            "INSERT INTO cadastro_prestadores (nome,sobrenome,data_nascimento,sexo,email,senha,areas_atuacao,telefone) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            dados
        )
        conn.commit()

        # ✅ após cadastro, já loga o usuário (prestador)
        session.permanent = True if request.form.get("lembrar") else False
        session["usuario_logado"] = email_cadastro
        session["tipo_usuario"] = "prestador"
        session["usuario_nome"] = f"{nome_cadastro} {sobrenome_cadastro}".strip()

        return redirect(url_for("index", cadastro="ok", tipo="prestador"))
    except Exception as e:
        return render_template("prestador.html", erro=str(e))
    finally:
        cursor.close(); conn.close()


# =========================
# AGENDAMENTO
# =========================
@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    dados = request.get_json()
    cliente_email = session["usuario_logado"]
    prestador_email = dados.get("prestador_email")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nome, sobrenome FROM cadastro_clientes WHERE email = %s", (cliente_email,))
    cliente = cursor.fetchone()

    cursor.execute("SELECT nome, sobrenome FROM cadastro_prestadores WHERE email = %s", (prestador_email,))
    prestador_row = cursor.fetchone()

    cursor.execute(
        "SELECT duracao FROM servicos_anunciados WHERE titulo = %s AND prestador_email = %s LIMIT 1",
        (dados.get("servico"), prestador_email)
    )
    servico_row = cursor.fetchone()
    duracao_horas = servico_row["duracao"] if servico_row else 1

    valores = (
        cliente_email, prestador_email,
        dados.get("servico"), dados.get("preco"),
        dados.get("data"), dados.get("horario"),
        dados.get("obs", ""),
    )

    try:
        cursor.execute(
            "INSERT INTO agendamentos (cliente_email,prestador_email,servico,preco,data_servico,horario,observacoes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            valores
        )
        conn.commit()
        agendamento_id = cursor.lastrowid

        nome_cliente = f"{cliente['nome']} {cliente['sobrenome']}" if cliente else cliente_email
        nome_prestador = f"{prestador_row['nome']} {prestador_row['sobrenome']}" if prestador_row else prestador_email

        msg_notif = (
            f"Novo agendamento de {nome_cliente} — "
            f"{dados.get('servico')} em {dados.get('data')} às {dados.get('horario')}"
        )
        criar_notificacao(prestador_email, "novo_agendamento", msg_notif, agendamento_id)

        calendar_url = gerar_url_google_agenda(
            titulo=dados.get("servico", "Serviço"), data_str=dados.get("data"),
            horario=dados.get("horario"), duracao_horas=duracao_horas,
            prestador_nome=nome_prestador, obs=dados.get("obs", ""),
        )
        google_token = session.get("google_token")
        if google_token:
            ok, _ = criar_evento_google_calendar(
                access_token=google_token, titulo=dados.get("servico", "Serviço"),
                data_str=dados.get("data"), horario=dados.get("horario"),
                duracao_horas=duracao_horas, prestador_nome=nome_prestador,
                cliente_email=cliente_email, prestador_email=prestador_email,
                obs=dados.get("obs", ""),
            )
        return jsonify({
            "mensagem": "Agendamento saved!",
            "id": agendamento_id,
            "nome_cliente": nome_cliente,
            "nome_prestador": nome_prestador,
            "email_cliente": cliente_email,
            "calendar_url": calendar_url,
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        cursor.close();
        conn.close()


# =========================
# SERVIÇOS PRESTADOR
# =========================
@app.route("/salvar_servico_prestador", methods=["POST"])
def salvar_servico_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json()
    email_prestador = session["usuario_logado"]

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT areas_atuacao FROM cadastro_prestadores WHERE email = %s", (email_prestador,))
        prestador_info = cursor.fetchone()

        if not prestador_info or not prestador_info.get("areas_atuacao"):
            return jsonify({"erro": "Prestador não tem área de atuação definida."}), 400

        area_oficial = prestador_info["areas_atuacao"]

        valores = (
            email_prestador,
            dados.get("titulo"),
            dados.get("descricao"),
            dados.get("preco"),
            area_oficial,
            dados.get("duracao"),
        )

        cursor.execute(
            "INSERT INTO servicos_anunciados (prestador_email,titulo,descricao,preco,area_atuacao,duracao) VALUES (%s,%s,%s,%s,%s,%s)",
            valores
        )
        conn.commit()
        return jsonify({"mensagem": "Serviço criado com sucesso na sua área!"})

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
    try:
        conn   = connectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.*, 
                p.nome AS prestador_nome,
                p.sobrenome AS prestador_sobrenome,
                p.areas_atuacao,
                p.telefone,
                COALESCE(ROUND(AVG(av.nota), 1), NULL) AS media_nota
            FROM servicos_anunciados s
            JOIN cadastro_prestadores p ON s.prestador_email = p.email
            LEFT JOIN agendamentos a
                   ON a.prestador_email = p.email
                  AND a.status = 'concluido'
            LEFT JOIN avaliacoes_prestadores av
                   ON av.agendamento_id = a.id
            GROUP BY s.id, p.nome, p.sobrenome, p.areas_atuacao, p.telefone
            ORDER BY s.id DESC
        """)
        dados = cursor.fetchall()

        for row in dados:
            row["avaliacao_media"] = row.get("media_nota")
            row["nome_prestador"] = f"{row.get('prestador_nome','')} {row.get('prestador_sobrenome','')}".strip() or "Prestador"

        cursor.close(); conn.close()
        return jsonify(dados)
    except Exception as e:
        print(f"[api/listar_servicos] erro: {e}")
        return jsonify({"erro": "Falha ao listar serviços", "detalhes": str(e)}), 500


@app.route("/api/meus_servicos")
def meus_servicos():
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401
    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM servicos_anunciados WHERE prestador_email=%s", (session["usuario_logado"],))
    dados = cursor.fetchall()
    cursor.close();
    conn.close()
    return jsonify(dados)


@app.route("/api/excluir_servico/<int:id>", methods=["DELETE"])
def excluir_servico(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401
    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM servicos_anunciados WHERE id=%s AND prestador_email=%s",
                   (id, session["usuario_logado"]))
    conn.commit()
    cursor.close();
    conn.close()
    return jsonify({"mensagem": "ok"})


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
    cursor.execute(
        "SELECT horario FROM agendamentos WHERE data_servico=%s AND prestador_email=%s AND status NOT IN ('cancelado')",
        (data, prestador_email)
    )
    rows = cursor.fetchall()
    cursor.close();
    conn.close()
    return jsonify([r["horario"] for r in rows])


# =========================
# API: PRESTADORES POR ÁREA
# =========================
@app.route("/api/prestadores_por_categoria")
def prestadores_por_categoria():
    categoria = request.args.get("categoria", "").lower()
    if not categoria:
        return jsonify([])
    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT nome, sobrenome, email FROM cadastro_prestadores WHERE LOWER(areas_atuacao) LIKE %s",
        (f"%{categoria}%",)
    )
    dados = cursor.fetchall()
    cursor.close();
    conn.close()
    return jsonify(dados)


# =========================
# CANCELAR AGENDAMENTO (CLIENTE)
# =========================
@app.route("/api/cancelar_agendamento/<int:id>", methods=["PATCH"])
def cancelar_agendamento(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM agendamentos WHERE id=%s AND cliente_email=%s", (id, session["usuario_logado"]))
    ag = cursor.fetchone()

    cursor.execute(
        "UPDATE agendamentos SET status='cancelado' WHERE id=%s AND cliente_email=%s",
        (id, session["usuario_logado"])
    )
    conn.commit()
    cursor.close();
    conn.close()

    if ag:
        criar_notificacao(
            ag["prestador_email"],
            "cancelamento",
            f"Agendamento #{id} foi cancelado pelo cliente — {ag.get('servico', '')} em {ag.get('data_servico', '')}",
            id,
        )
    return jsonify({"mensagem": "Agendamento cancelado"})


# =========================
# ATUALIZAR STATUS DO AGENDAMENTO (PRESTADOR) — CORRIGIDO
# =========================
@app.route("/api/atualizar_status/<int:id>", methods=["PATCH"])
def atualizar_status(id):
    if "usuario_logado" not in session:
        return jsonify({"erro": "não logado"}), 401

    dados = request.get_json() or {}
    novo_status = dados.get("status")
    STATUS_VALIDOS = ["pendente", "confirmado", "em_andamento", "concluido", "cancelado", "recusado"]

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM agendamentos WHERE id=%s", (id,))
    ag = cursor.fetchone()

    if not ag:
        cursor.close()
        conn.close()
        return jsonify({"erro": "Agendamento não encontrado"}), 404

    cursor.execute("UPDATE agendamentos SET status=%s WHERE id=%s", (novo_status, id))
    conn.commit()
    cursor.close()
    conn.close()

    if ag and novo_status == "concluido":
        nome_prestador = session.get("usuario_nome", "O prestador")
        msg_notif = f"Seu atendimento de '{ag.get('servico')}' foi concluído por {nome_prestador}! Clique aqui para deixar sua avaliação."
        criar_notificacao(
            ag["cliente_email"],
            "conclusao",
            msg_notif,
            id
        )
        print(f"[Agenda Fácil] Notificação de avaliação gerada com sucesso para o cliente: {ag['cliente_email']}")

    return jsonify({"mensagem": "Status updated"})


# =========================
# RECUSAR AGENDAMENTO (PRESTADOR)
# =========================
@app.route("/api/recusar_agendamento/<int:id>", methods=["PATCH"])
def recusar_agendamento(id):
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM agendamentos WHERE id=%s AND prestador_email=%s",
        (id, session["usuario_logado"]),
    )
    ag = cursor.fetchone()

    if not ag:
        cursor.close();
        conn.close()
        return jsonify({"erro": "Agendamento não encontrado"}), 404

    cursor.execute("UPDATE agendamentos SET status='recusado' WHERE id=%s", (id,))
    conn.commit()
    cursor.close();
    conn.close()

    try:
        criar_notificacao(
            ag["prestador_email"],
            "recusado",
            f"Agendamento #{id} foi recusado pelo prestador — {ag.get('servico', '')}",
            id,
        )
    except Exception:
        pass

    return jsonify({"mensagem": "Agendamento recusado"})


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
    cursor.close();
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
    cursor.close();
    conn.close()
    return jsonify(dados)


# =========================
# NOTIFICAÇÕES DO PRESTADOR
# =========================
@app.route("/api/notificacoes")
def listar_notificacoes():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, tipo, mensagem, lida, criada_em, agendamento_id
        FROM notificacoes
        WHERE prestador_email = %s
        ORDER BY criada_em DESC
        LIMIT 50
    """, (session["usuario_logado"],))
    notifs = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM notificacoes WHERE prestador_email=%s AND lida=0",
        (session["usuario_logado"],)
    )
    nao_lidas = cursor.fetchone()["total"]
    cursor.close();
    conn.close()

    for n in notifs:
        if hasattr(n.get("criada_em"), "isoformat"):
            n["criada_em"] = n["criada_em"].isoformat()

    return jsonify({"notificacoes": notifs, "nao_lidas": nao_lidas})


@app.route("/api/notificacoes/marcar_lida/<int:id>", methods=["PATCH"])
def marcar_notificacao_lida(id):
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notificacoes SET lida=1 WHERE id=%s AND prestador_email=%s",
        (id, session["usuario_logado"])
    )
    conn.commit()
    cursor.close();
    conn.close()
    return jsonify({"mensagem": "Notificação marcada como lida"})


@app.route("/api/notificacoes/marcar_todas_lidas", methods=["PATCH"])
def marcar_todas_lidas():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notificacoes SET lida=1 WHERE prestador_email=%s AND lida=0",
        (session["usuario_logado"],)
    )
    conn.commit()
    cursor.close();
    conn.close()
    return jsonify({"mensagem": "Todas as notificações marcadas como lidas"})


# =========================
# PERFIL DO PRESTADOR
# =========================
@app.route("/perfil_prestador/<email>")
def perfil_prestador(email):
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT nome, sobrenome, data_nascimento, sexo, email,
               areas_atuacao, bio, telefone, cidade, foto, certificados
        FROM cadastro_prestadores
        WHERE email = %s
    """, (email,))
    prestador = cursor.fetchone()
    if not prestador:
        cursor.close();
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
        WHERE a.prestador_email = %s
        ORDER BY
            CASE a.status
                WHEN 'em_andamento' THEN 1
                WHEN 'confirmado'   THEN 2
                WHEN 'pendente'     THEN 3
                WHEN 'concluido'    THEN 4
                WHEN 'cancelado'    THEN 5
                ELSE 6
            END,
            a.data_servico ASC, a.horario ASC
    """, (email,))
    todos_agendamentos = cursor.fetchall()

    for ag in todos_agendamentos:
        if ag.get("data_servico") and hasattr(ag["data_servico"], "strftime"):
            ag["data_servico"] = ag["data_servico"].strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT COUNT(*) AS total FROM agendamentos WHERE prestador_email=%s AND status='concluido'",
        (email,)
    )
    row = cursor.fetchone()
    agendamentos_count = row["total"] if row else 0

    cursor.close();
    conn.close()

    return render_template(
        "perfil-prestador.html",
        prestador=prestador,
        servicos=servicos,
        todos_agendamentos=todos_agendamentos,
        agendamentos_count=agendamentos_count,
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
    cursor.execute("SELECT * FROM cadastro_clientes WHERE email = %s", (session["usuario_logado"],))
    cliente = cursor.fetchone()

    cursor.execute("""
        SELECT a.*, p.nome AS prestador_nome, p.sobrenome AS prestador_sobrenome
        FROM agendamentos a
        LEFT JOIN cadastro_prestadores p ON a.prestador_email = p.email
        WHERE a.cliente_email = %s
        ORDER BY a.data_servico DESC
    """, (session["usuario_logado"],))
    agendamentos = cursor.fetchall()
    cursor.close();
    conn.close()

    return render_template("perfil-cliente.html", cliente=cliente, agendamentos=agendamentos)


@app.route("/meu_perfil")
def meu_perfil():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))
    if session.get("tipo_usuario") == "prestador":
        return redirect(url_for("perfil_prestador", email=session["usuario_logado"]))
    return redirect(url_for("perfil_cliente"))


# =========================
# UPLOAD FOTO DE PERFIL
# =========================
UPLOAD_FOLDER = os.path.join("static", "uploads", "fotos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/salvar_foto", methods=["POST"])
def salvar_foto():
    try:
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

        tipo = session.get("tipo_usuario", "cliente")
        conn = connectar()
        cursor = conn.cursor()
        table = "cadastro_prestadores" if tipo == "prestador" else "cadastro_clientes"
        cursor.execute(f"UPDATE {table} SET foto=%s WHERE email=%s", (url, session["usuario_logado"]))
        conn.commit()
        cursor.close();
        conn.close()

        session["usuario_foto"] = url
        return jsonify({"mensagem": "Foto salva!", "url": url})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    

# =========================
# UPLOAD DE CERTIFICADO
# =========================
CERT_FOLDER = os.path.join("static", "uploads", "certificados")
os.makedirs(CERT_FOLDER, exist_ok=True)


@app.route("/salvar_certificado", methods=["POST"])
def salvar_certificado():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401
    file = request.files.get("certificado")
    if not file:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    if ext not in {"pdf", "png", "jpg", "jpeg"}:
        return jsonify({"erro": "Use PDF, PNG ou JPG"}), 400

    import time
    email_safe = session["usuario_logado"].replace("@", "_").replace(".", "_")
    filename = f"{email_safe}_{int(time.time())}.{ext}"
    filepath = os.path.join(CERT_FOLDER, filename)
    file.save(filepath)
    url = "/" + filepath.replace("\\", "/")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT certificados FROM cadastro_prestadores WHERE email=%s", (session["usuario_logado"],))
    row = cursor.fetchone()
    existentes = row["certificados"] or "" if row else ""
    novos = (existentes + "," + url).strip(",")
    cursor.execute("UPDATE cadastro_prestadores SET certificados=%s WHERE email=%s", (novos, session["usuario_logado"]))
    conn.commit()
    cursor.close();
    conn.close()
    return jsonify({"mensagem": "Certificado salva!", "url": url})


# =========================
# EDITAR PERFIL
# =========================
@app.route("/editar_perfil_cliente", methods=["POST"])
def editar_perfil_cliente():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "cliente":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json() or {}
    nome = (dados.get("nome", "") or "").strip()
    sobrenome = (dados.get("sobrenome", "") or "").strip()

    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    conn = connectar()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE cadastro_clientes SET nome=%s,sobrenome=%s,telefone=%s,cidade=%s,sexo=%s WHERE email=%s",
            (
                nome,
                sobrenome,
                (dados.get("telefone", "") or "").strip(),
                (dados.get("cidade", "") or "").strip(),
                (dados.get("sexo", "") or "").strip(),
                session["usuario_logado"],
            )
        )
        conn.commit()
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

    session["usuario_nome"] = f"{nome} {sobrenome}".strip()
    return jsonify({"mensagem": "Perfil updated!"})


@app.route("/editar_perfil_prestador", methods=["POST"])
def editar_perfil_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return jsonify({"erro": "Acesso negado"}), 401
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome", "") or "").strip()
    sobrenome = (dados.get("sobrenome", "") or "").strip()
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    conn = connectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cadastro_prestadores SET nome=%s, sobrenome=%s, telefone=%s, sexo=%s WHERE email=%s",
        (nome, sobrenome, dados.get("telefone", "").strip(), dados.get("sexo", "").strip(), session["usuario_logado"])
    )
    conn.commit()
    cursor.close();
    conn.close()
    session["usuario_nome"] = f"{nome} {sobrenome}"
    return jsonify({"mensagem": "Perfil updated!"})


# =========================
# RECUPERAÇÃO DE SENHA
# =========================
@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "GET":
        return render_template("esqueci_senha.html")

    email = request.form.get("email")
    conn = connectar()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM cadastro_clientes WHERE email=%s", (email,))
    cliente = cursor.fetchone()

    cursor.execute("SELECT email FROM cadastro_prestadores WHERE email=%s", (email,))
    prestador = cursor.fetchone()
    cursor.close();
    conn.close()

    if cliente or prestador:
        token = serializer.dumps(email, salt='reset-senha')
        link = url_for('resetar_senha', token=token, _external=True)
        enviar_email_recuperacao(email, link)
        return render_template("esqueci_senha.html",
                               sucesso="Se o e-mail estiver cadastrado, as instruções serão enviadas.")

    return render_template("esqueci_senha.html",
                           sucesso="Se o e-mail estiver cadastrado, as instruções serão enviadas.")


@app.route("/resetar_senha/<token>", methods=["GET", "POST"])
def resetar_senha(token):
    try:
        email = serializer.loads(token, salt='reset-senha', max_age=900)
    except Exception:
        return "O link de recuperação é inválido ou expirou.", 4000

    if request.method == "GET":
        return render_template("resetar_senha.html", token=token)

    nova_senha = request.form.get("nova_senha")

    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE cadastro_clientes SET senha=%s WHERE email=%s", (nova_senha, email))
    cursor.execute("UPDATE cadastro_prestadores SET senha=%s WHERE email=%s", (nova_senha, email))
    conn.commit()
    cursor.close();
    conn.close()

    return redirect(url_for("login", mensagem="Senha atualizada com sucesso! Faça seu login."))


# =========================
# ADMIN — AUTH
# =========================
@app.route("/admin/login", methods=["GET"])
def admin_login_page():
    return render_template("admin/login.html", erro=None)


@app.route("/admin/autenticar", methods=["POST"])
def admin_autenticar():
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email, senha_hash, ativo FROM admins WHERE email=%s", (email,))
    admin = cursor.fetchone()
    cursor.close();
    conn.close()

    if not admin or not admin.get("ativo"):
        return render_template("login.html", erro="Credenciais inválidas")

    senha_hash = admin.get("senha_hash")
    try:
        if not bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8")):
            return render_template("login.html", erro="Credenciais inválidas")
    except Exception:
        return render_template("login.html", erro="Credenciais inválidas")

    session["usuario_logado"] = admin["email"]
    session["tipo_usuario"] = "admin"
    session["usuario_nome"] = admin["email"]
    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/api/metrics", methods=["GET"])
@admin_required
def admin_metrics():
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM cadastro_clientes")
    total_clients = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM cadastro_prestadores")
    total_providers = cursor.fetchone()["total"]

    hoje = datetime.now().date()
    cursor.execute("SELECT COUNT(*) AS total FROM agendamentos WHERE data_servico=%s", (hoje,))
    services_requested_today = cursor.fetchone()["total"]

    cursor.execute("SELECT status, COUNT(*) AS total FROM agendamentos GROUP BY status")
    status_counts = {"pendente": 0, "em_andamento": 0, "concluido": 0, "cancelado": 0}
    for r in cursor.fetchall():
        st = (r.get("status") or "").lower()
        if st in status_counts:
            status_counts[st] = int(r["total"] or 0)

    cursor.execute("""
        SELECT DATE(data_servico) AS dia, COUNT(*) AS total
        FROM agendamentos
        WHERE data_servico >= (CURDATE() - INTERVAL 6 DAY)
        GROUP BY dia
        ORDER BY dia ASC
    """)
    day_rows = cursor.fetchall()
    labels, values = [], []
    for dr in day_rows:
        dia = dr["dia"]
        labels.append(dia.strftime("%d/%m") if hasattr(dia, "strftime") else str(dia))
        values.append(int(dr["total"] or 0))

    cursor.execute("""
        SELECT
            a.prestador_email AS email,
            c.nome AS prestador_nome,
            c.sobrenome AS prestador_sobrenome,
            COUNT(*) AS agendamentos_count,
            SUM(CASE WHEN a.status='concluido' THEN 1 ELSE 0 END) AS concluido_count
        FROM agendamentos a
        LEFT JOIN cadastro_prestadores c ON c.email = a.prestador_email
        WHERE a.prestador_email IS NOT NULL
        GROUP BY a.prestador_email, c.nome, c.sobrenome
        ORDER BY concluido_count DESC, agendamentos_count DESC
        LIMIT 5
    """)
    top_prestadores = [
        {
            "email": r["email"],
            "prestador_nome": f"{r.get('prestador_nome') or ''} {r.get('prestador_sobrenome') or ''}".strip(),
            "agendamentos_count": int(r["agendamentos_count"] or 0),
            "concluido_count": int(r["concluido_count"] or 0),
        }
        for r in cursor.fetchall()
    ]

    cursor.execute("SELECT COUNT(*) AS total FROM agendamentos WHERE status='concluido'")
    total_concluidos = cursor.fetchone()["total"]

    cursor.close();
    conn.close()

    return jsonify({
        "total_clients": total_clients,
        "total_providers": total_providers,
        "services_requested_today": services_requested_today,
        "status_counts": status_counts,
        "solicitations_last_7": {"labels": labels, "values": values},
        "top_prestadores": top_prestadores,
        "total_concluidos": total_concluidos,
    })


@app.route("/admin/solicitacoes")
@admin_required
def admin_solicitacoes():
    return render_template("admin/solicitacoes.html")


@app.route("/admin/clientes")
@admin_required
def admin_clientes():
    return render_template("admin/clientes.html")


@app.route("/admin/prestadores")
@admin_required
def admin_prestadores():
    return render_template("admin/prestadores.html")


@app.route("/admin/notificacoes")
@admin_required
def admin_notificacoes():
    return render_template("admin/notificacoes.html")


@app.route("/agendamento_confirmado")
def agendamento_confirmado():
    if "usuario_logado" not in session:
        return redirect(url_for("login"))
    ag_id = request.args.get("id")
    if not ag_id:
        return redirect(url_for("servicos"))
    return redirect(url_for("sucesso_servico", id=ag_id))


# =========================
# ROTAS DE AVALIAÇÃO — Agenda Fácil
# =========================
@app.route("/avaliar")
def avaliar():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "cliente":
        return redirect(url_for("servicos"))

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                a.id,
                a.servico,
                a.prestador_email,
                a.data_servico,
                a.horario,
                p.nome        AS prestador_nome,
                p.sobrenome   AS prestador_sobrenome
            FROM agendamentos a
            LEFT JOIN cadastro_prestadores p
                   ON a.prestador_email = p.email
            LEFT JOIN avaliacoes_prestadores av
                   ON av.agendamento_id = a.id
            WHERE a.cliente_email = %s
              AND a.status        = 'concluido'
              AND av.id           IS NULL
            ORDER BY a.data_servico DESC
            LIMIT 1
        """, (session["usuario_logado"],))
        pendente = cursor.fetchone()

        if pendente and pendente.get("data_servico"):
            pendente["data_servico"] = str(pendente["data_servico"])

        if not pendente:
            return redirect(url_for("servicos"))

        return render_template("avaliar.html", pendente=pendente)
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass


@app.route("/api/avaliacoes_pendentes")
def avaliacoes_pendentes():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "cliente":
        return jsonify({"pendente": None})

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                a.id,
                a.servico,
                a.prestador_email,
                a.data_servico,
                a.horario,
                p.nome        AS prestador_nome,
                p.sobrenome   AS prestador_sobrenome
            FROM agendamentos a
            LEFT JOIN cadastro_prestadores p
                   ON a.prestador_email = p.email
            LEFT JOIN avaliacoes_prestadores av
                   ON av.agendamento_id = a.id
            WHERE a.cliente_email = %s
              AND a.status        = 'concluido'
              AND av.id           IS NULL
            ORDER BY a.data_servico DESC
            LIMIT 1
        """, (session["usuario_logado"],))
        pendente = cursor.fetchone()

        if pendente and pendente.get("data_servico"):
            pendente["data_servico"] = str(pendente["data_servico"])

        return jsonify({"pendente": pendente})
    except Exception as e:
        print(f"[Avaliação Pendente] Erro: {e}")
        return jsonify({"pendente": None})
    finally:
        cursor.close();
        conn.close()


@app.route("/api/salvar_avaliacao", methods=["POST"])
def salvar_avaliacao():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "cliente":
        return jsonify({"erro": "Acesso negado"}), 401

    dados = request.get_json() or {}
    agendamento_id = dados.get("agendamento_id")
    nota = dados.get("nota")
    comentario = (dados.get("comentario") or "").strip()

    if not agendamento_id or nota is None:
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        nota = int(nota)
    except (ValueError, TypeError):
        return jsonify({"erro": "Nota inválida"}), 400

    if not (1 <= nota <= 5):
        return jsonify({"erro": "Nota deve ser entre 1 e 5"}), 400

    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM agendamentos
            WHERE id = %s AND cliente_email = %s AND status = 'concluido'
        """, (agendamento_id, session["usuario_logado"]))
        ag = cursor.fetchone()

        if not ag:
            return jsonify({"erro": "Agendamento não encontrado ou não autorizado"}), 403

        cursor.execute("SELECT id FROM avaliacoes_prestadores WHERE agendamento_id = %s", (agendamento_id,))
        if cursor.fetchone():
            return jsonify({"erro": "Este serviço já foi avaliado"}), 409

        cursor.execute("""
            INSERT INTO avaliacoes_prestadores
                (prestador_email, cliente_email, agendamento_id, nota, comentario)
            VALUES (%s, %s, %s, %s, %s)
        """, (ag["prestador_email"], session["usuario_logado"], agendamento_id, nota, comentario))
        conn.commit()
        return jsonify({"mensagem": "Avaliação salva com sucesso!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        cursor.close();
        conn.close()


@app.route("/api/stats_prestador/<email>")
def stats_prestador(email):
    conn = connectar()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                COUNT(*)                                          AS total,
                COALESCE(AVG(nota), 0)                           AS media,
                SUM(CASE WHEN nota = 5 THEN 1 ELSE 0 END)       AS cinco,
                SUM(CASE WHEN nota = 4 THEN 1 ELSE 0 END)       AS quatro,
                SUM(CASE WHEN nota = 3 THEN 1 ELSE 0 END)       AS tres,
                SUM(CASE WHEN nota = 2 THEN 1 ELSE 0 END)       AS dois,
                SUM(CASE WHEN nota = 1 THEN 1 ELSE 0 END)       AS um
            FROM avaliacoes_prestadores
            WHERE prestador_email = %s
        """, (email,))
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT
                av.nota,
                av.comentario,
                av.criado_em,
                c.nome      AS cliente_nome,
                c.sobrenome AS cliente_sobrenome
            FROM avaliacoes_prestadores av
            LEFT JOIN cadastro_clientes c ON av.cliente_email = c.email
            WHERE av.prestador_email = %s
            ORDER BY av.criado_em DESC
            LIMIT 50
        """, (email,))
        avaliacoes = cursor.fetchall()

        for av in avaliacoes:
            if hasattr(av.get("criado_em"), "isoformat"):
                av["criado_em"] = av["criado_em"].isoformat()

        return jsonify({
            "total": int(stats["total"]) if stats else 0,
            "media": round(float(stats["media"]), 1) if stats and stats["media"] else 0,
            "distribuicao": {
                "5": int(stats["cinco"] or 0),
                "4": int(stats["quatro"] or 0),
                "3": int(stats["tres"] or 0),
                "2": int(stats["dois"] or 0),
                "1": int(stats["um"] or 0),
            },
            "avaliacoes": avaliacoes,
        })
    except Exception as e:
        return jsonify({"total": 0, "media": 0, "distribuicao": {}, "avaliacoes": [], "erro": str(e)})
    finally:
        cursor.close();
        conn.close()


@app.route("/api/checar_recusados_cliente")
def checar_recusados_cliente():
    if not session.get('usuario_logado'):
        return jsonify({"recusado": None})

    email_cliente = session.get('usuario_logado')
    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, servico 
        FROM agendamentos 
        WHERE cliente_email = %s AND status = 'recusado' AND alerta_visto = 0
        LIMIT 1
    """, (email_cliente,))

    resultado = cursor.fetchone()
    cursor.close();
    conn.close()

    return jsonify({"recusado": resultado})


@app.route("/api/marcar_alerta_visto/<int:id>", methods=["PATCH"])
def marcar_alerta_visto(id):
    conn = connectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE agendamentos SET alerta_visto = 1 WHERE id = %s", (id,))
    conn.commit()
    cursor.close();
    conn.close()
    return jsonify({"mensagem": "Alerta marcado como visto"})


if __name__ == "__main__":
    app.run(debug=True)