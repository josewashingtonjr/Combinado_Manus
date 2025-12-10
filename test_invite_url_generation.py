#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste específico para problemas de geração de URL nos convites
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from flask import url_for
import requests

def test_url_generation_issues():
    """Testa problemas específicos na geração de URLs dos convites"""
    
    with app.app_context():
        try:
            print("🔍 Investigando problemas de geração de URL...")
            
            # 1. Verificar configuração do servidor
            print("\n1️⃣ Verificando configuração do servidor...")
            
            print(f"   SERVER_NAME: {app.config.get('SERVER_NAME', 'Não definido')}")
            print(f"   APPLICATION_ROOT: {app.config.get('APPLICATION_ROOT', 'Não definido')}")
            print(f"   PREFERRED_URL_SCHEME: {app.config.get('PREFERRED_URL_SCHEME', 'http')}")
            
            # 2. Criar convite de teste
            print("\n2️⃣ Criando convite para teste...")
            
            client = User.query.filter_by(roles='cliente').first()
            if not client:
                print("❌ Nenhum cliente encontrado")
                return False
            
            # Garantir carteira e saldo
            try:
                WalletService.get_wallet_balance(client.id)
            except ValueError:
                WalletService.create_wallet_for_user(client)
                WalletService.credit_wallet(client.id, 300.0, 'Saldo para teste URL')
            
            delivery_date = datetime.now() + timedelta(days=2)
            
            result = InviteService.create_invite(
                client_id=client.id,
                invited_phone='(11) 97777-6666',
                service_title='Teste URL Generation',
                service_description='Teste para verificar geração de URLs',
                original_value=80.0,
                delivery_date=delivery_date,
                service_category='teste'
            )
            
            invite = InviteService.get_invite_by_token(result['token'])
            print(f"✅ Convite criado: {invite.token}")
            
            # 3. Testar diferentes contextos de geração de URL
            print("\n3️⃣ Testando geração de URLs em diferentes contextos...")
            
            # Contexto normal (sem request)
            try:
                url_normal = invite.invite_link
                print(f"   URL normal: {url_normal}")
            except Exception as e:
                print(f"   ❌ Erro URL normal: {e}")
            
            # Contexto de request de teste
            try:
                with app.test_request_context('http://localhost:5001'):
                    url_test_context = url_for('auth.convite_acesso', token=invite.token, _external=True)
                    print(f"   URL test context: {url_test_context}")
            except Exception as e:
                print(f"   ❌ Erro test context: {e}")
            
            # Contexto com diferentes hosts
            try:
                with app.test_request_context('http://127.0.0.1:5001'):
                    url_localhost = url_for('auth.convite_acesso', token=invite.token, _external=True)
                    print(f"   URL localhost: {url_localhost}")
            except Exception as e:
                print(f"   ❌ Erro localhost: {e}")
            
            # 4. Testar se o servidor está respondendo
            print("\n4️⃣ Testando conectividade do servidor...")
            
            try:
                # Verificar se o servidor está rodando
                response = requests.get('http://localhost:5001/', timeout=5)
                print(f"   ✅ Servidor respondendo: {response.status_code}")
            except requests.exceptions.ConnectionError:
                print("   ⚠️ Servidor não está rodando na porta 5001")
            except Exception as e:
                print(f"   ❌ Erro de conectividade: {e}")
            
            # 5. Testar acesso direto ao link
            print("\n5️⃣ Testando acesso direto ao link...")
            
            test_urls = [
                f"http://localhost:5001/auth/convite/{invite.token}",
                f"http://127.0.0.1:5001/auth/convite/{invite.token}",
                f"/auth/convite/{invite.token}"
            ]
            
            for test_url in test_urls:
                try:
                    if test_url.startswith('http'):
                        # Teste via requests
                        response = requests.get(test_url, timeout=5)
                        print(f"   {test_url}: {response.status_code}")
                    else:
                        # Teste via test_client
                        with app.test_client() as client_test:
                            response = client_test.get(test_url)
                            print(f"   {test_url}: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ {test_url}: {e}")
            
            # 6. Verificar template de convite
            print("\n6️⃣ Verificando template de convite...")
            
            with app.test_client() as client_test:
                response = client_test.get(f'/auth/convite/{invite.token}')
                
                if response.status_code == 200:
                    content = response.data.decode()
                    
                    # Verificar elementos importantes
                    checks = [
                        ('Título do serviço', invite.service_title in content),
                        ('Token do convite', invite.token in content),
                        ('Botões de ação', 'aceitar' in content.lower()),
                        ('JavaScript', '<script>' in content),
                        ('CSS', 'bootstrap' in content.lower() or 'css' in content.lower())
                    ]
                    
                    for check_name, check_result in checks:
                        status = "✅" if check_result else "❌"
                        print(f"   {status} {check_name}")
                        
                else:
                    print(f"   ❌ Template não carregou: {response.status_code}")
            
            # 7. Verificar problemas de CORS
            print("\n7️⃣ Verificando configuração CORS...")
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            with app.test_client() as client_test:
                response = client_test.get(f'/auth/convite/{invite.token}')
                
                for header in cors_headers:
                    if header in response.headers:
                        print(f"   ✅ {header}: {response.headers[header]}")
                    else:
                        print(f"   ⚠️ {header}: Não definido")
            
            # 8. Limpar dados de teste
            print("\n8️⃣ Limpando dados de teste...")
            
            db.session.delete(invite)
            db.session.commit()
            
            print("✅ Convite de teste removido")
            
            print("\n🎉 Investigação de URLs concluída!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante investigação: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_url_generation_issues()
    if success:
        print("\n✅ Investigação de URLs concluída!")
    else:
        print("\n❌ Problemas encontrados na geração de URLs.")