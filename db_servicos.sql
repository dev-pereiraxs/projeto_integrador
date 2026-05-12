-- =============================================
--  Agenda Fácil — Banco de Dados Completo
--  Execute do zero no MySQL / phpMyAdmin
-- =============================================

CREATE DATABASE servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servicos;

-- =============================================
-- 1. CLIENTES
-- =============================================
CREATE TABLE cadastro_clientes (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)  NOT NULL,
    sobrenome       VARCHAR(100)  NOT NULL,
    data_nascimento DATE,
    sexo            VARCHAR(20),
    email           VARCHAR(150)  NOT NULL UNIQUE,
    senha           VARCHAR(255),
    criado_em       DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. PRESTADORES
-- =============================================
CREATE TABLE cadastro_prestadores (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)  NOT NULL,
    sobrenome       VARCHAR(100)  NOT NULL,
    data_nascimento DATE,
    sexo            VARCHAR(20),
    email           VARCHAR(150)  NOT NULL UNIQUE,
    senha           VARCHAR(255)  NOT NULL,
    areas_atuacao   TEXT,
    criado_em       DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 3. SERVIÇOS ANUNCIADOS
-- =============================================
CREATE TABLE servicos_anunciados (
    id              INT            AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)   NOT NULL,
    titulo          VARCHAR(150)   NOT NULL,
    descricao       TEXT,
    preco           DECIMAL(10,2)  NOT NULL,
    area_atuacao    VARCHAR(100),
    duracao         VARCHAR(50),
    criado_em       DATETIME       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (prestador_email)
        REFERENCES cadastro_prestadores(email)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- 4. AGENDAMENTOS
-- =============================================
CREATE TABLE agendamentos (
    id              INT            AUTO_INCREMENT PRIMARY KEY,
    cliente_email   VARCHAR(150)   NOT NULL,
    prestador_email VARCHAR(150),
    servico         VARCHAR(200)   NOT NULL,
    preco           DECIMAL(10,2),
    data_servico    DATE           NOT NULL,
    horario         VARCHAR(10)    NOT NULL,
    status          ENUM('pendente','confirmado','em_andamento','concluido','cancelado')
                                   DEFAULT 'pendente',
    observacoes     TEXT,
    criado_em       DATETIME       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cliente   (cliente_email),
    INDEX idx_prestador (prestador_email),
    INDEX idx_status    (status),
    INDEX idx_data      (data_servico)
);

-- =====================================================
-- AGENDA FÁCIL - SISTEMA ADMINISTRATIVO
-- =====================================================

CREATE DATABASE IF NOT EXISTS agenda_facil;
USE servicos;

-- =====================================================
-- 1. ADMINISTRADORES
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
-- 2. HISTÓRICO DE AÇÕES ADMIN
-- =====================================================

CREATE TABLE admin_logs (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    admin_email       VARCHAR(150) NOT NULL,
    acao              VARCHAR(255) NOT NULL,
    entidade          VARCHAR(100),
    entidade_id       VARCHAR(100),
    detalhes          TEXT,
    ip_address        VARCHAR(60),
    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_admin_logs_admin (admin_email)
);

-- =====================================================
-- 3. CATEGORIAS DE SERVIÇOS
-- =====================================================

CREATE TABLE categorias_servicos (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nome              VARCHAR(100) NOT NULL UNIQUE,
    icone             VARCHAR(50) DEFAULT NULL,
    cor               VARCHAR(20) DEFAULT NULL,
    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em     DATETIME DEFAULT NULL
                         ON UPDATE CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. DENÚNCIAS
-- =====================================================

CREATE TABLE denuncias (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    denunciante_email    VARCHAR(150) NOT NULL,
    alvo_tipo            VARCHAR(50) NOT NULL,
    alvo_id              VARCHAR(100) NOT NULL,
    categoria            VARCHAR(100) DEFAULT NULL,
    descricao            TEXT NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'aberta',
    criado_em            DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em        DATETIME DEFAULT NULL
                           ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_denuncias_status (status)
);

-- =====================================================
-- 5. TICKETS DE SUPORTE
-- =====================================================

CREATE TABLE tickets (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    solicitante_email    VARCHAR(150) NOT NULL,
    categoria            VARCHAR(100) DEFAULT NULL,
    assunto              VARCHAR(150) NOT NULL,
    mensagem_inicial     TEXT NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'aberto',
    criado_em            DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em        DATETIME DEFAULT NULL
                           ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tickets_status (status)
);

-- =====================================================
-- 6. RESPOSTAS DOS TICKETS
-- =====================================================

CREATE TABLE ticket_respostas (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id         INT NOT NULL,
    autor_email       VARCHAR(150) NOT NULL,
    mensagem          TEXT NOT NULL,
    criado_em         DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ticket_respostas_ticket
        FOREIGN KEY (ticket_id)
        REFERENCES tickets(id)
        ON DELETE CASCADE
);

-- =====================================================
-- 7. NOTIFICAÇÕES
-- =====================================================

CREATE TABLE notificacoes (
    id                     INT AUTO_INCREMENT PRIMARY KEY,
    tipo                   VARCHAR(30) NOT NULL DEFAULT 'global',
    destinatario_email     VARCHAR(150) DEFAULT NULL,
    titulo                 VARCHAR(150) NOT NULL,
    mensagem               TEXT NOT NULL,
    lida                   TINYINT(1) NOT NULL DEFAULT 0,
    criado_em              DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_notificacoes_dest (destinatario_email)
);

-- =====================================================
-- 8. AVALIAÇÕES DOS PRESTADORES
-- =====================================================

CREATE TABLE avaliacoes_prestadores (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    prestador_email     VARCHAR(150) NOT NULL,
    cliente_email       VARCHAR(150) NOT NULL,
    agendamento_id      INT,
    nota                INT NOT NULL,
    comentario          TEXT,
    criado_em           DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_avaliacoes_prestador (prestador_email)
);

-- =====================================================
-- 9. INSERT DOS ADMINISTRADORES
-- Senha padrão: 123@senac
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
    '$2b$12$3euPcmQFCiblsZeEu5s7pugr8S0dM6D8w0S6p1L6Q2x5wY3jVn5xK',
    'admin',
    1
),
(
    'lucas@admin.com.br',
    '$2b$12$3euPcmQFCiblsZeEu5s7pugr8S0dM6D8w0S6p1L6Q2x5wY3jVn5xK',
    'admin',
    1
);

-- =====================================================
-- 10. CATEGORIAS INICIAIS
-- =====================================================

-- =====================================================
-- CATEGORIAS DE SERVIÇOS
-- =====================================================

INSERT INTO categorias_servicos (
    nome,
    icone,
    cor
)
VALUES
('Mecânica', 'wrench', '#f97316'),
('Elétrica', 'bolt', '#eab308'),
('Tecnologia', 'monitor-smartphone', '#3b82f6'),
('Reformas', 'hammer', '#ef4444'),
('Hidráulica', 'droplets', '#06b6d4'),
('Limpeza', 'sparkles', '#10b981');

-- =====================================================
-- FIM
-- =====================================================
SHOW TABLES;
USE servicos;
select * from agendamentos;