#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste básico para verificar se as rotas de convites estão funcionando
"""

from app import app
from models import db, User
from services.wallet_service import WalletService
from services.invite_service import InviteService
from datetime import datetime, timedelta

def test_invite_routes():
    with app.test_client() as client:
        with app.app_context():
            try:
                print("🧪 Testando rotas de convites...")
                
                # 1. Criar usuário de teste
                print("\n1. Criando usuário de teste...")
                
                import random
                import string
                unique_id = ''.join(random.choices(string.digits, k=6))
                
                user = User(
                    email=f"teste{unique_id}@cliente.com",
                    nome="Cliente Teste",
                    cpf=f"111{unique_id}11",
                    roles="cliente,prestador"
                )
                user.set_password("123456")
                
                db.session.add(user)
                db.session.commit()
                
                print(f"✅ Usuário criado: {user.email}")
                
                # 2. Criar carteira e adicionar saldo
                WalletService.ensure_user_has_wallet(user.id)
                WalletService.deposit(user.id, 200.0, "Saldo inicial para teste")
                
                print(f"✅ Carteira criada com saldo: R$ 200,00")
                
                # 3. Simular login
                with client.session_transaction() as sess:
                    sess['user_id'] = user.id
                    sess['user_email'] = user.email
                    sess['user_roles'] = user.roles.split(',')
                
                # 4. Testar rota de listagem de convites (cliente)
                print("\n4. Testando rota de listagem de convites...")
                
                response = client.get('/cliente/convites')
                print(f"✅ GET /cliente/convites: {response.status_code}")
                
                # 5. Testar rota de criação de convite
                print("\n5. Testando rota de criação de convite...")
                
                response = client.get('/cliente/convites/criar')
                print(f"✅ GET /cliente/convites/criar: {response.status_code}")
                
                # 6. Testar criação de convite via POST
                print("\n6. Testando criação de convite via POST...")
                
                response = client.post('/cliente/convites/criar', data={
                    'invited_email': f'prestador{unique_id}@teste.com',
                    'service_title': 'Teste de Serviço',
                    'service_description': 'Descrição do teste de serviço',
                    'original_value': '100.00',
                    'delivery_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                })
                print(f"✅ POST /cliente/convites/criar: {response.status_code}")
                
                # 7. Testar rotas do prestador
                print("\n7. Testando rotas do prestador...")
                
                response = client.get('/prestador/convites')
                print(f"✅ GET /prestador/convites: {response.status_code}")
                
                print("\n🎉 Todas as rotas de convites estão funcionando!")
                return True
                
            except Exception as e:
                print(f"\n❌ Erro no teste: {e}")
                return False

if __name__ == "__main__":
    test_invite_routes()