#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simulando um navegador real para verificar o problema de redirecionamento
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
import re

def test_real_browser_flow():
    """Simula um navegador real acessando o convite"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🌐 Simulando navegador real para convite: {token}")
            
            # 1. Primeira requisição - GET da página do convite
            print(f"\n1️⃣ GET /auth/convite/{token}")
            
            with app.test_client() as client:
                # Primeira requisição para obter a página e o CSRF token
                response1 = client.get(f'/auth/convite/{token}')
                
                print(f"   Status: {response1.status_code}")
                
                if response1.status_code != 200:
                    print(f"❌ Falha ao carregar página inicial")
                    return False
                
                # Extrair CSRF token do HTML
                content = response1.data.decode()
                csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', content)
                
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"✅ CSRF token extraído: {csrf_token[:20]}...")
                else:
                    print(f"❌ CSRF token não encontrado")
                    return False
                
                # 2. Segunda requisição - POST para aceitar o convite
                print(f"\n2️⃣ POST /auth/convite/{token}/aceitar-inicial")
                
                response2 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                      data={'csrf_token': csrf_token},
                                      follow_redirects=False)
                
                print(f"   Status: {response2.status_code}")
                
                if response2.status_code == 302:
                    redirect_location = response2.location
                    print(f"✅ Redirecionamento para: {redirect_location}")
                    
                    # Verificar se é o redirecionamento esperado
                    expected_path = f'/auth/convite/{token}/login-cadastro'
                    if expected_path in redirect_location:
                        print(f"✅ Redirecionamento correto")
                    else:
                        print(f"❌ Redirecionamento incorreto. Esperado: {expected_path}")
                        return False
                    
                    # 3. Terceira requisição - Seguir o redirecionamento
                    print(f"\n3️⃣ GET {redirect_location}")
                    
                    response3 = client.get(redirect_location)
                    print(f"   Status: {response3.status_code}")
                    
                    if response3.status_code == 200:
                        print(f"✅ Página de login/cadastro carregada")
                        
                        # Verificar conteúdo da página final
                        final_content = response3.data.decode()
                        
                        checks = [
                            ('Formulário de login', 'login' in final_content.lower()),
                            ('Formulário de cadastro', 'cadastro' in final_content.lower() or 'register' in final_content.lower()),
                            ('Token do convite', token in final_content),
                            ('Título da página', 'login' in final_content.lower() or 'cadastro' in final_content.lower())
                        ]
                        
                        for check_name, check_result in checks:
                            status = "✅" if check_result else "❌"
                            print(f"   {status} {check_name}")
                        
                        return True
                        
                    elif response3.status_code == 302:
                        print(f"↪️ Novo redirecionamento para: {response3.location}")
                        
                        # Verificar se é redirecionamento de volta (problema de sessão)
                        if f'/auth/convite/{token}' in response3.location:
                            print(f"⚠️ Redirecionamento de volta ao convite - problema de sessão")
                            
                            # Verificar mensagens flash
                            with client.session_transaction() as sess:
                                flashes = sess.get('_flashes', [])
                                if flashes:
                                    print(f"   Mensagens flash: {flashes}")
                        
                        return False
                        
                    else:
                        print(f"❌ Erro na página final: {response3.status_code}")
                        return False
                
                elif response2.status_code == 200:
                    print(f"⚠️ Não houve redirecionamento - possível erro")
                    
                    # Verificar se há mensagem de erro na página
                    error_content = response2.data.decode()
                    if 'erro' in error_content.lower() or 'error' in error_content.lower():
                        print(f"❌ Página contém erro")
                        
                        # Procurar por mensagens específicas
                        error_patterns = [
                            r'class="alert[^"]*alert-danger[^"]*"[^>]*>([^<]+)',
                            r'class="alert[^"]*alert-error[^"]*"[^>]*>([^<]+)',
                            r'flash[^>]*error[^>]*>([^<]+)'
                        ]
                        
                        for pattern in error_patterns:
                            matches = re.findall(pattern, error_content, re.IGNORECASE)
                            for match in matches:
                                print(f"   Erro encontrado: {match.strip()}")
                    
                    return False
                
                else:
                    print(f"❌ Status inesperado: {response2.status_code}")
                    
                    # Mostrar conteúdo da resposta para debug
                    if response2.data:
                        content_preview = response2.data.decode()[:500]
                        print(f"   Conteúdo: {content_preview}...")
                    
                    return False
            
        except Exception as e:
            print(f"\n❌ Erro durante simulação: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_real_browser_flow()
    if success:
        print("\n✅ Fluxo do navegador funcionando corretamente!")
        print("\n📋 Fluxo testado:")
        print("   1. GET página do convite")
        print("   2. Extrair CSRF token")
        print("   3. POST aceitar convite")
        print("   4. Seguir redirecionamento")
        print("   5. Carregar página de login/cadastro")
    else:
        print("\n❌ Problema encontrado no fluxo do navegador.")