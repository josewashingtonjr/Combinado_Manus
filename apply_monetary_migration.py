#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para Aplicar Migração Monetária
Aplica a migração Float → Numeric(18,2) no banco de dados SQLite
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def backup_database(db_path):
    """Cria backup do banco antes da migração"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path

def apply_migration(db_path):
    """Aplica a migração Float → Numeric(18,2)"""
    print(f"Aplicando migração em: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Iniciar transação
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Criar tabelas de backup
        print("1. Criando backups das tabelas...")
        
        cursor.execute("CREATE TABLE wallets_backup AS SELECT * FROM wallets;")
        cursor.execute("CREATE TABLE transactions_backup AS SELECT * FROM transactions;")
        cursor.execute("CREATE TABLE orders_backup AS SELECT * FROM orders;")
        cursor.execute("CREATE TABLE token_requests_backup AS SELECT * FROM token_requests;")
        
        # 2. Recriar tabela wallets
        print("2. Recriando tabela wallets...")
        cursor.execute("DROP TABLE wallets;")
        cursor.execute("""
            CREATE TABLE wallets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
                escrow_balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                CHECK (balance >= 0),
                CHECK (escrow_balance >= 0)
            );
        """)
        
        # 3. Recriar tabela transactions
        print("3. Recriando tabela transactions...")
        cursor.execute("DROP TABLE transactions;")
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type VARCHAR(50) NOT NULL,
                amount NUMERIC(18,2) NOT NULL,
                description VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                order_id INTEGER,
                related_user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (related_user_id) REFERENCES users (id),
                CHECK (amount != 0)
            );
        """)
        
        # 4. Recriar tabela orders
        print("4. Recriando tabela orders...")
        cursor.execute("DROP TABLE orders;")
        cursor.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                client_id INTEGER NOT NULL,
                provider_id INTEGER,
                title VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                value NUMERIC(18,2) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'disponivel',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accepted_at DATETIME,
                completed_at DATETIME,
                invite_id INTEGER,
                dispute_reason TEXT,
                dispute_opened_by INTEGER,
                dispute_opened_at DATETIME,
                dispute_resolved_at DATETIME,
                dispute_resolution TEXT,
                FOREIGN KEY (client_id) REFERENCES users (id),
                FOREIGN KEY (provider_id) REFERENCES users (id),
                FOREIGN KEY (invite_id) REFERENCES invites (id),
                FOREIGN KEY (dispute_opened_by) REFERENCES users (id),
                CHECK (value > 0)
            );
        """)
        
        # 5. Recriar tabela token_requests
        print("5. Recriando tabela token_requests...")
        cursor.execute("DROP TABLE token_requests;")
        cursor.execute("""
            CREATE TABLE token_requests (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount NUMERIC(18,2) NOT NULL,
                description TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                processed_by INTEGER,
                admin_notes TEXT,
                payment_method VARCHAR(50) DEFAULT 'pix',
                receipt_filename VARCHAR(255),
                receipt_original_name VARCHAR(255),
                receipt_uploaded_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (processed_by) REFERENCES admin_users (id),
                CHECK (amount > 0)
            );
        """)
        
        # 6. Restaurar dados (excluindo transações inválidas)
        print("6. Restaurando dados...")
        
        cursor.execute("INSERT INTO wallets SELECT * FROM wallets_backup;")
        cursor.execute("INSERT INTO transactions SELECT * FROM transactions_backup WHERE amount != 0;")
        cursor.execute("INSERT INTO orders SELECT * FROM orders_backup;")
        cursor.execute("INSERT INTO token_requests SELECT * FROM token_requests_backup;")
        
        # 7. Criar índices
        print("7. Criando índices...")
        cursor.execute("CREATE INDEX idx_wallets_user_id ON wallets(user_id);")
        cursor.execute("CREATE INDEX idx_transactions_user_id_created ON transactions(user_id, created_at DESC);")
        cursor.execute("CREATE INDEX idx_transactions_order_id ON transactions(order_id);")
        cursor.execute("CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);")
        cursor.execute("CREATE INDEX idx_token_requests_user_status ON token_requests(user_id, status);")
        
        # 8. Remover tabelas de backup
        print("8. Limpando tabelas de backup...")
        cursor.execute("DROP TABLE wallets_backup;")
        cursor.execute("DROP TABLE transactions_backup;")
        cursor.execute("DROP TABLE orders_backup;")
        cursor.execute("DROP TABLE token_requests_backup;")
        
        # Confirmar transação
        cursor.execute("COMMIT;")
        print("✅ Migração aplicada com sucesso!")
        
        # 9. Verificar integridade
        print("9. Verificando integridade...")
        
        # Verificar estrutura das tabelas
        cursor.execute("PRAGMA table_info(wallets);")
        wallets_info = cursor.fetchall()
        print(f"   • Estrutura wallets: {len(wallets_info)} colunas")
        
        cursor.execute("PRAGMA table_info(transactions);")
        transactions_info = cursor.fetchall()
        print(f"   • Estrutura transactions: {len(transactions_info)} colunas")
        
        # Verificar contagem de registros
        cursor.execute("SELECT COUNT(*) FROM wallets;")
        wallets_count = cursor.fetchone()[0]
        print(f"   • Registros wallets: {wallets_count}")
        
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        transactions_count = cursor.fetchone()[0]
        print(f"   • Registros transactions: {transactions_count}")
        
        cursor.execute("SELECT COUNT(*) FROM orders;")
        orders_count = cursor.fetchone()[0]
        print(f"   • Registros orders: {orders_count}")
        
        cursor.execute("SELECT COUNT(*) FROM token_requests;")
        token_requests_count = cursor.fetchone()[0]
        print(f"   • Registros token_requests: {token_requests_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {str(e)}")
        cursor.execute("ROLLBACK;")
        return False
        
    finally:
        conn.close()

def main():
    """Função principal"""
    print("=" * 80)
    print("APLICAÇÃO DA MIGRAÇÃO MONETÁRIA")
    print("Sistema de Correções Críticas - Tarefa 1")
    print("=" * 80)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Determinar qual banco usar
    db_paths = [
        "instance/test_combinado.db",
        "sistema_combinado.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Nenhum banco de dados encontrado!")
        return 1
    
    print(f"Usando banco: {db_path}")
    print()
    
    # Criar backup
    backup_path = backup_database(db_path)
    print()
    
    # Aplicar migração
    success = apply_migration(db_path)
    
    if success:
        print()
        print("=" * 80)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   • Banco migrado: {db_path}")
        print(f"   • Backup disponível: {backup_path}")
        print("   • Todos os campos monetários agora usam NUMERIC(18,2)")
        print("   • Constraints de integridade aplicadas")
        print("   • Transações inválidas removidas")
        print("=" * 80)
        return 0
    else:
        print()
        print("=" * 80)
        print("❌ MIGRAÇÃO FALHOU!")
        print(f"   • Backup disponível: {backup_path}")
        print("   • Restaure o backup se necessário")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)