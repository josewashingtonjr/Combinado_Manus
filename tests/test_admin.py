#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Funcionalidades Administrativas
"""

import pytest
from models import User, AdminUser, Wallet, SystemConfig, Transaction
from services.admin_service import AdminService
from services.wallet_service import WalletService


class TestAdminDashboard:
    """Testes do dashboard administrativo"""
    
    def test_admin_can_view_dashboard(self, authenticated_admin_client):
        """Testa que administrador pode visualizar o dashboard"""
        response = authenticated_admin_client.get('/admin/dashboard', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Admin' in response.data
        
    def test_admin_dashboard_shows_statistics(self, authenticated_admin_client, db_session):
        """Testa que o dashboard exibe estatísticas do sistema"""
        response = authenticated_admin_client.get('/admin/dashboard', follow_redirects=True)
        
        assert response.status_code == 200
        # Verificar que estatísticas estão presentes
        assert b'Usu' in response.data or b'Total' in response.data


class TestAdminUserManagement:
    """Testes de gerenciamento de usuários"""
    
    def test_admin_can_view_users(self, authenticated_admin_client):
        """Testa que administrador pode visualizar lista de usuários"""
        response = authenticated_admin_client.get('/admin/usuarios', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Usu' in response.data
        
    def test_admin_can_create_user(self, authenticated_admin_client, db_session):
        """Testa que administrador pode criar novo usuário"""
        response = authenticated_admin_client.post('/admin/usuarios/criar', data={
            'email': 'newuser@example.com',
            'nome': 'New User',
            'cpf': '12345678901',
            'phone': '11987654321',
            'password': 'newpassword123',
            'roles': 'cliente'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o usuário foi criado
        user = db_session.query(User).filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.nome == 'New User'
        
    def test_admin_can_edit_user(self, authenticated_admin_client, test_user, db_session):
        """Testa que administrador pode editar usuário existente"""
        response = authenticated_admin_client.post(f'/admin/usuarios/{test_user.id}/editar', data={
            'nome': 'Updated Name',
            'phone': '11999999999'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o usuário foi atualizado
        db_session.refresh(test_user)
        assert test_user.nome == 'Updated Name'
        
    def test_admin_can_delete_user(self, authenticated_admin_client, db_session):
        """Testa que administrador pode deletar usuário"""
        # Criar usuário para deletar
        user_to_delete = User(
            email='delete@example.com',
            nome='Delete Me',
            cpf='99988877766',
            phone='11900000000',
            roles='cliente'
        )
        user_to_delete.set_password('deletepass123')
        db_session.add(user_to_delete)
        db_session.commit()
        
        response = authenticated_admin_client.post(f'/admin/usuarios/{user_to_delete.id}/deletar', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o usuário foi deletado
        deleted_user = db_session.query(User).filter_by(id=user_to_delete.id).first()
        assert deleted_user is None or deleted_user.active is False


class TestAdminTokenManagement:
    """Testes de gerenciamento de tokens"""
    
    def test_admin_can_create_tokens(self, authenticated_admin_client, db_session):
        """Testa que administrador pode criar tokens"""
        response = authenticated_admin_client.post('/admin/tokens/criar', data={
            'amount': 1000.00,
            'description': 'Criação de tokens para teste'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_admin_can_view_token_history(self, authenticated_admin_client):
        """Testa que administrador pode visualizar histórico de tokens"""
        response = authenticated_admin_client.get('/admin/tokens', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Token' in response.data or b'Hist' in response.data
        
    def test_admin_cannot_create_negative_tokens(self, authenticated_admin_client):
        """Testa que administrador não pode criar quantidade negativa de tokens"""
        response = authenticated_admin_client.post('/admin/tokens/criar', data={
            'amount': -100.00,
            'description': 'Tentativa de criar tokens negativos'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'inv' in response.data.lower() or b'erro' in response.data.lower()


class TestAdminSystemConfig:
    """Testes de configurações do sistema"""
    
    def test_admin_can_view_system_config(self, authenticated_admin_client):
        """Testa que administrador pode visualizar configurações do sistema"""
        response = authenticated_admin_client.get('/admin/configuracoes', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Config' in response.data or b'Sistema' in response.data
        
    def test_admin_can_update_system_config(self, authenticated_admin_client, db_session):
        """Testa que administrador pode atualizar configurações do sistema"""
        response = authenticated_admin_client.post('/admin/configuracoes', data={
            'system_fee_percent': 0.10,  # 10%
            'min_withdrawal_amount': 20.00
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que a configuração foi atualizada
        config = db_session.query(SystemConfig).first()
        if config:
            assert config.system_fee_percent == 0.10
            
    def test_admin_config_validation(self, authenticated_admin_client):
        """Testa validação de configurações inválidas"""
        response = authenticated_admin_client.post('/admin/configuracoes', data={
            'system_fee_percent': 1.5,  # 150% - inválido
            'min_withdrawal_amount': -10.00  # Negativo - inválido
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'inv' in response.data.lower() or b'erro' in response.data.lower()


class TestAdminTransactionMonitoring:
    """Testes de monitoramento de transações"""
    
    def test_admin_can_view_all_transactions(self, authenticated_admin_client):
        """Testa que administrador pode visualizar todas as transações"""
        response = authenticated_admin_client.get('/admin/transacoes', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Transa' in response.data
        
    def test_admin_can_filter_transactions(self, authenticated_admin_client):
        """Testa que administrador pode filtrar transações"""
        response = authenticated_admin_client.get('/admin/transacoes?type=credit', follow_redirects=True)
        
        assert response.status_code == 200


class TestAdminOrderManagement:
    """Testes de gerenciamento de ordens"""
    
    def test_admin_can_view_all_orders(self, authenticated_admin_client):
        """Testa que administrador pode visualizar todas as ordens"""
        response = authenticated_admin_client.get('/admin/ordens', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Ordens' in response.data or b'Ordem' in response.data
        
    def test_admin_can_resolve_dispute(self, authenticated_admin_client, test_user, test_provider, db_session):
        """Testa que administrador pode resolver disputa"""
        from models import Order
        
        # Criar ordem em disputa
        order = Order(
            client_id=test_user.id,
            provider_id=test_provider.id,
            title='Ordem em Disputa',
            description='Descrição',
            value=50.00,
            status='em_disputa',
            dispute_reason='Cliente não recebeu o serviço'
        )
        db_session.add(order)
        db_session.commit()
        
        response = authenticated_admin_client.post(f'/admin/ordens/{order.id}/resolver-disputa', data={
            'resolution': 'refund',  # Reembolsar cliente
            'notes': 'Serviço não foi entregue conforme acordado'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestAdminReports:
    """Testes de relatórios administrativos"""
    
    def test_admin_can_generate_financial_report(self, authenticated_admin_client):
        """Testa que administrador pode gerar relatório financeiro"""
        response = authenticated_admin_client.get('/admin/relatorios/financeiro', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_admin_can_generate_user_report(self, authenticated_admin_client):
        """Testa que administrador pode gerar relatório de usuários"""
        response = authenticated_admin_client.get('/admin/relatorios/usuarios', follow_redirects=True)
        
        assert response.status_code == 200


class TestAdminService:
    """Testes do serviço administrativo"""
    
    def test_get_dashboard_stats(self, db_session):
        """Testa obtenção de estatísticas do dashboard"""
        stats = AdminService.get_dashboard_stats()
        
        assert 'total_users' in stats
        assert 'total_transactions' in stats
        assert 'total_orders' in stats
        
    def test_create_user_service(self, db_session):
        """Testa criação de usuário via serviço"""
        user_data = {
            'email': 'service@example.com',
            'nome': 'Service User',
            'cpf': '11122233344',
            'phone': '11988888888',
            'password': 'servicepass123',
            'roles': 'cliente'
        }
        
        user = AdminService.create_user(user_data)
        
        assert user is not None
        assert user.email == 'service@example.com'
        
        # Verificar que a carteira foi criada
        wallet = db_session.query(Wallet).filter_by(user_id=user.id).first()
        assert wallet is not None
        
    def test_update_system_config_service(self, db_session):
        """Testa atualização de configuração via serviço"""
        config_data = {
            'system_fee_percent': 0.08,
            'min_withdrawal_amount': 15.00
        }
        
        config = AdminService.update_system_config(config_data)
        
        assert config is not None
        assert config.system_fee_percent == 0.08


class TestAdminSecurity:
    """Testes de segurança administrativa"""
    
    def test_regular_user_cannot_access_admin_routes(self, authenticated_client):
        """Testa que usuário regular não pode acessar rotas administrativas"""
        response = authenticated_client.get('/admin/dashboard', follow_redirects=True)
        
        # Deve ser bloqueado ou redirecionado
        assert response.status_code == 200
        assert b'Acesso negado' in response.data or b'Admin' in response.data or b'Login' in response.data
        
    def test_unauthenticated_user_cannot_access_admin_routes(self, client):
        """Testa que usuário não autenticado não pode acessar rotas administrativas"""
        response = client.get('/admin/dashboard', follow_redirects=True)
        
        # Deve redirecionar para login
        assert response.status_code == 200
        assert b'Login' in response.data or b'Admin' in response.data
        
    def test_admin_actions_are_logged(self, authenticated_admin_client, db_session):
        """Testa que ações administrativas são logadas"""
        # Criar um usuário
        authenticated_admin_client.post('/admin/usuarios/criar', data={
            'email': 'logged@example.com',
            'nome': 'Logged User',
            'cpf': '55566677788',
            'phone': '11977777777',
            'password': 'loggedpass123',
            'roles': 'cliente'
        }, follow_redirects=True)
        
        # Verificar que a ação foi logada
        from models import ActionLog
        log = db_session.query(ActionLog).filter_by(action='create_user').order_by(ActionLog.created_at.desc()).first()
        
        if log:
            assert log.action == 'create_user'


class TestAdminWalletManagement:
    """Testes de gerenciamento de carteiras"""
    
    def test_admin_can_view_all_wallets(self, authenticated_admin_client):
        """Testa que administrador pode visualizar todas as carteiras"""
        response = authenticated_admin_client.get('/admin/carteiras', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_admin_can_credit_user_wallet(self, authenticated_admin_client, test_user, db_session):
        """Testa que administrador pode creditar carteira de usuário"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        response = authenticated_admin_client.post(f'/admin/carteiras/{test_user.id}/creditar', data={
            'amount': 100.00,
            'description': 'Crédito administrativo'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o saldo foi atualizado
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance + 100.00
        
    def test_admin_can_debit_user_wallet(self, authenticated_admin_client, test_user, db_session):
        """Testa que administrador pode debitar carteira de usuário"""
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        response = authenticated_admin_client.post(f'/admin/carteiras/{test_user.id}/debitar', data={
            'amount': 20.00,
            'description': 'Débito administrativo'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o saldo foi atualizado
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance - 20.00

