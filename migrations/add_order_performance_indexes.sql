-- ============================================================================
-- Script de Migração: Índices de Performance para Tabela Orders
-- Sistema de Gestão de Ordens Completo - Tarefa 32
-- Data: 2025-11-19
-- ============================================================================

-- Este script implementa índices específicos para otimizar consultas
-- frequentes na tabela de ordens, melhorando a performance do sistema
-- de gestão de ordens, especialmente para:
-- - Busca de ordens por status
-- - Verificação de prazos de confirmação automática
-- - Consultas de ordens por cliente e prestador
-- - Ordenação por data de criação

BEGIN;

-- ============================================================================
-- CRIAÇÃO DE ÍNDICES DE PERFORMANCE
-- ============================================================================

-- Índice para consultas por status
-- Usado em: listagem de ordens, filtros de dashboard, job de confirmação automática
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Índice para verificação de prazos de confirmação automática
-- Usado em: job auto_confirm_expired_orders que busca ordens expiradas
CREATE INDEX IF NOT EXISTS idx_orders_confirmation_deadline ON orders(confirmation_deadline);

-- Índice para consultas de ordens por cliente
-- Usado em: dashboard do cliente, listagem de ordens do cliente
CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id);

-- Índice para consultas de ordens por prestador
-- Usado em: dashboard do prestador, listagem de ordens do prestador
CREATE INDEX IF NOT EXISTS idx_orders_provider_id ON orders(provider_id);

-- Índice para ordenação por data de criação (DESC)
-- Usado em: listagens ordenadas por data mais recente
CREATE INDEX IF NOT EXISTS idx_orders_created_at_desc ON orders(created_at DESC);

-- ============================================================================
-- ÍNDICES COMPOSTOS ADICIONAIS PARA OTIMIZAÇÃO
-- ============================================================================

-- Índice composto para consultas de ordens por cliente e status
-- Otimiza consultas como: "buscar ordens do cliente X com status Y"
CREATE INDEX IF NOT EXISTS idx_orders_client_status ON orders(client_id, status);

-- Índice composto para consultas de ordens por prestador e status
-- Otimiza consultas como: "buscar ordens do prestador X com status Y"
CREATE INDEX IF NOT EXISTS idx_orders_provider_status ON orders(provider_id, status);

-- Índice composto para job de confirmação automática
-- Otimiza a busca de ordens com status=servico_executado e prazo expirado
CREATE INDEX IF NOT EXISTS idx_orders_status_confirmation_deadline ON orders(status, confirmation_deadline);

-- ============================================================================
-- VERIFICAÇÃO DOS ÍNDICES CRIADOS
-- ============================================================================

SELECT 'VERIFICAÇÃO DE ÍNDICES CRIADOS:' as titulo;

-- Listar todos os índices da tabela orders
SELECT 
    name as indice, 
    sql as definicao
FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name = 'orders'
AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- ============================================================================
-- ESTATÍSTICAS DA TABELA ORDERS
-- ============================================================================

SELECT 'ESTATÍSTICAS DA TABELA ORDERS:' as titulo;

-- Contagem total de ordens
SELECT 'Total de ordens:' as metrica, COUNT(*) as valor
FROM orders;

-- Distribuição por status
SELECT 'Distribuição por status:' as metrica;
SELECT status, COUNT(*) as quantidade
FROM orders
GROUP BY status
ORDER BY quantidade DESC;

-- Ordens aguardando confirmação automática
SELECT 'Ordens aguardando confirmação automática:' as metrica, COUNT(*) as valor
FROM orders
WHERE status = 'servico_executado' 
AND confirmation_deadline IS NOT NULL
AND confirmation_deadline > datetime('now');

-- Ordens expiradas (para confirmação automática)
SELECT 'Ordens expiradas (confirmação automática):' as metrica, COUNT(*) as valor
FROM orders
WHERE status = 'servico_executado' 
AND confirmation_deadline IS NOT NULL
AND confirmation_deadline <= datetime('now');

-- ============================================================================
-- ANÁLISE DE PERFORMANCE (OPCIONAL)
-- ============================================================================

-- Verificar o plano de execução de consultas comuns
-- Estas consultas mostram como o SQLite usará os índices

SELECT 'ANÁLISE DE PERFORMANCE - Plano de Execução:' as titulo;

-- Consulta 1: Buscar ordens por status
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE status = 'servico_executado';

-- Consulta 2: Buscar ordens expiradas para confirmação automática
EXPLAIN QUERY PLAN
SELECT * FROM orders 
WHERE status = 'servico_executado' 
AND confirmation_deadline <= datetime('now');

-- Consulta 3: Buscar ordens de um cliente específico
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE client_id = 1 ORDER BY created_at DESC;

-- Consulta 4: Buscar ordens de um prestador com status específico
EXPLAIN QUERY PLAN
SELECT * FROM orders WHERE provider_id = 1 AND status = 'aguardando_execucao';

-- ============================================================================
-- RECOMENDAÇÕES DE MANUTENÇÃO
-- ============================================================================

/*
RECOMENDAÇÕES PARA MANUTENÇÃO DOS ÍNDICES:

1. ANALYZE: Execute periodicamente para atualizar estatísticas
   ANALYZE orders;

2. VACUUM: Execute após grandes volumes de DELETE/UPDATE
   VACUUM;

3. REINDEX: Execute se houver corrupção ou degradação de performance
   REINDEX orders;

4. Monitoramento: Acompanhe o tamanho dos índices
   SELECT name, pgsize FROM dbstat WHERE name LIKE 'idx_orders%';

5. Performance: Use EXPLAIN QUERY PLAN para verificar uso dos índices
   EXPLAIN QUERY PLAN SELECT ...;
*/

COMMIT;

-- ============================================================================
-- RELATÓRIO FINAL
-- ============================================================================

SELECT 'IMPLEMENTAÇÃO CONCLUÍDA' as status,
       'Índices de performance para tabela orders criados com sucesso' as descricao,
       datetime('now') as data_implementacao;

SELECT 'ÍNDICES CRIADOS:' as resumo,
       '- idx_orders_status' as indice_1,
       '- idx_orders_confirmation_deadline' as indice_2,
       '- idx_orders_client_id' as indice_3,
       '- idx_orders_provider_id' as indice_4,
       '- idx_orders_created_at_desc' as indice_5,
       '- idx_orders_client_status (composto)' as indice_6,
       '- idx_orders_provider_status (composto)' as indice_7,
       '- idx_orders_status_confirmation_deadline (composto)' as indice_8;
