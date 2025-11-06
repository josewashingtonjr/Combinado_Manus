#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para aplicar migração da tabela token_creation_limits
Implementa controle de limites de criação de tokens por administrador
"""

import sqlite3
import os
from datetime import datetime

def apply_migration():
    """Aplica a migração para criar tabela token_creation_limits"""
    
    # Caminho do banco de dados
    db_path = 'sistema_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Aplicando migração da tabela token_creation_limits...")
        
        # Ler e executar o script de migração
        with open('migrations/add_token_creation_limits_table.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Executar a migração
        cursor.executescript(migration_sql)
        
        # Verificar se a tabela foi criada
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='token_creation_limits'
        """)
        
        if cursor.fetchone():
            print("✅ Tabela token_creation_limits criada com sucesso!")
            
            # Verificar quantos administradores receberam limites padrão
            cursor.execute("SELECT COUNT(*) FROM token_creation_limits")
            count = cursor.fetchone()[0]
            print(f"✅ Limites padrão configurados para {count} administrador(es)")
            
            # Mostrar estrutura da tabela
            cursor.execute("PRAGMA table_info(token_creation_limits)")
            columns = cursor.fetchall()
            print("\n📋 Estrutura da tabela token_creation_limits:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Mostrar dados inseridos
            cursor.execute("""
                SELECT tcl.admin_id, au.email, tcl.daily_limit, tcl.monthly_limit
                FROM token_creation_limits tcl
                JOIN admin_users au ON tcl.admin_id = au.id
                WHERE au.deleted_at IS NULL
            """)
            
            limits = cursor.fetchall()
            if limits:
                print("\n📊 Limites configurados:")
                for limit in limits:
                    admin_id, email, daily, monthly = limit
                    print(f"   - Admin {admin_id} ({email}): Diário R$ {daily:.2f}, Mensal R$ {monthly:.2f}")
            
        else:
            print("❌ Erro: Tabela token_creation_limits não foi criada")
            return False
        
        # Commit das alterações
        conn.commit()
        print("\n✅ Migração aplicada com sucesso!")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verifica se a migração foi aplicada corretamente"""
    
    db_path = 'sistema_combinado.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Verificando integridade da migração...")
        
        # Verificar constraints
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='token_creation_limits'
        """)
        
        table_sql = cursor.fetchone()
        if table_sql:
            sql = table_sql[0]
            constraints = ['CHECK (daily_limit > 0)', 'CHECK (monthly_limit > 0)', 
                          'CHECK (current_daily_used >= 0)', 'CHECK (current_monthly_used >= 0)']
            
            for constraint in constraints:
                if constraint in sql:
                    print(f"   ✅ Constraint encontrada: {constraint}")
                else:
                    print(f"   ❌ Constraint ausente: {constraint}")
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='token_creation_limits'
        """)
        
        indexes = cursor.fetchall()
        expected_indexes = ['idx_token_creation_limits_admin_id', 
                           'idx_token_creation_limits_daily_reset',
                           'idx_token_creation_limits_monthly_reset']
        
        print("\n📋 Índices criados:")
        for index in indexes:
            index_name = index[0]
            if index_name in expected_indexes:
                print(f"   ✅ {index_name}")
            else:
                print(f"   ℹ️  {index_name} (adicional)")
        
        # Verificar chave estrangeira
        cursor.execute("PRAGMA foreign_key_list(token_creation_limits)")
        foreign_keys = cursor.fetchall()
        
        if foreign_keys:
            print("\n🔗 Chaves estrangeiras:")
            for fk in foreign_keys:
                print(f"   ✅ {fk[2]} -> {fk[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MIGRAÇÃO: Tabela de Limites de Criação de Tokens")
    print("=" * 60)
    
    if apply_migration():
        verify_migration()
        print("\n🎉 Migração concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("   1. Implementar TokenCreationControlService")
        print("   2. Integrar controle nas rotas de criação de tokens")
        print("   3. Adicionar interface de configuração de limites")
    else:
        print("\n❌ Falha na aplicação da migração")