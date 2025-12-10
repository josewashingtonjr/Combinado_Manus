#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Integração - Fluxo de Aceitação Mútua de Convites
Valida o fluxo completo de aceitação de convites e criação automática de ordens
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from models import db, User, Order, Invite, Wallet, Transaction
from services.invite_service import InviteService
from services.invite_acceptance_coordinator import InviteAcceptanceCoordinator
from services.wallet_service import WalletService
from services.dashboard_data_service import DashboardDataService
from services.cliente_service import ClienteService
from services.prestador_service import PrestadorService


class TestCompleteMutualAcceptanceFlow:
    """Testes do fluxo completo de aceitação mútua"""
    
    def test_full_mutual_acceptance_flow(self, app, db_session):
        """
        Testa o fluxo completo de aceitação mútua
        
        Fluxo:
        1. Cliente cria convite
        2. Prestador aceita
        3. Cliente aceita
        4. Verificar ordem criada
        5. Verificar valores bloqueados
        6. Verificar dashboards atualizadas
        
        Requirements: Todos
        """
        with app.app_context():
            # Passo 1: Cliente cria convite
            cliente = User(
                email='cliente_mutual@test.com',
                nome='Cliente Mutual',
                cpf='11111111111',
                phone='11999990001',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_mutual@test.com',
                nome='Prestador Mutual',
                cpf='22222222222',
                phone='11999990002',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo suficiente
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            
            # Criar convite
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Instalação de Ar Condicionado',
                service_description='Instalação completa com suporte',
                service_category='instalador',
                original_value=Decimal('300.00'),
                current_value=Decimal('300.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Verificar estado inicial
            assert invite.status == 'pendente'
            assert invite.client_accepted is False
            assert invite.provider_accepted is False
            assert invite.is_mutually_accepted is False
            
            # Passo 2: Prestador aceita
            result_provider = InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            assert result_provider['success'] is True
            assert result_provider['order_created'] is False
            assert result_provider['message'] == 'Convite aceito! Aguardando aceitação do cliente.'
            
            db_session.refresh(invite)
            assert invite.provider_accepted is True
            assert invite.provider_accepted_at is not None
            assert invite.client_accepted is False
            assert invite.is_mutually_accepted is False
            
            # Passo 3: Cliente aceita
            result_client = InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            assert result_client['success'] is True
            assert result_client['order_created'] is True
            assert 'order_id' in result_client
            
            # Passo 4: Verificar ordem criada
            db_session.refresh(invite)
            assert invite.client_accepted is True
            assert invite.client_accepted_at is not None
            assert invite.is_mutually_accepted is True
            assert invite.status == 'convertido'
            assert invite.order_id is not None
            
            order = Order.query.get(result_client['order_id'])
            assert order is not None
            assert order.client_id == cliente.id
            assert order.provider_id == prestador.id
            assert order.title == 'Instalação de Ar Condicionado'
            assert order.value == Decimal('300.00')
            assert order.status == 'aguardando_execucao'
            assert order.invite_id == invite.id
            
            # Passo 5: Verificar valores bloqueados
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            contestation_fee = order.contestation_fee_at_creation
            
            # Cliente deve ter bloqueado: valor do serviço + taxa de contestação
            expected_client_escrow = Decimal('300.00') + contestation_fee
            assert client_wallet.escrow_balance == expected_client_escrow
            
            # Prestador deve ter bloqueado: taxa de contestação
            assert provider_wallet.escrow_balance == contestation_fee
            
            # Verificar saldos disponíveis
            assert client_wallet.balance == Decimal('500.00') - expected_client_escrow
            assert provider_wallet.balance == Decimal('50.00') - contestation_fee
            
            # Passo 6: Verificar dashboards atualizadas
            # Dashboard do cliente
            client_dashboard = ClienteService.get_dashboard_data(cliente.id)
            assert client_dashboard is not None
            assert 'open_orders' in client_dashboard
            assert len(client_dashboard['open_orders']) == 1
            assert client_dashboard['open_orders'][0]['id'] == order.id
            assert client_dashboard['blocked_funds']['total'] == float(expected_client_escrow)
            
            # Dashboard do prestador
            provider_dashboard = PrestadorService.get_dashboard_data(prestador.id)
            assert provider_dashboard is not None
            assert 'open_orders' in provider_dashboard
            assert len(provider_dashboard['open_orders']) == 1
            assert provider_dashboard['open_orders'][0]['id'] == order.id
            assert provider_dashboard['blocked_funds']['total'] == float(contestation_fee)
    
    def test_mutual_acceptance_reverse_order(self, app, db_session):
        """
        Testa aceitação mútua quando cliente aceita primeiro
        
        Fluxo:
        1. Cliente cria e aceita convite imediatamente
        2. Prestador aceita depois
        3. Ordem é criada automaticamente
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_reverse@test.com',
                nome='Cliente Reverse',
                cpf='33333333333',
                phone='11999990003',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_reverse@test.com',
                nome='Prestador Reverse',
                cpf='44444444444',
                phone='11999990004',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('400.00'), 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('30.00'), 'Crédito', 'credito')
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Manutenção Elétrica',
                service_description='Reparo de instalação elétrica',
                service_category='eletricista',
                original_value=Decimal('250.00'),
                current_value=Decimal('250.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Cliente aceita primeiro
            result_client = InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            assert result_client['success'] is True
            assert result_client['order_created'] is False
            
            db_session.refresh(invite)
            assert invite.client_accepted is True
            assert invite.provider_accepted is False
            
            # Prestador aceita depois - ordem deve ser criada
            result_provider = InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            assert result_provider['success'] is True
            assert result_provider['order_created'] is True
            assert 'order_id' in result_provider
            
            db_session.refresh(invite)
            assert invite.is_mutually_accepted is True
            assert invite.status == 'convertido'
            
            order = Order.query.get(result_provider['order_id'])
            assert order is not None
            assert order.value == Decimal('250.00')


class TestInsufficientBalanceFlow:
    """Testes do fluxo com saldo insuficiente"""
    
    def test_client_insufficient_balance_flow(self, app, db_session):
        """
        Testa fluxo quando cliente tem saldo insuficiente
        
        Fluxo:
        1. Cliente com saldo baixo tenta aceitar
        2. Verificar erro apropriado
        3. Adicionar saldo
        4. Aceitar com sucesso
        
        Requirements: 2.3, 2.4, 8.1-8.4
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_lowbal@test.com',
                nome='Cliente LowBal',
                cpf='55555555555',
                phone='11999990005',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_lowbal@test.com',
                nome='Prestador LowBal',
                cpf='66666666666',
                phone='11999990006',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            # Cliente com saldo insuficiente
            WalletService.credit_wallet(cliente.id, Decimal('50.00'), 'Crédito baixo', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('30.00'), 'Crédito', 'credito')
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Caro',
                service_description='Serviço que requer saldo alto',
                service_category='instalador',
                original_value=Decimal('200.00'),
                current_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Prestador aceita primeiro
            result_provider = InviteService.accept_invite_as_provider(invite.id, prestador.id)
            assert result_provider['success'] is True
            
            # Passo 1 e 2: Cliente tenta aceitar com saldo insuficiente
            with pytest.raises(ValueError) as exc_info:
                InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            assert 'Saldo insuficiente' in str(exc_info.value)
            
            # Verificar que convite não foi aceito pelo cliente
            db_session.refresh(invite)
            assert invite.client_accepted is False
            assert invite.provider_accepted is True
            assert invite.status == 'pendente'
            
            # Passo 3: Adicionar saldo
            WalletService.credit_wallet(cliente.id, Decimal('200.00'), 'Recarga', 'credito')
            
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            assert client_wallet.balance == Decimal('250.00')
            
            # Passo 4: Aceitar com sucesso
            result_client = InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            assert result_client['success'] is True
            assert result_client['order_created'] is True
            
            db_session.refresh(invite)
            assert invite.client_accepted is True
            assert invite.is_mutually_accepted is True
            assert invite.status == 'convertido'
            
            order = Order.query.get(result_client['order_id'])
            assert order is not None
    
    def test_provider_insufficient_balance_flow(self, app, db_session):
        """
        Testa fluxo quando prestador tem saldo insuficiente para taxa
        
        Fluxo:
        1. Prestador com saldo baixo tenta aceitar
        2. Verificar erro apropriado
        3. Adicionar saldo
        4. Aceitar com sucesso
        
        Requirements: 2.3, 2.4, 8.1-8.4
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_plowbal@test.com',
                nome='Cliente PLowBal',
                cpf='77777777777',
                phone='11999990007',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_plowbal@test.com',
                nome='Prestador PLowBal',
                cpf='88888888888',
                phone='11999990008',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            WalletService.credit_wallet(cliente.id, Decimal('300.00'), 'Crédito', 'credito')
            # Prestador com saldo insuficiente para taxa
            WalletService.credit_wallet(prestador.id, Decimal('2.00'), 'Crédito baixo', 'credito')
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Normal',
                service_description='Serviço padrão',
                service_category='instalador',
                original_value=Decimal('150.00'),
                current_value=Decimal('150.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Cliente aceita primeiro
            result_client = InviteService.accept_invite_as_client(invite.id, cliente.id)
            assert result_client['success'] is True
            
            # Passo 1 e 2: Prestador tenta aceitar com saldo insuficiente
            with pytest.raises(ValueError) as exc_info:
                InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            assert 'Saldo insuficiente' in str(exc_info.value)
            
            # Verificar que convite não foi aceito pelo prestador
            db_session.refresh(invite)
            assert invite.provider_accepted is False
            assert invite.client_accepted is True
            
            # Passo 3: Adicionar saldo
            WalletService.credit_wallet(prestador.id, Decimal('20.00'), 'Recarga', 'credito')
            
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            assert provider_wallet.balance >= Decimal('20.00')
            
            # Passo 4: Aceitar com sucesso
            result_provider = InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            assert result_provider['success'] is True
            assert result_provider['order_created'] is True
            
            db_session.refresh(invite)
            assert invite.provider_accepted is True
            assert invite.is_mutually_accepted is True


class TestRollbackFlow:
    """Testes do fluxo de rollback em caso de erro"""
    
    def test_rollback_on_escrow_failure(self, app, db_session):
        """
        Testa rollback quando bloqueio de escrow falha
        
        Fluxo:
        1. Simular falha no bloqueio de escrow
        2. Verificar rollback da ordem
        3. Verificar convite ainda aceito
        4. Verificar possibilidade de retry
        
        Requirements: 7.1, 7.2, 7.5
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_rollback@test.com',
                nome='Cliente Rollback',
                cpf='99999999999',
                phone='11999990009',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_rollback@test.com',
                nome='Prestador Rollback',
                cpf='10101010101',
                phone='11999990010',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('400.00'), 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('30.00'), 'Crédito', 'credito')
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço com Falha',
                service_description='Teste de rollback',
                service_category='instalador',
                original_value=Decimal('180.00'),
                current_value=Decimal('180.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Ambos aceitam
            InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            # Passo 1: Simular falha no bloqueio de escrow
            with patch('services.wallet_service.WalletService.transfer_to_escrow') as mock_escrow:
                mock_escrow.side_effect = Exception('Falha simulada no escrow')
                
                # Passo 2: Tentar aceitar pelo cliente (deve falhar)
                with pytest.raises(Exception) as exc_info:
                    InviteService.accept_invite_as_client(invite.id, cliente.id)
                
                assert 'Falha simulada no escrow' in str(exc_info.value) or 'erro' in str(exc_info.value).lower()
            
            # Passo 3: Verificar que ordem não foi criada
            db_session.refresh(invite)
            
            # O convite deve estar marcado como aceito por ambos
            assert invite.client_accepted is True
            assert invite.provider_accepted is True
            
            # Mas não deve ter sido convertido
            assert invite.status != 'convertido'
            assert invite.order_id is None
            
            # Verificar que nenhuma ordem foi criada
            orders = Order.query.filter_by(invite_id=invite.id).all()
            assert len(orders) == 0
            
            # Verificar que saldos não foram alterados
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert client_wallet.balance == Decimal('400.00')
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.balance == Decimal('30.00')
            assert provider_wallet.escrow_balance == Decimal('0.00')
            
            # Passo 4: Verificar possibilidade de retry
            # Remover o mock e tentar novamente
            result_retry = InviteAcceptanceCoordinator.process_acceptance(
                invite.id, cliente.id, 'client'
            )
            
            assert result_retry['success'] is True
            assert result_retry['order_created'] is True
            
            db_session.refresh(invite)
            assert invite.status == 'convertido'
            assert invite.order_id is not None
            
            # Verificar que ordem foi criada no retry
            order = Order.query.get(invite.order_id)
            assert order is not None
            assert order.value == Decimal('180.00')
    
    def test_rollback_on_order_creation_failure(self, app, db_session):
        """
        Testa rollback quando criação da ordem falha
        
        Fluxo:
        1. Simular falha na criação da ordem
        2. Verificar que convite permanece aceito
        3. Verificar que nenhum valor foi bloqueado
        4. Verificar possibilidade de retry
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_orderfail@test.com',
                nome='Cliente OrderFail',
                cpf='11111111112',
                phone='11999990011',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_orderfail@test.com',
                nome='Prestador OrderFail',
                cpf='22222222223',
                phone='11999990012',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('350.00'), 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('25.00'), 'Crédito', 'credito')
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço com Falha na Ordem',
                service_description='Teste de rollback de ordem',
                service_category='instalador',
                original_value=Decimal('220.00'),
                current_value=Decimal('220.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            # Ambos aceitam
            InviteService.accept_invite_as_provider(invite.id, prestador.id)
            
            # Passo 1: Simular falha na criação da ordem
            with patch('services.order_service.OrderService.create_order_from_invite') as mock_create:
                mock_create.side_effect = Exception('Falha simulada na criação da ordem')
                
                # Tentar aceitar pelo cliente (deve falhar)
                with pytest.raises(Exception):
                    InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            # Passo 2: Verificar que convite permanece aceito
            db_session.refresh(invite)
            assert invite.client_accepted is True
            assert invite.provider_accepted is True
            
            # Passo 3: Verificar que nenhum valor foi bloqueado
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.escrow_balance == Decimal('0.00')
            
            # Passo 4: Verificar possibilidade de retry
            result_retry = InviteAcceptanceCoordinator.process_acceptance(
                invite.id, cliente.id, 'client'
            )
            
            assert result_retry['success'] is True
            assert result_retry['order_created'] is True


class TestDashboardIntegration:
    """Testes de integração com dashboards"""
    
    def test_dashboard_updates_after_order_creation(self, app, db_session):
        """
        Testa que dashboards são atualizadas após criação de ordem
        
        Verifica:
        - Ordens em aberto aparecem
        - Fundos bloqueados são exibidos corretamente
        - Métricas são calculadas corretamente
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_dash@test.com',
                nome='Cliente Dash',
                cpf='33333333334',
                phone='11999990013',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_dash@test.com',
                nome='Prestador Dash',
                cpf='44444444445',
                phone='11999990014',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('600.00'), 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('40.00'), 'Crédito', 'credito')
            
            # Criar múltiplos convites e ordens
            for i in range(3):
                invite = Invite(
                    client_id=cliente.id,
                    invited_phone=prestador.phone,
                    service_title=f'Serviço {i+1}',
                    service_description=f'Descrição {i+1}',
                    service_category='instalador',
                    original_value=Decimal('100.00'),
                    current_value=Decimal('100.00'),
                    delivery_date=datetime.utcnow() + timedelta(days=7+i),
                    status='pendente',
                    client_accepted=False,
                    provider_accepted=False
                )
                db_session.add(invite)
                db_session.commit()
                
                # Aceitação mútua
                InviteService.accept_invite_as_provider(invite.id, prestador.id)
                InviteService.accept_invite_as_client(invite.id, cliente.id)
            
            # Verificar dashboard do cliente
            client_dashboard = ClienteService.get_dashboard_data(cliente.id)
            
            assert client_dashboard is not None
            assert 'open_orders' in client_dashboard
            assert len(client_dashboard['open_orders']) == 3
            
            # Verificar fundos bloqueados
            assert 'blocked_funds' in client_dashboard
            assert client_dashboard['blocked_funds']['total'] > 0
            assert len(client_dashboard['blocked_funds']['by_order']) == 3
            
            # Verificar dashboard do prestador
            provider_dashboard = PrestadorService.get_dashboard_data(prestador.id)
            
            assert provider_dashboard is not None
            assert 'open_orders' in provider_dashboard
            assert len(provider_dashboard['open_orders']) == 3
            
            # Verificar fundos bloqueados
            assert 'blocked_funds' in provider_dashboard
            assert provider_dashboard['blocked_funds']['total'] > 0
