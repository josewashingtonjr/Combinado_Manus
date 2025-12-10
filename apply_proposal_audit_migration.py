#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para aplicar migração das tabelas de auditoria de propostas

Este script cria as tabelas necessárias para o sistema de auditoria e monitoramento
de propostas, incluindo logs de auditoria, métricas e alertas.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import sys
import os
import logging
from flask import Flask
from config import Config
from models import db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/proposal_audit_migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Criar aplicação Flask para migração"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def apply_migration():
    """Aplicar migração das tabelas de auditoria"""
    try:
        logger.info("=== INICIANDO MIGRAÇÃO DE AUDITORIA DE PROPOSTAS ===")
        
        # Criar aplicação
        app = create_app()
        
        with app.app_context():
            # Verificar se o diretório de logs existe
            os.makedirs('logs', exist_ok=True)
            
            # Ler arquivo de migração
            migration_file = 'migrations/add_proposal_audit_tables.sql'
            
            if not os.path.exists(migration_file):
                logger.error(f"Arquivo de migração não encontrado: {migration_file}")
                return False
            
            logger.info(f"Lendo arquivo de migração: {migration_file}")
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Dividir em comandos individuais, tratando triggers especialmente
            commands = []
            current_command = ""
            in_trigger = False
            
            for line in migration_sql.split('\n'):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue
                
                current_command += line + '\n'
                
                # Detectar início de trigger
                if 'CREATE TRIGGER' in line.upper():
                    in_trigger = True
                
                # Detectar fim de trigger
                if in_trigger and line.upper() == 'END;':
                    commands.append(current_command.strip())
                    current_command = ""
                    in_trigger = False
                # Detectar fim de comando normal
                elif not in_trigger and line.endswith(';'):
                    commands.append(current_command.strip())
                    current_command = ""
            
            # Adicionar último comando se houver
            if current_command.strip():
                commands.append(current_command.strip())
            
            # Filtrar comandos vazios
            commands = [cmd for cmd in commands if cmd.strip()]
            
            logger.info(f"Executando {len(commands)} comandos SQL...")
            
            # Executar cada comando
            for i, command in enumerate(commands, 1):
                try:
                    if command.strip():
                        logger.info(f"Executando comando {i}/{len(commands)}")
                        logger.debug(f"SQL: {command[:100]}...")
                        
                        db.session.execute(db.text(command))
                        db.session.commit()
                        
                        logger.info(f"✓ Comando {i} executado com sucesso")
                
                except Exception as e:
                    logger.error(f"✗ Erro no comando {i}: {str(e)}")
                    logger.error(f"SQL que falhou: {command}")
                    db.session.rollback()
                    return False
            
            # Verificar se as tabelas foram criadas
            logger.info("Verificando tabelas criadas...")
            
            tables_to_check = [
                'proposal_audit_logs',
                'proposal_metrics', 
                'proposal_alerts'
            ]
            
            for table_name in tables_to_check:
                try:
                    result = db.session.execute(
                        db.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                    ).fetchone()
                    
                    if result:
                        logger.info(f"✓ Tabela {table_name} criada com sucesso")
                        
                        # Verificar estrutura da tabela
                        columns = db.session.execute(
                            db.text(f"PRAGMA table_info({table_name})")
                        ).fetchall()
                        
                        logger.info(f"  - {len(columns)} colunas criadas")
                        
                    else:
                        logger.error(f"✗ Tabela {table_name} não foi criada")
                        return False
                        
                except Exception as e:
                    logger.error(f"✗ Erro ao verificar tabela {table_name}: {str(e)}")
                    return False
            
            # Verificar índices criados
            logger.info("Verificando índices criados...")
            
            indices = db.session.execute(
                db.text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_proposal_%'")
            ).fetchall()
            
            logger.info(f"✓ {len(indices)} índices de propostas criados")
            
            # Verificar triggers criados
            triggers = db.session.execute(
                db.text("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%proposal%'")
            ).fetchall()
            
            logger.info(f"✓ {len(triggers)} triggers de propostas criados")
            
            # Verificar se a tabela SystemConfig existe antes de consultar
            try:
                from models import SystemConfig
                
                # Verificar se a tabela existe
                result = db.session.execute(
                    db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='system_configs'")
                ).fetchone()
                
                if result:
                    audit_configs = SystemConfig.query.filter(
                        SystemConfig.key.like('proposal_%')
                    ).all()
                    
                    logger.info(f"✓ {len(audit_configs)} configurações de auditoria encontradas")
                    
                    for config in audit_configs:
                        logger.info(f"  - {config.key}: {config.value}")
                else:
                    logger.info("ℹ Tabela system_configs não existe - configurações serão gerenciadas pelo código")
                    
            except Exception as e:
                logger.warning(f"Não foi possível verificar configurações: {str(e)}")
            
            logger.info("=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===")
            return True
            
    except Exception as e:
        logger.error(f"Erro crítico na migração: {str(e)}")
        return False

def main():
    """Função principal"""
    try:
        logger.info("Iniciando aplicação da migração de auditoria de propostas...")
        
        success = apply_migration()
        
        if success:
            logger.info("=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===")
            print("\n✅ Migração concluída com sucesso!")
            print("Sistema de auditoria de propostas está pronto para uso.")
            print("\nRecursos disponíveis:")
            print("- Logs de auditoria completos")
            print("- Métricas agregadas por período")
            print("- Alertas automáticos para padrões suspeitos")
            print("- Dashboard administrativo de monitoramento")
            return 0
        else:
            logger.error("=== MIGRAÇÃO FALHOU ===")
            print("\n❌ Migração falhou!")
            print("Verifique os logs para mais detalhes.")
            return 1
            
    except Exception as e:
        logger.error(f"Erro crítico na migração: {str(e)}")
        print(f"\n💥 Erro crítico: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())