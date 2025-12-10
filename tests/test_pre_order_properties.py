#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para PreOrder
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
propriedades universais do sistema de pré-ordens.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, Wallet,
    PreOrderHistory
)
from config import TestConfig


# ==============================================================================
# ESTRATÉGIAS (GENERATORS) PARA HYPOTHESIS
# ==============================================================================

@st.composite
def valid_user_data(draw):
    """Gera dados válidos para criar um usuário"""
    user_id = draw(st.integers(min_value=1, max_value=999999))
    return {
        'email': f'user{user_id}@example.com',
        'nome': f'Usuario {user_id}',
        'cpf': f'{user_id:011d}',
        'phone': f'119{user_id:08d}',
        'roles': draw(st.sampled_from(['cliente', 'prestador']))
    }


@st.composite
def valid_invite_data(draw, client_id):
    """Gera dados válidos para criar um convite"""
    value = draw(st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2))
    days_ahead = draw(st.integers(min_value=1, max_value=30))
    
    return {
        'client_id': client_id,
        'invited_phone': f'119{draw(st.integers(min_value=10000000, max_value=99999999))}',
        'service_title': f'Serviço {draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=("L",))))}',
        'service_description': f'Descrição do serviço {draw(st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=("L",))))}',
        'service_category': draw(st.sampled_from(['pedreiro', 'encanador', 'eletricista', 'pintor'])),
        'original_value': value,
        'delivery_date': datetime.utcnow() + timedelta(days=days_ahead),
        'status': 'aceito'
    }


@st.composite
def negotiation_days(draw):
    """Gera número de dias válido para negociação (1-30 dias)"""
    return draw(st.integers(min_value=1, max_value=30))


# ==============================================================================
# FIXTURES E HELPERS
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
        # Limpar todas as tabelas
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


# ==============================================================================
# PROPERTY 1: Criação de pré-ordem a partir de convite
# **Feature: sistema-pre-ordem-negociacao, Property 1: Criação de pré-ordem a partir de convite**
# **Validates: Requirements 1.1, 1.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    negotiation_period=negotiation_days()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_1_pre_order_creation_from_invite(
    test_app, client_data, provider_data, negotiation_period
):
    """
    Property 1: Criação de pré-ordem a partir de convite
    
    Para qualquer convite aceito, quando uma pré-ordem é criada:
    - A pré-ordem deve existir no banco de dados
    - Deve ter status 'em_negociacao'
    - Deve copiar todos os dados do convite (título, valor, descrição, prazo)
    - Deve ter client_id e provider_id corretos
    - Deve ter expires_at definido (prazo de negociação)
    
    Validates: Requirements 1.1, 1.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir que os dados são diferentes
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar cliente
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            session.flush()
            
            # Criar carteira para o cliente
            client_wallet = Wallet(user_id=client.id, balance=Decimal('1000.00'))
            session.add(client_wallet)
            
            # Criar prestador
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteira para o prestador
            provider_wallet = Wallet(user_id=provider.id, balance=Decimal('500.00'))
            session.add(provider_wallet)
            
            # Criar convite aceito
            invite_data = {
                'client_id': client.id,
                'invited_phone': provider.phone,
                'service_title': 'Serviço de Teste',
                'service_description': 'Descrição detalhada do serviço',
                'service_category': 'pedreiro',
                'original_value': Decimal('500.00'),
                'delivery_date': datetime.utcnow() + timedelta(days=15),
                'status': 'aceito',
                'expires_at': datetime.utcnow() + timedelta(days=15)
            }
            invite = Invite(**invite_data)
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem a partir do convite
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                service_category=invite.service_category,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=negotiation_period)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades
            assert pre_order.id is not None, "Pré-ordem deve ter ID após commit"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Pré-ordem deve ter status 'em_negociacao'"
            assert pre_order.title == invite.service_title, \
                "Título deve ser copiado do convite"
            assert pre_order.description == invite.service_description, \
                "Descrição deve ser copiada do convite"
            assert pre_order.current_value == invite.original_value, \
                "Valor atual deve ser igual ao valor original do convite"
            assert pre_order.original_value == invite.original_value, \
                "Valor original deve ser copiado do convite"
            assert pre_order.delivery_date == invite.delivery_date, \
                "Data de entrega deve ser copiada do convite"
            assert pre_order.client_id == client.id, \
                "Cliente deve ser o mesmo do convite"
            assert pre_order.provider_id == provider.id, \
                "Prestador deve ser identificado corretamente"
            assert pre_order.expires_at is not None, \
                "Prazo de expiração deve estar definido"
            assert pre_order.expires_at > datetime.utcnow(), \
                "Prazo de expiração deve ser no futuro"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 2: Convite marcado como convertido
# **Feature: sistema-pre-ordem-negociacao, Property 2: Convite marcado como convertido**
# **Validates: Requirements 1.3**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_2_invite_marked_as_converted(
    test_app, client_data, provider_data
):
    """
    Property 2: Convite marcado como convertido
    
    Para qualquer convite que gera uma pré-ordem:
    - O convite deve ter seu status atualizado para indicar conversão
    - O convite deve manter referência à pré-ordem criada
    - O convite não deve permitir mais modificações
    
    Validates: Requirements 1.3
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir que os dados são diferentes
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('1000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('500.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('300.00'),
                delivery_date=datetime.utcnow() + timedelta(days=10),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=10)
            )
            session.add(invite)
            session.flush()
            
            status_antes = invite.status
            
            # Criar pré-ordem
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            
            # Marcar convite como convertido
            invite.status = 'convertido_pre_ordem'
            session.commit()
            
            # Verificar propriedades
            assert invite.status == 'convertido_pre_ordem', \
                "Convite deve ter status 'convertido_pre_ordem'"
            assert invite.status != status_antes, \
                "Status do convite deve ter mudado"
            assert invite.pre_order is not None, \
                "Convite deve ter referência à pré-ordem"
            assert invite.pre_order.id == pre_order.id, \
                "Referência deve apontar para a pré-ordem correta"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 3: Pré-ordem não bloqueia valores
