#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para o sistema de terminologia diferenciada
Valida que administradores veem "tokens" e usuários veem "R$"
"""

import pytest
from flask import session
from app import app, db
from models import User, AdminUser, Wallet

class TestTerminologiaDiferenciada:
    """Testes para terminologia diferenciada por tipo de usuário"""
    
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
    def admin_user(self):
        """Criar usuário administrador para testes"""
        admin = AdminUser(
            email='admin@test.com',
            papel='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        return admin
    
    @pytest.fixture
    def regular_user(self):
        """Criar usuário regular para testes"""
        user = User(
            email='user@test.com',
            nome='Usuário Teste',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('user123')
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira para o usuário
        wallet = Wallet(user_id=user.id, balance=1000.0)
        db.session.add(wallet)
        db.session.commit()
        
        return user
    
    def test_filtro_format_currency(self, client):
        """Testar filtro format_currency para usuários finais"""
        with app.app_context():
            # Testar valores válidos
            assert app.jinja_env.filters['format_currency'](1000) == "R$ 1.000,00"
            assert app.jinja_env.filters['format_currency'](1000.50) == "R$ 1.000,50"
            assert app.jinja_env.filters['format_currency'](0) == "R$ 0,00"
            
            # Testar valores None e inválidos
            assert app.jinja_env.filters['format_currency'](None) == "R$ 0,00"
            assert app.jinja_env.filters['format_currency']("invalid") == "R$ 0,00"
    
    def test_filtro_format_tokens(self, client):
        """Testar filtro format_tokens para administradores"""
        with app.app_context():
            # Testar valores válidos
            assert app.jinja_env.filters['format_tokens'](1) == "1 token"
            assert app.jinja_env.filters['format_tokens'](1000) == "1.000 tokens"
            assert app.jinja_env.filters['format_tokens'](0) == "0 tokens"
            
            # Testar valores None e inválidos
            assert app.jinja_env.filters['format_tokens'](None) == "0 tokens"
            assert app.jinja_env.filters['format_tokens']("invalid") == "0 tokens"
    
    def test_filtro_format_value_by_user_type(self, client):
        """Testar filtro que formata baseado no tipo de usuário"""
        with app.app_context():
            # Admin deve ver tokens
            assert app.jinja_env.filters['format_value_by_user_type'](1000, 'admin') == "1.000 tokens"
            
            # Usuário deve ver R$
            assert app.jinja_env.filters['format_value_by_user_type'](1000, 'user') == "R$ 1.000,00"
            assert app.jinja_env.filters['format_value_by_user_type'](1000, None) == "R$ 1.000,00"
    
    def test_context_processor_admin(self, client, admin_user):
        """Testar context processor para administrador"""
        with app.test_request_context():
            # Simular sessão no contexto da requisição
            from flask import session
            session['admin_id'] = admin_user.id
            
            # Testar context processor diretamente
            from app import inject_user_context
            context = inject_user_context()
            
            assert context['user_type'] == 'admin'
            assert context['is_admin_user'] == True
            assert context['terminology']['balance_label'] == 'Tokens'
            assert context['terminology']['balance_unit'] == 'tokens'
            assert context['terminology']['technical_view'] == True
    
    def test_context_processor_user(self, client, regular_user):
        """Testar context processor para usuário regular"""
        with app.test_request_context():
            # Simular sessão no contexto da requisição
            from flask import session
            session['user_id'] = regular_user.id
            
            # Testar context processor diretamente
            from app import inject_user_context
            context = inject_user_context()
            
            assert context['user_type'] == 'user'
            assert context['is_admin_user'] == False
            assert context['terminology']['balance_label'] == 'Saldo'
            assert context['terminology']['balance_unit'] == 'R$'
            assert context['terminology']['technical_view'] == False
    
    def test_context_processor_sem_usuario(self, client):
        """Testar context processor sem usuário logado"""
        with app.test_request_context():
            # Testar context processor diretamente
            from app import inject_user_context
            context = inject_user_context()
            
            assert context['user_type'] == 'user'
            assert context['is_admin_user'] == False
            assert context['terminology']['balance_label'] == 'Saldo'
    
    def test_deteccao_automatica_tipo_usuario_simplificado(self, client, admin_user, regular_user):
        """Testar detecção automática do tipo de usuário (versão simplificada)"""
        # Testar context processor com admin
        with app.test_request_context():
            from flask import session
            session['admin_id'] = admin_user.id
            
            from app import inject_user_context
            context = inject_user_context()
            assert context['user_type'] == 'admin'
        
        # Testar context processor com usuário regular
        with app.test_request_context():
            from flask import session
            session['user_id'] = regular_user.id
            
            from app import inject_user_context
            context = inject_user_context()
            assert context['user_type'] == 'user'
    
    def test_validacao_nao_vazamento_terminologia(self, client):
        """Testar que terminologia técnica não vaza para usuários"""
        with app.test_request_context():
            # Simular contexto de usuário regular
            from flask import session
            session['user_id'] = 1  # Usuário regular
            
            from app import inject_user_context
            context = inject_user_context()
            
            # Verificar que usuário NÃO vê terminologia técnica
            assert 'token' not in context['terminology']['balance_label'].lower()
            assert 'token' not in context['terminology']['balance_unit'].lower()
            assert context['terminology']['technical_view'] == False
    
    def test_consistencia_terminologia_admin(self, client):
        """Testar consistência da terminologia para admin"""
        with app.test_request_context():
            # Simular sessão no contexto da requisição
            from flask import session
            session['admin_id'] = 1
            
            # Testar context processor diretamente
            from app import inject_user_context
            context = inject_user_context()
            
            # Verificar que admin vê terminologia técnica consistente
            assert context['terminology']['balance_label'] == 'Tokens'
            assert context['terminology']['balance_unit'] == 'tokens'
            assert context['terminology']['technical_view'] == True
            assert context['terminology']['currency_symbol'] == ''

if __name__ == '__main__':
    pytest.main([__file__, '-v'])