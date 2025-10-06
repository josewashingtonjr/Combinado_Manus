#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para o fluxo de cadastro via convite
"""

from app import app
from models import db, User
from services.wallet_service import WalletService
from services.invite_service import InviteService
from datetime import datetime, timedelta

def test_convite_cadastro():
    with app.test_client() as test_client:
        with app.app_context():
            try:
                print("🧪 Testando fluxo de cadastro via convite...")
                
                # 1. Criar cliente e convite
                print("\n1. Criando cliente e convite...")
                
                import random
                import string
                unique_id = ''.join(random.choices(string.digits, k=6))
                
                # Cliente
                client_user = User(
                    email=f"cliente{unique_id}@teste.com",
                    nome="Cliente Teste",
                    cpf=f"111{unique_id}11",
                    roles="cliente"
                )
                client_user.set_password("123456")
                
                db.session.add(client_user)
                db.session.commit()
                
                # Criar carteira e saldo
                WalletService.ensure_user_has_wallet(client_user.id)
                WalletService.deposit(client_user.id, 200.0, "Saldo inicial")
                
                # Criar convite
                result = InviteService.create_invite(
                    client_id=client_user.id,
                    invited_email=f"prestador{unique_id}@teste.com",
                    service_title="Serviço de Teste",
                    service_description="Descrição do serviço de teste",
                    original_value=100.0,
                    delivery_date=datetime.utcnow() + timedelta(days=7)
                )
                
                token = result['token']
                print(f"✅ Convite criado com token: {token}")
                
                # 2. Testar acesso via token
                print("\n2. Testando acesso via token...")
                
                response = test_client.get(f'/auth/convite/{token}')
                print(f"✅ GET /auth/convite/{token}: {response.status_code}")
                
                # 3. Testar cadastro via convite
                print("\n3. Testando cadastro via convite...")
                
                response = test_client.post(f'/auth/convite/{token}/cadastrar', data={
                    'nome': 'Prestador Teste',
                    'password': '123456',
                    'confirm_password': '123456',
                    'cpf': f'222{unique_id}22',
                    'phone': '(11) 99999-9999',
                    'terms': 'on'
                })
                
                print(f"✅ POST /auth/convite/{token}/cadastrar: {response.status_code}")
                
                # 4. Verificar se usuário foi criado
                print("\n4. Verificando se usuário foi criado...")
                
                new_user = User.query.filter_by(email=f"prestador{unique_id}@teste.com").first()
                if new_user:
                    print(f"✅ Usuário criado: {new_user.nome} ({new_user.email})")
                    print(f"   Papel: {new_user.roles}")
                    print(f"   CPF: {new_user.cpf}")
                else:
                    print("❌ Usuário não foi criado")
                
                # 5. Verificar se carteira foi criada
                print("\n5. Verificando se carteira foi criada...")
                
                if new_user:
                    wallet_info = WalletService.get_wallet_info(new_user.id)
                    print(f"✅ Carteira criada: {wallet_info}")
                
                print("\n🎉 Teste de cadastro via convite concluído!")
                return True
                
            except Exception as e:
                print(f"\n❌ Erro no teste: {e}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == "__main__":
    test_convite_cadastro()