#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para Task 13: Garantir que ordem de serviço usa valor efetivo correto

Validações:
- Ordem criada usa invite.current_value
- current_value retorna effective_value quando existe
- current_value retorna original_value quando não há proposta
- Referência à proposta é incluída na ordem
- Saldo do cliente é validado com valor correto

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from app import app
from models import db, User, Invite, Proposal, Order
from services.invite_service import InviteService
from services.order_service import OrderService
from services.proposal_service import ProposalService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def test_order_uses_effective_value():
    """
    Testa que a ordem de serviço usa o valor efetivo correto
    """
    with app.app_context():
        # Limpar dados de teste
        db.session.query(Order).delete()
        db.session.query(Proposal).delete()
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        print("\n" + "="*80)
        print("TESTE: Ordem de Serviço com Valor Efetivo Correto")
        print("="*80)
        
        # 1. Criar usuários
        print("\n1️⃣ Criando usuários...")
        cliente = User(
            email='cliente@test.com',
            nome='Cliente Teste',
            cpf='12345678901',
            phone='11999999999',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            email='prestador@test.com',
            nome='Prestador Teste',
            cpf='98765432100',
            phone='11988888888',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Adicionar saldo ao cliente
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.deposit(cliente.id, Decimal('1000.00'), "Saldo inicial para testes")
        
        # Adicionar saldo ao prestador
        WalletService.ensure_user_has_wallet(prestador.id)
        WalletService.deposit(prestador.id, Decimal('100.00'), "Saldo inicial para testes")
        
        print(f"✅ Cliente criado: {cliente.nome} (ID: {cliente.id})")
        print(f"✅ Prestador criado: {prestador.nome} (ID: {prestador.id})")
        print(f"   Saldo cliente: R$ {WalletService.get_wallet_balance(cliente.id):.2f}")
        print(f"   Saldo prestador: R$ {WalletService.get_wallet_balance(prestador.id):.2f}")
        
        # ========================================================================
        # CENÁRIO 1: Ordem sem proposta (deve usar original_value)
        # ========================================================================
        print("\n" + "="*80)
        print("CENÁRIO 1: Ordem sem proposta (valor original)")
        print("="*80)
        
        # Criar convite
        print("\n2️⃣ Criando convite sem proposta...")
        invite_result = InviteService.create_invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço Teste 1',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7)
        )
        
        invite1 = Invite.query.get(invite_result['invite_id'])
        print(f"✅ Convite criado: ID {invite1.id}")
        print(f"   Valor original: R$ {invite1.original_value:.2f}")
        print(f"   Valor efetivo: {invite1.effective_value}")
        print(f"   current_value: R$ {invite1.current_value:.2f}")
        
        # Validar que current_value retorna original_value quando não há proposta
        # Requirement: 6.2
        assert invite1.effective_value is None, "effective_value deve ser None sem proposta"
        assert invite1.current_value == invite1.original_value, "current_value deve retornar original_value sem proposta"
        print("✅ Validação: current_value retorna original_value quando não há proposta")
        
        # Aceitar convite
        print("\n3️⃣ Prestador aceita convite...")
        accept_result = InviteService.accept_invite(
            token=invite1.token,
            provider_id=prestador.id
        )
        print(f"✅ Convite aceito")
        
        # Converter em ordem
        print("\n4️⃣ Convertendo convite em ordem...")
        saldo_antes = WalletService.get_wallet_balance(cliente.id)
        
        order_result = InviteService.convert_invite_to_order(invite1.id)
        order1 = Order.query.get(order_result['order_id'])
        
        saldo_depois = WalletService.get_wallet_balance(cliente.id)
        
        print(f"✅ Ordem criada: ID {order1.id}")
        print(f"   Valor da ordem: R$ {order1.value:.2f}")
        print(f"   Valor original do convite: R$ {invite1.original_value:.2f}")
        print(f"   Saldo cliente antes: R$ {saldo_antes:.2f}")
        print(f"   Saldo cliente depois: R$ {saldo_depois:.2f}")
        print(f"   Diferença: R$ {(saldo_antes - saldo_depois):.2f}")
        
        # Validar que ordem usa valor correto
        # Requirement: 6.1
        assert order1.value == invite1.original_value, "Ordem deve usar original_value quando não há proposta"
        assert order1.value == invite1.current_value, "Ordem deve usar current_value"
        print("✅ Validação: Ordem usa valor original correto (sem proposta)")
        
        # Validar que saldo foi reservado corretamente
        # Requirement: 6.5
        assert saldo_antes - saldo_depois == float(invite1.original_value), "Saldo reservado deve ser igual ao valor original"
        print("✅ Validação: Saldo do cliente validado com valor correto")
        
        # ========================================================================
        # CENÁRIO 2: Ordem com proposta aceita (deve usar effective_value)
        # ========================================================================
        print("\n" + "="*80)
        print("CENÁRIO 2: Ordem com proposta aceita (valor efetivo)")
        print("="*80)
        
        # Criar segundo convite
        print("\n5️⃣ Criando segundo convite...")
        invite_result2 = InviteService.create_invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço Teste 2',
            service_description='Descrição do serviço 2',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7)
        )
        
        invite2 = Invite.query.get(invite_result2['invite_id'])
        print(f"✅ Convite criado: ID {invite2.id}")
        print(f"   Valor original: R$ {invite2.original_value:.2f}")
        
        # Criar proposta de alteração
        print("\n6️⃣ Prestador cria proposta de alteração...")
        try:
            proposal_result = ProposalService.create_proposal(
                invite_id=invite2.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('250.00'),
                justification='Necessário material adicional'
            )
            
            if 'proposal_id' not in proposal_result:
                print(f"⚠️  Resultado da proposta: {proposal_result}")
                raise ValueError("proposal_id não encontrado no resultado")
            
            proposal = Proposal.query.get(proposal_result['proposal_id'])
        except Exception as e:
            print(f"❌ Erro ao criar proposta: {e}")
            # Tentar buscar a proposta diretamente
            proposal = Proposal.query.filter_by(invite_id=invite2.id, prestador_id=prestador.id).first()
            if not proposal:
                raise
        print(f"✅ Proposta criada: ID {proposal.id}")
        print(f"   Valor original: R$ {proposal.original_value:.2f}")
        print(f"   Valor proposto: R$ {proposal.proposed_value:.2f}")
        
        # Cliente aprova proposta
        print("\n7️⃣ Cliente aprova proposta...")
        approve_result = ProposalService.approve_proposal(
            proposal_id=proposal.id,
            client_id=cliente.id,
            client_response_reason='Aprovado'
        )
        
        db.session.refresh(invite2)
        print(f"✅ Proposta aprovada")
        print(f"   Valor efetivo do convite: R$ {invite2.effective_value:.2f}")
        print(f"   current_value: R$ {invite2.current_value:.2f}")
        print(f"   has_active_proposal: {invite2.has_active_proposal}")
        print(f"   current_proposal_id: {invite2.current_proposal_id}")
        
        # Validar que current_value retorna effective_value quando existe
        # Requirement: 6.2
        assert invite2.effective_value is not None, "effective_value deve estar setado após aprovação"
        assert invite2.effective_value == proposal.proposed_value, "effective_value deve ser igual ao valor proposto"
        assert invite2.current_value == invite2.effective_value, "current_value deve retornar effective_value quando existe"
        print("✅ Validação: current_value retorna effective_value quando existe proposta aceita")
        
        # Prestador aceita convite
        print("\n8️⃣ Prestador aceita convite...")
        accept_result2 = InviteService.accept_invite(
            token=invite2.token,
            provider_id=prestador.id
        )
        print(f"✅ Convite aceito")
        
        # Converter em ordem
        print("\n9️⃣ Convertendo convite em ordem...")
        saldo_antes2 = WalletService.get_wallet_balance(cliente.id)
        
        order_result2 = InviteService.convert_invite_to_order(invite2.id)
        order2 = Order.query.get(order_result2['order_id'])
        
        saldo_depois2 = WalletService.get_wallet_balance(cliente.id)
        
        print(f"✅ Ordem criada: ID {order2.id}")
        print(f"   Valor da ordem: R$ {order2.value:.2f}")
        print(f"   Valor original do convite: R$ {invite2.original_value:.2f}")
        print(f"   Valor efetivo do convite: R$ {invite2.effective_value:.2f}")
        print(f"   Saldo cliente antes: R$ {saldo_antes2:.2f}")
        print(f"   Saldo cliente depois: R$ {saldo_depois2:.2f}")
        print(f"   Diferença: R$ {(saldo_antes2 - saldo_depois2):.2f}")
        
        # Validar que ordem usa valor efetivo
        # Requirement: 6.1
        assert order2.value == invite2.effective_value, "Ordem deve usar effective_value quando há proposta aceita"
        assert order2.value == invite2.current_value, "Ordem deve usar current_value"
        assert order2.value != invite2.original_value, "Ordem NÃO deve usar original_value quando há proposta aceita"
        print("✅ Validação: Ordem usa valor efetivo correto (com proposta aceita)")
        
        # Validar que saldo foi reservado com valor efetivo
        # Requirement: 6.5
        assert saldo_antes2 - saldo_depois2 == float(invite2.effective_value), "Saldo reservado deve ser igual ao valor efetivo"
        print("✅ Validação: Saldo do cliente validado com valor efetivo correto")
        
        # Validar que referência à proposta está na ordem
        # Requirement: 6.3, 6.4
        assert order_result2['proposal_history'] is not None, "Histórico da proposta deve estar presente"
        assert order_result2['proposal_history']['proposal_id'] == proposal.id, "ID da proposta deve estar no histórico"
        assert order_result2['proposal_history']['original_value'] == float(proposal.original_value), "Valor original deve estar no histórico"
        assert order_result2['proposal_history']['proposed_value'] == float(proposal.proposed_value), "Valor proposto deve estar no histórico"
        print("✅ Validação: Referência à proposta incluída na ordem")
        
        # ========================================================================
        # CENÁRIO 3: Validação de saldo insuficiente
        # ========================================================================
        print("\n" + "="*80)
        print("CENÁRIO 3: Validação de saldo insuficiente")
        print("="*80)
        
        # Criar terceiro convite com valor alto
        print("\n🔟 Criando convite com valor alto...")
        invite_result3 = InviteService.create_invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço Teste 3',
            service_description='Descrição do serviço 3',
            original_value=Decimal('50.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7)
        )
        
        invite3 = Invite.query.get(invite_result3['invite_id'])
        print(f"✅ Convite criado: ID {invite3.id}")
        print(f"   Valor original: R$ {invite3.original_value:.2f}")
        
        # Criar proposta com valor muito alto
        print("\n1️⃣1️⃣ Prestador cria proposta com valor alto...")
        proposal_result3 = ProposalService.create_proposal(
            invite_id=invite3.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('10000.00'),  # Valor muito alto
            justification='Projeto complexo'
        )
        
        proposal3 = Proposal.query.get(proposal_result3['proposal_id'])
        print(f"✅ Proposta criada: ID {proposal3.id}")
        print(f"   Valor proposto: R$ {proposal3.proposed_value:.2f}")
        
        # Cliente tenta aprovar (deve falhar por saldo insuficiente)
        print("\n1️⃣2️⃣ Cliente tenta aprovar proposta (deve falhar)...")
        saldo_atual = WalletService.get_wallet_balance(cliente.id)
        print(f"   Saldo atual do cliente: R$ {saldo_atual:.2f}")
        print(f"   Valor necessário: R$ {proposal3.proposed_value:.2f}")
        
        try:
            approve_result3 = ProposalService.approve_proposal(
                proposal_id=proposal3.id,
                client_id=cliente.id,
                client_response_reason='Tentando aprovar'
            )
            print("❌ ERRO: Deveria ter falhado por saldo insuficiente!")
            assert False, "Deveria ter lançado exceção por saldo insuficiente"
        except ValueError as e:
            print(f"✅ Validação: Aprovação bloqueada corretamente - {str(e)}")
            assert "saldo insuficiente" in str(e).lower(), "Mensagem deve mencionar saldo insuficiente"
        
        # ========================================================================
        # RESUMO FINAL
        # ========================================================================
        print("\n" + "="*80)
        print("RESUMO DOS TESTES")
        print("="*80)
        print("✅ Cenário 1: Ordem sem proposta usa original_value")
        print("✅ Cenário 2: Ordem com proposta aceita usa effective_value")
        print("✅ Cenário 3: Validação de saldo com valor correto")
        print("✅ current_value retorna effective_value quando existe")
        print("✅ current_value retorna original_value quando não há proposta")
        print("✅ Referência à proposta incluída na ordem")
        print("✅ Saldo do cliente validado corretamente")
        print("\n" + "="*80)
        print("TODOS OS TESTES PASSARAM! ✅")
        print("="*80)

if __name__ == '__main__':
    test_order_uses_effective_value()
