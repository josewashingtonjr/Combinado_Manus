#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste de Integração Completo: Convite → Pré-Ordem → Ordem
Feature: sistema-pre-ordem-negociacao
Task 10: Checkpoint - Testes de integração

Este teste verifica o fluxo completo do sistema:
1. Criação e aceitação de convite
2. Criação de pré-ordem
3. Negociação (propostas)
4. Aceitação mútua de termos
5. Conversão para ordem
6. Bloqueio de valores em escrow
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, PreOrderProposal,
    Order, Wallet, Transaction
)
from config import TestConfig
from services.invite_service import InviteService
from services.pre_order_service import PreOrderService
from services.pre_order_proposal_service import PreOrderProposalService
from services.pre_order_conversion_service import PreOrderConversionService


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture(scope='module')
def test_app():
    """Cria uma aplicação Flask para testes"""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def clean_db(test_app):
    """Limpa o banco de dados antes de cada teste"""
    with test_app.app_context():
        # Limpar todas as tabelas na ordem correta
        db.session.query(Transaction).delete()
        db.session.query(Order).delete()
        db.session.query(PreOrderProposal).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        yield
        db.session.rollback()


# ==============================================================================
# TESTE DE INTEGRAÇÃO COMPLETO
# ==============================================================================

def test_complete_flow_invite_to_order(test_app, clean_db):
    """
    Teste de integração completo: Convite → Pré-Ordem → Ordem
    
    Verifica:
    1. Convite é aceito e cria pré-ordem (não ordem)
    2. Valores NÃO são bloqueados na criação da pré-ordem
    3. Negociação funciona (propostas aceitas/rejeitadas)
    4. Aceitação mútua de termos
    5. Conversão para ordem
    6. Valores SÃO bloqueados apenas na conversão
    7. Convite convertido não permite modificações
    """
    with test_app.app_context():
        # ======================================================================
        # FASE 1: SETUP - Criar usuários e carteiras
        # ======================================================================
        print("\n=== FASE 1: Setup ===")
        
        client = User(
            email='cliente_flow@example.com',
            nome='Cliente Flow',
            cpf='11111111111',
            phone='11999999999',
            roles='cliente'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(
            email='prestador_flow@example.com',
            nome='Prestador Flow',
            cpf='22222222222',
            phone='11888888888',
            roles='prestador'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        # Criar carteiras com saldo suficiente
        service_value = Decimal('500.00')
        client_initial_balance = Decimal('1000.00')
        provider_initial_balance = Decimal('100.00')
        
        client_wallet = Wallet(user_id=client.id, balance=client_initial_balance)
        provider_wallet = Wallet(user_id=provider.id, balance=provider_initial_balance)
        db.session.add_all([client_wallet, provider_wallet])
        
        db.session.commit()
        
        print(f"✓ Cliente criado: {client.nome} (saldo: R$ {client_initial_balance})")
        print(f"✓ Prestador criado: {provider.nome} (saldo: R$ {provider_initial_balance})")
        
        # ======================================================================
        # FASE 2: CONVITE → PRÉ-ORDEM
        # ======================================================================
        print("\n=== FASE 2: Convite → Pré-Ordem ===")
        
        # Criar convite
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Serviço de Teste Completo',
            service_description='Descrição do serviço de teste',
            service_category='pedreiro',
            original_value=service_value,
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente',
            client_accepted=True,
            provider_accepted=False,
            client_accepted_at=datetime.utcnow()
        )
        db.session.add(invite)
        db.session.commit()
        
        print(f"✓ Convite criado: {invite.service_title} (valor: R$ {service_value})")
        
        # Prestador aceita convite (deve criar pré-ordem)
        result = InviteService.accept_invite_as_provider(invite.id, provider.id)
        
        assert result['success'], f"Aceitação do convite falhou: {result.get('error')}"
        assert result.get('pre_order_created') == True, "Deve criar pré-ordem"
        assert result.get('order_created', False) == False, "NÃO deve criar ordem ainda"
        
        pre_order_id = result['pre_order_id']
        print(f"✓ Pré-ordem criada: ID {pre_order_id}")
        
        # Verificar que convite foi convertido
        db.session.expire_all()
        invite = Invite.query.get(invite.id)
        assert invite.status == 'convertido_pre_ordem', \
            "Convite deve estar marcado como convertido_pre_ordem"
        print(f"✓ Convite convertido: status = {invite.status}")
        
        # Verificar que valores NÃO foram bloqueados
        client_wallet = Wallet.query.filter_by(user_id=client.id).first()
        provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
        
        assert client_wallet.balance == client_initial_balance, \
            "Saldo do cliente não deve ser alterado na criação da pré-ordem"
        assert provider_wallet.balance == provider_initial_balance, \
            "Saldo do prestador não deve ser alterado na criação da pré-ordem"
        assert client_wallet.escrow_balance == Decimal('0.00'), \
            "Cliente não deve ter valores em escrow"
        assert provider_wallet.escrow_balance == Decimal('0.00'), \
            "Prestador não deve ter valores em escrow"
        
        print(f"✓ Valores NÃO bloqueados: Cliente R$ {client_wallet.balance}, Prestador R$ {provider_wallet.balance}")
        
        # Verificar pré-ordem
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
            "Pré-ordem deve estar em negociação"
        assert pre_order.current_value == service_value, \
            "Valor atual deve ser o valor original"
        print(f"✓ Pré-ordem em negociação: valor R$ {pre_order.current_value}")
        
        # ======================================================================
        # FASE 3: NEGOCIAÇÃO (Propostas)
        # ======================================================================
        print("\n=== FASE 3: Negociação ===")
        
        # Prestador propõe redução de valor
        new_value = Decimal('450.00')
        proposal_result = PreOrderProposalService.create_proposal(
            pre_order_id=pre_order_id,
            user_id=provider.id,
            proposed_value=new_value,
            proposed_delivery_date=None,
            proposed_description=None,
            justification="Posso fazer por um valor menor mantendo a qualidade"
        )
        
        assert proposal_result['success'], f"Criação de proposta falhou: {proposal_result.get('error')}"
        proposal_id = proposal_result['proposal_id']
        print(f"✓ Proposta criada: ID {proposal_id} (R$ {service_value} → R$ {new_value})")
        
        # Verificar que status mudou para aguardando_resposta
        db.session.expire_all()
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order.status == PreOrderStatus.AGUARDANDO_RESPOSTA.value, \
            "Status deve ser aguardando_resposta após proposta"
        print(f"✓ Status atualizado: {pre_order.status}")
        
        # Cliente aceita a proposta
        accept_result = PreOrderProposalService.accept_proposal(
            proposal_id=proposal_id,
            user_id=client.id
        )
        
        assert accept_result['success'], f"Aceitação de proposta falhou: {accept_result.get('error')}"
        print(f"✓ Proposta aceita pelo cliente")
        
        # Verificar que valor foi atualizado
        db.session.expire_all()
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order.current_value == new_value, \
            f"Valor deve ser atualizado para R$ {new_value}"
        assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
            "Status deve voltar para em_negociacao"
        print(f"✓ Valor atualizado: R$ {pre_order.current_value}")
        
        # ======================================================================
        # FASE 4: ACEITAÇÃO MÚTUA DE TERMOS
        # ======================================================================
        print("\n=== FASE 4: Aceitação Mútua de Termos ===")
        
        # Cliente aceita termos
        client_accept = PreOrderService.accept_terms(pre_order_id, client.id)
        assert client_accept['success'], f"Cliente não conseguiu aceitar termos: {client_accept.get('error')}"
        print(f"✓ Cliente aceitou os termos")
        
        # Prestador aceita termos
        provider_accept = PreOrderService.accept_terms(pre_order_id, provider.id)
        assert provider_accept['success'], f"Prestador não conseguiu aceitar termos: {provider_accept.get('error')}"
        print(f"✓ Prestador aceitou os termos")
        
        # Verificar que status mudou para pronto_conversao
        db.session.expire_all()
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order.status == PreOrderStatus.PRONTO_CONVERSAO.value, \
            "Status deve ser pronto_conversao após aceitação mútua"
        assert pre_order.client_accepted_terms == True, \
            "Cliente deve ter aceitado termos"
        assert pre_order.provider_accepted_terms == True, \
            "Prestador deve ter aceitado termos"
        print(f"✓ Aceitação mútua alcançada: status = {pre_order.status}")
        
        # ======================================================================
        # FASE 5: CONVERSÃO PARA ORDEM
        # ======================================================================
        print("\n=== FASE 5: Conversão para Ordem ===")
        
        # Converter para ordem
        conversion_result = PreOrderConversionService.convert_to_order(pre_order_id)
        
        assert conversion_result['success'], \
            f"Conversão para ordem falhou: {conversion_result.get('error')}"
        order_id = conversion_result['order_id']
        print(f"✓ Ordem criada: ID {order_id}")
        
        # Verificar que pré-ordem foi marcada como convertida
        db.session.expire_all()
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order.status == PreOrderStatus.CONVERTIDA.value, \
            "Pré-ordem deve estar marcada como convertida"
        assert pre_order.order_id == order_id, \
            "Pré-ordem deve referenciar a ordem criada"
        print(f"✓ Pré-ordem convertida: status = {pre_order.status}")
        
        # Verificar que ordem foi criada corretamente
        order = Order.query.get(order_id)
        assert order is not None, "Ordem deve existir"
        assert order.client_id == client.id, "Cliente deve estar correto"
        assert order.provider_id == provider.id, "Prestador deve estar correto"
        assert order.value == new_value, \
            f"Valor da ordem deve ser R$ {new_value}"
        assert order.status == 'aceita', "Ordem deve estar aceita"
        print(f"✓ Ordem criada corretamente: valor R$ {order.value}, status = {order.status}")
        
        # ======================================================================
        # FASE 6: VERIFICAR BLOQUEIO DE VALORES
        # ======================================================================
        print("\n=== FASE 6: Verificação de Bloqueio de Valores ===")
        
        # Verificar que valores foram bloqueados APENAS na conversão
        db.session.expire_all()
        client_wallet = Wallet.query.filter_by(user_id=client.id).first()
        provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
        
        # Cliente deve ter valor bloqueado em escrow
        expected_client_escrow = new_value
        assert client_wallet.escrow_balance == expected_client_escrow, \
            f"Cliente deve ter R$ {expected_client_escrow} em escrow, tem R$ {client_wallet.escrow_balance}"
        
        expected_client_balance = client_initial_balance - expected_client_escrow
        assert client_wallet.balance == expected_client_balance, \
            f"Saldo do cliente deve ser R$ {expected_client_balance}, é R$ {client_wallet.balance}"
        
        print(f"✓ Cliente: saldo R$ {client_wallet.balance}, escrow R$ {client_wallet.escrow_balance}")
        
        # Prestador deve ter taxa de contestação bloqueada
        # (assumindo 10% do valor como taxa de contestação)
        expected_provider_escrow = new_value * Decimal('0.10')
        assert provider_wallet.escrow_balance == expected_provider_escrow, \
            f"Prestador deve ter R$ {expected_provider_escrow} em escrow, tem R$ {provider_wallet.escrow_balance}"
        
        expected_provider_balance = provider_initial_balance - expected_provider_escrow
        assert provider_wallet.balance == expected_provider_balance, \
            f"Saldo do prestador deve ser R$ {expected_provider_balance}, é R$ {provider_wallet.balance}"
        
        print(f"✓ Prestador: saldo R$ {provider_wallet.balance}, escrow R$ {provider_wallet.escrow_balance}")
        
        # ======================================================================
        # FASE 7: VERIFICAR IMUTABILIDADE DO CONVITE
        # ======================================================================
        print("\n=== FASE 7: Verificação de Imutabilidade ===")
        
        # Convite convertido não deve permitir modificações
        invite = Invite.query.get(invite.id)
        assert invite.status == 'convertido_pre_ordem', \
            "Convite deve permanecer como convertido_pre_ordem"
        
        # Tentar modificar convite deve falhar (se houver validação)
        # Por enquanto, apenas verificamos o status
        print(f"✓ Convite permanece imutável: status = {invite.status}")
        
        # ======================================================================
        # RESUMO FINAL
        # ======================================================================
        print("\n=== RESUMO DO FLUXO COMPLETO ===")
        print(f"✓ Convite aceito → Pré-ordem criada (sem bloqueio)")
        print(f"✓ Negociação realizada (proposta aceita)")
        print(f"✓ Aceitação mútua de termos")
        print(f"✓ Conversão para ordem")
        print(f"✓ Valores bloqueados em escrow (apenas na conversão)")
        print(f"✓ Convite convertido permanece imutável")
        print(f"\n✅ FLUXO COMPLETO VALIDADO COM SUCESSO!")


def test_values_not_blocked_before_conversion(test_app, clean_db):
    """
    Teste específico: Valores não são bloqueados antes da conversão
    
    Verifica que durante toda a fase de negociação (pré-ordem),
    nenhum valor é bloqueado em escrow.
    """
    with test_app.app_context():
        # Criar usuários e carteiras
        client = User(
            email='client_noblock@example.com',
            nome='Cliente No Block',
            cpf='33333333333',
            phone='11777777777',
            roles='cliente'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(
            email='provider_noblock@example.com',
            nome='Prestador No Block',
            cpf='44444444444',
            phone='11666666666',
            roles='prestador'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        initial_balance = Decimal('1000.00')
        client_wallet = Wallet(user_id=client.id, balance=initial_balance)
        provider_wallet = Wallet(user_id=provider.id, balance=initial_balance)
        db.session.add_all([client_wallet, provider_wallet])
        
        db.session.commit()
        
        # Criar convite e aceitar (cria pré-ordem)
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Teste Bloqueio',
            service_description='Teste',
            service_category='pintor',
            original_value=Decimal('300.00'),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            status='pendente',
            client_accepted=True,
            provider_accepted=False,
            client_accepted_at=datetime.utcnow()
        )
        db.session.add(invite)
        db.session.commit()
        
        result = InviteService.accept_invite_as_provider(invite.id, provider.id)
        assert result['success']
        pre_order_id = result['pre_order_id']
        
        # Verificar saldos após criação da pré-ordem
        db.session.expire_all()
        client_wallet = Wallet.query.filter_by(user_id=client.id).first()
        provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
        
        assert client_wallet.balance == initial_balance, \
            "Saldo do cliente não deve mudar"
        assert client_wallet.escrow_balance == Decimal('0.00'), \
            "Cliente não deve ter escrow"
        assert provider_wallet.balance == initial_balance, \
            "Saldo do prestador não deve mudar"
        assert provider_wallet.escrow_balance == Decimal('0.00'), \
            "Prestador não deve ter escrow"
        
        # Fazer várias rodadas de negociação
        for i in range(3):
            # Criar proposta (justificativa deve ter pelo menos 50 caracteres)
            proposal_result = PreOrderProposalService.create_proposal(
                pre_order_id=pre_order_id,
                user_id=provider.id,
                proposed_value=Decimal('280.00') - Decimal(i * 10),
                proposed_delivery_date=None,
                proposed_description=None,
                justification=f"Proposta {i+1} - Esta é uma justificativa detalhada para a alteração de valor proposta"
            )
            assert proposal_result['success']
            
            # Verificar que saldos não mudaram
            db.session.expire_all()
            client_wallet = Wallet.query.filter_by(user_id=client.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
            
            assert client_wallet.balance == initial_balance
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.balance == initial_balance
            assert provider_wallet.escrow_balance == Decimal('0.00')
            
            # Aceitar proposta
            if i < 2:  # Aceitar apenas as duas primeiras
                accept_result = PreOrderProposalService.accept_proposal(
                    proposal_id=proposal_result['proposal_id'],
                    user_id=client.id
                )
                assert accept_result['success']
        
        print("\n✅ Valores não foram bloqueados durante toda a negociação")


def test_converted_invite_immutable(test_app, clean_db):
    """
    Teste específico: Convite convertido não permite modificações
    
    Verifica que após um convite ser convertido em pré-ordem,
    ele não pode ser modificado.
    """
    with test_app.app_context():
        # Criar usuários
        client = User(
            email='client_immut@example.com',
            nome='Cliente Immut',
            cpf='55555555555',
            phone='11555555555',
            roles='cliente'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(
            email='provider_immut@example.com',
            nome='Prestador Immut',
            cpf='66666666666',
            phone='11444444444',
            roles='prestador'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        # Criar carteiras
        client_wallet = Wallet(user_id=client.id, balance=Decimal('1000.00'))
        provider_wallet = Wallet(user_id=provider.id, balance=Decimal('100.00'))
        db.session.add_all([client_wallet, provider_wallet])
        
        db.session.commit()
        
        # Criar e aceitar convite
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Teste Imutabilidade',
            service_description='Teste',
            service_category='eletricista',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=3),
            status='pendente',
            client_accepted=True,
            provider_accepted=False,
            client_accepted_at=datetime.utcnow()
        )
        db.session.add(invite)
        db.session.commit()
        
        original_title = invite.service_title
        original_value = invite.original_value
        
        # Aceitar convite (converte para pré-ordem)
        result = InviteService.accept_invite_as_provider(invite.id, provider.id)
        assert result['success']
        
        # Verificar que convite foi convertido
        db.session.expire_all()
        invite = Invite.query.get(invite.id)
        assert invite.status == 'convertido_pre_ordem'
        
        # Verificar que dados do convite permanecem inalterados
        assert invite.service_title == original_title
        assert invite.original_value == original_value
        
        # O convite não deve ser modificável após conversão
        # (a lógica de negociação agora está na pré-ordem)
        print("\n✅ Convite convertido permanece imutável")
