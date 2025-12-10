#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste de Constraints de Integridade Financeira
Sistema de Correções Críticas - Tarefa 2

Este script testa se todas as constraints de integridade financeira
estão funcionando corretamente no banco de dados.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Wallet, Transaction, Order, TokenRequest
from sqlalchemy.exc import IntegrityError

def test_wallet_negative_balance_constraint():
    """Testa se a constraint impede saldo negativo em wallets"""
    with app.app_context():
        try:
            # Tentar criar wallet com saldo negativo
            db.session.execute(
                db.text("INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (999, -10.00, 0.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu saldo negativo"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu saldo negativo"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_wallet_negative_escrow_constraint():
    """Testa se a constraint impede escrow negativo em wallets"""
    with app.app_context():
        try:
            # Tentar criar wallet com escrow negativo
            db.session.execute(
                db.text("INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (998, 0.00, -5.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu escrow negativo"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu escrow negativo"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_transaction_zero_amount_constraint():
    """Testa se a constraint impede transações com valor zero"""
    with app.app_context():
        try:
            # Tentar criar transação com valor zero
            db.session.execute(
                db.text("INSERT INTO transactions (user_id, type, amount, description) VALUES (999, 'teste', 0.00, 'Teste constraint')")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu transação com valor zero"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu transação com valor zero"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_order_negative_value_constraint():
    """Testa se a constraint impede ordens com valor negativo"""
    with app.app_context():
        try:
            # Tentar criar ordem com valor negativo
            db.session.execute(
                db.text("INSERT INTO orders (client_id, title, description, value) VALUES (999, 'Teste', 'Teste constraint', -50.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu ordem com valor negativo"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu ordem com valor negativo"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_order_zero_value_constraint():
    """Testa se a constraint impede ordens com valor zero"""
    with app.app_context():
        try:
            # Tentar criar ordem com valor zero
            db.session.execute(
                db.text("INSERT INTO orders (client_id, title, description, value) VALUES (998, 'Teste', 'Teste constraint', 0.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu ordem com valor zero"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu ordem com valor zero"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_token_request_negative_amount_constraint():
    """Testa se a constraint impede solicitações de token com valor negativo"""
    with app.app_context():
        try:
            # Tentar criar solicitação com valor negativo
            db.session.execute(
                db.text("INSERT INTO token_requests (user_id, amount) VALUES (999, -100.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu solicitação com valor negativo"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu solicitação com valor negativo"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_token_request_zero_amount_constraint():
    """Testa se a constraint impede solicitações de token com valor zero"""
    with app.app_context():
        try:
            # Tentar criar solicitação com valor zero
            db.session.execute(
                db.text("INSERT INTO token_requests (user_id, amount) VALUES (998, 0.00)")
            )
            db.session.commit()
            return False, "Constraint falhou: permitiu solicitação com valor zero"
        except IntegrityError:
            db.session.rollback()
            return True, "Constraint funcionando: impediu solicitação com valor zero"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {e}"

def test_indexes_exist():
    """Verifica se todos os índices necessários foram criados"""
    with app.app_context():
        try:
            # Verificar índices das tabelas financeiras
            result = db.session.execute(
                db.text("""
                SELECT name, tbl_name 
                FROM sqlite_master 
                WHERE type = 'index' 
                AND tbl_name IN ('wallets', 'transactions', 'orders', 'token_requests')
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
                """)
            ).fetchall()
            
            expected_indexes = [
                'idx_wallets_user_id',
                'idx_wallets_balance', 
                'idx_wallets_escrow_balance',
                'idx_wallets_updated_at',
                'idx_transactions_user_id_created',
                'idx_transactions_order_id',
                'idx_transactions_type_created',
                'idx_transactions_amount_created',
                'idx_transactions_related_user',
                'idx_orders_status_created',
                'idx_orders_client_status',
                'idx_orders_provider_status',
                'idx_orders_value_created',
                'idx_token_requests_user_status',
                'idx_token_requests_status_created',
                'idx_token_requests_processed_by',
                'idx_token_requests_amount_status'
            ]
            
            existing_indexes = [row[0] for row in result]
            missing_indexes = [idx for idx in expected_indexes if idx not in existing_indexes]
            
            if missing_indexes:
                return False, f"Índices faltando: {missing_indexes}"
            else:
                return True, f"Todos os {len(expected_indexes)} índices estão presentes"
                
        except Exception as e:
            return False, f"Erro ao verificar índices: {e}"

def run_all_tests():
    """Executa todos os testes de integridade financeira"""
    print("=" * 80)
    print("TESTE DE CONSTRAINTS DE INTEGRIDADE FINANCEIRA")
    print("Sistema de Correções Críticas - Tarefa 2")
    print("=" * 80)
    
    tests = [
        ("Constraint: Saldo negativo em wallets", test_wallet_negative_balance_constraint),
        ("Constraint: Escrow negativo em wallets", test_wallet_negative_escrow_constraint),
        ("Constraint: Transação com valor zero", test_transaction_zero_amount_constraint),
        ("Constraint: Ordem com valor negativo", test_order_negative_value_constraint),
        ("Constraint: Ordem com valor zero", test_order_zero_value_constraint),
        ("Constraint: Token request com valor negativo", test_token_request_negative_amount_constraint),
        ("Constraint: Token request com valor zero", test_token_request_zero_amount_constraint),
        ("Verificação: Índices de performance", test_indexes_exist),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"{status} | {test_name}")
            print(f"         {message}")
            
            if success:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ ERRO  | {test_name}")
            print(f"         Erro durante execução: {e}")
            failed += 1
        
        print()
    
    print("=" * 80)
    print(f"RESULTADO FINAL: {passed} testes passaram, {failed} falharam")
    print("=" * 80)
    
    if failed == 0:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("As constraints de integridade financeira estão funcionando corretamente.")
        return True
    else:
        print("⚠️  ALGUNS TESTES FALHARAM!")
        print("Verifique as constraints que não estão funcionando adequadamente.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)