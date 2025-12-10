#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de propriedade para o template de detalhes da pré-ordem

**Feature: sistema-pre-ordem-negociacao, Property 29-34, 41, 54**
Valida apresentação de dados, indicadores de status e informações principais
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from models import db, PreOrder, PreOrderStatus, Invite


# Estratégias para geração de dados
@st.composite
def pre_order_data(draw):
    """Gera dados válidos para uma pré-ordem"""
    current_value = draw(st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2))
    original_value = draw(st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2))
    
    title = draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs')))).strip()
    if not title:
        title = 'Título Teste'
    
    description = draw(st.text(min_size=20, max_size=500, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs')))).strip()
    if len(description) < 20:
        description = 'Descrição de teste com mais de 20 caracteres para atender requisito mínimo'
    
    return {
        'title': title,
        'description': description,
        'current_value': current_value,
        'original_value': original_value,
        'delivery_date': datetime.utcnow() + timedelta(days=draw(st.integers(min_value=1, max_value=30))),
        'service_category': draw(st.one_of(st.none(), st.text(min_size=3, max_size=50))),
        'status': draw(st.sampled_from([s.value for s in PreOrderStatus])),
        'client_accepted_terms': draw(st.booleans()),
        'provider_accepted_terms': draw(st.booleans()),
    }


class TestPreOrderTemplateProperties:
    """Testes de propriedade para o template de pré-ordem"""
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_29_title_always_present(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 29: Título sempre presente**
        **Validates: Requirements 9.2, 18.1**
        
        Para qualquer pré-ordem, o título deve sempre estar presente no modelo
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.title is not None
            assert len(pre_order.title) > 0
            assert pre_order.title == data['title']
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_30_value_information_complete(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 30: Informações de valor completas**
        **Validates: Requirements 9.2, 10.2**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.current_value is not None
            assert pre_order.original_value is not None
            assert pre_order.current_value > 0
            assert pre_order.original_value > 0
            
            expected_diff = data['current_value'] - data['original_value']
            assert pre_order.value_difference_from_original == expected_diff


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_31_delivery_date_present(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 31: Prazo de entrega presente**
        **Validates: Requirements 9.2, 18.1**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.delivery_date is not None
            assert pre_order.delivery_date == data['delivery_date']
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_32_description_present(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 32: Descrição presente**
        **Validates: Requirements 9.3, 18.1**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.description is not None
            assert len(pre_order.description) >= 20
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_33_parties_information_present(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 33: Informações das partes presentes**
        **Validates: Requirements 10.1, 18.1**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.client_id is not None
            assert pre_order.provider_id is not None
            assert pre_order.client is not None
            assert pre_order.provider is not None
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_34_acceptance_status_present(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 34: Status de aceitação presente**
        **Validates: Requirements 10.3, 10.4**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.client_accepted_terms is not None
            assert pre_order.provider_accepted_terms is not None
            assert isinstance(pre_order.client_accepted_terms, bool)
            assert isinstance(pre_order.provider_accepted_terms, bool)
    
    @given(status=st.sampled_from([s.value for s in PreOrderStatus]))
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_41_status_indicators_correct(self, app, db_session, test_user, test_provider, status):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 41: Indicadores de status corretos**
        **Validates: Requirements 13.1, 13.2, 13.3, 13.4**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição teste com mais de 20 caracteres',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Teste',
                description='Descrição teste com mais de 20 caracteres',
                current_value=Decimal('100.00'),
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status=status,
                client_accepted_terms=False,
                provider_accepted_terms=False,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.status == status
            assert pre_order.status_display is not None
            assert len(pre_order.status_display) > 0
            assert pre_order.status_color_class is not None
            assert pre_order.status_color_class.startswith('bg-')
    
    @given(data=pre_order_data())
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_54_main_information_accessible(self, app, db_session, test_user, test_provider, data):
        """
        **Feature: sistema-pre-ordem-negociacao, Property 54: Informações principais acessíveis**
        **Validates: Requirements 18.1**
        """
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title=data['title'],
                service_description=data['description'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=test_user.id,
                provider_id=test_provider.id,
                title=data['title'],
                description=data['description'],
                current_value=data['current_value'],
                original_value=data['original_value'],
                delivery_date=data['delivery_date'],
                service_category=data['service_category'],
                status=data['status'],
                client_accepted_terms=data['client_accepted_terms'],
                provider_accepted_terms=data['provider_accepted_terms'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(pre_order)
            db_session.commit()
            
            assert pre_order.title is not None and len(pre_order.title) > 0
            assert pre_order.description is not None and len(pre_order.description) >= 20
            assert pre_order.current_value is not None and pre_order.current_value > 0
            assert pre_order.original_value is not None and pre_order.original_value > 0
            assert pre_order.delivery_date is not None
            assert pre_order.status is not None
            assert pre_order.client is not None
            assert pre_order.provider is not None
