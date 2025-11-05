-- Migração: Adicionar campos de disputa ao modelo Order
-- Data: 2025-10-05
-- Task: 11.4

ALTER TABLE orders ADD COLUMN dispute_reason TEXT;
ALTER TABLE orders ADD COLUMN dispute_opened_by INTEGER REFERENCES users(id);
ALTER TABLE orders ADD COLUMN dispute_opened_at TIMESTAMP;
ALTER TABLE orders ADD COLUMN dispute_resolved_at TIMESTAMP;
ALTER TABLE orders ADD COLUMN dispute_resolution TEXT;
