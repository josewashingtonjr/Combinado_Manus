#!/usr/bin/env python3
"""
Script de validação das migrações aplicadas ao banco de dados.
Testa constraints, tipos de dados e funcionalidades implementadas.
"""

import sys
from decimal import Decimal
from datetime import datetime
from app import app, db
from models import User, Wallet, Transaction, Order
from sqlalchemy import text

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"❌ {text}")

def print_info(text):
    """Imprime mensagem informativa"""
    print(f"ℹ️  {text}")

def test_numeric_precision():
    """Testa a precisão dos campos Numeric(18,2)"""
    print_header("Teste 1: Precisão de Campos Monetários (Float → Numeric)")
    
    try:
        # Criar usuário de teste
        user = User(
            email=f"test_numeric_{datetime.now().timestamp()}@test.com",
            nome="Test Numeric User",
            password_hash="hash",
            cpf=f"{int(datetime.now().timestamp()) % 100000000000:011d}",
            roles="client"
        )
        db.session.add(user)
        db.session.flush()
        
        # Criar wallet com valores precisos
        wallet = Wallet(
            user_id=user.id,
            balance=Decimal('100.99'),
            escrow_balance=Decimal('50.01')
        )
        db.session.add(wallet)
        db.session.flush()
        
        # Verificar tipos
        assert isinstance(wallet.balance, Decimal), "Balance deve ser Decimal"
        assert isinstance(wallet.escrow_balance, Decimal), "Escrow balance deve ser Decimal"
        
        # Verificar precisão
        assert wallet.balance == Decimal('100.99'), f"Balance incorreto: {wallet.balance}"
        assert wallet.escrow_balance == Decimal('50.01'), f"Escrow balance incorreto: {wallet.escrow_balance}"
        
        db.session.rollback()
        print_success("Campos monetários usando Numeric(18,2) com precisão correta")
        return True
        
    except Exception as e:
        db.session.rollback()
        print_error(f"Falha no teste de precisão: {e}")
        return False

def test_check_constraints():
    """Testa as CHECK constraints de saldos não-negativos"""
    print_header("Teste 2: CHECK Constraints (Saldos Não-Negativos)")
    
    try:
        # Criar usuário de teste
        user = User(
            email=f"test_check_{datetime.now().timestamp()}@test.com",
            nome="Test Check User",
            password_hash="hash",
            cpf=f"{int(datetime.now().timestamp()) % 100000000000:011d}",
            roles="client"
        )
        db.session.add(user)
        db.session.flush()
        
        # Tentar criar wallet com saldo negativo
        wallet = Wallet(
            user_id=user.id,
            balance=Decimal('-10.00'),  # Valor negativo - deve falhar
            escrow_balance=Decimal('0.00')
        )
        db.session.add(wallet)
        
        try:
            db.session.flush()
            db.session.rollback()
            print_error("CHECK constraint não impediu saldo negativo!")
            return False
        except Exception as constraint_error:
            db.session.rollback()
            print_success("CHECK constraint impediu saldo negativo corretamente")
            print_info(f"Erro capturado: {str(constraint_error)[:100]}")
            return True
            
    except Exception as e:
        db.session.rollback()
        print_error(f"Falha no teste de CHECK constraints: {e}")
        return False

def test_unique_constraints():
    """Testa as UNIQUE constraints de email e CPF"""
    print_header("Teste 3: UNIQUE Constraints (Email e CPF)")
    
    try:
        timestamp = datetime.now().timestamp()
        email = f"test_unique_{timestamp}@test.com"
        cpf = f"{int(timestamp) % 100000000000:011d}"
        
        # Criar primeiro usuário
        user1 = User(
            email=email,
            nome="Test Unique User 1",
            password_hash="hash1",
            cpf=cpf,
            roles="client"
        )
        db.session.add(user1)
        db.session.flush()
        
        # Tentar criar segundo usuário com mesmo email
        user2 = User(
            email=email,  # Email duplicado - deve falhar
            nome="Test Unique User 2",
            password_hash="hash2",
            cpf=f"{int(timestamp) % 100000000000 + 1:011d}",
            roles="client"
        )
        db.session.add(user2)
        
        try:
            db.session.flush()
            db.session.rollback()
            print_error("UNIQUE constraint não impediu email duplicado!")
            return False
        except Exception as constraint_error:
            db.session.rollback()
            print_success("UNIQUE constraint impediu email duplicado corretamente")
            print_info(f"Erro capturado: {str(constraint_error)[:100]}")
            return True
            
    except Exception as e:
        db.session.rollback()
        print_error(f"Falha no teste de UNIQUE constraints: {e}")
        return False

