#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes Unitários para InviteAcceptanceCoordinator

Testa:
- Detecção de aceitação mútua
- Criação de ordem após aceitação mútua
- Validação de saldos insuficientes (cliente e prestador)
- Rollback em caso de erro

Requirements: Todos os requisitos do spec
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from models import db, User, Invite, Order, Wallet
from services.invite_acceptance_coordinator import InviteAcceptanceCoordinator
from services.exceptions import (
    InsufficientBalanceError,
    OrderCreationError,
    EscrowBlockError
)


class TestDetectMutualAcceptance:
    """Testes para detecção de aceitação mútua"""
    
    def test_nenhuma_aceitacao(self, app, db_session):
        """Testa quando nenhuma parte aceitou"""
        with app.app_context():
            # Criar convite sem aceitações
            invite = Invite(
                client_id=1,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=False,
                provider_accepted=False
            )
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            
            assert not is_mutual
            assert 'cliente' in msg.lower() or 'prestador' in msg.lower()
    
    def test_apenas_cliente_aceita(self, app, db_session):
        """Testa quando apenas o cliente aceitou"""
        with app.app_context():
            invite = Invite(
                client_id=1,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=False
            )
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            
            assert not is_mutual
            assert 'prestador' in msg.lower()
    
    def test_apenas_prestador_aceita(self, app, db_session):
        """Testa quando apenas o prestador aceitou"""
        with app.app_context():
            invite = Invite(
                client_id=1,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=False,
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow()
            )
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            
            assert not is_mutual
            assert 'cliente' in msg.lower()
    
    def test_ambos_aceitam(self, app, db_session):
        """Testa quando ambas as partes aceitaram"""
        with app.app_context():
            invite = Invite(
                client_id=1,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow()
            )
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            
            assert is_mutual
            assert 'ambas' in msg.lower()
    
    def test_convite_nulo(self, app):
        """Testa com convite nulo"""
        with app.app_context():
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(None)
            
            assert not is_mutual
            assert 'não encontrado' in msg.lower()


class TestCreateOrderOnMutualAcceptance:
    """Testes para criação de ordem após aceitação mútua"""
    
    def test_cria_ordem_com_sucesso(self, app, db_session, test_user, test_provider):
        """Testa criação bem-sucedida de ordem"""
        with app.app_context():
            # Adicionar saldo suficiente
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('500.00')
            provider_wallet.balance = Decimal('50.00')
            db_session.commit()
            
            # Criar convite com aceitação mútua
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            # Criar ordem
            with patch('services.invite_acceptance_coordinator.NotificationService'):
                result = InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
            
            assert result['success']
            assert result['order_id'] is not None
            assert result['order'] is not None
            
            # Verificar que convite foi atualizado
            db_session.refresh(invite)
            assert invite.status == 'convertido'
            assert invite.order_id == result['order_id']
    
    def test_falha_sem_aceitacao_mutua(self, app, db_session, test_user):
        """Testa que falha se não há aceitação mútua"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11999999999',
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                provider_accepted=False
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="não foi aceito por ambas as partes"):
                InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
    
    def test_falha_prestador_nao_encontrado(self, app, db_session, test_user):
        """Testa que falha se prestador não existe no sistema"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone='11888888888',  # Telefone que não existe
                service_title='Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow()
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Prestador não encontrado"):
                InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)


class TestInsufficientBalanceClient:
    """Testes para saldo insuficiente do cliente"""
    
    def test_cliente_sem_saldo_suficiente(self, app, db_session, test_user, test_provider):
        """Testa erro quando cliente não tem saldo suficiente"""
        with app.app_context():
            # Cliente com saldo insuficiente
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('50.00')  # Menos que o necessário
            provider_wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),  # Mais que o saldo
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            with patch('services.invite_acceptance_coordinator.NotificationService'):
                with pytest.raises(InsufficientBalanceError) as exc_info:
                    InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                
                error = exc_info.value
                assert error.user_type == 'cliente'
                assert error.required_amount == Decimal('100.00')
                assert error.current_balance == Decimal('50.00')
    
    def test_validacao_saldo_cliente(self, app):
        """Testa validação de saldo do cliente"""
        with app.app_context():
            with patch('services.invite_acceptance_coordinator.WalletService') as mock_wallet:
                mock_wallet.get_wallet_balance.side_effect = [
                    Decimal('50.00'),  # Cliente
                    Decimal('50.00')   # Prestador
                ]
                
                result = InviteAcceptanceCoordinator._validate_balances_for_order(
                    client_id=1,
                    provider_id=2,
                    service_value=Decimal('100.00')
                )
                
                assert not result['valid']
                assert result['error'] == 'cliente'
                assert result['client_balance'] == Decimal('50.00')
                assert result['client_required'] == Decimal('100.00')


