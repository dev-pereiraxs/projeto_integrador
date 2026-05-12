-- Script auxiliar (DB): criar admins iniciais e colocar senha bcrypt.
-- IMPORTANTE: substitua os hashes abaixo por bcrypt reais.
--
-- Para gerar bcrypt no Python:
--   from bcrypt import gensalt, hashpw; import getpass
--
-- ou via htpasswd/bcrypt.

USE servicos;

-- Exemplo (NÃO cole sem substituir):
-- INSERT INTO admins (email, senha_hash, nivel, ativo) VALUES
-- ('felipe@admin.com.br', '$2b$12$SEU_HASH_BCRYPT_AQUI', 'admin', 1),
-- ('lucas@admin.com.br',  '$2b$12$SEU_HASH_BCRYPT_AQUI', 'admin', 1);

-- Verifique se não existem ainda:
-- SELECT email FROM admins WHERE email IN ('felipe@admin.com.br','lucas@admin.com.br');

