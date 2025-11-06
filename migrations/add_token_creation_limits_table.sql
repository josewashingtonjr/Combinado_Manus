-- Migração para adicionar tabela de controle de limites de criação de tokens
-- Data: 2025-11-06
-- Descrição: Implementa controle de limites diários e mensais para criação de tokens por administrador

-- Criar tabela token_creation_limits
CREATE TABLE IF NOT EXISTS token_creation_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL UNIQUE,
    daily_limit DECIMAL(18,2) NOT NULL DEFAULT 10000.00,
    monthly_limit DECIMAL(18,2) NOT NULL DEFAULT 100000.00,
    current_daily_used DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    current_monthly_used DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    last_daily_reset DATE NOT NULL DEFAULT (date('now')),
    last_monthly_reset DATE NOT NULL DEFAULT (date('now')),
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    
    -- Chave estrangeira para admin_users
    FOREIGN KEY (admin_id) REFERENCES admin_users(id) ON DELETE CASCADE,
    
    -- Constraints de validação
    CHECK (daily_limit > 0),
    CHECK (monthly_limit > 0),
    CHECK (current_daily_used >= 0),
    CHECK (current_monthly_used >= 0)
);

-- Criar índices para otimização
CREATE INDEX IF NOT EXISTS idx_token_creation_limits_admin_id ON token_creation_limits(admin_id);
CREATE INDEX IF NOT EXISTS idx_token_creation_limits_daily_reset ON token_creation_limits(last_daily_reset);
CREATE INDEX IF NOT EXISTS idx_token_creation_limits_monthly_reset ON token_creation_limits(last_monthly_reset);

-- Inserir limites padrão para administradores existentes
INSERT OR IGNORE INTO token_creation_limits (admin_id, daily_limit, monthly_limit)
SELECT id, 10000.00, 100000.00 
FROM admin_users 
WHERE deleted_at IS NULL;

-- Comentários sobre a estrutura
-- admin_id: ID do administrador (único por admin)
-- daily_limit: Limite diário de criação de tokens (padrão: R$ 10.000,00)
-- monthly_limit: Limite mensal de criação de tokens (padrão: R$ 100.000,00)
-- current_daily_used: Valor já usado no dia atual
-- current_monthly_used: Valor já usado no mês atual
-- last_daily_reset: Data do último reset diário
-- last_monthly_reset: Data do último reset mensal