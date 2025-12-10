#!/usr/bin/env python3
"""
Script para forçar a adição das colunas no banco SQLite diretamente
"""
import sqlite3
import os

DB_PATH = 'sistema_combinado.db'

def force_add_columns():
    """Adiciona as colunas diretamente usando SQL"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar colunas existentes
        cursor.execute("PRAGMA table_info(orders)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"✓ Colunas existentes em orders: {existing_columns}")
        
        columns_to_add = [
            ('valor_efetivo_cliente', 'NUMERIC(10, 2)'),
            ('valor_efetivo_prestador', 'NUMERIC(10, 2)'),
            ('taxa_plataforma_percentual', 'NUMERIC(5, 2)'),
            ('taxa_plataforma_valor', 'NUMERIC(10, 2)')
        ]
        
        added = []
        skipped = []
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"
                    print(f"\n🔧 Executando: {sql}")
                    cursor.execute(sql)
                    added.append(col_name)
                    print(f"✓ Coluna '{col_name}' adicionada com sucesso")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  Erro ao adicionar '{col_name}': {e}")
            else:
                skipped.append(col_name)
                print(f"⏭️  Coluna '{col_name}' já existe")
        
        conn.commit()
        
        # Verificar resultado final
        cursor.execute("PRAGMA table_info(orders)")
        final_columns = {row[1] for row in cursor.fetchall()}
        
        print("\n" + "="*60)
        print("RESULTADO FINAL")
        print("="*60)
        print(f"✓ Colunas adicionadas: {added if added else 'Nenhuma'}")
        print(f"⏭️  Colunas já existentes: {skipped if skipped else 'Nenhuma'}")
        print(f"\n✓ Total de colunas na tabela orders: {len(final_columns)}")
        
        # Verificar se todas as colunas necessárias estão presentes
        required = {'valor_efetivo_cliente', 'valor_efetivo_prestador', 
                   'taxa_plataforma_percentual', 'taxa_plataforma_valor'}
        missing = required - final_columns
        
        if missing:
            print(f"\n❌ Colunas ainda faltando: {missing}")
            return False
        else:
            print(f"\n✅ Todas as colunas necessárias estão presentes!")
            return True
            
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("="*60)
    print("FORÇANDO ADIÇÃO DE COLUNAS NO BANCO SQLITE")
    print("="*60)
    
    success = force_add_columns()
    
    if success:
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
