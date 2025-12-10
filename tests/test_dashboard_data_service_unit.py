#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes Unitários para DashboardDataService

Testa:
- get_open_orders para cliente
- get_open_orders para prestador
- get_blocked_funds_summary
- get_dashboard_metrics

Requirements: 3.1-3.5, 4.1-4.5, 5.1-5.5
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from models import db, User, Order, Wallet, Transaction
from services.dashboard_data_service import DashboardDataService


class TestGetOpenOrdersCliente:
    """Testes para get_open_orders (cliente)"""
    
    def test_retorna_ordens_em_aberto_cliente(self, app, db_session, test_user, test_provider):
        """Testa que retorna ordens em aberto do cliente"""
        with app.app_context():
            # Criar ordem em aberto
            order = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Serviço Teste',
                description='Descrição',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add(order)
            db_session.commit()
            
            orders = DashboardDataService.get_open_orders(test_user.id, 'cliente')
            
            assert len(orders) > 0
            assert orders[0]['id'] == order.id
            assert orders[0]['title'] == 'Serviço Teste'
            assert orders[0]['value'] == Decimal('100.00')
    
    def test_filtra_apenas_status_abertos(self, app, db_session, test_user, test_provider):
        """Testa que filtra apenas ordens com status em aberto"""
        with app.app_context():
            # Criar ordens com diferentes status
            order_aceita = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Aceita',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            order_concluida = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Concluída',
                description='Desc',
                value=Decimal('200.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add_all([order_aceita, order_concluida])
            db_session.commit()
            
            orders = DashboardDataService.get_open_orders(test_user.id, 'cliente')
            
            # Deve retornar apenas a ordem aceita
            order_ids = [o['id'] for o in orders]
            assert order_aceita.id in order_ids
            assert order_concluida.id not in order_ids
    
    def test_ordena_por_data_criacao(self, app, db_session, test_user, test_provider):
        """Testa que ordena por data de criação (mais recentes primeiro)"""
        with app.app_context():
            # Criar ordens em momentos diferentes
            order1 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Antiga',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            order2 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Recente',
                description='Desc',
                value=Decimal('200.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add_all([order1, order2])
            db_session.commit()
            
            orders = DashboardDataService.get_open_orders(test_user.id, 'cliente')
            
            # Primeira ordem deve ser a mais recente
            assert orders[0]['id'] == order2.id
    
    def test_retorna_lista_vazia_sem_ordens(self, app, db_session, test_user):
        """Testa que retorna lista vazia quando não há ordens"""
        with app.app_context():
            orders = DashboardDataService.get_open_orders(test_user.id, 'cliente')
            
            assert orders == []


class TestGetOpenOrdersPrestador:
    """Testes para get_open_orders (prestador)"""
    
    def test_retorna_ordens_em_aberto_prestador(self, app, db_session, test_user, test_provider):
        """Testa que retorna ordens em aberto do prestador"""
        with app.app_context():
            order = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Serviço Teste',
                description='Descrição',
                value=Decimal('100.00'),
                status='em_andamento',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add(order)
            db_session.commit()
            
            orders = DashboardDataService.get_open_orders(test_provider.id, 'prestador')
            
            assert len(orders) > 0
            assert orders[0]['id'] == order.id
    
    def test_ordena_por_data_entrega(self, app, db_session, test_user, test_provider):
        """Testa que ordena por data de entrega (mais urgentes primeiro)"""
        with app.app_context():
            # Ordem urgente (entrega em 1 dia)
            order_urgente = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Urgente',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=1),
                created_at=datetime.utcnow()
            )
            # Ordem normal (entrega em 7 dias)
            order_normal = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Normal',
                description='Desc',
                value=Decimal('200.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add_all([order_normal, order_urgente])
            db_session.commit()
            
            orders = DashboardDataService.get_open_orders(test_provider.id, 'prestador')
            
            # Primeira ordem deve ser a mais urgente
            assert orders[0]['id'] == order_urgente.id


class TestGetBlockedFundsSummary:
    """Testes para get_blocked_funds_summary"""
    
    def test_calcula_total_bloqueado(self, app, db_session, test_user, test_provider):
        """Testa cálculo do total de fundos bloqueados"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            
            # Criar ordem e bloquear fundos
            order = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Serviço',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add(order)
            db_session.commit()
            
            # Simular bloqueio no escrow
            wallet.escrow_balance = Decimal('100.00')
            db_session.commit()
            
            summary = DashboardDataService.get_blocked_funds_summary(test_user.id)
            
            assert summary['total_blocked'] == Decimal('100.00')
    
    def test_detalha_valores_por_ordem(self, app, db_session, test_user, test_provider):
        """Testa detalhamento de valores bloqueados por ordem"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            
            # Criar duas ordens
            order1 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Serviço 1',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            order2 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Serviço 2',
                description='Desc',
                value=Decimal('200.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add_all([order1, order2])
            db_session.commit()
            
            # Criar transações de escrow
            trans1 = Transaction(
                wallet_id=wallet.id,
                amount=Decimal('100.00'),
                transaction_type='escrow_block',
                description=f'Bloqueio para ordem #{order1.id}',
                order_id=order1.id
            )
            trans2 = Transaction(
                wallet_id=wallet.id,
                amount=Decimal('200.00'),
                transaction_type='escrow_block',
                description=f'Bloqueio para ordem #{order2.id}',
                order_id=order2.id
            )
            db_session.add_all([trans1, trans2])
            wallet.escrow_balance = Decimal('300.00')
            db_session.commit()
            
            summary = DashboardDataService.get_blocked_funds_summary(test_user.id)
            
            assert len(summary['by_order']) == 2
            assert summary['total_blocked'] == Decimal('300.00')


class TestGetDashboardMetrics:
    """Testes para get_dashboard_metrics"""
    
    def test_agrega_saldo_disponivel_e_bloqueado(self, app, db_session, test_user):
        """Testa agregação de saldo disponível e bloqueado"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('500.00')
            wallet.escrow_balance = Decimal('100.00')
            db_session.commit()
            
            metrics = DashboardDataService.get_dashboard_metrics(test_user.id, 'cliente')
            
            assert metrics['balance']['available'] == Decimal('500.00')
            assert metrics['balance']['blocked'] == Decimal('100.00')
            assert metrics['balance']['total'] == Decimal('600.00')
    
    def test_conta_ordens_por_status(self, app, db_session, test_user, test_provider):
        """Testa contagem de ordens por status"""
        with app.app_context():
            # Criar ordens com diferentes status
            order1 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem 1',
                description='Desc',
                value=Decimal('100.00'),
                status='aceita',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            order2 = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem 2',
                description='Desc',
                value=Decimal('200.00'),
                status='em_andamento',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db_session.add_all([order1, order2])
            db_session.commit()
            
            metrics = DashboardDataService.get_dashboard_metrics(test_user.id, 'cliente')
            
            assert metrics['open_orders_count'] == 2
            assert 'aceita' in metrics['orders_by_status']
            assert 'em_andamento' in metrics['orders_by_status']
    
    def test_calcula_estatisticas_mes(self, app, db_session, test_user, test_provider):
        """Testa cálculo de estatísticas do mês"""
        with app.app_context():
            # Criar ordem do mês atual
            order = Order(
                client_id=test_user.id,
                provider_id=test_provider.id,
                title='Ordem Mês',
                description='Desc',
                value=Decimal('100.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db_session.add(order)
            db_session.commit()
            
            metrics = DashboardDataService.get_dashboard_metrics(test_user.id, 'cliente')
            
            assert 'month_stats' in metrics
            assert metrics['month_stats']['orders_completed'] >= 1
    
    def test_gera_alertas_saldo_baixo(self, app, db_session, test_user):
        """Testa geração de alertas de saldo baixo"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('5.00')  # Saldo muito baixo
            db_session.commit()
            
            metrics = DashboardDataService.get_dashboard_metrics(test_user.id, 'cliente')
            
            assert 'alerts' in metrics
            # Deve ter alerta de saldo baixo
            alert_types = [alert['type'] for alert in metrics['alerts']]
            assert 'warning' in alert_types or 'danger' in alert_types
