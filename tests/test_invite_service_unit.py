#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes Unitários para InviteService (métodos de aceitação)

Testa:
- accept_invite_as_client
- accept_invite_as_provider
- Aceitação mútua que dispara criação de ordem
- Validação antes da aceitação

Requirements: 1.1-1.5, 8.1-8.5
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from models import db, User, Invite, Wallet
from services.invite_service import InviteService
from services.exceptions import InsufficientBalanceError


class TestAcceptAsClient:
    """Testes para accept_invite_as_client"""
    
    def test_cliente_aceita_convite_com_sucesso(self, app, db_session, test_user, test_provider):
        """Testa aceitação bem-sucedida pelo cliente"""
        with app.app_context():
            # Adicionar saldo suficiente
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('500.00')
            db_session.commit()
            
            # Criar convite
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': False,
                    'message': 'Aguardando prestador',
                    'pending_acceptance_from': 'prestador'
                }
                
                result = InviteService.accept_invite_as_client(invite.id, test_user.id)
            
            assert result['success']
            assert not result['order_created']
            
            # Verificar que convite foi marcado como aceito pelo cliente
            db_session.refresh(invite)
            assert invite.client_accepted is True
            assert invite.client_accepted_at is not None
    
    def test_valida_usuario_e_cliente_correto(self, app, db_session, test_user, test_provider):
        """Testa que valida se usuário é o cliente correto"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            # Tentar aceitar com ID de outro usuário
            with pytest.raises(ValueError, match="não autorizado"):
                InviteService.accept_invite_as_client(invite.id, test_provider.id)
    
    def test_valida_saldo_suficiente_antes_aceitar(self, app, db_session, test_user, test_provider):
        """Testa validação de saldo antes de aceitar"""
        with app.app_context():
            # Cliente com saldo insuficiente
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Saldo insuficiente"):
                InviteService.accept_invite_as_client(invite.id, test_user.id)
    
    def test_nao_aceita_convite_expirado(self, app, db_session, test_user, test_provider):
        """Testa que não aceita convite expirado"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('500.00')
            db_session.commit()
            
            # Convite expirado
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() - timedelta(days=1),
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="expirado"):
                InviteService.accept_invite_as_client(invite.id, test_user.id)


class TestAcceptAsProvider:
    """Testes para accept_invite_as_provider"""
    
    def test_prestador_aceita_convite_com_sucesso(self, app, db_session, test_user, test_provider):
        """Testa aceitação bem-sucedida pelo prestador"""
        with app.app_context():
            # Adicionar saldo suficiente para taxa
            wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': False,
                    'message': 'Aguardando cliente',
                    'pending_acceptance_from': 'cliente'
                }
                
                result = InviteService.accept_invite_as_provider(invite.id, test_provider.id)
            
            assert result['success']
            assert not result['order_created']
            
            # Verificar que convite foi marcado como aceito pelo prestador
            db_session.refresh(invite)
            assert invite.provider_accepted is True
            assert invite.provider_accepted_at is not None
    
    def test_valida_usuario_e_prestador_correto(self, app, db_session, test_user, test_provider):
        """Testa que valida se usuário é o prestador correto"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            # Tentar aceitar com usuário que não é o prestador convidado
            with pytest.raises(ValueError, match="não autorizado"):
                InviteService.accept_invite_as_provider(invite.id, test_user.id)
    
    def test_valida_saldo_para_taxa_antes_aceitar(self, app, db_session, test_user, test_provider):
        """Testa validação de saldo para taxa antes de aceitar"""
        with app.app_context():
            # Prestador com saldo insuficiente para taxa
            wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            wallet.balance = Decimal('5.00')  # Menos que a taxa de R$ 10
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="Saldo insuficiente"):
                InviteService.accept_invite_as_provider(invite.id, test_provider.id)


class TestMutualAcceptanceTriggersOrder:
    """Testes para aceitação mútua que dispara criação de ordem"""
    
    def test_ordem_criada_quando_ambos_aceitam(self, app, db_session, test_user, test_provider):
        """Testa que ordem é criada quando ambas as partes aceitam"""
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
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            # Cliente aceita primeiro
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': False,
                    'message': 'Aguardando prestador',
                    'pending_acceptance_from': 'prestador'
                }
                
                result1 = InviteService.accept_invite_as_client(invite.id, test_user.id)
                assert not result1['order_created']
            
            # Prestador aceita depois
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': True,
                    'order_id': 123,
                    'message': 'Ordem criada'
                }
                
                result2 = InviteService.accept_invite_as_provider(invite.id, test_provider.id)
                assert result2['order_created']
                assert result2['order_id'] == 123
    
    def test_ordem_criada_independente_da_ordem_aceitacao(self, app, db_session, test_user, test_provider):
        """Testa que ordem é criada independente de quem aceita primeiro"""
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
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db_session.add(invite)
            db_session.commit()
            
            # Prestador aceita primeiro
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': False,
                    'message': 'Aguardando cliente',
                    'pending_acceptance_from': 'cliente'
                }
                
                result1 = InviteService.accept_invite_as_provider(invite.id, test_provider.id)
                assert not result1['order_created']
            
            # Cliente aceita depois
            with patch('services.invite_service.InviteAcceptanceCoordinator') as mock_coord:
                mock_coord.process_acceptance.return_value = {
                    'success': True,
                    'order_created': True,
                    'order_id': 456,
                    'message': 'Ordem criada'
                }
                
                result2 = InviteService.accept_invite_as_client(invite.id, test_user.id)
                assert result2['order_created']
                assert result2['order_id'] == 456


class TestValidationBeforeAcceptance:
    """Testes para validação antes da aceitação"""
    
    def test_valida_convite_existe(self, app, db_session, test_user):
        """Testa validação de que convite existe"""
        with app.app_context():
            with pytest.raises(ValueError, match="não encontrado"):
                InviteService.accept_invite_as_client(99999, test_user.id)
    
    def test_valida_convite_nao_ja_convertido(self, app, db_session, test_user, test_provider):
        """Testa que não aceita convite já convertido em ordem"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                status='convertido',
                order_id=123
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="já foi convertido"):
                InviteService.accept_invite_as_client(invite.id, test_user.id)
    
    def test_valida_convite_nao_rejeitado(self, app, db_session, test_user, test_provider):
        """Testa que não aceita convite rejeitado"""
        with app.app_context():
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                status='rejeitado'
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="rejeitado"):
                InviteService.accept_invite_as_client(invite.id, test_user.id)
    
    def test_impede_aceitacao_duplicada_cliente(self, app, db_session, test_user, test_provider):
        """Testa que impede aceitação duplicada pelo cliente"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_user.id).first()
            wallet.balance = Decimal('500.00')
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
                client_accepted_at=datetime.utcnow()
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="já aceitou"):
                InviteService.accept_invite_as_client(invite.id, test_user.id)
    
    def test_impede_aceitacao_duplicada_prestador(self, app, db_session, test_user, test_provider):
        """Testa que impede aceitação duplicada pelo prestador"""
        with app.app_context():
            wallet = Wallet.query.filter_by(user_id=test_provider.id).first()
            wallet.balance = Decimal('50.00')
            db_session.commit()
            
            invite = Invite(
                client_id=test_user.id,
                invited_phone=test_provider.phone,
                service_title='Serviço Teste',
                service_description='Descrição',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7),
                provider_accepted=True,
                provider_accepted_at=datetime.utcnow()
            )
            db_session.add(invite)
            db_session.commit()
            
            with pytest.raises(ValueError, match="já aceitou"):
                InviteService.accept_invite_as_provider(invite.id, test_provider.id)
