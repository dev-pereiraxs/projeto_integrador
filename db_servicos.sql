DROP DATABASE IF EXISTS servicos;
CREATE DATABASE servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servicos;

-- ============================================================
-- TABELAS
-- ============================================================

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
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE agendamentos (
    id              INT            AUTO_INCREMENT PRIMARY KEY,
    cliente_email   VARCHAR(150)   NOT NULL,
    prestador_email VARCHAR(150),
    servico         VARCHAR(200)   NOT NULL,
    preco           DECIMAL(10,2),
    data_servico    DATE           NOT NULL,
    horario         VARCHAR(10)    NOT NULL,
    status          ENUM('pendente','confirmado','em_andamento','concluido','cancelado','recusado')
                                   NOT NULL DEFAULT 'pendente',
    observacoes     TEXT,
    alerta_visto    TINYINT(1)     NOT NULL DEFAULT 0,
    criado_em       DATETIME       DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cliente   (cliente_email),
    INDEX idx_prestador (prestador_email),
    INDEX idx_status    (status),
    INDEX idx_data      (data_servico)
);

CREATE TABLE notificacoes (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NULL,
    tipo            VARCHAR(30)   NOT NULL,
    mensagem        TEXT          NOT NULL,
    agendamento_id  INT           DEFAULT NULL,
    lida            TINYINT(1)    NOT NULL DEFAULT 0,
    criada_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notif_prestador (prestador_email)
);

CREATE TABLE avaliacoes_prestadores (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NOT NULL,
    cliente_email   VARCHAR(150)  NOT NULL,
    agendamento_id  INT,
    nota            INT           NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario      TEXT,
    criado_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_avaliacoes_prestador   (prestador_email),
    INDEX idx_avaliacoes_agendamento (agendamento_id)
);

CREATE TABLE admins (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    email     VARCHAR(150)  NOT NULL UNIQUE,
    senha     VARCHAR(255)  NOT NULL,
    nivel     VARCHAR(50)   NOT NULL DEFAULT 'admin',
    ativo     TINYINT(1)    NOT NULL DEFAULT 1,
    criado_em DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_ativo (ativo)
);

CREATE TABLE categorias_servicos (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    nome      VARCHAR(100)  NOT NULL UNIQUE,
    icone     VARCHAR(50)   DEFAULT NULL,
    cor       VARCHAR(20)   DEFAULT NULL,
    criado_em DATETIME      DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE solicitacoes_orcamento (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(120)  NOT NULL,
    telefone      VARCHAR(20)   NOT NULL,
    email         VARCHAR(150)  NULL,
    categoria     VARCHAR(100)  NOT NULL,
    categoria_id  INT           NULL,
    descricao     TEXT          NOT NULL,
    status        ENUM('pendente','enviado','erro','cancelado') NOT NULL DEFAULT 'pendente',
    motivo_recusa TEXT          NULL,
    alerta_visto  TINYINT(1)    NOT NULL DEFAULT 0,
    cliente_email VARCHAR(150)  NULL,
    criado_em     DATETIME      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_orc_categoria (categoria),
    INDEX idx_orc_status    (status),
    INDEX idx_orc_criado_em (criado_em),
    INDEX idx_orc_cli_email (cliente_email),
    FOREIGN KEY (categoria_id)
        REFERENCES categorias_servicos(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (cliente_email)
        REFERENCES cadastro_clientes(email)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ============================================================
-- TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_orc_before_insert;

DELIMITER $$
CREATE TRIGGER trg_orc_before_insert
BEFORE INSERT ON solicitacoes_orcamento
FOR EACH ROW
BEGIN
    SET NEW.categoria_id = (
        SELECT id FROM categorias_servicos WHERE nome = NEW.categoria LIMIT 1
    );
    IF NEW.email IS NOT NULL AND NEW.email != '' THEN
        SET NEW.cliente_email = (
            SELECT email FROM cadastro_clientes WHERE email = NEW.email LIMIT 1
        );
    END IF;
END$$
DELIMITER ;

-- ============================================================
-- DADOS INICIAIS
-- ============================================================

INSERT INTO admins (email, senha, nivel, ativo) VALUES
('felipe@admin.com.br', '123@senac', 'admin', 1),
('lucas@admin.com.br',  '123@senac', 'admin', 1);

INSERT INTO categorias_servicos (nome, icone, cor) VALUES
('Mecânica',   'wrench',             '#f97316'),
('Elétrica',   'bolt',               '#eab308'),
('Tecnologia', 'monitor-smartphone', '#3b82f6'),
('Reformas',   'hammer',             '#ef4444'),
('Hidráulica', 'droplets',           '#06b6d4'),
('Limpeza',    'sparkles',           '#10b981');

INSERT INTO cadastro_prestadores (nome, sobrenome, email, senha, areas_atuacao, telefone, cidade) VALUES
('Carlos',   'Oliveira',  'carlos.mecanica@email.com',  '123456', 'Mecânica',   '(11) 91111-0001', 'São Paulo'),
('Roberto',  'Silva',     'roberto.mecanica@email.com', '123456', 'Mecânica',   '(11) 91111-0002', 'São Paulo'),
('André',    'Santos',    'andre.eletrica@email.com',   '123456', 'Elétrica',   '(11) 92222-0001', 'São Paulo'),
('Marcos',   'Pereira',   'marcos.eletrica@email.com',  '123456', 'Elétrica',   '(11) 92222-0002', 'São Paulo'),
('Felipe',   'Costa',     'felipe.ti@email.com',        '123456', 'Tecnologia', '(11) 93333-0001', 'São Paulo'),
('Lucas',    'Mendes',    'lucas.ti@email.com',          '123456', 'Tecnologia', '(11) 93333-0002', 'São Paulo'),
('Paulo',    'Rodrigues', 'paulo.reforma@email.com',    '123456', 'Reformas',   '(11) 94444-0001', 'São Paulo'),
('Diego',    'Alves',     'diego.reforma@email.com',    '123456', 'Reformas',   '(11) 94444-0002', 'São Paulo'),
('João',     'Ferreira',  'joao.hidro@email.com',       '123456', 'Hidráulica', '(11) 95555-0001', 'São Paulo'),
('Rafael',   'Souza',     'rafael.hidro@email.com',     '123456', 'Hidráulica', '(11) 95555-0002', 'São Paulo'),
('Patrícia', 'Lima',      'patricia.limpeza@email.com', '123456', 'Limpeza',    '(11) 96666-0001', 'São Paulo'),
('Juliana',  'Martins',   'juliana.limpeza@email.com',  '123456', 'Limpeza',    '(11) 96666-0002', 'São Paulo');

-- ============================================================
-- VERIFICAÇÃO — todas as tabelas
-- ============================================================

SELECT 'cadastro_clientes'       AS tabela, COUNT(*) AS registros FROM cadastro_clientes
UNION ALL
SELECT 'cadastro_prestadores',   COUNT(*) FROM cadastro_prestadores
UNION ALL
SELECT 'servicos_anunciados',    COUNT(*) FROM servicos_anunciados
UNION ALL
SELECT 'agendamentos',           COUNT(*) FROM agendamentos
UNION ALL
SELECT 'notificacoes',           COUNT(*) FROM notificacoes
UNION ALL
SELECT 'avaliacoes_prestadores', COUNT(*) FROM avaliacoes_prestadores
UNION ALL
SELECT 'admins',                 COUNT(*) FROM admins
UNION ALL
SELECT 'categorias_servicos',    COUNT(*) FROM categorias_servicos
UNION ALL
SELECT 'solicitacoes_orcamento', COUNT(*) FROM solicitacoes_orcamento;