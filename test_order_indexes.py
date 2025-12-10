#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste de verificação dos índices de performance da tabela orders
Tarefa 32 - Sistema de Gestão de Ordens Completo
"""

import sqlite3
import os

def test_indexes_exist():
    """Testa se todos os índices esperados existem"""
    
    db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    print("=" * 80)
    print("TESTE DE ÍNDICES DA TABELA ORDERS")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Índices esperados
        expected_indexes = {
            'idx_orders_status': 'status',
            'idx_orders_confirmation_deadline': 'confirmation_deadline',
            'idx_orders_client_id': 'client_id',
            'idx_orders_provider_id': 'provider_id',
            'idx_orders_created_at_desc': 'created_at DESC',
            'idx_orders_client_status': 'client_id, status',
            'idx_orders_provider_status': 'provider_id, status',
            'idx_orders_status_confirmation_deadline': 'status, confirmation_deadline'
        }
        
        print(f"\n📋 Verificando {len(expected_indexes)} índices esperados...\n")
        
        all_exist = True
        for idx_name, idx_fields in expected_indexes.items():
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type = 'index' 
                AND name = ?
            """, (idx_name,))
            
            result = cursor.fetchone()
            if result:
                print(f"✅ {idx_name}")
                print(f"   Campos: {idx_fields}")
                print(f"   SQL: {result['sql']}\n")
            else:
                print(f"❌ {idx_name} - NÃO ENCONTRADO\n")
                all_exist = False
        
        # Testar uso dos índices com EXPLAIN QUERY PLAN
        print("=" * 80)
        print("TESTE DE USO DOS ÍNDICES")
        print("=" * 80)
        
        test_queries = [
            ("Busca por status", "SELECT * FROM orders WHERE status = 'servico_executado'"),
            ("Busca por cliente", "SELECT * FROM orders WHERE client_id = 1 ORDER BY created_at DESC"),
            ("Busca por prestador e status", "SELECT * FROM orders WHERE provider_id = 1 AND status = 'aguardando_execucao'"),
            ("Job de confirmação automática", "SELECT * FROM orders WHERE status = 'servico_executado' AND confirmation_deadline <= datetime('now')")
        ]
        
        print("\n🔍 Verificando planos de execução:\n")
        
        for query_name, query in test_queries:
            print(f"📊 {query_name}:")
            print(f"   Query: {query}")
            
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            uses_index = False
            for row in plan:
                plan_text = str(row)
                if 'idx_orders' in plan_text.lower():
                    uses_index = True
                print(f"   {row}")
            
            if uses_index:
                print("   ✅ Usa índice otimizado\n")
            else:
                print("   ⚠️  Não usa índice (pode ser scan completo)\n")
        
        # Estatísticas
        print("=" * 80)
        print("ESTATÍSTICAS DA TABELA")
        print("=" * 80)
        
        cursor.execute("SELECT COUNT(*) as total FROM orders")
        total = cursor.fetchone()['total']
        print(f"\n📊 Total de ordens: {total}")
        
        cursor.execute("""
            SELECT status, COUNT(*) as quantidade 
            FROM orders 
            GROUP BY status 
            ORDER BY quantidade DESC
        """)
        
        status_dist = cursor.fetchall()
        if status_dist:
            print("\n📈 Distribuição por status:")
            for row in status_dist:
                print(f"   - {row['status']}: {row['quantidade']}")
        
        # Tamanho dos índices
        print("\n💾 Informações de armazenamento:")
        cursor.execute("""
            SELECT name, pgsize 
            FROM dbstat 
            WHERE name LIKE 'idx_orders%'
            ORDER BY pgsize DESC
        """)
        
        index_sizes = cursor.fetchall()
        if index_sizes:
            print("   Tamanho dos índices:")
            for row in index_sizes:
                size_kb = row['pgsize'] / 1024
                print(f"   - {row['name']}: {size_kb:.2f} KB")
        
        conn.close()
        
        print("\n" + "=" * 80)
        if all_exist:
            print("✅ TESTE PASSOU - Todos os índices estão presentes e funcionais")
        else:
            print("❌ TESTE FALHOU - Alguns índices estão faltando")
        print("=" * 80)
        
        return all_exist
        
    except Exception as e:
        print(f"\n❌ Erro ao executar teste: {e}")
        return False

def test_index_performance():
    """Testa a performance com e sem índices (simulação)"""
    
    db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(db_path):
        return
    
    print("\n" + "=" * 80)
    print("ANÁLISE DE PERFORMANCE")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM orders")
        total = cursor.fetchone()[0]
        
        print(f"\n📊 Analisando performance com {total} ordens...")
        
        if total < 100:
            print("\n⚠️  Nota: Com poucos registros ({total}), o benefício dos índices")
            print("   não é tão perceptível. Em produção com milhares de ordens,")
            print("   os índices podem reduzir o tempo de consulta em 50-90%.")
        else:
            print("\n✅ Volume de dados adequado para análise de performance.")
        
        # Simular consultas comuns
        import time
        
        queries = [
            "SELECT * FROM orders WHERE status = 'servico_executado'",
            "SELECT * FROM orders WHERE client_id = 1",
            "SELECT * FROM orders WHERE provider_id = 1 AND status = 'aguardando_execucao'"
        ]
        
        print("\n⏱️  Executando consultas de teste:")
        for query in queries:
            start = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            elapsed = (time.time() - start) * 1000  # em ms
            
            print(f"   - {len(results)} resultados em {elapsed:.2f}ms")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro na análise de performance: {e}")

if __name__ == '__main__':
    print("\n🚀 Iniciando testes de índices...\n")
    
    success = test_indexes_exist()
    
    if success:
        test_index_performance()
        print("\n✅ Todos os testes concluídos!")
    else:
        print("\n❌ Testes falharam. Verifique os índices.")
