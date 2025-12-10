#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de integração para a rota de ajuste de quantidade de tokens
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, AdminUser, TokenRequest
from decimal import Decimal
from datetime import datetime
import json

def setup_test_data():
    """Configura dados de teste e retorna IDs"""
    with app.app_context():
        # Limpar dados de teste anteriores
        TokenRequest.query.filter_by(description='TEST_ROUTE_ADJUST').delete()
        db.session.commit()
        
        # Criar usuário de teste se não existir
        user = User.query.filter_by(email='test_route_adjust@example.com').first()
        if not user:
            user = User(
                nome='Usuário Teste Rota',
                email='test_route_adjust@example.com',
                cpf='98765432100',
                phone='11988888888',
                roles='cliente',
                active=True
            )
            user.set_password('senha123')
            db.session.add(user)
            db.session.commit()
        
        # Criar admin de teste se não existir
        admin = AdminUser.query.filter_by(email='admin_route_test@example.com').first()
        if not admin:
            admin = AdminUser(
                email='admin_route_test@example.com',
                papel='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Criar solicitação de teste pendente
        token_request = TokenRequest(
            user_id=user.id,
            amount=Decimal('100.00'),
            description='TEST_ROUTE_ADJUST',
            status='pending'
        )
        db.session.add(token_request)
        db.session.commit()
        
        return user.id, admin.id, token_request.id

def test_adjust_route_success():
    """Teste: Rota de ajuste com sucesso"""
    print("\n=== Teste 1: Rota de ajuste com sucesso ===")
    
    user_id, admin_id, request_id = setup_test_data()
    
    # Desabilitar CSRF e timeout de sessão para testes
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Fazer login como admin
        with client.session_transaction() as sess:
            sess['admin_id'] = admin_id
            sess['admin_email'] = 'admin_route_test@example.com'
            sess['last_activity'] = datetime.now().timestamp()  # Evitar timeout
        
        # Fazer requisição de ajuste
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 50.00,
                'adjustment_reason': 'Teste de ajuste via rota'
            },
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # Verificações
        assert response.status_code == 200, f"Status code incorreto: {response.status_code}"
        
        data = response.get_json()
        assert data['success'] == True, "Resposta deveria indicar sucesso"
        assert data['old_amount'] == 100.00, f"Valor antigo incorreto: {data['old_amount']}"
        assert data['new_amount'] == 50.00, f"Valor novo incorreto: {data['new_amount']}"
        assert data['request_id'] == request_id, f"Request ID incorreto: {data['request_id']}"
        
        print("✓ Teste passou: Rota de ajuste funcionando corretamente")

def test_adjust_route_authentication():
    """Teste: Rota sem autenticação"""
    print("\n=== Teste 2: Rota sem autenticação (deve falhar) ===")
    
    user_id, admin_id, request_id = setup_test_data()
    
    # Desabilitar CSRF para testes
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Fazer requisição sem login
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 50.00,
                'adjustment_reason': 'Teste sem auth'
            },
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        
        # Verificações - deve redirecionar para login (302) ou retornar 401
        assert response.status_code in [302, 401], f"Status code incorreto: {response.status_code}"
        
        print("✓ Teste passou: Rota bloqueada sem autenticação")

def test_adjust_route_validation():
    """Teste: Validações da rota"""
    print("\n=== Teste 3: Validações da rota ===")
    
    user_id, admin_id, request_id = setup_test_data()
    
    # Desabilitar CSRF para testes
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Fazer login como admin
        with client.session_transaction() as sess:
            sess['admin_id'] = admin_id
            sess['admin_email'] = 'admin_route_test@example.com'
            sess['last_activity'] = datetime.now().timestamp()  # Evitar timeout
        
        # Teste 3.1: Valor inválido (zero)
        print("\n  3.1: Testando valor zero...")
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 0,
                'adjustment_reason': 'Teste valor zero'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400, f"Status code incorreto: {response.status_code}"
        data = response.get_json()
        assert data['success'] == False, "Deveria falhar"
        assert 'maior que zero' in data['error'].lower(), f"Mensagem incorreta: {data['error']}"
        print("  ✓ Valor zero bloqueado")
        
        # Teste 3.2: Valor igual ao atual
        print("\n  3.2: Testando valor igual ao atual...")
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 100.00,
                'adjustment_reason': 'Teste valor igual'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400, f"Status code incorreto: {response.status_code}"
        data = response.get_json()
        assert data['success'] == False, "Deveria falhar"
        assert 'diferente' in data['error'].lower(), f"Mensagem incorreta: {data['error']}"
        print("  ✓ Valor igual bloqueado")
        
        # Teste 3.3: Justificativa muito longa
        print("\n  3.3: Testando justificativa muito longa...")
        long_reason = 'A' * 501  # 501 caracteres
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 50.00,
                'adjustment_reason': long_reason
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400, f"Status code incorreto: {response.status_code}"
        data = response.get_json()
        assert data['success'] == False, "Deveria falhar"
        assert '500 caracteres' in data['error'], f"Mensagem incorreta: {data['error']}"
        print("  ✓ Justificativa longa bloqueada")
        
        # Teste 3.4: Solicitação não encontrada
        print("\n  3.4: Testando solicitação inexistente...")
        response = client.post(
            '/admin/tokens/solicitacoes/999999/ajustar',
            json={
                'new_amount': 50.00,
                'adjustment_reason': 'Teste não encontrado'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 404, f"Status code incorreto: {response.status_code}"
        data = response.get_json()
        assert data['success'] == False, "Deveria falhar"
        assert 'não encontrada' in data['error'].lower(), f"Mensagem incorreta: {data['error']}"
        print("  ✓ Solicitação inexistente bloqueada")
        
        print("\n✓ Teste passou: Todas as validações funcionando")

def test_adjust_route_invalid_status():
    """Teste: Tentar ajustar solicitação não-pendente"""
    print("\n=== Teste 4: Ajustar solicitação aprovada (deve falhar) ===")
    
    user_id, admin_id, request_id = setup_test_data()
    
    with app.app_context():
        # Aprovar a solicitação
        token_request = db.session.get(TokenRequest, request_id)
        token_request.status = 'approved'
        db.session.commit()
    
    # Desabilitar CSRF para testes
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # Fazer login como admin
        with client.session_transaction() as sess:
            sess['admin_id'] = admin_id
            sess['admin_email'] = 'admin_route_test@example.com'
            sess['last_activity'] = datetime.now().timestamp()  # Evitar timeout
        
        # Tentar ajustar
        response = client.post(
            f'/admin/tokens/solicitacoes/{request_id}/ajustar',
            json={
                'new_amount': 50.00,
                'adjustment_reason': 'Teste status inválido'
            },
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # Verificações
        assert response.status_code == 400, f"Status code incorreto: {response.status_code}"
        data = response.get_json()
        assert data['success'] == False, "Deveria falhar"
        assert 'pendentes' in data['error'].lower(), f"Mensagem incorreta: {data['error']}"
        
        print("✓ Teste passou: Ajuste bloqueado para solicitação aprovada")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTES DE INTEGRAÇÃO - ROTA DE AJUSTE DE QUANTIDADE")
    print("=" * 60)
    
    try:
        test_adjust_route_success()
        test_adjust_route_authentication()
        test_adjust_route_validation()
        test_adjust_route_invalid_status()
        
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
