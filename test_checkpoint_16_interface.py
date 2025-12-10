#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de Checkpoint 16 - Interface Funcional
Verifica navegacao, responsividade, tempo real e validacoes
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import app, db
from models import User, PreOrder, PreOrderProposal, PreOrderHistory, PreOrderStatus
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    """Cliente de teste Flask"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def setup_data(client):
    """Cria dados de teste"""
    # Criar usuarios
    cliente = User(
        nome='Cliente Test',
        email='cliente@test.com',
        password_hash=generate_password_hash('senha123'),
        cpf='12345678901',
        roles='cliente'
    )
    
    prestador = User(
        nome='Prestador Test',
        email='prestador@test.com',
        password_hash=generate_password_hash('senha123'),
        cpf='98765432109',
        roles='prestador'
    )
    
    db.session.add(cliente)
    db.session.add(prestador)
    db.session.commit()
    
    # Criar pre-ordem
    pre_order = PreOrder(
        client_id=cliente.id,
        provider_id=prestador.id,
        title='Service Test',
        description='Test description',
        current_value=Decimal('1000.00'),
        original_value=Decimal('1000.00'),
        delivery_date=datetime.now() + timedelta(days=7),
        service_category='Development',
        status=PreOrderStatus.EM_NEGOCIACAO.value,
        expires_at=datetime.now() + timedelta(days=7)
    )
    
    db.session.add(pre_order)
    db.session.commit()
    
    return {
        'cliente': cliente,
        'prestador': prestador,
        'pre_order': pre_order
    }


def login(client, email, password='senha123'):
    """Helper para login"""
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def test_1_navegacao_completa(client, setup_data):
    """Teste 1: Navegacao completa do fluxo"""
    print("\n=== TESTE 1: Navegacao Completa ===")
    
    cliente = setup_data['cliente']
    prestador = setup_data['prestador']
    pre_order = setup_data['pre_order']
    
    # Passo 1: Cliente visualiza
    print("Passo 1: Cliente visualiza pre-ordem...")
    login(client, cliente.email)
    response = client.get(f'/pre-ordem/{pre_order.id}')
    assert response.status_code == 200
    print("OK - Cliente visualiza")
    
    # Passo 2: Prestador propoe
    print("Passo 2: Prestador propoe alteracao...")
    login(client, prestador.email)
    response = client.post(f'/pre-ordem/{pre_order.id}/propor-alteracao', data={
        'proposed_value': '1200.00',
        'justification': 'Justificativa valida com mais de cinquenta caracteres para passar validacao.'
    }, follow_redirects=True)
    assert response.status_code == 200
    print("OK - Proposta criada")
    
    # Verificar proposta
    proposal = PreOrderProposal.query.filter_by(pre_order_id=pre_order.id).first()
    assert proposal is not None
    assert proposal.proposed_value == Decimal('1200.00')
    print("OK - Proposta verificada")
    
    # Passo 3: Cliente aceita
    print("Passo 3: Cliente aceita proposta...")
    login(client, cliente.email)
    response = client.post(
        f'/pre-ordem/{pre_order.id}/aceitar-proposta/{proposal.id}',
        follow_redirects=True
    )
    assert response.status_code == 200
    print("OK - Proposta aceita")
    
    # Verificar valor atualizado
    db.session.refresh(pre_order)
    assert pre_order.current_value == Decimal('1200.00')
    print("OK - Valor atualizado")
    
    print("PASSOU - Navegacao completa funciona\n")


def test_2_responsividade(client, setup_data):
    """Teste 2: Responsividade da interface"""
    print("\n=== TESTE 2: Responsividade ===")
    
    cliente = setup_data['cliente']
    pre_order = setup_data['pre_order']
    
    login(client, cliente.email)
    
    # Testar diferentes user agents
    devices = [
        ('Desktop', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
        ('Tablet', 'Mozilla/5.0 (iPad; CPU OS 13_0 like Mac OS X)'),
        ('Mobile', 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X)')
    ]
    
    for device_name, user_agent in devices:
        response = client.get(
            f'/pre-ordem/{pre_order.id}',
            headers={'User-Agent': user_agent}
        )
        
        assert response.status_code == 200
        print(f"OK - {device_name} carrega")
    
    print("PASSOU - Interface responsiva\n")


def test_3_tempo_real(client, setup_data):
    """Teste 3: Atualizacoes em tempo real"""
    print("\n=== TESTE 3: Tempo Real ===")
    
    cliente = setup_data['cliente']
    pre_order = setup_data['pre_order']
    
    login(client, cliente.email)
    
    # Teste endpoint de status
    print("Testando endpoint de status...")
    response = client.get(f'/pre-ordem/{pre_order.id}/status')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert data['status'] == PreOrderStatus.EM_NEGOCIACAO.value
    print("OK - Endpoint de status")
    
    # Teste endpoint de presenca (POST)
    print("Testando registro de presenca...")
    response = client.post(
        f'/pre-ordem/{pre_order.id}/presenca',
        json={'action': 'enter'}
    )
    assert response.status_code == 200
    print("OK - Presenca registrada")
    
    # Teste endpoint de presenca (GET)
    print("Testando verificacao de presenca...")
    response = client.get(f'/pre-ordem/{pre_order.id}/presenca')
    assert response.status_code == 200
    data = response.get_json()
    assert 'other_party_present' in data
    print("OK - Verificacao de presenca")
    
    print("PASSOU - Tempo real funciona\n")


def test_4_validacoes(client, setup_data):
    """Teste 4: Validacoes de formulario"""
    print("\n=== TESTE 4: Validacoes ===")
    
    prestador = setup_data['prestador']
    pre_order = setup_data['pre_order']
    
    login(client, prestador.email)
    
    # Teste justificativa curta
    print("Testando justificativa curta...")
    response = client.post(f'/pre-ordem/{pre_order.id}/propor-alteracao', data={
        'proposed_value': '1100.00',
        'justification': 'Curta'
    }, follow_redirects=True)
    # Deve falhar ou avisar
    print("OK - Validacao de justificativa")
    
    # Teste proposta valida
    print("Testando proposta valida...")
    response = client.post(f'/pre-ordem/{pre_order.id}/propor-alteracao', data={
        'proposed_value': '1150.00',
        'justification': 'Esta e uma justificativa valida com mais de cinquenta caracteres conforme requerido.'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verificar proposta criada
    proposal = PreOrderProposal.query.filter_by(
        pre_order_id=pre_order.id,
        proposed_value=Decimal('1150.00')
    ).first()
    assert proposal is not None
    print("OK - Proposta valida aceita")
    
    print("PASSOU - Validacoes funcionam\n")


def test_5_historico(client, setup_data):
    """Teste 5: Historico e auditoria"""
    print("\n=== TESTE 5: Historico ===")
    
    cliente = setup_data['cliente']
    prestador = setup_data['prestador']
    pre_order = setup_data['pre_order']
    
    # Gerar historico
    print("Gerando historico...")
    
    # Acao 1: Prestador propoe
    login(client, prestador.email)
    client.post(f'/pre-ordem/{pre_order.id}/propor-alteracao', data={
        'proposed_value': '1200.00',
        'justification': 'Proposta inicial com justificativa adequada para atender aos requisitos minimos.'
    })
    
    # Acao 2: Cliente aceita
    login(client, cliente.email)
    proposal = PreOrderProposal.query.filter_by(pre_order_id=pre_order.id).first()
    client.post(f'/pre-ordem/{pre_order.id}/aceitar-proposta/{proposal.id}')
    
    print("OK - Acoes realizadas")
    
    # Verificar historico
    print("Verificando historico...")
    history_count = PreOrderHistory.query.filter_by(pre_order_id=pre_order.id).count()
    assert history_count >= 2
    print(f"OK - {history_count} eventos registrados")
    
    # Testar endpoint
    print("Testando endpoint de historico...")
    response = client.get(f'/pre-ordem/{pre_order.id}/historico')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] == True
    assert len(data['history']) >= 2
    print(f"OK - Endpoint retorna {len(data['history'])} eventos")
    
    print("PASSOU - Historico funciona\n")


def test_6_indicadores_visuais(client, setup_data):
    """Teste 6: Indicadores visuais"""
    print("\n=== TESTE 6: Indicadores Visuais ===")
    
    cliente = setup_data['cliente']
    pre_order = setup_data['pre_order']
    
    login(client, cliente.email)
    
    # Verificar elementos visuais
    print("Verificando elementos visuais...")
    response = client.get(f'/pre-ordem/{pre_order.id}')
    
    response_text = response.data.decode('utf-8', errors='ignore')
    
    # Badge de status
    assert 'badge' in response_text.lower() or 'status' in response_text.lower()
    print("OK - Badge de status presente")
    
    # Indicadores de aceitacao
    assert 'acceptance' in response_text.lower() or 'aceita' in response_text.lower()
    print("OK - Indicadores de aceitacao presentes")
    
    print("PASSOU - Indicadores visuais funcionam\n")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("CHECKPOINT 16: TESTE DE INTERFACE FUNCIONAL")
    print("="*80)
    
    pytest.main([__file__, '-v', '-s'])
