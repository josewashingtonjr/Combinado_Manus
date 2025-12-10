-- Migração para adicionar campo transaction_id único na tabela transactions
-- Data: 2024-11-06
-- Descrição: Implementa sistema de identificação única de transações

-- Adicionar campo transaction_id na tabela transactions
ALTER TABLE transactions 
ADD COLUMN transaction_id VARCHAR(50);

-- Criar índice único para transaction_id
CREATE UNIQUE INDEX idx_transactions_transaction_id 
ON transactions(transaction_id);

-- Adicionar constraint de não-nulo após popular os dados existentes
-- (será executado em script separado após migração dos dados)

-- Comentários para documentação
COMMENT ON COLUMN transactions.transaction_id IS 'Identificador único da transação no formato TXN-YYYYMMDD-HHMMSS-UUID8';