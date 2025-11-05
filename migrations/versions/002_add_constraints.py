"""Add database constraints for data integrity

Revision ID: 002
Revises: 001
Create Date: 2025-10-31

Description:
    Adiciona constraints de integridade ao banco de dados:
    - CHECK constraints para garantir saldos não-negativos
    - UNIQUE constraints para email e CPF
    - Índices para melhorar performance

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    """Apply database constraints"""
    
    # ==============================================================================
    # 1. CHECK CONSTRAINTS - Garantir saldos não-negativos
    # ==============================================================================
    
    # Wallet.balance >= 0
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'wallet_balance_non_negative',
            'balance >= 0'
        )
        batch_op.create_check_constraint(
            'wallet_escrow_balance_non_negative',
            'escrow_balance >= 0'
        )
    
    # ==============================================================================
    # 2. UNIQUE CONSTRAINTS - Garantir unicidade de email e CPF
    # ==============================================================================
    
    # User.email - UNIQUE
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Verificar se a constraint já existe
        try:
            batch_op.create_unique_constraint(
                'user_email_unique',
                ['email']
            )
        except:
            pass  # Constraint já existe
        
        # User.cpf - UNIQUE (apenas se não for NULL)
        try:
            batch_op.create_unique_constraint(
                'user_cpf_unique',
                ['cpf']
            )
        except:
            pass  # Constraint já existe
    
    # ==============================================================================
    # 3. ÍNDICES - Melhorar performance de queries
    # ==============================================================================
    
    # Índice em Wallet.user_id (se não existir)
    try:
        op.create_index(
            'idx_wallet_user_id',
            'wallets',
            ['user_id']
        )
    except:
        pass  # Índice já existe
    
    # Índice em Transaction.user_id
    try:
        op.create_index(
            'idx_transaction_user_id',
            'transactions',
            ['user_id']
        )
    except:
        pass
    
    # Índice em Transaction.created_at para queries temporais
    try:
        op.create_index(
            'idx_transaction_created_at',
            'transactions',
            ['created_at']
        )
    except:
        pass
    
    # Índice em Order.status para filtros
    try:
        op.create_index(
            'idx_order_status',
            'orders',
            ['status']
        )
    except:
        pass
    
    # Índice em Order.client_id
    try:
        op.create_index(
            'idx_order_client_id',
            'orders',
            ['client_id']
        )
    except:
        pass
    
    # Índice em Order.provider_id
    try:
        op.create_index(
            'idx_order_provider_id',
            'orders',
            ['provider_id']
        )
    except:
        pass


def downgrade():
    """Remove database constraints"""
    
    # Remover índices
    try:
        op.drop_index('idx_order_provider_id', table_name='orders')
    except:
        pass
    
    try:
        op.drop_index('idx_order_client_id', table_name='orders')
    except:
        pass
    
    try:
        op.drop_index('idx_order_status', table_name='orders')
    except:
        pass
    
    try:
        op.drop_index('idx_transaction_created_at', table_name='transactions')
    except:
        pass
    
    try:
        op.drop_index('idx_transaction_user_id', table_name='transactions')
    except:
        pass
    
    try:
        op.drop_index('idx_wallet_user_id', table_name='wallets')
    except:
        pass
    
    # Remover UNIQUE constraints
    with op.batch_alter_table('users', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('user_cpf_unique', type_='unique')
        except:
            pass
        
        try:
            batch_op.drop_constraint('user_email_unique', type_='unique')
        except:
            pass
    
    # Remover CHECK constraints
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('wallet_escrow_balance_non_negative', type_='check')
        except:
            pass
        
        try:
            batch_op.drop_constraint('wallet_balance_non_negative', type_='check')
        except:
            pass

