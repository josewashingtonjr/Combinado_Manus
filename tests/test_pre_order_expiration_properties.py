#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para Sistema de Expiração de Pré-Ordens

Este módulo testa as propriedades de correção relacionadas à expiração de pré-ordens.

**Feature: sistema-pre-ordem-negociacao, Property 48-50: Notificações e expiração (Req 15.2-15.4)**

Requirements testados:
- 15.2: Notificação 24h antes da expiração
- 15.3: Marcação automática como expirada
- 15.4: Notificação de expiração
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, PreOrderHistory
)
from jobs.expire_pre_orders import PreOrderExpirationJob
from services.notification_service import NotificationService


# ==================== ESTRATÉGIAS DE GERAÇÃO ====================

@st.composite
def pre_order_expiring_soon_strategy(draw):
    """
    Gera pré-ordem que expirará nas próximas 24 horas
    
    Para testar Property 48: Notificação 24h antes da expiração
    """
    # Gerar tempo até expiração entre 23h e 25h (janela de notificação)
    hours_until_expiration = draw(st.floats(min_value=23.0, max_value=25.0))
    
    expires_at = datetime.utcnow() + timedelta(hours=hours_until_expiration)
    created_at = expires_at - timedelta(days=7)  # Criada 7 dias antes
    
    return {
        'title': draw(st.text(min_size=5, max_size=100)),
        'description': draw(st.text(min_size=10, max_size=500)),
        'current_value': draw(st.decimals(min_value=10, max_value=10000, places=2)),
        'original_value': draw(st.decimals(min_value=10, max_value=10000, places=2)),
        'delivery_date': expires_at + timedelta(days=1),
        'status': draw(st.sampled_from([
            PreOrderStatus.EM_NEGOCIACAO.value,
            PreOrderStatus.AGUARDANDO_RESPOSTA.value
        ])),
        'created_at': created_at,
        'expires_at': expires_at
    }


@st.composite
def pre_order_expired_strategy(draw):
    """
    Gera pré-ordem que já expirou
    
    Para testar Property 49-50: Marcação e notificação de expiração
    """
    # Gerar tempo desde expiração entre 1 minuto e 7 dias
    hours_since_expiration = draw(st.floats(min_value=0.017, max_value=168.0))  # 1min a 7 dias
    
    expires_at = datetime.utcnow() - timedelta(hours=hours_since_expiration)
    created_at = expires_at - timedelta(days=7)  # Criada 7 dias antes
    
    return {
        'title': draw(st.text(min_size=5, max_size=100)),
        'description': draw(st.text(min_size=10, max_size=500)),
        'current_value': draw(st.decimals(min_value=10, max_value=10000, places=2)),
        'original_value': draw(st.decimals(min_value=10, max_value=10000, places=2)),
        'delivery_date': expires_at + timedelta(days=1),
        'status': draw(st.sampled_from([
            PreOrderStatus.EM_NEGOCIACAO.value,
            PreOrderStatus.AGUARDANDO_RESPOSTA.value,
            PreOrderStatus.PRONTO_CONVERSAO.value
        ])),
        'created_at': created_at,
        'expires_at': expires_at
    }


# ==================== FIXTURES ====================

@pytest.fixture
def setup_users(app):
    """Cria usuários de teste"""
    with app.app_context():
        # Limpar dados existentes
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        
        # Criar cliente
        client = User(
            email='cliente@test.com',
            nome='Cliente Teste',
            cpf='12345678901',
            phone='11999999999'
        )
        client.set_password('senha123')
        db.session.add(client)
        
        # Criar prestador
        provider = User(
            email='prestador@test.com',
            nome='Prestador Teste',
            cpf='98765432100',
            phone='11888888888'
        )
        provider.set_password('senha123')
        db.session.add(provider)
        
        db.session.commit()
        
        yield {
            'client': client,
            'provider': provider
        }
        
        # Cleanup
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        db.session.commit()


# ==================== PROPERTY 48: NOTIFICAÇÃO 24H ANTES ====================

