-- Migração para adicionar tabelas de auditoria e monitoramento de propostas
-- Requirements: 8.1, 8.2, 8.3, 8.4, 8.5

-- Tabela de logs de auditoria de propostas
CREATE TABLE IF NOT EXISTS proposal_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    invite_id INTEGER NOT NULL,
    action_type VARCHAR(50) NOT NULL, -- created, approved, rejected, cancelled, modified
    actor_user_id INTEGER NULL,
    actor_admin_id INTEGER NULL,
    actor_role VARCHAR(20) NOT NULL, -- cliente, prestador, admin, system
    
    -- Dados da ação
    previous_data TEXT NULL, -- JSON com estado anterior
    new_data TEXT NULL, -- JSON com novo estado
    reason TEXT NULL, -- Motivo/justificativa da ação
    
    -- Metadados técnicos
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    session_id VARCHAR(255) NULL,
    
    -- Dados financeiros
    original_value DECIMAL(10,2) NULL,
    proposed_value DECIMAL(10,2) NULL,
    value_difference DECIMAL(10,2) NULL,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (proposal_id) REFERENCES invite_proposals(id),
    FOREIGN KEY (invite_id) REFERENCES invites(id),
    FOREIGN KEY (actor_user_id) REFERENCES users(id),
    FOREIGN KEY (actor_admin_id) REFERENCES admin_users(id)
);

-- Tabela de métricas agregadas de propostas
CREATE TABLE IF NOT EXISTS proposal_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Período da métrica
    metric_date DATE NOT NULL,
    metric_type VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    
    -- Contadores básicos
    total_proposals INTEGER NOT NULL DEFAULT 0,
    proposals_created INTEGER NOT NULL DEFAULT 0,
    proposals_approved INTEGER NOT NULL DEFAULT 0,
    proposals_rejected INTEGER NOT NULL DEFAULT 0,
    proposals_cancelled INTEGER NOT NULL DEFAULT 0,
    
    -- Métricas de valor
    total_original_value DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    total_proposed_value DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    total_approved_value DECIMAL(18,2) NOT NULL DEFAULT 0.00,
    
    -- Métricas de comportamento
    proposals_with_increase INTEGER NOT NULL DEFAULT 0,
    proposals_with_decrease INTEGER NOT NULL DEFAULT 0,
    average_response_time_hours DECIMAL(8,2) NULL,
    
    -- Métricas de usuários únicos
    unique_prestadores INTEGER NOT NULL DEFAULT 0,
    unique_clientes INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint para evitar duplicatas
    UNIQUE(metric_date, metric_type)
);

-- Tabela de alertas sobre padrões suspeitos
CREATE TABLE IF NOT EXISTS proposal_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Tipo e severidade do alerta
    alert_type VARCHAR(50) NOT NULL, -- suspicious_pattern, high_rejection_rate, unusual_values, etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'medium', -- low, medium, high, critical
    
    -- Dados do alerta
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Entidades relacionadas
    user_id INTEGER NULL,
    proposal_id INTEGER NULL,
    invite_id INTEGER NULL,
    
    -- Dados do padrão detectado
    pattern_data TEXT NULL, -- JSON com detalhes do padrão
    threshold_exceeded VARCHAR(100) NULL, -- Qual limite foi ultrapassado
    
    -- Status do alerta
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, investigating, resolved, false_positive
    resolved_at DATETIME NULL,
    resolved_by INTEGER NULL,
    resolution_notes TEXT NULL,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (proposal_id) REFERENCES invite_proposals(id),
    FOREIGN KEY (invite_id) REFERENCES invites(id),
    FOREIGN KEY (resolved_by) REFERENCES admin_users(id)
);

-- Índices para otimização de consultas

-- Índices para proposal_audit_logs
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_proposal_id ON proposal_audit_logs(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_invite_id ON proposal_audit_logs(invite_id);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_action_type ON proposal_audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_actor_user_id ON proposal_audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_actor_role ON proposal_audit_logs(actor_role);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_created_at ON proposal_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_proposal_audit_logs_action_user_date ON proposal_audit_logs(action_type, actor_user_id, created_at);

-- Índices para proposal_metrics
CREATE INDEX IF NOT EXISTS idx_proposal_metrics_date_type ON proposal_metrics(metric_date, metric_type);
CREATE INDEX IF NOT EXISTS idx_proposal_metrics_type_date ON proposal_metrics(metric_type, metric_date);

-- Índices para proposal_alerts
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_status ON proposal_alerts(status);
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_severity ON proposal_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_alert_type ON proposal_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_user_id ON proposal_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_created_at ON proposal_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_proposal_alerts_status_severity ON proposal_alerts(status, severity);

-- Triggers para atualizar updated_at em proposal_metrics
CREATE TRIGGER IF NOT EXISTS update_proposal_metrics_updated_at
    AFTER UPDATE ON proposal_metrics
    FOR EACH ROW
BEGIN
    UPDATE proposal_metrics 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Configurações padrão serão gerenciadas pelo código da aplicação

-- Comentários nas tabelas
-- proposal_audit_logs: Registra todas as ações realizadas em propostas para auditoria completa
-- proposal_metrics: Armazena métricas agregadas por período para análise de tendências
-- proposal_alerts: Gerencia alertas sobre padrões suspeitos detectados automaticamente