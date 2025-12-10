-- Migration: Add invite proposals table and related fields
-- Description: Creates the invite_proposals table and adds proposal-related fields to invites table
-- Requirements: 8.2, 8.3

-- Create invite_proposals table
CREATE TABLE IF NOT EXISTS invite_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invite_id INTEGER NOT NULL,
    prestador_id INTEGER NOT NULL,
    original_value DECIMAL(10,2) NOT NULL,
    proposed_value DECIMAL(10,2) NOT NULL,
    justification TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP NULL,
    client_response_reason TEXT NULL,
    FOREIGN KEY (invite_id) REFERENCES invites(id) ON DELETE CASCADE,
    FOREIGN KEY (prestador_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add proposal-related fields to invites table
ALTER TABLE invites ADD COLUMN has_active_proposal BOOLEAN DEFAULT FALSE;
ALTER TABLE invites ADD COLUMN current_proposal_id INTEGER NULL;
ALTER TABLE invites ADD COLUMN effective_value DECIMAL(10,2) NULL;

-- Add foreign key constraint for current_proposal_id
-- Note: SQLite doesn't support adding foreign key constraints to existing tables
-- This will be handled in the Python migration script

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_invites_proposal_status ON invites(has_active_proposal, status);
CREATE INDEX IF NOT EXISTS idx_proposals_invite_status ON invite_proposals(invite_id, status);
CREATE INDEX IF NOT EXISTS idx_proposals_prestador ON invite_proposals(prestador_id);
CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON invite_proposals(created_at);

-- Add constraints for data integrity
-- Note: SQLite has limited support for adding constraints to existing tables
-- These will be enforced at the application level and in the model definitions

-- Ensure proposed_value is positive
-- This will be handled in the model validation

-- Ensure status is valid
-- This will be handled in the model validation