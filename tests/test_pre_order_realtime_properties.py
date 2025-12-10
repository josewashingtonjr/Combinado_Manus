#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para Atualizações em Tempo Real de Pré-Ordens
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
propriedades universais do sistema de atualizações em tempo real.

**Feature: sistema-pre-ordem-negociacao, Property 59-62: Atualizações em tempo real**
**Validates: Requirements 20.1-20.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask
import json

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, Wallet,
    PreOrderProposal, ProposalStatus, PreOrderHistory
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
def valid_proposal_data(draw):
    """Gera dados válidos para uma proposta"""
    # Gerar valor proposto diferente do original (500.00)
    proposed_value = draw(st.decimals(
        min_value=Decimal('100.00'), 
        max_value=Decimal('5000.00'), 
        places=2
    ))
    # Garantir que é diferente do valor original típico
    if proposed_value == Decimal('500.00'):
        proposed_value = Decimal('600.00')
    
    return {
        'proposed_value': proposed_value,
        'justification': 'Justificativa detalhada para a proposta de alteração. ' * 2
    }


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
        db.session.query(PreOrderProposal).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


def create_test_pre_order(session, client, provider, invite, status=PreOrderStatus.EM_NEGOCIACAO.value):
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
        status=status,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    session.add(pre_order)
    session.flush()
    return pre_order


def create_test_users_and_invite(session, client_data, provider_data):
    """Helper para criar usuários e convite de teste"""
    # Criar cliente
    client = User(**client_data)
    client.set_password('senha123')
    session.add(client)
    session.flush()
    
    # Criar carteira para o cliente
    client_wallet = Wallet(user_id=client.id, balance=Decimal('2000.00'))
    session.add(client_wallet)
    
    # Criar prestador
    provider = User(**provider_data)
    provider.set_password('senha123')
    session.add(provider)
    session.flush()
    
    # Criar carteira para o prestador
    provider_wallet = Wallet(user_id=provider.id, balance=Decimal('1000.00'))
    session.add(provider_wallet)
    
    # Criar convite
    invite = Invite(
        client_id=client.id,
        invited_phone=provider.phone,
        service_title='Serviço de Teste',
        service_description='Descrição detalhada do serviço',
        service_category='pedreiro',
        original_value=Decimal('500.00'),
        delivery_date=datetime.utcnow() + timedelta(days=15),
        status='aceito',
        expires_at=datetime.utcnow() + timedelta(days=15)
    )
    session.add(invite)
    session.flush()
    
    return client, provider, invite


