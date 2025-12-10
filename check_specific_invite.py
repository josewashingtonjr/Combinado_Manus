#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Verificar convite específico mencionado pelo usuário
"""

from app import app
from models import db, Invite
from services.invite_service import InviteService

def check_specific_invite():
    """Verifica o convite específico HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"""
    
    with app.app_context():
        try:
            token = "HIPgij0QzzlQ6C8fXs2A9lxRBaXczKKa"
            print(f"🔍 Verificando convite com token: {token}")
            
            # Tentar buscar o convite
            try:
                invite = InviteService.get_invite_by_token(token)
                
                print(f"\n✅ Convite encontrado:")
                print(f"   ID: {invite.id}")
                print(f"   Título: {invite.service_title}")
                print(f"   Telefone: {invite.invited_phone}")
                print(f"   Status: {invite.status}")
                print(f"   Valor: R$ {invite.original_value:.2f}")
                print(f"   Data de entrega: {invite.delivery_date}")
                print(f"   Expirado: {invite.is_expired}")
                print(f"   Pode ser aceito: {invite.can_be_accepted}")
                print(f"   Link: {invite.invite_link}")
                
                # Testar acesso ao link
                print(f"\n🌐 Testando acesso ao link...")
                
                with app.test_client() as client:
                    response = client.get(f'/auth/convite/{token}')
                    print(f"   Status HTTP: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("   ✅ Página carregando corretamente")
                        
                        # Verificar conteúdo
                        content = response.data.decode()
                        if invite.service_title in content:
                            print("   ✅ Título do serviço presente na página")
                        if token in content:
                            print("   ✅ Token presente na página")
                        if 'aceitar' in content.lower():
                            print("   ✅ Botões de ação presentes")
                            
                    elif response.status_code == 302:
                        print(f"   ↪️ Redirecionamento para: {response.location}")
                        print("   ⚠️ Convite pode estar expirado ou inválido")
                    else:
                        print(f"   ❌ Erro no acesso: {response.status_code}")
                
            except ValueError as e:
                print(f"\n❌ Convite não encontrado: {e}")
                
                # Verificar se existe na base de dados
                invite_db = Invite.query.filter_by(token=token).first()
                if invite_db:
                    print(f"   ⚠️ Convite existe no banco mas não passou na validação")
                    print(f"   Status: {invite_db.status}")
                    print(f"   Expirado: {invite_db.is_expired}")
                else:
                    print(f"   ❌ Convite não existe no banco de dados")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante verificação: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    check_specific_invite()