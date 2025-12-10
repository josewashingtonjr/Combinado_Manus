#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para a funcionalidade de ajuste de quantidade em solicitações de tokens
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, AdminUser, TokenRequest
from services.admin_service import AdminService
from decimal import Decimal
from datetime import datetime

def setup_test_data():
    """Configura dados de teste e retorna IDs"""
    # Limpar dados de teste anteriores
    TokenRequest.query.filter_by(description='TEST_ADJUST').delete()
    db.session.commit()
    
    # Criar usuário de teste se não existir
    user = User.query.filter_by(email='test_adjust@example.com').first()
    if not user:
        user = User(
            nome='Usuário Teste Ajuste',
            email='test_adjust@example.com',
            cpf='12345678901',
            phone='11999999999',
            roles='cliente',
            active=True
        )
        user.set_password('senha123')
        db.session.add(user)
        db.session.commit()
    
    # Criar admin de teste se não existir
    admin = AdminUser.query.filter_by(email='admin_test@example.com').first()
    if not admin:
        admin = AdminUser(
            email='admin_test@example.com',
            papel='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Criar solicitação de teste pendente
    token_request = TokenRequest(
        user_id=user.id,
        amount=Decimal('100.00'),
        description='TEST_ADJUST',
        status='pending'
    )
    db.session.add(token_request)
    db.session.commit()
    
    return user.id, admin.id, token_request.id

def test_adjust_token_request_amount_success():
    """Teste: Ajuste válido de quantidade"""
    print("\n=== Teste 1: Ajuste válido de quantidade ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Ajustar quantidade
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('50.00'),
            admin_id=admin_id,
            reason='Comprovante mostra pagamento de apenas R$ 50,00'
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == True, "Ajuste deveria ter sucesso"
        assert result['old_amount'] == 100.00, f"Valor antigo incorreto: {result['old_amount']}"
        assert result['new_amount'] == 50.00, f"Valor novo incorreto: {result['new_amount']}"
        
        # Verificar no banco
        token_request = TokenRequest.query.get(request_id)
        assert token_request.amount == Decimal('50.00'), f"Amount não foi atualizado: {token_request.amount}"
        assert 'Quantidade ajustada' in token_request.admin_notes, "Nota de ajuste não foi adicionada"
        assert 'R$ 100.00 para R$ 50.00' in token_request.admin_notes, "Valores não estão na nota"
        assert 'Comprovante mostra pagamento' in token_request.admin_notes, "Justificativa não está na nota"
        
        print("✓ Teste passou: Amount atualizado corretamente")
        print(f"✓ Admin notes: {token_request.admin_notes[:200]}...")

def test_adjust_token_request_amount_invalid_status():
    """Teste: Tentar ajustar solicitação não-pendente"""
    print("\n=== Teste 2: Ajustar solicitação aprovada (deve falhar) ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Aprovar a solicitação
        token_request = TokenRequest.query.get(request_id)
        token_request.status = 'approved'
        db.session.commit()
        
        # Tentar ajustar
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('50.00'),
            admin_id=admin_id
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == False, "Ajuste deveria falhar"
        assert 'pendentes' in result['error'].lower(), f"Mensagem de erro incorreta: {result['error']}"
        
        print("✓ Teste passou: Ajuste bloqueado para solicitação aprovada")

def test_adjust_token_request_amount_invalid_value():
    """Teste: Tentar ajustar com valor inválido"""
    print("\n=== Teste 3: Ajustar com valor <= 0 (deve falhar) ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Tentar ajustar com valor zero
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('0.00'),
            admin_id=admin_id
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == False, "Ajuste deveria falhar"
        assert 'maior que zero' in result['error'].lower(), f"Mensagem de erro incorreta: {result['error']}"
        
        print("✓ Teste passou: Ajuste bloqueado para valor zero")

def test_adjust_token_request_amount_same_value():
    """Teste: Tentar ajustar com valor igual ao atual"""
    print("\n=== Teste 4: Ajustar com valor igual (deve falhar) ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Tentar ajustar com o mesmo valor
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('100.00'),
            admin_id=admin_id
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == False, "Ajuste deveria falhar"
        assert 'diferente' in result['error'].lower(), f"Mensagem de erro incorreta: {result['error']}"
        
        print("✓ Teste passou: Ajuste bloqueado para valor igual")

def test_adjust_token_request_amount_preserves_notes():
    """Teste: Ajustar solicitação que já tem admin_notes"""
    print("\n=== Teste 5: Preservar notas anteriores ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Adicionar nota anterior
        token_request = TokenRequest.query.get(request_id)
        token_request.admin_notes = "Nota anterior do sistema"
        db.session.commit()
        
        # Ajustar quantidade
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('75.00'),
            admin_id=admin_id,
            reason='Ajuste após verificação'
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == True, "Ajuste deveria ter sucesso"
        
        # Verificar no banco
        token_request = TokenRequest.query.get(request_id)
        assert 'Nota anterior do sistema' in token_request.admin_notes, "Nota anterior foi perdida"
        assert 'Quantidade ajustada' in token_request.admin_notes, "Nova nota não foi adicionada"
        
        print("✓ Teste passou: Notas anteriores preservadas")
        print(f"✓ Admin notes completas:\n{token_request.admin_notes}")

def test_adjust_token_request_amount_without_reason():
    """Teste: Ajustar sem justificativa"""
    print("\n=== Teste 6: Ajustar sem justificativa ===")
    
    with app.app_context():
        user_id, admin_id, request_id = setup_test_data()
        
        # Ajustar sem justificativa
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('60.00'),
            admin_id=admin_id
        )
        
        print(f"Resultado: {result}")
        
        # Verificações
        assert result['success'] == True, "Ajuste deveria ter sucesso"
        
        # Verificar no banco
        token_request = TokenRequest.query.get(request_id)
        assert 'Quantidade ajustada' in token_request.admin_notes, "Nota de ajuste não foi adicionada"
        assert 'Justificativa:' not in token_request.admin_notes, "Não deveria ter justificativa"
        
        print("✓ Teste passou: Ajuste sem justificativa funciona")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTES DE AJUSTE DE QUANTIDADE EM SOLICITAÇÕES DE TOKENS")
    print("=" * 60)
    
    try:
        test_adjust_token_request_amount_success()
        test_adjust_token_request_amount_invalid_status()
        test_adjust_token_request_amount_invalid_value()
        test_adjust_token_request_amount_same_value()
        test_adjust_token_request_amount_preserves_notes()
        test_adjust_token_request_amount_without_reason()
        
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
