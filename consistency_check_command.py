#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Comando para Verificação Periódica de Consistência

Este script pode ser executado periodicamente (via cron) para verificar
e corrigir automaticamente inconsistências no sistema de propostas.

Requirements: 4.4 - Validação de integridade de dados contínua
"""

import sys
import os
import argparse
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.error_recovery_service import ErrorRecoveryService
from services.notification_service import NotificationService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consistency_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_consistency_check(auto_fix=False, notify_admin=True, report_file=None):
    """
    Executa verificação de consistência
    
    Args:
        auto_fix: Se deve tentar corrigir automaticamente
        notify_admin: Se deve notificar administradores
        report_file: Arquivo para salvar relatório
    """
    logger.info("Iniciando verificação de consistência do sistema")
    
    try:
        # Executar verificação
        result = ErrorRecoveryService.run_consistency_check()
        
        if result.get('success'):
            inconsistencies_count = result.get('inconsistencies_detected', 0)
            recoveries_count = result.get('automatic_recoveries', 0)
            successful_recoveries = result.get('successful_recoveries', 0)
            
            logger.info(f"Verificação concluída:")
            logger.info(f"  - Inconsistências detectadas: {inconsistencies_count}")
            logger.info(f"  - Recuperações tentadas: {recoveries_count}")
            logger.info(f"  - Recuperações bem-sucedidas: {successful_recoveries}")
            
            # Salvar relatório se solicitado
            if report_file:
                with open(report_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                logger.info(f"Relatório salvo em: {report_file}")
            
            # Notificar administradores se houver problemas críticos
            if notify_admin and inconsistencies_count > 0:
                critical_issues = [
                    inc for inc in result.get('inconsistencies', [])
                    if inc.get('severity') in ['high', 'critical']
                ]
                
                if critical_issues:
                    try:
                        # Notificar administradores sobre problemas críticos
                        admin_message = f"""
Verificação de Consistência - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Problemas críticos detectados: {len(critical_issues)}
Total de inconsistências: {inconsistencies_count}
Recuperações automáticas: {successful_recoveries}/{recoveries_count}

Problemas críticos:
""" + "\n".join([f"- {issue['description']}" for issue in critical_issues])
                        
                        # Aqui você pode implementar notificação por email, Slack, etc.
                        logger.warning("Problemas críticos detectados - notificação de admin necessária")
                        logger.warning(admin_message)
                        
                    except Exception as e:
                        logger.error(f"Erro ao notificar administradores: {e}")
            
            return True
            
        else:
            logger.error(f"Verificação de consistência falhou: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Erro durante verificação de consistência: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Verificação de Consistência do Sistema')
    
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Tentar corrigir automaticamente inconsistências críticas'
    )
    
    parser.add_argument(
        '--no-notify',
        action='store_true',
        help='Não notificar administradores sobre problemas'
    )
    
    parser.add_argument(
        '--report-file',
        type=str,
        help='Arquivo para salvar relatório detalhado'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Logging mais detalhado'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        success = run_consistency_check(
            auto_fix=args.auto_fix,
            notify_admin=not args.no_notify,
            report_file=args.report_file
        )
        
        if success:
            logger.info("Verificação de consistência concluída com sucesso")
            sys.exit(0)
        else:
            logger.error("Verificação de consistência falhou")
            sys.exit(1)

if __name__ == '__main__':
    main()