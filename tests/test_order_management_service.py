#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes Unitários para OrderManagementService
Valida todas as operações principais do serviço de gestão de ordens
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models import db, User, Order, Invite, Wallet, Transaction
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from services.config_service import ConfigService


class TestCreateOrderFromInvite:
    """Testes para create_order_from_invite()"""
    
    def test_create_order_success(self, app, db_session):
        """Testa criação bem-sucedida de ordem a partir de convite"""
        with app.app_context():
            # Criar cliente e prestador
            cliente = User(email='cliente@test.com', nome='Cliente', cpf='11111111111', 
                          phone='11999999001', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador@test.com', nome='Prestador', cpf='22222222222',
                           phone='11999999002', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('200.00'), 'Crédito teste', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito teste', 'credito')
            
            # Criar convite aceito
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Instalação Elétrica',
                service_description='Instalação de tomadas',
                service_category='eletricista',
                original_value=Decimal('150.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            # Executar criação de ordem
            result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
            
            # Validações
            assert result['success'] is True
            assert result['order_id'] is not None
            assert result['effective_value'] == 150.00
            
            # Verificar ordem criada
            order = result['order']
            assert order.client_id == cliente.id
            assert order.provider_id == prestador.id
            assert order.status == 'aguardando_execucao'
            assert order.value == Decimal('150.00')
            assert order.invite_id == invite.id
            
            # Verificar taxas armazenadas
            assert order.platform_fee_percentage_at_creation is not None
            assert order.contestation_fee_at_creation is not None
            assert order.cancellation_fee_percentage_at_creation is not None
            
            # Verificar convite atualizado
            db_session.refresh(invite)
            assert invite.status == 'convertido'
            assert invite.order_id == order.id
            
            # Verificar escrow
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            assert client_wallet.escrow_balance > 0
            assert provider_wallet.escrow_balance > 0
    
    def test_create_order_invite_not_found(self, app, db_session):
        """Testa erro quando convite não existe"""
        with app.app_context():
            with pytest.raises(ValueError, match="Convite não encontrado"):
                OrderManagementService.create_order_from_invite(99999, 1)
    
    def test_create_order_invite_already_converted(self, app, db_session):
        """Testa erro quando convite já foi convertido"""
        with app.app_context():
            cliente = User(email='cliente2@test.com', nome='Cliente', cpf='33333333333',
                          phone='11999999003', roles='cliente')
            cliente.set_password('senha123')
            db_session.add(cliente)
            db_session.commit()
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone='11999999004',
                service_title='Serviço',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='convertido'
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="já foi convertido"):
                OrderManagementService.create_order_from_invite(invite.id, 1)
    
    def test_create_order_insufficient_balance(self, app, db_session):
        """Testa erro quando cliente não tem saldo suficiente"""
        with app.app_context():
            cliente = User(email='cliente3@test.com', nome='Cliente', cpf='44444444444',
                          phone='11999999005', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador3@test.com', nome='Prestador', cpf='55555555555',
                           phone='11999999006', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras sem saldo suficiente
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Caro',
                service_description='Descrição',
                original_value=Decimal('1000.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="saldo suficiente"):
                OrderManagementService.create_order_from_invite(invite.id, prestador.id)


class TestMarkServiceCompleted:
    """Testes para mark_service_completed()"""
    
    def test_mark_completed_success(self, app, db_session):
        """Testa marcação bem-sucedida de serviço como concluído"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente4@test.com', nome='Cliente', cpf='66666666666',
                          phone='11999999007', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador4@test.com', nome='Prestador', cpf='77777777777',
                           phone='11999999008', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar ordem
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Teste',
                description='Descrição',
                value=Decimal('200.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            # Marcar como concluído
            result = OrderManagementService.mark_service_completed(order.id, prestador.id)
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'servico_executado'
            assert result['hours_to_confirm'] == 36
            assert result['confirmation_deadline'] is not None
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'servico_executado'
            assert order.completed_at is not None
            assert order.confirmation_deadline is not None
            assert order.dispute_deadline is not None
            
            # Verificar prazo de 36 horas
            diff = order.confirmation_deadline - order.completed_at
            hours = diff.total_seconds() / 3600
            assert abs(hours - 36) < 0.1
    
    def test_mark_completed_wrong_provider(self, app, db_session):
        """Testa erro quando usuário não é o prestador"""
        with app.app_context():
            cliente = User(email='cliente5@test.com', nome='Cliente', cpf='88888888888',
                          phone='11999999009', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador5@test.com', nome='Prestador', cpf='99999999999',
                           phone='11999999010', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não é o prestador"):
                OrderManagementService.mark_service_completed(order.id, cliente.id)
    
    def test_mark_completed_invalid_status(self, app, db_session):
        """Testa erro quando ordem não está em status válido"""
        with app.app_context():
            cliente = User(email='cliente6@test.com', nome='Cliente', cpf='10101010101',
                          phone='11999999011', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador6@test.com', nome='Prestador', cpf='20202020202',
                           phone='11999999012', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não pode ser marcada como concluída"):
                OrderManagementService.mark_service_completed(order.id, prestador.id)


class TestConfirmService:
    """Testes para confirm_service()"""
    
    def test_confirm_service_success(self, app, db_session):
        """Testa confirmação manual bem-sucedida pelo cliente"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente7@test.com', nome='Cliente', cpf='30303030303',
                          phone='11999999013', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador7@test.com', nome='Prestador', cpf='40404040404',
                           phone='11999999014', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo em escrow
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            # Adicionar saldo e transferir para escrow
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Teste', 'credito')
            
            # Criar ordem em status servico_executado
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=service_value,
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Confirmar serviço
            result = OrderManagementService.confirm_service(order.id, cliente.id)
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'concluida'
            assert result['confirmation_type'] == 'manual'
            assert result['payments'] is not None
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'concluida'
            assert order.confirmed_at is not None
            assert order.platform_fee is not None
    
    def test_confirm_service_wrong_client(self, app, db_session):
        """Testa erro quando usuário não é o cliente"""
        with app.app_context():
            cliente = User(email='cliente8@test.com', nome='Cliente', cpf='50505050505',
                          phone='11999999015', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador8@test.com', nome='Prestador', cpf='60606060606',
                           phone='11999999016', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não é o cliente"):
                OrderManagementService.confirm_service(order.id, prestador.id)
    
    def test_confirm_service_expired_deadline(self, app, db_session):
        """Testa erro quando prazo de confirmação expirou"""
        with app.app_context():
            cliente = User(email='cliente9@test.com', nome='Cliente', cpf='70707070707',
                          phone='11999999017', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador9@test.com', nome='Prestador', cpf='80808080808',
                           phone='11999999018', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(hours=48),
                confirmation_deadline=datetime.utcnow() - timedelta(hours=12)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Prazo para confirmação expirado"):
                OrderManagementService.confirm_service(order.id, cliente.id)


class TestAutoConfirmExpiredOrders:
    """Testes para auto_confirm_expired_orders()"""
    
    def test_auto_confirm_success(self, app, db_session):
        """Testa confirmação automática de ordens expiradas"""
        with app.app_context():
            # Limpar ordens antigas primeiro
            Order.query.delete()
            db_session.commit()
            
            # Criar usuários
            cliente = User(email='cliente10@test.com', nome='Cliente', cpf='90909090909',
                          phone='11999999019', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador10@test.com', nome='Prestador', cpf='01010101010',
                           phone='11999999020', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo em escrow
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('150.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Teste', 'credito')
            
            # Criar ordem expirada
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Expirado',
                description='Descrição',
                value=service_value,
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(hours=48),
                confirmation_deadline=datetime.utcnow() - timedelta(hours=12),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Executar confirmação automática
            result = OrderManagementService.auto_confirm_expired_orders()
            
            # Validações - deve processar exatamente 1 ordem
            assert result['processed'] == 1
            assert result['confirmed'] == 1
            assert len(result['errors']) == 0
            
            # Verificar ordem confirmada
            db_session.refresh(order)
            assert order.status == 'concluida'
            assert order.confirmed_at is not None
            assert order.auto_confirmed is True
    
    def test_auto_confirm_no_expired_orders(self, app, db_session):
        """Testa quando não há ordens expiradas"""
        with app.app_context():
            # Limpar todas as ordens
            Order.query.delete()
            db_session.commit()
            
            result = OrderManagementService.auto_confirm_expired_orders()
            
            assert result['processed'] == 0
            assert result['confirmed'] == 0
            assert len(result['errors']) == 0


class TestCancelOrder:
    """Testes para cancel_order()"""
    
    def test_cancel_by_client_success(self, app, db_session):
        """Testa cancelamento bem-sucedido pelo cliente"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente11@test.com', nome='Cliente', cpf='12121212121',
                          phone='11999999021', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador11@test.com', nome='Prestador', cpf='13131313131',
                           phone='11999999022', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo em escrow
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Teste', 'credito')
            
            # Criar ordem
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=service_value,
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Cancelar ordem
            result = OrderManagementService.cancel_order(
                order.id, 
                cliente.id, 
                'Motivo do cancelamento pelo cliente'
            )
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'cancelada'
            assert result['cancelled_by'] == 'cliente'
            assert result['cancellation_fee'] > 0
            assert result['injured_party'] == 'prestador'
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'cancelada'
            assert order.cancelled_by == cliente.id
            assert order.cancelled_at is not None
            assert order.cancellation_reason == 'Motivo do cancelamento pelo cliente'
            assert order.cancellation_fee is not None
    
    def test_cancel_by_provider_success(self, app, db_session):
        """Testa cancelamento bem-sucedido pelo prestador"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente12@test.com', nome='Cliente', cpf='14141414141',
                          phone='11999999023', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador12@test.com', nome='Prestador', cpf='15151515151',
                           phone='11999999024', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, service_value + contestation_fee, 'Teste', 'credito')
            
            # Criar ordem
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=service_value,
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Cancelar ordem pelo prestador
            result = OrderManagementService.cancel_order(
                order.id,
                prestador.id,
                'Motivo do cancelamento pelo prestador'
            )
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'cancelada'
            assert result['cancelled_by'] == 'prestador'
            assert result['injured_party'] == 'cliente'
    
    def test_cancel_invalid_status(self, app, db_session):
        """Testa erro ao cancelar ordem em status inválido"""
        with app.app_context():
            cliente = User(email='cliente13@test.com', nome='Cliente', cpf='16161616161',
                          phone='11999999025', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador13@test.com', nome='Prestador', cpf='17171717171',
                           phone='11999999026', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não pode ser cancelada"):
                OrderManagementService.cancel_order(order.id, cliente.id, 'Motivo')
    
    def test_cancel_without_reason(self, app, db_session):
        """Testa erro ao cancelar sem fornecer motivo"""
        with app.app_context():
            cliente = User(email='cliente14@test.com', nome='Cliente', cpf='18181818181',
                          phone='11999999027', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador14@test.com', nome='Prestador', cpf='19191919191',
                           phone='11999999028', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Motivo do cancelamento é obrigatório"):
                OrderManagementService.cancel_order(order.id, cliente.id, '')


class TestOpenDispute:
    """Testes para open_dispute()"""
    
    def test_open_dispute_success(self, app, db_session):
        """Testa abertura bem-sucedida de contestação"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente15@test.com', nome='Cliente', cpf='20202020202',
                          phone='11999999029', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador15@test.com', nome='Prestador', cpf='21212121212',
                           phone='11999999030', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar ordem em status servico_executado
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('200.00'),
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36),
                dispute_deadline=datetime.utcnow() + timedelta(hours=36),
                contestation_fee_at_creation=Decimal('10.00')
            )
            db_session.add(order)
            db_session.commit()
            
            # Abrir contestação
            reason = 'Serviço não foi executado conforme combinado. Problemas graves.'
            result = OrderManagementService.open_dispute(order.id, cliente.id, reason)
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'contestada'
            assert result['dispute_opened_at'] is not None
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'contestada'
            assert order.dispute_opened_by == cliente.id
            assert order.dispute_opened_at is not None
            assert order.dispute_client_statement == reason
    
    def test_open_dispute_short_reason(self, app, db_session):
        """Testa erro quando motivo é muito curto"""
        with app.app_context():
            cliente = User(email='cliente16@test.com', nome='Cliente', cpf='22222222223',
                          phone='11999999031', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador16@test.com', nome='Prestador', cpf='23232323232',
                           phone='11999999032', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36),
                dispute_deadline=datetime.utcnow() + timedelta(hours=36)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="no mínimo 20 caracteres"):
                OrderManagementService.open_dispute(order.id, cliente.id, 'Curto')
    
    def test_open_dispute_expired_deadline(self, app, db_session):
        """Testa erro quando prazo de contestação expirou"""
        with app.app_context():
            cliente = User(email='cliente17@test.com', nome='Cliente', cpf='24242424242',
                          phone='11999999033', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador17@test.com', nome='Prestador', cpf='25252525252',
                           phone='11999999034', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(hours=48),
                confirmation_deadline=datetime.utcnow() - timedelta(hours=12),
                dispute_deadline=datetime.utcnow() - timedelta(hours=12)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Prazo para contestação expirado"):
                OrderManagementService.open_dispute(
                    order.id, 
                    cliente.id, 
                    'Motivo longo o suficiente para passar na validação'
                )
    
    def test_open_dispute_wrong_status(self, app, db_session):
        """Testa erro quando ordem não está em status válido"""
        with app.app_context():
            cliente = User(email='cliente18@test.com', nome='Cliente', cpf='26262626262',
                          phone='11999999035', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador18@test.com', nome='Prestador', cpf='27272727272',
                           phone='11999999036', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não pode ser contestada"):
                OrderManagementService.open_dispute(
                    order.id,
                    cliente.id,
                    'Motivo longo o suficiente para passar na validação'
                )


class TestResolveDispute:
    """Testes para resolve_dispute()"""
    
    def test_resolve_dispute_client_wins(self, app, db_session):
        """Testa resolução de disputa a favor do cliente"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente19@test.com', nome='Cliente', cpf='28282828282',
                          phone='11999999037', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador19@test.com', nome='Prestador', cpf='29292929292',
                           phone='11999999038', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo em escrow
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Teste', 'credito')
            
            # Criar ordem contestada
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=service_value,
                status='contestada',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                dispute_opened_at=datetime.utcnow(),
                dispute_opened_by=cliente.id,
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Resolver disputa a favor do cliente
            result = OrderManagementService.resolve_dispute(
                order.id,
                1,  # admin_id
                'client',
                'Cliente apresentou provas suficientes'
            )
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'resolvida'
            assert result['winner'] == 'client'
            assert result['winner_name'] == 'cliente'
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'resolvida'
            assert order.dispute_winner == 'client'
            assert order.dispute_resolved_at is not None
            assert order.dispute_admin_notes == 'Cliente apresentou provas suficientes'
    
    def test_resolve_dispute_provider_wins(self, app, db_session):
        """Testa resolução de disputa a favor do prestador"""
        with app.app_context():
            # Criar usuários
            cliente = User(email='cliente20@test.com', nome='Cliente', cpf='30303030304',
                          phone='11999999039', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador20@test.com', nome='Prestador', cpf='31313131313',
                           phone='11999999040', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo em escrow
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Teste', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Teste', 'credito')
            
            # Criar ordem contestada
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=service_value,
                status='contestada',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                dispute_opened_at=datetime.utcnow(),
                dispute_opened_by=cliente.id,
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Resolver disputa a favor do prestador
            result = OrderManagementService.resolve_dispute(
                order.id,
                1,  # admin_id
                'provider',
                'Prestador comprovou execução correta'
            )
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'resolvida'
            assert result['winner'] == 'provider'
            assert result['winner_name'] == 'prestador'
            
            # Verificar ordem atualizada
            db_session.refresh(order)
            assert order.status == 'resolvida'
            assert order.dispute_winner == 'provider'
            assert order.dispute_resolved_at is not None
    
    def test_resolve_dispute_invalid_winner(self, app, db_session):
        """Testa erro quando winner é inválido"""
        with app.app_context():
            cliente = User(email='cliente21@test.com', nome='Cliente', cpf='32323232323',
                          phone='11999999041', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador21@test.com', nome='Prestador', cpf='33333333334',
                           phone='11999999042', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='contestada',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Winner deve ser 'client' ou 'provider'"):
                OrderManagementService.resolve_dispute(order.id, 1, 'invalid', 'Notas')
    
    def test_resolve_dispute_wrong_status(self, app, db_session):
        """Testa erro quando ordem não está contestada"""
        with app.app_context():
            cliente = User(email='cliente22@test.com', nome='Cliente', cpf='34343434343',
                          phone='11999999043', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador22@test.com', nome='Prestador', cpf='35353535353',
                           phone='11999999044', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço',
                description='Descrição',
                value=Decimal('100.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(order)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não está contestada"):
                OrderManagementService.resolve_dispute(order.id, 1, 'client', 'Notas')


class TestGetOrdersByUser:
    """Testes para get_orders_by_user()"""
    
    def test_get_orders_by_client(self, app, db_session):
        """Testa busca de ordens por cliente"""
        with app.app_context():
            cliente = User(email='cliente23@test.com', nome='Cliente', cpf='36363636363',
                          phone='11999999045', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador23@test.com', nome='Prestador', cpf='37373737373',
                           phone='11999999046', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar múltiplas ordens
            for i in range(3):
                order = Order(
                    client_id=cliente.id,
                    provider_id=prestador.id,
                    title=f'Serviço Cliente23 {i}',
                    description='Descrição',
                    value=Decimal('100.00'),
                    status='aguardando_execucao',
                    service_deadline=datetime.utcnow() + timedelta(days=7)
                )
                db_session.add(order)
            db_session.commit()
            
            # Buscar ordens
            orders = OrderManagementService.get_orders_by_user(cliente.id, 'cliente')
            
            # Filtrar apenas as ordens deste teste
            orders_test = [o for o in orders if 'Cliente23' in o.title]
            assert len(orders_test) == 3
            assert all(order.client_id == cliente.id for order in orders_test)
    
    def test_get_orders_with_status_filter(self, app, db_session):
        """Testa busca de ordens com filtro de status"""
        with app.app_context():
            cliente = User(email='cliente24@test.com', nome='Cliente', cpf='38383838383',
                          phone='11999999047', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador24@test.com', nome='Prestador', cpf='39393939393',
                           phone='11999999048', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar ordens com diferentes status
            order1 = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Cliente24 Aguardando',
                description='Descrição',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            order2 = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Cliente24 Concluída',
                description='Descrição',
                value=Decimal('100.00'),
                status='concluida',
                service_deadline=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add_all([order1, order2])
            db_session.commit()
            
            # Buscar apenas ordens concluídas
            orders = OrderManagementService.get_orders_by_user(
                cliente.id, 
                'cliente', 
                status_filter='concluida'
            )
            
            # Filtrar apenas as ordens deste teste
            orders_test = [o for o in orders if 'Cliente24' in o.title]
            assert len(orders_test) == 1
            assert orders_test[0].status == 'concluida'


class TestGetOrderStatistics:
    """Testes para get_order_statistics()"""
    
    def test_get_statistics_for_client(self, app, db_session):
        """Testa estatísticas de ordens para cliente"""
        with app.app_context():
            cliente = User(email='cliente25@test.com', nome='Cliente', cpf='40404040404',
                          phone='11999999049', roles='cliente')
            cliente.set_password('senha123')
            prestador = User(email='prestador25@test.com', nome='Prestador', cpf='41414141414',
                           phone='11999999050', roles='prestador')
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar ordens com diferentes status
            statuses = ['aguardando_execucao', 'servico_executado', 'concluida', 'cancelada']
            for status in statuses:
                order = Order(
                    client_id=cliente.id,
                    provider_id=prestador.id,
                    title=f'Serviço Cliente25 {status}',
                    description='Descrição',
                    value=Decimal('100.00'),
                    status=status,
                    service_deadline=datetime.utcnow() + timedelta(days=7)
                )
                db_session.add(order)
            db_session.commit()
            
            # Obter estatísticas
            stats = OrderManagementService.get_order_statistics(cliente.id, 'cliente')
            
            # Verificar que as estatísticas incluem pelo menos as ordens criadas
            assert stats['total'] >= 4
            assert stats['aguardando'] >= 1
            assert stats['para_confirmar'] >= 1
            assert stats['concluidas'] >= 1
            assert stats['canceladas'] >= 1
    
    def test_get_statistics_empty(self, app, db_session):
        """Testa estatísticas quando não há ordens"""
        with app.app_context():
            cliente = User(email='cliente26@test.com', nome='Cliente', cpf='42424242424',
                          phone='11999999051', roles='cliente')
            cliente.set_password('senha123')
            db_session.add(cliente)
            db_session.commit()
            
            stats = OrderManagementService.get_order_statistics(cliente.id, 'cliente')
            
            assert stats['total'] == 0
            assert stats['aguardando'] == 0
            assert stats['para_confirmar'] == 0
            assert stats['concluidas'] == 0
