#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para Validação de Saldo em Pré-Ordens
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
propriedades de validação de saldo ao aceitar termos de pré-ordens.

Properties 21-22: Mensagens e fluxo de saldo (Req 7.2-7.4)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, Wallet
)
from services.pre_order_service import PreOrderService
from services.config_service import ConfigService
from services.wallet_service import WalletService
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


def get_clean_db_session(app):
    """Retorna uma sessão limpa do banco de dados"""
    with app.app_context():
        from models import PreOrderHistory, PreOrderProposal
        # Limpar todas as tabelas relacionadas
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrderProposal).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


def create_test_pre_order(session, client_balance, provider_balance, service_value):
    """
    Helper para criar uma pré-ordem de teste com saldos específicos
    
    Args:
        session: Sessão do banco de dados
        client_balance: Saldo inicial do cliente
        provider_balance: Saldo inicial do prestador
        service_value: Valor do serviço
        
    Returns:
        tuple: (pre_order, client, provider, client_wallet, provider_wallet)
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # Criar cliente
    client = User(
        email=f'cliente_{unique_id}@test.com',
        nome=f'Cliente {unique_id}',
        cpf=f'{hash(unique_id) % 10**11:011d}',
        phone=f'119{hash(unique_id) % 10**8:08d}',
        roles='cliente'
    )
    client.set_password('senha123')
    session.add(client)
    session.flush()
    
    # Criar carteira do cliente
    client_wallet = Wallet(
        user_id=client.id,
        balance=client_balance,
        escrow_balance=Decimal('0.00')
    )
    session.add(client_wallet)
    
    # Criar prestador
    provider = User(
        email=f'prestador_{unique_id}@test.com',
        nome=f'Prestador {unique_id}',
        cpf=f'{(hash(unique_id) + 1) % 10**11:011d}',
        phone=f'118{hash(unique_id) % 10**8:08d}',
        roles='prestador'
    )
    provider.set_password('senha123')
    session.add(provider)
    session.flush()
    
    # Criar carteira do prestador
    provider_wallet = Wallet(
        user_id=provider.id,
        balance=provider_balance,
        escrow_balance=Decimal('0.00')
    )
    session.add(provider_wallet)
    
    # Criar convite
    invite = Invite(
        client_id=client.id,
        invited_phone=provider.phone,
        service_title=f'Serviço {unique_id}',
        service_description='Descrição do serviço de teste',
        original_value=service_value,
        delivery_date=datetime.utcnow() + timedelta(days=15),
        status='aceito',
        expires_at=datetime.utcnow() + timedelta(days=15)
    )
    session.add(invite)
    session.flush()
    
    # Criar pré-ordem
    pre_order = PreOrder(
        invite_id=invite.id,
        client_id=client.id,
        provider_id=provider.id,
        title=invite.service_title,
        description=invite.service_description,
        current_value=service_value,
        original_value=service_value,
        delivery_date=invite.delivery_date,
        status=PreOrderStatus.EM_NEGOCIACAO.value,
        expires_at=datetime.utcnow() + timedelta(days=7),
        client_accepted_terms=False,
        provider_accepted_terms=False,
        has_active_proposal=False
    )
    session.add(pre_order)
    session.commit()
    
    return pre_order, client, provider, client_wallet, provider_wallet


# ==============================================================================
# PROPERTY 21: Mensagem clara de saldo insuficiente
# **Feature: sistema-pre-ordem-negociacao, Property 21: Mensagem clara de saldo insuficiente**
# **Validates: Requirements 7.2**
# ==============================================================================

@given(
    service_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2),
    client_balance_factor=st.floats(min_value=0.0, max_value=0.9)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_21_insufficient_balance_message(
    test_app, service_value, client_balance_factor
):
    """
    Property 21: Mensagem clara de saldo insuficiente
    
    Para qualquer tentativa de aceitar termos com saldo insuficiente:
    - O sistema deve retornar uma mensagem clara indicando o problema
    - A mensagem deve incluir o valor necessário
    - A mensagem deve incluir o saldo atual
    - A mensagem deve incluir quanto falta (shortfall)
    - O aceite deve ser bloqueado
    
    Validates: Requirements 7.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Obter taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            
            # Calcular valor necessário para o cliente
            required_amount = service_value + contestation_fee
            
            # Definir saldo insuficiente (fração do necessário)
            client_balance = Decimal(str(float(required_amount) * client_balance_factor))
            
            # Garantir que o saldo é realmente insuficiente
            assume(client_balance < required_amount)
            
            # Prestador com saldo suficiente
            provider_balance = contestation_fee + Decimal('100.00')
            
            # Criar pré-ordem
            pre_order, client, provider, client_wallet, provider_wallet = create_test_pre_order(
                session, client_balance, provider_balance, service_value
            )
            
            # Tentar aceitar termos como cliente
            result = PreOrderService.accept_terms(
                pre_order_id=pre_order.id,
                user_id=client.id
            )
            
            # Verificar propriedades
            assert result['success'] == False, \
                "Aceite deve falhar com saldo insuficiente"
            assert result['error'] == 'Saldo insuficiente', \
                "Erro deve indicar saldo insuficiente"
            assert 'required_amount' in result, \
                "Resultado deve incluir valor necessário"
            assert 'current_balance' in result, \
                "Resultado deve incluir saldo atual"
            assert 'shortfall' in result, \
                "Resultado deve incluir quanto falta"
            assert 'message' in result, \
                "Resultado deve incluir mensagem explicativa"
            
            # Verificar valores (com tolerância para arredondamento)
            result_required = Decimal(str(result['required_amount']))
            result_balance = Decimal(str(result['current_balance']))
            result_shortfall = Decimal(str(result['shortfall']))
            
            # Usar tolerância de 0.01 para comparações
            tolerance = Decimal('0.01')
            
            assert abs(result_required - required_amount) <= tolerance, \
                f"Valor necessário deve ser correto. Esperado: {required_amount}, Obtido: {result_required}"
            assert abs(result_balance - client_balance) <= tolerance, \
                f"Saldo atual deve ser correto. Esperado: {client_balance}, Obtido: {result_balance}"
            
            expected_shortfall = required_amount - client_balance
            assert abs(result_shortfall - expected_shortfall) <= tolerance, \
                f"Shortfall deve ser a diferença. Esperado: {expected_shortfall}, Obtido: {result_shortfall}"
            
            # Verificar que a mensagem contém informações úteis
            message = result['message']
            assert 'insuficiente' in message.lower() or 'saldo' in message.lower(), \
                "Mensagem deve mencionar saldo insuficiente"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 22: Fluxo de adição de saldo permite aceite
