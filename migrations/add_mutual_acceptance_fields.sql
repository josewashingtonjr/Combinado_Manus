-- Migração: Adicionar campos de aceitação mútua ao modelo Invite
-- Data: 2025-11-20
-- Descrição: Adiciona campos para rastrear aceitação individual do cliente e prestador
--            antes de criar automaticamente a ordem de serviço

-- Adicionar campos de aceitação do cliente
ALTER TABLE invites ADD COLUMN client_accepted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE invites ADD COLUMN client_accepted_at TIMESTAMP NULL;

-- Adicionar campos de aceitação do prestador
ALTER TABLE invites ADD COLUMN provider_accepted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE invites ADD COLUMN provider_accepted_at TIMESTAMP NULL;

-- Criar índice composto para performance em consultas de aceitação mútua
CREATE INDEX idx_invite_mutual_acceptance ON invites(client_accepted, provider_accepted, status);

-- Comentários para documentação
COMMENT ON COLUMN invites.client_accepted IS 'Indica se o cliente aceitou o convite';
COMMENT ON COLUMN invites.client_accepted_at IS 'Timestamp de quando o cliente aceitou';
COMMENT ON COLUMN invites.provider_accepted IS 'Indica se o prestador aceitou o convite';
COMMENT ON COLUMN invites.provider_accepted_at IS 'Timestamp de quando o prestador aceitou';
