#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Debug do template de convite para verificar o problema de redirecionamento
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService

def debug_invite_template():
    """Debug do template de convite"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🔍 Debugando template do convite: {token}")
            
            # 1. Verificar se o convite existe
            try:
                invite = InviteService.get_invite_by_token(token)
                print(f"✅ Convite encontrado: {invite.service_title}")
            except ValueError as e:
                print(f"❌ Convite não encontrado: {e}")
                return False
            
            # 2. Fazer request e capturar o HTML completo
            print(f"\n2️⃣ Capturando HTML da página...")
            
            with app.test_client() as client:
                response = client.get(f'/auth/convite/{token}')
                
                if response.status_code == 200:
                    content = response.data.decode()
                    
                    # Salvar HTML para análise
                    with open('debug_invite_page.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✅ HTML salvo em debug_invite_page.html")
                    
                    # 3. Procurar elementos específicos
                    print(f"\n3️⃣ Analisando elementos da página...")
                    
                    searches = [
                        ('Formulário de aceitação', 'aceitar_convite_inicial'),
                        ('Action do formulário', 'action='),
                        ('Botão de aceitar', 'Aceitar Convite'),
                        ('Token no formulário', token),
                        ('CSRF token', 'csrf_token'),
                        ('Method POST', 'method="POST"'),
                        ('Bootstrap', 'bootstrap'),
                        ('JavaScript', '<script>'),
                        ('Título do serviço', invite.service_title),
                        ('Nome do cliente', invite.client.nome if invite.client else 'N/A')
                    ]
                    
                    for search_name, search_term in searches:
                        found = search_term in content
                        status = "✅" if found else "❌"
                        print(f"   {status} {search_name}: {'Encontrado' if found else 'Não encontrado'}")
                        
                        if found and search_term == 'aceitar_convite_inicial':
                            # Encontrar a linha específica
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if search_term in line:
                                    print(f"      Linha {i+1}: {line.strip()}")
                                    break
                    
                    # 4. Verificar se há erros JavaScript
                    print(f"\n4️⃣ Verificando possíveis erros...")
                    
                    error_indicators = [
                        'error', 'Error', 'ERROR',
                        'undefined', 'null',
                        'failed', 'Failed',
                        '404', '500', '403'
                    ]
                    
                    for indicator in error_indicators:
                        if indicator in content:
                            print(f"   ⚠️ Possível erro encontrado: {indicator}")
                            # Mostrar contexto
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if indicator in line:
                                    print(f"      Linha {i+1}: {line.strip()}")
                                    break
                    
                    # 5. Verificar estrutura do formulário
                    print(f"\n5️⃣ Analisando estrutura do formulário...")
                    
                    import re
                    
                    # Procurar por formulários
                    form_pattern = r'<form[^>]*>(.*?)</form>'
                    forms = re.findall(form_pattern, content, re.DOTALL | re.IGNORECASE)
                    
                    print(f"   Formulários encontrados: {len(forms)}")
                    
                    for i, form in enumerate(forms):
                        if 'aceitar_convite_inicial' in form:
                            print(f"   ✅ Formulário {i+1} contém aceitar_convite_inicial")
                            
                            # Extrair action
                            action_match = re.search(r'action="([^"]*)"', form, re.IGNORECASE)
                            if action_match:
                                print(f"      Action: {action_match.group(1)}")
                            
                            # Extrair method
                            method_match = re.search(r'method="([^"]*)"', form, re.IGNORECASE)
                            if method_match:
                                print(f"      Method: {method_match.group(1)}")
                        else:
                            print(f"   ⚠️ Formulário {i+1} não contém aceitar_convite_inicial")
                    
                    return True
                    
                else:
                    print(f"❌ Erro ao acessar página: {response.status_code}")
                    return False
            
        except Exception as e:
            print(f"\n❌ Erro durante debug: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    debug_invite_template()