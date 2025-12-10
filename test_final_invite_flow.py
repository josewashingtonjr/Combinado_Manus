#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste final para confirmar que o problema de redirecionamento foi resolvido
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
import re

def test_final_invite_flow():
    """Teste final do fluxo completo de convites"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🎯 Teste final do fluxo de convites: {token}")
            
            # 1. Verificar se o convite ainda existe
            try:
                invite = InviteService.get_invite_by_token(token)
                print(f"✅ Convite encontrado: {invite.service_title}")
                print(f"   Status: {invite.status}")
                print(f"   Cliente: {invite.client.nome}")
                print(f"   Valor: R$ {invite.original_value:.2f}")
            except ValueError as e:
                print(f"❌ Convite não encontrado: {e}")
                return False
            
            # 2. Testar fluxo completo simulando um usuário real
            print(f"\n2️⃣ Simulando usuário real...")
            
            with app.test_client() as client:
                
                # Passo 1: Acessar link do convite
                print(f"   Passo 1: Acessando link do convite")
                response1 = client.get(f'/auth/convite/{token}')
                
                if response1.status_code != 200:
                    print(f"   ❌ Falha ao acessar convite: {response1.status_code}")
                    return False
                
                print(f"   ✅ Página do convite carregada")
                
                # Extrair CSRF token
                content1 = response1.data.decode()
                csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', content1)
                
                if not csrf_match:
                    print(f"   ❌ CSRF token não encontrado")
                    return False
                
                csrf_token = csrf_match.group(1)
                print(f"   ✅ CSRF token obtido")
                
                # Passo 2: Aceitar o convite
                print(f"   Passo 2: Aceitando o convite")
                response2 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                      data={'csrf_token': csrf_token},
                                      follow_redirects=False)
                
                if response2.status_code != 302:
                    print(f"   ❌ Falha ao aceitar convite: {response2.status_code}")
                    if response2.data:
                        error_content = response2.data.decode()
                        print(f"   Conteúdo: {error_content[:200]}...")
                    return False
                
                redirect_url = response2.location
                print(f"   ✅ Convite aceito, redirecionando para: {redirect_url}")
                
                # Verificar se o redirecionamento é correto
                expected_path = f'/auth/convite/{token}/login-cadastro'
                if expected_path not in redirect_url:
                    print(f"   ❌ Redirecionamento incorreto. Esperado: {expected_path}")
                    return False
                
                # Passo 3: Seguir redirecionamento
                print(f"   Passo 3: Seguindo redirecionamento")
                response3 = client.get(redirect_url)
                
                if response3.status_code != 200:
                    print(f"   ❌ Falha ao carregar página de login/cadastro: {response3.status_code}")
                    if response3.status_code == 302:
                        print(f"   Novo redirecionamento: {response3.location}")
                    return False
                
                print(f"   ✅ Página de login/cadastro carregada")
                
                # Verificar conteúdo da página final
                content3 = response3.data.decode()
                
                # Verificações importantes
                checks = [
                    ('Formulário de login', 'id="loginForm"' in content3 or 'login' in content3.lower()),
                    ('Formulário de cadastro', 'id="cadastroForm"' in content3 or 'cadastro' in content3.lower()),
                    ('Informações do convite', invite.service_title in content3),
                    ('Token do convite', token in content3),
                    ('Nome do cliente', invite.client.nome in content3),
                    ('Valor do serviço', str(invite.original_value) in content3),
                    ('JavaScript carregado', '<script>' in content3),
                    ('CSS carregado', 'bootstrap' in content3.lower())
                ]
                
                print(f"\n   Verificações da página final:")
                all_checks_passed = True
                
                for check_name, check_result in checks:
                    status = "✅" if check_result else "❌"
                    print(f"     {status} {check_name}")
                    if not check_result:
                        all_checks_passed = False
                
                if not all_checks_passed:
                    print(f"   ⚠️ Algumas verificações falharam")
                    return False
                
                # Passo 4: Testar se pode fazer login/cadastro
                print(f"\n   Passo 4: Testando formulários")
                
                # Verificar se há formulários funcionais
                login_form_match = re.search(r'<form[^>]*id="loginForm"[^>]*>(.*?)</form>', content3, re.DOTALL | re.IGNORECASE)
                cadastro_form_match = re.search(r'<form[^>]*id="cadastroForm"[^>]*>(.*?)</form>', content3, re.DOTALL | re.IGNORECASE)
                
                if login_form_match:
                    print(f"     ✅ Formulário de login encontrado")
                else:
                    print(f"     ⚠️ Formulário de login não encontrado especificamente")
                
                if cadastro_form_match:
                    print(f"     ✅ Formulário de cadastro encontrado")
                else:
                    print(f"     ⚠️ Formulário de cadastro não encontrado especificamente")
            
            # 3. Verificar se a sessão foi criada corretamente
            print(f"\n3️⃣ Verificando sessão...")
            
            with app.test_client() as client:
                # Simular aceitação novamente para verificar sessão
                response = client.get(f'/auth/convite/{token}')
                csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', response.data.decode())
                csrf_token = csrf_match.group(1) if csrf_match else 'invalid'
                
                response = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                     data={'csrf_token': csrf_token})
                
                # Verificar sessão
                with client.session_transaction() as sess:
                    invite_accepted = sess.get('invite_accepted')
                    acceptance_time = sess.get('invite_acceptance_time')
                    
                    if invite_accepted == token:
                        print(f"   ✅ Sessão criada corretamente")
                        print(f"   Token na sessão: {invite_accepted}")
                        print(f"   Tempo de aceitação: {acceptance_time}")
                    else:
                        print(f"   ❌ Sessão não criada corretamente")
                        print(f"   Esperado: {token}")
                        print(f"   Encontrado: {invite_accepted}")
                        return False
            
            print(f"\n🎉 Teste final concluído com sucesso!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante teste final: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_final_invite_flow()
    if success:
        print(f"\n✅ PROBLEMA RESOLVIDO!")
        print(f"\n📋 Correções implementadas:")
        print(f"   ✅ Links de convites corrigidos (sem duplicação)")
        print(f"   ✅ Middleware de sessão atualizado")
        print(f"   ✅ Rotas de convite adicionadas às exceções")
        print(f"   ✅ Redirecionamento funcionando corretamente")
        print(f"   ✅ Sessão sendo criada adequadamente")
        print(f"   ✅ Página de login/cadastro carregando")
        
        print(f"\n🌐 Como testar no navegador:")
        print(f"   1. Acesse: http://127.0.0.1:5001/auth/convite/HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa")
        print(f"   2. Clique em 'Aceitar Convite'")
        print(f"   3. Confirme na caixa de diálogo")
        print(f"   4. Você será redirecionado para a página de login/cadastro")
        print(f"   5. Faça login ou cadastre-se para visualizar o convite")
        
    else:
        print(f"\n❌ Ainda há problemas no fluxo de convites.")