# **Feature: sistema-pre-ordem-negociacao, Property 22: Fluxo de adição de saldo permite aceite**
# **Validates: Requirements 7.3, 7.4**
# ==============================================================================

@given(
    service_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2),
    initial_balance_factor=st.floats(min_value=0.0, max_value=0.5)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_22_add_balance_enables_acceptance(
    test_app, service_value, initial_balance_factor
):
    """
    Property 22: Fluxo de adição de saldo permite aceite
    
    Para qualquer usuário com saldo insuficiente:
    - Após adicionar saldo suficiente, o aceite deve ser permitido
    - O valor sugerido para adição deve ser pelo menos o shortfall
    - Após adicionar o valor sugerido, o aceite deve ter sucesso
    
    Validates: Requirements 7.3, 7.4
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Obter taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            
            # Calcular valor necessário para o cliente
            required_amount = service_value + contestation_fee
            
            # Definir saldo inicial insuficiente
            initial_balance = Decimal(str(float(required_amount) * initial_balance_factor))
            
            # Garantir que o saldo inicial é insuficiente
            assume(initial_balance < required_amount)
            
            # Prestador com saldo suficiente
            provider_balance = contestation_fee + Decimal('100.00')
            
            # Criar pré-ordem
            pre_order, client, provider, client_wallet, provider_wallet = create_test_pre_order(
                session, initial_balance, provider_balance, service_value
            )
            
            # Primeira tentativa - deve falhar
            result_before = PreOrderService.accept_terms(
                pre_order_id=pre_order.id,
                user_id=client.id
            )
            
            assert result_before['success'] == False, \
                "Primeira tentativa deve falhar com saldo insuficiente"
            
            # Obter valor que falta
            shortfall = Decimal(str(result_before['shortfall']))
            
            # Adicionar saldo suficiente (shortfall + margem)
            amount_to_add = shortfall + Decimal('1.00')  # Margem de segurança
            
            # Simular adição de saldo
            client_wallet.balance += amount_to_add
            session.commit()
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            # Segunda tentativa - deve ter sucesso
            result_after = PreOrderService.accept_terms(
                pre_order_id=pre_order.id,
                user_id=client.id
            )
            
            # Verificar propriedades
            assert result_after['success'] == True, \
                f"Após adicionar saldo, aceite deve ter sucesso. Erro: {result_after.get('error', 'N/A')}"
            assert result_after['client_accepted'] == True, \
                "Cliente deve ter aceitação registrada"
            assert 'message' in result_after, \
                "Resultado deve incluir mensagem de sucesso"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 21b: Mensagem clara para prestador com saldo insuficiente
# **Feature: sistema-pre-ordem-negociacao, Property 21b: Mensagem para prestador**
# **Validates: Requirements 7.2**
# ==============================================================================

@given(
    service_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2),
    provider_balance_factor=st.floats(min_value=0.0, max_value=0.9)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_21b_provider_insufficient_balance_message(
    test_app, service_value, provider_balance_factor
):
    """
    Property 21b: Mensagem clara de saldo insuficiente para prestador
    
    Para qualquer tentativa do prestador aceitar termos com saldo insuficiente:
    - O sistema deve retornar uma mensagem clara indicando o problema
    - A mensagem deve incluir o valor necessário (taxa de contestação)
    - A mensagem deve incluir o saldo atual
    - A mensagem deve incluir quanto falta (shortfall)
    - O aceite deve ser bloqueado
    
    Validates: Requirements 7.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Obter taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            
            # Prestador precisa apenas da taxa de contestação
            required_amount = contestation_fee
            
            # Definir saldo insuficiente para prestador
            provider_balance = Decimal(str(float(required_amount) * provider_balance_factor))
            
            # Garantir que o saldo é realmente insuficiente
            assume(provider_balance < required_amount)
            
            # Cliente com saldo suficiente
            client_balance = service_value + contestation_fee + Decimal('100.00')
            
            # Criar pré-ordem
            pre_order, client, provider, client_wallet, provider_wallet = create_test_pre_order(
                session, client_balance, provider_balance, service_value
            )
            
            # Tentar aceitar termos como prestador
            result = PreOrderService.accept_terms(
                pre_order_id=pre_order.id,
                user_id=provider.id
            )
            
            # Verificar propriedades
            assert result['success'] == False, \
                "Aceite deve falhar com saldo insuficiente"
            assert result['error'] == 'Saldo insuficiente', \
                "Erro deve indicar saldo insuficiente"
            assert 'required_amount' in result, \
                "Resultado deve incluir valor necessário"
            assert 'current_balance' in result, \
                "Resultado deve incluir saldo atual"
            assert 'shortfall' in result, \
                "Resultado deve incluir quanto falta"
            
            # Verificar que o valor necessário é apenas a taxa de contestação
            assert Decimal(str(result['required_amount'])) == contestation_fee, \
                "Prestador precisa apenas da taxa de contestação"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 22b: Verificação de saldo via endpoint
