#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste específico para identificar problemas de redirecionamento
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from flask import session
import re

def test_redirect_issue():
    """Testa especificamente problemas de redirecionamento"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🔍 Investigando problema de redirecionamento para: {token}")
            
            # 1. Verificar se o convite existe e está válido
            try:
                invite = InviteService.get_invite_by_token(token)
                print(f"✅ Convite válido: {invite.service_title}")
            except ValueError as e:
                print(f"❌ Convite inválido: {e}")
                return False
            
            # 2. Testar diferentes cenários de redirecionamento
            print(f"\n2️⃣ Testando cenários de redirecionamento...")
            
            with app.test_client() as client:
                
                # Cenário 1: Fluxo normal completo
                print(f"\n   Cenário 1: Fluxo normal")
                
                # GET inicial
                response1 = client.get(f'/auth/convite/{token}')
                print(f"   GET convite: {response1.status_code}")
                
                if response1.status_code != 200:
                    print(f"   ❌ Falha no GET inicial")
                    return False
                
                # Extrair CSRF
                content = response1.data.decode()
                csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', content)
                csrf_token = csrf_match.group(1) if csrf_match else 'invalid'
                
                # POST aceitar
                response2 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                      data={'csrf_token': csrf_token},
                                      follow_redirects=False)
                
                print(f"   POST aceitar: {response2.status_code}")
                print(f"   Location: {response2.location if response2.status_code == 302 else 'N/A'}")
                
                # Verificar sessão após POST
                with client.session_transaction() as sess:
                    invite_accepted = sess.get('invite_accepted')
                    acceptance_time = sess.get('invite_acceptance_time')
                    print(f"   Sessão - invite_accepted: {invite_accepted}")
                    print(f"   Sessão - acceptance_time: {acceptance_time}")
                
                # Cenário 2: Testar com follow_redirects=True
                print(f"\n   Cenário 2: Com follow_redirects=True")
                
                response3 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                      data={'csrf_token': csrf_token},
                                      follow_redirects=True)
                
                print(f"   Status final: {response3.status_code}")
                print(f"   URL final: {response3.request.url if hasattr(response3, 'request') else 'N/A'}")
                
                # Verificar conteúdo da página final
                if response3.status_code == 200:
                    final_content = response3.data.decode()
                    
                    # Verificar se chegou na página correta
                    if 'login' in final_content.lower() and 'cadastro' in final_content.lower():
                        print(f"   ✅ Chegou na página de login/cadastro")
                    elif 'aceitar convite' in final_content.lower():
                        print(f"   ⚠️ Ainda na página do convite - possível loop")
                    else:
                        print(f"   ❓ Página desconhecida")
                
                # Cenário 3: Testar acesso direto à página de login/cadastro
                print(f"\n   Cenário 3: Acesso direto ao login/cadastro")
                
                # Limpar sessão primeiro
                with client.session_transaction() as sess:
                    sess.clear()
                
                response4 = client.get(f'/auth/convite/{token}/login-cadastro')
                print(f"   GET login/cadastro sem sessão: {response4.status_code}")
                
                if response4.status_code == 302:
                    print(f"   Redirecionamento: {response4.location}")
                    
                    # Deve redirecionar de volta ao convite
                    if f'/auth/convite/{token}' in response4.location:
                        print(f"   ✅ Redirecionamento correto (sem sessão)")
                    else:
                        print(f"   ❌ Redirecionamento incorreto")
                
                # Cenário 4: Testar com sessão válida
                print(f"\n   Cenário 4: Com sessão válida")
                
                with client.session_transaction() as sess:
                    sess['invite_accepted'] = token
                    from datetime import datetime
                    sess['invite_acceptance_time'] = datetime.now().isoformat()
                
                response5 = client.get(f'/auth/convite/{token}/login-cadastro')
                print(f"   GET login/cadastro com sessão: {response5.status_code}")
                
                if response5.status_code == 200:
                    print(f"   ✅ Página carregada com sessão válida")
                elif response5.status_code == 302:
                    print(f"   ⚠️ Redirecionamento inesperado: {response5.location}")
                
                # Cenário 5: Testar expiração de sessão
                print(f"\n   Cenário 5: Sessão expirada")
                
                with client.session_transaction() as sess:
                    sess['invite_accepted'] = token
                    from datetime import datetime, timedelta
                    expired_time = datetime.now() - timedelta(minutes=35)
                    sess['invite_acceptance_time'] = expired_time.isoformat()
                
                response6 = client.get(f'/auth/convite/{token}/login-cadastro')
                print(f"   GET com sessão expirada: {response6.status_code}")
                
                if response6.status_code == 302:
                    print(f"   Redirecionamento: {response6.location}")
                    if f'/auth/convite/{token}' in response6.location:
                        print(f"   ✅ Redirecionamento correto (sessão expirada)")
            
            # 3. Verificar configurações do Flask que podem afetar redirecionamento
            print(f"\n3️⃣ Verificando configurações do Flask...")
            
            config_checks = [
                ('SECRET_KEY', app.config.get('SECRET_KEY', 'Não definido')),
                ('SESSION_COOKIE_SECURE', app.config.get('SESSION_COOKIE_SECURE', False)),
                ('SESSION_COOKIE_HTTPONLY', app.config.get('SESSION_COOKIE_HTTPONLY', True)),
                ('PERMANENT_SESSION_LIFETIME', app.config.get('PERMANENT_SESSION_LIFETIME', 'Padrão')),
                ('WTF_CSRF_ENABLED', app.config.get('WTF_CSRF_ENABLED', True)),
                ('WTF_CSRF_TIME_LIMIT', app.config.get('WTF_CSRF_TIME_LIMIT', 3600))
            ]
            
            for config_name, config_value in config_checks:
                print(f"   {config_name}: {config_value}")
            
            # 4. Verificar se há middlewares ou hooks que podem interferir
            print(f"\n4️⃣ Verificando middlewares...")
            
            # Verificar before_request handlers
            before_request_funcs = app.before_request_funcs.get(None, [])
            print(f"   Before request handlers: {len(before_request_funcs)}")
            
            for func in before_request_funcs:
                print(f"     - {func.__name__ if hasattr(func, '__name__') else str(func)}")
            
            # Verificar after_request handlers
            after_request_funcs = app.after_request_funcs.get(None, [])
            print(f"   After request handlers: {len(after_request_funcs)}")
            
            for func in after_request_funcs:
                print(f"     - {func.__name__ if hasattr(func, '__name__') else str(func)}")
            
            print(f"\n🎉 Investigação de redirecionamento concluída!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante investigação: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_redirect_issue()
    if success:
        print("\n✅ Investigação concluída!")
        print("\n📋 Pontos verificados:")
        print("   ✅ Fluxo normal de redirecionamento")
        print("   ✅ Comportamento com follow_redirects")
        print("   ✅ Validação de sessão")
        print("   ✅ Expiração de sessão")
        print("   ✅ Configurações do Flask")
        print("   ✅ Middlewares")
    else:
        print("\n❌ Problemas encontrados na investigação.")