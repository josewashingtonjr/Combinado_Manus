-- Migração para adicionar campos de soft delete aos modelos User e AdminUser
-- Data: 2025-01-06
-- Descrição: Adiciona campos deleted_at, deleted_by e deletion_reason para implementar soft delete

-- Adicionar campos de soft delete na tabela users
ALTER TABLE users 
ADD COLUMN deleted_at DATETIME NULL,
ADD COLUMN deleted_by INTEGER NULL,
ADD COLUMN deletion_reason TEXT NULL;

-- Adicionar foreign key constraint para deleted_by em users
-- (referencia admin_users.id)
-- Nota: Em SQLite, não podemos adicionar FK constraints após a criação da tabela
-- Em PostgreSQL, descomente a linha abaixo:
-- ALTER TABLE users ADD CONSTRAINT fk_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES admin_users(id);

-- Adicionar campos de soft delete na tabela admin_users
ALTER TABLE admin_users 
ADD COLUMN deleted_at DATETIME NULL,
ADD COLUMN deleted_by INTEGER NULL,
ADD COLUMN deletion_reason TEXT NULL;

-- Adicionar foreign key constraint para deleted_by em admin_users (auto-referência)
-- Nota: Em SQLite, não podemos adicionar FK constraints após a criação da tabela
-- Em PostgreSQL, descomente a linha abaixo:
-- ALTER TABLE admin_users ADD CONSTRAINT fk_admin_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES admin_users(id);

-- Criar índices para melhorar performance das consultas de soft delete
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
CREATE INDEX idx_users_deleted_by ON users(deleted_by);
CREATE INDEX idx_admin_users_deleted_at ON admin_users(deleted_at);
CREATE INDEX idx_admin_users_deleted_by ON admin_users(deleted_by);

-- Criar índice composto para consultas de usuários ativos (não deletados)
CREATE INDEX idx_users_active ON users(deleted_at, active) WHERE deleted_at IS NULL;
CREATE INDEX idx_admin_users_active ON admin_users(deleted_at) WHERE deleted_at IS NULL;