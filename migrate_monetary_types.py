#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script de migração para converter tipos Float para Numeric(18,2)
Execute este script para migrar os dados existentes
"""

import sys
import os
import logging
from flask import Flask
from config import Config
from models import db
from services.monetary_migration_service import MonetaryMigrationService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monetary_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Cria a aplicação Flask para migração"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    return app

def main():
    """Função principal de migração"""
    try:
        logger.info("=== INICIANDO MIGRAÇÃO DE TIPOS MONETÁRIOS ===")
        
        # Cria a aplicação
        app = create_app()
        
        with app.app_context():
            # Verifica se o diretório de logs existe
            os.makedirs('logs', exist_ok=True)
            
            # Executa a migração
            success, errors = MonetaryMigrationService.migrate_float_to_numeric()
            
            if success:
                logger.info("=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===")
                print("\n✅ Migração concluída com sucesso!")
                print("Todos os campos monetários foram convertidos para Numeric(18,2)")
                print("Constraints de integridade foram adicionadas")
                print("Índices de performance foram criados")
                return 0
            else:
                logger.error("=== MIGRAÇÃO FALHOU ===")
                print("\n❌ Migração falhou!")
                print("Erros encontrados:")
                for error in errors:
                    print(f"  - {error}")
                return 1
                
    except Exception as e:
        logger.error(f"Erro crítico na migração: {str(e)}")
        print(f"\n💥 Erro crítico: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)