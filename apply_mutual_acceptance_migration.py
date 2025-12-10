#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar migração de campos de aceitação mútua
"""

import sys
from app import app, db
from models import Invite
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_columns_exist():
    """Verifica se as colunas já existem"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('invites')]
    
    required_columns = ['client_accepted', 'client_accepted_at', 'provider_accepted', 'provider_accepted_at']
    existing = [col for col in required_columns if col in columns]
    missing = [col for col in required_columns if col not in columns]
    
    return existing, missing


def check_index_exists():
    """Verifica se o índice já existe"""
    inspector = inspect(db.engine)
    indexes = inspector.get_indexes('invites')
    
    for idx in indexes:
        if idx['name'] == 'idx_invite_mutual_acceptance':
            return True
    return False


def apply_migration():
    """Aplica a migração de aceitação mútua"""
    with app.app_context():
        try:
            logger.info("=" * 60)
            logger.info("INICIANDO MIGRAÇÃO: Campos de Aceitação Mútua")
            logger.info("=" * 60)
            
            # Verificar estado atual
            existing_cols, missing_cols = check_columns_exist()
            index_exists = check_index_exists()
            
            logger.info(f"\nColunas existentes: {existing_cols}")
            logger.info(f"Colunas faltando: {missing_cols}")
            logger.info(f"Índice existe: {index_exists}")
            
            if not missing_cols and index_exists:
                logger.info("\n✓ Migração já foi aplicada anteriormente!")
                return True
            
            # Aplicar migração
            logger.info("\n" + "=" * 60)
            logger.info("APLICANDO MIGRAÇÃO")
            logger.info("=" * 60)
            
            # Adicionar colunas se necessário
            if 'client_accepted' in missing_cols:
                logger.info("\n1. Adicionando coluna client_accepted...")
                db.session.execute(text(
                    "ALTER TABLE invites ADD COLUMN client_accepted BOOLEAN NOT NULL DEFAULT FALSE"
                ))
                logger.info("   ✓ Coluna client_accepted adicionada")
            
            if 'client_accepted_at' in missing_cols:
                logger.info("\n2. Adicionando coluna client_accepted_at...")
                db.session.execute(text(
                    "ALTER TABLE invites ADD COLUMN client_accepted_at TIMESTAMP NULL"
                ))
                logger.info("   ✓ Coluna client_accepted_at adicionada")
            
            if 'provider_accepted' in missing_cols:
                logger.info("\n3. Adicionando coluna provider_accepted...")
                db.session.execute(text(
                    "ALTER TABLE invites ADD COLUMN provider_accepted BOOLEAN NOT NULL DEFAULT FALSE"
                ))
                logger.info("   ✓ Coluna provider_accepted adicionada")
            
            if 'provider_accepted_at' in missing_cols:
                logger.info("\n4. Adicionando coluna provider_accepted_at...")
                db.session.execute(text(
                    "ALTER TABLE invites ADD COLUMN provider_accepted_at TIMESTAMP NULL"
                ))
                logger.info("   ✓ Coluna provider_accepted_at adicionada")
            
            # Criar índice se necessário
            if not index_exists:
                logger.info("\n5. Criando índice composto idx_invite_mutual_acceptance...")
                db.session.execute(text(
                    "CREATE INDEX idx_invite_mutual_acceptance ON invites(client_accepted, provider_accepted, status)"
                ))
                logger.info("   ✓ Índice criado com sucesso")
            
            # Commit das alterações
            db.session.commit()
            logger.info("\n✓ Migração aplicada com sucesso!")
            
            # Verificar resultado
            logger.info("\n" + "=" * 60)
            logger.info("VERIFICANDO RESULTADO")
            logger.info("=" * 60)
            
            existing_cols, missing_cols = check_columns_exist()
            index_exists = check_index_exists()
            
            logger.info(f"\nColunas existentes: {existing_cols}")
            logger.info(f"Colunas faltando: {missing_cols}")
            logger.info(f"Índice existe: {index_exists}")
            
            if not missing_cols and index_exists:
                logger.info("\n✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                return True
            else:
                logger.error("\n✗ Erro: Algumas colunas ou índice ainda estão faltando")
                return False
                
        except Exception as e:
            logger.error(f"\n✗ Erro ao aplicar migração: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False


def test_migration():
    """Testa a migração criando e consultando um convite"""
    with app.app_context():
        try:
            logger.info("\n" + "=" * 60)
            logger.info("TESTANDO MIGRAÇÃO")
            logger.info("=" * 60)
            
            # Buscar um convite existente ou criar um de teste
            invite = Invite.query.first()
            
            if invite:
                logger.info(f"\nTestando com convite existente ID: {invite.id}")
                logger.info(f"  - client_accepted: {invite.client_accepted}")
                logger.info(f"  - client_accepted_at: {invite.client_accepted_at}")
                logger.info(f"  - provider_accepted: {invite.provider_accepted}")
                logger.info(f"  - provider_accepted_at: {invite.provider_accepted_at}")
                logger.info(f"  - is_mutually_accepted: {invite.is_mutually_accepted}")
                logger.info(f"  - pending_acceptance_from: {invite.pending_acceptance_from}")
                
                logger.info("\n✓ Campos acessíveis e funcionando corretamente!")
                return True
            else:
                logger.info("\nNenhum convite encontrado para testar, mas estrutura está OK")
                return True
                
        except Exception as e:
            logger.error(f"\n✗ Erro ao testar migração: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    logger.info("\n" + "=" * 60)
    logger.info("MIGRAÇÃO: Campos de Aceitação Mútua para Invites")
    logger.info("=" * 60)
    
    # Aplicar migração
    if not apply_migration():
        logger.error("\n✗ Falha ao aplicar migração")
        sys.exit(1)
    
    # Testar migração
    if not test_migration():
        logger.error("\n✗ Falha ao testar migração")
        sys.exit(1)
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ MIGRAÇÃO COMPLETA E TESTADA COM SUCESSO!")
    logger.info("=" * 60)
    logger.info("\nNovos campos adicionados ao modelo Invite:")
    logger.info("  - client_accepted (Boolean)")
    logger.info("  - client_accepted_at (DateTime)")
    logger.info("  - provider_accepted (Boolean)")
    logger.info("  - provider_accepted_at (DateTime)")
    logger.info("\nÍndice criado:")
    logger.info("  - idx_invite_mutual_acceptance (client_accepted, provider_accepted, status)")
    logger.info("\nPropriedades adicionadas:")
    logger.info("  - is_mutually_accepted")
    logger.info("  - pending_acceptance_from")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
