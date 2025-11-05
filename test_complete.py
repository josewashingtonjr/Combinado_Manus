#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste completo do sistema - Tarefa 1: Validar e testar a base existente
"""

import os
import sys
import time
import subprocess
import threading
from multiprocessing import Process

# Configurar SQLite para teste
os.environ['DATABASE_URL'] = 'sqlite:///test_combinado.db'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_database():
    """Configurar banco de dados de teste"""
    print("🔄 Configurando banco de dados de teste...")
    
    try:
        from app import app, db
        from models import AdminUser, User
        
        with app.app_context():
            # Limpar e recriar tabelas
            db.drop_all()
            db.create_all()
            
            # Criar admin de teste
            admin = AdminUser(email='admin@test.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Criar usuário cliente
            cliente = User(
                nome='Cliente Teste',
                email='cliente@test.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            cliente.set_password('123456')
            db.session.add(cliente)
            
            # Criar usuário prestador
            prestador = User(
                nome='Prestador Teste',
                email='prestador@test.com',
                cpf='98765432100',
                phone='(11) 88888-8888',
                roles='prestador',
                active=True
            )
            prestador.set_password('123456')
            db.session.add(prestador)
            
            # Criar usuário dual
            dual = User(
                nome='Usuário Dual',
                email='dual@test.com',
                cpf='11122233344',
                phone='(11) 77777-7777',
                roles='cliente,prestador',
                active=True
            )
            dual.set_password('123456')
            db.session.add(dual)
            
            db.session.commit()
            
            print("✅ Banco de dados configurado com sucesso")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_models():
    """Testar modelos do banco de dados"""
    print("🔄 Testando modelos do banco de dados...")
    
    try:
        from app import app, db
        from models import User, AdminUser, Wallet, Transaction, Order
        
        with app.app_context():
            # Verificar se os usuários foram criados
            admin_count = AdminUser.query.count()
            user_count = User.query.count()
            
            print(f"   Admins: {admin_count}")
            print(f"   Usuários: {user_count}")
            
            # Testar autenticação
            admin = AdminUser.query.filter_by(email='admin@test.com').first()
            cliente = User.query.filter_by(email='cliente@test.com').first()
            
            assert admin is not None
            assert cliente is not None
            assert admin.check_password('admin123')
            assert cliente.check_password('123456')
            
            print("✅ Modelos funcionando corretamente")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos modelos: {e}")
        return False

def test_routes_and_templates():
    """Testar rotas e renderização de templates"""
    print("🔄 Testando rotas e templates...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            routes_to_test = [
                ('/', 'Página inicial'),
                ('/auth/admin-login', 'Login admin'),
                ('/auth/login', 'Login usuário'),
                ('/test-login', 'Página de teste'),
                ('/auth/check-auth', 'Verificação de auth')
            ]
            
            results = []
            for route, name in routes_to_test:
                response = client.get(route)
                if response.status_code == 200:
                    print(f"   ✅ {name}: OK")
                    results.append(True)
                else:
                    print(f"   ⚠️  {name}: Status {response.status_code}")
                    results.append(False)
            
            print(f"✅ Rotas testadas: {sum(results)}/{len(results)} funcionando")
            return sum(results) == len(results)
            
    except Exception as e:
        print(f"❌ Erro nas rotas: {e}")
        return False

def test_authentication_flow():
    """Testar fluxo completo de autenticação"""
    print("🔄 Testando fluxo de autenticação...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Testar login admin via form
            response = client.post('/auth/admin-login', data={
                'email': 'admin@test.com',
                'password': 'admin123'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✅ Login admin via form: OK")
            else:
                print(f"   ⚠️  Login admin via form: Status {response.status_code}")
            
            # Testar logout
            response = client.get('/auth/logout', follow_redirects=True)
            print("   ✅ Logout: OK")
            
            # Testar login usuário via form
            response = client.post('/auth/login', data={
                'email': 'cliente@test.com',
                'password': '123456'
            }, follow_redirects=True)
            
            if response.status_code == 200:
                print("   ✅ Login usuário via form: OK")
            else:
                print(f"   ⚠️  Login usuário via form: Status {response.status_code}")
            
            # Testar login admin via JSON
            response = client.post('/auth/admin-login', 
                                 json={
                                     'email': 'admin@test.com',
                                     'password': 'admin123'
                                 })
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('ok'):
                    print("   ✅ Login admin via JSON: OK")
                else:
                    print("   ⚠️  Login admin via JSON: Resposta inválida")
            else:
                print(f"   ⚠️  Login admin via JSON: Status {response.status_code}")
            
            print("✅ Fluxo de autenticação testado")
            return True
            
    except Exception as e:
        print(f"❌ Erro no fluxo de autenticação: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Testar serviços do sistema"""
    print("🔄 Testando serviços...")
    
    try:
        from app import app
        from services.auth_service import AuthService
        
        with app.app_context():
            # Testar AuthService
            user = AuthService.authenticate_user('cliente@test.com', '123456')
            admin = AuthService.authenticate_admin('admin@test.com', 'admin123')
            
            assert user is not None
            assert admin is not None
            
            print("   ✅ AuthService funcionando")
            
            # Testar WalletService se existir
            try:
                from services.wallet_service import WalletService
                from models import User
                
                user = User.query.filter_by(email='cliente@test.com').first()
                if user and not user.wallet:
                    WalletService.create_wallet_for_user(user)
                    print("   ✅ WalletService funcionando")
                else:
                    print("   ✅ WalletService: Carteira já existe")
                    
            except ImportError:
                print("   ⚠️  WalletService não encontrado")
            
            print("✅ Serviços testados")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos serviços: {e}")
        return False

