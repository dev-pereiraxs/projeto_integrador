from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
app = Flask(__name__)
app.secret_key = '2a962fb071252f38d97cafb2f3a84c80c49568ebb87bc1b1'

oauth = OAuth(app)
google = oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


def connectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="servicos"
    )


@app.route("/login-google")
def login_google():
    redirect_uri = "http://127.0.0.1:5000/callback"
    return google.authorize_redirect(redirect_uri)


@app.route("/callback")
def auth():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    if user_info:
        nome = user_info.get('given_name')
        sobrenome = user_info.get('family_name')
        email = user_info.get('email')

        salvar_usuario_google(nome, sobrenome, email)
        return f"Olá {nome}, seu cadastro via Google foi realizado com sucesso!"
    return "Erro ao obter dados do Google."


def salvar_usuario_google(nome, sobrenome, email):
    conn = connectar()
    cursor = conn.cursor()
    sql = "INSERT INTO cadastro_clientes (nome, sobrenome, email) VALUES (%s, %s, %s)"
    try:
        cursor.execute(sql, (nome, sobrenome, email))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao salvar Google: {err}")
    finally:
        cursor.close()
        conn.close()


@app.route("/salvar", methods=["POST"])
def salvar():
    nome = request.form["nome"]
    sobrenome = request.form["sobrenome"]
    data_nascimento = request.form["data_nascimento"]
    sexo = request.form["sexo"]  # <--- Pegando o sexo do HTML
    email = request.form["email"]
    senha = request.form["senha"]

    conn = connectar()
    cursor = conn.cursor()

    # Adicionamos a coluna sexo e mais um %s nos VALUES
    sql = """
    INSERT INTO cadastro_clientes 
    (nome, sobrenome, data_nascimento, sexo, email, senha)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    # Adicionamos a variável sexo na lista de valores
    valores = (nome, sobrenome, data_nascimento, sexo, email, senha)

    try:
        cursor.execute(sql, valores)
        conn.commit()
        return redirect(url_for('index'))

    except mysql.connector.Error as err:
        if err.errno == 1062:
            mensagem_erro = "Este e-mail já está cadastrado. Tente fazer login ou use outro e-mail."
        else:
            mensagem_erro = "Ocorreu um erro interno. Tente novamente mais tarde."

        return render_template("cadastro.html", erro=mensagem_erro)

    finally:
        cursor.close()
        conn.close()
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
    return render_template("servicos.html")


@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html")


@app.route("/perfil")
def perfil():
    return render_template("cliente.html")


@app.route("/prestador")
def prestador():
    return render_template('prestador.html')


@app.route("/orcamento")
def orcamento():
    return render_template("orcamentos.html")

@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form["email"]
    senha = request.form["senha"]

    conn = connectar()
    cursor = conn.cursor()

    sql = "SELECT * FROM cadastro_clientes WHERE email = %s AND senha = %s"
    cursor.execute(sql, (email, senha))

    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    if usuario:
        session["usuario_logado"] = email
        return redirect(url_for('servicos'))
    else:
        mensagem_erro = "E-mail ou senha incorretos. Tente novamente."
        return render_template("login.html", erro=mensagem_erro)
if __name__ == "__main__":
    app.run(debug=True)