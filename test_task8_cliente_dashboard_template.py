#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar a atualização do template da dashboard do cliente
Tarefa 8: Atualizar template da dashboard do cliente
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from datetime import datetime
from models import User, Order, db
from services.wallet_service import WalletService
from services.dashboard_data_service import DashboardDataService
from services.cliente_service import ClienteService


def test_dashboard_template_shows_open_orders(client, db_session):
    """Testa se a dashboard exibe ordens em aberto"""
    # Criar usuário cliente
    cliente = User(
        email='cliente_test@example.com',
        nome='Cliente Teste',
        phone='11999999999',
        roles='cliente',
        active=True
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    db.session.commit()
    
    # Criar usuário prestador
    prestador = User(
        email='prestador_test@example.com',
        nome='Prestador Teste',
        phone='11888888888',
        roles='prestador',
        active=True
    )
    prestador.set_password('senha123')
    db.session.add(prestador)
    db.session.commit()
    
    # Garantir carteiras
    WalletService.ensure_user_has_wallet(cliente.id)
    WalletService.ensure_user_has_wallet(prestador.id)
    
    # Adicionar saldo
    WalletService.add_balance(cliente.id, 1000.0, 'Saldo inicial')
    WalletService.add_balance(prestador.id, 100.0, 'Saldo inicial')
    
    # Criar ordem em aberto
    ordem = Order(
        client_id=cliente.id,
        provider_id=prestador.id,
        title='Serviço de Teste',
        description='Descrição do serviço',
        value=100.0,
        status='aceita',
        created_at=datetime.utcnow()
    )
    db.session.add(ordem)
    db.session.commit()
    
    # Fazer login como cliente
    response = client.post('/auth/login', data={
        'email': 'cliente_test@example.com',
        'password': 'senha123'
    }, follow_redirects=True)
    
    # Acessar dashboard
    response = client.get('/cliente/dashboard')
    assert response.status_code == 200
    
    # Verificar se a seção de ordens em aberto está presente
    html = response.data.decode('utf-8')
    assert 'Ordens em Aberto' in html
    assert 'Serviço de Teste' in html
    assert 'Prestador Teste' in html
    assert '#' + str(ordem.id) in html
    

def test_dashboard_template_shows_blocked_funds(client, db_session):
    """Testa se a dashboard exibe fundos bloqueados"""
    # Criar usuário cliente
    cliente = User(
        email='cliente_blocked@example.com',
        nome='Cliente Bloqueado',
        phone='11777777777',
        roles='cliente',
        active=True
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    db.session.commit()
    
    # Criar usuário prestador
    prestador = User(
        email='prestador_blocked@example.com',
        nome='Prestador Bloqueado',
        phone='11666666666',
        roles='prestador',
        active=True
    )
    prestador.set_password('senha123')
    db.session.add(prestador)
    db.session.commit()
    
    # Garantir carteiras
    WalletService.ensure_user_has_wallet(cliente.id)
    WalletService.ensure_user_has_wallet(prestador.id)
    
    # Adicionar saldo
    WalletService.add_balance(cliente.id, 1000.0, 'Saldo inicial')
    WalletService.add_balance(prestador.id, 100.0, 'Saldo inicial')
    
    # Criar ordem e bloquear valores
    ordem = Order(
        client_id=cliente.id,
        provider_id=prestador.id,
        title='Serviço com Bloqueio',
        description='Descrição',
        value=200.0,
        status='aceita',
        created_at=datetime.utcnow()
    )
    db.session.add(ordem)
    db.session.commit()
    
    # Bloquear valores em escrow
    WalletService.transfer_to_escrow(cliente.id, 200.0, ordem.id, 'Bloqueio para ordem')
    
    # Fazer login como cliente
    response = client.post('/auth/login', data={
        'email': 'cliente_blocked@example.com',
        'password': 'senha123'
    }, follow_redirects=True)
    
    # Acessar dashboard
    response = client.get('/cliente/dashboard')
    assert response.status_code == 200
    
    # Verificar se a seção de fundos bloqueados está presente
    html = response.data.decode('utf-8')
    assert 'Fundos em Garantia' in html
    assert 'Bloqueado em Garantia' in html
    assert 'Detalhamento por Ordem' in html
    assert 'Serviço com Bloqueio' in html
    

def test_dashboard_template_shows_empty_state(client, db_session):
    """Testa se a dashboard exibe mensagem quando não há ordens"""
    # Criar usuário cliente
    cliente = User(
        email='cliente_empty@example.com',
        nome='Cliente Vazio',
        phone='11555555555',
        roles='cliente',
        active=True
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    db.session.commit()
    
    # Garantir carteira
    WalletService.ensure_user_has_wallet(cliente.id)
    WalletService.add_balance(cliente.id, 500.0, 'Saldo inicial')
    
    # Fazer login como cliente
    response = client.post('/auth/login', data={
        'email': 'cliente_empty@example.com',
        'password': 'senha123'
    }, follow_redirects=True)
    
    # Acessar dashboard
    response = client.get('/cliente/dashboard')
    assert response.status_code == 200
    
    # Verificar mensagem de estado vazio
    html = response.data.decode('utf-8')
    assert 'não tem ordens em aberto no momento' in html or 'Nenhuma ordem em aberto' in html
    

def test_dashboard_template_updated_statistics_cards(client, db_session):
    """Testa se os cards de estatísticas foram atualizados"""
    # Criar usuário cliente
    cliente = User(
        email='cliente_stats@example.com',
        nome='Cliente Stats',
        phone='11444444444',
        roles='cliente',
        active=True
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    db.session.commit()
    
    # Garantir carteira
    WalletService.ensure_user_has_wallet(cliente.id)
    WalletService.add_balance(cliente.id, 1000.0, 'Saldo inicial')
    
    # Fazer login como cliente
    response = client.post('/auth/login', data={
        'email': 'cliente_stats@example.com',
        'password': 'senha123'
    }, follow_redirects=True)
    
    # Acessar dashboard
    response = client.get('/cliente/dashboard')
    assert response.status_code == 200
    
    # Verificar se os cards de estatísticas estão presentes
    html = response.data.decode('utf-8')
    assert 'Saldo Disponível' in html
    assert 'Ordens em Aberto' in html
    assert 'Saldo Total' in html
    assert 'Transações (Mês)' in html
    

def test_dashboard_data_service_integration(client, db_session):
    """Testa integração com DashboardDataService"""
    # Criar usuário cliente
    cliente = User(
        email='cliente_integration@example.com',
        nome='Cliente Integration',
        phone='11333333333',
        roles='cliente',
        active=True
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    db.session.commit()
    
    # Criar usuário prestador
    prestador = User(
        email='prestador_integration@example.com',
        nome='Prestador Integration',
        phone='11222222222',
        roles='prestador',
        active=True
    )
    prestador.set_password('senha123')
    db.session.add(prestador)
    db.session.commit()
    
    # Garantir carteiras
    WalletService.ensure_user_has_wallet(cliente.id)
    WalletService.ensure_user_has_wallet(prestador.id)
    
    # Adicionar saldo
    WalletService.add_balance(cliente.id, 1000.0, 'Saldo inicial')
    WalletService.add_balance(prestador.id, 100.0, 'Saldo inicial')
    
    # Criar múltiplas ordens
    for i in range(3):
        ordem = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title=f'Serviço {i+1}',
            description=f'Descrição {i+1}',
            value=100.0 * (i+1),
            status='aceita' if i < 2 else 'em_andamento',
            created_at=datetime.utcnow()
        )
        db.session.add(ordem)
    db.session.commit()
    
    # Obter métricas do DashboardDataService
    metrics = DashboardDataService.get_dashboard_metrics(cliente.id, 'cliente')
    
    # Verificar métricas
    assert metrics['open_orders_count'] == 3
    assert len(metrics['open_orders']) == 3
    assert metrics['balance']['available'] == 1000.0
    
    # Fazer login e acessar dashboard
    response = client.post('/auth/login', data={
        'email': 'cliente_integration@example.com',
        'password': 'senha123'
    }, follow_redirects=True)
    
    response = client.get('/cliente/dashboard')
    assert response.status_code == 200
    
    # Verificar se todas as ordens aparecem
    html = response.data.decode('utf-8')
    assert 'Serviço 1' in html
    assert 'Serviço 2' in html
    assert 'Serviço 3' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