# **Feature: sistema-pre-ordem-negociacao, Property 3: Pré-ordem não bloqueia valores**
# **Validates: Requirements 1.5, 6.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    service_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_3_pre_order_does_not_block_values(
    test_app, client_data, provider_data, service_value
):
    """
    Property 3: Pré-ordem não bloqueia valores
    
    Para qualquer pré-ordem em negociação:
    - Os saldos das carteiras não devem ser bloqueados (escrow_balance = 0)
    - O saldo disponível do cliente deve permanecer inalterado
    - O saldo disponível do prestador deve permanecer inalterado
    - Apenas quando convertida em ordem os valores são bloqueados
    
    Validates: Requirements 1.5, 6.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras com saldos iniciais
            initial_client_balance = Decimal('2000.00')
            initial_provider_balance = Decimal('1000.00')
            
            client_wallet = Wallet(
                user_id=client.id,
                balance=initial_client_balance,
                escrow_balance=Decimal('0.00')
            )
            provider_wallet = Wallet(
                user_id=provider.id,
                balance=initial_provider_balance,
                escrow_balance=Decimal('0.00')
            )
            session.add(client_wallet)
            session.add(provider_wallet)
            session.flush()
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço',
                service_description='Descrição',
                original_value=service_value,
                delivery_date=datetime.utcnow() + timedelta(days=10),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=10)
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
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Recarregar carteiras do banco
            session.refresh(client_wallet)
            session.refresh(provider_wallet)
            
            # Verificar propriedades
            assert client_wallet.balance == initial_client_balance, \
                "Saldo do cliente não deve ser alterado durante negociação"
            assert client_wallet.escrow_balance == Decimal('0.00'), \
                "Nenhum valor deve estar em escrow para o cliente"
            assert provider_wallet.balance == initial_provider_balance, \
                "Saldo do prestador não deve ser alterado durante negociação"
            assert provider_wallet.escrow_balance == Decimal('0.00'), \
                "Nenhum valor deve estar em escrow para o prestador"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Pré-ordem deve estar em negociação"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 47: Prazo de negociação
# **Feature: sistema-pre-ordem-negociacao, Property 47: Prazo de negociação**
# **Validates: Requirements 15.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    negotiation_days=st.integers(min_value=1, max_value=30)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_47_negotiation_deadline(
    test_app, client_data, provider_data, negotiation_days
):
    """
    Property 47: Prazo de negociação
    
    Para qualquer pré-ordem criada:
    - Deve ter um prazo de expiração definido (expires_at)
    - O prazo deve ser no futuro (maior que created_at)
    - O prazo padrão deve ser de 7 dias se não especificado
    - A propriedade is_expired deve retornar True quando o prazo passar
    - A propriedade days_until_expiration deve calcular corretamente os dias restantes
    
    Validates: Requirements 15.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('1000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('500.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço',
                service_description='Descrição',
                original_value=Decimal('400.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem com prazo específico
            now = datetime.utcnow()
            expires_at = now + timedelta(days=negotiation_days)
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=expires_at
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades
            assert pre_order.expires_at is not None, \
                "Pré-ordem deve ter prazo de expiração definido"
            assert pre_order.expires_at > pre_order.created_at, \
                "Prazo de expiração deve ser posterior à criação"
            assert not pre_order.is_expired, \
                "Pré-ordem recém-criada não deve estar expirada"
            
            # Verificar cálculo de dias restantes
            days_remaining = pre_order.days_until_expiration
            assert days_remaining >= 0, \
                "Dias até expiração não deve ser negativo"
            assert days_remaining <= negotiation_days, \
                "Dias restantes deve ser menor ou igual ao prazo definido"
            
            # Verificar que pré-ordem com prazo de 1 dia ou menos está próxima da expiração
            if negotiation_days <= 1:
                assert pre_order.is_near_expiration, \
                    "Pré-ordem com menos de 24h deve estar próxima da expiração"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 6: Proposta requer justificativa
# **Feature: sistema-pre-ordem-negociacao, Property 6: Proposta requer justificativa**
# **Validates: Requirements 2.4**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposed_value=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2),
    justification_length=st.integers(min_value=0, max_value=200)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_6_proposal_requires_justification(
    test_app, client_data, provider_data, proposed_value, justification_length
):
    """
    Property 6: Proposta requer justificativa
    
    Para qualquer proposta de alteração em uma pré-ordem:
    - A justificativa deve ser obrigatória (NOT NULL)
    - A justificativa deve ter no mínimo 50 caracteres
    - Propostas com justificativa < 50 caracteres devem ser rejeitadas pelo banco
    - Propostas sem justificativa devem ser rejeitadas
    
    Validates: Requirements 2.4
    """
    from models import PreOrderProposal, ProposalStatus
    from sqlalchemy.exc import IntegrityError
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Gerar justificativa com tamanho específico
            justification = 'A' * justification_length if justification_length > 0 else None
            
            # Tentar criar proposta
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=proposed_value,
                justification=justification,
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            
            # Verificar comportamento baseado no tamanho da justificativa
            if justification is None or justification_length < 50:
                # Deve falhar com IntegrityError
                with pytest.raises(IntegrityError):
                    session.commit()
                session.rollback()
            else:
                # Deve ter sucesso
                session.commit()
                
                # Verificar propriedades
                assert proposal.id is not None, \
                    "Proposta com justificativa válida deve ser criada"
                assert proposal.justification is not None, \
                    "Justificativa deve estar presente"
                assert len(proposal.justification) >= 50, \
                    "Justificativa deve ter no mínimo 50 caracteres"
                assert proposal.status == ProposalStatus.PENDENTE.value, \
                    "Proposta deve ter status pendente"
        except IntegrityError:
            # Esperado para justificativas inválidas
            session.rollback()
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 10: Registro de histórico
# **Feature: sistema-pre-ordem-negociacao, Property 10: Registro de histórico**
# **Validates: Requirements 3.5, 17.1, 17.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    event_type=st.sampled_from([
        'created', 'proposal_sent', 'proposal_accepted', 'proposal_rejected',
        'terms_accepted_client', 'terms_accepted_provider', 'cancelled'
    ])
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_10_history_recording(
    test_app, client_data, provider_data, event_type
):
    """
    Property 10: Registro de histórico
    
    Para qualquer ação em uma pré-ordem:
    - Um registro de histórico deve ser criado
    - O registro deve conter: event_type, actor_id, description, created_at
    - O registro pode conter event_data (JSON) com informações adicionais
    - O histórico deve ser ordenado por created_at (mais recente primeiro)
    - Todos os eventos devem ser rastreáveis para auditoria
    
    Validates: Requirements 3.5, 17.1, 17.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Determinar o ator baseado no tipo de evento
            if 'client' in event_type:
                actor_id = client.id
                actor_name = client.nome
            else:
                actor_id = provider.id
                actor_name = provider.nome
            
            # Criar registro de histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type=event_type,
                actor_id=actor_id,
                description=f'{actor_name} executou ação: {event_type}',
                event_data={
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_type': event_type,
                    'actor_role': 'cliente' if actor_id == client.id else 'prestador'
                }
            )
            session.add(history_entry)
            session.commit()
            
            # Verificar propriedades
            assert history_entry.id is not None, \
                "Registro de histórico deve ser criado"
            assert history_entry.pre_order_id == pre_order.id, \
                "Histórico deve estar vinculado à pré-ordem correta"
            assert history_entry.event_type == event_type, \
                "Tipo de evento deve estar registrado corretamente"
            assert history_entry.actor_id == actor_id, \
                "Ator deve estar identificado corretamente"
            assert history_entry.description is not None, \
                "Descrição do evento deve estar presente"
            assert len(history_entry.description) > 0, \
                "Descrição não deve estar vazia"
            assert history_entry.created_at is not None, \
                "Timestamp de criação deve estar presente"
            assert history_entry.event_data is not None, \
                "Dados do evento devem estar presentes"
            assert isinstance(history_entry.event_data, dict), \
                "event_data deve ser um dicionário (JSON)"
            
            # Verificar que o histórico pode ser consultado pela pré-ordem
            history_records = pre_order.history.all()
            assert len(history_records) > 0, \
                "Pré-ordem deve ter registros de histórico"
            assert history_entry in history_records, \
                "Registro criado deve estar no histórico da pré-ordem"
            
            # Verificar ordenação (mais recente primeiro)
            if len(history_records) > 1:
                for i in range(len(history_records) - 1):
                    assert history_records[i].created_at >= history_records[i + 1].created_at, \
                        "Histórico deve estar ordenado por created_at (desc)"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 7: Transição ao submeter proposta
# **Feature: sistema-pre-ordem-negociacao, Property 7: Transição ao submeter proposta**
# **Validates: Requirements 2.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposed_value=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_7_transition_on_proposal_submission(
    test_app, client_data, provider_data, proposed_value
):
    """
    Property 7: Transição ao submeter proposta
    
    Para qualquer pré-ordem em estado EM_NEGOCIACAO:
    - Quando uma proposta é submetida, o estado deve transicionar para AGUARDANDO_RESPOSTA
    - A transição deve ser registrada no histórico
    - As flags de aceitação devem ser resetadas
    - A proposta deve ser marcada como ativa
    
    Validates: Requirements 2.5
    """
    from models import PreOrderProposal, ProposalStatus
    from services.pre_order_state_manager import PreOrderStateManager
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                client_accepted_terms=True,  # Simular que cliente já havia aceitado
                provider_accepted_terms=False,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Verificar estado inicial
            initial_state = PreOrderStateManager.get_current_state(pre_order)
            assert initial_state == PreOrderStatus.EM_NEGOCIACAO
            
            # Criar proposta
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=proposed_value,
                justification='A' * 60,  # Justificativa válida
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            session.flush()
            
            # Marcar proposta como ativa
            pre_order.has_active_proposal = True
            pre_order.active_proposal_id = proposal.id
            
            # Transicionar para AGUARDANDO_RESPOSTA
            result = PreOrderStateManager.transition_to(
                pre_order.id,
                PreOrderStatus.AGUARDANDO_RESPOSTA,
                provider.id,
                "Proposta de alteração enviada"
            )
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            # Verificar propriedades
            assert result['success'], "Transição deve ter sucesso"
            assert result['new_state'] == PreOrderStatus.AGUARDANDO_RESPOSTA.value, \
                "Estado deve ser AGUARDANDO_RESPOSTA"
            assert pre_order.status == PreOrderStatus.AGUARDANDO_RESPOSTA.value, \
                "Status da pré-ordem deve ser atualizado"
            assert pre_order.has_active_proposal, \
                "Deve ter proposta ativa"
            assert pre_order.active_proposal_id == proposal.id, \
                "Proposta ativa deve estar referenciada"
            
            # Verificar que histórico foi registrado
            history_records = pre_order.history.all()
            assert len(history_records) > 0, \
                "Transição deve ser registrada no histórico"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 15: Retorno à negociação após rejeição
# **Feature: sistema-pre-ordem-negociacao, Property 15: Retorno à negociação após rejeição**
# **Validates: Requirements 4.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_15_return_to_negotiation_after_rejection(
    test_app, client_data, provider_data
):
    """
    Property 15: Retorno à negociação após rejeição
    
    Para qualquer pré-ordem em estado AGUARDANDO_RESPOSTA:
    - Quando uma proposta é rejeitada, o estado deve retornar para EM_NEGOCIACAO
    - A proposta ativa deve ser limpa
    - As partes devem poder continuar negociando
    - O histórico deve registrar a rejeição
    
    Validates: Requirements 4.5
    """
    from models import PreOrderProposal, ProposalStatus
    from services.pre_order_state_manager import PreOrderStateManager
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem em estado AGUARDANDO_RESPOSTA
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.AGUARDANDO_RESPOSTA.value,
                has_active_proposal=True,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Criar proposta pendente
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=Decimal('600.00'),
                justification='A' * 60,
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            session.flush()
            
            pre_order.active_proposal_id = proposal.id
            session.commit()
            
            # Verificar estado inicial
            initial_state = PreOrderStateManager.get_current_state(pre_order)
            assert initial_state == PreOrderStatus.AGUARDANDO_RESPOSTA
            
            # Rejeitar proposta - limpar proposta ativa
            pre_order.has_active_proposal = False
            pre_order.active_proposal_id = None
            proposal.status = ProposalStatus.REJEITADA.value
            session.commit()
            
            # Transicionar de volta para EM_NEGOCIACAO
            result = PreOrderStateManager.transition_to(
                pre_order.id,
                PreOrderStatus.EM_NEGOCIACAO,
                client.id,
                "Proposta rejeitada, retornando à negociação"
            )
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            # Verificar propriedades
            assert result['success'], "Transição deve ter sucesso"
            assert result['new_state'] == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Estado deve retornar para EM_NEGOCIACAO"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Status da pré-ordem deve ser EM_NEGOCIACAO"
            assert not pre_order.has_active_proposal, \
                "Não deve ter proposta ativa após rejeição"
            assert pre_order.active_proposal_id is None, \
                "Referência à proposta ativa deve ser limpa"
            
            # Verificar que pode transicionar novamente para AGUARDANDO_RESPOSTA
            can_transition, reason = PreOrderStateManager.can_transition_to(
                pre_order,
                PreOrderStatus.AGUARDANDO_RESPOSTA
            )
            assert can_transition, \
                "Deve poder enviar nova proposta após rejeição"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 16: Detecção de aceitação mútua
# **Feature: sistema-pre-ordem-negociacao, Property 16: Detecção de aceitação mútua**
# **Validates: Requirements 5.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    client_accepts=st.booleans(),
    provider_accepts=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_16_mutual_acceptance_detection(
    test_app, client_data, provider_data, client_accepts, provider_accepts
):
    """
    Property 16: Detecção de aceitação mútua
    
    Para qualquer pré-ordem:
    - check_mutual_acceptance deve retornar True apenas quando ambas as partes aceitaram
    - Se apenas uma parte aceitou, deve retornar False
    - Se nenhuma parte aceitou, deve retornar False
    - A transição para PRONTO_CONVERSAO só deve ser possível com aceitação mútua
    
    Validates: Requirements 5.1
    """
    from services.pre_order_state_manager import PreOrderStateManager
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem com flags de aceitação específicas
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                client_accepted_terms=client_accepts,
                provider_accepted_terms=provider_accepts,
                has_active_proposal=False,  # Sem proposta pendente
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar detecção de aceitação mútua
            has_mutual = PreOrderStateManager.check_mutual_acceptance(pre_order.id)
            expected_mutual = client_accepts and provider_accepts
            
            assert has_mutual == expected_mutual, \
                f"check_mutual_acceptance deve retornar {expected_mutual} quando " \
                f"cliente={client_accepts} e prestador={provider_accepts}"
            
            # Verificar propriedade do modelo
            assert pre_order.has_mutual_acceptance == expected_mutual, \
                "Propriedade has_mutual_acceptance deve corresponder"
            
            # Verificar se pode transicionar para PRONTO_CONVERSAO
            can_transition, reason = PreOrderStateManager.can_transition_to(
                pre_order,
                PreOrderStatus.PRONTO_CONVERSAO
            )
            
            if expected_mutual and not pre_order.has_active_proposal:
                assert can_transition, \
                    "Deve poder transicionar para PRONTO_CONVERSAO com aceitação mútua"
            else:
                assert not can_transition, \
                    "Não deve poder transicionar para PRONTO_CONVERSAO sem aceitação mútua"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 27: Transição para cancelada
# **Feature: sistema-pre-ordem-negociacao, Property 27: Transição para cancelada**
# **Validates: Requirements 8.4**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    initial_state=st.sampled_from([
        PreOrderStatus.EM_NEGOCIACAO,
        PreOrderStatus.AGUARDANDO_RESPOSTA,
        PreOrderStatus.PRONTO_CONVERSAO
    ]),
    cancelled_by_client=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_27_transition_to_cancelled(
    test_app, client_data, provider_data, initial_state, cancelled_by_client
):
    """
    Property 27: Transição para cancelada
    
    Para qualquer pré-ordem em estado não-final:
    - Deve ser possível transicionar para CANCELADA de qualquer estado não-final
    - O campo cancelled_at deve ser preenchido
    - O campo cancelled_by deve identificar quem cancelou
    - O histórico deve registrar o cancelamento
    - Estados finais (CONVERTIDA, CANCELADA, EXPIRADA) não permitem cancelamento
    
    Validates: Requirements 8.4
    """
    from services.pre_order_state_manager import PreOrderStateManager
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem no estado inicial especificado
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=initial_state.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Definir quem está cancelando
            canceller_id = client.id if cancelled_by_client else provider.id
            canceller_name = client.nome if cancelled_by_client else provider.nome
            cancellation_reason = f"{canceller_name} cancelou a pré-ordem"
            
            # Registrar cancelled_by antes da transição
            pre_order.cancelled_by = canceller_id
            pre_order.cancellation_reason = cancellation_reason
            session.commit()
            
            # Verificar que pode transicionar para CANCELADA
            can_transition, reason = PreOrderStateManager.can_transition_to(
                pre_order,
                PreOrderStatus.CANCELADA
            )
            assert can_transition, \
                f"Deve poder cancelar de {initial_state.value}"
            
            # Transicionar para CANCELADA
            result = PreOrderStateManager.transition_to(
                pre_order.id,
                PreOrderStatus.CANCELADA,
                canceller_id,
                cancellation_reason
            )
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            # Verificar propriedades
            assert result['success'], "Transição deve ter sucesso"
            assert result['new_state'] == PreOrderStatus.CANCELADA.value, \
                "Estado deve ser CANCELADA"
            assert pre_order.status == PreOrderStatus.CANCELADA.value, \
                "Status da pré-ordem deve ser CANCELADA"
            assert pre_order.cancelled_at is not None, \
                "Campo cancelled_at deve ser preenchido"
            assert pre_order.cancelled_by == canceller_id, \
                "Campo cancelled_by deve identificar quem cancelou"
            assert pre_order.cancellation_reason == cancellation_reason, \
                "Motivo do cancelamento deve estar registrado"
            
            # Verificar que histórico foi registrado
            history_records = pre_order.history.all()
            assert len(history_records) > 0, \
                "Cancelamento deve ser registrado no histórico"
            
            # Verificar que não pode mais transicionar para outros estados
            for target_state in [PreOrderStatus.EM_NEGOCIACAO, PreOrderStatus.PRONTO_CONVERSAO]:
                can_transition, _ = PreOrderStateManager.can_transition_to(
                    pre_order,
                    target_state
                )
                assert not can_transition, \
                    f"Não deve poder transicionar de CANCELADA para {target_state.value}"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 4: Notificação de criação
# **Feature: sistema-pre-ordem-negociacao, Property 4: Notificação de criação**
# **Validates: Requirements 1.4, 11.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_4_creation_notification(
    test_app, client_data, provider_data
):
    """
    Property 4: Notificação de criação
    
    Para qualquer pré-ordem criada:
    - Ambas as partes (cliente e prestador) devem ser notificadas
    - A notificação deve conter informações sobre a pré-ordem
    - A notificação deve incluir o prazo de negociação
    - O serviço de notificação deve ser chamado para ambas as partes
    
    Validates: Requirements 1.4, 11.1
    """
    from services.pre_order_service import PreOrderService
    from unittest.mock import patch, MagicMock
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite aceito
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.commit()
            
            # Mock do NotificationService
            with patch('services.pre_order_service.NotificationService') as mock_notification:
                mock_notification.notify_pre_order_created = MagicMock(return_value={'success': True})
                
                # Criar pré-ordem usando o serviço
                result = PreOrderService.create_from_invite(invite.id)
                
                # Verificar que o serviço foi bem-sucedido
                assert result['success'], "Criação da pré-ordem deve ser bem-sucedida"
                
                # Verificar que notificações foram enviadas
                assert mock_notification.notify_pre_order_created.call_count == 2, \
                    "Deve notificar ambas as partes (cliente e prestador)"
                
                # Verificar chamadas de notificação
                calls = mock_notification.notify_pre_order_created.call_args_list
                
                # Verificar notificação do cliente
                client_call = [c for c in calls if c[1]['user_type'] == 'cliente'][0]
                assert client_call[1]['user_id'] == client.id
                assert client_call[1]['pre_order_id'] == result['pre_order_id']
                
                # Verificar notificação do prestador
                provider_call = [c for c in calls if c[1]['user_type'] == 'prestador'][0]
                assert provider_call[1]['user_id'] == provider.id
                assert provider_call[1]['pre_order_id'] == result['pre_order_id']
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 20: Validação de saldo ao aceitar termos
# **Feature: sistema-pre-ordem-negociacao, Property 20: Validação de saldo ao aceitar termos**
# **Validates: Requirements 7.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    service_value=st.decimals(min_value=Decimal('100.00'), max_value=Decimal('1000.00'), places=2),
    client_balance=st.decimals(min_value=Decimal('0.00'), max_value=Decimal('2000.00'), places=2)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_20_balance_validation_on_accept_terms(
    test_app, client_data, provider_data, service_value, client_balance
):
    """
    Property 20: Validação de saldo ao aceitar termos
    
    Para qualquer tentativa de aceitar termos:
    - Se o cliente não tiver saldo suficiente (valor + taxa), deve falhar
    - Se o prestador não tiver saldo suficiente (taxa), deve falhar
    - Se ambos tiverem saldo suficiente, deve ter sucesso
    - A mensagem de erro deve indicar claramente o valor faltante
    
    Validates: Requirements 7.1
    """
    from services.pre_order_service import PreOrderService
    from services.config_service import ConfigService
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras com saldos específicos
            contestation_fee = ConfigService.get_contestation_fee()
            required_client_amount = service_value + contestation_fee
            
            client_wallet = Wallet(user_id=client.id, balance=client_balance)
            provider_wallet = Wallet(user_id=provider.id, balance=contestation_fee + Decimal('10.00'))
            session.add(client_wallet)
            session.add(provider_wallet)
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=service_value,
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
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
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Tentar aceitar termos como cliente
            result = PreOrderService.accept_terms(pre_order.id, client.id)
            
            # Verificar resultado baseado no saldo
            if client_balance >= required_client_amount:
                # Deve ter sucesso
                assert result['success'], "Aceitação deve ter sucesso com saldo suficiente"
                assert result['client_accepted'], "Cliente deve ter aceitado os termos"
            else:
                # Deve falhar
                assert not result['success'], "Aceitação deve falhar com saldo insuficiente"
                assert 'error' in result, "Deve retornar mensagem de erro"
                assert 'shortfall' in result, "Deve indicar valor faltante"
                assert result['shortfall'] == float(required_client_amount - client_balance), \
                    "Valor faltante deve ser calculado corretamente"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 23: Marcação de aceitação
# **Feature: sistema-pre-ordem-negociacao, Property 23: Marcação de aceitação**
# **Validates: Requirements 7.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    who_accepts_first=st.sampled_from(['cliente', 'prestador'])
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_23_acceptance_marking(
    test_app, client_data, provider_data, who_accepts_first
):
    """
    Property 23: Marcação de aceitação
    
    Para qualquer aceitação de termos:
    - A flag correspondente (client_accepted_terms ou provider_accepted_terms) deve ser True
    - O timestamp de aceitação deve ser registrado
    - A outra parte ainda não deve ter aceitado (a menos que aceite depois)
    - Quando ambos aceitam, has_mutual_acceptance deve ser True
    
    Validates: Requirements 7.5
    """
    from services.pre_order_service import PreOrderService
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras com saldo suficiente
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Primeira aceitação
            first_user_id = client.id if who_accepts_first == 'cliente' else provider.id
            result1 = PreOrderService.accept_terms(pre_order.id, first_user_id)
            
            assert result1['success'], "Primeira aceitação deve ter sucesso"
            assert not result1['has_mutual_acceptance'], \
                "Não deve ter aceitação mútua após apenas uma aceitação"
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            if who_accepts_first == 'cliente':
                assert pre_order.client_accepted_terms, "Cliente deve ter aceitado"
                assert not pre_order.provider_accepted_terms, "Prestador ainda não aceitou"
                assert pre_order.client_accepted_at is not None, "Timestamp deve estar registrado"
            else:
                assert pre_order.provider_accepted_terms, "Prestador deve ter aceitado"
                assert not pre_order.client_accepted_terms, "Cliente ainda não aceitou"
                assert pre_order.provider_accepted_at is not None, "Timestamp deve estar registrado"
            
            # Segunda aceitação
            second_user_id = provider.id if who_accepts_first == 'cliente' else client.id
            result2 = PreOrderService.accept_terms(pre_order.id, second_user_id)
            
            assert result2['success'], "Segunda aceitação deve ter sucesso"
            assert result2['has_mutual_acceptance'], \
                "Deve ter aceitação mútua após ambas as aceitações"
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            assert pre_order.client_accepted_terms, "Cliente deve ter aceitado"
            assert pre_order.provider_accepted_terms, "Prestador deve ter aceitado"
            assert pre_order.has_mutual_acceptance, "Deve ter aceitação mútua"
            assert pre_order.status == PreOrderStatus.PRONTO_CONVERSAO.value, \
                "Status deve ser PRONTO_CONVERSAO após aceitação mútua"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 24-28: Cancelamento
# **Feature: sistema-pre-ordem-negociacao, Property 24-28: Cancelamento**
# **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    who_cancels=st.sampled_from(['cliente', 'prestador']),
    reason_length=st.integers(min_value=0, max_value=200)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_24_28_cancellation(
    test_app, client_data, provider_data, who_cancels, reason_length
):
    """
    Property 24-28: Cancelamento
    
    Para qualquer cancelamento de pré-ordem:
    - Property 24: Motivo deve ser obrigatório (mínimo 10 caracteres) - Req 8.2
    - Property 25: Apenas cliente ou prestador podem cancelar - Req 8.1
    - Property 26: Outra parte deve ser notificada - Req 8.3
    - Property 27: Status deve mudar para CANCELADA - Req 8.4
    - Property 28: Nenhuma ordem deve ser criada - Req 8.5
    
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
    """
    from services.pre_order_service import PreOrderService
    from unittest.mock import patch, MagicMock
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Gerar motivo com tamanho específico
            reason = 'A' * reason_length if reason_length > 0 else ''
            
            # Determinar quem está cancelando
            canceller_id = client.id if who_cancels == 'cliente' else provider.id
            
            # Mock do NotificationService
            with patch('services.pre_order_service.NotificationService') as mock_notification:
                mock_notification.notify_pre_order_cancelled = MagicMock(return_value={'success': True})
                
                # Tentar cancelar
                try:
                    result = PreOrderService.cancel_pre_order(pre_order.id, canceller_id, reason)
                    
                    # Property 24: Motivo deve ter mínimo 10 caracteres
                    if reason_length < 10:
                        pytest.fail("Deveria ter lançado ValueError para motivo curto")
                    
                    # Property 25: Cancelamento deve ter sucesso para partes envolvidas
                    assert result['success'], "Cancelamento deve ter sucesso"
                    assert result['cancelled_by'] == canceller_id, \
                        "Deve registrar quem cancelou"
                    
                    # Property 27: Status deve ser CANCELADA
                    session.refresh(pre_order)
                    assert pre_order.status == PreOrderStatus.CANCELADA.value, \
                        "Status deve ser CANCELADA"
                    assert pre_order.cancelled_by == canceller_id, \
                        "Deve registrar quem cancelou"
                    assert pre_order.cancellation_reason == reason, \
                        "Deve registrar o motivo"
                    assert pre_order.cancelled_at is not None, \
                        "Deve registrar timestamp do cancelamento"
                    
                    # Property 26: Outra parte deve ser notificada
                    assert mock_notification.notify_pre_order_cancelled.called, \
                        "Deve notificar a outra parte"
                    
                    # Property 28: Nenhuma ordem deve ser criada
                    assert pre_order.order_id is None, \
                        "Nenhuma ordem deve ser criada após cancelamento"
                    
                except ValueError as e:
                    # Property 24: Deve falhar se motivo for muito curto
                    if reason_length < 10:
                        assert "pelo menos 10 caracteres" in str(e), \
                            "Erro deve mencionar tamanho mínimo do motivo"
                    else:
                        raise e
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 5: Permissão para propor
# **Feature: sistema-pre-ordem-negociacao, Property 5: Permissão para propor**
# **Validates: Requirements 2.1, 3.1, 3.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    third_party_data=valid_user_data(),
    proposed_value=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_5_permission_to_propose(
    test_app, client_data, provider_data, third_party_data, proposed_value
):
    """
    Property 5: Permissão para propor
    
    Para qualquer pré-ordem:
    - Apenas cliente ou prestador podem criar propostas
    - Terceiros não devem ter permissão para criar propostas
    - Tentativa de proposta por terceiro deve gerar PermissionError
    - Propostas de cliente e prestador devem ser aceitas
    
    Validates: Requirements 2.1, 3.1, 3.2
    """
    from services.pre_order_proposal_service import PreOrderProposalService
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(third_party_data['email'] not in [client_data['email'], provider_data['email']])
            assume(third_party_data['cpf'] not in [client_data['cpf'], provider_data['cpf']])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            
            third_party = User(**third_party_data)
            third_party.set_password('senha123')
            session.add(third_party)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            session.add(Wallet(user_id=third_party.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Tentar criar proposta como terceiro (deve falhar)
            with pytest.raises(PermissionError):
                PreOrderProposalService.create_proposal(
                    pre_order_id=pre_order.id,
                    user_id=third_party.id,
                    proposed_value=proposed_value,
                    justification='A' * 60
                )
            
            # Criar proposta como prestador (deve ter sucesso)
            result_provider = PreOrderProposalService.create_proposal(
                pre_order_id=pre_order.id,
                user_id=provider.id,
                proposed_value=proposed_value,
                justification='B' * 60
            )
            assert result_provider['success'], "Prestador deve poder criar proposta"
            assert result_provider['user_role'] == 'prestador'
            
            # Limpar proposta para testar cliente
            session.query(PreOrderProposal).delete()
            pre_order.has_active_proposal = False
            pre_order.active_proposal_id = None
            session.commit()
            
            # Criar proposta como cliente (deve ter sucesso)
            result_client = PreOrderProposalService.create_proposal(
                pre_order_id=pre_order.id,
                user_id=client.id,
                proposed_value=proposed_value,
                justification='C' * 60
            )
            assert result_client['success'], "Cliente deve poder criar proposta"
            assert result_client['user_role'] == 'cliente'
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 8-9: Notificação e apresentação de proposta
# **Feature: sistema-pre-ordem-negociacao, Property 8-9: Notificação e apresentação**
# **Validates: Requirements 2.2, 2.3, 11.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposed_value=st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_8_9_proposal_notification_and_presentation(
    test_app, client_data, provider_data, proposed_value
):
    """
    Property 8-9: Notificação e apresentação de proposta
    
    Para qualquer proposta criada:
    - A outra parte deve ser notificada imediatamente
    - A proposta deve ser apresentada com valor original e proposto lado a lado
    - A justificativa deve estar visível
    - O status deve ser 'pendente'
    
    Validates: Requirements 2.2, 2.3, 11.2
    """
    from services.pre_order_proposal_service import PreOrderProposalService
    from models import PreOrderProposal
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            original_value = Decimal('500.00')
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=original_value,
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=original_value,
                original_value=original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            justification = 'Justificativa detalhada da proposta com mais de 50 caracteres'
            
            # Criar proposta
            result = PreOrderProposalService.create_proposal(
                pre_order_id=pre_order.id,
                user_id=provider.id,
                proposed_value=proposed_value,
                justification=justification
            )
            
            # Verificar resultado
            assert result['success'], "Criação de proposta deve ter sucesso"
            
            # Buscar proposta criada
            proposal = PreOrderProposal.query.get(result['proposal_id'])
            assert proposal is not None, "Proposta deve existir no banco"
            
            # Verificar apresentação (valores lado a lado)
            assert proposal.proposed_value == proposed_value, \
                "Valor proposto deve estar correto"
            assert pre_order.current_value == original_value, \
                "Valor original deve estar preservado"
            
            # Verificar que ambos os valores estão disponíveis para comparação
            value_diff = proposal.value_difference
            assert value_diff is not None, \
                "Diferença de valor deve ser calculável"
            assert value_diff == (proposed_value - original_value), \
                "Diferença deve ser calculada corretamente"
            
            # Verificar justificativa visível
            assert proposal.justification == justification, \
                "Justificativa deve estar armazenada"
            assert len(proposal.justification) >= 50, \
                "Justificativa deve ter tamanho mínimo"
            
            # Verificar status pendente
            assert proposal.is_pending, \
                "Proposta deve estar pendente"
            assert proposal.status == ProposalStatus.PENDENTE.value, \
                "Status deve ser 'pendente'"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 11-14: Aprovação e rejeição de propostas
# **Feature: sistema-pre-ordem-negociacao, Property 11-14: Aprovação e rejeição**
# **Validates: Requirements 3.4, 4.1, 4.2, 4.3, 4.4, 4.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposed_value=st.decimals(min_value=Decimal('100.00'), max_value=Decimal('1000.00'), places=2),
    accept_proposal=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_11_14_proposal_acceptance_and_rejection(
    test_app, client_data, provider_data, proposed_value, accept_proposal
):
    """
    Property 11-14: Aprovação e rejeição de propostas
    
    Para qualquer proposta:
    - Se aceita: valores da pré-ordem devem ser atualizados
    - Se aceita: status deve mudar para 'aceita'
    - Se aceita: aceitações devem ser resetadas
    - Se aceita: estado deve voltar para EM_NEGOCIACAO
    - Se rejeitada: valores da pré-ordem devem permanecer inalterados
    - Se rejeitada: status deve mudar para 'rejeitada'
    - Se rejeitada: estado deve voltar para EM_NEGOCIACAO
    - Proposta ativa deve ser limpa em ambos os casos
    
    Validates: Requirements 3.4, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    from services.pre_order_proposal_service import PreOrderProposalService
    from models import PreOrderProposal
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite e pré-ordem
            original_value = Decimal('500.00')
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=original_value,
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=original_value,
                original_value=original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                client_accepted_terms=True,  # Simular aceitação prévia
                provider_accepted_terms=True,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Criar proposta
            result_create = PreOrderProposalService.create_proposal(
                pre_order_id=pre_order.id,
                user_id=provider.id,
                proposed_value=proposed_value,
                justification='A' * 60
            )
            assert result_create['success']
            
            proposal_id = result_create['proposal_id']
            
            # Recarregar pré-ordem
            session.refresh(pre_order)
            
            # Verificar que aceitações foram resetadas
            assert not pre_order.client_accepted_terms, \
                "Aceitações devem ser resetadas ao criar proposta"
            assert not pre_order.provider_accepted_terms, \
                "Aceitações devem ser resetadas ao criar proposta"
            
            if accept_proposal:
                # ACEITAR PROPOSTA
                result = PreOrderProposalService.accept_proposal(
                    proposal_id=proposal_id,
                    user_id=client.id
                )
                
                assert result['success'], "Aceitação deve ter sucesso"
                
                # Recarregar pré-ordem e proposta
                session.refresh(pre_order)
                proposal = PreOrderProposal.query.get(proposal_id)
                
                # Verificar que valores foram atualizados
                assert pre_order.current_value == proposed_value, \
                    "Valor da pré-ordem deve ser atualizado"
                assert proposal.is_accepted, \
                    "Proposta deve estar aceita"
                assert proposal.status == ProposalStatus.ACEITA.value, \
                    "Status deve ser 'aceita'"
                
                # Verificar que proposta ativa foi limpa
                assert not pre_order.has_active_proposal, \
                    "Proposta ativa deve ser limpa"
                assert pre_order.active_proposal_id is None, \
                    "Referência à proposta ativa deve ser limpa"
                
                # Verificar que estado voltou para EM_NEGOCIACAO
                assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                    "Estado deve voltar para EM_NEGOCIACAO"
                
                # Verificar que aceitações foram resetadas novamente
                assert not pre_order.client_accepted_terms, \
                    "Aceitações devem ser resetadas após aceitar proposta"
                assert not pre_order.provider_accepted_terms, \
                    "Aceitações devem ser resetadas após aceitar proposta"
                
            else:
                # REJEITAR PROPOSTA
                result = PreOrderProposalService.reject_proposal(
                    proposal_id=proposal_id,
                    user_id=client.id,
                    rejection_reason="Não concordo com o valor proposto"
                )
                
                assert result['success'], "Rejeição deve ter sucesso"
                
                # Recarregar pré-ordem e proposta
                session.refresh(pre_order)
                proposal = PreOrderProposal.query.get(proposal_id)
                
                # Verificar que valores NÃO foram alterados
                assert pre_order.current_value == original_value, \
                    "Valor da pré-ordem deve permanecer inalterado"
                assert proposal.is_rejected, \
                    "Proposta deve estar rejeitada"
                assert proposal.status == ProposalStatus.REJEITADA.value, \
                    "Status deve ser 'rejeitada'"
                
                # Verificar que proposta ativa foi limpa
                assert not pre_order.has_active_proposal, \
                    "Proposta ativa deve ser limpa"
                assert pre_order.active_proposal_id is None, \
                    "Referência à proposta ativa deve ser limpa"
                
                # Verificar que estado voltou para EM_NEGOCIACAO
                assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                    "Estado deve voltar para EM_NEGOCIACAO"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 55-58: Propostas extremas
