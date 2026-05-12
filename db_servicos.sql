-- =============================================
--  Agenda Fácil — Banco de Dados Completo
--  Gerado com base no app.py
--  Execute do zero no MySQL / phpMyAdmin
-- =============================================

DROP DATABASE IF EXISTS servicos;
CREATE DATABASE servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servicos;

-- =============================================
-- 1. CLIENTES
-- =============================================
CREATE TABLE cadastro_clientes (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    nome             VARCHAR(100)  NOT NULL,
    sobrenome        VARCHAR(100)  NOT NULL,
    data_nascimento  DATE,
    sexo             VARCHAR(20),
    email            VARCHAR(150)  NOT NULL UNIQUE,
    senha            VARCHAR(255),                      -- bcrypt hash
    foto_url         VARCHAR(500),                      -- foto Google OAuth
    foto             VARCHAR(500),                      -- foto upload manual
    telefone         VARCHAR(20),
    cidade           VARCHAR(100),
    criado_em        DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. PRESTADORES
-- =============================================
CREATE TABLE cadastro_prestadores (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    nome             VARCHAR(100)  NOT NULL,
    sobrenome        VARCHAR(100)  NOT NULL,
    data_nascimento  DATE,
    sexo             VARCHAR(20),
    email            VARCHAR(150)  NOT NULL UNIQUE,
    senha            VARCHAR(255)  NOT NULL,             -- bcrypt hash
    areas_atuacao    TEXT,
    foto_url         VARCHAR(500),                       -- foto Google OAuth
    foto             VARCHAR(500),                       -- foto upload manual
    telefone         VARCHAR(20),
    cidade           VARCHAR(100),
    bio              TEXT,                               -- descrição do prestador
    certificados     TEXT,                               -- paths de certificados
    criado_em        DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 3. SERVIÇOS ANUNCIADOS
-- =============================================
CREATE TABLE servicos_anunciados (
    id               INT            AUTO_INCREMENT PRIMARY KEY,
    prestador_email  VARCHAR(150)   NOT NULL,
    titulo           VARCHAR(150)   NOT NULL,
    descricao        TEXT,
    preco            DECIMAL(10,2)  NOT NULL,
    area_atuacao     VARCHAR(100),
    duracao          VARCHAR(50),
    criado_em        DATETIME       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (prestador_email)
        REFERENCES cadastro_prestadores(email)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- =============================================
-- 4. AGENDAMENTOS
-- =============================================
CREATE TABLE agendamentos (
    id               INT            AUTO_INCREMENT PRIMARY KEY,
    cliente_email    VARCHAR(150)   NOT NULL,
    prestador_email  VARCHAR(150),
    servico          VARCHAR(200)   NOT NULL,
    preco            DECIMAL(10,2),
    data_servico     DATE           NOT NULL,
    horario          VARCHAR(10)    NOT NULL,
    status           ENUM(
                       'pendente',
                       'confirmado',
                       'em_andamento',
                       'concluido',
                       'cancelado'
                     )              DEFAULT 'pendente',
    observacoes      TEXT,
    criado_em        DATETIME       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cliente   (cliente_email),
    INDEX idx_prestador (prestador_email),
    INDEX idx_status    (status),
    INDEX idx_data      (data_servico)
);

-- =============================================
-- 5. ADMINISTRADORES
-- =============================================
CREATE TABLE admins (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    email            VARCHAR(150) NOT NULL UNIQUE,
    senha_hash       VARCHAR(255) NOT NULL,
    nivel            VARCHAR(50) NOT NULL DEFAULT 'admin',
    ativo            TINYINT(1) NOT NULL DEFAULT 1,
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_ativo (ativo)
);

-- =============================================
-- 6. HISTÓRICO DE AÇÕES ADMIN
-- =============================================
CREATE TABLE admin_logs (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    admin_email      VARCHAR(150) NOT NULL,
    acao             VARCHAR(255) NOT NULL,
    entidade         VARCHAR(100),
    entidade_id      VARCHAR(100),
    detalhes         TEXT,
    ip_address        VARCHAR(60),
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_logs_admin (admin_email)
);

-- =============================================
-- 7. CATEGORIAS (com ícone e cor)
-- =============================================
CREATE TABLE categorias_servicos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL UNIQUE,
    icone       VARCHAR(50) DEFAULT NULL,
    cor         VARCHAR(20) DEFAULT NULL,
    criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================
-- 8. DENÚNCIAS E TICKETS (suporte)
-- =============================================
CREATE TABLE denuncias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    denunciante_email VARCHAR(150) NOT NULL,
    alvo_tipo      VARCHAR(50) NOT NULL, -- 'prestador'|'cliente'|'servico'|'agendamento'
    alvo_id        VARCHAR(100) NOT NULL,
    categoria       VARCHAR(100) DEFAULT NULL,
    descricao       TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'aberta',
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_denuncias_status (status)
);

CREATE TABLE tickets (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    solicitante_email VARCHAR(150) NOT NULL,
    categoria       VARCHAR(100) DEFAULT NULL,
    assunto         VARCHAR(150) NOT NULL,
    mensagem_inicial TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'aberto',
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tickets_status (status)
);

CREATE TABLE ticket_respostas (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id     INT NOT NULL,
    autor_email   VARCHAR(150) NOT NULL,
    mensagem      TEXT NOT NULL,
    criado_em     DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ticket_respostas_ticket
      FOREIGN KEY (ticket_id) REFERENCES tickets(id)
      ON DELETE CASCADE
);

-- =============================================
-- 9. ALERTAS / NOTIFICAÇÕES
-- =============================================
CREATE TABLE notificacoes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tipo            VARCHAR(30) NOT NULL DEFAULT 'global', -- global|prestador|admin
    destinatario_email VARCHAR(150) DEFAULT NULL,
    titulo          VARCHAR(150) NOT NULL,
    mensagem        TEXT NOT NULL,
    lida            TINYINT(1) NOT NULL DEFAULT 0,
    criado_em       DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notificacoes_dest (destinatario_email)
);

-- =============================================
-- 10. AVALIAÇÕES E RANKING (mínimo para ranking)
-- =============================================
CREATE TABLE avaliacoes_prestadores (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150) NOT NULL,
    cliente_email   VARCHAR(150) NOT NULL,
    agendamento_id  INT,
    nota             INT NOT NULL,
    comentario      TEXT,
    criado_em        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_avaliacoes_prestador (prestador_email)
);

-- =============================================
-- 11. SEEDS (admin inicial)
-- =============================================
-- Para senha_hash, defina bcrypt/sha apropriado no seu fluxo.
-- Placeholder abaixo: remova e substitua pelo hash real quando inserir os admins.
-- Exemplo: senha_hash = '$2b$12$...'
-- INSERT INTO admins (email, senha_hash, nivel, ativo) VALUES
-- ('felipe@admin.com.br', 'SEU_HASH_BCRYPT_AQUI', 'admin', 1),
-- ('lucas@admin.com.br', 'SEU_HASH_BCRYPT_AQUI', 'admin', 1);

