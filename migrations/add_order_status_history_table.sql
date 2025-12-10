-- Migração para adicionar tabela de histórico de status de ordens
-- Implementa requisito 7.4: Adicionar histórico de mudanças de status para cada order

-- Criar tabela order_status_history
CREATE TABLE IF NOT EXISTS order_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    previous_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,
    changed_by_user_id INTEGER,
    changed_by_admin_id INTEGER,
    reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (changed_by_user_id) REFERENCES users (id),
    FOREIGN KEY (changed_by_admin_id) REFERENCES admin_users (id)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_order_status_history_order_id ON order_status_history(order_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_created_at ON order_status_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_status_history_user_id ON order_status_history(changed_by_user_id);
CREATE INDEX IF NOT EXISTS idx_order_status_history_admin_id ON order_status_history(changed_by_admin_id);

-- Comentários para documentação
-- Esta tabela registra todas as mudanças de status de ordens para auditoria
-- Permite rastrear quem fez a mudança, quando e por que motivo
-- Suporta tanto usuários normais quanto administradores
-- Inclui informações de IP e User-Agent para auditoria de segurança