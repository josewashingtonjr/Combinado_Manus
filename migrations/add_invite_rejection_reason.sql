-- Migração para adicionar campo de motivo de rejeição aos convites
-- Data: 2024-11-06
-- Descrição: Adiciona campo rejection_reason à tabela invites para armazenar o motivo da rejeição

-- Adicionar campo rejection_reason à tabela invites
ALTER TABLE invites ADD COLUMN rejection_reason TEXT NULL;

-- Comentário sobre o campo
-- rejection_reason: Motivo opcional fornecido pelo prestador ao rejeitar um convite