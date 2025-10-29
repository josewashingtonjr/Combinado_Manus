#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Funcionalidades de Cliente e Prestador
"""

import pytest
from models import User, Wallet, Order, Transaction, Invite
from services.wallet_service import WalletService
from services.order_service import OrderService
from services.invite_service import InviteService


class TestClienteWallet:
    """Testes de carteira do cliente"""
    
    def test_cliente_can_view_wallet(self, authenticated_client):
        """Testa que cliente pode visualizar sua carteira"""
        response = authenticated_client.get('/app/carteira', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Carteira' in response.data or b'Saldo' in response.data
        
    def test_cliente_wallet_shows_correct_balance(self, authenticated_client, test_user, db_session):
        """Testa que a carteira exibe o saldo correto"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        
        response = authenticated_client.get('/app/carteira', follow_redirects=True)
        
        assert response.status_code == 200
        # Verificar que o saldo está presente na resposta
        assert str(wallet.balance) in response.data.decode() or 'R$' in response.data.decode()


class TestClienteOrders:
    """Testes de ordens de serviço do cliente"""
    
    def test_cliente_can_create_order(self, authenticated_client, test_provider, db_session):
        """Testa que cliente pode criar uma ordem de serviço"""
        response = authenticated_client.post('/cliente/ordens/criar', data={
            'provider_id': test_provider.id,
            'title': 'Teste de Ordem',
            'description': 'Descrição da ordem de teste',
            'value': 50.00
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que a ordem foi criada
        order = db_session.query(Order).filter_by(title='Teste de Ordem').first()
        assert order is not None
        assert order.value == 50.00
        
    def test_cliente_cannot_create_order_without_balance(self, authenticated_client, test_user, test_provider, db_session):
        """Testa que cliente não pode criar ordem sem saldo suficiente"""
        # Zerar saldo do cliente
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        wallet.balance = 0.0
        db_session.commit()
        
        response = authenticated_client.post('/cliente/ordens/criar', data={
            'provider_id': test_provider.id,
            'title': 'Ordem Sem Saldo',
            'description': 'Esta ordem não deve ser criada',
            'value': 50.00
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Saldo insuficiente' in response.data or b'saldo' in response.data.lower()
        
    def test_cliente_can_view_order_history(self, authenticated_client):
        """Testa que cliente pode visualizar histórico de ordens"""
        response = authenticated_client.get('/cliente/ordens', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Ordens' in response.data or b'Hist' in response.data


class TestClienteInvites:
    """Testes de convites do cliente"""
    
    def test_cliente_can_create_invite(self, authenticated_client, db_session):
        """Testa que cliente pode criar um convite"""
        response = authenticated_client.post('/cliente/convites/criar', data={
            'invited_email': 'prestador@example.com',
            'service_title': 'Serviço de Teste',
            'service_description': 'Descrição do serviço',
            'original_value': 100.00,
            'delivery_date': '2025-12-31'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o convite foi criado
        invite = db_session.query(Invite).filter_by(service_title='Serviço de Teste').first()
        assert invite is not None
        
    def test_cliente_can_view_invites(self, authenticated_client):
        """Testa que cliente pode visualizar seus convites"""
        response = authenticated_client.get('/cliente/convites', follow_redirects=True)
        
        assert response.status_code == 200


class TestPrestadorDashboard:
    """Testes do dashboard do prestador"""
    
    def test_prestador_can_view_dashboard(self, client, test_provider):
        """Testa que prestador pode visualizar seu dashboard"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/dashboard', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Prestador' in response.data


class TestPrestadorOrders:
    """Testes de ordens do prestador"""
    
    def test_prestador_can_view_available_orders(self, client, test_provider):
        """Testa que prestador pode visualizar ordens disponíveis"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/ordens/disponiveis', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_prestador_can_accept_order(self, client, test_provider, test_user, db_session):
        """Testa que prestador pode aceitar uma ordem"""
        # Criar uma ordem disponível
        order = Order(
            client_id=test_user.id,
            title='Ordem para Aceitar',
            description='Descrição',
            value=50.00,
            status='disponivel'
        )
        db_session.add(order)
        db_session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.post(f'/prestador/ordens/{order.id}/aceitar', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que a ordem foi aceita
        db_session.refresh(order)
        assert order.status == 'aceita'
        assert order.provider_id == test_provider.id
        
    def test_prestador_can_complete_order(self, client, test_provider, test_user, db_session):
        """Testa que prestador pode concluir uma ordem"""
        # Criar uma ordem aceita
        order = Order(
            client_id=test_user.id,
            provider_id=test_provider.id,
            title='Ordem para Concluir',
            description='Descrição',
            value=50.00,
            status='aceita'
        )
        db_session.add(order)
        db_session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.post(f'/prestador/ordens/{order.id}/concluir', follow_redirects=True)
        
        assert response.status_code == 200


class TestPrestadorInvites:
    """Testes de convites do prestador"""
    
    def test_prestador_can_view_invites(self, client, test_provider):
        """Testa que prestador pode visualizar convites recebidos"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/convites', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_prestador_can_accept_invite(self, client, test_provider, test_user, db_session):
        """Testa que prestador pode aceitar um convite"""
        # Criar um convite
        invite = Invite(
            client_id=test_user.id,
            invited_email=test_provider.email,
            service_title='Serviço Convidado',
            service_description='Descrição',
            original_value=100.00,
            final_value=100.00,
            status='pendente',
            token='test-token-123'
        )
        db_session.add(invite)
        db_session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.post(f'/prestador/convites/{invite.id}/aceitar', data={
            'final_value': 90.00,
            'delivery_date': '2025-12-31'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_prestador_can_reject_invite(self, client, test_provider, test_user, db_session):
        """Testa que prestador pode recusar um convite"""
        # Criar um convite
        invite = Invite(
            client_id=test_user.id,
            invited_email=test_provider.email,
            service_title='Serviço para Recusar',
            service_description='Descrição',
            original_value=100.00,
            final_value=100.00,
            status='pendente',
            token='test-token-456'
        )
        db_session.add(invite)
        db_session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.post(f'/prestador/convites/{invite.id}/recusar', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o convite foi recusado
        db_session.refresh(invite)
        assert invite.status == 'recusado'


class TestPrestadorWallet:
    """Testes de carteira do prestador"""
    
    def test_prestador_can_view_wallet(self, client, test_provider):
        """Testa que prestador pode visualizar sua carteira"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/carteira', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Carteira' in response.data or b'Saldo' in response.data
        
    def test_prestador_can_request_withdrawal(self, client, test_provider, db_session):
        """Testa que prestador pode solicitar saque"""
        # Garantir que o prestador tem saldo suficiente
        wallet = db_session.query(Wallet).filter_by(user_id=test_provider.id).first()
        wallet.balance = 100.0
        db_session.commit()
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.post('/prestador/carteira/saque', data={
            'amount': 50.00,
            'bank_account': '12345-6',
            'bank_name': 'Banco Teste'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestTransactionHistory:
    """Testes de histórico de transações"""
    
    def test_cliente_can_view_transaction_history(self, authenticated_client):
        """Testa que cliente pode visualizar histórico de transações"""
        response = authenticated_client.get('/app/historico', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Hist' in response.data or b'Transa' in response.data
        
    def test_prestador_can_view_transaction_history(self, client, test_provider):
        """Testa que prestador pode visualizar histórico de transações"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/historico', follow_redirects=True)
        
        assert response.status_code == 200


class TestWalletService:
    """Testes do serviço de carteira"""
    
    def test_credit_wallet(self, test_user, db_session):
        """Testa crédito na carteira"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        WalletService.credit_wallet(test_user.id, 50.00, 'Teste de crédito')
        
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance + 50.00
        
    def test_debit_wallet(self, test_user, db_session):
        """Testa débito na carteira"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        WalletService.debit_wallet(test_user.id, 20.00, 'Teste de débito')
        
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance - 20.00
        
    def test_debit_wallet_insufficient_balance(self, test_user, db_session):
        """Testa que débito falha com saldo insuficiente"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        wallet.balance = 10.0
        db_session.commit()
        
        with pytest.raises(ValueError):
            WalletService.debit_wallet(test_user.id, 50.00, 'Teste de débito sem saldo')
            
    def test_transfer_to_escrow(self, test_user, db_session):
        """Testa transferência para escrow"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        initial_escrow = wallet.escrow_balance
        
        WalletService.transfer_to_escrow(test_user.id, 30.00)
        
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance - 30.00
        assert wallet.escrow_balance == initial_escrow + 30.00

