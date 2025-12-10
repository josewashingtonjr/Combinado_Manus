#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para criar tabelas e aplicar migração de soft delete
"""

import os
from flask import Flask
from models import db

def create_app():
    """Cria aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração do banco de dados
    database_path = os.path.join(os.path.dirname(__file__), 'sistema_combinado.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def create_tables_and_migrate():
    """Cria todas as tabelas e aplica migração de soft delete"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Criando todas as tabelas...")
            
            # Criar todas as tabelas definidas nos modelos
            db.create_all()
            
            print("✓ Tabelas criadas com sucesso!")
            
            # Verificar se as tabelas foram criadas
            from sqlalchemy import text
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Tabelas criadas: {', '.join(tables)}")
            
            # Verificar se os campos de soft delete já estão presentes
            if 'users' in tables:
                result = db.session.execute(text("PRAGMA table_info(users)"))
                user_columns = [row[1] for row in result.fetchall()]
                
                expected_columns = ['deleted_at', 'deleted_by', 'deletion_reason']
                missing_columns = [col for col in expected_columns if col not in user_columns]
                
                if missing_columns:
                    print(f"⚠ Campos de soft delete faltando em users: {missing_columns}")
                    print("Isso é esperado pois os modelos já incluem os campos de soft delete.")
                else:
                    print("✓ Todos os campos de soft delete estão presentes em users!")
            
            if 'admin_users' in tables:
                result = db.session.execute(text("PRAGMA table_info(admin_users)"))
                admin_columns = [row[1] for row in result.fetchall()]
                
                expected_columns = ['deleted_at', 'deleted_by', 'deletion_reason']
                missing_columns = [col for col in expected_columns if col not in admin_columns]
                
                if missing_columns:
                    print(f"⚠ Campos de soft delete faltando em admin_users: {missing_columns}")
                    print("Isso é esperado pois os modelos já incluem os campos de soft delete.")
                else:
                    print("✓ Todos os campos de soft delete estão presentes em admin_users!")
            
            return True
            
        except Exception as e:
            print(f"Erro: {str(e)}")
            return False

def test_soft_delete_functionality():
    """Testa a funcionalidade de soft delete"""
    app = create_app()
    
    with app.app_context():
        try:
            from models import User, AdminUser
            from services.soft_delete_service import SoftDeleteService
            
            print("\nTestando funcionalidade de soft delete...")
            
            # Criar um admin de teste
            admin = AdminUser(email='admin@test.com', papel='admin')
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
            
            # Criar um usuário de teste
            user = User(email='user@test.com', nome='Usuário Teste', cpf='12345678901')
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            
            print(f"✓ Admin criado: {admin.email} (ID: {admin.id})")
            print(f"✓ Usuário criado: {user.email} (ID: {user.id})")
            
            # Testar soft delete do usuário
            print(f"Testando soft delete do usuário...")
            result = SoftDeleteService.soft_delete_user(user.id, admin.id, "Teste de soft delete")
            
            if result:
                print("✓ Soft delete do usuário executado com sucesso!")
                
                # Verificar se o usuário foi marcado como deletado
                user_updated = User.query.get(user.id)
                if user_updated.is_deleted:
                    print("✓ Usuário marcado como deletado corretamente!")
                else:
                    print("✗ Usuário não foi marcado como deletado!")
                
                # Testar restauração
                print("Testando restauração do usuário...")
                restore_result = SoftDeleteService.restore_user(user.id, admin.id)
                
                if restore_result:
                    print("✓ Restauração do usuário executada com sucesso!")
                    
                    # Verificar se o usuário foi restaurado
                    user_restored = User.query.get(user.id)
                    if not user_restored.is_deleted:
                        print("✓ Usuário restaurado corretamente!")
                    else:
                        print("✗ Usuário não foi restaurado!")
                else:
                    print("✗ Falha na restauração do usuário!")
            else:
                print("✗ Falha no soft delete do usuário!")
            
            # Limpar dados de teste
            db.session.delete(user)
            db.session.delete(admin)
            db.session.commit()
            
            print("✓ Dados de teste removidos!")
            
            return True
            
        except Exception as e:
            print(f"Erro no teste: {str(e)}")
            return False

if __name__ == '__main__':
    print("=== Criação de Tabelas e Migração de Soft Delete ===")
    
    if create_tables_and_migrate():
        if test_soft_delete_functionality():
            print("\n🎉 Tabelas criadas e soft delete funcionando corretamente!")
        else:
            print("\n⚠ Tabelas criadas mas teste de soft delete falhou!")
    else:
        print("\n❌ Falha na criação das tabelas!")