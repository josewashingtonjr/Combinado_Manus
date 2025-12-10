#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Simulação exata do comportamento do navegador
"""

from app import app
import re
import time

def test_browser_simulation():
    """Simula exatamente o que acontece no navegador"""
    
    with app.app_context():
        token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
        
        print(f"🌐 Simulação exata do navegador: {token}")
        
        with app.test_client() as client:
            
            # Passo 1: Usuário acessa o link
            print(f"\n1️⃣ Usuário acessa o link...")
            response1 = client.get(f'/auth/convite/{token}')
            
            print(f"   Status: {response1.status_code}")
            if response1.status_code != 200:
                print(f"   ❌ Falha ao carregar página")
                return False
            
            # Passo 2: Página carrega, JavaScript executa
            print(f"\n2️⃣ Página carrega, JavaScript executa...")
            
            html_content = response1.data.decode()
            
            # Verificar se o botão tem onclick
            onclick_match = re.search(r'onclick="([^"]*)"', html_content)
            if onclick_match:
                onclick_code = onclick_match.group(1)
                print(f"   ✅ Onclick encontrado: {onclick_code[:50]}...")
            else:
                print(f"   ❌ Onclick não encontrado")
                return False
            
            # Passo 3: Usuário clica no botão
            print(f"\n3️⃣ Usuário clica no botão 'Aceitar Convite'...")
            
            # Simular o confirm() retornando true (usuário confirma)
            print(f"   Usuário confirma na caixa de diálogo")
            
            # Passo 4: Formulário é enviado
            print(f"\n4️⃣ Formulário é enviado...")
            
            # Extrair CSRF token
            csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', html_content)
            csrf_token = csrf_match.group(1) if csrf_match else 'invalid'
            
            # Simular POST exato do navegador
            response2 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                  data={'csrf_token': csrf_token},
                                  headers={
                                      'Content-Type': 'application/x-www-form-urlencoded',
                                      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                      'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                                      'Accept-Encoding': 'gzip, deflate',
                                      'Referer': f'http://127.0.0.1:5001/auth/convite/{token}',
                                      'Origin': 'http://127.0.0.1:5001',
                                      'Connection': 'keep-alive',
                                      'Upgrade-Insecure-Requests': '1'
                                  },
                                  follow_redirects=False)
            
            print(f"   Status da resposta: {response2.status_code}")
            
            # Passo 5: Verificar resposta do servidor
            if response2.status_code == 302:
                redirect_location = response2.location
                print(f"   ✅ Servidor retorna redirecionamento: {redirect_location}")
                
                # Passo 6: Navegador segue o redirecionamento
                print(f"\n5️⃣ Navegador segue o redirecionamento...")
                
                response3 = client.get(redirect_location,
                                     headers={
                                         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                         'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                                         'Referer': f'http://127.0.0.1:5001/auth/convite/{token}'
                                     })
                
                print(f"   Status da página final: {response3.status_code}")
                
                if response3.status_code == 200:
                    final_content = response3.data.decode()
                    
                    # Verificar se chegou na página correta
                    if 'login' in final_content.lower() and 'cadastro' in final_content.lower():
                        print(f"   ✅ Chegou na página de login/cadastro")
                        
                        # Verificar elementos específicos
                        checks = [
                            ('Formulário de login', 'loginForm' in final_content or 'login' in final_content.lower()),
                            ('Formulário de cadastro', 'cadastroForm' in final_content or 'cadastro' in final_content.lower()),
                            ('Token do convite', token in final_content),
                            ('Título correto', 'Login' in final_content or 'Cadastro' in final_content)
                        ]
                        
                        print(f"\n   Verificações finais:")
                        for check_name, check_result in checks:
                            status = "✅" if check_result else "❌"
                            print(f"     {status} {check_name}")
                        
                        return True
                        
                    else:
                        print(f"   ❌ Não chegou na página correta")
                        print(f"   Conteúdo: {final_content[:200]}...")
                        return False
                        
                elif response3.status_code == 302:
                    print(f"   ⚠️ Novo redirecionamento: {response3.location}")
                    
                    # Pode ser redirecionamento de volta por problema de sessão
                    if f'/auth/convite/{token}' in response3.location:
                        print(f"   ❌ Redirecionamento de volta - problema de sessão")
                    
                    return False
                    
                else:
                    print(f"   ❌ Erro na página final: {response3.status_code}")
                    return False
                    
            elif response2.status_code == 200:
                print(f"   ❌ Não houve redirecionamento")
                
                # Verificar se há erro na página
                error_content = response2.data.decode()
                if 'erro' in error_content.lower():
                    print(f"   Página contém erro")
                
                return False
                
            else:
                print(f"   ❌ Status inesperado: {response2.status_code}")
                return False

if __name__ == "__main__":
    success = test_browser_simulation()
    if success:
        print(f"\n✅ SIMULAÇÃO COMPLETA - FUNCIONANDO!")
        print(f"\n🎯 O problema pode estar em:")
        print(f"   1. Cache do navegador")
        print(f"   2. JavaScript sendo executado diferente")
        print(f"   3. Configurações de segurança do navegador")
        print(f"   4. Extensões do navegador interferindo")
        
        print(f"\n🔧 Soluções para testar:")
        print(f"   1. Abrir em aba anônima/privada")
        print(f"   2. Limpar cache do navegador")
        print(f"   3. Desabilitar extensões")
        print(f"   4. Testar em navegador diferente")
        
    else:
        print(f"\n❌ Ainda há problemas na simulação")