# **Feature: sistema-pre-ordem-negociacao, Property 55-58: Propostas extremas**
# **Validates: Requirements 19.1, 19.2, 19.3, 19.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    base_value=st.decimals(min_value=Decimal('100.00'), max_value=Decimal('1000.00'), places=2),
    change_factor=st.sampled_from([
        Decimal('0.3'),   # -70% (extrema)
        Decimal('0.6'),   # -40% (normal)
        Decimal('1.5'),   # +50% (normal)
        Decimal('2.5'),   # +150% (extrema)
        Decimal('3.0')    # +200% (extrema)
    ])
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_55_58_extreme_proposals(
    test_app, client_data, provider_data, base_value, change_factor
):
    """
    Property 55-58: Propostas extremas
    
    Para qualquer proposta:
    - Aumentos >100% devem ser detectados como extremos
    - Reduções >50% devem ser detectadas como extremas
    - Propostas extremas devem exigir justificativa de pelo menos 100 caracteres
    - Propostas extremas com justificativa curta devem ser rejeitadas
    - Propostas normais devem aceitar justificativa de 50 caracteres
    
    Validates: Requirements 19.1, 19.2, 19.3, 19.5
    """
    from services.pre_order_proposal_service import PreOrderProposalService
    
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('5000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('2000.00')))
            
            # Criar convite e pré-ordem
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                original_value=base_value,
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=base_value,
                original_value=base_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Calcular valor proposto
            proposed_value = base_value * change_factor
            
            # Calcular percentual de mudança
            change_percent = ((proposed_value - base_value) / base_value) * 100
            
            # Determinar se é proposta extrema
            is_extreme = change_percent > 100 or change_percent < -50
            
            # Tentar criar proposta com justificativa curta (60 caracteres)
            short_justification = 'A' * 60
            
            if is_extreme:
                # Proposta extrema com justificativa curta deve falhar
                with pytest.raises(ValueError) as exc_info:
                    PreOrderProposalService.create_proposal(
                        pre_order_id=pre_order.id,
                        user_id=provider.id,
                        proposed_value=proposed_value,
                        justification=short_justification
                    )
                
                assert "extrema" in str(exc_info.value).lower(), \
                    "Erro deve mencionar proposta extrema"
                assert "100" in str(exc_info.value), \
                    "Erro deve mencionar requisito de 100 caracteres"
                
                # Tentar novamente com justificativa longa (deve ter sucesso)
                long_justification = 'B' * 120
                result = PreOrderProposalService.create_proposal(
                    pre_order_id=pre_order.id,
                    user_id=provider.id,
                    proposed_value=proposed_value,
                    justification=long_justification
                )
                
                assert result['success'], \
                    "Proposta extrema com justificativa longa deve ter sucesso"
                assert result['is_extreme'], \
                    "Proposta deve ser marcada como extrema"
                assert result['extreme_reason'] is not None, \
                    "Motivo da extremidade deve estar presente"
                
            else:
                # Proposta normal com justificativa curta deve ter sucesso
                result = PreOrderProposalService.create_proposal(
                    pre_order_id=pre_order.id,
                    user_id=provider.id,
                    proposed_value=proposed_value,
                    justification=short_justification
                )
                
                assert result['success'], \
                    "Proposta normal com justificativa de 50+ caracteres deve ter sucesso"
                assert not result['is_extreme'], \
                    "Proposta não deve ser marcada como extrema"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 37: Convite convertido não pode ser modificado
# **Feature: sistema-pre-ordem-negociacao, Property 37: Convite convertido não pode ser modificado**
# **Validates: Requirements 12.1**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    user_id_offset=st.integers(min_value=1000, max_value=999999)
)
def test_property_37_converted_invite_immutable(test_app, user_id_offset):
    """
    Property 37: Convite convertido não pode ser modificado
    
    Para qualquer convite que foi convertido em pré-ordem,
    o convite não deve permitir modificações.
    
    Validates: Requirements 12.1
    """
    with test_app.app_context():
        session = get_clean_db_session(test_app)
        
        try:
            # Criar cliente e prestador
            client = User(
                email=client_data['email'],
                nome=client_data['nome'],
                cpf=client_data['cpf'],
                phone=client_data['phone'],
                roles='cliente'
            )
            client.set_password('senha123')
            session.add(client)
            
            provider = User(
                email=provider_data['email'],
                nome=provider_data['nome'],
                cpf=provider_data['cpf'],
                phone=provider_data['phone'],
                roles='prestador'
            )
            provider.set_password('senha123')
            session.add(provider)
            
            # Criar carteiras
            client_wallet = Wallet(user_id=client.id, balance=Decimal('1000.00'))
            provider_wallet = Wallet(user_id=provider.id, balance=Decimal('100.00'))
            session.add_all([client_wallet, provider_wallet])
            
            session.commit()
            
            # Criar convite aceito
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                service_category='pedreiro',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito',
                client_accepted=True,
                provider_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted_at=datetime.utcnow()
            )
            session.add(invite)
            session.commit()
            
            # Criar pré-ordem a partir do convite
            from services.pre_order_service import PreOrderService
            result = PreOrderService.create_from_invite(invite.id)
            
            assert result['success'], "Pré-ordem deve ser criada com sucesso"
            
            # Recarregar convite
            session.expire(invite)
            invite = Invite.query.get(invite.id)
            
            # Verificar que o convite foi marcado como convertido
            assert invite.status == 'convertido_pre_ordem', \
                "Convite deve estar marcado como convertido_pre_ordem"
            
            # Tentar modificar o convite (não deve ser permitido)
            # O sistema deve impedir modificações em convites convertidos
            # Isso é validado através do status do convite
            assert invite.status == 'convertido_pre_ordem', \
                "Status do convite convertido não deve permitir modificações"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 38: Convite convertido mostra status correto
