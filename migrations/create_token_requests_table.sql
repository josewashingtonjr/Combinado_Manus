-- Migração: Criar tabela de solicitações de tokens
-- Data: 2025-11-05
-- Descrição: Tabela para gerenciar solicitações de compra de tokens pelos clientes

CREATE TABLE IF NOT EXISTS token_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    processed_by INTEGER,
    admin_notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (processed_by) REFERENCES admin_users (id)
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_token_requests_user_id ON token_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_token_requests_status ON token_requests(status);
CREATE INDEX IF NOT EXISTS idx_token_requests_created_at ON token_requests(created_at);

-- Inserir dados de exemplo (opcional)
-- INSERT INTO token_requests (user_id, amount, description, status) 
-- VALUES (1, 100.00, 'Primeira compra de tokens', 'pending');