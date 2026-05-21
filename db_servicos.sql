-- =====================================================
-- AGENDA FÁCIL — BANCO DE DADOS COMPLETO
-- MySQL / phpMyAdmin
-- =====================================================

CREATE DATABASE IF NOT EXISTS servicos
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE servicos;

-- =====================================================
-- CLIENTES
-- =====================================================

CREATE TABLE cadastro_clientes (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nome              VARCHAR(100) NOT NULL,
    sobrenome         VARCHAR(100) NOT NULL,
    data_nascimento   DATE,
    sexo              VARCHAR(20),
    email             VARCHAR(150) NOT NULL UNIQUE,
    senha             VARCHAR(255),
    foto              TEXT,
    telefone          VARCHAR(30),
    cidade            VARCHAR(100),
    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRESTADORES
-- =====================================================

CREATE TABLE cadastro_prestadores (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nome              VARCHAR(100) NOT NULL,
    sobrenome         VARCHAR(100) NOT NULL,
    data_nascimento   DATE,
    sexo              VARCHAR(20),
    email             VARCHAR(150) NOT NULL UNIQUE,
    senha             VARCHAR(255) NOT NULL,

    areas_atuacao     TEXT,
    bio               TEXT,
    telefone          VARCHAR(30),
    cidade            VARCHAR(100),

    foto              TEXT,
    certificados      LONGTEXT,

    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SERVIÇOS ANUNCIADOS
-- =====================================================

CREATE TABLE servicos_anunciados (
    id                INT AUTO_INCREMENT PRIMARY KEY,

    prestador_email   VARCHAR(150) NOT NULL,

    titulo            VARCHAR(150) NOT NULL,
    descricao         TEXT,

    preco             DECIMAL(10,2) NOT NULL,
    area_atuacao      VARCHAR(100),
    duracao           VARCHAR(50),

    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_servico_prestador
        FOREIGN KEY (prestador_email)
        REFERENCES cadastro_prestadores(email)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =====================================================
-- AGENDAMENTOS
-- =====================================================

CREATE TABLE agendamentos (
    id                INT AUTO_INCREMENT PRIMARY KEY,

    cliente_email     VARCHAR(150) NOT NULL,
    prestador_email   VARCHAR(150),

    servico           VARCHAR(200) NOT NULL,
    preco             DECIMAL(10,2),

    data_servico      DATE NOT NULL,
    horario           VARCHAR(10) NOT NULL,

    status ENUM(
        'pendente',
        'confirmado',
        'em_andamento',
        'concluido',
        'cancelado',
        'recusado'
    ) DEFAULT 'pendente',

    observacoes       TEXT,

    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cliente     (cliente_email),
    INDEX idx_prestador   (prestador_email),
    INDEX idx_status      (status),
    INDEX idx_data        (data_servico)
);

-- =====================================================
-- ADMINISTRADORES
-- =====================================================

CREATE TABLE admins (
    id                INT AUTO_INCREMENT PRIMARY KEY,

    email             VARCHAR(150) NOT NULL UNIQUE,
    senha_hash        VARCHAR(255) NOT NULL,

    nivel             VARCHAR(50) NOT NULL DEFAULT 'admin',
    ativo             TINYINT(1) NOT NULL DEFAULT 1,

    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_admin_ativo (ativo)
);

-- =====================================================
-- NOTIFICAÇÕES
-- =====================================================

CREATE TABLE notificacoes (
    id                      INT AUTO_INCREMENT PRIMARY KEY,

    tipo                    VARCHAR(30) NOT NULL DEFAULT 'global',

    destinatario_email      VARCHAR(150),

    titulo                  VARCHAR(150) NOT NULL,
    mensagem                TEXT NOT NULL,

    lida                    TINYINT(1) NOT NULL DEFAULT 0,

    criado_em               DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_notificacoes_dest (destinatario_email)
);

-- =====================================================
-- DENÚNCIAS
-- =====================================================

CREATE TABLE denuncias (
    id                    INT AUTO_INCREMENT PRIMARY KEY,

    denunciante_email     VARCHAR(150) NOT NULL,

    alvo_tipo             VARCHAR(50) NOT NULL,
    alvo_id               VARCHAR(100) NOT NULL,

    categoria             VARCHAR(100),
    descricao             TEXT NOT NULL,

    status                VARCHAR(20) NOT NULL DEFAULT 'aberta',

    criado_em             DATETIME DEFAULT CURRENT_TIMESTAMP,

    atualizado_em         DATETIME DEFAULT NULL
                              ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_denuncias_status (status)
);

-- =====================================================
-- AVALIAÇÕES DOS PRESTADORES
-- =====================================================

CREATE TABLE avaliacoes_prestadores (
    id                    INT AUTO_INCREMENT PRIMARY KEY,

    prestador_email       VARCHAR(150) NOT NULL,
    cliente_email         VARCHAR(150) NOT NULL,

    agendamento_id        INT,

    nota                  INT NOT NULL,
    comentario            TEXT,

    criado_em             DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_avaliacoes_prestador (prestador_email)
);

-- =====================================================
-- ADMIN PADRÃO
-- Senha: 123@senac
-- =====================================================

INSERT INTO admins (
    email,
    senha_hash,
    nivel,
    ativo
)
VALUES
(
    'felipe@admin.com.br',
    '$2b$12$rpGugLoX1fXJwCIqy74HK.XRI5Q3TDQV7FQ/tqDNoDZNNGsv1zcbq',
    'admin',
    1
);

-- =====================================================
-- CONSULTAS ÚTEIS
-- =====================================================

SHOW TABLES;

SELECT * FROM admins;

SELECT * FROM agendamentos;

SELECT email, ativo FROM admins;

SELECT LENGTH(senha_hash)
FROM admins
WHERE email = 'felipe@admin.com.br';