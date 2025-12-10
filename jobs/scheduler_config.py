#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Configuração do Scheduler para Jobs Agendados

Este módulo configura o APScheduler para executar jobs periódicos.
Para usar, importe e inicialize no app.py:

    from jobs.scheduler_config import init_scheduler
    init_scheduler(app)

Requirements: 15.1-15.5
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import atexit

logger = logging.getLogger(__name__)


def init_scheduler(app):
    """
    Inicializa o scheduler com todos os jobs agendados
    
    Args:
        app: Instância da aplicação Flask
    """
    # Criar scheduler em background
    scheduler = BackgroundScheduler(
        daemon=True,
        timezone='America/Sao_Paulo'
    )
    
    # Importar job dentro da função para evitar import circular
    from jobs.expire_pre_orders import PreOrderExpirationJob
    
    # Job 1: Expirar pré-ordens (a cada hora)
    scheduler.add_job(
        func=lambda: run_job_with_context(app, PreOrderExpirationJob.run),
        trigger=IntervalTrigger(hours=1),
        id='expire_pre_orders',
        name='Expirar Pré-Ordens',
        replace_existing=True,
        max_instances=1  # Evitar execuções simultâneas
    )
    
    # Iniciar scheduler
    scheduler.start()
    logger.info("Scheduler iniciado com sucesso")
    logger.info(f"Jobs agendados: {len(scheduler.get_jobs())}")
    
    # Garantir que o scheduler seja desligado ao encerrar a aplicação
    atexit.register(lambda: shutdown_scheduler(scheduler))
    
    return scheduler


def run_job_with_context(app, job_func):
    """
    Executa um job dentro do contexto da aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
        job_func: Função do job a ser executada
    """
    with app.app_context():
        try:
            result = job_func()
            logger.info(f"Job executado com sucesso: {result}")
            return result
        except Exception as e:
            logger.error(f"Erro ao executar job: {str(e)}")
            raise


def shutdown_scheduler(scheduler):
    """
    Desliga o scheduler de forma segura
    
    Args:
        scheduler: Instância do scheduler
    """
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler desligado com sucesso")


# Exemplo de uso alternativo com Cron (horários específicos)
def init_scheduler_with_cron(app):
    """
    Versão alternativa usando triggers cron para horários específicos
    
    Exemplo: executar às 00:00, 06:00, 12:00, 18:00
    """
    scheduler = BackgroundScheduler(
        daemon=True,
        timezone='America/Sao_Paulo'
    )
    
    from jobs.expire_pre_orders import PreOrderExpirationJob
    
    # Executar 4 vezes por dia em horários específicos
    scheduler.add_job(
        func=lambda: run_job_with_context(app, PreOrderExpirationJob.run),
        trigger=CronTrigger(hour='0,6,12,18', minute=0),
        id='expire_pre_orders',
        name='Expirar Pré-Ordens',
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    logger.info("Scheduler (cron) iniciado com sucesso")
    
    atexit.register(lambda: shutdown_scheduler(scheduler))
    
    return scheduler
