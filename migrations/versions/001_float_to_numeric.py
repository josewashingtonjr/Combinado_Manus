"""Migrar Float para Numeric em campos monetários

Revision ID: 001_float_to_numeric
Revises: 
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '60679096b063'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migra campos Float para Numeric(18, 2) para garantir precisão monetária.
    
    Campos afetados:
    - wallets.balance
    - wallets.escrow_balance
    - transactions.amount
    - orders.value
    
    Nota: SQLite não suporta ALTER COLUMN TYPE diretamente.
    Usamos batch operations para recriar as tabelas.
    """
    
    # Para SQLite, precisamos usar batch operations
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.alter_column('balance',
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=18, scale=2),
                              existing_nullable=False)
        batch_op.alter_column('escrow_balance',
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=18, scale=2),
                              existing_nullable=False)
    
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('amount',
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=18, scale=2),
                              existing_nullable=False)
    
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('value',
                              existing_type=sa.Float(),
                              type_=sa.Numeric(precision=18, scale=2),
                              existing_nullable=False)


def downgrade():
    """
    Reverte a migração de Numeric para Float.
    ATENÇÃO: Pode haver perda de precisão ao reverter.
    """
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('value',
                              existing_type=sa.Numeric(precision=18, scale=2),
                              type_=sa.Float(),
                              existing_nullable=False)
    
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('amount',
                              existing_type=sa.Numeric(precision=18, scale=2),
                              type_=sa.Float(),
                              existing_nullable=False)
    
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.alter_column('escrow_balance',
                              existing_type=sa.Numeric(precision=18, scale=2),
                              type_=sa.Float(),
                              existing_nullable=False)
        batch_op.alter_column('balance',
                              existing_type=sa.Numeric(precision=18, scale=2),
                              type_=sa.Float(),
                              existing_nullable=False)