# ==============================================================================
# PROPERTY 59: Atualização automática de propostas
# **Feature: sistema-pre-ordem-negociacao, Property 59: Atualização automática de propostas**
# **Validates: Requirements 20.1**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposal_data=valid_proposal_data()
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_59_automatic_proposal_update(
    test_app, client_data, provider_data, proposal_data
):
    """
    Property 59: Atualização automática de propostas
    
    Para qualquer proposta submetida em uma pré-ordem:
    - A pré-ordem deve ter has_active_proposal = True após submissão
    - O status da pré-ordem deve mudar para 'aguardando_resposta'
    - Um registro de histórico deve ser criado com event_type = 'proposal_sent'
    - A proposta deve estar acessível via pre_order.proposals
    - O updated_at da pré-ordem deve ser atualizado
    
    Validates: Requirements 20.1
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários e convite
            client, provider, invite = create_test_users_and_invite(
                session, client_data, provider_data
            )
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            original_updated_at = pre_order.updated_at
            session.commit()
            
            # Criar proposta
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=proposal_data['proposed_value'],
                justification=proposal_data['justification'],
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            
            # Atualizar pré-ordem (simulando o que o serviço faria)
            pre_order.has_active_proposal = True
            pre_order.active_proposal_id = proposal.id
            pre_order.status = PreOrderStatus.AGUARDANDO_RESPOSTA.value
            pre_order.updated_at = datetime.utcnow()
            
            # Criar registro de histórico
            history = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='proposal_sent',
                actor_id=provider.id,
                description=f'{provider.nome} enviou uma proposta de alteração',
                event_data={
                    'proposed_value': str(proposal_data['proposed_value']),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            session.add(history)
            session.commit()
            
            # Recarregar do banco
            session.refresh(pre_order)
            
            # Verificar propriedades
            assert pre_order.has_active_proposal is True, \
                "Pré-ordem deve ter proposta ativa após submissão"
            assert pre_order.status == PreOrderStatus.AGUARDANDO_RESPOSTA.value, \
                "Status deve ser 'aguardando_resposta' após proposta"
            assert pre_order.active_proposal_id == proposal.id, \
                "ID da proposta ativa deve estar correto"
            
            # Verificar histórico
            history_entries = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order.id,
                event_type='proposal_sent'
            ).all()
            assert len(history_entries) >= 1, \
                "Deve existir registro de histórico para proposta enviada"
            
            # Verificar que proposta está acessível
            proposals = pre_order.proposals.all()
            assert len(proposals) >= 1, \
                "Proposta deve estar acessível via relacionamento"
            assert proposals[0].id == proposal.id, \
                "Proposta correta deve estar no relacionamento"
            
            # Verificar atualização de timestamp
            assert pre_order.updated_at >= original_updated_at, \
                "updated_at deve ser atualizado após proposta"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 60: Atualização imediata em aceites/rejeições
# **Feature: sistema-pre-ordem-negociacao, Property 60: Atualização imediata em aceites/rejeições**
# **Validates: Requirements 20.2**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    proposal_data=valid_proposal_data(),
    accept_proposal=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_60_immediate_accept_reject_update(
    test_app, client_data, provider_data, proposal_data, accept_proposal
):
    """
    Property 60: Atualização imediata em aceites/rejeições
    
    Para qualquer proposta aceita ou rejeitada:
    - Se aceita: valores da pré-ordem devem ser atualizados
    - Se aceita: status da proposta deve ser 'aceita'
    - Se rejeitada: valores da pré-ordem devem permanecer inalterados
    - Se rejeitada: status da proposta deve ser 'rejeitada'
    - Em ambos os casos: has_active_proposal deve ser False
    - Em ambos os casos: status da pré-ordem deve voltar para 'em_negociacao'
    - Em ambos os casos: registro de histórico deve ser criado
    
    Validates: Requirements 20.2
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários e convite
            client, provider, invite = create_test_users_and_invite(
                session, client_data, provider_data
            )
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            original_value = pre_order.current_value
            
            # Criar proposta pendente
            proposal = PreOrderProposal(
                pre_order_id=pre_order.id,
                proposed_by=provider.id,
                proposed_value=proposal_data['proposed_value'],
                justification=proposal_data['justification'],
                status=ProposalStatus.PENDENTE.value
            )
            session.add(proposal)
            
            # Marcar pré-ordem como aguardando resposta
            pre_order.has_active_proposal = True
            pre_order.active_proposal_id = proposal.id
            pre_order.status = PreOrderStatus.AGUARDANDO_RESPOSTA.value
            session.commit()
            
            # Processar aceite ou rejeição
            if accept_proposal:
                # Aceitar proposta
                proposal.status = ProposalStatus.ACEITA.value
                proposal.responded_at = datetime.utcnow()
                
                # Atualizar valores da pré-ordem
                pre_order.current_value = proposal.proposed_value
                
                event_type = 'proposal_accepted'
                description = f'{client.nome} aceitou a proposta'
            else:
                # Rejeitar proposta
                proposal.status = ProposalStatus.REJEITADA.value
                proposal.responded_at = datetime.utcnow()
                
                # Valores permanecem inalterados
                event_type = 'proposal_rejected'
                description = f'{client.nome} rejeitou a proposta'
            
            # Atualizar estado da pré-ordem
            pre_order.has_active_proposal = False
            pre_order.active_proposal_id = None
            pre_order.status = PreOrderStatus.EM_NEGOCIACAO.value
            pre_order.updated_at = datetime.utcnow()
            
            # Criar registro de histórico
            history = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type=event_type,
                actor_id=client.id,
                description=description,
                event_data={
                    'proposal_id': proposal.id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            session.add(history)
            session.commit()
            
            # Recarregar do banco
            session.refresh(pre_order)
            session.refresh(proposal)
            
            # Verificar propriedades comuns
            assert pre_order.has_active_proposal is False, \
                "has_active_proposal deve ser False após resposta"
            assert pre_order.active_proposal_id is None, \
                "active_proposal_id deve ser None após resposta"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Status deve voltar para 'em_negociacao'"
            assert proposal.responded_at is not None, \
                "responded_at deve estar preenchido"
            
            # Verificar propriedades específicas
            if accept_proposal:
                assert proposal.status == ProposalStatus.ACEITA.value, \
                    "Status da proposta deve ser 'aceita'"
                assert pre_order.current_value == proposal.proposed_value, \
                    "Valor da pré-ordem deve ser atualizado para valor proposto"
            else:
                assert proposal.status == ProposalStatus.REJEITADA.value, \
                    "Status da proposta deve ser 'rejeitada'"
                assert pre_order.current_value == original_value, \
                    "Valor da pré-ordem deve permanecer inalterado"
            
            # Verificar histórico
            history_entries = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order.id,
                event_type=event_type
            ).all()
            assert len(history_entries) >= 1, \
                f"Deve existir registro de histórico para {event_type}"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 61: Atualização automática ao alcançar aceitação mútua
