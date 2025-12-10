#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Debug específico para comportamento do navegador vs testes
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
import re

def debug_browser_behavior():
    """Debug do comportamento específico do navegador"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🔍 Debug do comportamento do navegador: {token}")
            
            # 1. Verificar se o convite existe
            try:
                invite = InviteService.get_invite_by_token(token)
                print(f"✅ Convite válido: {invite.service_title}")
            except ValueError as e:
                print(f"❌ Convite inválido: {e}")
                return False
            
            # 2. Capturar HTML exato que o navegador recebe
            print(f"\n2️⃣ Capturando HTML exato...")
            
            with app.test_client() as client:
                response = client.get(f'/auth/convite/{token}')
                
                if response.status_code != 200:
                    print(f"❌ Erro ao carregar página: {response.status_code}")
                    return False
                
                html_content = response.data.decode()
                
                # Salvar HTML completo
                with open('debug_browser_html.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ HTML salvo em debug_browser_html.html")
                
                # 3. Analisar formulário específico
                print(f"\n3️⃣ Analisando formulário de aceitação...")
                
                # Procurar pelo formulário exato
                form_pattern = r'<form[^>]*action="[^"]*aceitar-inicial"[^>]*>(.*?)</form>'
                form_match = re.search(form_pattern, html_content, re.DOTALL | re.IGNORECASE)
                
                if form_match:
                    form_html = form_match.group(0)
                    print(f"✅ Formulário encontrado:")
                    
                    # Extrair detalhes do formulário
                    action_match = re.search(r'action="([^"]*)"', form_html, re.IGNORECASE)
                    method_match = re.search(r'method="([^"]*)"', form_html, re.IGNORECASE)
                    csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', form_html)
                    
                    print(f"   Action: {action_match.group(1) if action_match else 'N/A'}")
                    print(f"   Method: {method_match.group(1) if method_match else 'N/A'}")
                    print(f"   CSRF Token: {csrf_match.group(1)[:20] + '...' if csrf_match else 'N/A'}")
                    
                    # Verificar botão de submit
                    button_pattern = r'<button[^>]*type="submit"[^>]*>(.*?)</button>'
                    button_match = re.search(button_pattern, form_html, re.DOTALL | re.IGNORECASE)
                    
                    if button_match:
                        print(f"   ✅ Botão de submit encontrado")
                        button_html = button_match.group(0)
                        
                        # Verificar se há onclick ou outros eventos
                        if 'onclick' in button_html.lower():
                            onclick_match = re.search(r'onclick="([^"]*)"', button_html, re.IGNORECASE)
                            print(f"   Onclick: {onclick_match.group(1) if onclick_match else 'N/A'}")
                        
                        # Verificar classes CSS
                        class_match = re.search(r'class="([^"]*)"', button_html, re.IGNORECASE)
                        if class_match:
                            print(f"   Classes: {class_match.group(1)}")
                    else:
                        print(f"   ❌ Botão de submit não encontrado")
                        return False
                        
                else:
                    print(f"❌ Formulário de aceitação não encontrado")
                    return False
                
                # 4. Verificar JavaScript que pode interferir
                print(f"\n4️⃣ Verificando JavaScript...")
                
                # Procurar por event listeners que podem interferir
                js_patterns = [
                    (r'addEventListener\s*\(\s*[\'"]click[\'"]', 'Event listener de click'),
                    (r'addEventListener\s*\(\s*[\'"]submit[\'"]', 'Event listener de submit'),
                    (r'\.preventDefault\s*\(\s*\)', 'preventDefault calls'),
                    (r'return\s+false', 'return false statements'),
                    (r'handleAcceptClick', 'handleAcceptClick function'),
                    (r'confirm\s*\(', 'confirm dialogs')
                ]
                
                for pattern, description in js_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        print(f"   ⚠️ {description}: {len(matches)} ocorrências")
                    else:
                        print(f"   ✅ {description}: Não encontrado")
                
                # 5. Testar POST direto sem JavaScript
                print(f"\n5️⃣ Testando POST direto (sem JavaScript)...")
                
                csrf_token = csrf_match.group(1) if csrf_match else 'invalid'
                
                # Simular POST como se fosse enviado diretamente pelo navegador
                post_response = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                          data={'csrf_token': csrf_token},
                                          headers={
                                              'Content-Type': 'application/x-www-form-urlencoded',
                                              'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                                          },
                                          follow_redirects=False)
                
                print(f"   Status: {post_response.status_code}")
                
                if post_response.status_code == 302:
                    print(f"   ✅ Redirecionamento: {post_response.location}")
                    
                    # Testar se o redirecionamento funciona
                    redirect_response = client.get(post_response.location)
                    print(f"   Status do redirect: {redirect_response.status_code}")
                    
                    if redirect_response.status_code == 200:
                        print(f"   ✅ Página de destino carregada")
                    else:
                        print(f"   ❌ Erro na página de destino")
                        
                elif post_response.status_code == 200:
                    print(f"   ⚠️ Não houve redirecionamento - verificando conteúdo...")
                    
                    post_content = post_response.data.decode()
                    if 'erro' in post_content.lower() or 'error' in post_content.lower():
                        print(f"   ❌ Página contém erro")
                        
                        # Procurar mensagens de erro específicas
                        error_patterns = [
                            r'class="alert[^"]*alert-danger[^"]*"[^>]*>([^<]+)',
                            r'flash[^>]*>([^<]+)',
                            r'error[^>]*>([^<]+)'
                        ]
                        
                        for pattern in error_patterns:
                            error_matches = re.findall(pattern, post_content, re.IGNORECASE)
                            for error in error_matches:
                                print(f"     Erro: {error.strip()}")
                    else:
                        print(f"   ⚠️ Página sem erro aparente")
                        
                else:
                    print(f"   ❌ Status inesperado: {post_response.status_code}")
                
                # 6. Verificar logs do servidor
                print(f"\n6️⃣ Verificando logs recentes...")
                
                # Fazer uma nova requisição para gerar logs
                test_response = client.get(f'/auth/convite/{token}')
                print(f"   Requisição de teste: {test_response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante debug: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    debug_browser_behavior()