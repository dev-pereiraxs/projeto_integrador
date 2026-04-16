CREATE DATABASE IF NOT EXISTS servicos;
USE servicos;

CREATE TABLE IF NOT EXISTS cadastro_clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    sobrenome VARCHAR(100) NOT NULL,
    idade INT NULL, 
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NULL
);

select * from cadastro_clientes;