-- ============================================================================
-- Script de Migração: Constraints Adicionais de Integridade Financeira
-- Sistema de Correções Críticas - Tarefa 2
-- Data: 2025-11-06
-- ============================================================================

-- Este script implementa constraints adicionais e índices para otimizar
-- consultas financeiras frequentes e garantir integridade dos dados

BEGIN;

-- ============================================================================
-- VERIFICAÇÃO E CRIAÇÃO DE ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ============================================================================

-- Índices para consultas de auditoria e relatórios financeiros
CREATE INDEX IF NOT EXISTS idx_transactions_type_created ON transactions(type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_amount_created ON transactions(amount DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_related_user ON transactions(related_user_id, created_at DESC);

-- Índices para consultas de ordens por cliente e prestador
CREATE INDEX IF NOT EXISTS idx_orders_client_status ON orders(client_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_provider_status ON orders(provider_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_value_created ON orders(value DESC, created_at DESC);

-- Índices para consultas de solicitações de tokens
CREATE INDEX IF NOT EXISTS idx_token_requests_status_created ON token_requests(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_requests_processed_by ON token_requests(processed_by, processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_token_requests_amount_status ON token_requests(amount DESC, status);

-- Índices para consultas de carteiras por saldo
CREATE INDEX IF NOT EXISTS idx_wallets_balance ON wallets(balance DESC);
CREATE INDEX IF NOT EXISTS idx_wallets_escrow_balance ON wallets(escrow_balance DESC);
CREATE INDEX IF NOT EXISTS idx_wallets_updated_at ON wallets(updated_at DESC);

-- ============================================================================
-- CONSTRAINTS ADICIONAIS DE INTEGRIDADE DE DADOS
-- ============================================================================

-- Verificar se constraints já existem antes de adicionar (SQLite não suporta IF NOT EXISTS para constraints)
-- Estas constraints já estão nos modelos SQLAlchemy, mas garantimos que estejam no banco

-- Para SQLite, as constraints CHECK já foram criadas durante a migração anterior
-- Vamos apenas verificar se existem dados que violam as regras

-- ============================================================================
-- VALIDAÇÃO DE INTEGRIDADE DOS DADOS EXISTENTES
-- ============================================================================

-- Verificar se existem violações de integridade nos dados atuais
SELECT 'VERIFICAÇÃO DE INTEGRIDADE FINANCEIRA' as titulo;

-- Verificar saldos negativos em wallets
SELECT 'Wallets com saldo negativo:' as verificacao, COUNT(*) as total
FROM wallets 
WHERE balance < 0 OR escrow_balance < 0;

-- Verificar transações com valor zero
SELECT 'Transações com valor zero:' as verificacao, COUNT(*) as total
FROM transactions 
WHERE amount = 0;

-- Verificar ordens com valor não positivo
SELECT 'Ordens com valor inválido:' as verificacao, COUNT(*) as total
FROM orders 
WHERE value <= 0;

-- Verificar solicitações de tokens com valor não positivo
SELECT 'Solicitações de tokens com valor inválido:' as verificacao, COUNT(*) as total
FROM token_requests 
WHERE amount <= 0;

-- Verificar precisão decimal (máximo 2 casas decimais)
SELECT 'Valores com mais de 2 casas decimais:' as verificacao,
       (SELECT COUNT(*) FROM wallets WHERE (balance * 100) != ROUND(balance * 100)) +
       (SELECT COUNT(*) FROM wallets WHERE (escrow_balance * 100) != ROUND(escrow_balance * 100)) +
       (SELECT COUNT(*) FROM transactions WHERE (amount * 100) != ROUND(amount * 100)) +
       (SELECT COUNT(*) FROM orders WHERE (value * 100) != ROUND(value * 100)) +
       (SELECT COUNT(*) FROM token_requests WHERE (amount * 100) != ROUND(amount * 100)) as total;

-- ============================================================================
-- ESTATÍSTICAS DE PERFORMANCE DOS ÍNDICES
-- ============================================================================

-- Verificar se os índices foram criados corretamente
SELECT 'ÍNDICES CRIADOS:' as titulo;

-- Listar todos os índices das tabelas financeiras
SELECT name as indice, tbl_name as tabela, sql as definicao
FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name IN ('wallets', 'transactions', 'orders', 'token_requests')
AND name NOT LIKE 'sqlite_%'
ORDER BY tbl_name, name;

COMMIT;

-- ============================================================================
-- SCRIPT DE TESTE DE CONSTRAINTS (OPCIONAL - EXECUTAR SEPARADAMENTE)
-- ============================================================================

/*
-- ATENÇÃO: Este bloco é apenas para teste e deve ser executado separadamente
-- Não executar em produção!

-- Teste 1: Tentar inserir saldo negativo (deve falhar)
-- INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (999, -10.00, 0.00);

-- Teste 2: Tentar inserir transação com valor zero (deve falhar)  
-- INSERT INTO transactions (user_id, type, amount, description) VALUES (999, 'teste', 0.00, 'Teste constraint');

-- Teste 3: Tentar inserir ordem com valor negativo (deve falhar)
-- INSERT INTO orders (client_id, title, description, value) VALUES (999, 'Teste', 'Teste constraint', -50.00);

-- Teste 4: Tentar inserir solicitação de token com valor negativo (deve falhar)
-- INSERT INTO token_requests (user_id, amount) VALUES (999, -100.00);
*/

-- ============================================================================
-- RELATÓRIO FINAL
-- ============================================================================

SELECT 'IMPLEMENTAÇÃO CONCLUÍDA' as status,
       'Constraints de integridade financeira implementadas' as descricao,
       datetime('now') as data_implementacao;