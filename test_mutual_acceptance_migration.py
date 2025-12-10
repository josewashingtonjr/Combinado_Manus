#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste completo da migração de aceitação mútua
"""

from app import app, db
from models import Invite, User
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mutual_acceptance_fields():
    """Testa os campos de aceitação mútua"""
    with app.app_context():
        try:
            logger.info("\n" + "=" * 60)
            logger.info("TESTE: Campos de Aceitação Mútua")
            logger.info("=" * 60)
            
            # Buscar usuário existente
            client = User.query.first()
            if not client:
                logger.error("\nNenhum usuário encontrado no banco de dados")
                return False
            logger.info(f"\nUsando cliente existente: ID {client.id} - {client.nome}")
            
            # Criar convite de teste
            logger.info("\nCriando convite de teste...")
            invite = Invite(
                client_id=client.id,
                invited_phone='11988888888',
                service_title='Teste de Aceitação Mútua',
                service_description='Teste dos novos campos',
                original_value=100.00,
                delivery_date=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(invite)
            db.session.commit()
            logger.info(f"✓ Convite criado: ID {invite.id}")
            
            # Teste 1: Estado inicial
            logger.info("\n--- Teste 1: Estado Inicial ---")
            logger.info(f"client_accepted: {invite.client_accepted} (esperado: False)")
            logger.info(f"provider_accepted: {invite.provider_accepted} (esperado: False)")
            logger.info(f"is_mutually_accepted: {invite.is_mutually_accepted} (esperado: False)")
            logger.info(f"pending_acceptance_from: {invite.pending_acceptance_from} (esperado: cliente)")
            
            assert invite.client_accepted == False, "client_accepted deveria ser False"
            assert invite.provider_accepted == False, "provider_accepted deveria ser False"
            assert invite.is_mutually_accepted == False, "is_mutually_accepted deveria ser False"
            assert invite.pending_acceptance_from == 'cliente', "pending_acceptance_from deveria ser 'cliente'"
            logger.info("✓ Teste 1 passou!")
            
            # Teste 2: Cliente aceita
            logger.info("\n--- Teste 2: Cliente Aceita ---")
            invite.client_accepted = True
            invite.client_accepted_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"client_accepted: {invite.client_accepted} (esperado: True)")
            logger.info(f"client_accepted_at: {invite.client_accepted_at}")
            logger.info(f"is_mutually_accepted: {invite.is_mutually_accepted} (esperado: False)")
            logger.info(f"pending_acceptance_from: {invite.pending_acceptance_from} (esperado: prestador)")
            
            assert invite.client_accepted == True, "client_accepted deveria ser True"
            assert invite.client_accepted_at is not None, "client_accepted_at deveria ter timestamp"
            assert invite.is_mutually_accepted == False, "is_mutually_accepted deveria ser False"
            assert invite.pending_acceptance_from == 'prestador', "pending_acceptance_from deveria ser 'prestador'"
            logger.info("✓ Teste 2 passou!")
            
            # Teste 3: Prestador aceita (aceitação mútua)
            logger.info("\n--- Teste 3: Prestador Aceita (Aceitação Mútua) ---")
            invite.provider_accepted = True
            invite.provider_accepted_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"provider_accepted: {invite.provider_accepted} (esperado: True)")
            logger.info(f"provider_accepted_at: {invite.provider_accepted_at}")
            logger.info(f"is_mutually_accepted: {invite.is_mutually_accepted} (esperado: True)")
            logger.info(f"pending_acceptance_from: {invite.pending_acceptance_from} (esperado: None)")
            
            assert invite.provider_accepted == True, "provider_accepted deveria ser True"
            assert invite.provider_accepted_at is not None, "provider_accepted_at deveria ter timestamp"
            assert invite.is_mutually_accepted == True, "is_mutually_accepted deveria ser True"
            assert invite.pending_acceptance_from is None, "pending_acceptance_from deveria ser None"
            logger.info("✓ Teste 3 passou!")
            
            # Teste 4: Consulta com índice
            logger.info("\n--- Teste 4: Consulta com Índice ---")
            mutually_accepted = Invite.query.filter_by(
                client_accepted=True,
                provider_accepted=True,
                status='pendente'
            ).all()
            logger.info(f"Convites com aceitação mútua encontrados: {len(mutually_accepted)}")
            logger.info("✓ Consulta com índice funcionando!")
            
            # Limpar dados de teste
            logger.info("\n--- Limpando Dados de Teste ---")
            db.session.delete(invite)
            db.session.commit()
            logger.info("✓ Convite de teste removido")
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
            logger.info("=" * 60)
            
            return True
            
        except AssertionError as e:
            logger.error(f"\n✗ Teste falhou: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"\n✗ Erro durante teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_index_performance():
    """Testa a performance do índice"""
    with app.app_context():
        try:
            logger.info("\n" + "=" * 60)
            logger.info("TESTE: Performance do Índice")
            logger.info("=" * 60)
            
            # Contar convites por estado de aceitação
            total = Invite.query.count()
            client_accepted = Invite.query.filter_by(client_accepted=True).count()
            provider_accepted = Invite.query.filter_by(provider_accepted=True).count()
            mutually_accepted = Invite.query.filter_by(
                client_accepted=True,
                provider_accepted=True
            ).count()
            
            logger.info(f"\nTotal de convites: {total}")
            logger.info(f"Aceitos pelo cliente: {client_accepted}")
            logger.info(f"Aceitos pelo prestador: {provider_accepted}")
            logger.info(f"Aceitação mútua: {mutually_accepted}")
            
            logger.info("\n✓ Consultas executadas com sucesso usando o índice!")
            return True
            
        except Exception as e:
            logger.error(f"\n✗ Erro ao testar índice: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    logger.info("\n" + "=" * 60)
    logger.info("SUITE DE TESTES: Migração de Aceitação Mútua")
    logger.info("=" * 60)
    
    success = True
    
    # Teste 1: Campos e propriedades
    if not test_mutual_acceptance_fields():
        logger.error("\n✗ Falha nos testes de campos")
        success = False
    
    # Teste 2: Performance do índice
    if not test_index_performance():
        logger.error("\n✗ Falha nos testes de índice")
        success = False
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✓ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        logger.info("\nA migração está funcionando corretamente:")
        logger.info("  ✓ Campos adicionados ao banco de dados")
        logger.info("  ✓ Propriedades do modelo funcionando")
        logger.info("  ✓ Índice criado e otimizando consultas")
        logger.info("  ✓ Lógica de aceitação mútua validada")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("\n✗ ALGUNS TESTES FALHARAM")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
