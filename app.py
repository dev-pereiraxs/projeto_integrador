from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv
from flask import jsonify

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

@app.route("/painel")
def painel():
    return render_template("painel.html")

@app.route("/formulario")
def formulario():
    return render_template("formulario.html")    

@app.route('/sucesso-servico')
def sucesso_servico():
    return render_template('sucessoservico.html')

@app.route('/agendamentos')
def agendamentos():
    return render_template('agendamento.html')


@app.route("/autenticar", methods=["POST"])
def autenticar():
    email = request.form["email"]
    senha = request.form["senha"]

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    # 1ª TENTATIVA: Procura na tabela de PRESTADORES primeiro (Prioridade máxima!)
    sql_prestador = "SELECT * FROM cadastro_prestadores WHERE email = %s AND senha = %s"
    cursor.execute(sql_prestador, (email, senha))
    usuario_prestador = cursor.fetchone()

    if usuario_prestador:
        # Achou na tabela de prestadores!
        session["usuario_logado"] = email
        session["tipo_usuario"] = "prestador"
        cursor.close()
        conn.close()
        return redirect(url_for('servicos'))

    # 2ª TENTATIVA: Se não for prestador, aí sim procura na tabela de CLIENTES
    sql_cliente = "SELECT * FROM cadastro_clientes WHERE email = %s AND senha = %s"
    cursor.execute(sql_cliente, (email, senha))
    usuario_cliente = cursor.fetchone()

    # Fechamos o banco aqui, pois acabaram as buscas
    cursor.close()
    conn.close()

    if usuario_cliente:
        # Achou na tabela de clientes!2
        session["usuario_logado"] = email
        session["tipo_usuario"] = "cliente"
        return redirect(url_for('servicos'))

    else:
        # Se não achou em NENHUMA das duas tabelas, aí sim é erro!
        mensagem_erro = "E-mail ou senha incorretos. Tente novamente."
        return render_template("login.html", erro=mensagem_erro)


@app.route("/salvar_prestador", methods=["POST"])
def salvar_prestador():
    nome = request.form["nome"]
    sobrenome = request.form["sobrenome"]
    data_nascimento = request.form["data_nascimento"]
    sexo = request.form["sexo"]
    email = request.form["email"]
    senha = request.form["senha"]

    # Aqui pegamos aquele input invisível que o JS criou!
    areas_atuacao = request.form["areas_atuacao"]

    conn = connectar()
    cursor = conn.cursor()

    sql = """
    INSERT INTO cadastro_prestadores 
    (nome, sobrenome, data_nascimento, sexo, email, senha, areas_atuacao)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    valores = (nome, sobrenome, data_nascimento, sexo, email, senha, areas_atuacao)

    try:
        cursor.execute(sql, valores)
        conn.commit()
        return redirect(url_for('index'))  # Manda de volta para a tela inicial

    except mysql.connector.Error as err:
        if err.errno == 1062:
            mensagem_erro = "Este e-mail já está cadastrado como prestador."
        else:
            mensagem_erro = f"Erro interno: {err}"

        return render_template("prestador.html", erro=mensagem_erro)

    finally:
        cursor.close()
        conn.close()


@app.route("/salvar_agendamento", methods=["POST"])
def salvar_agendamento():
    # 1. Trava de segurança: garantir que tem alguém logado
    if "usuario_logado" not in session:
        return {"erro": "Usuário não está logado."}, 401

    email_cliente = session["usuario_logado"]

    # 2. Recebe o pacote JSON que o JavaScript vai enviar
    dados = request.get_json()

    servico = dados.get("servico")
    preco = dados.get("preco")
    data_servico = dados.get("data")
    horario = dados.get("horario")

    # 3. Salva tudo no banco de dados
    conn = connectar()
    cursor = conn.cursor()

    sql = """
    INSERT INTO agendamentos (cliente_email, servico, preco, data_servico, horario)
    VALUES (%s, %s, %s, %s, %s)
    """
    valores = (email_cliente, servico, preco, data_servico, horario)

    try:
        cursor.execute(sql, valores)
        conn.commit()
        return {"mensagem": "Agendamento salvo com sucesso no banco!"}, 200
    except Exception as e:
        return {"erro": f"Erro interno: {e}"}, 500
    finally:
        cursor.close()
        conn.close()


@app.route("/salvar_servico_prestador", methods=["POST"])
def salvar_servico_prestador():
    if "usuario_logado" not in session or session.get("tipo_usuario") != "prestador":
        return {"erro": "Acesso negado. Apenas prestadores podem anunciar."}, 401

    dados = request.get_json()
    email_prestador = session["usuario_logado"]

    titulo = dados.get("titulo")
    categoria = dados.get("categoria")
    descricao = dados.get("descricao")
    preco = dados.get("preco")

    # PEGAMOS A DURAÇÃO AQUI AGORA!
    duracao = dados.get("duracao")

    conn = connectar()
    cursor = conn.cursor()

    # Atualizamos o SQL para incluir a duração
    sql = """
    INSERT INTO servicos_anunciados (prestador_email, titulo, descricao, preco, area_atuacao, duracao)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    valores = (email_prestador, titulo, descricao, preco, categoria, duracao)

    try:
        cursor.execute(sql, valores)
        conn.commit()
        return {"mensagem": "Serviço cadastrado com sucesso!"}, 200
    except Exception as e:
        return {"erro": f"Erro interno: {e}"}, 500
    finally:
        cursor.close()
        conn.close()

@app.route("/api/listar_servicos", methods=["GET"])
def api_listar_servicos():
    conn = connectar()
    # dictionary=True é importante para o JS entender os nomes das colunas
    cursor = conn.cursor(dictionary=True)

    # Busca todos os serviços do mais recente para o mais antigo
    cursor.execute("SELECT * FROM servicos_anunciados ORDER BY id DESC")
    lista_servicos = cursor.fetchall()

    cursor.close()
    conn.close()

    # jsonify transforma a lista do Python em um formato que o JavaScript adora!
    return jsonify(lista_servicos)


# 1. Rota para buscar os serviços apenas do prestador logado
@app.route("/api/meus_servicos", methods=["GET"])
def api_meus_servicos():
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    email_prestador = session["usuario_logado"]

    conn = connectar()
    cursor = conn.cursor(dictionary=True)

    # Busca apenas onde o email bate com o do prestador logado
    sql = "SELECT * FROM servicos_anunciados WHERE prestador_email = %s ORDER BY id DESC"
    cursor.execute(sql, (email_prestador,))
    meus_servicos = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(meus_servicos)


# 2. Rota para deletar um serviço do banco de dados
@app.route("/api/excluir_servico/<int:id_servico>", methods=["DELETE"])
def api_excluir_servico(id_servico):
    if "usuario_logado" not in session:
        return jsonify({"erro": "Usuário não logado"}), 401

    email_prestador = session["usuario_logado"]

    conn = connectar()
    cursor = conn.cursor()

    # Deleta o serviço pelo ID, mas garante que é do dono certo
    sql = "DELETE FROM servicos_anunciados WHERE id = %s AND prestador_email = %s"
    cursor.execute(sql, (id_servico, email_prestador))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"mensagem": "Serviço excluído com sucesso!"}), 200

if __name__ == "__main__":
    app.run(debug=True)