#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para corrigir o schema da tabela invites
"""

from app import app
from models import db

def fix_invites_schema():
    """Corrige o schema da tabela invites"""
    
    with app.app_context():
        try:
            print("🔧 Corrigindo schema da tabela invites...")
            
            with db.engine.connect() as conn:
                # SQLite não suporta ALTER COLUMN diretamente
                # Vamos recriar a tabela com o schema correto
                
                print("📋 Criando tabela temporária...")
                
                # 1. Criar tabela temporária com schema correto
                conn.execute(db.text("""
                    CREATE TABLE invites_temp (
                        id INTEGER PRIMARY KEY,
                        client_id INTEGER NOT NULL,
                        invited_email VARCHAR(120) NULL,
                        invited_phone VARCHAR(20) NOT NULL,
                        service_title VARCHAR(200) NOT NULL,
                        service_description TEXT NOT NULL,
                        service_category VARCHAR(100) NULL,
                        original_value NUMERIC(10, 2) NOT NULL,
                        final_value NUMERIC(10, 2) NULL,
                        delivery_date DATETIME NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                        token VARCHAR(100) NOT NULL UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL,
                        responded_at DATETIME NULL,
                        order_id INTEGER NULL,
                        FOREIGN KEY (client_id) REFERENCES users(id),
                        FOREIGN KEY (order_id) REFERENCES orders(id)
                    )
                """))
                
                print("📊 Copiando dados existentes...")
                
                # 2. Copiar dados existentes (com email fictício se necessário)
                conn.execute(db.text("""
                    INSERT INTO invites_temp (
                        id, client_id, invited_email, invited_phone, service_title, 
                        service_description, service_category, original_value, final_value,
                        delivery_date, status, token, created_at, expires_at, 
                        responded_at, order_id
                    )
                    SELECT 
                        id, client_id, 
                        CASE 
                            WHEN invited_email IS NOT NULL THEN invited_email
                            ELSE 'temp@email.com'
                        END as invited_email,
                        CASE 
                            WHEN invited_phone IS NOT NULL THEN invited_phone
                            ELSE '(11) 99999-' || SUBSTR('0000' || id, -4)
                        END as invited_phone,
                        service_title, service_description, service_category,
                        original_value, final_value, delivery_date, status, token,
                        created_at, expires_at, responded_at, order_id
                    FROM invites
                """))
                
                print("🗑️ Removendo tabela antiga...")
                
                # 3. Remover tabela antiga
                conn.execute(db.text("DROP TABLE invites"))
                
                print("🔄 Renomeando tabela temporária...")
                
                # 4. Renomear tabela temporária
                conn.execute(db.text("ALTER TABLE invites_temp RENAME TO invites"))
                
                # 5. Recriar índices se necessário
                conn.execute(db.text("CREATE UNIQUE INDEX idx_invites_token ON invites(token)"))
                
                conn.commit()
                
                print("✅ Schema da tabela invites corrigido!")
                
                # Verificar resultado
                result = conn.execute(db.text('PRAGMA table_info(invites);'))
                print("\n📋 Novo schema:")
                for row in result:
                    print(f"   {row}")
                
                return True
                
        except Exception as e:
            print(f"❌ Erro ao corrigir schema: {e}")
            return False

if __name__ == "__main__":
    success = fix_invites_schema()
    if success:
        print("\n🎉 Schema corrigido com sucesso!")
    else:
        print("\n💥 Falha ao corrigir schema!")