class TestInsufficientBalanceProvider:
    """Testes para saldo insuficiente do prestador"""
    
    def test_prestador_sem_saldo_suficiente(self, app, db_session, test_user, test_provider):
        """Testa erro quando prestador não tem saldo para taxa"""
        with app.app_context():
            # Prestador com saldo insuficiente para taxa
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('500.00')
            provider_wallet.balance = Decimal('5.00')  # Menos que a taxa de R$ 10
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            with patch('services.invite_acceptance_coordinator.NotificationService'):
                with pytest.raises(InsufficientBalanceError) as exc_info:
                    InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                
                error = exc_info.value
                assert error.user_type == 'prestador'
                assert error.required_amount == Decimal('10.00')
                assert error.current_balance == Decimal('5.00')
    
    def test_validacao_saldo_prestador(self, app):
        """Testa validação de saldo do prestador"""
        with app.app_context():
            with patch('services.invite_acceptance_coordinator.WalletService') as mock_wallet:
                mock_wallet.get_wallet_balance.side_effect = [
                    Decimal('500.00'),  # Cliente
                    Decimal('5.00')     # Prestador
                ]
                
                result = InviteAcceptanceCoordinator._validate_balances_for_order(
                    client_id=1,
                    provider_id=2,
                    service_value=Decimal('100.00')
                )
                
                assert not result['valid']
                assert result['error'] == 'prestador'
                assert result['provider_balance'] == Decimal('5.00')
                assert result['provider_required'] == Decimal('10.00')


class TestRollbackOnError:
    """Testes para rollback em caso de erro"""
    
    def test_rollback_em_erro_criacao_ordem(self, app, db_session, test_user, test_provider):
        """Testa rollback quando criação de ordem falha"""
        with app.app_context():
            # Configurar saldos adequados
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('500.00')
            provider_wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            original_status = invite.status
            
            # Simular erro na criação da ordem
            with patch('services.invite_acceptance_coordinator.OrderService') as mock_order:
                mock_order.create_order_from_invite.return_value = {
                    'success': False,
                    'error': 'Erro simulado'
                }
                
                with pytest.raises(OrderCreationError):
                    InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                
                # Verificar que status foi revertido
                db_session.refresh(invite)
                assert invite.status == 'aceito'
                assert invite.order_id is None
    
    def test_rollback_em_erro_bloqueio_escrow(self, app, db_session, test_user, test_provider):
        """Testa rollback quando bloqueio de escrow falha"""
        with app.app_context():
            # Configurar saldos adequados
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('500.00')
            provider_wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            # Simular sucesso na criação da ordem mas falha no bloqueio
            with patch('services.invite_acceptance_coordinator.OrderService') as mock_order:
                with patch('services.invite_acceptance_coordinator.WalletService') as mock_wallet:
                    # Ordem criada com sucesso
                    mock_order.create_order_from_invite.return_value = {
                        'success': True,
                        'order': Mock(id=123)
                    }
                    
                    # Validação de saldo retorna valores válidos
                    mock_wallet.get_wallet_balance.side_effect = [
                        Decimal('500.00'),  # Cliente
                        Decimal('50.00')    # Prestador
                    ]
                    
                    # Bloqueio de escrow falha
                    mock_wallet.transfer_to_escrow.side_effect = Exception("Erro no escrow")
                    
                    with pytest.raises(EscrowBlockError):
                        InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                    
                    # Verificar que convite foi revertido para permitir retry
                    db_session.refresh(invite)
                    assert invite.status == 'aceito'
                    assert invite.order_id is None
    
    def test_convite_permanece_aceito_para_retry(self, app, db_session, test_user, test_provider):
        """Testa que convite permanece aceito após erro para permitir retry"""
        with app.app_context():
            client_wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            
            client_wallet.balance = Decimal('500.00')
            provider_wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                client_accepted=True,
                client_accepted_at=datetime.utcnow(),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow(),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            with patch('services.invite_acceptance_coordinator.OrderService') as mock_order:
                mock_order.create_order_from_invite.side_effect = Exception("Erro temporário")
                
                with pytest.raises(OrderCreationError):
                    InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                
                # Verificar que aceitações permanecem
                db_session.refresh(invite)
                assert invite.client_accepted is True
                assert invite.provider_accepted is True
                assert invite.status == 'aceito'  # Revertido para aceito, não pendente
