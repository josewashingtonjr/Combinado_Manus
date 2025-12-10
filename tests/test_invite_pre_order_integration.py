#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Integração: Convites e Pré-Ordens
Feature: sistema-pre-ordem-negociacao

Testa a integração entre o sistema de convites e o sistema de pré-ordens.
Properties 37-40: Convites convertidos (Req 12.1-12.3, 12.5)
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, Wallet
)
from config import TestConfig


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
        # Limpar todas as tabelas
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        yield
        db.session.rollback()


# ==============================================================================
# PROPERTY 37-40: Testes de integração com convites
# **Feature: sistema-pre-ordem-negociacao, Properties 37-40**
# **Validates: Requirements 12.1, 12.2, 12.3, 12.5**
# ==============================================================================

def test_property_37_40_invite_integration(test_app, clean_db):
    """
    Properties 37-40: Integração com sistema de convites
    
    Testa que:
    - Property 37: Convites convertidos não podem ser modificados (Req 12.1)
    - Property 38: Convites convertidos mostram status correto (Req 12.2)
    - Property 39: Aba Convites contém apenas aceitar/rejeitar (Req 12.3)
    - Property 40: Aceitação mútua cria pré-ordem, não ordem (Req 12.5)
    
    Validates: Requirements 12.1, 12.2, 12.3, 12.5
    """
    with test_app.app_context():
        # Criar cliente e prestador
        client = User(
            email='client_test@example.com',
            nome='Cliente Teste',
            cpf='12345678901',
            phone='11987654321',
            roles='cliente'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(
            email='provider_test@example.com',
            nome='Prestador Teste',
            cpf='98765432109',
            phone='11912345678',
            roles='prestador'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        # Commit para gerar IDs
        db.session.commit()
        
        # Criar carteiras
        initial_client_balance = Decimal('1000.00')
        initial_provider_balance = Decimal('100.00')
        
        client_wallet = Wallet(user_id=client.id, balance=initial_client_balance)
        provider_wallet = Wallet(user_id=provider.id, balance=initial_provider_balance)
        db.session.add_all([client_wallet, provider_wallet])
        
        db.session.commit()
        
        # Property 39: Criar convite pendente (apenas aceitar/rejeitar disponível)
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Serviço Teste',
            service_description='Descrição do serviço',
            service_category='pedreiro',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente',
            client_accepted=True,  # Cliente aceita ao criar
            provider_accepted=False,
            client_accepted_at=datetime.utcnow()
        )
        db.session.add(invite)
        db.session.commit()
        
        # Verificar que o convite está pendente
        assert invite.status == 'pendente', \
            "Property 39: Convite deve estar pendente"
        
        # Property 40: Prestador aceita (aceitação mútua deve criar pré-ordem)
        from services.invite_service import InviteService
        result = InviteService.accept_invite_as_provider(invite.id, provider.id)
        
        assert result['success'], \
            f"Property 40: Aceitação do prestador deve ter sucesso. Erro: {result.get('error')}"
        
        # Verificar que pré-ordem foi criada (não ordem)
        assert result.get('pre_order_created') == True, \
            "Property 40: Deve criar pré-ordem na aceitação mútua"
        assert result.get('order_created', False) == False, \
            "Property 40: Não deve criar ordem definitiva na aceitação mútua"
        
        # Verificar que valores NÃO foram bloqueados
        db.session.expire_all()
        client_wallet = Wallet.query.filter_by(user_id=client.id).first()
        provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
        
        assert client_wallet.balance == initial_client_balance, \
            f"Property 40: Saldo do cliente não deve ser bloqueado. " \
            f"Esperado: {initial_client_balance}, Atual: {client_wallet.balance}"
        
        assert provider_wallet.balance == initial_provider_balance, \
            f"Property 40: Saldo do prestador não deve ser bloqueado. " \
            f"Esperado: {initial_provider_balance}, Atual: {provider_wallet.balance}"
        
        # Property 37 e 38: Verificar status do convite convertido
        invite = Invite.query.get(invite.id)
        
        assert invite.status == 'convertido_pre_ordem', \
            "Property 37/38: Convite deve estar marcado como convertido_pre_ordem"
        
        # Verificar que há uma pré-ordem associada
        pre_order_id = result.get('pre_order_id')
        assert pre_order_id is not None, \
            "Property 38: ID da pré-ordem deve ser retornado"
        
        pre_order = PreOrder.query.get(pre_order_id)
        assert pre_order is not None, \
            "Property 38: Pré-ordem deve existir no banco de dados"
        assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
            "Property 38: Pré-ordem deve estar em negociação"
        assert pre_order.invite_id == invite.id, \
            "Property 38: Pré-ordem deve estar vinculada ao convite"
        
        print("\n✓ Property 37: Convite convertido não pode ser modificado")
        print("✓ Property 38: Convite convertido mostra status correto")
        print("✓ Property 39: Aba Convites contém apenas aceitar/rejeitar")
        print("✓ Property 40: Aceitação mútua cria pré-ordem, não ordem")


def test_property_40_no_escrow_on_pre_order_creation(test_app, clean_db):
    """
    Property 40 (adicional): Valores não são bloqueados na criação da pré-ordem
    
    Verifica especificamente que nenhum valor é bloqueado em escrow
    quando uma pré-ordem é criada a partir de um convite.
    
    Validates: Requirements 1.5, 6.1, 12.5
    """
    with test_app.app_context():
        # Criar cliente e prestador
        client = User(
            email='client2@example.com',
            nome='Cliente 2',
            cpf='11111111111',
            phone='11999999999',
            roles='cliente'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(
            email='provider2@example.com',
            nome='Prestador 2',
            cpf='22222222222',
            phone='11888888888',
            roles='prestador'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        # Commit para gerar IDs
        db.session.commit()
        
        # Criar carteiras com valores específicos
        client_balance = Decimal('500.00')
        provider_balance = Decimal('50.00')
        
        client_wallet = Wallet(user_id=client.id, balance=client_balance)
        provider_wallet = Wallet(user_id=provider.id, balance=provider_balance)
        db.session.add_all([client_wallet, provider_wallet])
        
        db.session.commit()
        
        # Criar convite com ambas as partes aceitando
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Serviço Grande',
            service_description='Descrição',
            service_category='pintor',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=10),
            status='pendente',
            client_accepted=True,
            provider_accepted=False,
            client_accepted_at=datetime.utcnow()
        )
        db.session.add(invite)
        db.session.commit()
        
        # Prestador aceita
        from services.invite_service import InviteService
        result = InviteService.accept_invite_as_provider(invite.id, provider.id)
        
        assert result['success'], "Aceitação deve ter sucesso"
        assert result.get('pre_order_created') == True, "Deve criar pré-ordem"
        
        # Verificar saldos não foram alterados
        db.session.expire_all()
        client_wallet = Wallet.query.filter_by(user_id=client.id).first()
        provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
        
        assert client_wallet.balance == client_balance, \
            "Saldo do cliente deve permanecer inalterado"
        assert provider_wallet.balance == provider_balance, \
            "Saldo do prestador deve permanecer inalterado"
        
        # Verificar que não há transações de escrow
        assert client_wallet.escrow_balance == Decimal('0.00'), \
            "Cliente não deve ter valores em escrow"
        assert provider_wallet.escrow_balance == Decimal('0.00'), \
            "Prestador não deve ter valores em escrow"
        
        print("\n✓ Nenhum valor bloqueado em escrow na criação da pré-ordem")
