-- Migration: Sistema de Pré-Ordem
-- Data: 2025-11-21
-- Descrição: Adiciona tabelas para sistema de pré-ordem que permite negociação
--            antes da conversão em ordem definitiva com bloqueio de valores

-- ============================================================================
-- Tabela: pre_orders
-- ============================================================================
CREATE TABLE IF NOT EXISTS pre_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invite_id INTEGER NOT NULL,
    
    -- Partes envolvidas
    client_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    
    -- Dados do serviço
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Valores
    current_value NUMERIC(18, 2) NOT NULL,
    original_value NUMERIC(18, 2) NOT NULL,
    
    -- Prazo e categoria
    delivery_date TIMESTAMP NOT NULL,
    service_category VARCHAR(100),
    
    -- Status e controle de estado
    status VARCHAR(50) NOT NULL DEFAULT 'em_negociacao',
    
    -- Aceitação de termos
    client_accepted_terms BOOLEAN NOT NULL DEFAULT 0,
    provider_accepted_terms BOOLEAN NOT NULL DEFAULT 0,
    
    -- Controle de propostas
    has_active_proposal BOOLEAN NOT NULL DEFAULT 0,
    active_proposal_id INTEGER,
    
    -- Rodada de negociação
    negotiation_round INTEGER NOT NULL DEFAULT 0,
    
    -- Controle otimista de concorrência
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    converted_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Cancelamento
    cancelled_by INTEGER,
    cancellation_reason TEXT,
    
    -- Ordem resultante
    order_id INTEGER,
    
    -- Foreign keys
    FOREIGN KEY (invite_id) REFERENCES invites(id),
    FOREIGN KEY (client_id) REFERENCES users(id),
    FOREIGN KEY (provider_id) REFERENCES users(id),
    FOREIGN KEY (cancelled_by) REFERENCES users(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (active_proposal_id) REFERENCES pre_order_proposals(id),
    
    -- Constraints
    CONSTRAINT check_current_value_positive CHECK (current_value > 0),
    CONSTRAINT check_original_value_positive CHECK (original_value > 0),
    CONSTRAINT check_expires_after_creation CHECK (expires_at > created_at),
    CONSTRAINT check_valid_status CHECK (status IN (
        'em_negociacao',
        'aguardando_resposta',
        'pronto_conversao',
        'convertida',
        'cancelada',
        'expirada'
    ))
);

-- ============================================================================
-- Tabela: pre_order_proposals
-- ============================================================================
CREATE TABLE IF NOT EXISTS pre_order_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pre_order_id INTEGER NOT NULL,
    
    -- Autor da proposta
    proposed_by INTEGER NOT NULL,
    
    -- Valores propostos (NULL = sem alteração)
    proposed_value NUMERIC(18, 2),
    proposed_delivery_date TIMESTAMP,
    proposed_description TEXT,
    
    -- Justificativa obrigatória
    justification TEXT NOT NULL,
    
    -- Status da proposta
    status VARCHAR(50) NOT NULL DEFAULT 'pendente',
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (pre_order_id) REFERENCES pre_orders(id),
    FOREIGN KEY (proposed_by) REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT check_proposal_status CHECK (status IN (
        'pendente',
        'aceita',
        'rejeitada',
        'cancelada'
    )),
    CONSTRAINT check_proposed_value_positive CHECK (
        proposed_value IS NULL OR proposed_value > 0
    ),
    CONSTRAINT check_justification_not_empty CHECK (
        LENGTH(TRIM(justification)) >= 50
    )
);

-- ============================================================================
-- Tabela: pre_order_history
-- ============================================================================
CREATE TABLE IF NOT EXISTS pre_order_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pre_order_id INTEGER NOT NULL,
    
    -- Tipo de evento
    event_type VARCHAR(50) NOT NULL,
    
    -- Ator que realizou a ação
    actor_id INTEGER NOT NULL,
    
    -- Descrição do evento
    description TEXT NOT NULL,
    
    -- Dados adicionais em JSON
    event_data TEXT,
    
    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (pre_order_id) REFERENCES pre_orders(id),
    FOREIGN KEY (actor_id) REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT check_event_type CHECK (event_type IN (
        'created',
        'proposal_sent',
        'proposal_accepted',
        'proposal_rejected',
        'proposal_cancelled',
        'terms_accepted_client',
        'terms_accepted_provider',
        'cancelled',
        'expired',
        'converted',
        'conversion_failed',
        'status_changed'
    ))
);

