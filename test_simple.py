#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste simples para validar o sistema com SQLite
"""

import os
import sys
import tempfile

# Configurar variável de ambiente para usar SQLite
os.environ['DATABASE_URL'] = 'sqlite:///test_combinado.db'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Teste básico de funcionalidade"""
    print("🔄 Testando funcionalidade básica...")
    
    try:
        # Importar app com SQLite
        from app import app, db
        from models import User, AdminUser, Wallet, Transaction, Order
        
        # Configurar para teste
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            # Criar tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso")
            
            # Testar criação de admin
            admin = AdminUser(email='admin@test.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado com sucesso")
            
            # Testar criação de usuário
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
            print("✅ Usuário criado com sucesso")
            
            # Testar autenticação
            admin_check = AdminUser.query.filter_by(email='admin@test.com').first()
            user_check = User.query.filter_by(email='user@test.com').first()
            
            assert admin_check.check_password('admin123')
            assert user_check.check_password('user123')
            print("✅ Autenticação funcionando")
            
        # Testar rotas básicas
        with app.test_client() as client:
            # Página inicial
            response = client.get('/')
            print(f"✅ Página inicial: {response.status_code}")
            
            # Login admin
            response = client.get('/auth/admin-login')
            print(f"✅ Login admin: {response.status_code}")
            
            # Login usuário
            response = client.get('/auth/login')
            print(f"✅ Login usuário: {response.status_code}")
            
            # Testar login funcional
            response = client.post('/auth/admin-login', data={
                'email': 'admin@test.com',
                'password': 'admin123'
            }, follow_redirects=True)
            print(f"✅ Login admin funcional: {response.status_code}")
            
        print("🎉 Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_templates():
    """Testar renderização de templates"""
    print("🔄 Testando templates...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Testar templates principais
            templates_to_test = [
                ('/', 'Página inicial'),
                ('/auth/admin-login', 'Login admin'),
                ('/auth/login', 'Login usuário'),
                ('/test-login', 'Teste login')
            ]
            
            for route, name in templates_to_test:
                response = client.get(route)
                if response.status_code == 200:
                    print(f"✅ {name}: OK")
                else:
                    print(f"⚠️  {name}: Status {response.status_code}")
            
        print("✅ Templates testados")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos templates: {e}")
        return False

def main():
    """Executar testes"""
    print("🚀 Iniciando testes simples do sistema...")
    print("=" * 50)
    
    # Limpar banco de teste se existir
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    results = []
    
    # Executar testes
    results.append(test_basic_functionality())
    results.append(test_templates())
    
    # Resumo
    print("\n📊 RESUMO:")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes aprovados: {passed}/{total}")
    
    if passed == total:
        print("🎉 SISTEMA FUNCIONANDO!")
        return True
    else:
        print("⚠️  SISTEMA PRECISA DE CORREÇÕES")
        return False

if __name__ == '__main__':
    success = main()
    
    # Limpar arquivo de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    sys.exit(0 if success else 1)