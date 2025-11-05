#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Autenticação e Autorização
"""

import pytest
from models import User, AdminUser
from services.auth_service import AuthService


class TestUserAuthentication:
    """Testes de autenticação de usuários"""
    
    def test_user_login_success(self, client, test_user):
        """Testa login de usuário com credenciais válidas"""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_user_login_invalid_email(self, client):
        """Testa login com email inválido"""
        response = client.post('/auth/login', data={
            'email': 'invalid@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Credenciais inv' in response.data or b'Email ou senha inv' in response.data
        
    def test_user_login_invalid_password(self, client, test_user):
        """Testa login com senha inválida"""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Credenciais inv' in response.data or b'Email ou senha inv' in response.data
        
    def test_user_logout(self, authenticated_client):
        """Testa logout de usuário"""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o usuário não está mais autenticado
        with authenticated_client.session_transaction() as sess:
            assert 'user_id' not in sess


class TestAdminAuthentication:
    """Testes de autenticação de administradores"""
    
    def test_admin_login_success(self, client, test_admin):
        """Testa login de administrador com credenciais válidas"""
        response = client.post('/auth/admin-login', data={
            'email': 'admin@example.com',
            'password': 'adminpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_admin_login_invalid_email(self, client):
        """Testa login de admin com email inválido"""
        response = client.post('/auth/admin-login', data={
            'email': 'invalid@example.com',
            'password': 'adminpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Credenciais inv' in response.data or b'Email ou senha inv' in response.data
        
    def test_admin_login_invalid_password(self, client, test_admin):
        """Testa login de admin com senha inválida"""
        response = client.post('/auth/admin-login', data={
            'email': 'admin@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Credenciais inv' in response.data or b'Email ou senha inv' in response.data
        
    def test_admin_logout(self, authenticated_admin_client):
        """Testa logout de administrador"""
        response = authenticated_admin_client.get('/auth/admin-logout', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o admin não está mais autenticado
        with authenticated_admin_client.session_transaction() as sess:
            assert 'admin_id' not in sess


class TestAuthorization:
    """Testes de autorização e controle de acesso"""
    
    def test_protected_route_requires_login(self, client):
        """Testa que rotas protegidas requerem login"""
        response = client.get('/app/home', follow_redirects=True)
        
        # Deve redirecionar para login
        assert response.status_code == 200
        assert b'Login' in response.data or b'Entrar' in response.data
        
    def test_admin_route_requires_admin_login(self, client):
        """Testa que rotas administrativas requerem login de admin"""
        response = client.get('/admin/dashboard', follow_redirects=True)
        
        # Deve redirecionar para login de admin
        assert response.status_code == 200
        assert b'Admin' in response.data or b'Login' in response.data
        
    def test_user_cannot_access_admin_routes(self, authenticated_client):
        """Testa que usuários não podem acessar rotas administrativas"""
        response = authenticated_client.get('/admin/dashboard', follow_redirects=True)
        
        # Deve ser bloqueado
        assert response.status_code == 200
        assert b'Acesso negado' in response.data or b'Admin' in response.data
        
    def test_authenticated_user_can_access_protected_routes(self, authenticated_client):
        """Testa que usuários autenticados podem acessar rotas protegidas"""
        response = authenticated_client.get('/app/home', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_authenticated_admin_can_access_admin_routes(self, authenticated_admin_client):
        """Testa que administradores podem acessar rotas administrativas"""
        response = authenticated_admin_client.get('/admin/dashboard', follow_redirects=True)
        
        assert response.status_code == 200


class TestRoleManagement:
    """Testes de gerenciamento de papéis"""
    
    def test_user_with_cliente_role_can_access_cliente_routes(self, authenticated_client):
        """Testa que usuários com papel de cliente podem acessar rotas de cliente"""
        response = authenticated_client.get('/app/home', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_user_with_prestador_role_can_access_prestador_routes(self, client, test_provider):
        """Testa que usuários com papel de prestador podem acessar rotas de prestador"""
        with client.session_transaction() as sess:
            sess['user_id'] = test_provider.id
            sess['active_role'] = 'prestador'
            
        response = client.get('/prestador/dashboard', follow_redirects=True)
        
        assert response.status_code == 200
        
    def test_role_switching_for_dual_role_user(self, client, db_session):
        """Testa troca de papel para usuário com múltiplos papéis"""
        # Criar usuário com múltiplos papéis
        dual_user = User(
            email='dual@example.com',
            nome='Dual User',
            cpf='11122233344',
            phone='11999999999',
            roles='cliente,prestador'
        )
        dual_user.set_password('dualpass123')
        db_session.add(dual_user)
        db_session.commit()
        
        # Autenticar como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = dual_user.id
            sess['active_role'] = 'cliente'
            
        # Trocar para prestador
        response = client.post('/role/switch', follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verificar que o papel foi trocado
        with client.session_transaction() as sess:
            assert sess.get('active_role') == 'prestador'


class TestPasswordSecurity:
    """Testes de segurança de senha"""
    
    def test_password_is_hashed(self, db_session):
        """Testa que senhas são armazenadas de forma criptografada"""
        user = User(
            email='security@example.com',
            nome='Security Test',
            cpf='55566677788',
            phone='11988888888',
            roles='cliente'
        )
        user.set_password('mysecretpassword')
        db_session.add(user)
        db_session.commit()
        
        # Verificar que a senha não é armazenada em texto plano
        assert user.password_hash != 'mysecretpassword'
        assert len(user.password_hash) > 20  # Hash deve ser longo
        
    def test_password_verification(self, test_user):
        """Testa verificação de senha"""
        # Senha correta
        assert test_user.check_password('testpassword123') is True
        
        # Senha incorreta
        assert test_user.check_password('wrongpassword') is False


class TestSessionManagement:
    """Testes de gerenciamento de sessão"""
    
    def test_session_created_on_login(self, client, test_user):
        """Testa que a sessão é criada após login"""
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword123'
        })
        
        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert sess['user_id'] == test_user.id
            
    def test_session_cleared_on_logout(self, authenticated_client):
        """Testa que a sessão é limpa após logout"""
        authenticated_client.get('/auth/logout')
        
        with authenticated_client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'active_role' not in sess

