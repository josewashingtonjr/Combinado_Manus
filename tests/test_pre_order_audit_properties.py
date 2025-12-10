#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para PreOrderAuditService
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
propriedades universais do sistema de auditoria de pré-ordens.

Property 52-53: Histórico e alertas (Req 17.3, 17.5)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, Wallet,
    PreOrderHistory, PreOrderProposal, ProposalStatus
)
from services.pre_order_audit_service import PreOrderAuditService
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
def valid_event_types(draw):
    """Gera tipos de eventos válidos para histórico"""
    return draw(st.sampled_from([
        'created', 'proposal_sent', 'proposal_accepted', 'proposal_rejected',
        'terms_accepted_client', 'terms_accepted_provider', 'cancelled',
        'expired', 'converted', 'value_updated'
    ]))


@st.composite
def proposal_count_strategy(draw):
    """Gera número de propostas para testar limites"""
    return draw(st.integers(min_value=0, max_value=15))


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
        # Limpar todas as tabelas na ordem correta
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrderProposal).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


def create_test_pre_order(session, client, provider, invite):
    """Helper para criar uma pré-ordem de teste"""
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
    return pre_order


# ==============================================================================
# PROPERTY 52: Histórico completo para consulta em disputas
# **Feature: sistema-pre-ordem-negociacao, Property 52: Histórico completo para consulta em disputas**
# **Validates: Requirements 17.3**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    num_events=st.integers(min_value=1, max_value=10),
    event_type=valid_event_types()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_52_full_history_for_disputes(
    test_app, client_data, provider_data, num_events, event_type
):
    """
    Property 52: Histórico completo para consulta em disputas
    
    Para qualquer pré-ordem com eventos registrados:
    - O método get_full_history deve retornar todos os eventos
    - Cada evento deve conter: event_type, actor_id, description, created_at
    - Os eventos devem estar ordenados cronologicamente
    - O histórico deve ser consultável para fins de auditoria e disputas
    - Metadados devem incluir informações sobre negociações excessivas
    
    Validates: Requirements 17.3
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
                service_title='Serviço de Teste para Auditoria',
                service_description='Descrição detalhada do serviço',
                original_value=Decimal('500.00'),
                delivery_date=datetime.utcnow() + timedelta(days=15),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            
            # Criar múltiplos eventos de histórico
            created_events = []
            for i in range(num_events):
                actor_id = client.id if i % 2 == 0 else provider.id
                history_entry = PreOrderHistory(
                    pre_order_id=pre_order.id,
                    event_type=event_type,
                    actor_id=actor_id,
                    description=f'Evento de teste #{i+1}: {event_type}',
                    event_data={
                        'test_index': i,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                session.add(history_entry)
                created_events.append(history_entry)
            
            session.commit()
            
            # Obter histórico completo
            result = PreOrderAuditService.get_full_history(pre_order.id)
            
            # Verificar propriedades
            assert result['success'] is True, \
                "get_full_history deve retornar sucesso"
            
            assert result['total_events'] == num_events, \
                f"Deve retornar {num_events} eventos, retornou {result['total_events']}"
            
            # Verificar que cada evento tem os campos obrigatórios
            for event in result['history']:
                assert 'event_type' in event, \
                    "Cada evento deve ter event_type"
                assert 'actor_id' in event, \
                    "Cada evento deve ter actor_id"
                assert 'description' in event, \
                    "Cada evento deve ter description"
                assert 'created_at' in event, \
                    "Cada evento deve ter created_at"
                assert 'event_data' in event, \
                    "Cada evento deve ter event_data"
            
            # Verificar ordenação cronológica (ascendente)
            timestamps = [event['timestamp'] for event in result['history']]
            assert timestamps == sorted(timestamps), \
                "Eventos devem estar ordenados cronologicamente"
            
            # Verificar metadados
            assert 'metadata' in result, \
                "Resultado deve incluir metadados"
            assert 'is_excessive_negotiation' in result['metadata'], \
                "Metadados devem indicar se há negociação excessiva"
            assert 'query_timestamp' in result['metadata'], \
                "Metadados devem incluir timestamp da consulta"
            
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 53: Alertas de negociações excessivas
# **Feature: sistema-pre-ordem-negociacao, Property 53: Alertas de negociações excessivas**
# **Validates: Requirements 17.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    num_proposals=proposal_count_strategy()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_53_excessive_negotiations_alert(
    test_app, client_data, provider_data, num_proposals
):
    """
    Property 53: Alertas de negociações excessivas
    
    Para qualquer pré-ordem:
    - Se tiver mais de 5 propostas, deve gerar alerta de negociação excessiva
    - O alerta deve indicar o número de propostas e o limite
    - O método check_excessive_negotiations deve retornar is_excessive=True quando >5
    - O método check_excessive_negotiations deve retornar is_excessive=False quando <=5
    - O alerta deve ter nível 'warning' quando excessivo
    
    Validates: Requirements 17.5
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
            session.add(Wallet(user_id=client.id, balance=Decimal('5000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('2000.00')))
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço para Teste de Alertas',
                service_description='Descrição do serviço',
                original_value=Decimal('1000.00'),
                delivery_date=datetime.utcnow() + timedelta(days=20),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=20)
            )
            session.add(invite)
            session.flush()
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            
            # Criar propostas
            for i in range(num_proposals):
                proposer_id = provider.id if i % 2 == 0 else client.id
                proposal = PreOrderProposal(
                    pre_order_id=pre_order.id,
                    proposed_by=proposer_id,
                    proposed_value=Decimal('1000.00') + Decimal(str(i * 50)),
                    justification='A' * 60,  # Justificativa com 60 caracteres (>50)
                    status=ProposalStatus.REJEITADA.value if i < num_proposals - 1 else ProposalStatus.PENDENTE.value
                )
                session.add(proposal)
            
            session.commit()
            
            # Verificar alertas de negociação excessiva
            result = PreOrderAuditService.check_excessive_negotiations(pre_order.id)
            
            # Verificar propriedades
            assert result['success'] is True, \
                "check_excessive_negotiations deve retornar sucesso"
            
            assert result['proposal_count'] == num_proposals, \
                f"Deve contar {num_proposals} propostas, contou {result['proposal_count']}"
            
            assert result['threshold'] == PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD, \
                "Deve retornar o limite configurado"
            
            # Verificar lógica de alerta
            expected_excessive = num_proposals > PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD
            assert result['is_excessive'] == expected_excessive, \
                f"is_excessive deve ser {expected_excessive} para {num_proposals} propostas"
            
            # Verificar nível de alerta
            if expected_excessive:
                assert result['alert_level'] == 'warning', \
                    "Nível de alerta deve ser 'warning' quando excessivo"
                assert 'alert_message' in result, \
                    "Deve incluir mensagem de alerta quando excessivo"
            else:
                assert result['alert_level'] == 'normal', \
                    "Nível de alerta deve ser 'normal' quando não excessivo"
            
        finally:
            session.rollback()


# ==============================================================================
# TESTES ADICIONAIS DE AUDITORIA
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    ip_address=st.ip_addresses(v=4).map(str),
    user_agent=st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "P")))
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_audit_log_with_ip_and_user_agent(
    test_app, client_data, provider_data, ip_address, user_agent
):
    """
    Teste adicional: Logs de auditoria com IP e user agent
    
    Para qualquer evento de auditoria:
    - O IP e user agent devem ser registrados no event_data
    - Os dados de auditoria devem ser recuperáveis
    
    Validates: Requirements 17.1, 17.2
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
            
            # Criar convite e pré-ordem
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
            
            pre_order = create_test_pre_order(session, client, provider, invite)
            session.commit()
            
            # Registrar evento de auditoria com IP e user agent
            result = PreOrderAuditService.log_audit_event(
                pre_order_id=pre_order.id,
                event_type='test_audit_event',
                actor_id=client.id,
                description='Evento de teste com dados de auditoria',
                event_data={'test_key': 'test_value'},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Verificar resultado
            assert result['success'] is True, \
                "log_audit_event deve retornar sucesso"
            
            assert result['history_id'] is not None, \
                "Deve retornar ID do registro de histórico"
            
            # Verificar que os dados foram salvos corretamente
            history_entry = PreOrderHistory.query.get(result['history_id'])
            assert history_entry is not None, \
                "Registro de histórico deve existir"
            
            assert history_entry.event_data is not None, \
                "event_data deve estar presente"
            
            assert 'audit' in history_entry.event_data, \
                "Dados de auditoria devem estar em event_data"
            
            assert history_entry.event_data['audit']['ip_address'] == ip_address, \
                "IP deve ser registrado corretamente"
            
            assert history_entry.event_data['audit']['user_agent'] == user_agent, \
                "User agent deve ser registrado corretamente"
            
        finally:
            session.rollback()


@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    value_change_percent=st.floats(min_value=-80, max_value=200)
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_extreme_proposals_detection(
    test_app, client_data, provider_data, value_change_percent
):
    """
    Teste adicional: Detecção de propostas extremas
    
    Para qualquer proposta:
    - Aumentos > 100% devem ser marcados como extremos
    - Reduções > 50% devem ser marcados como extremos
    - O relatório deve listar todas as propostas extremas
    
    Validates: Requirements 19.1-19.3
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
            session.add(Wallet(user_id=client.id, balance=Decimal('5000.00')))
            session.add(Wallet(user_id=provider.id, balance=Decimal('2000.00')))
            
            # Criar convite
            base_value = Decimal('1000.00')
            invite = Invite(
                client_id=client.id,
                invited_phone=provider.phone,
                service_title='Serviço Teste Extremo',
                service_description='Descrição',
                original_value=base_value,
                delivery_date=datetime.utcnow() + timedelta(days=10),
                status='aceito',
                expires_at=datetime.utcnow() + timedelta(days=10)
            )
            session.add(invite)
            session.flush()
            
            pre_order = create_test_pre_order(session, client, provider, invite)
            
            # Calcular valor proposto baseado na porcentagem
            proposed_value = base_value * (1 + Decimal(str(value_change_percent / 100)))
            proposed_value = max(Decimal('10.00'), proposed_value)  # Garantir valor mínimo
            
            # Criar proposta
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=proposed_value,
                justification='A' * 60,
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            session.commit()
            
            # Gerar relatório de propostas extremas
            result = PreOrderAuditService.generate_extreme_proposals_report()
            
            # Verificar propriedades
            assert result['success'] is True, \
                "generate_extreme_proposals_report deve retornar sucesso"
            
            # Verificar se a proposta foi detectada como extrema
            is_extreme_increase = value_change_percent > 100
            is_extreme_decrease = value_change_percent < -50
            should_be_extreme = is_extreme_increase or is_extreme_decrease
            
            found_in_report = any(
                p['proposal_id'] == proposal.id 
                for p in result['extreme_proposals']
            )
            
            assert found_in_report == should_be_extreme, \
                f"Proposta com {value_change_percent}% de mudança " \
                f"{'deveria' if should_be_extreme else 'não deveria'} estar no relatório"
            
        finally:
            session.rollback()
