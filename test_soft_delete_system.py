#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para o sistema de soft delete
"""

import os
from flask import Flask
from models import db, User, AdminUser
from services.soft_delete_service import SoftDeleteService, SoftDeleteError

def create_test_app():
    """Cria aplicação Flask para testes"""
    app = Flask(__name__)
    
    # Usar banco em memória para testes
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    db.init_app(app)
    return app

def test_soft_delete_user():
    """Testa soft delete de usuário"""
    app = create_test_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Criar admin
        admin = AdminUser(email='admin@test.com', papel='admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        
        # Criar usuário
        user = User(email='user@test.com', nome='Usuário Teste', cpf='12345678901')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Verificar que usuário não está deletado
        assert not user.is_deleted
        
        # Executar soft delete
        result = SoftDeleteService.soft_delete_user(user.id, admin.id, "Teste")
        assert result is True
        
        # Verificar que usuário foi marcado como deletado
        user_updated = db.session.get(User, user.id)
        assert user_updated.is_deleted
        assert user_updated.deleted_by == admin.id
        assert user_updated.deletion_reason == "Teste"
        assert not user_updated.active
        
        print("✓ Teste de soft delete de usuário passou!")

def test_restore_user():
    """Testa restauração de usuário"""
    app = create_test_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Criar admin
        admin = AdminUser(email='admin@test.com', papel='admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        
        # Criar usuário
        user = User(email='user@test.com', nome='Usuário Teste', cpf='12345678901')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Deletar usuário
        SoftDeleteService.soft_delete_user(user.id, admin.id, "Teste")
        
        # Verificar que está deletado
        user_deleted = db.session.get(User, user.id)
        assert user_deleted.is_deleted
        
        # Restaurar usuário
        result = SoftDeleteService.restore_user(user.id, admin.id)
        assert result is True
        
        # Verificar que foi restaurado
        user_restored = db.session.get(User, user.id)
        assert not user_restored.is_deleted
        assert user_restored.deleted_by is None
        assert user_restored.deletion_reason is None
        assert user_restored.active
        
        print("✓ Teste de restauração de usuário passou!")

def test_get_active_users():
    """Testa filtro de usuários ativos"""
    app = create_test_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Criar admin
        admin = AdminUser(email='admin@test.com', papel='admin')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        
        # Criar usuários
        user1 = User(email='user1@test.com', nome='Usuário 1', cpf='11111111111')
        user1.set_password('123456')
        db.session.add(user1)
        
        user2 = User(email='user2@test.com', nome='Usuário 2', cpf='22222222222')
        user2.set_password('123456')
        db.session.add(user2)
        
        db.session.commit()
        
        # Deletar um usuário
        SoftDeleteService.soft_delete_user(user2.id, admin.id, "Teste")
        
        # Verificar filtros
        active_users = SoftDeleteService.get_active_users()
        deleted_users = SoftDeleteService.get_deleted_users()
        
        assert len(active_users) == 1
        assert active_users[0].id == user1.id
        
        assert len(deleted_users) == 1
        assert deleted_users[0].id == user2.id
        
        print("✓ Teste de filtros de usuários passou!")

def test_soft_delete_errors():
    """Testa tratamento de erros"""
    app = create_test_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Tentar deletar usuário inexistente
        try:
            SoftDeleteService.soft_delete_user(999, 1, "Teste")
            assert False, "Deveria ter lançado exceção"
        except SoftDeleteError as e:
            assert "não encontrado" in str(e)
        
        # Tentar deletar com admin inexistente
        user = User(email='user@test.com', nome='Usuário Teste', cpf='12345678901')
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        try:
            SoftDeleteService.soft_delete_user(user.id, 999, "Teste")
            assert False, "Deveria ter lançado exceção"
        except SoftDeleteError as e:
            assert "Admin com ID 999 não encontrado" in str(e)
        
        print("✓ Teste de tratamento de erros passou!")

if __name__ == '__main__':
    print("=== Testes do Sistema de Soft Delete ===")
    
    try:
        test_soft_delete_user()
        test_restore_user()
        test_get_active_users()
        test_soft_delete_errors()
        
        print("\n🎉 Todos os testes passaram!")
        
    except Exception as e:
        print(f"\n❌ Erro nos testes: {str(e)}")
        import traceback
        traceback.print_exc()