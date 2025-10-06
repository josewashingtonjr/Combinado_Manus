#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para o sistema de alternância de papéis
Valida que usuários dual podem alternar entre cliente e prestador
"""

import pytest
from flask import session
from app import app, db
from models import User, Wallet
from services.role_service import RoleService

class TestAlternanciaPapeis:
    """Testes para alternância de papéis de usuário"""
    
    @pytest.fixture
    def client(self):
        """Cliente de teste Flask"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def user_cliente_only(self):
        """Criar usuário apenas cliente"""
        user = User(
            email='cliente@test.com',
            nome='Cliente Teste',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        return user
    
    @pytest.fixture
    def user_prestador_only(self):
        """Criar usuário apenas prestador"""
        user = User(
            email='prestador@test.com',
            nome='Prestador Teste',
            cpf='98765432100',
            roles='prestador'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        return user
    
    @pytest.fixture
    def user_dual_role(self):
        """Criar usuário com múltiplos papéis"""
        user = User(
            email='dual@test.com',
            nome='Usuário Dual',
            cpf='11122233344',
            roles='cliente,prestador'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        return user
    
    def test_get_user_roles_single(self, client, user_cliente_only):
        """Testar obtenção de papéis para usuário com papel único"""
        roles = RoleService.get_user_roles(user_cliente_only.id)
        assert roles == ['cliente']
    
    def test_get_user_roles_dual(self, client, user_dual_role):
        """Testar obtenção de papéis para usuário dual"""
        roles = RoleService.get_user_roles(user_dual_role.id)
        assert set(roles) == {'cliente', 'prestador'}
    
    def test_is_dual_role_user_false(self, client, user_cliente_only):
        """Testar detecção de usuário não-dual"""
        assert RoleService.is_dual_role_user(user_cliente_only.id) == False
    
    def test_is_dual_role_user_true(self, client, user_dual_role):
        """Testar detecção de usuário dual"""
        assert RoleService.is_dual_role_user(user_dual_role.id) == True
    
    def test_has_role_true(self, client, user_dual_role):
        """Testar verificação de papel existente"""
        assert RoleService.has_role(user_dual_role.id, 'cliente') == True
        assert RoleService.has_role(user_dual_role.id, 'prestador') == True
    
    def test_has_role_false(self, client, user_cliente_only):
        """Testar verificação de papel inexistente"""
        assert RoleService.has_role(user_cliente_only.id, 'prestador') == False
    
    def test_initialize_user_session(self, client, user_dual_role):
        """Testar inicialização de sessão do usuário"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_dual_role.id
        
        with app.test_request_context():
            session['user_id'] = user_dual_role.id
            result = RoleService.initialize_user_session(user_dual_role.id)
            
            assert result == True
            assert session.get('active_role') in ['cliente', 'prestador']
            assert session.get('user_roles') == ['cliente', 'prestador']
    
    def test_set_active_role_valid(self, client, user_dual_role):
        """Testar definição de papel ativo válido"""
        with app.test_request_context():
            session['user_id'] = user_dual_role.id
            
            result = RoleService.set_active_role('prestador')
            assert result == True
            assert RoleService.get_active_role() == 'prestador'
    
    def test_set_active_role_invalid(self, client, user_cliente_only):
        """Testar definição de papel ativo inválido"""
        with app.test_request_context():
            session['user_id'] = user_cliente_only.id
            
            result = RoleService.set_active_role('prestador')
            assert result == False
    
    def test_switch_role_dual_user(self, client, user_dual_role):
        """Testar alternância de papel para usuário dual"""
        with app.test_request_context():
            session['user_id'] = user_dual_role.id
            session['active_role'] = 'cliente'
            
            result = RoleService.switch_role()
            assert result == True
            assert RoleService.get_active_role() == 'prestador'
            
            # Alternar novamente
            result = RoleService.switch_role()
            assert result == True
            assert RoleService.get_active_role() == 'cliente'
    
    def test_switch_role_single_user(self, client, user_cliente_only):
        """Testar alternância de papel para usuário com papel único"""
        with app.test_request_context():
            session['user_id'] = user_cliente_only.id
            session['active_role'] = 'cliente'
            
            result = RoleService.switch_role()
            assert result == False  # Não pode alternar
    
    def test_get_available_roles(self, client, user_dual_role):
        """Testar obtenção de papéis disponíveis"""
        roles = RoleService.get_available_roles(user_dual_role.id)
        
        assert len(roles) == 2
        role_codes = [role[0] for role in roles]
        role_names = [role[1] for role in roles]
        
        assert 'cliente' in role_codes
        assert 'prestador' in role_codes
        assert 'Cliente' in role_names
        assert 'Prestador' in role_names
    
    def test_get_role_dashboard_url(self, client):
        """Testar obtenção de URL do dashboard por papel"""
        assert RoleService.get_role_dashboard_url('cliente') == 'cliente.dashboard'
        assert RoleService.get_role_dashboard_url('prestador') == 'prestador.dashboard'
        assert RoleService.get_role_dashboard_url('invalid') == 'cliente.dashboard'  # Default
    
    def test_get_role_color(self, client):
        """Testar obtenção de cor por papel"""
        assert RoleService.get_role_color('cliente') == 'success'
        assert RoleService.get_role_color('prestador') == 'warning'
        assert RoleService.get_role_color('invalid') == 'secondary'  # Default
    
    def test_get_role_icon(self, client):
        """Testar obtenção de ícone por papel"""
        assert RoleService.get_role_icon('cliente') == 'fas fa-user-tie'
        assert RoleService.get_role_icon('prestador') == 'fas fa-user-cog'
        assert RoleService.get_role_icon('invalid') == 'fas fa-user'  # Default
    
    def test_get_context_for_templates_dual_user(self, client, user_dual_role):
        """Testar contexto para templates com usuário dual"""
        with app.test_request_context():
            session['user_id'] = user_dual_role.id
            session['active_role'] = 'cliente'
            
            context = RoleService.get_context_for_templates()
            
            assert context['active_role'] == 'cliente'
            assert context['is_dual_role'] == True
            assert context['can_switch_roles'] == True
            assert len(context['available_roles']) == 2
            assert context['role_color'] == 'success'
            assert context['role_icon'] == 'fas fa-user-tie'
    
    def test_get_context_for_templates_single_user(self, client, user_cliente_only):
        """Testar contexto para templates com usuário de papel único"""
        with app.test_request_context():
            session['user_id'] = user_cliente_only.id
            session['active_role'] = 'cliente'
            
            context = RoleService.get_context_for_templates()
            
            assert context['active_role'] == 'cliente'
            assert context['is_dual_role'] == False
            assert context['can_switch_roles'] == False
            assert len(context['available_roles']) == 1
    
    def test_get_context_for_templates_no_user(self, client):
        """Testar contexto para templates sem usuário logado"""
        with app.test_request_context():
            context = RoleService.get_context_for_templates()
            
            assert context['active_role'] is None
            assert context['is_dual_role'] == False
            assert context['can_switch_roles'] == False
            assert context['available_roles'] == []
    
    def test_role_routes_switch(self, client, user_dual_role):
        """Testar rota de alternância de papéis"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_dual_role.id
            sess['active_role'] = 'cliente'
        
        response = client.get('/role/switch')
        
        # Deve redirecionar para dashboard do prestador
        assert response.status_code == 302
        assert '/prestador/dashboard' in response.location
    
    def test_role_routes_set_valid(self, client, user_dual_role):
        """Testar rota de definição de papel válido"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_dual_role.id
        
        response = client.get('/role/set/prestador')
        
        # Deve redirecionar para dashboard do prestador
        assert response.status_code == 302
        assert '/prestador/dashboard' in response.location
    
    def test_role_routes_set_invalid(self, client, user_cliente_only):
        """Testar rota de definição de papel inválido"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_cliente_only.id
        
        response = client.get('/role/set/prestador')
        
        # Deve redirecionar com erro
        assert response.status_code == 302
    
    def test_role_routes_current_api(self, client, user_dual_role):
        """Testar API de papel atual"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_dual_role.id
            sess['active_role'] = 'cliente'
        
        response = client.get('/role/current')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['active_role'] == 'cliente'
        assert data['is_dual_role'] == True
        assert data['can_switch_roles'] == True
        assert len(data['available_roles']) == 2
    
    def test_role_routes_info_api(self, client, user_dual_role):
        """Testar API de informações de papéis"""
        with client.session_transaction() as sess:
            sess['user_id'] = user_dual_role.id
            sess['active_role'] = 'prestador'
        
        response = client.get('/role/info')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['user_id'] == user_dual_role.id
        assert data['user_name'] == user_dual_role.nome
        assert data['user_email'] == user_dual_role.email
        assert set(data['all_roles']) == {'cliente', 'prestador'}
        assert data['active_role'] == 'prestador'
        assert data['is_dual_role'] == True
        assert data['role_color'] == 'warning'
        assert data['role_icon'] == 'fas fa-user-cog'
    
    def test_terminologia_mantida_apos_troca(self, client, user_dual_role):
        """Testar que terminologia R$ é mantida após troca de papel"""
        with app.test_request_context():
            session['user_id'] = user_dual_role.id
            session['active_role'] = 'cliente'
            
            # Obter contexto como cliente
            from app import inject_user_context
            context_cliente = inject_user_context()
            
            # Alternar para prestador
            RoleService.set_active_role('prestador')
            context_prestador = inject_user_context()
            
            # Ambos devem usar terminologia "R$" (não "tokens")
            assert context_cliente['terminology']['balance_label'] == 'Saldo'
            assert context_cliente['terminology']['currency_symbol'] == 'R$'
            assert context_prestador['terminology']['balance_label'] == 'Saldo'
            assert context_prestador['terminology']['currency_symbol'] == 'R$'
            
            # Verificar que não há terminologia técnica
            assert 'token' not in context_cliente['terminology']['balance_label'].lower()
            assert 'token' not in context_prestador['terminology']['balance_label'].lower()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])