#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do servidor em execução
"""

import os
import sys
import time
import subprocess
import requests
import threading
from multiprocessing import Process

# Configurar SQLite para teste
os.environ['DATABASE_URL'] = 'sqlite:///test_combinado.db'

def start_server():
    """Iniciar servidor Flask"""
    try:
        from app import app, db
        
        with app.app_context():
            db.create_all()
            
            # Criar usuários de teste
            from models import AdminUser, User
            
            # Admin
            admin = AdminUser.query.filter_by(email='admin@test.com').first()
            if not admin:
                admin = AdminUser(email='admin@test.com', papel='super_admin')
                admin.set_password('admin123')
                db.session.add(admin)
            
            # Usuário cliente
            user = User.query.filter_by(email='cliente@test.com').first()
            if not user:
                user = User(
                    nome='Cliente Teste',
                    email='cliente@test.com',
                    cpf='12345678901',
                    phone='(11) 99999-9999',
                    roles='cliente',
                    active=True
                )
                user.set_password('123456')
                db.session.add(user)
            
            # Usuário prestador
            prestador = User.query.filter_by(email='prestador@test.com').first()
            if not prestador:
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
            
            db.session.commit()
        
        # Iniciar servidor
        app.run(debug=False, host='127.0.0.1', port=5001, threaded=True)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

def test_server_endpoints():
    """Testar endpoints do servidor"""
    print("🔄 Testando endpoints do servidor...")
    
    base_url = "http://127.0.0.1:5001"
    
    # Aguardar servidor iniciar
    time.sleep(3)
    
    endpoints_to_test = [
        ('/', 'Página inicial'),
        ('/auth/admin-login', 'Login admin'),
        ('/auth/login', 'Login usuário'),
        ('/test-login', 'Página de teste'),
        ('/auth/check-auth', 'Verificação de auth')
    ]
    
    results = []
    
    for endpoint, name in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK ({response.status_code})")
                results.append(True)
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                results.append(False)
        except Exception as e:
            print(f"❌ {name}: Erro - {e}")
            results.append(False)
    
    return results

def test_authentication():
    """Testar autenticação via API"""
    print("🔄 Testando autenticação...")
    
    base_url = "http://127.0.0.1:5001"
    
    # Testar login admin
    try:
        response = requests.post(f"{base_url}/auth/admin-login", 
                               json={
                                   'email': 'admin@test.com',
                                   'password': 'admin123'
                               },
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Login admin via API: OK")
                return True
            else:
                print(f"❌ Login admin falhou: {data.get('error')}")
                return False
        else:
            print(f"❌ Login admin: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no login admin: {e}")
        return False

def main():
    """Executar teste completo do servidor"""
    print("🚀 Iniciando teste do servidor...")
    print("=" * 50)
    
    # Limpar banco de teste
    if os.path.exists('test_combinado.db'):
        os.remove('test_combinado.db')
    
    # Iniciar servidor em processo separado
    server_process = Process(target=start_server)
    server_process.start()
    
    try:
        # Aguardar servidor inicializar
        print("⏳ Aguardando servidor inicializar...")
        time.sleep(5)
        
        # Testar endpoints
        endpoint_results = test_server_endpoints()
        
        # Testar autenticação
        auth_result = test_authentication()
        
        # Resumo
        print("\n📊 RESUMO DOS TESTES:")
        print("=" * 30)
        
        endpoint_passed = sum(endpoint_results)
        endpoint_total = len(endpoint_results)
        
        print(f"✅ Endpoints funcionando: {endpoint_passed}/{endpoint_total}")
        print(f"✅ Autenticação: {'OK' if auth_result else 'FALHOU'}")
        
        total_passed = endpoint_passed + (1 if auth_result else 0)
        total_tests = endpoint_total + 1
        
        if total_passed == total_tests:
            print("🎉 SERVIDOR FUNCIONANDO PERFEITAMENTE!")
            success = True
        else:
            print("⚠️  SERVIDOR PRECISA DE AJUSTES")
            success = False
            
    finally:
        # Parar servidor
        server_process.terminate()
        server_process.join(timeout=5)
        
        # Limpar arquivo de teste
        if os.path.exists('test_combinado.db'):
            os.remove('test_combinado.db')
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)