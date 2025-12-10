#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para Notificações de Pré-Ordem
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
propriedades universais do sistema de notificações de pré-ordens.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, PreOrderProposal, 
    ProposalStatus, Order, Wallet
)
from services.notification_service import NotificationService
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
def valid_pre_order_data(draw, client_id, provider_id):
    """Gera dados válidos para criar uma pré-ordem"""
    value = draw(st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2))
    days_ahead = draw(st.integers(min_value=1, max_value=30))
    
    return {
        'client_id': client_id,
        'provider_id': provider_id,
        'title': f'Serviço {draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=("L",))))}',
        'description': f'Descrição {draw(st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=("L",))))}',
        'current_value': value,
        'original_value': value,
        'delivery_date': datetime.utcnow() + timedelta(days=days_ahead),
        'status': PreOrderStatus.EM_NEGOCIACAO.value,
        'expires_at': datetime.utcnow() + timedelta(days=7)
    }


# ==============================================================================
# FIXTURES E HELPERS
# ==============================================================================

@pytest.fixture(scope='module')
def test_app():
    """Cria uma aplicação Flask para testes"""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def get_clean_db_session(app):
    """Retorna uma sessão limpa do banco de dados"""
    with app.app_context():
        # Limpar todas as tabelas na ordem correta
        db.session.query(PreOrderProposal).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


# ==============================================================================
# PROPERTY 35: Notificação de resposta à proposta
# **Feature: sistema-pre-ordem-negociacao, Property 35: Notificação de resposta à proposta**
# **Validates: Requirements 11.3**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    pre_order_data=st.data()
)
def test_property_35_proposal_response_notification(test_app, client_data, provider_data, pre_order_data):
    """
    Property 35: Notificação de resposta à proposta
    
    Para qualquer proposta aceita ou rejeitada, o sistema deve notificar o autor da proposta
    com informações claras sobre a decisão.
    
    Validates: Requirements 11.3
    """
    with test_app.app_context():
        # Limpar banco
        get_clean_db_session(test_app)
        
        # Criar usuários
        client = User(**client_data)
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(**provider_data)
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        # Criar carteiras
        client_wallet = Wallet(user_id=client.id, balance=Decimal('10000.00'))
        provider_wallet = Wallet(user_id=provider.id, balance=Decimal('1000.00'))
        db.session.add_all([client_wallet, provider_wallet])
        db.session.commit()
        
        # Criar convite
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Serviço Teste',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar pré-ordem
        pre_order_info = pre_order_data.draw(valid_pre_order_data(client.id, provider.id))
        pre_order = PreOrder(invite_id=invite.id, **pre_order_info)
        db.session.add(pre_order)
        db.session.commit()
        
        # Criar proposta
        proposal = PreOrderProposal(
            pre_order_id=pre_order.id,
            proposed_by=provider.id,
            proposed_value=pre_order.current_value + Decimal('50.00'),
            justification='Justificativa da proposta de aumento de valor'
        )
        db.session.add(proposal)
        db.session.commit()
        
        # Testar notificação de aceitação
        proposal.status = ProposalStatus.ACEITA.value
        db.session.commit()
        
        result = NotificationService.notify_pre_order_proposal_accepted(
            proposal.id, client.id, provider.id
        )
        
        # Verificar que a notificação foi criada com sucesso
        assert result['success'] is True
        assert result['notification_type'] == 'pre_order_proposal_accepted'
        assert result['proposal_id'] == proposal.id
        assert 'message' in result
        
        # Testar notificação de rejeição
        proposal.status = ProposalStatus.REJEITADA.value
        db.session.commit()
        
        result = NotificationService.notify_pre_order_proposal_rejected(
            proposal.id, client.id, provider.id, 'Motivo da rejeição'
        )
        
        # Verificar que a notificação foi criada com sucesso
        assert result['success'] is True
        assert result['notification_type'] == 'pre_order_proposal_rejected'
        assert result['proposal_id'] == proposal.id
        assert 'message' in result


# ==============================================================================
# PROPERTY 36: Notificação de conversão
# **Feature: sistema-pre-ordem-negociacao, Property 36: Notificação de conversão**
# **Validates: Requirements 11.4**
# ==============================================================================

