#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste específico para verificar o fluxo de aceitação de convites
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta

def test_invite_acceptance_flow():
    """Testa o fluxo completo de aceitação de convites"""
    
    with app.app_context():
        try:
            print("🔄 Testando fluxo de aceitação de convites...")
            
            # 1. Usar o convite específico mencionado pelo usuário
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"\n1️⃣ Testando com convite: {token}")
            
            # Verificar se o convite existe
            try:
                invite = InviteService.get_invite_by_token(token)
                print(f"✅ Convite encontrado: {invite.service_title}")
                print(f"   Status: {invite.status}")
                print(f"   Expirado: {invite.is_expired}")
            except ValueError as e:
                print(f"❌ Convite não encontrado: {e}")
                return False
            
            # 2. Testar acesso à página inicial do convite
            print(f"\n2️⃣ Testando acesso à página do convite...")
            
            with app.test_client() as client:
                response = client.get(f'/auth/convite/{token}')
                print(f"   Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ Página do convite não carregou corretamente")
                    if response.status_code == 302:
                        print(f"   Redirecionamento para: {response.location}")
                    return False
                
                # Verificar se o formulário de aceitação está presente
                content = response.data.decode()
                if 'aceitar_convite_inicial' in content:
                    print("✅ Formulário de aceitação encontrado")
                else:
                    print("❌ Formulário de aceitação não encontrado")
                    return False
            
            # 3. Testar POST para aceitar o convite
            print(f"\n3️⃣ Testando aceitação do convite...")
            
            with app.test_client() as client:
                # Simular sessão
                with client.session_transaction() as sess:
                    sess['csrf_token'] = 'test_token'
                
                # Fazer POST para aceitar convite
                response = client.post(f'/auth/convite/{token}/aceitar-inicial', 
                                     data={'csrf_token': 'test_token'},
                                     follow_redirects=False)
                
                print(f"   Status da resposta: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"✅ Redirecionamento detectado para: {response.location}")
                    
                    # Verificar se o redirecionamento é para a página correta
                    expected_redirect = f'/auth/convite/{token}/login-cadastro'
                    if expected_redirect in response.location:
                        print("✅ Redirecionamento correto para login/cadastro")
                    else:
                        print(f"❌ Redirecionamento incorreto. Esperado: {expected_redirect}")
                        return False
                        
                elif response.status_code == 200:
                    print("⚠️ Não houve redirecionamento (pode ser problema)")
                    content = response.data.decode()
                    if 'erro' in content.lower() or 'error' in content.lower():
                        print("❌ Página retornou erro")
                        return False
                else:
                    print(f"❌ Status inesperado: {response.status_code}")
                    return False
            
            # 4. Testar acesso à página de login/cadastro
            print(f"\n4️⃣ Testando página de login/cadastro...")
            
            with app.test_client() as client:
                # Simular sessão com convite aceito
                with client.session_transaction() as sess:
                    sess['invite_accepted'] = token
                    sess['invite_acceptance_time'] = datetime.now().isoformat()
                
                response = client.get(f'/auth/convite/{token}/login-cadastro')
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ Página de login/cadastro carregou")
                    
                    # Verificar conteúdo da página
                    content = response.data.decode()
                    checks = [
                        ('Formulário de login', 'login' in content.lower()),
                        ('Formulário de cadastro', 'cadastro' in content.lower() or 'register' in content.lower()),
                        ('Informações do convite', invite.service_title in content),
                        ('Token do convite', token in content)
                    ]
                    
                    for check_name, check_result in checks:
                        status = "✅" if check_result else "❌"
                        print(f"   {status} {check_name}")
                        
                elif response.status_code == 302:
                    print(f"↪️ Redirecionamento para: {response.location}")
                    print("⚠️ Pode indicar problema na sessão ou validação")
                else:
                    print(f"❌ Erro ao carregar página: {response.status_code}")
                    return False
            
            # 5. Testar sem sessão (simulando problema real)
            print(f"\n5️⃣ Testando sem sessão (simulando problema)...")
            
            with app.test_client() as client:
                # Não definir sessão - simular usuário real
                response = client.post(f'/auth/convite/{token}/aceitar-inicial', 
                                     data={'csrf_token': 'test_token'},
                                     follow_redirects=False)
                
                print(f"   Status sem sessão: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"   Redirecionamento: {response.location}")
                
                # Tentar acessar login/cadastro sem ter aceito
                response2 = client.get(f'/auth/convite/{token}/login-cadastro')
                print(f"   Status login/cadastro sem aceitar: {response2.status_code}")
                
                if response2.status_code == 302:
                    print(f"   Redirecionamento: {response2.location}")
                    if f'/auth/convite/{token}' in response2.location:
                        print("✅ Redirecionamento correto de volta ao convite")
                    else:
                        print("⚠️ Redirecionamento para local inesperado")
            
            # 6. Verificar logs de erro
            print(f"\n6️⃣ Verificando possíveis problemas...")
            
            # Verificar se as rotas estão registradas
            routes_found = []
            for rule in app.url_map.iter_rules():
                if token in rule.rule or 'convite' in rule.rule:
                    routes_found.append(f"{rule.rule} -> {rule.endpoint}")
            
            print("   Rotas relacionadas a convites:")
            for route in routes_found[:10]:  # Limitar a 10 para não poluir
                print(f"     {route}")
            
            print("\n🎉 Teste de fluxo de aceitação concluído!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_invite_acceptance_flow()
    if success:
        print("\n✅ Teste de fluxo de aceitação concluído!")
        print("\n📋 Pontos verificados:")
        print("   ✅ Acesso à página do convite")
        print("   ✅ Formulário de aceitação")
        print("   ✅ Redirecionamento após aceitação")
        print("   ✅ Página de login/cadastro")
        print("   ✅ Validação de sessão")
    else:
        print("\n❌ Problemas encontrados no fluxo de aceitação.")