#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para migrar a tabela token_requests para a nova estrutura
"""

import sqlite3
import os
from datetime import datetime

def migrate_token_requests():
    """Migra a tabela token_requests para incluir campos de comprovante e usar NUMERIC"""
    
    db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    print("🔄 Migrando tabela token_requests...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Criar backup da tabela atual
        print("1. Criando backup da tabela token_requests...")
        cursor.execute("CREATE TABLE token_requests_backup AS SELECT * FROM token_requests;")
        
        # 2. Remover tabela atual
        print("2. Removendo tabela token_requests atual...")
        cursor.execute("DROP TABLE token_requests;")
        
        # 3. Criar nova estrutura
        print("3. Criando nova estrutura da tabela token_requests...")
        cursor.execute("""
            CREATE TABLE token_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        # 4. Restaurar dados existentes (se houver)
        print("4. Restaurando dados existentes...")
        cursor.execute("""
            INSERT INTO token_requests (
                id, user_id, amount, description, status, 
                created_at, processed_at, processed_by, admin_notes
            )
            SELECT 
                id, user_id, amount, description, status,
                created_at, processed_at, processed_by, admin_notes
            FROM token_requests_backup;
        """)
        
        # 5. Criar índices
        print("5. Criando índices...")
        cursor.execute("CREATE INDEX idx_token_requests_user_status ON token_requests(user_id, status);")
        cursor.execute("CREATE INDEX idx_token_requests_status ON token_requests(status);")
        cursor.execute("CREATE INDEX idx_token_requests_created_at ON token_requests(created_at DESC);")
        
        # 6. Remover backup
        print("6. Removendo backup temporário...")
        cursor.execute("DROP TABLE token_requests_backup;")
        
        # Confirmar transação
        conn.commit()
        
        # Verificar resultado
        cursor.execute("SELECT COUNT(*) FROM token_requests;")
        count = cursor.fetchone()[0]
        
        print(f"✅ Migração concluída com sucesso!")
        print(f"   • Registros migrados: {count}")
        
        # Verificar estrutura
        cursor.execute("PRAGMA table_info(token_requests);")
        columns = cursor.fetchall()
        print(f"   • Colunas na nova tabela: {len(columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MIGRAÇÃO: Tabela token_requests")
    print("=" * 60)
    
    if migrate_token_requests():
        print("\n🎉 Migração concluída com sucesso!")
    else:
        print("\n❌ Falha na migração")