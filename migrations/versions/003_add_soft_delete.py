"""Add soft delete fields to User and Order

Revision ID: 003
Revises: 002
Create Date: 2025-10-31

Description:
    Adiciona campos deleted_at para implementar soft delete:
    - User.deleted_at: Permite desativar usuários sem remover dados
    - Order.deleted_at: Permite arquivar ordens sem perder histórico

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    """Add soft delete fields"""
    
    # Adicionar deleted_at ao User
    op.add_column('users', 
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Adicionar deleted_at ao Order
    op.add_column('orders', 
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    
    # Criar índice em User.deleted_at para queries eficientes
    op.create_index(
        'idx_users_deleted_at',
        'users',
        ['deleted_at']
    )
    
    # Criar índice em Order.deleted_at para queries eficientes
    op.create_index(
        'idx_orders_deleted_at',
        'orders',
        ['deleted_at']
    )
    
    print("✅ Campos de soft delete adicionados com sucesso!")


def downgrade():
    """Remove soft delete fields"""
    
    # Remover índices
    op.drop_index('idx_orders_deleted_at', table_name='orders')
    op.drop_index('idx_users_deleted_at', table_name='users')
    
    # Remover colunas
    op.drop_column('orders', 'deleted_at')
    op.drop_column('users', 'deleted_at')
    
    print("✅ Campos de soft delete removidos com sucesso!")


if __name__ == '__main__':
    """
    Script pode ser executado diretamente para aplicar migração
    """
    print("=" * 80)
    print("MIGRAÇÃO 003: Adicionar Soft Delete")
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