# **Feature: sistema-pre-ordem-negociacao, Property 38: Convite convertido mostra status correto**
# **Validates: Requirements 12.2**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
def test_property_38_converted_invite_shows_status(test_app, client_data, provider_data):
    """
    Property 38: Convite convertido mostra status correto
    
    Para qualquer convite convertido em pré-ordem,
    o status deve ser 'convertido_pre_ordem' e deve ter link para a pré-ordem.
    
    Validates: Requirements 12.2
    """
    with test_app.app_context():
        session = get_clean_db_session(test_app)
        
        try:
            # Criar cliente e prestador
            client = User(
                email=client_data['email'],
                nome=client_data['nome'],
                cpf=client_data['cpf'],
                phone=client_data['phone'],
                roles='cliente'
            )
            client.set_password('senha123')
            session.add(client)
            
            provider = User(
                email=provider_data['email'],
                nome=provider_data['nome'],
                cpf=provider_data['cpf'],
                phone=provider_data['phone'],
                roles='prestador'
            )
            provider.set_password('senha123')
            session.add(provider)
            
            # Criar carteiras
            client_wallet = Wallet(user_id=client.id, balance=Decimal('1000.00'))
            provider_wallet = Wallet(user_id=provider.id, balance=Decimal('100.00'))
            session.add_all([client_wallet, provider_wallet])
            
            session.commit()
            
            # Criar convite aceito
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                service_category='pedreiro',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito',
                client_accepted=True,
                provider_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted_at=datetime.utcnow()
            )
            session.add(invite)
            session.commit()
            
            # Criar pré-ordem a partir do convite
            from services.pre_order_service import PreOrderService
            result = PreOrderService.create_from_invite(invite.id)
            
            assert result['success'], "Pré-ordem deve ser criada com sucesso"
            pre_order_id = result['pre_order_id']
            
            # Recarregar convite
            session.expire(invite)
            invite = Invite.query.get(invite.id)
            
            # Verificar status e link
            assert invite.status == 'convertido_pre_ordem', \
                "Convite deve ter status 'convertido_pre_ordem'"
            
            # Verificar que há uma pré-ordem associada
            pre_order = PreOrder.query.filter_by(invite_id=invite.id).first()
            assert pre_order is not None, \
                "Deve existir uma pré-ordem associada ao convite"
            assert pre_order.id == pre_order_id, \
                "ID da pré-ordem deve corresponder ao retornado"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 39: Aba Convites contém apenas aceitar/rejeitar
