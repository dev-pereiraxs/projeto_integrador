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
    idade = request.form["idade"]
    email = request.form["email"]
    senha = request.form["senha"]
    
    conn = connectar()
    cursor = conn.cursor()
    
    sql = """
    INSERT INTO cadastro_clientes 
    (nome, sobrenome, idade, email, senha)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    valores = (nome, sobrenome, idade, email, senha)
    try:
        cursor.execute(sql, valores)
        conn.commit() 
        return "Cadastro realizado com sucesso!" 
    except mysql.connector.Error as err:
        return f"Erro ao cadastrar {err}"
    finally:
        cursor.close()
        conn.close()

@app.route("/")
def index():
    return "Página Inicial - O servidor está rodando!"

@app.route("/servicos")
def servicos():
    return render_template("servicos.html")

if __name__ == "__main__":
    app.run(debug=True)
    
