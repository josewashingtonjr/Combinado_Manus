#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para criar a tabela session_timeouts no banco de dados
"""

import sqlite3
import os
from datetime import datetime

def create_session_timeout_table():
    """Criar tabela session_timeouts no banco de dados"""
    
    # Conectar ao banco de dados principal
    db_path = 'sistema_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='session_timeouts'
        """)
        
        if cursor.fetchone():
            print("✅ Tabela session_timeouts já existe")
            conn.close()
            return True
        
        # Criar a tabela session_timeouts
        cursor.execute("""
            CREATE TABLE session_timeouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER,
                admin_id INTEGER,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES admin_users (id)
            )
        """)
        
        # Criar índices para performance
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_session_id 
            ON session_timeouts(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_expires_at 
            ON session_timeouts(expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_user_id 
            ON session_timeouts(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_admin_id 
            ON session_timeouts(admin_id)
        """)
        
        # Confirmar as mudanças
        conn.commit()
        conn.close()
        
        print("✅ Tabela session_timeouts criada com sucesso!")
        print("✅ Índices criados para otimização de consultas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela session_timeouts: {str(e)}")
        return False

def create_in_test_db():
    """Criar tabela também no banco de teste"""
    
    test_db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(test_db_path):
        print(f"⚠️ Banco de teste não encontrado: {test_db_path}")
        return False
    
    try:
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='session_timeouts'
        """)
        
        if cursor.fetchone():
            print("✅ Tabela session_timeouts já existe no banco de teste")
            conn.close()
            return True
        
        # Criar a tabela session_timeouts
        cursor.execute("""
            CREATE TABLE session_timeouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER,
                admin_id INTEGER,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES admin_users (id)
            )
        """)
        
        # Criar índices
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_session_id 
            ON session_timeouts(session_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_expires_at 
            ON session_timeouts(expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_user_id 
            ON session_timeouts(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_session_timeouts_admin_id 
            ON session_timeouts(admin_id)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Tabela session_timeouts criada no banco de teste!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela no banco de teste: {str(e)}")
        return False

if __name__ == '__main__':
    print("🔧 Criando tabela session_timeouts...")
    
    # Criar no banco principal
    success_main = create_session_timeout_table()
    
    # Criar no banco de teste
    success_test = create_in_test_db()
    
    if success_main:
        print("\n✅ Tabela session_timeouts criada com sucesso no banco principal!")
    
    if success_test:
        print("✅ Tabela session_timeouts criada com sucesso no banco de teste!")
    
    if success_main or success_test:
        print("\n🎉 Sistema de timeout de sessão pronto para uso!")
    else:
        print("\n❌ Falha ao criar tabelas. Verifique os erros acima.")