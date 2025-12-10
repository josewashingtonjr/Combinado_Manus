#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Migração: Convites → Pré-Ordens

Este script identifica convites com status 'aceito' sem order_id associado
e os converte em pré-ordens, preservando todos os dados.

Requirements: 16.1-16.5
"""

import sys
import os
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Invite, PreOrder, PreOrderStatus, PreOrderHistory, User
from services.notification_service import NotificationService
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InviteMigrationService:
    """
    Serviço para migração de convites aceitos para pré-ordens
    
    Requirements: 16.1-16.5
    """
    
    # Prazo padrão de negociação (7 dias)
    DEFAULT_NEGOTIATION_DAYS = 7
    
    def __init__(self, dry_run=False):
        """
        Inicializa o serviço de migração
        
        Args:
            dry_run: Se True, apenas simula a migração sem fazer alterações
        """
        self.dry_run = dry_run
        self.stats = {
            'total_found': 0,
            'total_migrated': 0,
            'total_errors': 0,
            'errors': [],
            'migrated_ids': [],
            'start_time': None,
            'end_time': None,
            'execution_time_seconds': 0
        }
    
    def find_eligible_invites(self):
        """
        Identifica convites elegíveis para migração
        
        Critérios:
        - Status 'aceito'
        - Sem order_id associado
        - Ainda não convertido para pré-ordem
        
        Returns:
            list: Lista de convites elegíveis
            
        Requirement: 16.1
        """
        try:
            logger.info("Buscando convites elegíveis para migração...")
            
            # Buscar convites aceitos sem ordem associada
            invites = Invite.query.filter(
                Invite.status == 'aceito',
                Invite.order_id.is_(None)
            ).all()
            
            # Filtrar convites que já têm pré-ordem
            eligible_invites = []
            for invite in invites:
                # Verificar se já existe pré-ordem para este convite
                existing_pre_order = PreOrder.query.filter_by(invite_id=invite.id).first()
                if not existing_pre_order:
                    eligible_invites.append(invite)
                else:
                    logger.debug(
                        f"Convite {invite.id} já possui pré-ordem {existing_pre_order.id}, "
                        f"pulando..."
                    )
            
            self.stats['total_found'] = len(eligible_invites)
            
            logger.info(f"✓ Encontrados {len(eligible_invites)} convites elegíveis para migração")
            
            if eligible_invites:
                logger.info("\nDetalhes dos convites encontrados:")
                for invite in eligible_invites:
                    logger.info(
                        f"  - Convite #{invite.id}: '{invite.service_title}' "
                        f"(Cliente: {invite.client_id}, Valor: R$ {invite.current_value:.2f})"
                    )
            
            return eligible_invites
            
        except Exception as e:
            logger.error(f"Erro ao buscar convites elegíveis: {str(e)}")
            raise
    
    def migrate_invite_to_pre_order(self, invite):
        """
        Migra um convite individual para pré-ordem
        
        Preserva todos os dados do convite e cria registro no histórico.
        
        Args:
            invite: Objeto Invite a ser migrado
            
        Returns:
            dict: Resultado da migração
            
        Requirements: 16.2, 16.3, 16.4
        """
        try:
            logger.info(f"\nMigrando convite #{invite.id}...")
            
            # Buscar prestador pelo telefone do convite
            provider = User.query.filter_by(phone=invite.invited_phone).first()
            if not provider:
                error_msg = f"Prestador não encontrado para o telefone {invite.invited_phone}"
                logger.error(f"  ✗ {error_msg}")
                return {
                    'success': False,
                    'invite_id': invite.id,
                    'error': error_msg
                }
            
            # Calcular data de expiração (7 dias a partir de agora)
            expires_at = datetime.utcnow() + timedelta(days=self.DEFAULT_NEGOTIATION_DAYS)
            
            if self.dry_run:
                logger.info(f"  [DRY-RUN] Criaria pré-ordem:")
                logger.info(f"    - Cliente: {invite.client_id}")
                logger.info(f"    - Prestador: {provider.id} ({provider.nome})")
                logger.info(f"    - Título: {invite.service_title}")
                logger.info(f"    - Valor atual: R$ {invite.current_value:.2f}")
                logger.info(f"    - Valor original: R$ {invite.original_value:.2f}")
                logger.info(f"    - Data de entrega: {invite.delivery_date}")
                logger.info(f"    - Expira em: {expires_at}")
                logger.info(f"  [DRY-RUN] Atualizaria status do convite para 'convertido_pre_ordem'")
                logger.info(f"  [DRY-RUN] Criaria registro no histórico")
                logger.info(f"  [DRY-RUN] Notificaria ambas as partes")
                
                return {
                    'success': True,
                    'invite_id': invite.id,
                    'dry_run': True,
                    'would_create': {
                        'client_id': invite.client_id,
                        'provider_id': provider.id,
                        'title': invite.service_title,
                        'current_value': float(invite.current_value),
                        'original_value': float(invite.original_value)
                    }
                }
            
            # Requirement 16.3: Criar pré-ordem preservando todos os dados
            pre_order = PreOrder(
                invite_id=invite.id,
                client_id=invite.client_id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.current_value,
                original_value=invite.original_value,
                delivery_date=invite.delivery_date,
                service_category=invite.service_category,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=expires_at,
                client_accepted_terms=False,
                provider_accepted_terms=False,
                has_active_proposal=False
            )
            
            db.session.add(pre_order)
            db.session.flush()  # Para obter o ID da pré-ordem
            
            logger.info(f"  ✓ Pré-ordem #{pre_order.id} criada")
            
            # Requirement 16.2: Atualizar status do convite
            invite.status = 'convertido_pre_ordem'
            logger.info(f"  ✓ Status do convite atualizado para 'convertido_pre_ordem'")
            
            # Criar registro no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='created',
                actor_id=None,  # Sistema
                description=f'Pré-ordem criada automaticamente via migração do convite #{invite.id}',
                event_data={
                    'migration': True,
                    'invite_id': invite.id,
                    'initial_value': float(pre_order.current_value),
                    'original_value': float(pre_order.original_value),
                    'delivery_date': pre_order.delivery_date.isoformat(),
                    'expires_at': expires_at.isoformat(),
                    'migrated_at': datetime.utcnow().isoformat()
                }
            )
            db.session.add(history_entry)
            logger.info(f"  ✓ Registro de histórico criado")
            
            # Commit da transação
            db.session.commit()
            
            # Requirement 16.4: Notificar usuários afetados
            try:
                # Notificar cliente
                NotificationService.notify_pre_order_created(
                    pre_order_id=pre_order.id,
                    user_id=invite.client_id,
                    user_type='cliente'
                )
                logger.info(f"  ✓ Cliente {invite.client_id} notificado")
                
                # Notificar prestador
                NotificationService.notify_pre_order_created(
                    pre_order_id=pre_order.id,
                    user_id=provider.id,
                    user_type='prestador'
                )
                logger.info(f"  ✓ Prestador {provider.id} notificado")
                
            except Exception as e:
                # Notificações não devem bloquear a migração
                logger.warning(f"  ⚠ Erro ao enviar notificações: {str(e)}")
            
            logger.info(
                f"  ✓ Convite #{invite.id} migrado com sucesso para pré-ordem #{pre_order.id}"
            )
            
            return {
                'success': True,
                'invite_id': invite.id,
                'pre_order_id': pre_order.id,
                'client_id': invite.client_id,
                'provider_id': provider.id,
                'title': invite.service_title,
                'current_value': float(invite.current_value),
                'original_value': float(invite.original_value),
                'expires_at': expires_at.isoformat()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Erro de banco de dados ao migrar convite {invite.id}: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            return {
                'success': False,
                'invite_id': invite.id,
                'error': error_msg
            }
        except Exception as e:
            db.session.rollback()
            error_msg = f"Erro inesperado ao migrar convite {invite.id}: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            return {
                'success': False,
                'invite_id': invite.id,
                'error': error_msg
            }
    
    def migrate_all(self):
        """
        Executa migração de todos os convites elegíveis
        
        Returns:
            dict: Estatísticas da migração
            
        Requirement: 16.5
        """
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            logger.info("=" * 80)
            logger.info("INICIANDO MIGRAÇÃO: Convites → Pré-Ordens")
            if self.dry_run:
                logger.info("MODO: DRY-RUN (Simulação - Nenhuma alteração será feita)")
            logger.info("=" * 80)
            logger.info(f"Início: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("")
            
            # Buscar convites elegíveis
            eligible_invites = self.find_eligible_invites()
            
            if not eligible_invites:
                logger.info("\n✓ Nenhum convite elegível encontrado. Migração não necessária.")
                self.stats['end_time'] = datetime.utcnow()
                self.stats['execution_time_seconds'] = (
                    self.stats['end_time'] - self.stats['start_time']
                ).total_seconds()
                return self.stats
            
            logger.info(f"\nIniciando migração de {len(eligible_invites)} convites...")
            logger.info("=" * 80)
            
            # Migrar cada convite
            for i, invite in enumerate(eligible_invites, 1):
                logger.info(f"\n[{i}/{len(eligible_invites)}] Processando convite #{invite.id}...")
                
                result = self.migrate_invite_to_pre_order(invite)
                
                if result['success']:
                    self.stats['total_migrated'] += 1
                    self.stats['migrated_ids'].append(invite.id)
                else:
                    self.stats['total_errors'] += 1
                    self.stats['errors'].append({
                        'invite_id': invite.id,
                        'error': result.get('error', 'Erro desconhecido')
                    })
            
            self.stats['end_time'] = datetime.utcnow()
            self.stats['execution_time_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()
            
            # Exibir resumo
            self._print_summary()
            
            # Requirement 16.5: Gerar relatório JSON
            self._generate_report()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"\n✗ Erro crítico durante migração: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.stats['end_time'] = datetime.utcnow()
            self.stats['execution_time_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()
            
            return self.stats
    
    def _print_summary(self):
        """Exibe resumo da migração"""
        logger.info("\n" + "=" * 80)
        logger.info("RESUMO DA MIGRAÇÃO")
        logger.info("=" * 80)
        logger.info(f"Modo: {'DRY-RUN (Simulação)' if self.dry_run else 'PRODUÇÃO'}")
        logger.info(f"Convites encontrados: {self.stats['total_found']}")
        logger.info(f"Convites migrados: {self.stats['total_migrated']}")
        logger.info(f"Erros: {self.stats['total_errors']}")
        logger.info(f"Tempo de execução: {self.stats['execution_time_seconds']:.2f} segundos")
        
        if self.stats['migrated_ids']:
            logger.info(f"\nConvites migrados: {self.stats['migrated_ids']}")
        
        if self.stats['errors']:
            logger.info(f"\nErros encontrados:")
            for error in self.stats['errors']:
                logger.info(f"  - Convite #{error['invite_id']}: {error['error']}")
        
        if self.stats['total_errors'] == 0 and self.stats['total_migrated'] > 0:
            logger.info("\n✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        elif self.stats['total_errors'] > 0:
            logger.warning(
                f"\n⚠ MIGRAÇÃO CONCLUÍDA COM {self.stats['total_errors']} ERRO(S)"
            )
        
        logger.info("=" * 80)
    
    def _generate_report(self):
        """
        Gera relatório JSON com estatísticas da migração
        
        Requirement: 16.5
        """
        report_filename = f"migration_report_invites_to_pre_orders_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'migration_type': 'invites_to_pre_orders',
            'dry_run': self.dry_run,
            'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
            'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None,
            'execution_time_seconds': self.stats['execution_time_seconds'],
            'statistics': {
                'total_found': self.stats['total_found'],
                'total_migrated': self.stats['total_migrated'],
                'total_errors': self.stats['total_errors'],
                'success_rate': (
                    (self.stats['total_migrated'] / self.stats['total_found'] * 100)
                    if self.stats['total_found'] > 0 else 0
                )
            },
            'migrated_invite_ids': self.stats['migrated_ids'],
            'errors': self.stats['errors']
        }
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n✓ Relatório JSON gerado: {report_filename}")
            
        except Exception as e:
            logger.error(f"\n✗ Erro ao gerar relatório JSON: {str(e)}")
    
    def rollback(self):
        """
        Implementa rollback em caso de erro
        
        Requirement: 16.5
        """
        try:
            logger.warning("\nExecutando rollback...")
            db.session.rollback()
            logger.info("✓ Rollback executado com sucesso")
        except Exception as e:
            logger.error(f"✗ Erro ao executar rollback: {str(e)}")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migração de Convites Aceitos para Pré-Ordens'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Executa em modo simulação sem fazer alterações no banco'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirma execução em modo produção (obrigatório se não for dry-run)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.dry_run and not args.confirm:
        print("\n❌ ERRO: Para executar em modo produção, use --confirm")
        print("   Para simular sem fazer alterações, use --dry-run")
        print("\nExemplos:")
        print("  python migrate_invites_to_pre_orders.py --dry-run")
        print("  python migrate_invites_to_pre_orders.py --confirm")
        sys.exit(1)
    
    # Executar migração
    with app.app_context():
        migration_service = InviteMigrationService(dry_run=args.dry_run)
        
        try:
            stats = migration_service.migrate_all()
            
            # Determinar código de saída
            if stats['total_errors'] > 0:
                sys.exit(1)
            else:
                sys.exit(0)
                
        except KeyboardInterrupt:
            logger.warning("\n\n⚠ Migração interrompida pelo usuário")
            migration_service.rollback()
            sys.exit(2)
        except Exception as e:
            logger.error(f"\n✗ Erro fatal: {str(e)}")
            migration_service.rollback()
            sys.exit(1)


if __name__ == '__main__':
    main()