@given(pre_order_data=pre_order_expiring_soon_strategy())
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_48_expiring_soon_notification(app, setup_users, pre_order_data):
    """
    **Property 48: Notificação 24h antes da expiração**
    
    Para qualquer pré-ordem que expirará nas próximas 24 horas,
    o sistema deve enviar notificação de aviso para ambas as partes.
    
    **Validates: Requirements 15.2**
    """
    with app.app_context():
        # Limpar dados antes de cada teste
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.commit()
        
        users = setup_users
        
        # Criar convite
        invite = Invite(
            client_id=users['client'].id,
            invited_phone=users['provider'].phone,
            service_title=pre_order_data['title'],
            service_description=pre_order_data['description'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status='aceito',
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar pré-ordem expirando em breve
        pre_order = PreOrder(
            invite_id=invite.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id,
            title=pre_order_data['title'],
            description=pre_order_data['description'],
            current_value=pre_order_data['current_value'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status=pre_order_data['status'],
            created_at=pre_order_data['created_at'],
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(pre_order)
        db.session.commit()
        
        # Executar verificação de pré-ordens expirando
        result = PreOrderExpirationJob.check_expiring_soon()
        
        # PROPRIEDADE: Deve ter verificado e notificado a pré-ordem
        assert result['success'], "Job deve executar com sucesso"
        assert result['checked'] >= 1, "Deve ter verificado pelo menos 1 pré-ordem"
        assert result['notified'] >= 1, "Deve ter notificado pelo menos 1 pré-ordem"
        
        # Verificar que foi registrado no histórico
        warning_history = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order.id,
            event_type='expiration_warning'
        ).first()
        
        assert warning_history is not None, "Deve ter registrado aviso no histórico"
        assert warning_history.event_data is not None, "Deve ter dados do evento"
        assert 'hours_remaining' in warning_history.event_data, "Deve ter horas restantes"
        
        # Verificar que não envia notificação duplicada
        result2 = PreOrderExpirationJob.check_expiring_soon()
        assert result2['notified'] == 0, "Não deve enviar notificação duplicada"


# ==================== PROPERTY 49: MARCAÇÃO AUTOMÁTICA ====================

@given(pre_order_data=pre_order_expired_strategy())
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_49_automatic_expiration(app, setup_users, pre_order_data):
    """
    **Property 49: Marcação automática como expirada**
    
    Para qualquer pré-ordem que ultrapassou o prazo de expiração,
    o sistema deve marcar automaticamente como EXPIRADA.
    
    **Validates: Requirements 15.3**
    """
    with app.app_context():
        # Limpar dados antes de cada teste
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.commit()
        
        users = setup_users
        
        # Criar convite
        invite = Invite(
            client_id=users['client'].id,
            invited_phone=users['provider'].phone,
            service_title=pre_order_data['title'],
            service_description=pre_order_data['description'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status='aceito',
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar pré-ordem expirada
        pre_order = PreOrder(
            invite_id=invite.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id,
            title=pre_order_data['title'],
            description=pre_order_data['description'],
            current_value=pre_order_data['current_value'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status=pre_order_data['status'],
            created_at=pre_order_data['created_at'],
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(pre_order)
        db.session.commit()
        
        previous_status = pre_order.status
        
        # Executar marcação de pré-ordens expiradas
        result = PreOrderExpirationJob.expire_overdue()
        
        # PROPRIEDADE: Deve ter marcado como expirada
        assert result['success'], "Job deve executar com sucesso"
        assert result['checked'] >= 1, "Deve ter verificado pelo menos 1 pré-ordem"
        assert result['expired'] >= 1, "Deve ter expirado pelo menos 1 pré-ordem"
        
        # Recarregar pré-ordem do banco
        db.session.refresh(pre_order)
        
        # Verificar que status mudou para EXPIRADA
        assert pre_order.status == PreOrderStatus.EXPIRADA.value, \
            f"Status deve ser EXPIRADA, mas é {pre_order.status}"
        
        # Verificar que foi registrado no histórico
        expired_history = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order.id,
            event_type='expired'
        ).first()
        
        assert expired_history is not None, "Deve ter registrado expiração no histórico"
        assert expired_history.event_data is not None, "Deve ter dados do evento"
        assert expired_history.event_data['previous_status'] == previous_status, \
            "Deve ter registrado status anterior"


# ==================== PROPERTY 50: NOTIFICAÇÃO DE EXPIRAÇÃO ====================

@given(pre_order_data=pre_order_expired_strategy())
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_property_50_expiration_notification(app, setup_users, pre_order_data):
    """
    **Property 50: Notificação de expiração**
    
    Para qualquer pré-ordem que foi marcada como expirada,
    o sistema deve enviar notificação para ambas as partes.
    
    **Validates: Requirements 15.4**
    """
    with app.app_context():
        # Limpar dados antes de cada teste
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.commit()
        
        users = setup_users
        
        # Criar convite
        invite = Invite(
            client_id=users['client'].id,
            invited_phone=users['provider'].phone,
            service_title=pre_order_data['title'],
            service_description=pre_order_data['description'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status='aceito',
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar pré-ordem expirada
        pre_order = PreOrder(
            invite_id=invite.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id,
            title=pre_order_data['title'],
            description=pre_order_data['description'],
            current_value=pre_order_data['current_value'],
            original_value=pre_order_data['original_value'],
            delivery_date=pre_order_data['delivery_date'],
            status=pre_order_data['status'],
            created_at=pre_order_data['created_at'],
            expires_at=pre_order_data['expires_at']
        )
        db.session.add(pre_order)
        db.session.commit()
        
        # Executar marcação de pré-ordens expiradas (que também notifica)
        result = PreOrderExpirationJob.expire_overdue()
        
        # PROPRIEDADE: Deve ter executado com sucesso
        assert result['success'], "Job deve executar com sucesso"
        
        # Recarregar pré-ordem
        db.session.refresh(pre_order)
        
        # Verificar que status é EXPIRADA
        assert pre_order.status == PreOrderStatus.EXPIRADA.value, \
            "Status deve ser EXPIRADA"
        
        # Testar notificação diretamente
        notification_result = NotificationService.notify_pre_order_expired(
            pre_order_id=pre_order.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id
        )
        
        # PROPRIEDADE: Notificação deve ser enviada com sucesso
        assert notification_result['success'], "Notificação deve ser enviada com sucesso"
        assert notification_result['notification_type'] == 'pre_order_expired', \
            "Tipo de notificação deve ser pre_order_expired"
        assert notification_result['pre_order_id'] == pre_order.id, \
            "Deve conter ID da pré-ordem"
        assert notification_result['client_id'] == users['client'].id, \
            "Deve conter ID do cliente"
        assert notification_result['provider_id'] == users['provider'].id, \
            "Deve conter ID do prestador"
        assert 'message' in notification_result, "Deve conter mensagem"
        assert 'expirou' in notification_result['message'].lower() or \
               'expirada' in notification_result['message'].lower(), \
            "Mensagem deve mencionar expiração"


# ==================== TESTES DE INTEGRAÇÃO ====================

def test_full_expiration_flow(app, setup_users):
    """
    Teste de integração: fluxo completo de expiração
    
    1. Criar pré-ordem expirando em breve
    2. Verificar notificação de aviso
    3. Avançar tempo
    4. Verificar marcação como expirada
    5. Verificar notificação de expiração
    """
    with app.app_context():
        users = setup_users
        
        # Criar pré-ordem expirando em 24h
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        invite = Invite(
            client_id=users['client'].id,
            invited_phone=users['provider'].phone,
            service_title='Serviço Teste',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            delivery_date=expires_at + timedelta(days=1),
            status='aceito',
            expires_at=expires_at
        )
        db.session.add(invite)
        db.session.flush()
        
        pre_order = PreOrder(
            invite_id=invite.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id,
            title='Serviço Teste',
            description='Descrição teste',
            current_value=Decimal('100.00'),
            original_value=Decimal('100.00'),
            delivery_date=expires_at + timedelta(days=1),
            status=PreOrderStatus.EM_NEGOCIACAO.value,
            expires_at=expires_at
        )
        db.session.add(pre_order)
        db.session.commit()
        
        # Etapa 1: Verificar notificação de aviso
        result1 = PreOrderExpirationJob.check_expiring_soon()
        assert result1['success']
        assert result1['notified'] >= 1
        
        # Verificar histórico de aviso
        warning = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order.id,
            event_type='expiration_warning'
        ).first()
        assert warning is not None
        
        # Etapa 2: Criar uma segunda pré-ordem já expirada
        expired_at = datetime.utcnow() - timedelta(hours=1)
        created_at_expired = expired_at - timedelta(days=7)
        
        invite2 = Invite(
            client_id=users['client'].id,
            invited_phone=users['provider'].phone,
            service_title='Serviço Teste Expirado',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            delivery_date=expired_at + timedelta(days=1),
            status='aceito',
            expires_at=expired_at
        )
        db.session.add(invite2)
        db.session.flush()
        
        pre_order_expired = PreOrder(
            invite_id=invite2.id,
            client_id=users['client'].id,
            provider_id=users['provider'].id,
            title='Serviço Teste Expirado',
            description='Descrição teste',
            current_value=Decimal('100.00'),
            original_value=Decimal('100.00'),
            delivery_date=expired_at + timedelta(days=1),
            status=PreOrderStatus.EM_NEGOCIACAO.value,
            created_at=created_at_expired,
            expires_at=expired_at
        )
        db.session.add(pre_order_expired)
        db.session.commit()
        
        # Etapa 3: Verificar marcação como expirada
        result2 = PreOrderExpirationJob.expire_overdue()
        assert result2['success']
        assert result2['expired'] >= 1
        
        # Recarregar do banco (o job faz commit)
        db.session.expire_all()
        pre_order_expired = PreOrder.query.get(pre_order_expired.id)
        
        # Verificar status
        assert pre_order_expired.status == PreOrderStatus.EXPIRADA.value
        
        # Verificar histórico de expiração
        expired = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order_expired.id,
            event_type='expired'
        ).first()
        assert expired is not None
