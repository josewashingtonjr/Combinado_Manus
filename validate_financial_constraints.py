#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validação de Constraints de Integridade Financeira
Sistema de Correções Críticas - Tarefa 2

Este script valida se todas as constraints de integridade financeira
estão funcionando corretamente no banco de dados.
"""

import sqlite3
import sys
import os

def test_constraints():
    """Testa todas as constraints de integridade financeira"""
    
    db_path = "instance/test_combinado.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    print("=" * 80)
    print("VALIDAÇÃO DE CONSTRAINTS DE INTEGRIDADE FINANCEIRA")
    print("Sistema de Correções Críticas - Tarefa 2")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tests_passed = 0
    tests_total = 0
    
    # Teste 1: Constraint de saldo negativo em wallets
    tests_total += 1
    try:
        cursor.execute("INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (999, -10.00, 0.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de saldo negativo em wallets")
        print("         Permitiu inserir saldo negativo")
    except sqlite3.IntegrityError as e:
        if "balance >= 0" in str(e):
            print("✅ PASSOU | Constraint de saldo negativo em wallets")
            print("         Impediu corretamente saldo negativo")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de saldo negativo em wallets - Erro: {e}")
    
    # Teste 2: Constraint de escrow negativo em wallets
    tests_total += 1
    try:
        cursor.execute("INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (998, 0.00, -5.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de escrow negativo em wallets")
        print("         Permitiu inserir escrow negativo")
    except sqlite3.IntegrityError as e:
        if "escrow_balance >= 0" in str(e):
            print("✅ PASSOU | Constraint de escrow negativo em wallets")
            print("         Impediu corretamente escrow negativo")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de escrow negativo em wallets - Erro: {e}")
    
    # Teste 3: Constraint de transação com valor zero
    tests_total += 1
    try:
        cursor.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (997, 'teste', 0.00, 'Teste constraint');")
        conn.commit()
        print("❌ FALHOU | Constraint de transação com valor zero")
        print("         Permitiu inserir transação com valor zero")
    except sqlite3.IntegrityError as e:
        if "amount != 0" in str(e):
            print("✅ PASSOU | Constraint de transação com valor zero")
            print("         Impediu corretamente transação com valor zero")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de transação com valor zero - Erro: {e}")
    
    # Teste 4: Constraint de ordem com valor negativo
    tests_total += 1
    try:
        cursor.execute("INSERT INTO orders (client_id, title, description, value) VALUES (996, 'Teste', 'Teste constraint', -50.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de ordem com valor negativo")
        print("         Permitiu inserir ordem com valor negativo")
    except sqlite3.IntegrityError as e:
        if "value > 0" in str(e):
            print("✅ PASSOU | Constraint de ordem com valor negativo")
            print("         Impediu corretamente ordem com valor negativo")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de ordem com valor negativo - Erro: {e}")
    
    # Teste 5: Constraint de ordem com valor zero
    tests_total += 1
    try:
        cursor.execute("INSERT INTO orders (client_id, title, description, value) VALUES (995, 'Teste', 'Teste constraint', 0.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de ordem com valor zero")
        print("         Permitiu inserir ordem com valor zero")
    except sqlite3.IntegrityError as e:
        if "value > 0" in str(e):
            print("✅ PASSOU | Constraint de ordem com valor zero")
            print("         Impediu corretamente ordem com valor zero")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de ordem com valor zero - Erro: {e}")
    
    # Teste 6: Constraint de token request com valor negativo
    tests_total += 1
    try:
        cursor.execute("INSERT INTO token_requests (user_id, amount) VALUES (994, -100.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de token request com valor negativo")
        print("         Permitiu inserir token request com valor negativo")
    except sqlite3.IntegrityError as e:
        if "amount > 0" in str(e):
            print("✅ PASSOU | Constraint de token request com valor negativo")
            print("         Impediu corretamente token request com valor negativo")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de token request com valor negativo - Erro: {e}")
    
    # Teste 7: Constraint de token request com valor zero
    tests_total += 1
    try:
        cursor.execute("INSERT INTO token_requests (user_id, amount) VALUES (993, 0.00);")
        conn.commit()
        print("❌ FALHOU | Constraint de token request com valor zero")
        print("         Permitiu inserir token request com valor zero")
    except sqlite3.IntegrityError as e:
        if "amount > 0" in str(e):
            print("✅ PASSOU | Constraint de token request com valor zero")
            print("         Impediu corretamente token request com valor zero")
            tests_passed += 1
        else:
            print(f"❌ FALHOU | Constraint de token request com valor zero - Erro: {e}")
    
    print()
    
    # Teste 8: Verificar índices
    tests_total += 1
    try:
        cursor.execute("""
        SELECT name, tbl_name 
        FROM sqlite_master 
        WHERE type = 'index' 
        AND tbl_name IN ('wallets', 'transactions', 'orders', 'token_requests')
        AND name NOT LIKE 'sqlite_%'
        ORDER BY tbl_name, name
        """)
        
        indexes = cursor.fetchall()
        
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
        
        existing_indexes = [idx[0] for idx in indexes]
        missing_indexes = [idx for idx in expected_indexes if idx not in existing_indexes]
        
        if not missing_indexes:
            print("✅ PASSOU | Verificação de índices de performance")
            print(f"         Todos os {len(expected_indexes)} índices estão presentes")
            tests_passed += 1
        else:
            print("❌ FALHOU | Verificação de índices de performance")
            print(f"         Índices faltando: {missing_indexes}")
            
    except Exception as e:
        print(f"❌ FALHOU | Verificação de índices de performance - Erro: {e}")
    
    # Limpeza: remover registros de teste que podem ter sido inseridos
    try:
        cursor.execute("DELETE FROM wallets WHERE user_id >= 993;")
        cursor.execute("DELETE FROM transactions WHERE user_id >= 993;")
        cursor.execute("DELETE FROM orders WHERE client_id >= 993;")
        cursor.execute("DELETE FROM token_requests WHERE user_id >= 993;")
        conn.commit()
    except:
        pass  # Ignorar erros de limpeza
    
    conn.close()
    
    print()
    print("=" * 80)
    print(f"RESULTADO FINAL: {tests_passed}/{tests_total} testes passaram")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("As constraints de integridade financeira estão funcionando corretamente.")
        return True
    else:
        print("⚠️  ALGUNS TESTES FALHARAM!")
        print("Verifique as constraints que não estão funcionando adequadamente.")
        return False

if __name__ == "__main__":
    success = test_constraints()
    sys.exit(0 if success else 1)