-- ============================================================================
-- Índices para performance
-- ============================================================================

-- Índice para buscar pré-ordens por status
CREATE INDEX idx_pre_orders_status ON pre_orders(status);

-- Índice para buscar pré-ordens do cliente
CREATE INDEX idx_pre_orders_client ON pre_orders(client_id, status);

-- Índice para buscar pré-ordens do prestador
CREATE INDEX idx_pre_orders_provider ON pre_orders(provider_id, status);

-- Índice para buscar pré-ordens próximas da expiração
CREATE INDEX idx_pre_orders_expires ON pre_orders(expires_at, status);

-- Índice para buscar pré-ordens por convite
CREATE INDEX idx_pre_orders_invite ON pre_orders(invite_id);

-- Índice para buscar propostas por pré-ordem
CREATE INDEX idx_pre_order_proposals_pre_order ON pre_order_proposals(pre_order_id, status);

-- Índice para buscar propostas por autor
CREATE INDEX idx_pre_order_proposals_author ON pre_order_proposals(proposed_by);

-- Índice único para garantir apenas uma proposta pendente por pré-ordem
CREATE UNIQUE INDEX uq_preorder_active_proposal 
ON pre_order_proposals(pre_order_id) 
WHERE status = 'pendente';

-- Índice para histórico ordenado por data
CREATE INDEX idx_pre_order_history_pre_order ON pre_order_history(pre_order_id, created_at DESC);

-- Índice para buscar eventos por tipo
CREATE INDEX idx_pre_order_history_event_type ON pre_order_history(event_type, created_at DESC);

-- ============================================================================
-- Comentários para documentação (SQLite não suporta COMMENT ON, apenas para referência)
-- ============================================================================

-- Tabela pre_orders: Pré-ordens - estágio intermediário de negociação entre convite e ordem definitiva
-- Colunas:
--   status: Status atual (em_negociacao, aguardando_resposta, pronto_conversao, convertida, cancelada, expirada)
--   current_value: Valor atual acordado (pode mudar durante negociação)
--   original_value: Valor original do convite (imutável)
--   client_accepted_terms: Cliente aceitou os termos atuais
--   provider_accepted_terms: Prestador aceitou os termos atuais
--   has_active_proposal: Indica se há proposta pendente de resposta
--   negotiation_round: Contador de rodadas de negociação
--   version: Versão para controle otimista de concorrência
--   expires_at: Data/hora de expiração da negociação

-- Tabela pre_order_proposals: Propostas de alteração durante negociação da pré-ordem
-- Colunas:
--   proposed_value: Novo valor proposto (NULL = sem alteração)
--   proposed_delivery_date: Nova data proposta (NULL = sem alteração)
--   proposed_description: Nova descrição proposta (NULL = sem alteração)
--   justification: Justificativa obrigatória (mínimo 50 caracteres)

-- Tabela pre_order_history: Histórico completo de eventos da pré-ordem para auditoria
-- Colunas:
--   event_type: Tipo do evento registrado
--   event_data: Dados adicionais em formato JSON

-- ============================================================================
-- Atualização da tabela invites
-- ============================================================================

-- Adicionar coluna para indicar que convite foi convertido em pré-ordem
ALTER TABLE invites ADD COLUMN converted_to_pre_order BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE invites ADD COLUMN pre_order_id INTEGER;

-- Foreign key para pré-ordem
-- Nota: SQLite não suporta ADD CONSTRAINT após criação, então documentamos apenas
-- FOREIGN KEY (pre_order_id) REFERENCES pre_orders(id)

-- Índice para buscar convites convertidos
CREATE INDEX idx_invites_pre_order ON invites(pre_order_id) WHERE pre_order_id IS NOT NULL;

-- Colunas adicionadas em invites:
--   converted_to_pre_order: Indica se o convite foi convertido em pré-ordem
--   pre_order_id: ID da pré-ordem criada a partir deste convite
