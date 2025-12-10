#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para aplicar migration de índices de performance na tabela orders
Sistema de Gestão de Ordens Completo - Tarefa 32
"""

import sqlite3
import os
from datetime import datetime

def apply_migration(db_path=None):
    """Aplica a migration de índices de performance"""
    
    # Caminho do banco de dados
    if db_path is None:
        # Tentar encontrar o banco de dados correto
        possible_paths = [
            'instance/test_combinado.db',
            'instance/sistema_combinado.db'
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                # Verificar se tem a tabela orders
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
                    if cursor.fetchone():
                        db_path = path
                        conn.close()
                        break
                    conn.close()
                except:
                    pass
        
        if db_path is None:
            print("❌ Erro: Nenhum banco de dados com tabela 'orders' encontrado")
            print("   Bancos verificados:")
            for path in possible_paths:
                print(f"   - {path}")
            return False
    
    migration_file = 'migrations/add_order_performance_indexes.sql'
    
    if not os.path.exists(db_path):
        print(f"❌ Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    if not os.path.exists(migration_file):
        print(f"❌ Erro: Arquivo de migration não encontrado em {migration_file}")
        return False
    
    print("=" * 80)
    print("APLICAÇÃO DE MIGRATION - ÍNDICES DE PERFORMANCE PARA ORDERS")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Banco de dados: {db_path}")
    print(f"Migration: {migration_file}")
    print("=" * 80)
    print()
    
    try:
        # Conectar ao banco de dados
        print("📊 Conectando ao banco de dados...")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Ler o arquivo de migration
        print("📄 Lendo arquivo de migration...")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Verificar índices existentes antes da migration
        print("\n📋 Verificando índices existentes na tabela orders...")
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type = 'index' 
            AND tbl_name = 'orders'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        existing_indexes = cursor.fetchall()
        print(f"   Índices existentes: {len(existing_indexes)}")
        for idx in existing_indexes:
            print(f"   - {idx['name']}")
        
        # Executar a migration
        print("\n🔧 Aplicando migration...")
        cursor.executescript(migration_sql)
        
        # Verificar índices após a migration
        print("\n✅ Verificando índices após migration...")
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type = 'index' 
            AND tbl_name = 'orders'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        new_indexes = cursor.fetchall()
        print(f"   Total de índices: {len(new_indexes)}")
        
        # Listar novos índices criados
        new_index_names = [idx['name'] for idx in new_indexes]
        old_index_names = [idx['name'] for idx in existing_indexes]
        created_indexes = [name for name in new_index_names if name not in old_index_names]
        
        if created_indexes:
            print(f"\n🆕 Novos índices criados ({len(created_indexes)}):")
            for idx_name in created_indexes:
                print(f"   ✓ {idx_name}")
        else:
            print("\n   ℹ️  Todos os índices já existiam (nenhum novo índice criado)")
        
        # Mostrar todos os índices atuais
        print(f"\n📊 Índices atuais na tabela orders ({len(new_indexes)}):")
        for idx in new_indexes:
            print(f"   - {idx['name']}")
        
        # Estatísticas da tabela
        print("\n📈 Estatísticas da tabela orders:")
        cursor.execute("SELECT COUNT(*) as total FROM orders")
        total = cursor.fetchone()['total']
        print(f"   Total de ordens: {total}")
        
        cursor.execute("""
            SELECT status, COUNT(*) as quantidade 
            FROM orders 
            GROUP BY status 
            ORDER BY quantidade DESC
        """)
        status_dist = cursor.fetchall()
        if status_dist:
            print("   Distribuição por status:")
            for row in status_dist:
                print(f"     - {row['status']}: {row['quantidade']}")
        
        # Commit das alterações
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION APLICADA COM SUCESSO!")
        print("=" * 80)
        print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Erro ao aplicar migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()
            print("🔌 Conexão com banco de dados fechada.")

def verify_indexes(db_path=None):
    """Verifica se os índices foram criados corretamente"""
    
    if db_path is None:
        # Tentar encontrar o banco de dados correto
        possible_paths = [
            'instance/test_combinado.db',
            'instance/sistema_combinado.db'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
                    if cursor.fetchone():
                        db_path = path
                        conn.close()
                        break
                    conn.close()
                except:
                    pass
        
        if db_path is None:
            db_path = 'instance/sistema_combinado.db'
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE ÍNDICES")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Índices esperados
        expected_indexes = [
            'idx_orders_status',
            'idx_orders_confirmation_deadline',
            'idx_orders_client_id',
            'idx_orders_provider_id',
            'idx_orders_created_at_desc',
            'idx_orders_client_status',
            'idx_orders_provider_status',
            'idx_orders_status_confirmation_deadline'
        ]
        
        # Verificar cada índice
        print("\n📋 Verificando índices esperados:")
        all_exist = True
        
        for idx_name in expected_indexes:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type = 'index' 
                AND name = ?
            """, (idx_name,))
            
            result = cursor.fetchone()
            if result:
                print(f"   ✓ {idx_name} - OK")
            else:
                print(f"   ✗ {idx_name} - NÃO ENCONTRADO")
                all_exist = False
        
        if all_exist:
            print("\n✅ Todos os índices esperados foram criados com sucesso!")
        else:
            print("\n⚠️  Alguns índices não foram encontrados.")
        
        conn.close()
        return all_exist
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar índices: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    print("\n🚀 Iniciando aplicação de migration de índices...\n")
    
    # Permitir especificar o banco via argumento
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = apply_migration(db_path)
    
    if success:
        print("\n🔍 Executando verificação final...")
        verify_indexes(db_path)
        print("\n✅ Processo concluído com sucesso!")
    else:
        print("\n❌ Processo falhou. Verifique os erros acima.")
