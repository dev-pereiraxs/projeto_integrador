-- ============================================================
--  Agenda Fácil — Schema completo e sincronizado com app.py
--  Gerado em: 2026-05-27
-- ============================================================

DROP DATABASE IF EXISTS servicos;
CREATE DATABASE servicos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE servicos;

SELECT areas_atuacao FROM cadastro_prestadores;


-- ============================================================
--  1. CLIENTES
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


-- ============================================================
--  2. PRESTADORES
-- ============================================================
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


-- ============================================================
--  3. SERVIÇOS ANUNCIADOS
-- ============================================================
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


-- ============================================================
--  4. AGENDAMENTOS
-- ============================================================
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
                    )              NOT NULL DEFAULT 'pendente',
    observacoes     TEXT,
    alerta_visto    TINYINT(1)     NOT NULL DEFAULT 0,
    criado_em       DATETIME       DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_cliente   (cliente_email),
    INDEX idx_prestador (prestador_email),
    INDEX idx_status    (status),
    INDEX idx_data      (data_servico)
);


-- ============================================================
--  5. NOTIFICAÇÕES
--  CORREÇÃO: prestador_email agora é NULL para suportar
--  notificações administrativas (rejeitar_solicitacao no blueprint)
-- ============================================================
CREATE TABLE notificacoes (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NULL,              -- ← era NOT NULL, causava erro no admin
    tipo            VARCHAR(30)   NOT NULL,
    mensagem        TEXT          NOT NULL,
    agendamento_id  INT           DEFAULT NULL,
    lida            TINYINT(1)    NOT NULL DEFAULT 0,
    criada_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_notif_prestador (prestador_email)
);



-- ============================================================
--  6. AVALIAÇÕES DOS PRESTADORES
-- ============================================================
CREATE TABLE avaliacoes_prestadores (
    id              INT           AUTO_INCREMENT PRIMARY KEY,
    prestador_email VARCHAR(150)  NOT NULL,
    cliente_email   VARCHAR(150)  NOT NULL,
    agendamento_id  INT,
    nota            INT           NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario      TEXT,
    criado_em       DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_avaliacoes_prestador (prestador_email),
    INDEX idx_avaliacoes_agendamento (agendamento_id)
);


-- ============================================================
--  7. ADMINISTRADORES
--  CORREÇÃO: coluna renomeada senha → senha_hash
--  O app.py usa bcrypt.checkpw(senha, senha_hash), não comparação direta.
--
--  Como gerar o hash antes de inserir:

-- ============================================================
CREATE TABLE admins (
    id          INT           AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(150)  NOT NULL UNIQUE,
    senha       VARCHAR(255)  NOT NULL,
    nivel       VARCHAR(50)   NOT NULL DEFAULT 'admin',
    ativo       TINYINT(1)    NOT NULL DEFAULT 1,
    criado_em   DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_admin_ativo (ativo)
);


INSERT INTO admins (email, senha, nivel, ativo) VALUES
('felipe@admin.com.br', '123@senac', 'admin', 1),
('lucas@admin.com.br',  '123@senac', 'admin', 1);


-- ============================================================
--  8. CATEGORIAS DE SERVIÇOS
-- ============================================================
CREATE TABLE categorias_servicos (
    id        INT           AUTO_INCREMENT PRIMARY KEY,
    nome      VARCHAR(100)  NOT NULL UNIQUE,
    icone     VARCHAR(50)   DEFAULT NULL,
    cor       VARCHAR(20)   DEFAULT NULL,
    criado_em DATETIME      DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categorias_servicos (nome, icone, cor) VALUES
('Mecânica',    'wrench',             '#f97316'),
('Elétrica',    'bolt',               '#eab308'),
('Tecnologia',  'monitor-smartphone', '#3b82f6'),
('Reformas',    'hammer',             '#ef4444'),
('Hidráulica',  'droplets',           '#06b6d4'),
('Limpeza',     'sparkles',           '#10b981');


-- ============================================================
--  9. SOLICITAÇÕES DE ORÇAMENTO
--  TABELA NOVA — ausente no schema original mas usada em:
--    /api/solicitar-orcamento, /admin/api/orcamentos,
--    /admin/api/solicitacoes-orcamento e seus endpoints de aprovação
-- ============================================================
CREATE TABLE solicitacoes_orcamento (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(120)  NOT NULL,
    telefone      VARCHAR(20)   NOT NULL,
    email         VARCHAR(150)  NULL,
    categoria     VARCHAR(100)  NOT NULL,
    categoria_id  INT           NULL,
    descricao     TEXT          NOT NULL,
    status        ENUM(
                      'pendente',
                      'enviado',
                      'erro'
                  )             NOT NULL DEFAULT 'pendente',
    cliente_email VARCHAR(150)  NULL,
    criado_em     DATETIME      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_orc_categoria  (categoria),
    INDEX idx_orc_status     (status),
    INDEX idx_orc_criado_em  (criado_em),
    INDEX idx_orc_cli_email  (cliente_email),

    FOREIGN KEY (categoria_id)
        REFERENCES categorias_servicos(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    FOREIGN KEY (cliente_email)
        REFERENCES cadastro_clientes(email)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);


-- ============================================================
--  TRIGGER: preenche categoria_id e cliente_email ao inserir
--  solicitação de orçamento (definida UMA única vez)
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_orc_before_insert
BEFORE INSERT ON solicitacoes_orcamento
FOR EACH ROW
BEGIN
    SET NEW.categoria_id = (
        SELECT id FROM categorias_servicos
        WHERE nome = NEW.categoria
        LIMIT 1
    );

    IF NEW.email IS NOT NULL THEN
        SET NEW.cliente_email = (
            SELECT email FROM cadastro_clientes
            WHERE email = NEW.email
            LIMIT 1
        );
    END IF;
END$$

DELIMITER ;

=============================================================
--  10. CORRIGE ÁREAS DE ATUAÇÃO PARA VALORES PADRONIZADOS

SET SQL_SAFE_UPDATES = 0;

UPDATE cadastro_prestadores SET areas_atuacao = 'Tecnologia' WHERE LOWER(areas_atuacao) LIKE '%ti%';
UPDATE cadastro_prestadores SET areas_atuacao = 'Mecânica'   WHERE LOWER(areas_atuacao) LIKE '%mec%';
UPDATE cadastro_prestadores SET areas_atuacao = 'Elétrica'   WHERE LOWER(areas_atuacao) LIKE '%el%tric%';
UPDATE cadastro_prestadores SET areas_atuacao = 'Hidráulica' WHERE LOWER(areas_atuacao) LIKE '%hidr%';
UPDATE cadastro_prestadores SET areas_atuacao = 'Reformas'   WHERE LOWER(areas_atuacao) LIKE '%reform%';
UPDATE cadastro_prestadores SET areas_atuacao = 'Limpeza'    WHERE LOWER(areas_atuacao) LIKE '%limpez%';

SET SQL_SAFE_UPDATES = 1;

-- ============================================================
--  FIM DO SCHEMA
-- ============================================================