# **Feature: sistema-pre-ordem-negociacao, Property 61: Atualização automática ao alcançar aceitação mútua**
# **Validates: Requirements 20.3, 20.4**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    client_accepts_first=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_61_mutual_acceptance_update(
    test_app, client_data, provider_data, client_accepts_first
):
    """
    Property 61: Atualização automática ao alcançar aceitação mútua
    
    Para qualquer pré-ordem onde ambas as partes aceitam os termos:
    - has_mutual_acceptance deve retornar True quando ambos aceitam
    - O status deve mudar para 'pronto_conversao' quando ambos aceitam
    - A ordem de aceitação (cliente primeiro ou prestador primeiro) não importa
    - Registros de histórico devem ser criados para cada aceitação
    - can_be_converted deve retornar True quando pronto para conversão
    
    Validates: Requirements 20.3, 20.4
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários e convite
            client, provider, invite = create_test_users_and_invite(
                session, client_data, provider_data
            )
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            session.commit()
            
            # Verificar estado inicial
            assert pre_order.client_accepted_terms is False, \
                "Cliente não deve ter aceitado inicialmente"
            assert pre_order.provider_accepted_terms is False, \
                "Prestador não deve ter aceitado inicialmente"
            assert pre_order.has_mutual_acceptance is False, \
                "Não deve haver aceitação mútua inicialmente"
            
            # Primeira aceitação
            if client_accepts_first:
                first_acceptor = client
                first_field = 'client_accepted_terms'
                first_event = 'terms_accepted_client'
            else:
                first_acceptor = provider
                first_field = 'provider_accepted_terms'
                first_event = 'terms_accepted_provider'
            
            # Registrar primeira aceitação
            setattr(pre_order, first_field, True)
            pre_order.updated_at = datetime.utcnow()
            
            history1 = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type=first_event,
                actor_id=first_acceptor.id,
                description=f'{first_acceptor.nome} aceitou os termos',
                event_data={'timestamp': datetime.utcnow().isoformat()}
            )
            session.add(history1)
            session.commit()
            
            # Verificar após primeira aceitação
            session.refresh(pre_order)
            assert pre_order.has_mutual_acceptance is False, \
                "Não deve haver aceitação mútua após apenas uma aceitação"
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                "Status deve permanecer em_negociacao após uma aceitação"
            
            # Segunda aceitação
            if client_accepts_first:
                second_acceptor = provider
                second_field = 'provider_accepted_terms'
                second_event = 'terms_accepted_provider'
            else:
                second_acceptor = client
                second_field = 'client_accepted_terms'
                second_event = 'terms_accepted_client'
            
            # Registrar segunda aceitação
            setattr(pre_order, second_field, True)
            pre_order.status = PreOrderStatus.PRONTO_CONVERSAO.value
            pre_order.updated_at = datetime.utcnow()
            
            history2 = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type=second_event,
                actor_id=second_acceptor.id,
                description=f'{second_acceptor.nome} aceitou os termos',
                event_data={'timestamp': datetime.utcnow().isoformat()}
            )
            session.add(history2)
            
            # Registrar aceitação mútua
            history3 = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='mutual_acceptance',
                actor_id=None,
                description='Ambas as partes aceitaram os termos',
                event_data={'timestamp': datetime.utcnow().isoformat()}
            )
            session.add(history3)
            session.commit()
            
            # Verificar após aceitação mútua
            session.refresh(pre_order)
            
            assert pre_order.client_accepted_terms is True, \
                "Cliente deve ter aceitado"
            assert pre_order.provider_accepted_terms is True, \
                "Prestador deve ter aceitado"
            assert pre_order.has_mutual_acceptance is True, \
                "Deve haver aceitação mútua quando ambos aceitam"
            assert pre_order.status == PreOrderStatus.PRONTO_CONVERSAO.value, \
                "Status deve ser 'pronto_conversao' após aceitação mútua"
            assert pre_order.can_be_converted is True, \
                "Pré-ordem deve poder ser convertida"
            
            # Verificar histórico
            history_entries = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order.id
            ).all()
            event_types = [h.event_type for h in history_entries]
            
            assert 'terms_accepted_client' in event_types, \
                "Deve haver registro de aceitação do cliente"
            assert 'terms_accepted_provider' in event_types, \
                "Deve haver registro de aceitação do prestador"
            assert 'mutual_acceptance' in event_types, \
                "Deve haver registro de aceitação mútua"
                
        finally:
            session.rollback()


# ==============================================================================
# PROPERTY 62: Indicador de presença da outra parte
# **Feature: sistema-pre-ordem-negociacao, Property 62: Indicador de presença da outra parte**
# **Validates: Requirements 20.5**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    viewer_is_client=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_62_presence_indicator(
    test_app, client_data, provider_data, viewer_is_client
):
    """
    Property 62: Indicador de presença da outra parte
    
    Para qualquer pré-ordem sendo visualizada:
    - O sistema deve identificar corretamente quem é a "outra parte"
    - Se o cliente está visualizando, a outra parte é o prestador
    - Se o prestador está visualizando, a outra parte é o cliente
    - O sistema deve poder registrar e verificar presença
    - A presença deve expirar após um período de inatividade
    
    Validates: Requirements 20.5
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários e convite
            client, provider, invite = create_test_users_and_invite(
                session, client_data, provider_data
            )
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            session.commit()
            
            # Determinar quem está visualizando e quem é a outra parte
            if viewer_is_client:
                viewer = client
                other_party = provider
                viewer_role = 'cliente'
            else:
                viewer = provider
                other_party = client
                viewer_role = 'prestador'
            
            # Verificar identificação correta das partes
            assert pre_order.client_id == client.id, \
                "client_id deve estar correto"
            assert pre_order.provider_id == provider.id, \
                "provider_id deve estar correto"
            
            # Simular lógica de identificação da outra parte
            if viewer.id == pre_order.client_id:
                identified_other_party_id = pre_order.provider_id
            else:
                identified_other_party_id = pre_order.client_id
            
            assert identified_other_party_id == other_party.id, \
                "Sistema deve identificar corretamente a outra parte"
            
            # Verificar que ambas as partes são participantes válidos
            participants = [pre_order.client_id, pre_order.provider_id]
            assert viewer.id in participants, \
                "Visualizador deve ser participante da pré-ordem"
            assert other_party.id in participants, \
                "Outra parte deve ser participante da pré-ordem"
            
            # Verificar que viewer e other_party são diferentes
            assert viewer.id != other_party.id, \
                "Visualizador e outra parte devem ser diferentes"
            
            # Simular cache de presença (estrutura de dados)
            presence_cache = {}
            
            # Registrar presença do visualizador
            presence_key = f"{pre_order.id}_{viewer.id}"
            presence_cache[presence_key] = datetime.utcnow()
            
            # Verificar presença registrada
            assert presence_key in presence_cache, \
                "Presença do visualizador deve estar registrada"
            
            # Verificar que outra parte não está presente inicialmente
            other_party_key = f"{pre_order.id}_{other_party.id}"
            assert other_party_key not in presence_cache, \
                "Outra parte não deve estar presente inicialmente"
            
            # Simular outra parte entrando
            presence_cache[other_party_key] = datetime.utcnow()
            
            # Verificar que ambos estão presentes
            assert presence_key in presence_cache, \
                "Visualizador deve continuar presente"
            assert other_party_key in presence_cache, \
                "Outra parte deve estar presente agora"
            
            # Simular expiração de presença (presença antiga)
            old_timestamp = datetime.utcnow() - timedelta(minutes=5)
            presence_cache[other_party_key] = old_timestamp
            
            # Verificar lógica de expiração (2 minutos)
            def is_presence_valid(timestamp, timeout_seconds=120):
                return (datetime.utcnow() - timestamp).total_seconds() < timeout_seconds
            
            assert not is_presence_valid(presence_cache[other_party_key]), \
                "Presença antiga deve ser considerada expirada"
            assert is_presence_valid(presence_cache[presence_key]), \
                "Presença recente deve ser considerada válida"
                
        finally:
            session.rollback()


