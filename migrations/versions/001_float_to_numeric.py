"""Migrar Float para Numeric em campos monetários

Revision ID: 001_float_to_numeric
Revises: 
Create Date: 2025-10-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_float_to_numeric'
down_revision = None
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
    """
    # Wallet: balance e escrow_balance
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=18, scale=2),
                    existing_nullable=False,
                    postgresql_using='balance::numeric(18,2)')
    
    op.alter_column('wallets', 'escrow_balance',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=18, scale=2),
                    existing_nullable=False,
                    postgresql_using='escrow_balance::numeric(18,2)')
    
    # Transaction: amount
    op.alter_column('transactions', 'amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=18, scale=2),
                    existing_nullable=False,
                    postgresql_using='amount::numeric(18,2)')
    
    # Order: value
    op.alter_column('orders', 'value',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(precision=18, scale=2),
                    existing_nullable=False,
                    postgresql_using='value::numeric(18,2)')


def downgrade():
    """
    Reverte a migração de Numeric para Float.
    ATENÇÃO: Pode haver perda de precisão ao reverter.
    """
    # Order: value
    op.alter_column('orders', 'value',
                    existing_type=sa.Numeric(precision=18, scale=2),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='value::float')
    
    # Transaction: amount
    op.alter_column('transactions', 'amount',
                    existing_type=sa.Numeric(precision=18, scale=2),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='amount::float')
    
    # Wallet: escrow_balance e balance
    op.alter_column('wallets', 'escrow_balance',
                    existing_type=sa.Numeric(precision=18, scale=2),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='escrow_balance::float')
    
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(precision=18, scale=2),
                    type_=sa.Float(),
                    existing_nullable=False,
                    postgresql_using='balance::float')

