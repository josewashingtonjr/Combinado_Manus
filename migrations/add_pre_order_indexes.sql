-- ============================================================================
-- Migração: Adicionar Índices de Performance para Sistema de Pré-Ordens
-- ============================================================================
-- Data: 2025-11-26
-- Descrição: Adiciona índices para otimizar consultas frequentes no sistema
--            de pré-ordens, propostas e histórico.
-- ============================================================================

-- Índices para pre_orders
-- Nota: Alguns índices já podem existir se foram criados via SQLAlchemy
-- Usamos IF NOT EXISTS para evitar erros

-- Índice para consultas por status (filtros de dashboard)
CREATE INDEX IF NOT EXISTS idx_pre_orders_status 
ON pre_orders(status);

-- Índice para consultas por cliente (dashboard do cliente)
CREATE INDEX IF NOT EXISTS idx_pre_orders_client 
ON pre_orders(client_id);

-- Índice para consultas por prestador (dashboard do prestador)
CREATE INDEX IF NOT EXISTS idx_pre_orders_provider 
ON pre_orders(provider_id);

-- Índice para consultas por data de expiração (job de expiração)
CREATE INDEX IF NOT EXISTS idx_pre_orders_expires 
ON pre_orders(expires_at);

-- Índice composto para consultas de pré-ordens ativas por usuário
-- Otimiza: "pré-ordens ativas do cliente X" ou "pré-ordens ativas do prestador Y"
CREATE INDEX IF NOT EXISTS idx_pre_orders_client_status 
ON pre_orders(client_id, status);

CREATE INDEX IF NOT EXISTS idx_pre_orders_provider_status 
ON pre_orders(provider_id, status);

-- Índice para consultas de pré-ordens próximas da expiração
-- Otimiza: notificações de expiração iminente
CREATE INDEX IF NOT EXISTS idx_pre_orders_status_expires 
ON pre_orders(status, expires_at);

-- ============================================================================
-- Índices para pre_order_proposals
-- ============================================================================

-- Índice para consultas por status (propostas pendentes, aceitas, etc.)
CREATE INDEX IF NOT EXISTS idx_pre_order_proposals_status 
ON pre_order_proposals(status);

-- Índice composto para consultas de propostas por pré-ordem ordenadas por data
-- Otimiza: histórico de propostas de uma pré-ordem
CREATE INDEX IF NOT EXISTS idx_pre_order_proposals_pre_order 
ON pre_order_proposals(pre_order_id, created_at);

-- Índice para consultas por autor da proposta
CREATE INDEX IF NOT EXISTS idx_pre_order_proposals_proposer 
ON pre_order_proposals(proposed_by);

-- Índice composto para propostas pendentes de uma pré-ordem
-- Otimiza: verificação de proposta ativa
CREATE INDEX IF NOT EXISTS idx_pre_order_proposals_pre_order_status 
ON pre_order_proposals(pre_order_id, status);

-- ============================================================================
-- Índices para pre_order_history
-- ============================================================================

-- Índice composto para histórico de uma pré-ordem ordenado por data
-- Otimiza: timeline de eventos de uma pré-ordem
CREATE INDEX IF NOT EXISTS idx_pre_order_history_pre_order 
ON pre_order_history(pre_order_id, created_at DESC);

-- Índice para consultas por tipo de evento (auditoria)
CREATE INDEX IF NOT EXISTS idx_pre_order_history_event_type 
ON pre_order_history(event_type);

-- Índice para consultas por ator (quem fez a ação)
CREATE INDEX IF NOT EXISTS idx_pre_order_history_actor 
ON pre_order_history(actor_id);

-- Índice composto para eventos de um tipo específico ordenados por data
-- Otimiza: relatórios de auditoria por tipo de evento
CREATE INDEX IF NOT EXISTS idx_pre_order_history_event_created 
ON pre_order_history(event_type, created_at DESC);

-- ============================================================================
-- Índices para otimizar joins frequentes
-- ============================================================================

-- Índice para relacionamento pre_order -> invite
CREATE INDEX IF NOT EXISTS idx_pre_orders_invite 
ON pre_orders(invite_id);

-- Índice para relacionamento pre_order -> order (conversão)
CREATE INDEX IF NOT EXISTS idx_pre_orders_order 
ON pre_orders(order_id);

-- ============================================================================
-- Análise de performance (opcional - executar após criação dos índices)
-- ============================================================================

-- Para SQLite, executar ANALYZE para atualizar estatísticas
ANALYZE;

-- ============================================================================
-- Verificação dos índices criados
-- ============================================================================

-- Para verificar os índices criados, execute:
-- SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND tbl_name LIKE 'pre_order%';

-- ============================================================================
-- Notas de Performance
-- ============================================================================

-- 1. Índices compostos são mais eficientes para consultas que filtram por
--    múltiplas colunas na ordem especificada no índice.
--
-- 2. Índices em colunas de status são essenciais para dashboards que filtram
--    por estado (ex: "pré-ordens em negociação", "propostas pendentes").
--
-- 3. Índices em foreign keys melhoram performance de joins e consultas
--    relacionadas.
--
-- 4. Índices em timestamps (created_at, expires_at) otimizam ordenação e
--    consultas por período.
--
-- 5. O índice DESC em created_at do histórico otimiza a consulta padrão
--    que mostra eventos mais recentes primeiro.
--
-- ============================================================================
-- Estimativa de Impacto
-- ============================================================================

-- Consultas otimizadas:
-- - Dashboard de pré-ordens por usuário: 10-50x mais rápido
-- - Listagem de propostas pendentes: 5-20x mais rápido
-- - Timeline de histórico: 10-30x mais rápido
-- - Job de expiração: 20-100x mais rápido
-- - Consultas de auditoria: 10-50x mais rápido
--
-- Overhead:
-- - Espaço em disco: ~5-10% adicional
-- - Tempo de INSERT/UPDATE: ~5-15% mais lento (aceitável)
--
-- ============================================================================
