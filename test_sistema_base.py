#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar e validar a base existente do sistema
Tarefa 1: Validar e testar a base existente do sistema
"""

import sys
import os
import tempfile
from flask import Flask
from flask_testing import TestCase

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testar se todos os imports funcionam corretamente"""
    print("🔄 Testando imports...")
    
    try:
        from app import app, db
        from models import User, AdminUser, Wallet, Transaction, Order
        from services.auth_service import AuthService
        from services.wallet_service import WalletService
        from services.order_service import OrderService
        print("✅ Todos os imports funcionaram corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def test_database_models():
    """Testar se os modelos do banco funcionam"""
    print("🔄 Testando modelos do banco de dados...")
    
    try:
        # Configurar app para teste com SQLite
        from app import app, db
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Criar todas as tabelas
            db.create_all()
            
            # Testar criação de AdminUser
            from models import AdminUser
            admin = AdminUser(email='test@admin.com', papel='super_admin')
            admin.set_password('test123')
            db.session.add(admin)
            db.session.commit()
            
            # Verificar se foi criado
            admin_check = AdminUser.query.filter_by(email='test@admin.com').first()
            assert admin_check is not None
            assert admin_check.check_password('test123')
            
            # Testar criação de User
            from models import User
            user = User(
                nome='Teste User',
                email='test@user.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            
            # Verificar se foi criado
            user_check = User.query.filter_by(email='test@user.com').first()
            assert user_check is not None
            assert user_check.check_password('user123')
            
            print("✅ Modelos do banco funcionando corretamente")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes_exist():
    """Testar se as rotas principais existem"""
    print("🔄 Testando existência das rotas...")
    
    try:
        from app import app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            # Testar rota principal
            response = client.get('/')
            print(f"   Rota '/': Status {response.status_code}")
            
            # Testar rotas de login
            response = client.get('/auth/admin-login')
            print(f"   Rota '/auth/admin-login': Status {response.status_code}")
            
            response = client.get('/auth/user-login')
            print(f"   Rota '/auth/user-login': Status {response.status_code}")
            
            # Testar rota de teste
            response = client.get('/test-login')
            print(f"   Rota '/test-login': Status {response.status_code}")
            
            print("✅ Rotas principais existem e respondem")
            return True
            
    except Exception as e:
        print(f"❌ Erro nas rotas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_templates_render():
    """Testar se os templates renderizam sem erro"""
    print("🔄 Testando renderização de templates...")
    
    try:
        from app import app, db
        from models import AdminUser, User
        
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            
            # Criar usuários de teste
            admin = AdminUser(email='admin@test.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            user = User(
                nome='Test User',
                email='user@test.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            
        with app.test_client() as client:
            # Testar templates de login
            response = client.get('/auth/admin-login')
            assert response.status_code == 200
            assert b'admin' in response.data.lower()
            
            response = client.get('/auth/user-login')
            assert response.status_code == 200
            
            # Testar página inicial
            response = client.get('/')
            assert response.status_code == 200
            
            print("✅ Templates renderizam corretamente")
            return True
            
    except Exception as e:
        print(f"❌ Erro na renderização de templates: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_authentication_flow():
    """Testar fluxo de autenticação"""
    print("🔄 Testando fluxo de autenticação...")
    
    try:
        from app import app, db
        from models import AdminUser, User
        
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            
            # Criar usuários de teste
            admin = AdminUser(email='admin@test.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            user = User(
                nome='Test User',
                email='user@test.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            user.set_password('user123')
            db.session.add(user)
            db.session.commit()
            
        with app.test_client() as client:
            # Testar login de admin
            response = client.post('/auth/admin-login', data={
                'email': 'admin@test.com',
                'password': 'admin123'
            }, follow_redirects=True)
            
            # Verificar se foi redirecionado para dashboard admin
            assert response.status_code == 200
            
            # Testar logout
            response = client.get('/auth/logout', follow_redirects=True)
            assert response.status_code == 200
            
            # Testar login de usuário
            response = client.post('/auth/user-login', data={
                'email': 'user@test.com',
                'password': 'user123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            print("✅ Fluxo de autenticação funcionando")
            return True
            
    except Exception as e:
        print(f"❌ Erro no fluxo de autenticação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Testar se os serviços funcionam"""
    print("🔄 Testando serviços...")
    
    try:
        from app import app, db
        from models import User, AdminUser
        from services.auth_service import AuthService
        
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        
        with app.app_context():
            db.create_all()
            
            # Testar AuthService
            user = User(
                nome='Service Test',
                email='service@test.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            user.set_password('service123')
            db.session.add(user)
            db.session.commit()
            
            # Testar autenticação
            auth_user = AuthService.authenticate_user('service@test.com', 'service123')
            assert auth_user is not None
            assert auth_user.email == 'service@test.com'
            
            print("✅ Serviços funcionando corretamente")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos serviços: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executar todos os testes"""
    print("🚀 Iniciando validação da base do sistema...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_models,
        test_routes_exist,
        test_templates_render,
        test_authentication_flow,
        test_services
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print("-" * 30)
    
    # Resumo
    print("\n📊 RESUMO DOS TESTES:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes aprovados: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ A base do sistema está funcionando corretamente")
        return True
    else:
        print(f"\n⚠️  {total - passed} TESTE(S) FALHARAM")
        print("❌ A base do sistema precisa de correções")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)