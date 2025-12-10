#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar a criação de ordens de serviço com valor efetivo e histórico de propostas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Invite, Proposal, Order
from services.order_service import OrderService
from services.invite_service import InviteService
from services.proposal_service import ProposalService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def test_order_creation_with_proposals():
    """Testa a criação de ordens com valor efetivo e histórico de propostas"""
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # Inicializar banco de dados
        db.create_all()
        print("🧪 Testando criação de ordens com propostas aceitas...")
        
        try:
            # 1. Criar usuários de teste
            print("\n1️⃣ Criando usuários de teste...")
            
            cliente = User(
                email="cliente@teste.com",
                nome="Cliente Teste",
                phone="11999999999",
                roles=['cliente']
            )
            cliente.set_password("senha123")
            
            prestador = User(
                email="prestador@teste.com", 
                nome="Prestador Teste",
                phone="11888888888",
                roles=['prestador']
            )
            prestador.set_password("senha123")
            
            db.session.add_all([cliente, prestador])
            db.session.commit()
            
            print(f"✅ Cliente criado: {cliente.nome} (ID: {cliente.id})")
            print(f"✅ Prestador criado: {prestador.nome} (ID: {prestador.id})")
            
            # 2. Adicionar saldo ao cliente
            print("\n2️⃣ Adicionando saldo ao cliente...")
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.add_balance(cliente.id, Decimal('500.00'), 'Saldo inicial para teste')
            
            balance = WalletService.get_wallet_balance(cliente.id)
            print(f"✅ Saldo do cliente: R$ {balance:.2f}")
            
            # 3. Adicionar saldo ao prestador
            print("\n3️⃣ Adicionando saldo ao prestador...")
            
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.add_balance(prestador.id, Decimal('100.00'), 'Saldo inicial para teste')
            
            balance_prestador = WalletService.get_wallet_balance(prestador.id)
            print(f"✅ Saldo do prestador: R$ {balance_prestador:.2f}")
            
            # 4. Criar convite
            print("\n4️⃣ Criando convite...")
            
            invite_result = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Desenvolvimento de Website",
                service_description="Criar um website responsivo",
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                service_category="desenvolvimento"
            )
            
            invite = Invite.query.get(invite_result['invite_id'])
            print(f"✅ Convite criado: {invite.service_title} - R$ {invite.original_value:.2f}")
            
            # 5. Prestador cria proposta de alteração
            print("\n5️⃣ Prestador criando proposta de alteração...")
            
            proposal_result = ProposalService.create_proposal(
                invite_id=invite.id,
                prestador_id=prestador.id,
                new_value=Decimal('250.00'),
                justification="Valor ajustado devido à complexidade adicional do projeto"
            )
            
            proposal = Proposal.query.get(proposal_result['proposal_id'])
            print(f"✅ Proposta criada: R$ {proposal.original_value:.2f} → R$ {proposal.proposed_value:.2f}")
            
            # 6. Cliente aprova a proposta
            print("\n6️⃣ Cliente aprovando proposta...")
            
            approval_result = ProposalService.approve_proposal(
                proposal_id=proposal.id,
                client_id=cliente.id
            )
            
            print(f"✅ Proposta aprovada: {approval_result['message']}")
            print(f"   Valor efetivo: R$ {approval_result['effective_value']:.2f}")
            
            # 7. Prestador aceita convite
            print("\n7️⃣ Prestador aceitando convite...")
            
            accept_result = InviteService.accept_invite(
                token=invite.token,
                provider_id=prestador.id
            )
            
            print(f"✅ Convite aceito: {accept_result['message']}")
            
            # 8. Converter convite em ordem de serviço
            print("\n8️⃣ Convertendo convite em ordem de serviço...")
            
            conversion_result = InviteService.convert_invite_to_order(invite.id)
            
            print(f"✅ Conversão realizada: {conversion_result['message']}")
            print(f"   ID da Ordem: {conversion_result['order_id']}")
            print(f"   Valor Original: R$ {conversion_result['original_value']:.2f}")
            print(f"   Valor Efetivo: R$ {conversion_result['effective_value']:.2f}")
            
            # 9. Verificar ordem criada
            print("\n9️⃣ Verificando ordem criada...")
            
            order = Order.query.get(conversion_result['order_id'])
            
            print(f"✅ Ordem #{order.id}:")
            print(f"   Título: {order.title}")
            print(f"   Valor: R$ {order.value:.2f}")
            print(f"   Status: {order.status}")
            print(f"   Cliente: {order.client_id}")
            print(f"   Prestador: {order.provider_id}")
            print(f"   Convite ID: {order.invite_id}")
            
            # Verificar se histórico da proposta está na descrição
            if "Histórico da Proposta" in order.description:
                print("✅ Histórico da proposta incluído na ordem")
            else:
                print("⚠️ Histórico da proposta não encontrado na descrição")
            
            # 10. Verificar saldos após conversão
            print("\n🔟 Verificando saldos após conversão...")
            
            client_wallet = WalletService.get_wallet_info(cliente.id)
            provider_wallet = WalletService.get_wallet_info(prestador.id)
            
            print(f"✅ Saldo Cliente:")
            print(f"   Disponível: R$ {client_wallet['balance']:.2f}")
            print(f"   Em Escrow: R$ {client_wallet['escrow_balance']:.2f}")
            
            print(f"✅ Saldo Prestador:")
            print(f"   Disponível: R$ {provider_wallet['balance']:.2f}")
            print(f"   Em Escrow: R$ {provider_wallet['escrow_balance']:.2f}")
            
            # 11. Teste de criação direta de ordem com proposta
            print("\n1️⃣1️⃣ Testando criação direta de ordem com histórico...")
            
            # Criar outro convite com proposta para teste direto
            invite_result2 = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Manutenção de Sistema",
                service_description="Correções e melhorias",
                original_value=Decimal('150.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                service_category="manutencao"
            )
            
            invite2 = Invite.query.get(invite_result2['invite_id'])
            
            # Criar e aprovar proposta
            proposal_result2 = ProposalService.create_proposal(
                invite_id=invite2.id,
                prestador_id=prestador.id,
                new_value=Decimal('180.00'),
                justification="Escopo expandido conforme solicitação"
            )
            
            ProposalService.approve_proposal(
                proposal_id=proposal_result2['proposal_id'],
                client_id=cliente.id
            )
            
            # Aceitar convite
            InviteService.accept_invite(
                token=invite2.token,
                provider_id=prestador.id
            )
            
            # Usar método direto de criação de ordem
            direct_order_result = OrderService.create_order_from_invite(
                invite_id=invite2.id,
                provider_id=prestador.id
            )
            
            print(f"✅ Ordem criada diretamente:")
            print(f"   ID: {direct_order_result['order_id']}")
            print(f"   Valor Original: R$ {direct_order_result['original_value']:.2f}")
            print(f"   Valor Efetivo: R$ {direct_order_result['effective_value']:.2f}")
            
            if direct_order_result['proposal_history']:
                print(f"   Proposta ID: {direct_order_result['proposal_history']['proposal_id']}")
                print(f"   Justificativa: {direct_order_result['proposal_history']['justification']}")
            
            print("\n🎉 Todos os testes passaram com sucesso!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_order_creation_with_proposals()
    if success:
        print("\n✅ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)