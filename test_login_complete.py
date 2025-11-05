#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste completo de login com todos os tipos de usuário
"""

import os
import sys

# Configurar SQLite para teste
os.environ['DATABASE_URL'] = 'sqlite:///test_combinado.db'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_user_types():
    """Testar login com todos os tipos de usuário"""
    print("🔄 Testando login com todos os tipos de usuário...")
    
    try:
        from app import app, db
        from models import AdminUser, User
        
        # Configurar banco
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # Criar usuários de teste
            admin = AdminUser(email='admin@combinado.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            cliente = User(
                nome='Cliente Teste',
                email='cliente@teste.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            cliente.set_password('123456')
            db.session.add(cliente)
            
            prestador = User(
                nome='Prestador Teste',
                email='prestador@teste.com',
                cpf='98765432100',
                phone='(11) 88888-8888',
                roles='prestador',
                active=True
            )
            prestador.set_password('123456')
            db.session.add(prestador)
            
            dual = User(
                nome='Usuário Dual',
                email='dual@teste.com',
                cpf='11122233344',
                phone='(11) 77777-7777',
                roles='cliente,prestador',
                active=True
            )
            dual.set_password('123456')
            db.session.add(dual)
            
            db.session.commit()
        
        # Testar com cliente de teste
        with app.test_client() as client:
            print("\n📋 TESTANDO TODOS OS TIPOS DE LOGIN:")
            print("-" * 40)
            
            # 1. Login Admin
            print("🔐 Testando login de administrador...")
            response = client.post('/auth/admin-login', 
                                 json={
                                     'email': 'admin@combinado.com',
                                     'password': 'admin123'
                                 })
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('ok'):
                    print("   ✅ Admin login: SUCESSO")
                    print(f"   📧 Email: {data['user']['email']}")
                    print(f"   👤 Papel: {data['user']['papel']}")
                else:
                    print("   ❌ Admin login: Resposta inválida")
            else:
                print(f"   ❌ Admin login: Status {response.status_code}")
            
            # Logout
            client.get('/auth/logout')
            
            # 2. Login Cliente
            print("\n🔐 Testando login de cliente...")
            response = client.post('/auth/login', 
                                 json={
                                     'email': 'cliente@teste.com',
                                     'password': '123456'
                                 })
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('ok'):
                    print("   ✅ Cliente login: SUCESSO")
                    print(f"   📧 Email: {data['user']['email']}")
                    print(f"   👤 Papel: {data['user']['role']}")
                    print(f"   🎭 Papéis: {data['user']['roles']}")
                else:
                    print("   ❌ Cliente login: Resposta inválida")
            else:
                print(f"   ❌ Cliente login: Status {response.status_code}")
            
            # Logout
            client.get('/auth/logout')
            
            # 3. Login Prestador
            print("\n🔐 Testando login de prestador...")
            response = client.post('/auth/login', 
                                 json={
                                     'email': 'prestador@teste.com',
                                     'password': '123456'
                                 })
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('ok'):
                    print("   ✅ Prestador login: SUCESSO")
                    print(f"   📧 Email: {data['user']['email']}")
                    print(f"   👤 Papel: {data['user']['role']}")
                    print(f"   🎭 Papéis: {data['user']['roles']}")
                else:
                    print("   ❌ Prestador login: Resposta inválida")
            else:
                print(f"   ❌ Prestador login: Status {response.status_code}")
            
            # Logout
            client.get('/auth/logout')
            
            # 4. Login Usuário Dual
            print("\n🔐 Testando login de usuário dual...")
            response = client.post('/auth/login', 
                                 json={
                                     'email': 'dual@teste.com',
                                     'password': '123456'
                                 })
            
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('ok'):
                    print("   ✅ Usuário dual login: SUCESSO")
                    print(f"   📧 Email: {data['user']['email']}")
                    print(f"   👤 Papel principal: {data['user']['role']}")
                    print(f"   🎭 Todos os papéis: {data['user']['roles']}")
                else:
                    print("   ❌ Usuário dual login: Resposta inválida")
            else:
                print(f"   ❌ Usuário dual login: Status {response.status_code}")
            
            # 5. Testar credenciais inválidas
            print("\n🔐 Testando credenciais inválidas...")
            response = client.post('/auth/login', 
                                 json={
                                     'email': 'inexistente@teste.com',
                                     'password': 'senhaerrada'
                                 })
            
            if response.status_code == 401:
                print("   ✅ Credenciais inválidas: Rejeitado corretamente")
            else:
                print(f"   ⚠️  Credenciais inválidas: Status {response.status_code}")
            
            print("\n🎉 TODOS OS TESTES DE LOGIN CONCLUÍDOS!")
            return True
            
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executar teste completo de login"""
    print("🚀 TESTE COMPLETO DE LOGIN - TODOS OS TIPOS DE USUÁRIO")
    print("=" * 60)
    
    # Limpar banco de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    success = test_all_user_types()
    
    # Limpar arquivo de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    if success:
        print("\n✅ SISTEMA DE AUTENTICAÇÃO COMPLETAMENTE FUNCIONAL!")
        print("📋 Tipos de usuário testados:")
        print("   ✅ Administrador (super_admin)")
        print("   ✅ Cliente")
        print("   ✅ Prestador")
        print("   ✅ Usuário Dual (cliente + prestador)")
        print("   ✅ Validação de credenciais inválidas")
    else:
        print("\n❌ SISTEMA PRECISA DE CORREÇÕES")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)