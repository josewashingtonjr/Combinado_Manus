#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Configuração base para testes pytest
"""

import pytest
import sys
import os

# Adicionar o diretório raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, AdminUser, Wallet
from config import TestConfig


@pytest.fixture(scope='session')
def app():
    """Cria uma instância da aplicação para testes"""
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cria um cliente de teste para fazer requisições"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Cria um runner para comandos CLI"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Cria uma sessão de banco de dados para testes"""
    with app.app_context():
        # Limpar todas as tabelas antes de cada teste
        db.session.query(User).delete()
        db.session.query(AdminUser).delete()
        db.session.query(Wallet).delete()
        db.session.commit()
        
        yield db.session
        
        # Rollback após cada teste
        db.session.rollback()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Cria um usuário de teste"""
    user = User(
        email='test@example.com',
        nome='Test User',
        cpf='12345678901',
        phone='11987654321',
        roles='cliente'
    )
    user.set_password('testpassword123')
    db_session.add(user)
    db_session.commit()
    
    # Criar carteira para o usuário
    wallet = Wallet(user_id=user.id, balance=100.0, escrow_balance=0.0)
    db_session.add(wallet)
    db_session.commit()
    
    return user


@pytest.fixture(scope='function')
def test_admin(db_session):
    """Cria um administrador de teste"""
    admin = AdminUser(
        email='admin@example.com',
        papel='admin'
    )
    admin.set_password('adminpassword123')
    db_session.add(admin)
    db_session.commit()
    
    return admin


@pytest.fixture(scope='function')
def test_provider(db_session):
    """Cria um prestador de teste"""
    provider = User(
        email='provider@example.com',
        nome='Test Provider',
        cpf='98765432109',
        phone='11912345678',
        roles='prestador'
    )
    provider.set_password('providerpass123')
    db_session.add(provider)
    db_session.commit()
    
    # Criar carteira para o prestador
    wallet = Wallet(user_id=provider.id, balance=50.0, escrow_balance=0.0)
    db_session.add(wallet)
    db_session.commit()
    
    return provider


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Cria um cliente autenticado como usuário"""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
        sess['active_role'] = 'cliente'
    return client


@pytest.fixture(scope='function')
def authenticated_admin_client(client, test_admin):
    """Cria um cliente autenticado como administrador"""
    with client.session_transaction() as sess:
        sess['admin_id'] = test_admin.id
    return client

