#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples para confirmar que a aceitação de convites está funcionando
"""

from app import app
import re

def test_simple_acceptance():
    """Teste simples de aceitação de convite"""
    
    with app.app_context():
        token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
        
        print(f"🧪 Teste simples de aceitação: {token}")
        
        with app.test_client() as client:
            # 1. GET da página do convite
            response1 = client.get(f'/auth/convite/{token}')
            print(f"1. GET convite: {response1.status_code}")
            
            if response1.status_code != 200:
                return False
            
            # 2. Extrair CSRF e fazer POST
            content = response1.data.decode()
            csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', content)
            csrf_token = csrf_match.group(1) if csrf_match else 'invalid'
            
            response2 = client.post(f'/auth/convite/{token}/aceitar-inicial',
                                  data={'csrf_token': csrf_token},
                                  follow_redirects=True)
            
            print(f"2. POST aceitar (com redirect): {response2.status_code}")
            
            # 3. Verificar se chegou na página correta
            final_content = response2.data.decode()
            
            if 'login' in final_content.lower() and 'cadastro' in final_content.lower():
                print(f"3. ✅ Chegou na página de login/cadastro")
                return True
            else:
                print(f"3. ❌ Não chegou na página correta")
                return False

if __name__ == "__main__":
    success = test_simple_acceptance()
    if success:
        print(f"\n✅ SUCESSO! O redirecionamento está funcionando!")
        print(f"\n🌐 Teste no navegador:")
        print(f"   URL: http://127.0.0.1:5001/auth/convite/HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa")
        print(f"   1. Clique em 'Aceitar Convite'")
        print(f"   2. Confirme na caixa de diálogo")
        print(f"   3. Você será redirecionado automaticamente")
    else:
        print(f"\n❌ Ainda há problemas")