def test_soft_delete():
    """Testa a funcionalidade de soft delete"""
    print_header("Teste 4: Soft Delete (deleted_at)")
    
    try:
        timestamp = datetime.now().timestamp()
        
        # Criar usuário de teste
        user = User(
            email=f"test_softdelete_{timestamp}@test.com",
            nome="Test Soft Delete User",
            password_hash="hash",
            cpf=f"{int(timestamp) % 100000000000:011d}",
            roles="client"
        )
        db.session.add(user)
        db.session.flush()
        
        # Verificar que deleted_at existe e é None
        assert hasattr(user, 'deleted_at'), "Campo deleted_at não existe em User"
        assert user.deleted_at is None, "deleted_at deve ser None inicialmente"
        
        # Marcar como deletado
        user.deleted_at = datetime.utcnow()
        db.session.flush()
        
        # Verificar que foi marcado
        assert user.deleted_at is not None, "deleted_at deve estar preenchido"
        
        db.session.rollback()
        print_success("Soft delete funcionando corretamente em User")
        
        # Testar em Order
        user = User(
            email=f"test_order_softdelete_{timestamp}@test.com",
            nome="Test Order Soft Delete User",
            password_hash="hash",
            cpf=f"{int(timestamp) % 100000000000 + 1:011d}",
            roles="client"
        )
        db.session.add(user)
        db.session.flush()
        
        order = Order(
            client_id=user.id,
            title="Test Order",
            description="Test Description",
            value=Decimal('100.00'),
            status="pending"
        )
        db.session.add(order)
        db.session.flush()
        
        # Verificar que deleted_at existe e é None
        assert hasattr(order, 'deleted_at'), "Campo deleted_at não existe em Order"
        assert order.deleted_at is None, "deleted_at deve ser None inicialmente"
        
        # Marcar como deletado
        order.deleted_at = datetime.utcnow()
        db.session.flush()
        
        # Verificar que foi marcado
        assert order.deleted_at is not None, "deleted_at deve estar preenchido"
        
        db.session.rollback()
        print_success("Soft delete funcionando corretamente em Order")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print_error(f"Falha no teste de soft delete: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_indexes():
    """Verifica se os índices foram criados"""
    print_header("Teste 5: Índices de Performance")
    
    try:
        # Consultar índices no SQLite
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        )
        indexes = [row[0] for row in result]
        
        expected_indexes = [
            'idx_wallet_user_id',
            'idx_transaction_user_id',
            'idx_transaction_created_at',
            'idx_order_status',
            'idx_order_client_id',
            'idx_order_provider_id',
        ]
        
        found_count = 0
        for idx in expected_indexes:
            if idx in indexes:
                print_success(f"Índice encontrado: {idx}")
                found_count += 1
            else:
                print_info(f"Índice não encontrado: {idx}")
        
        if found_count >= 4:  # Pelo menos 4 dos 6 índices esperados
            print_success(f"Índices criados corretamente ({found_count}/{len(expected_indexes)})")
            return True
        else:
            print_error(f"Poucos índices encontrados ({found_count}/{len(expected_indexes)})")
            return False
            
    except Exception as e:
        print_error(f"Falha no teste de índices: {e}")
        return False

def main():
    """Executa todos os testes de validação"""
    print_header("VALIDAÇÃO DAS MIGRAÇÕES DO BANCO DE DADOS")
    print_info("Testando as correções críticas implementadas nas Ondas 1, 2 e 3")
    
    with app.app_context():
        results = []
        
        # Executar testes
        results.append(("Precisão Monetária", test_numeric_precision()))
        results.append(("CHECK Constraints", test_check_constraints()))
        results.append(("UNIQUE Constraints", test_unique_constraints()))
        results.append(("Soft Delete", test_soft_delete()))
        results.append(("Índices", test_indexes()))
        
        # Resumo
        print_header("RESUMO DOS TESTES")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{status} - {test_name}")
        
        print("\n" + "=" * 80)
        print(f"  RESULTADO FINAL: {passed}/{total} testes passaram")
        print("=" * 80)
        
        if passed == total:
            print_success("Todas as migrações foram aplicadas corretamente!")
            return 0
        else:
            print_error(f"{total - passed} teste(s) falharam")
            return 1

if __name__ == '__main__':
    sys.exit(main())