# **Feature: sistema-pre-ordem-negociacao, Property 22b: Endpoint de verificação**
# **Validates: Requirements 7.1, 7.2**
# ==============================================================================

@given(
    service_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2),
    balance_sufficient=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_22b_balance_check_endpoint_consistency(
    test_app, service_value, balance_sufficient
):
    """
    Property 22b: Consistência do endpoint de verificação de saldo
    
    Para qualquer pré-ordem e usuário:
    - O endpoint de verificação deve retornar is_sufficient corretamente
    - Se is_sufficient=True, o aceite deve ter sucesso
    - Se is_sufficient=False, o aceite deve falhar
    - Os valores retornados devem ser consistentes
    
    Validates: Requirements 7.1, 7.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Obter taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            
            # Calcular valor necessário para o cliente
            required_amount = service_value + contestation_fee
            
            # Definir saldo baseado no parâmetro
            if balance_sufficient:
                client_balance = required_amount + Decimal('100.00')
            else:
                client_balance = required_amount - Decimal('10.00')
                # Garantir que é positivo
                if client_balance < Decimal('0.00'):
                    client_balance = Decimal('0.00')
            
            # Prestador com saldo suficiente
            provider_balance = contestation_fee + Decimal('100.00')
            
            # Criar pré-ordem
            pre_order, client, provider, client_wallet, provider_wallet = create_test_pre_order(
                session, client_balance, provider_balance, service_value
            )
            
            # Verificar saldo manualmente (simulando o endpoint)
            wallet_info = WalletService.get_wallet_info(client.id)
            current_balance = Decimal(str(wallet_info['balance']))
            is_sufficient = current_balance >= required_amount
            
            # Verificar consistência
            assert is_sufficient == balance_sufficient, \
                f"Verificação de saldo deve ser consistente. " \
                f"Esperado: {balance_sufficient}, Obtido: {is_sufficient}"
            
            # Tentar aceitar termos
            result = PreOrderService.accept_terms(
                pre_order_id=pre_order.id,
                user_id=client.id
            )
            
            # Verificar que o resultado é consistente com a verificação
            if is_sufficient:
                assert result['success'] == True, \
                    "Com saldo suficiente, aceite deve ter sucesso"
            else:
                assert result['success'] == False, \
                    "Com saldo insuficiente, aceite deve falhar"
                assert result['error'] == 'Saldo insuficiente', \
                    "Erro deve indicar saldo insuficiente"
                    
        finally:
            session.rollback()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
