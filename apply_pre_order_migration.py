#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migração do sistema de pré-ordem
"""

import sys
import os
from app import app, db
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_tables_exist():
    """Verifica se as tabelas já existem"""
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    required_tables = ['pre_orders', 'pre_order_proposals', 'pre_order_history']
    existing = [table for table in required_tables if table in existing_tables]
    missing = [table for table in required_tables if table not in existing_tables]
    
    return existing, missing


def check_pre_order_columns_exist():
    """Verifica se todas as colunas necessárias existem na tabela pre_orders"""
    inspector = inspect(db.engine)
    
    if 'pre_orders' not in inspector.get_table_names():
        return [], ['negotiation_round', 'version']
    
    columns = [col['name'] for col in inspector.get_columns('pre_orders')]
    
    required_columns = ['negotiation_round', 'version']
    existing = [col for col in required_columns if col in columns]
    missing = [col for col in required_columns if col not in columns]
    
    return existing, missing


def check_invite_columns_exist():
    """Verifica se as colunas foram adicionadas à tabela invites"""
    inspector = inspect(db.engine)
    
    # Verificar se tabela invites existe
    if 'invites' not in inspector.get_table_names():
        return [], ['converted_to_pre_order', 'pre_order_id']
    
    columns = [col['name'] for col in inspector.get_columns('invites')]
    
    required_columns = ['converted_to_pre_order', 'pre_order_id']
    existing = [col for col in required_columns if col in columns]
    missing = [col for col in required_columns if col not in columns]
    
    return existing, missing


def check_indexes_exist():
    """Verifica se os índices já existem"""
    inspector = inspect(db.engine)
    
    # Verificar índices de pre_orders
    pre_order_indexes = []
    if 'pre_orders' in inspector.get_table_names():
        pre_order_indexes = [idx['name'] for idx in inspector.get_indexes('pre_orders')]
    
    # Verificar índices de pre_order_proposals
    proposal_indexes = []
    if 'pre_order_proposals' in inspector.get_table_names():
        proposal_indexes = [idx['name'] for idx in inspector.get_indexes('pre_order_proposals')]
    
    # Verificar índices de pre_order_history
    history_indexes = []
    if 'pre_order_history' in inspector.get_table_names():
        history_indexes = [idx['name'] for idx in inspector.get_indexes('pre_order_history')]
    
    # Verificar índices de invites
    invite_indexes = []
    if 'invites' in inspector.get_table_names():
        invite_indexes = [idx['name'] for idx in inspector.get_indexes('invites')]
    
    required_indexes = {
        'pre_orders': ['idx_pre_orders_status', 'idx_pre_orders_client', 
                       'idx_pre_orders_provider', 'idx_pre_orders_expires'],
        'pre_order_proposals': ['uq_preorder_active_proposal'],
        'invites': ['idx_invites_pre_order']
    }
    
    return {
        'pre_orders': pre_order_indexes,
        'pre_order_proposals': proposal_indexes,
        'pre_order_history': history_indexes,
        'invites': invite_indexes
    }, required_indexes


def read_migration_file():
    """Lê o arquivo SQL de migração"""
    migration_file = 'migrations/add_pre_order_system.sql'
    
    if not os.path.exists(migration_file):
        logger.error(f"Arquivo de migração não encontrado: {migration_file}")
        return None
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        return f.read()


def apply_migration():
    """Aplica a migração do sistema de pré-ordem"""
    with app.app_context():
        try:
            logger.info("=" * 70)
            logger.info("INICIANDO MIGRAÇÃO: Sistema de Pré-Ordem")
            logger.info("=" * 70)
            
            # Verificar estado atual
            existing_tables, missing_tables = check_tables_exist()
            existing_invite_cols, missing_invite_cols = check_invite_columns_exist()
            existing_pre_order_cols, missing_pre_order_cols = check_pre_order_columns_exist()
            existing_indexes, required_indexes = check_indexes_exist()
            
            logger.info(f"\nTabelas existentes: {existing_tables}")
            logger.info(f"Tabelas faltando: {missing_tables}")
            logger.info(f"\nColunas em invites existentes: {existing_invite_cols}")
            logger.info(f"Colunas em invites faltando: {missing_invite_cols}")
            logger.info(f"\nColunas em pre_orders existentes: {existing_pre_order_cols}")
            logger.info(f"Colunas em pre_orders faltando: {missing_pre_order_cols}")
            
            # Adicionar colunas faltantes em pre_orders se a tabela já existe
            if 'pre_orders' in existing_tables and missing_pre_order_cols:
                logger.info("\n" + "=" * 70)
                logger.info("ADICIONANDO COLUNAS FALTANTES EM PRE_ORDERS")
                logger.info("=" * 70)
                
                if 'negotiation_round' in missing_pre_order_cols:
                    logger.info("\nAdicionando coluna negotiation_round...")
                    db.session.execute(text(
                        'ALTER TABLE pre_orders ADD COLUMN negotiation_round INTEGER NOT NULL DEFAULT 0'
                    ))
                    logger.info("   ✓ Coluna negotiation_round adicionada")
                
                if 'version' in missing_pre_order_cols:
                    logger.info("\nAdicionando coluna version...")
                    db.session.execute(text(
                        'ALTER TABLE pre_orders ADD COLUMN version INTEGER NOT NULL DEFAULT 1'
                    ))
                    logger.info("   ✓ Coluna version adicionada")
                
                db.session.commit()
                logger.info("\n✓ Colunas adicionadas com sucesso!")
                
                # Atualizar verificação
                existing_pre_order_cols, missing_pre_order_cols = check_pre_order_columns_exist()
            
            if not missing_tables and not missing_invite_cols and not missing_pre_order_cols:
                logger.info("\n✓ Migração já foi aplicada anteriormente!")
                logger.info("\nVerificando índices...")
                
                all_indexes_ok = True
                for table, required in required_indexes.items():
                    existing = existing_indexes.get(table, [])
                    missing = [idx for idx in required if idx not in existing]
                    if missing:
                        logger.warning(f"  Índices faltando em {table}: {missing}")
                        all_indexes_ok = False
                
                if all_indexes_ok:
                    logger.info("  ✓ Todos os índices estão presentes")
                    return True
            
            # Ler arquivo de migração
            logger.info("\n" + "=" * 70)
            logger.info("LENDO ARQUIVO DE MIGRAÇÃO")
            logger.info("=" * 70)
            
            migration_sql = read_migration_file()
            if not migration_sql:
                return False
            
            logger.info("✓ Arquivo de migração lido com sucesso")
            
            # Aplicar migração
            logger.info("\n" + "=" * 70)
            logger.info("APLICANDO MIGRAÇÃO")
            logger.info("=" * 70)
            
            # Dividir o SQL em statements individuais
            # SQLite não suporta múltiplos statements em uma única execução
            statements = []
            current_statement = []
            
            for line in migration_sql.split('\n'):
                # Ignorar comentários e linhas vazias
                stripped = line.strip()
                if not stripped or stripped.startswith('--') or stripped.startswith('COMMENT'):
                    continue
                
                current_statement.append(line)
                
                # Se a linha termina com ponto e vírgula, é o fim de um statement
                if stripped.endswith(';'):
                    statement = '\n'.join(current_statement)
                    if statement.strip():
                        statements.append(statement)
                    current_statement = []
            
            logger.info(f"\nTotal de statements SQL a executar: {len(statements)}")
            
            # Executar cada statement
            for i, statement in enumerate(statements, 1):
                try:
                    # Mostrar apenas as primeiras palavras do statement
                    preview = ' '.join(statement.split()[:8])
                    logger.info(f"\n{i}. Executando: {preview}...")
                    
                    db.session.execute(text(statement))
                    logger.info(f"   ✓ Sucesso")
                    
                except Exception as e:
                    error_msg = str(e)
                    # Ignorar erros de "já existe" que são esperados
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        logger.info(f"   ⚠ Já existe (ignorando): {error_msg}")
                    else:
                        logger.error(f"   ✗ Erro: {error_msg}")
                        raise
            
            # Commit das alterações
            db.session.commit()
            logger.info("\n✓ Migração aplicada com sucesso!")
            
            # Verificar resultado
            logger.info("\n" + "=" * 70)
            logger.info("VERIFICANDO RESULTADO")
            logger.info("=" * 70)
            
            existing_tables, missing_tables = check_tables_exist()
            existing_invite_cols, missing_invite_cols = check_invite_columns_exist()
            existing_pre_order_cols, missing_pre_order_cols = check_pre_order_columns_exist()
            existing_indexes, required_indexes = check_indexes_exist()
            
            logger.info(f"\nTabelas criadas: {existing_tables}")
            logger.info(f"Tabelas faltando: {missing_tables}")
            logger.info(f"\nColunas em invites: {existing_invite_cols}")
            logger.info(f"Colunas em invites faltando: {missing_invite_cols}")
            logger.info(f"\nColunas em pre_orders: {existing_pre_order_cols}")
            logger.info(f"Colunas em pre_orders faltando: {missing_pre_order_cols}")
            
            logger.info("\nÍndices criados:")
            for table, indexes in existing_indexes.items():
                if indexes:
                    logger.info(f"  {table}: {indexes}")
            
            if not missing_tables and not missing_invite_cols and not missing_pre_order_cols:
                logger.info("\n✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                return True
            else:
                logger.error("\n✗ Erro: Algumas tabelas ou colunas ainda estão faltando")
                return False
                
        except Exception as e:
            logger.error(f"\n✗ Erro ao aplicar migração: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


def test_migration():
    """Testa a migração verificando a estrutura das tabelas"""
    with app.app_context():
        try:
            logger.info("\n" + "=" * 70)
            logger.info("TESTANDO MIGRAÇÃO")
            logger.info("=" * 70)
            
            inspector = inspect(db.engine)
            
            # Testar tabela pre_orders
            logger.info("\n1. Verificando estrutura de pre_orders...")
            if 'pre_orders' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('pre_orders')]
                logger.info(f"   Colunas ({len(columns)}): {', '.join(columns[:10])}...")
                logger.info("   ✓ Tabela pre_orders OK")
            else:
                logger.error("   ✗ Tabela pre_orders não encontrada")
                return False
            
            # Testar tabela pre_order_proposals
            logger.info("\n2. Verificando estrutura de pre_order_proposals...")
            if 'pre_order_proposals' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('pre_order_proposals')]
                logger.info(f"   Colunas ({len(columns)}): {', '.join(columns)}")
                logger.info("   ✓ Tabela pre_order_proposals OK")
            else:
                logger.error("   ✗ Tabela pre_order_proposals não encontrada")
                return False
            
            # Testar tabela pre_order_history
            logger.info("\n3. Verificando estrutura de pre_order_history...")
            if 'pre_order_history' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('pre_order_history')]
                logger.info(f"   Colunas ({len(columns)}): {', '.join(columns)}")
                logger.info("   ✓ Tabela pre_order_history OK")
            else:
                logger.error("   ✗ Tabela pre_order_history não encontrada")
                return False
            
            # Testar colunas adicionadas em invites
            logger.info("\n4. Verificando colunas adicionadas em invites...")
            if 'invites' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('invites')]
                if 'converted_to_pre_order' in columns and 'pre_order_id' in columns:
                    logger.info("   ✓ Colunas converted_to_pre_order e pre_order_id OK")
                else:
                    logger.error("   ✗ Colunas não encontradas em invites")
                    return False
            
            logger.info("\n✓ Todas as estruturas estão corretas!")
            return True
                
        except Exception as e:
            logger.error(f"\n✗ Erro ao testar migração: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    logger.info("\n" + "=" * 70)
    logger.info("MIGRAÇÃO: Sistema de Pré-Ordem")
    logger.info("=" * 70)
    
    # Aplicar migração
    if not apply_migration():
        logger.error("\n✗ Falha ao aplicar migração")
        sys.exit(1)
    
    # Testar migração
    if not test_migration():
        logger.error("\n✗ Falha ao testar migração")
        sys.exit(1)
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ MIGRAÇÃO COMPLETA E TESTADA COM SUCESSO!")
    logger.info("=" * 70)
    logger.info("\nTabelas criadas:")
    logger.info("  - pre_orders (pré-ordens)")
    logger.info("  - pre_order_proposals (propostas de alteração)")
    logger.info("  - pre_order_history (histórico de eventos)")
    logger.info("\nColunas adicionadas em invites:")
    logger.info("  - converted_to_pre_order (Boolean)")
    logger.info("  - pre_order_id (Integer)")
    logger.info("\nÍndices criados:")
    logger.info("  - idx_pre_orders_status")
    logger.info("  - idx_pre_orders_client")
    logger.info("  - idx_pre_orders_provider")
    logger.info("  - idx_pre_orders_expires")
    logger.info("  - uq_preorder_active_proposal (único)")
    logger.info("  - idx_invites_pre_order")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
