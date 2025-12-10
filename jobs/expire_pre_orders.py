#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Job de Expiração de Pré-Ordens

Este job é executado periodicamente (a cada hora) para:
1. Verificar pré-ordens próximas da expiração (24h)
2. Enviar notificações de aviso
3. Marcar pré-ordens expiradas automaticamente
4. Enviar notificações de expiração

Requirements: 15.1-15.5
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, PreOrder, PreOrderStatus, PreOrderHistory
from services.notification_service import NotificationService
from services.pre_order_state_manager import PreOrderStateManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/expire_pre_orders.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PreOrderExpirationJob:
    """
    Job para gerenciar expiração de pré-ordens
    
    Responsável por:
    - Notificar pré-ordens próximas da expiração (24h)
    - Marcar pré-ordens expiradas automaticamente
    - Registrar eventos no histórico
    - Enviar notificações às partes envolvidas
    """
    
    @staticmethod
    def check_expiring_soon():
        """
        Verifica pré-ordens que expirarão em 24 horas
        
        Envia notificação de aviso para ambas as partes.
        
        Requirement 15.2: Notificação 24h antes da expiração
        """
        try:
            # Calcular janela de tempo: entre 23h e 25h a partir de agora
            # (para evitar notificações duplicadas)
            now = datetime.utcnow()
            warning_start = now + timedelta(hours=23)
            warning_end = now + timedelta(hours=25)
            
            # Buscar pré-ordens que expirarão nas próximas 24h
            expiring_soon = PreOrder.query.filter(
                PreOrder.expires_at.between(warning_start, warning_end),
                PreOrder.status.in_([
                    PreOrderStatus.EM_NEGOCIACAO.value,
                    PreOrderStatus.AGUARDANDO_RESPOSTA.value
                ])
            ).all()
            
            logger.info(f"Verificando pré-ordens próximas da expiração: {len(expiring_soon)} encontradas")
            
            notified_count = 0
            
            for pre_order in expiring_soon:
                try:
                    # Verificar se já foi enviada notificação de aviso
                    # (checando histórico para evitar duplicatas)
                    existing_warning = PreOrderHistory.query.filter_by(
                        pre_order_id=pre_order.id,
                        event_type='expiration_warning'
                    ).first()
                    
                    if existing_warning:
                        logger.debug(f"Pré-ordem {pre_order.id} já possui notificação de aviso")
                        continue
                    
                    # Calcular horas restantes
                    time_remaining = pre_order.expires_at - now
                    hours_remaining = int(time_remaining.total_seconds() / 3600)
                    
                    # Registrar aviso no histórico
                    history_entry = PreOrderHistory(
                        pre_order_id=pre_order.id,
                        event_type='expiration_warning',
                        actor_id=None,  # Sistema
                        description=f'Aviso de expiração: faltam {hours_remaining}h para expirar',
                        event_data={
                            'hours_remaining': hours_remaining,
                            'expires_at': pre_order.expires_at.isoformat(),
                            'current_status': pre_order.status
                        }
                    )
                    db.session.add(history_entry)
                    
                    # Enviar notificações
                    NotificationService.notify_pre_order_expiring_soon(
                        pre_order_id=pre_order.id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id,
                        hours_remaining=hours_remaining
                    )
                    
                    notified_count += 1
                    
                    logger.info(
                        f"Notificação de expiração enviada - Pré-ordem: {pre_order.id}, "
                        f"Expira em: {hours_remaining}h"
                    )
                    
                except Exception as e:
                    logger.error(f"Erro ao notificar pré-ordem {pre_order.id}: {str(e)}")
                    continue
            
            db.session.commit()
            
            logger.info(f"Notificações de aviso enviadas: {notified_count}")
            
            return {
                'success': True,
                'checked': len(expiring_soon),
                'notified': notified_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao verificar pré-ordens expirando: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def expire_overdue():
        """
        Marca pré-ordens expiradas automaticamente
        
        Busca pré-ordens que ultrapassaram o prazo e marca como expiradas.
        
        Requirements 15.3, 15.4: Marcar como expirada e notificar
        """
        try:
            now = datetime.utcnow()
            
            # Buscar pré-ordens que já expiraram
            expired_pre_orders = PreOrder.query.filter(
                PreOrder.expires_at < now,
                PreOrder.status.in_([
                    PreOrderStatus.EM_NEGOCIACAO.value,
                    PreOrderStatus.AGUARDANDO_RESPOSTA.value,
                    PreOrderStatus.PRONTO_CONVERSAO.value  # Mesmo pronto, se não converteu, expira
                ])
            ).all()
            
            logger.info(f"Verificando pré-ordens expiradas: {len(expired_pre_orders)} encontradas")
            
            expired_count = 0
            
            for pre_order in expired_pre_orders:
                try:
                    previous_status = pre_order.status
                    
                    # Requirement 15.3: Marcar como expirada
                    PreOrderStateManager.transition_to(
                        pre_order_id=pre_order.id,
                        new_status=PreOrderStatus.EXPIRADA,
                        actor_id=None,  # Sistema
                        reason=f'Prazo de negociação expirado (era {previous_status})'
                    )
                    
                    # Registrar no histórico
                    history_entry = PreOrderHistory(
                        pre_order_id=pre_order.id,
                        event_type='expired',
                        actor_id=None,  # Sistema
                        description='Pré-ordem expirada automaticamente por ultrapassar prazo',
                        event_data={
                            'expired_at': now.isoformat(),
                            'expires_at': pre_order.expires_at.isoformat(),
                            'previous_status': previous_status,
                            'days_overdue': (now - pre_order.expires_at).days
                        }
                    )
                    db.session.add(history_entry)
                    
                    # Requirement 15.4: Notificar ambas as partes
                    NotificationService.notify_pre_order_expired(
                        pre_order_id=pre_order.id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id
                    )
                    
                    expired_count += 1
                    
                    logger.info(
                        f"Pré-ordem {pre_order.id} marcada como expirada. "
                        f"Status anterior: {previous_status}, "
                        f"Expirou em: {pre_order.expires_at}"
                    )
                    
                except Exception as e:
                    logger.error(f"Erro ao expirar pré-ordem {pre_order.id}: {str(e)}")
                    continue
            
            db.session.commit()
            
            logger.info(f"Pré-ordens expiradas: {expired_count}")
            
            return {
                'success': True,
                'checked': len(expired_pre_orders),
                'expired': expired_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao expirar pré-ordens: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def run():
        """
        Executa o job completo de expiração
        
        1. Verifica pré-ordens próximas da expiração (24h)
        2. Marca pré-ordens expiradas
        
        Este método deve ser chamado pelo scheduler a cada hora.
        """
        logger.info("=" * 80)
        logger.info("Iniciando job de expiração de pré-ordens")
        logger.info("=" * 80)
        
        start_time = datetime.utcnow()
        
        # Etapa 1: Notificar pré-ordens próximas da expiração
        logger.info("Etapa 1: Verificando pré-ordens próximas da expiração...")
        expiring_result = PreOrderExpirationJob.check_expiring_soon()
        
        # Etapa 2: Marcar pré-ordens expiradas
        logger.info("Etapa 2: Marcando pré-ordens expiradas...")
        expired_result = PreOrderExpirationJob.expire_overdue()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Resumo da execução
        logger.info("=" * 80)
        logger.info("Job de expiração concluído")
        logger.info(f"Duração: {duration:.2f}s")
        logger.info(f"Avisos enviados: {expiring_result.get('notified', 0)}")
        logger.info(f"Pré-ordens expiradas: {expired_result.get('expired', 0)}")
        logger.info("=" * 80)
        
        return {
            'success': expiring_result['success'] and expired_result['success'],
            'duration_seconds': duration,
            'expiring_checked': expiring_result.get('checked', 0),
            'expiring_notified': expiring_result.get('notified', 0),
            'expired_checked': expired_result.get('checked', 0),
            'expired_count': expired_result.get('expired', 0),
            'timestamp': end_time.isoformat()
        }


def main():
    """Função principal para execução standalone do job"""
    with app.app_context():
        try:
            result = PreOrderExpirationJob.run()
            
            if result['success']:
                logger.info("Job executado com sucesso")
                sys.exit(0)
            else:
                logger.error("Job falhou")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Erro fatal ao executar job: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    main()
