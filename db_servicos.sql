
DROP DATABASE IF EXISTS servicos;
CREATE DATABASE servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servicos;

select *  from cadastro_clientes;
select *  from cadastro_prestadores;
select *  from admins;

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
    telefone        VARCHAR(30),
    cidade          VARCHAR(100),
    foto            VARCHAR(255),
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
    telefone        VARCHAR(30),
    bio             TEXT,
    cidade          VARCHAR(100),
    foto            VARCHAR(255),
    certificados    TEXT,
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
    status          ENUM(
                        'pendente',
                        'confirmado',
                        'em_andamento',
                        'concluido',
                        'cancelado',
                        'recusado'
                    )              DEFAULT 'pendente',
    observacoes     TEXT,
    alerta_visto    TINYINT(1)     DEFAULT 0,
    criado_em       DATETIME       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cliente   (cliente_email),
    INDEX idx_prestador (prestador_email),
    INDEX idx_status    (status),
    INDEX idx_data      (data_servico)
);

-- =============================================
-- 5. NOTIFICAÇÕES
-- =============================================
CREATE TABLE notificacoes (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NOT NULL,
    tipo            VARCHAR(30)   NOT NULL,
    mensagem        TEXT          NOT NULL,
    agendamento_id  INT           DEFAULT NULL,
    lida            TINYINT(1)    NOT NULL DEFAULT 0,
    criada_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_notif_prestador (prestador_email)
);

-- =============================================
-- 6. AVALIAÇÕES DOS PRESTADORES
-- =============================================
CREATE TABLE avaliacoes_prestadores (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NOT NULL,
    cliente_email   VARCHAR(150)  NOT NULL,
    agendamento_id  INT,
    nota            INT           NOT NULL,
    comentario      TEXT,
    criado_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_avaliacoes_prestador (prestador_email)
);

-- =============================================
-- 7. ADMINISTRADORES (senha em texto simples)
-- =============================================
CREATE TABLE admins (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    email     VARCHAR(150)  NOT NULL UNIQUE,
    senha     VARCHAR(255)  NOT NULL,
    nivel     VARCHAR(50)   NOT NULL DEFAULT 'admin',
    ativo     TINYINT(1)    NOT NULL DEFAULT 1,
    criado_em DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_admin_ativo (ativo)
);

-- =============================================
-- 8. ADMINS INICIAIS
-- Senha padrão: 123@senac
-- =============================================
INSERT INTO admins (email, senha, nivel, ativo) VALUES
('felipe@admin.com.br', '123@senac', 'admin', 1),
('lucas@admin.com.br',  '123@senac', 'admin', 1);

-- =============================================
-- 9. CATEGORIAS DE SERVIÇOS
-- =============================================
CREATE TABLE categorias_servicos (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100)  NOT NULL UNIQUE,
    icone         VARCHAR(50)   DEFAULT NULL,
    cor           VARCHAR(20)   DEFAULT NULL,
    criado_em     DATETIME      DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categorias_servicos (nome, icone, cor) VALUES
('Mecânica',    'wrench',              '#f97316'),
('Elétrica',    'bolt',                '#eab308'),
('Tecnologia',  'monitor-smartphone',  '#3b82f6'),
('Reformas',    'hammer',              '#ef4444'),
('Hidráulica',  'droplets',            '#06b6d4'),
('Limpeza',     'sparkles',            '#10b981');

-- =============================================
-- FIM
-- =============================================