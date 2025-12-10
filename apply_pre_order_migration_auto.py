#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para aplicar migration do sistema de pré-ordem (modo automático)
"""

import sys
import os
from datetime import datetime
import sqlite3

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_migration():
    """Aplica a migration do sistema de pré-ordem"""
    logger.info("=" * 80)
    logger.info("INICIANDO MIGRATION DO SISTEMA DE PRÉ-ORDEM")
    logger.info("=" * 80)
    
    try:
        # Ler arquivo SQL
        migration_file = 'migrations/add_pre_order_system.sql'
        logger.info(f"Lendo arquivo de migration: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Executar SQL usando executescript (mais robusto)
        with app.app_context():
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            try:
                logger.info("Executando script SQL...")
                cursor.executescript(sql_content)
                connection.commit()
                logger.info("✓ Script SQL executado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao executar script: {str(e)}")
                raise
            finally:
                cursor.close()
                connection.close()
        
        # Verificar tabelas criadas
        logger.info("Verificando tabelas criadas...")
        with app.app_context():
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = ['pre_orders', 'pre_order_proposals', 'pre_order_history']
            for table in required_tables:
                if table in existing_tables:
                    logger.info(f"✓ Tabela '{table}' criada com sucesso")
                    columns = inspector.get_columns(table)
                    logger.info(f"  - {len(columns)} colunas")
                    indexes = inspector.get_indexes(table)
                    if indexes:
                        logger.info(f"  - {len(indexes)} índices")
                else:
                    logger.error(f"✗ Tabela '{table}' NÃO foi criada")
                    return False
        
        logger.info("=" * 80)
        logger.info("MIGRATION CONCLUÍDA COM SUCESSO!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro durante migration: {str(e)}")
        logger.exception(e)
        return False


if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
