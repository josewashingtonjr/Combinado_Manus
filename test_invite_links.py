#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste específico para verificar problemas com links de convites
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from flask import url_for

def test_invite_links():
    """Testa especificamente os links dos convites"""
    
    with app.app_context():
        try:
            print("🔗 Testando links de convites...")
            
            # 1. Criar um convite de teste
            print("\n1️⃣ Criando convite para teste de link...")
            
            # Buscar cliente existente
            client = User.query.filter_by(roles='cliente').first()
            if not client:
                print("❌ Nenhum cliente encontrado")
                return False
            
            # Garantir que tem carteira
            try:
                current_balance = WalletService.get_wallet_balance(client.id)
            except ValueError:
                # Criar carteira se não existir
                WalletService.create_wallet_for_user(client)
                current_balance = 0
            
            # Garantir saldo
            if current_balance < 200:
                WalletService.credit_wallet(client.id, 500.0, 'Saldo para teste de link')
            
            delivery_date = datetime.now() + timedelta(days=3)
            
            result = InviteService.create_invite(
                client_id=client.id,
                invited_phone='(11) 98888-7777',
                service_title='Teste Link Convite',
                service_description='Teste para verificar links',
                original_value=100.0,
                delivery_date=delivery_date,
                service_category='teste'
            )
            
            invite = InviteService.get_invite_by_token(result['token'])
            
            print(f"✅ Convite criado: {invite.id}")
            print(f"   Token: {invite.token}")
            
            # 2. Testar diferentes formas de gerar o link
            print("\n2️⃣ Testando geração de links...")
            
            # Link via propriedade do modelo
            model_link = invite.invite_link
            print(f"   Link via modelo: {model_link}")
            
            # Link via url_for direto
            try:
                with app.test_request_context():
                    direct_link = url_for('auth.convite_acesso', token=invite.token, _external=True)
                    print(f"   Link via url_for: {direct_link}")
            except Exception as e:
                print(f"   ❌ Erro no url_for: {e}")
            
            # Link via url_for sem _external
            try:
                with app.test_request_context():
                    internal_link = url_for('auth.convite_acesso', token=invite.token)
                    print(f"   Link interno: {internal_link}")
            except Exception as e:
                print(f"   ❌ Erro no link interno: {e}")
            
            # 3. Testar acesso ao link
            print("\n3️⃣ Testando acesso ao link...")
            
            with app.test_client() as client_test:
                # Testar GET na rota do convite
                response = client_test.get(f'/auth/convite/{invite.token}')
                
                print(f"   Status da resposta: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Link acessível")
                    # Verificar se o template foi renderizado
                    if b'convite' in response.data.lower():
                        print("   ✅ Template de convite carregado")
                    else:
                        print("   ⚠️ Template pode não estar correto")
                elif response.status_code == 302:
                    print(f"   ↪️ Redirecionamento para: {response.location}")
                else:
                    print(f"   ❌ Erro no acesso: {response.status_code}")
                    print(f"   Dados: {response.data.decode()[:200]}...")
            
            # 4. Verificar se a rota existe
            print("\n4️⃣ Verificando rotas registradas...")
            
            routes_found = []
            for rule in app.url_map.iter_rules():
                if 'convite' in rule.rule:
                    routes_found.append(f"{rule.rule} -> {rule.endpoint}")
            
            print("   Rotas de convite encontradas:")
            for route in routes_found:
                print(f"     {route}")
            
            # 5. Testar com diferentes tokens
            print("\n5️⃣ Testando validação de tokens...")
            
            with app.test_client() as client_test:
                # Token válido
                response = client_test.get(f'/auth/convite/{invite.token}')
                print(f"   Token válido: {response.status_code}")
                
                # Token inválido
                response = client_test.get('/auth/convite/token_inexistente')
                print(f"   Token inválido: {response.status_code}")
                
                # Token vazio
                response = client_test.get('/auth/convite/')
                print(f"   Token vazio: {response.status_code}")
            
            # 6. Limpar dados de teste
            print("\n6️⃣ Limpando dados de teste...")
            
            db.session.delete(invite)
            db.session.commit()
            
            print("✅ Convite de teste removido")
            
            print("\n🎉 Teste de links concluído!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante teste de links: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_invite_links()
    if success:
        print("\n✅ Links de convites testados com sucesso!")
    else:
        print("\n❌ Problemas encontrados nos links de convites.")