-- Migration: Adicionar campos para sistema de gestão de ordens
-- Data: 2025-11-14
-- Descrição: Adiciona campos de configuração de taxas, confirmação automática e provas de contestação

-- Adicionar campos de taxas vigentes na criação
ALTER TABLE orders ADD COLUMN platform_fee_percentage_at_creation NUMERIC(5, 2);
ALTER TABLE orders ADD COLUMN contestation_fee_at_creation NUMERIC(10, 2);
ALTER TABLE orders ADD COLUMN cancellation_fee_percentage_at_creation NUMERIC(5, 2);

-- Adicionar campo de confirmação automática
ALTER TABLE orders ADD COLUMN auto_confirmed BOOLEAN NOT NULL DEFAULT FALSE;

-- Adicionar campo de URLs de provas de contestação
ALTER TABLE orders ADD COLUMN dispute_evidence_urls TEXT;

-- Comentários para documentação
COMMENT ON COLUMN orders.platform_fee_percentage_at_creation IS 'Taxa da plataforma (%) vigente no momento da criação da ordem';
COMMENT ON COLUMN orders.contestation_fee_at_creation IS 'Taxa de contestação (valor fixo) vigente no momento da criação da ordem';
COMMENT ON COLUMN orders.cancellation_fee_percentage_at_creation IS 'Taxa de cancelamento (%) vigente no momento da criação da ordem';
COMMENT ON COLUMN orders.auto_confirmed IS 'Indica se a ordem foi confirmada automaticamente após 36 horas';
COMMENT ON COLUMN orders.dispute_evidence_urls IS 'JSON array com URLs dos arquivos de prova enviados na contestação';
