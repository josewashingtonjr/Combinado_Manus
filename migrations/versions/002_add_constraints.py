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
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Apply database constraints"""
    
    # ==============================================================================
    # 1. CHECK CONSTRAINTS - Garantir saldos não-negativos
    # ==============================================================================
    
    # Wallet.balance >= 0
    op.create_check_constraint(
        'wallet_balance_non_negative',
        'wallet',
        'balance >= 0'
    )
    
    # Wallet.escrow_balance >= 0
    op.create_check_constraint(
        'wallet_escrow_balance_non_negative',
        'wallet',
        'escrow_balance >= 0'
    )
    
    # ==============================================================================
    # 2. UNIQUE CONSTRAINTS - Garantir unicidade de email e CPF
    # ==============================================================================
    
    # User.email - UNIQUE
    # Nota: Verificar se já existe antes de criar
    try:
        op.create_unique_constraint(
            'user_email_unique',
            'user',
            ['email']
        )
    except Exception as e:
        print(f"Constraint user_email_unique já existe ou erro: {e}")
    
    # User.cpf - UNIQUE (apenas se não for NULL)
    # Nota: PostgreSQL permite múltiplos NULLs em UNIQUE constraints
    try:
        op.create_unique_constraint(
            'user_cpf_unique',
            'user',
            ['cpf']
        )
    except Exception as e:
        print(f"Constraint user_cpf_unique já existe ou erro: {e}")
    
    # ==============================================================================
    # 3. ÍNDICES - Melhorar performance de queries
    # ==============================================================================
    
    # Índice em Wallet.user_id (se não existir)
    try:
        op.create_index(
            'idx_wallet_user_id',
            'wallet',
            ['user_id']
        )
    except Exception as e:
        print(f"Índice idx_wallet_user_id já existe ou erro: {e}")
    
    # Índice em Transaction.user_id
    try:
        op.create_index(
            'idx_transaction_user_id',
            'transaction',
            ['user_id']
        )
    except Exception as e:
        print(f"Índice idx_transaction_user_id já existe ou erro: {e}")
    
    # Índice em Transaction.created_at para queries temporais
    try:
        op.create_index(
            'idx_transaction_created_at',
            'transaction',
            ['created_at']
        )
    except Exception as e:
        print(f"Índice idx_transaction_created_at já existe ou erro: {e}")
    
    # Índice em Order.status para filtros
    try:
        op.create_index(
            'idx_order_status',
            'order',
            ['status']
        )
    except Exception as e:
        print(f"Índice idx_order_status já existe ou erro: {e}")
    
    # Índice em Order.client_id
    try:
        op.create_index(
            'idx_order_client_id',
            'order',
            ['client_id']
        )
    except Exception as e:
        print(f"Índice idx_order_client_id já existe ou erro: {e}")
    
    # Índice em Order.provider_id
    try:
        op.create_index(
            'idx_order_provider_id',
            'order',
            ['provider_id']
        )
    except Exception as e:
        print(f"Índice idx_order_provider_id já existe ou erro: {e}")
    
    print("✅ Constraints e índices adicionados com sucesso!")


def downgrade():
    """Remove database constraints"""
    
    # Remover índices
    op.drop_index('idx_order_provider_id', table_name='order')
    op.drop_index('idx_order_client_id', table_name='order')
    op.drop_index('idx_order_status', table_name='order')
    op.drop_index('idx_transaction_created_at', table_name='transaction')
    op.drop_index('idx_transaction_user_id', table_name='transaction')
    op.drop_index('idx_wallet_user_id', table_name='wallet')
    
    # Remover UNIQUE constraints
    op.drop_constraint('user_cpf_unique', 'user', type_='unique')
    op.drop_constraint('user_email_unique', 'user', type_='unique')
    
    # Remover CHECK constraints
    op.drop_constraint('wallet_escrow_balance_non_negative', 'wallet', type_='check')
    op.drop_constraint('wallet_balance_non_negative', 'wallet', type_='check')
    
    print("✅ Constraints e índices removidos com sucesso!")


if __name__ == '__main__':
    """
    Script pode ser executado diretamente para aplicar migração
    """
    print("=" * 80)
    print("MIGRAÇÃO 002: Adicionar Constraints de Banco de Dados")
    print("=" * 80)
    print()
    print("⚠️  ATENÇÃO: Faça backup do banco de dados antes de continuar!")
    print()
    
    response = input("Deseja continuar com a migração? (sim/não): ")
    
    if response.lower() in ['sim', 's', 'yes', 'y']:
        from app import app, db
        
        with app.app_context():
            try:
                upgrade()
                print()
                print("=" * 80)
                print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                print("=" * 80)
            except Exception as e:
                print()
                print("=" * 80)
                print(f"❌ ERRO NA MIGRAÇÃO: {e}")
                print("=" * 80)
                print()
                print("Executando rollback...")
                try:
                    downgrade()
                    print("✅ Rollback concluído")
                except Exception as rollback_error:
                    print(f"❌ Erro no rollback: {rollback_error}")
    else:
        print("Migração cancelada pelo usuário.")