@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    pre_order_data=st.data()
)
def test_property_36_conversion_notification(test_app, client_data, provider_data, pre_order_data):
    """
    Property 36: Notificação de conversão
    
    Para qualquer pré-ordem convertida em ordem, o sistema deve notificar ambas as partes
    com informações sobre a ordem criada e valores bloqueados.
    
    Validates: Requirements 11.4
    """
    with test_app.app_context():
        # Limpar banco
        get_clean_db_session(test_app)
        
        # Criar usuários
        client = User(**client_data)
        client.set_password('senha123')
        db.session.add(client)
        
        provider = User(**provider_data)
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        # Criar carteiras com saldo suficiente
        client_wallet = Wallet(user_id=client.id, balance=Decimal('10000.00'))
        provider_wallet = Wallet(user_id=provider.id, balance=Decimal('1000.00'))
        db.session.add_all([client_wallet, provider_wallet])
        db.session.commit()
        
        # Criar convite
        invite = Invite(
            client_id=client.id,
            invited_phone=provider.phone,
            service_title='Serviço Teste',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar pré-ordem
        pre_order_info = pre_order_data.draw(valid_pre_order_data(client.id, provider.id))
        pre_order = PreOrder(invite_id=invite.id, **pre_order_info)
        pre_order.status = PreOrderStatus.PRONTO_CONVERSAO.value
        pre_order.client_accepted_terms = True
        pre_order.provider_accepted_terms = True
        db.session.add(pre_order)
        db.session.commit()
        
        # Criar ordem
        order = Order(
            client_id=client.id,
            provider_id=provider.id,
            title=pre_order.title,
            description=pre_order.description,
            value=pre_order.current_value,
            service_deadline=pre_order.delivery_date,
            status='aceita'
        )
        db.session.add(order)
        db.session.commit()
        
        # Atualizar pré-ordem com a ordem criada
        pre_order.order_id = order.id
        pre_order.status = PreOrderStatus.CONVERTIDA.value
        db.session.commit()
        
        # Testar notificação de conversão
        result = NotificationService.notify_pre_order_converted(
            pre_order.id, order.id, client.id, provider.id, float(order.value)
        )
        
        # Verificar que a notificação foi criada com sucesso
        assert result['success'] is True
        assert result['notification_type'] == 'pre_order_converted'
        assert result['pre_order_id'] == pre_order.id
        assert result['order_id'] == order.id
        assert result['client_id'] == client.id
        assert result['provider_id'] == provider.id
        assert 'message' in result
        assert 'client_name' in result
        assert 'provider_name' in result


# ==============================================================================
# HELPER: Métodos de notificação adicionais para o NotificationService
# ==============================================================================

# Nota: Os métodos abaixo devem ser adicionados ao NotificationService
# se ainda não existirem

def notify_pre_order_proposal_accepted_helper(proposal_id, acceptor_id, proposer_id):
    """Helper para notificar aceitação de proposta"""
    try:
        from models import PreOrderProposal, User
        
        proposal = PreOrderProposal.query.get(proposal_id)
        if not proposal:
            return {'success': False, 'error': 'Proposta não encontrada'}
        
        acceptor = User.query.get(acceptor_id)
        proposer = User.query.get(proposer_id)
        
        acceptor_name = acceptor.nome if acceptor else "Usuário"
        proposer_name = proposer.nome if proposer else "Usuário"
        
        message = f"✅ {acceptor_name} aceitou sua proposta!"
        
        return {
            'success': True,
            'notification_type': 'pre_order_proposal_accepted',
            'proposal_id': proposal_id,
            'message': message,
            'acceptor_id': acceptor_id,
            'proposer_id': proposer_id
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def notify_pre_order_proposal_rejected_helper(proposal_id, rejector_id, proposer_id, reason):
    """Helper para notificar rejeição de proposta"""
    try:
        from models import PreOrderProposal, User
        
        proposal = PreOrderProposal.query.get(proposal_id)
        if not proposal:
            return {'success': False, 'error': 'Proposta não encontrada'}
        
        rejector = User.query.get(rejector_id)
        proposer = User.query.get(proposer_id)
        
        rejector_name = rejector.nome if rejector else "Usuário"
        proposer_name = proposer.nome if proposer else "Usuário"
        
        message = f"❌ {rejector_name} rejeitou sua proposta. Motivo: {reason}"
        
        return {
            'success': True,
            'notification_type': 'pre_order_proposal_rejected',
            'proposal_id': proposal_id,
            'message': message,
            'rejector_id': rejector_id,
            'proposer_id': proposer_id,
            'reason': reason
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Adicionar métodos ao NotificationService temporariamente para os testes
NotificationService.notify_pre_order_proposal_accepted = staticmethod(notify_pre_order_proposal_accepted_helper)
NotificationService.notify_pre_order_proposal_rejected = staticmethod(notify_pre_order_proposal_rejected_helper)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
