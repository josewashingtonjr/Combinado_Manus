#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Job de Confirmação Automática de Ordens
Executa periodicamente para confirmar ordens que ultrapassaram 36h
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.order_management_service import OrderManagementService
import logging

# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'auto_confirm_orders.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_auto_confirmation():
    """Executa o job de confirmação automática"""
    with app.app_context():
        try:
            logger.info("Iniciando job de confirmação automática de ordens...")
            
            result = OrderManagementService.auto_confirm_expired_orders()
            
            logger.info(
                f"Job concluído. Ordens confirmadas: {result['confirmed']} "
                f"de {result['processed']} processadas"
            )
            
            if result['errors']:
                logger.warning(f"Erros encontrados: {len(result['errors'])}")
                for error in result['errors']:
                    logger.error(error)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao executar job de confirmação automática: {e}")
            raise


if __name__ == '__main__':
    run_auto_confirmation()
