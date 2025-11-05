-- Migração: Adicionar campos de telefone e categoria de serviço ao modelo Invite
-- Data: 2025-11-05
-- Descrição: Substituir email por telefone e adicionar categoria de serviço

-- Adicionar nova coluna para telefone
ALTER TABLE invites ADD COLUMN invited_phone VARCHAR(20);

-- Adicionar nova coluna para categoria de serviço
ALTER TABLE invites ADD COLUMN service_category VARCHAR(100);

-- Migrar dados existentes (se houver) - email para telefone
-- UPDATE invites SET invited_phone = invited_email WHERE invited_phone IS NULL;

-- Comentário: O campo invited_email será mantido por compatibilidade, mas invited_phone será o campo principal