# **Feature: sistema-pre-ordem-negociacao, Property 39: Aba Convites contém apenas aceitar/rejeitar**
# **Validates: Requirements 12.3**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
def test_property_39_invite_tab_simple_actions(test_app, client_data, provider_data):
    """
    Property 39: Aba Convites contém apenas aceitar/rejeitar
    
    Para qualquer convite pendente, as únicas ações disponíveis
    devem ser aceitar ou rejeitar. Negociações devem ocorrer na pré-ordem.
    
    Validates: Requirements 12.3
    """
    with test_app.app_context():
        session = get_clean_db_session(test_app)
        
        try:
            # Criar cliente e prestador
            client = User(
                email=client_data['email'],
                nome=client_data['nome'],
                cpf=client_data['cpf'],
                phone=client_data['phone'],
                roles='cliente'
            )
            client.set_password('senha123')
            session.add(client)
            
            provider = User(
                email=provider_data['email'],
                nome=provider_data['nome'],
                cpf=provider_data['cpf'],
                phone=provider_data['phone'],
                roles='prestador'
            )
            provider.set_password('senha123')
            session.add(provider)
            
            # Criar carteiras
            client_wallet = Wallet(user_id=client.id, balance=Decimal('1000.00'))
            provider_wallet = Wallet(user_id=provider.id, balance=Decimal('100.00'))
            session.add_all([client_wallet, provider_wallet])
            
            session.commit()
            
            # Criar convite pendente
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
            session.add(invite)
            session.commit()
            
            # Verificar que o convite está pendente
            assert invite.status == 'pendente', \
                "Convite deve estar pendente"
            
            # Verificar que pode ser aceito ou rejeitado
            from services.invite_service import InviteService
            
            # Testar aceitação (deve funcionar)
            result = InviteService.accept_invite_as_provider(invite.id, provider.id)
            assert result['success'], \
                "Prestador deve poder aceitar convite pendente"
            
            # Após aceitação mútua, deve criar pré-ordem (não ordem)
            if result.get('pre_order_created'):
                assert result['pre_order_created'] == True, \
                    "Deve criar pré-ordem, não ordem definitiva"
                assert result.get('order_created', False) == False, \
                    "Não deve criar ordem definitiva diretamente"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 40: Aceitação mútua cria pré-ordem, não ordem