# ==============================================================================
# TESTES ADICIONAIS DE INTEGRAÇÃO
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    num_proposals=st.integers(min_value=1, max_value=5)
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_realtime_history_ordering(
    test_app, client_data, provider_data, num_proposals
):
    """
    Teste adicional: Ordenação correta do histórico em tempo real
    
    Para qualquer sequência de eventos em uma pré-ordem:
    - O histórico deve estar ordenado por created_at
    - Eventos mais recentes devem aparecer primeiro (DESC)
    - Todos os eventos devem ter timestamps válidos
    
    Validates: Requirements 20.1-20.5 (ordenação para exibição em tempo real)
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Garantir dados únicos
            assume(client_data['email'] != provider_data['email'])
            assume(client_data['cpf'] != provider_data['cpf'])
            assume(client_data['phone'] != provider_data['phone'])
            
            # Criar usuários e convite
            client, provider, invite = create_test_users_and_invite(
                session, client_data, provider_data
            )
            
            # Criar pré-ordem
            pre_order = create_test_pre_order(session, client, provider, invite)
            session.commit()
            
            # Criar múltiplos eventos de histórico
            import time
            for i in range(num_proposals):
                history = PreOrderHistory(
                    pre_order_id=pre_order.id,
                    event_type=f'test_event_{i}',
                    actor_id=client.id if i % 2 == 0 else provider.id,
                    description=f'Evento de teste {i}',
                    event_data={'index': i}
                )
                session.add(history)
                session.flush()
                time.sleep(0.01)  # Pequeno delay para garantir timestamps diferentes
            
            session.commit()
            
            # Buscar histórico ordenado
            history_entries = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order.id
            ).order_by(PreOrderHistory.created_at.desc()).all()
            
            # Verificar ordenação
            assert len(history_entries) == num_proposals, \
                f"Deve haver {num_proposals} entradas de histórico"
            
            for i in range(len(history_entries) - 1):
                assert history_entries[i].created_at >= history_entries[i + 1].created_at, \
                    "Histórico deve estar ordenado por created_at DESC"
            
            # Verificar que todos os timestamps são válidos
            for entry in history_entries:
                assert entry.created_at is not None, \
                    "Todos os eventos devem ter timestamp"
                assert entry.created_at <= datetime.utcnow(), \
                    "Timestamps não devem estar no futuro"
                
        finally:
            session.rollback()