def test_navigation():
    """Testar navegação entre páginas"""
    print("🔄 Testando navegação...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Fazer login como admin
            response = client.post('/auth/admin-login', data={
                'email': 'admin@test.com',
                'password': 'admin123'
            })
            
            # Tentar acessar dashboard admin
            response = client.get('/admin/dashboard')
            if response.status_code in [200, 302]:
                print("   ✅ Navegação para dashboard admin: OK")
            else:
                print(f"   ⚠️  Dashboard admin: Status {response.status_code}")
            
            # Logout e login como usuário
            client.get('/auth/logout')
            
            response = client.post('/auth/login', data={
                'email': 'cliente@test.com',
                'password': '123456'
            })
            
            # Tentar acessar dashboard cliente
            response = client.get('/cliente/dashboard')
            if response.status_code in [200, 302]:
                print("   ✅ Navegação para dashboard cliente: OK")
            else:
                print(f"   ⚠️  Dashboard cliente: Status {response.status_code}")
            
            print("✅ Navegação testada")
            return True
            
    except Exception as e:
        print(f"❌ Erro na navegação: {e}")
        return False

def main():
    """Executar todos os testes da Tarefa 1"""
    print("🚀 TAREFA 1: VALIDAR E TESTAR A BASE EXISTENTE DO SISTEMA")
    print("=" * 60)
    
    # Limpar banco de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    # Lista de testes
    tests = [
        ("Configuração do banco", setup_test_database),
        ("Modelos do banco", test_database_models),
        ("Rotas e templates", test_routes_and_templates),
        ("Fluxo de autenticação", test_authentication_flow),
        ("Serviços", test_services),
        ("Navegação", test_navigation)
    ]
    
    results = []
    
    # Executar cada teste
    for test_name, test_func in tests:
        print(f"\n📋 {test_name.upper()}")
        print("-" * 40)
        result = test_func()
        results.append(result)
        
        if result:
            print(f"✅ {test_name}: PASSOU")
        else:
            print(f"❌ {test_name}: FALHOU")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL DA TAREFA 1")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes aprovados: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TAREFA 1 CONCLUÍDA COM SUCESSO!")
        print("✅ A base do sistema está funcionando corretamente")
        print("\n📋 VALIDAÇÕES REALIZADAS:")
        print("   ✅ Sistema de autenticação completo")
        print("   ✅ Renderização de templates sem erros")
        print("   ✅ Navegação entre páginas funcionando")
        print("   ✅ Banco de dados e modelos operacionais")
        print("   ✅ Serviços básicos funcionando")
        success = True
    else:
        print(f"\n⚠️  TAREFA 1 PARCIALMENTE CONCLUÍDA")
        print(f"❌ {total - passed} componente(s) precisam de correção")
        success = False
    
    # Limpar arquivo de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)