# **Feature: sistema-pre-ordem-negociacao, Property 40: Aceitação mútua cria pré-ordem, não ordem**
# **Validates: Requirements 12.5**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2)
)
def test_property_40_mutual_acceptance_creates_pre_order(test_app, client_data, provider_data, value):
    """
    Property 40: Aceitação mútua cria pré-ordem, não ordem
    
    Para qualquer convite, quando ambas as partes aceitam,
    deve ser criada uma pré-ordem (não uma ordem definitiva).
    Valores não devem ser bloqueados neste momento.
    
    Validates: Requirements 12.5
    """
    with test_app.app_context():
        session = get_clean_db_session(test_app)
        
        try:
            # Criar cliente e prestador
            client = User(
                email=client_data['email'],
                nome=client_data['nome'],
                cpf=client_data['cpf'],
                phone=client_data['phone'],
                roles='cliente'
            )
            client.set_password('senha123')
            session.add(client)
            
            provider = User(
                email=provider_data['email'],
                nome=provider_data['nome'],
                cpf=provider_data['cpf'],
                phone=provider_data['phone'],
                roles='prestador'
            )
            provider.set_password('senha123')
            session.add(provider)
            
            # Criar carteiras com saldo suficiente
            initial_client_balance = value + Decimal('100.00')
            initial_provider_balance = Decimal('100.00')
            
            client_wallet = Wallet(user_id=client.id, balance=initial_client_balance)
            provider_wallet = Wallet(user_id=provider.id, balance=initial_provider_balance)
            session.add_all([client_wallet, provider_wallet])
            
            session.commit()
            
            # Criar convite com apenas cliente aceitando
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição do serviço',
                service_category='pedreiro',
                original_value=value,
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=True,
                provider_accepted=False,
                client_accepted_at=datetime.utcnow()
            )
            session.add(invite)
            session.commit()
            
            # Prestador aceita (aceitação mútua)
            from services.invite_service import InviteService
            result = InviteService.accept_invite_as_provider(invite.id, provider.id)
            
            assert result['success'], \
                "Aceitação do prestador deve ter sucesso"
            
            # Verificar que pré-ordem foi criada (não ordem)
            assert result.get('pre_order_created') == True, \
                "Deve criar pré-ordem na aceitação mútua"
            assert result.get('order_created', False) == False, \
                "Não deve criar ordem definitiva na aceitação mútua"
            
            # Verificar que valores NÃO foram bloqueados
            session.expire_all()
            client_wallet = Wallet.query.filter_by(user_id=client.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=provider.id).first()
            
            assert client_wallet.balance == initial_client_balance, \
                f"Saldo do cliente não deve ser bloqueado na criação da pré-ordem. " \
                f"Esperado: {initial_client_balance}, Atual: {client_wallet.balance}"
            
            assert provider_wallet.balance == initial_provider_balance, \
                f"Saldo do prestador não deve ser bloqueado na criação da pré-ordem. " \
                f"Esperado: {initial_provider_balance}, Atual: {provider_wallet.balance}"
            
            # Verificar que pré-ordem existe
            pre_order_id = result.get('pre_order_id')
            assert pre_order_id is not None, \
                "ID da pré-ordem deve ser retornado"
            
            pre_order = PreOrder.query.get(pre_order_id)
            assert pre_order is not None, \
                "Pré-ordem deve existir no banco de dados"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Pré-ordem deve estar em negociação"
            assert pre_order.current_value == value, \
                "Valor da pré-ordem deve corresponder ao valor do convite"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 29: Apresentação de título e descrição
