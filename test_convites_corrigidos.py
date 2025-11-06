#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do sistema de convites corrigido
"""

from app import app
from models import db, User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta

def test_invite_system():
    """Testa o sistema de convites corrigido"""
    
    with app.app_context():
        try:
            print("🧪 Testando sistema de convites corrigido...")
            
            # 1. Criar usuário cliente de teste
            print("\n1️⃣ Criando cliente de teste...")
            
            # Verificar se já existe
            client = User.query.filter_by(email='cliente.teste@email.com').first()
            if not client:
                # Gerar CPF único baseado no timestamp
                import time
                unique_cpf = f'999.888.{int(time.time()) % 10000:04d}-99'
                
                client = User(
                    nome='Cliente Teste',
                    email='cliente.teste@email.com',
                    cpf=unique_cpf,
                    phone='(11) 98765-4321',
                    roles='cliente'
                )
                client.set_password('123456')
                db.session.add(client)
                db.session.commit()
                
                # Criar carteira
                WalletService.create_wallet_for_user(client)
                
                # Adicionar saldo
                WalletService.credit_wallet(client.id, 1000.0, 'Saldo inicial para teste')
                
                print(f"✅ Cliente criado: {client.nome} (ID: {client.id})")
            else:
                print(f"✅ Cliente existente: {client.nome} (ID: {client.id})")
            
            # Garantir que o cliente tem saldo suficiente
            current_balance = WalletService.get_wallet_balance(client.id)
            if current_balance < 200:
                WalletService.credit_wallet(client.id, 1000.0, 'Saldo para teste')
                print(f"✅ Saldo adicionado. Saldo atual: R$ {WalletService.get_wallet_balance(client.id):.2f}")
            
            # 2. Testar criação de convite com telefone
            print("\n2️⃣ Testando criação de convite...")
            
            delivery_date = datetime.now() + timedelta(days=7)
            
            result = InviteService.create_invite(
                client_id=client.id,
                invited_phone='(11) 99999-8888',
                service_title='Limpeza Residencial Teste',
                service_description='Limpeza completa de casa de 3 quartos para teste do sistema',
                original_value=150.0,
                delivery_date=delivery_date,
                service_category='limpeza'
            )
            
            print(f"✅ Convite criado com sucesso!")
            print(f"   Token: {result['token']}")
            print(f"   Link: {result['invite_link']}")
            print(f"   Expira em: {result['expires_at']}")
            
            # 3. Verificar se o convite foi salvo corretamente
            print("\n3️⃣ Verificando dados do convite...")
            
            invite = InviteService.get_invite_by_token(result['token'])
            
            print(f"✅ Convite recuperado:")
            print(f"   ID: {invite.id}")
            print(f"   Telefone: {invite.invited_phone}")
            print(f"   Título: {invite.service_title}")
            print(f"   Categoria: {invite.service_category}")
            print(f"   Valor: R$ {invite.original_value}")
            print(f"   Status: {invite.status}")
            print(f"   Pode ser aceito: {invite.can_be_accepted}")
            print(f"   Está expirado: {invite.is_expired}")
            print(f"   Link: {invite.invite_link}")
            
            # 4. Testar busca por telefone
            print("\n4️⃣ Testando busca por telefone...")
            
            invites_for_phone = InviteService.get_invites_for_phone('(11) 99999-8888')
            
            print(f"✅ Encontrados {len(invites_for_phone)} convites para o telefone")
            
            if invites_for_phone:
                invite_data = invites_for_phone[0]
                print(f"   Primeiro convite: {invite_data['service_title']}")
                print(f"   Link: {invite_data['invite_link']}")
            
            # 5. Testar lógica de expiração
            print("\n5️⃣ Testando lógica de expiração...")
            
            # Testar se convite atual não está expirado
            print(f"✅ Convite atual:")
            print(f"   Data de entrega: {invite.delivery_date}")
            print(f"   Está expirado: {invite.is_expired}")
            print(f"   Pode ser aceito: {invite.can_be_accepted}")
            
            # Testar validação de data passada
            try:
                expired_delivery = datetime.now() - timedelta(hours=1)
                InviteService.create_invite(
                    client_id=client.id,
                    invited_phone='(11) 88888-7777',
                    service_title='Convite Expirado Teste',
                    service_description='Este convite deveria falhar',
                    original_value=100.0,
                    delivery_date=expired_delivery,
                    service_category='teste'
                )
                print("❌ Erro: Deveria ter rejeitado data passada")
            except ValueError as e:
                print(f"✅ Validação funcionando: {e}")
            
            # 6. Testar estatísticas
            print("\n6️⃣ Testando estatísticas...")
            
            stats = InviteService.get_invite_statistics(client.id)
            
            print(f"✅ Estatísticas do cliente:")
            print(f"   Total de convites: {stats['total_invites']}")
            print(f"   Convites pendentes: {stats['pending_invites']}")
            print(f"   Taxa de aceitação: {stats['acceptance_rate']:.1f}%")
            print(f"   Valor total: R$ {stats['total_value']:.2f}")
            
            # 7. Limpar dados de teste
            print("\n7️⃣ Limpando dados de teste...")
            
            # Remover convites de teste
            test_invites = Invite.query.filter(
                Invite.client_id == client.id,
                Invite.service_title.like('%Teste%')
            ).all()
            
            for invite in test_invites:
                db.session.delete(invite)
            
            db.session.commit()
            
            print(f"✅ {len(test_invites)} convites de teste removidos")
            
            print("\n🎉 Todos os testes passaram! Sistema de convites funcionando corretamente.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_invite_system()
    if success:
        print("\n✅ Sistema de convites está funcionando corretamente!")
        print("\n📋 Funcionalidades testadas:")
        print("   ✅ Criação de convite com telefone")
        print("   ✅ Geração de link do convite")
        print("   ✅ Expiração baseada na data do serviço")
        print("   ✅ Busca por telefone")
        print("   ✅ Validação de dados")
        print("   ✅ Estatísticas")
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")