-- ============================================================================
-- Script de Migração: Float para Numeric(18,2)
-- Sistema de Correções Críticas - Tarefa 1
-- ============================================================================

-- PostgreSQL Version
-- ============================================================================

-- Migração para PostgreSQL
BEGIN;

-- Migração da tabela wallets
ALTER TABLE wallets 
  ALTER COLUMN balance TYPE NUMERIC(18,2),
  ALTER COLUMN escrow_balance TYPE NUMERIC(18,2);

-- Migração da tabela transactions
ALTER TABLE transactions 
  ALTER COLUMN amount TYPE NUMERIC(18,2);

-- Migração da tabela orders
ALTER TABLE orders 
  ALTER COLUMN value TYPE NUMERIC(18,2);

-- Migração da tabela token_requests
ALTER TABLE token_requests 
  ALTER COLUMN amount TYPE NUMERIC(18,2);

-- Adicionar constraints de integridade (se não existirem)
DO $$
BEGIN
    -- Constraint para balance não negativo
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_balance_non_negative' 
        AND table_name = 'wallets'
    ) THEN
        ALTER TABLE wallets 
        ADD CONSTRAINT check_balance_non_negative CHECK (balance >= 0);
    END IF;
    
    -- Constraint para escrow_balance não negativo
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_escrow_balance_non_negative' 
        AND table_name = 'wallets'
    ) THEN
        ALTER TABLE wallets 
        ADD CONSTRAINT check_escrow_balance_non_negative CHECK (escrow_balance >= 0);
    END IF;
    
    -- Constraint para transaction amount não zero
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_transaction_amount_not_zero' 
        AND table_name = 'transactions'
    ) THEN
        ALTER TABLE transactions 
        ADD CONSTRAINT check_transaction_amount_not_zero CHECK (amount != 0);
    END IF;
    
    -- Constraint para order value positivo
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_order_value_positive' 
        AND table_name = 'orders'
    ) THEN
        ALTER TABLE orders 
        ADD CONSTRAINT check_order_value_positive CHECK (value > 0);
    END IF;
    
    -- Constraint para token_request amount positivo
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'check_token_request_amount_positive' 
        AND table_name = 'token_requests'
    ) THEN
        ALTER TABLE token_requests 
        ADD CONSTRAINT check_token_request_amount_positive CHECK (amount > 0);
    END IF;
END $$;

-- Criar índices para otimização (se não existirem)
CREATE INDEX IF NOT EXISTS idx_wallets_user_id ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_order_id ON transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_requests_user_status ON token_requests(user_id, status);

COMMIT;

-- ============================================================================
-- SQLite Version (comentado - usar apenas se necessário)
-- ============================================================================

/*
-- Script de Migração para SQLite
-- ATENÇÃO: SQLite requer recriação completa das tabelas

BEGIN TRANSACTION;

-- 1. Backup das tabelas existentes
CREATE TABLE wallets_backup AS SELECT * FROM wallets;
CREATE TABLE transactions_backup AS SELECT * FROM transactions;
CREATE TABLE orders_backup AS SELECT * FROM orders;
CREATE TABLE token_requests_backup AS SELECT * FROM token_requests;

-- 2. Recriar tabela wallets com tipos corretos
DROP TABLE wallets;
CREATE TABLE wallets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    escrow_balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    CHECK (balance >= 0),
    CHECK (escrow_balance >= 0)
);

-- 3. Recriar tabela transactions com tipos corretos
DROP TABLE transactions;
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    order_id INTEGER,
    related_user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (related_user_id) REFERENCES users (id),
    CHECK (amount != 0)
);

-- 4. Recriar tabela orders com tipos corretos
DROP TABLE orders;
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    provider_id INTEGER,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    value NUMERIC(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'disponivel',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME,
    completed_at DATETIME,
    invite_id INTEGER,
    dispute_reason TEXT,
    dispute_opened_by INTEGER,
    dispute_opened_at DATETIME,
    dispute_resolved_at DATETIME,
    dispute_resolution TEXT,
    FOREIGN KEY (client_id) REFERENCES users (id),
    FOREIGN KEY (provider_id) REFERENCES users (id),
    FOREIGN KEY (invite_id) REFERENCES invites (id),
    FOREIGN KEY (dispute_opened_by) REFERENCES users (id),
    CHECK (value > 0)
);

-- 5. Recriar tabela token_requests com tipos corretos
DROP TABLE token_requests;
CREATE TABLE token_requests (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    processed_by INTEGER,
    admin_notes TEXT,
    payment_method VARCHAR(50) DEFAULT 'pix',
    receipt_filename VARCHAR(255),
    receipt_original_name VARCHAR(255),
    receipt_uploaded_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (processed_by) REFERENCES admin_users (id),
    CHECK (amount > 0)
);

-- 6. Restaurar dados das tabelas backup
INSERT INTO wallets SELECT * FROM wallets_backup;
INSERT INTO transactions SELECT * FROM transactions_backup;
INSERT INTO orders SELECT * FROM orders_backup;
INSERT INTO token_requests SELECT * FROM token_requests_backup;

-- 7. Criar índices para otimização
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_transactions_user_id_created ON transactions(user_id, created_at DESC);
CREATE INDEX idx_transactions_order_id ON transactions(order_id);
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);
CREATE INDEX idx_token_requests_user_status ON token_requests(user_id, status);

-- 8. Remover tabelas de backup
DROP TABLE wallets_backup;
DROP TABLE transactions_backup;
DROP TABLE orders_backup;
DROP TABLE token_requests_backup;

COMMIT;
*/

-- ============================================================================
-- Verificação de Integridade Pós-Migração
-- ============================================================================

-- Verificar se todos os valores monetários são válidos
SELECT 'wallets' as tabela, COUNT(*) as total_registros,
       COUNT(CASE WHEN balance < 0 THEN 1 END) as saldos_negativos,
       COUNT(CASE WHEN escrow_balance < 0 THEN 1 END) as escrow_negativos
FROM wallets
UNION ALL
SELECT 'transactions' as tabela, COUNT(*) as total_registros,
       COUNT(CASE WHEN amount = 0 THEN 1 END) as amounts_zero,
       0 as escrow_negativos
FROM transactions
UNION ALL
SELECT 'orders' as tabela, COUNT(*) as total_registros,
       COUNT(CASE WHEN value <= 0 THEN 1 END) as valores_invalidos,
       0 as escrow_negativos
FROM orders
UNION ALL
SELECT 'token_requests' as tabela, COUNT(*) as total_registros,
       COUNT(CASE WHEN amount <= 0 THEN 1 END) as amounts_invalidos,
       0 as escrow_negativos
FROM token_requests;

-- Verificar precisão decimal (máximo 2 casas decimais)
SELECT 'Verificação de Precisão Decimal' as verificacao,
       (SELECT COUNT(*) FROM wallets WHERE (balance * 100) != ROUND(balance * 100)) as wallets_imprecisos,
       (SELECT COUNT(*) FROM transactions WHERE (amount * 100) != ROUND(amount * 100)) as transactions_imprecisos,
       (SELECT COUNT(*) FROM orders WHERE (value * 100) != ROUND(value * 100)) as orders_imprecisos,
       (SELECT COUNT(*) FROM token_requests WHERE (amount * 100) != ROUND(amount * 100)) as token_requests_imprecisos;