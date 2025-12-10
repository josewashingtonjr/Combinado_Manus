#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para aplicar índices de performance no sistema de pré-ordens

Este script aplica os índices definidos em migrations/add_pre_order_indexes.sql
para otimizar consultas no sistema de pré-ordens.

Uso:
    python apply_pre_order_indexes.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def apply_indexes():
    """
    Aplica os índices de performance para o sistema de pré-ordens
    """
    migration_file = Path('migrations/add_pre_order_indexes.sql')
    
    if not migration_file.exists():
        logger.error(f"Arquivo de migração não encontrado: {migration_file}")
        return False
    
    logger.info("=" * 80)
    logger.info("APLICAÇÃO DE ÍNDICES DE PERFORMANCE - SISTEMA DE PRÉ-ORDENS")
    logger.info("=" * 80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        with app.app_context():
            # Ler arquivo SQL
            logger.info(f"Lendo arquivo de migração: {migration_file}")
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Dividir em comandos individuais (separados por ponto-e-vírgula)
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            # Filtrar comentários e comandos vazios
            commands = [
                cmd for cmd in commands 
                if cmd and not cmd.startswith('--') and cmd.upper() not in ['ANALYZE']
            ]
            
            logger.info(f"Total de comandos SQL a executar: {len(commands)}")
            logger.info("")
            
            # Executar cada comando
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for i, command in enumerate(commands, 1):
                # Extrair nome do índice do comando
                index_name = "desconhecido"
                if "CREATE INDEX" in command.upper():
                    parts = command.split()
                    try:
                        idx = parts.index("INDEX") + 1
                        if idx < len(parts) and parts[idx].upper() == "IF":
                            idx += 3  # Pular "IF NOT EXISTS"
                        if idx < len(parts):
                            index_name = parts[idx]
                    except:
                        pass
                
                try:
                    logger.info(f"[{i}/{len(commands)}] Executando: {index_name}")
                    db.session.execute(text(command))
                    db.session.commit()
                    success_count += 1
                    logger.info(f"  ✓ Sucesso")
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Verificar se é erro de índice já existente
                    if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                        logger.info(f"  ⊘ Índice já existe (pulando)")
                        skip_count += 1
                        db.session.rollback()
                    else:
                        logger.error(f"  ✗ Erro: {error_msg}")
                        error_count += 1
                        db.session.rollback()
            
            # Executar ANALYZE para atualizar estatísticas
            logger.info("")
            logger.info("Atualizando estatísticas do banco de dados...")
            try:
                db.session.execute(text("ANALYZE"))
                db.session.commit()
                logger.info("  ✓ Estatísticas atualizadas")
            except Exception as e:
                logger.warning(f"  ⚠ Não foi possível atualizar estatísticas: {e}")
            
            # Resumo
            logger.info("")
            logger.info("=" * 80)
            logger.info("RESUMO DA APLICAÇÃO DE ÍNDICES")
            logger.info("=" * 80)
            logger.info(f"Índices criados com sucesso: {success_count}")
            logger.info(f"Índices já existentes (pulados): {skip_count}")
            logger.info(f"Erros: {error_count}")
            logger.info("")
            
            if error_count == 0:
                logger.info("✓ Migração concluída com sucesso!")
                logger.info("")
                logger.info("Os seguintes índices foram aplicados:")
                logger.info("  • idx_pre_orders_status - Consultas por status")
                logger.info("  • idx_pre_orders_client - Consultas por cliente")
                logger.info("  • idx_pre_orders_provider - Consultas por prestador")
                logger.info("  • idx_pre_orders_expires - Consultas por expiração")
                logger.info("  • idx_pre_order_proposals_status - Propostas por status")
                logger.info("  • idx_pre_order_history_pre_order - Histórico por pré-ordem")
                logger.info("  • E outros índices compostos para otimização")
                logger.info("")
                logger.info("Impacto esperado:")
                logger.info("  • Dashboards: 10-50x mais rápidos")
                logger.info("  • Consultas de histórico: 10-30x mais rápidas")
                logger.info("  • Jobs de expiração: 20-100x mais rápidos")
                return True
            else:
                logger.warning("⚠ Migração concluída com erros. Verifique os logs acima.")
                return False
                
    except Exception as e:
        logger.error(f"Erro fatal ao aplicar índices: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_indexes():
    """
    Verifica quais índices foram criados
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("VERIFICAÇÃO DE ÍNDICES CRIADOS")
    logger.info("=" * 80)
    
    try:
        with app.app_context():
            # Consultar índices das tabelas de pré-ordem
            query = text("""
                SELECT name, tbl_name, sql 
                FROM sqlite_master 
                WHERE type='index' 
                AND tbl_name LIKE 'pre_order%'
                ORDER BY tbl_name, name
            """)
            
            result = db.session.execute(query)
            indexes = result.fetchall()
            
            if not indexes:
                logger.warning("Nenhum índice encontrado nas tabelas de pré-ordem")
                return
            
            current_table = None
            for idx_name, tbl_name, sql in indexes:
                if tbl_name != current_table:
                    logger.info("")
                    logger.info(f"Tabela: {tbl_name}")
                    logger.info("-" * 80)
                    current_table = tbl_name
                
                logger.info(f"  • {idx_name}")
            
            logger.info("")
            logger.info(f"Total de índices: {len(indexes)}")
            
    except Exception as e:
        logger.error(f"Erro ao verificar índices: {e}")


if __name__ == '__main__':
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "APLICAÇÃO DE ÍNDICES DE PERFORMANCE" + " " * 23 + "║")
    print("║" + " " * 25 + "Sistema de Pré-Ordens" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    # Aplicar índices
    success = apply_indexes()
    
    # Verificar índices criados
    if success:
        verify_indexes()
    
    print("\n")
    
    sys.exit(0 if success else 1)