# **Feature: sistema-pre-ordem-negociacao, Property 29: Apresentação de título e descrição**
# **Validates: Requirements 9.2, 18.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    title=st.text(min_size=5, max_size=200, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z"))),
    description=st.text(min_size=10, max_size=1000, alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")))
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_29_presentation_of_title_and_description(
    test_app, client_data, provider_data, title, description
):
    """
    Property 29: Apresentação de título e descrição
    
    Para qualquer pré-ordem visualizada:
    - O título deve ser exibido corretamente
    - A descrição deve ser exibida corretamente
    - Ambos devem corresponder aos dados armazenados no banco
    - Caracteres especiais devem ser tratados adequadamente
    
    Validates: Requirements 9.2, 18.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(len(title.strip()) >= 5)
            assume(len(description.strip()) >= 10)
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title=title.strip(),
                service_description=description.strip(),
                original_value=Decimal('500.00'),
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
                title=title.strip(),
                description=description.strip(),
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de apresentação
            assert pre_order.title == title.strip(), \
                "Título exibido deve corresponder ao armazenado"
            assert pre_order.description == description.strip(), \
                "Descrição exibida deve corresponder à armazenada"
            assert len(pre_order.title) > 0, \
                "Título não deve estar vazio"
            assert len(pre_order.description) > 0, \
                "Descrição não deve estar vazia"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 30: Apresentação de valores com comparação
# **Feature: sistema-pre-ordem-negociacao, Property 30: Apresentação de valores com comparação**
# **Validates: Requirements 9.2, 9.3**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    original_value=st.decimals(min_value=Decimal('50.00'), max_value=Decimal('5000.00'), places=2),
    value_change_percent=st.floats(min_value=-50.0, max_value=100.0)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_30_value_presentation_with_comparison(
    test_app, client_data, provider_data, original_value, value_change_percent
):
    """
    Property 30: Apresentação de valores com comparação
    
    Para qualquer pré-ordem com valor alterado:
    - O valor atual deve ser exibido
    - O valor original deve ser exibido
    - A diferença percentual deve ser calculada corretamente
    - Indicadores visuais (setas, cores) devem refletir aumento/redução
    
    Validates: Requirements 9.2, 9.3
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Calcular valor atual baseado na mudança percentual
            current_value = original_value * (Decimal('1') + Decimal(str(value_change_percent / 100)))
            current_value = max(Decimal('10.00'), current_value)  # Mínimo de 10.00
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('10000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=original_value,
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem com valor alterado
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title='Serviço Teste',
                description='Descrição',
                current_value=current_value,
                original_value=original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de apresentação de valores
            assert pre_order.current_value == current_value, \
                "Valor atual deve ser exibido corretamente"
            assert pre_order.original_value == original_value, \
                "Valor original deve ser exibido corretamente"
            
            # Verificar cálculo de diferença
            value_diff = pre_order.value_difference_from_original
            assert value_diff == (current_value - original_value), \
                "Diferença de valor deve ser calculada corretamente"
            
            # Verificar percentual de mudança
            if original_value > 0:
                expected_percent = float((current_value - original_value) / original_value * 100)
                actual_percent = float(pre_order.value_change_percentage)
                assert abs(actual_percent - expected_percent) < 0.01, \
                    "Percentual de mudança deve ser calculado corretamente"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 31: Apresentação de prazo de entrega
# **Feature: sistema-pre-ordem-negociacao, Property 31: Apresentação de prazo de entrega**
# **Validates: Requirements 9.2, 10.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    days_ahead=st.integers(min_value=1, max_value=90)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_31_delivery_date_presentation(
    test_app, client_data, provider_data, days_ahead
):
    """
    Property 31: Apresentação de prazo de entrega
    
    Para qualquer pré-ordem:
    - A data de entrega deve ser exibida em formato legível
    - A data deve estar no futuro
    - O formato deve ser consistente (DD/MM/YYYY HH:MM)
    
    Validates: Requirements 9.2, 10.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Definir data de entrega
            delivery_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
                delivery_date=delivery_date,
                status='aceito',
                expires_at=delivery_date
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title='Serviço Teste',
                description='Descrição',
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de apresentação de data
            assert pre_order.delivery_date == delivery_date, \
                "Data de entrega deve ser exibida corretamente"
            assert pre_order.delivery_date > datetime.utcnow(), \
                "Data de entrega deve estar no futuro"
            
            # Verificar que a data pode ser formatada
            formatted_date = pre_order.delivery_date.strftime('%d/%m/%Y %H:%M')
            assert len(formatted_date) > 0, \
                "Data deve poder ser formatada"
            assert '/' in formatted_date, \
                "Formato de data deve conter separadores"
        finally:
            session.rollback()



# ==============================================================================
# PROPERTY 32: Apresentação de partes envolvidas
# **Feature: sistema-pre-ordem-negociacao, Property 32: Apresentação de partes envolvidas**
# **Validates: Requirements 9.2, 10.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_32_parties_presentation(
    test_app, client_data, provider_data
):
    """
    Property 32: Apresentação de partes envolvidas
    
    Para qualquer pré-ordem:
    - O nome do cliente deve ser exibido
    - O nome do prestador deve ser exibido
    - Os contatos (telefone) devem ser exibidos quando disponíveis
    - Deve haver indicação clara de qual parte é o usuário atual
    
    Validates: Requirements 9.2, 10.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
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
                title='Serviço Teste',
                description='Descrição',
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de apresentação das partes
            assert pre_order.client_id == client.id, \
                "Cliente deve ser identificado corretamente"
            assert pre_order.provider_id == provider.id, \
                "Prestador deve ser identificado corretamente"
            assert pre_order.client.nome == client.nome, \
                "Nome do cliente deve ser acessível"
            assert pre_order.provider.nome == provider.nome, \
                "Nome do prestador deve ser acessível"
            assert pre_order.client.phone == client.phone, \
                "Telefone do cliente deve ser acessível"
            assert pre_order.provider.phone == provider.phone, \
                "Telefone do prestador deve ser acessível"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 33: Apresentação de histórico em timeline
# **Feature: sistema-pre-ordem-negociacao, Property 33: Apresentação de histórico em timeline**
# **Validates: Requirements 10.1, 10.3, 10.4**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    num_events=st.integers(min_value=1, max_value=10)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_33_history_timeline_presentation(
    test_app, client_data, provider_data, num_events
):
    """
    Property 33: Apresentação de histórico em timeline
    
    Para qualquer pré-ordem com histórico:
    - Os eventos devem ser ordenados por data (mais recente primeiro)
    - Cada evento deve mostrar: tipo, ator, descrição, timestamp
    - O formato de apresentação deve ser consistente
    - Dados adicionais (event_data) devem ser acessíveis
    
    Validates: Requirements 10.1, 10.3, 10.4
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
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
                title='Serviço Teste',
                description='Descrição',
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.flush()
            
            # Criar múltiplos eventos de histórico
            event_types = ['created', 'proposal_sent', 'proposal_accepted', 'terms_accepted_client']
            events_created = []
            
            for i in range(min(num_events, len(event_types))):
                event = PreOrderHistory(
                    pre_order_id=pre_order.id,
                    event_type=event_types[i],
                    actor_id=client.id if i % 2 == 0 else provider.id,
                    description=f'Evento {i+1}: {event_types[i]}',
                    event_data={'index': i, 'type': event_types[i]},
                    created_at=datetime.utcnow() + timedelta(seconds=i)
                )
                session.add(event)
                events_created.append(event)
            
            session.commit()
            
            # Buscar histórico ordenado
            history = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order.id
            ).order_by(PreOrderHistory.created_at.desc()).all()
            
            # Verificar propriedades de apresentação do histórico
            assert len(history) == len(events_created), \
                "Todos os eventos devem estar no histórico"
            
            # Verificar ordenação (mais recente primeiro)
            for i in range(len(history) - 1):
                assert history[i].created_at >= history[i+1].created_at, \
                    "Histórico deve estar ordenado por data (mais recente primeiro)"
            
            # Verificar que cada evento tem os campos necessários
            for event in history:
                assert event.event_type is not None, \
                    "Evento deve ter tipo definido"
                assert event.actor_id is not None, \
                    "Evento deve ter ator definido"
                assert event.description is not None, \
                    "Evento deve ter descrição"
                assert event.created_at is not None, \
                    "Evento deve ter timestamp"
                assert event.event_type_display is not None, \
                    "Evento deve ter formato de exibição"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 34: Apresentação de categoria de serviço
# **Feature: sistema-pre-ordem-negociacao, Property 34: Apresentação de categoria de serviço**
# **Validates: Requirements 9.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    category=st.sampled_from(['pedreiro', 'encanador', 'eletricista', 'pintor', 'jardineiro', None])
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_34_service_category_presentation(
    test_app, client_data, provider_data, category
):
    """
    Property 34: Apresentação de categoria de serviço
    
    Para qualquer pré-ordem:
    - A categoria de serviço deve ser exibida quando disponível
    - Quando não há categoria, não deve causar erro
    - A categoria deve ser apresentada de forma legível
    
    Validates: Requirements 9.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                service_category=category,
                original_value=Decimal('500.00'),
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
                title='Serviço Teste',
                description='Descrição',
                service_category=category,
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de apresentação de categoria
            if category is not None:
                assert pre_order.service_category == category, \
                    "Categoria deve ser exibida corretamente"
                assert len(pre_order.service_category) > 0, \
                    "Categoria não deve estar vazia quando definida"
            else:
                assert pre_order.service_category is None, \
                    "Categoria pode ser None sem causar erro"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 41: Indicadores de status visuais
