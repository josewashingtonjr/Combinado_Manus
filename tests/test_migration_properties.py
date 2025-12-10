#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Propriedade para Migração de Convites → Pré-Ordens
Feature: sistema-pre-ordem-negociacao

Estes testes usam Property-Based Testing (PBT) com Hypothesis para validar
que a migração preserva todos os dados corretamente.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask

from models import (
    db, User, Invite, PreOrder, PreOrderStatus, PreOrderHistory, Wallet
)
from config import TestConfig
from migrate_invites_to_pre_orders import InviteMigrationService


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
def valid_invite_data(draw, client_id, provider_phone):
    """Gera dados válidos para criar um convite aceito"""
    value = draw(st.decimals(min_value=Decimal('10.00'), max_value=Decimal('10000.00'), places=2))
    days_ahead = draw(st.integers(min_value=1, max_value=30))
    
    # Gerar título e descrição com caracteres válidos
    title_words = draw(st.lists(
        st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=("L",))),
        min_size=2,
        max_size=5
    ))
    title = ' '.join(title_words)[:100]  # Limitar a 100 caracteres
    
    desc_words = draw(st.lists(
        st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=("L",))),
        min_size=5,
        max_size=20
    ))
    description = ' '.join(desc_words)[:500]  # Limitar a 500 caracteres
    
    return {
        'client_id': client_id,
        'invited_phone': provider_phone,
        'service_title': title if title else 'Servico Teste',
        'service_description': description if description else 'Descricao do servico de teste',
        'service_category': draw(st.sampled_from(['pedreiro', 'encanador', 'eletricista', 'pintor', 'marceneiro'])),
        'original_value': value,
        'delivery_date': datetime.utcnow() + timedelta(days=days_ahead),
        'status': 'aceito',
        'order_id': None  # Sem ordem associada
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
        # Limpar todas as tabelas na ordem correta (respeitando foreign keys)
        db.session.query(PreOrderHistory).delete()
        db.session.query(PreOrder).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        return db.session


# ==============================================================================
# PROPERTY 51: Preservação de dados na migração
# **Feature: sistema-pre-ordem-negociacao, Property 51: Preservação de dados**
# **Validates: Requirements 16.3**
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    data=st.data()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_property_51_migration_preserves_all_data(
    test_app, client_data, provider_data, data
):
    """
    Property 51: Preservação de dados na migração
    
    Para qualquer convite aceito sem ordem associada, quando migrado para pré-ordem:
    - Todos os dados do convite devem ser preservados na pré-ordem
    - title deve ser igual a service_title
    - description deve ser igual a service_description
    - current_value deve ser igual ao valor atual do convite
    - original_value deve ser igual ao valor original do convite
    - delivery_date deve ser preservado
    - service_category deve ser preservado
    - client_id deve ser preservado
    - provider_id deve corresponder ao usuário com o telefone do convite
    - Status do convite deve ser atualizado para 'convertido_pre_ordem'
    - Um registro de histórico deve ser criado
    
    Validates: Requirements 16.3
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
            
            # Criar convite aceito usando o telefone do prestador
            invite_data = data.draw(valid_invite_data(
                client_id=client.id,
                provider_phone=provider.phone
            ))
            
            invite = Invite(**invite_data)
            # Gerar token manualmente
            invite.token = Invite.generate_token()
            # Definir expires_at
            invite.expires_at = invite.delivery_date
            session.add(invite)
            session.commit()
            
            # Guardar dados originais do convite para comparação
            original_title = invite.service_title
            original_description = invite.service_description
            original_current_value = invite.current_value
            original_original_value = invite.original_value
            original_delivery_date = invite.delivery_date
            original_service_category = invite.service_category
            original_client_id = invite.client_id
            original_invite_id = invite.id
            
            # Executar migração
            migration_service = InviteMigrationService(dry_run=False)
            result = migration_service.migrate_invite_to_pre_order(invite)
            
            # Verificar que a migração foi bem-sucedida
            assert result['success'], f"Migração falhou: {result.get('error', 'Erro desconhecido')}"
            
            # Buscar a pré-ordem criada
            pre_order = PreOrder.query.filter_by(invite_id=original_invite_id).first()
            assert pre_order is not None, "Pré-ordem não foi criada"
            
            # PROPERTY: Todos os dados devem ser preservados
            
            # Verificar título
            assert pre_order.title == original_title, \
                f"Título não preservado: esperado '{original_title}', obtido '{pre_order.title}'"
            
            # Verificar descrição
            assert pre_order.description == original_description, \
                f"Descrição não preservada: esperado '{original_description}', obtido '{pre_order.description}'"
            
            # Verificar valor atual
            assert pre_order.current_value == original_current_value, \
                f"Valor atual não preservado: esperado {original_current_value}, obtido {pre_order.current_value}"
            
            # Verificar valor original
            assert pre_order.original_value == original_original_value, \
                f"Valor original não preservado: esperado {original_original_value}, obtido {pre_order.original_value}"
            
            # Verificar data de entrega
            assert pre_order.delivery_date == original_delivery_date, \
                f"Data de entrega não preservada: esperado {original_delivery_date}, obtido {pre_order.delivery_date}"
            
            # Verificar categoria de serviço
            assert pre_order.service_category == original_service_category, \
                f"Categoria não preservada: esperado '{original_service_category}', obtido '{pre_order.service_category}'"
            
            # Verificar client_id
            assert pre_order.client_id == original_client_id, \
                f"Client ID não preservado: esperado {original_client_id}, obtido {pre_order.client_id}"
            
            # Verificar provider_id
            assert pre_order.provider_id == provider.id, \
                f"Provider ID incorreto: esperado {provider.id}, obtido {pre_order.provider_id}"
            
            # Verificar que o convite foi atualizado
            session.refresh(invite)
            assert invite.status == 'convertido_pre_ordem', \
                f"Status do convite não atualizado: esperado 'convertido_pre_ordem', obtido '{invite.status}'"
            
            # Verificar que um registro de histórico foi criado
            history_entries = PreOrderHistory.query.filter_by(pre_order_id=pre_order.id).all()
            assert len(history_entries) > 0, "Nenhum registro de histórico foi criado"
            
            # Verificar que o histórico contém informações da migração
            migration_history = [h for h in history_entries if h.event_type == 'created']
            assert len(migration_history) > 0, "Registro de criação não encontrado no histórico"
            
            # Verificar dados do evento no histórico
            history_event = migration_history[0]
            assert history_event.event_data is not None, "Dados do evento não registrados"
            assert history_event.event_data.get('migration') == True, \
                "Evento não marcado como migração"
            assert history_event.event_data.get('invite_id') == original_invite_id, \
                "ID do convite não registrado no histórico"
            
            # Verificar estado inicial da pré-ordem
            assert pre_order.status == PreOrderStatus.EM_NEGOCIACAO.value, \
                f"Status inicial incorreto: esperado '{PreOrderStatus.EM_NEGOCIACAO.value}', obtido '{pre_order.status}'"
            
            assert pre_order.client_accepted_terms == False, \
                "Cliente não deveria ter aceitado termos inicialmente"
            
            assert pre_order.provider_accepted_terms == False, \
                "Prestador não deveria ter aceitado termos inicialmente"
            
            assert pre_order.has_active_proposal == False, \
                "Não deveria ter proposta ativa inicialmente"
            
            # Verificar que expires_at foi definido (7 dias no futuro)
            assert pre_order.expires_at is not None, "Data de expiração não definida"
            time_until_expiration = pre_order.expires_at - datetime.utcnow()
            assert 6 <= time_until_expiration.days <= 8, \
                f"Prazo de expiração incorreto: {time_until_expiration.days} dias (esperado ~7 dias)"
            
            # PROPERTY VALIDADA: Todos os dados foram preservados corretamente
            
        finally:
            # Limpar dados do teste
            session.rollback()


# ==============================================================================
# TESTE ADICIONAL: Migração não cria duplicatas
# ==============================================================================

@given(
    client_data=valid_user_data(),
    provider_data=valid_user_data(),
    data=st.data()
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_migration_does_not_create_duplicates(
    test_app, client_data, provider_data, data
):
    """
    Teste adicional: Migração não cria pré-ordens duplicadas
    
    Se um convite já foi migrado, tentar migrar novamente não deve criar
    uma segunda pré-ordem.
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
            invite_data = data.draw(valid_invite_data(
                client_id=client.id,
                provider_phone=provider.phone
            ))
            
            invite = Invite(**invite_data)
            invite.token = Invite.generate_token()
            invite.expires_at = invite.delivery_date
            session.add(invite)
            session.commit()
            
            # Executar primeira migração
            migration_service = InviteMigrationService(dry_run=False)
            result1 = migration_service.migrate_invite_to_pre_order(invite)
            assert result1['success'], "Primeira migração falhou"
            
            pre_order_id_1 = result1['pre_order_id']
            
            # Tentar migrar novamente
            result2 = migration_service.migrate_invite_to_pre_order(invite)
            
            # A segunda tentativa deve falhar ou retornar a mesma pré-ordem
            if result2['success']:
                # Se retornou sucesso, deve ser a mesma pré-ordem
                assert result2['pre_order_id'] == pre_order_id_1, \
                    "Segunda migração criou pré-ordem diferente"
            else:
                # Se falhou, deve ter mensagem apropriada
                assert 'já possui pré-ordem' in result2.get('error', '').lower(), \
                    "Erro não indica que pré-ordem já existe"
            
            # Verificar que existe apenas uma pré-ordem para este convite
            pre_orders = PreOrder.query.filter_by(invite_id=invite.id).all()
            assert len(pre_orders) == 1, \
                f"Múltiplas pré-ordens criadas: {len(pre_orders)}"
            
        finally:
            session.rollback()


# ==============================================================================
# TESTE ADICIONAL: Migração em lote
# ==============================================================================

@given(
    num_invites=st.integers(min_value=1, max_value=10)
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_batch_migration_preserves_all_data(test_app, num_invites):
    """
    Teste adicional: Migração em lote preserva dados de todos os convites
    
    Quando múltiplos convites são migrados, todos devem ter seus dados
    preservados corretamente.
    """
    session = get_clean_db_session(test_app)
    
    with test_app.app_context():
        try:
            # Criar usuários base
            client = User(
                email='client@example.com',
                nome='Cliente Teste',
                cpf='12345678901',
                phone='11987654321',
                roles='cliente'
            )
            client.set_password('senha123')
            session.add(client)
            session.flush()
            
            client_wallet = Wallet(user_id=client.id, balance=Decimal('10000.00'))
            session.add(client_wallet)
            
            # Criar múltiplos convites
            invites_data = []
            for i in range(num_invites):
                provider = User(
                    email=f'provider{i}@example.com',
                    nome=f'Prestador {i}',
                    cpf=f'{i+10000000000:011d}',
                    phone=f'119{i+10000000:08d}',
                    roles='prestador'
                )
                provider.set_password('senha123')
                session.add(provider)
                session.flush()
                
                provider_wallet = Wallet(user_id=provider.id, balance=Decimal('500.00'))
                session.add(provider_wallet)
                
                invite = Invite(
                    client_id=client.id,
                    invited_phone=provider.phone,
                    service_title=f'Servico {i}',
                    service_description=f'Descricao do servico {i}',
                    service_category='pedreiro',
                    original_value=Decimal('100.00') + Decimal(i),
                    delivery_date=datetime.utcnow() + timedelta(days=7),
                    status='aceito',
                    order_id=None
                )
                invite.token = Invite.generate_token()
                invite.expires_at = invite.delivery_date
                session.add(invite)
                session.flush()
                
                invites_data.append({
                    'invite': invite,
                    'provider': provider,
                    'original_title': invite.service_title,
                    'original_value': invite.current_value
                })
            
            session.commit()
            
            # Executar migração em lote
            migration_service = InviteMigrationService(dry_run=False)
            stats = migration_service.migrate_all()
            
            # Verificar estatísticas
            assert stats['total_found'] == num_invites, \
                f"Número incorreto de convites encontrados: {stats['total_found']} != {num_invites}"
            
            assert stats['total_migrated'] == num_invites, \
                f"Número incorreto de convites migrados: {stats['total_migrated']} != {num_invites}"
            
            assert stats['total_errors'] == 0, \
                f"Erros durante migração: {stats['errors']}"
            
            # Verificar que todas as pré-ordens foram criadas corretamente
            for data in invites_data:
                invite = data['invite']
                session.refresh(invite)
                
                # Verificar status do convite
                assert invite.status == 'convertido_pre_ordem', \
                    f"Convite {invite.id} não foi marcado como convertido"
                
                # Buscar pré-ordem
                pre_order = PreOrder.query.filter_by(invite_id=invite.id).first()
                assert pre_order is not None, \
                    f"Pré-ordem não criada para convite {invite.id}"
                
                # Verificar preservação de dados
                assert pre_order.title == data['original_title'], \
                    f"Título não preservado para convite {invite.id}"
                
                assert pre_order.current_value == data['original_value'], \
                    f"Valor não preservado para convite {invite.id}"
                
                assert pre_order.provider_id == data['provider'].id, \
                    f"Provider ID incorreto para convite {invite.id}"
            
        finally:
            session.rollback()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
