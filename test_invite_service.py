#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste completo para o InviteService
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta

def test_invite_service():
    with app.app_context():
        try:
            print("🧪 Testando InviteService...")
            
            # 1. Criar usuários de teste
            print("\n1. Criando usuários de teste...")
            
            import random
            import string
            
            # Gerar IDs únicos
            unique_id = ''.join(random.choices(string.digits, k=6))
            
            # Cliente
            client = User(
                email=f"cliente{unique_id}@teste.com",
                nome="Cliente Teste",
                cpf=f"123{unique_id}01",
                roles="cliente"
            )
            client.set_password("123456")
            
            # Prestador
            provider = User(
                email=f"prestador{unique_id}@teste.com",
                nome="Prestador Teste",
                cpf=f"109{unique_id}21",
                roles="prestador"
            )
            provider.set_password("123456")
            
            db.session.add_all([client, provider])
            db.session.commit()
            
            print(f"✅ Cliente criado: ID {client.id}")
            print(f"✅ Prestador criado: ID {provider.id}")
            
            # 2. Criar carteiras e adicionar saldo
            print("\n2. Criando carteiras e adicionando saldo...")
            
            WalletService.ensure_user_has_wallet(client.id)
            WalletService.ensure_user_has_wallet(provider.id)
            
            # Adicionar saldo suficiente para o cliente (valor + taxa)
            WalletService.deposit(client.id, 200.0, "Saldo inicial para teste")
            WalletService.deposit(provider.id, 50.0, "Saldo inicial para teste")
            
            client_balance = WalletService.get_wallet_balance(client.id)
            provider_balance = WalletService.get_wallet_balance(provider.id)
            
            print(f"✅ Saldo cliente: R$ {client_balance:.2f}")
            print(f"✅ Saldo prestador: R$ {provider_balance:.2f}")
            
            # 3. Testar criação de convite
            print("\n3. Testando criação de convite...")
            
            result = InviteService.create_invite(
                client_id=client.id,
                invited_email=provider.email,
                service_title="Limpeza Residencial",
                service_description="Limpeza completa de casa de 3 quartos",
                original_value=100.0,
                delivery_date=datetime.utcnow() + timedelta(days=7)
            )
            
            print(f"✅ Convite criado: {result}")
            
            # 4. Testar recuperação de convite
            print("\n4. Testando recuperação de convite...")
            
            invite = InviteService.get_invite_by_token(result['token'])
            print(f"✅ Convite recuperado: {invite.service_title}")
            print(f"   Status: {invite.status}")
            print(f"   Pode ser aceito: {invite.can_be_accepted}")
            
            # 5. Testar listagem de convites
            print("\n5. Testando listagem de convites...")
            
            sent_invites = InviteService.get_invites_sent_by_client(client.id)
            received_invites = InviteService.get_invites_for_email(provider.email)
            
            print(f"✅ Convites enviados pelo cliente: {len(sent_invites)}")
            print(f"✅ Convites recebidos pelo prestador: {len(received_invites)}")
            
            # 6. Testar aceitação de convite
            print("\n6. Testando aceitação de convite...")
            
            accept_result = InviteService.accept_invite(
                token=result['token'],
                provider_id=provider.id,
                final_value=120.0  # Prestador altera o valor
            )
            
            print(f"✅ Convite aceito: {accept_result}")
            
            # 7. Testar conversão para ordem
            print("\n7. Testando conversão para ordem...")
            
            convert_result = InviteService.convert_invite_to_order(invite.id)
            print(f"✅ Convite convertido em ordem: {convert_result}")
            
            # 8. Testar estatísticas
            print("\n8. Testando estatísticas...")
            
            stats = InviteService.get_invite_statistics(client.id)
            print(f"✅ Estatísticas do cliente: {stats}")
            
            general_stats = InviteService.get_invite_statistics()
            print(f"✅ Estatísticas gerais: {general_stats}")
            
            # 9. Verificar estado final
            print("\n9. Verificando estado final...")
            
            # Verificar saldos após conversão
            final_client_balance = WalletService.get_wallet_info(client.id)
            final_provider_balance = WalletService.get_wallet_info(provider.id)
            
            print(f"✅ Saldo final cliente: {final_client_balance}")
            print(f"✅ Saldo final prestador: {final_provider_balance}")
            
            print("ℹ️  Dados de teste mantidos no banco para inspeção")
            
            print("\n🎉 Todos os testes do InviteService passaram!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    test_invite_service()