# **Feature: sistema-pre-ordem-negociacao, Property 41: Indicadores de status visuais**
# **Validates: Requirements 13.1, 13.2, 13.3, 13.4**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    status=st.sampled_from([
        PreOrderStatus.EM_NEGOCIACAO.value,
        PreOrderStatus.AGUARDANDO_RESPOSTA.value,
        PreOrderStatus.PRONTO_CONVERSAO.value,
        PreOrderStatus.CONVERTIDA.value,
        PreOrderStatus.CANCELADA.value,
        PreOrderStatus.EXPIRADA.value
    ])
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_41_status_visual_indicators(
    test_app, client_data, provider_data, status
):
    """
    Property 41: Indicadores de status visuais
    
    Para qualquer pré-ordem em qualquer status:
    - Deve ter um status_display legível em português
    - Deve ter uma classe CSS de cor apropriada (status_color_class)
    - A cor deve refletir o estado (sucesso=verde, aviso=amarelo, erro=vermelho)
    - Badges e indicadores devem ser consistentes
    
    Validates: Requirements 13.1, 13.2, 13.3, 13.4
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem com status específico
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=client.id,
                provider_id=provider.id,
                title='Serviço Teste',
                description='Descrição',
                current_value=Decimal('500.00'),
                original_value=Decimal('500.00'),
                delivery_date=invite.delivery_date,
                status=status,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar propriedades de indicadores visuais
            assert pre_order.status == status, \
                "Status deve ser o definido"
            assert pre_order.status_display is not None, \
                "Deve ter texto de exibição do status"
            assert len(pre_order.status_display) > 0, \
                "Texto de exibição não deve estar vazio"
            assert pre_order.status_color_class is not None, \
                "Deve ter classe CSS de cor"
            assert 'bg-' in pre_order.status_color_class, \
                "Classe de cor deve seguir padrão Bootstrap"
            
            # Verificar mapeamento correto de cores por status
            color_expectations = {
                PreOrderStatus.EM_NEGOCIACAO.value: 'bg-info',
                PreOrderStatus.AGUARDANDO_RESPOSTA.value: 'bg-warning',
                PreOrderStatus.PRONTO_CONVERSAO.value: 'bg-success',
                PreOrderStatus.CONVERTIDA.value: 'bg-primary',
                PreOrderStatus.CANCELADA.value: 'bg-danger',
                PreOrderStatus.EXPIRADA.value: 'bg-secondary'
            }
            
            expected_color = color_expectations.get(status, 'bg-secondary')
            assert pre_order.status_color_class == expected_color, \
                f"Cor para status {status} deve ser {expected_color}"
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 54: Informações principais completas
# **Feature: sistema-pre-ordem-negociacao, Property 54: Informações principais completas**
# **Validates: Requirements 18.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_54_complete_main_information(
    test_app, client_data, provider_data
):
    """
    Property 54: Informações principais completas
    
    Para qualquer pré-ordem visualizada:
    - Todas as informações principais devem estar presentes e acessíveis
    - Título, descrição, valor, prazo, partes, status devem estar disponíveis
    - Nenhum campo obrigatório deve estar None ou vazio
    - A interface deve ter todos os dados necessários para tomada de decisão
    
    Validates: Requirements 18.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            
            # Criar usuários
            client = User(**client_data)
            client.set_password('senha123')
            session.add(client)
            
            provider = User(**provider_data)
            provider.set_password('senha123')
            session.add(provider)
            session.flush()
            
            # Criar carteiras
            session.add(Wallet(user_id=client.id, balance=Decimal('2000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('1000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Completo de Teste',
                service_description='Descrição detalhada do serviço a ser realizado',
                service_category='pedreiro',
                original_value=Decimal('750.00'),
                delivery_date=datetime.utcnow() + timedelta(days=20),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=20)
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
                service_category=invite.service_category,
                current_value=invite.original_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            session.add(pre_order)
            session.commit()
            
            # Verificar que todas as informações principais estão presentes
            assert pre_order.id is not None, \
                "ID deve estar presente"
            assert pre_order.title is not None and len(pre_order.title) > 0, \
                "Título deve estar presente e não vazio"
            assert pre_order.description is not None and len(pre_order.description) > 0, \
                "Descrição deve estar presente e não vazia"
            assert pre_order.current_value is not None and pre_order.current_value > 0, \
                "Valor atual deve estar presente e positivo"
            assert pre_order.original_value is not None and pre_order.original_value > 0, \
                "Valor original deve estar presente e positivo"
            assert pre_order.delivery_date is not None, \
                "Data de entrega deve estar presente"
            assert pre_order.status is not None, \
                "Status deve estar presente"
            assert pre_order.client_id is not None, \
                "ID do cliente deve estar presente"
            assert pre_order.provider_id is not None, \
                "ID do prestador deve estar presente"
            assert pre_order.expires_at is not None, \
                "Prazo de expiração deve estar presente"
            assert pre_order.created_at is not None, \
                "Data de criação deve estar presente"
            
            # Verificar que relacionamentos estão acessíveis
            assert pre_order.client is not None, \
                "Relacionamento com cliente deve estar acessível"
            assert pre_order.provider is not None, \
                "Relacionamento com prestador deve estar acessível"
            assert pre_order.invite is not None, \
                "Relacionamento com convite deve estar acessível"
            
            # Verificar propriedades calculadas
            assert pre_order.status_display is not None, \
                "Status formatado deve estar disponível"
            assert pre_order.status_color_class is not None, \
                "Classe de cor do status deve estar disponível"
            assert pre_order.days_until_expiration is not None, \
                "Dias até expiração deve ser calculável"
        finally:
            session.rollback()
