#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Rate Limiting

Este módulo fornece rate limiting para proteger o sistema contra abuso.
Usa Flask-Limiter para controlar taxa de requisições.

Requirements: Security considerations, Task 23
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import request, session
import logging

logger = logging.getLogger(__name__)


def get_user_identifier():
    """
    Obtém identificador único do usuário para rate limiting
    
    Prioridade:
    1. user_id da sessão (se autenticado)
    2. IP address (se não autenticado)
    
    Returns:
        str: Identificador único do usuário
    """
    # Se usuário está autenticado, usar user_id
    if 'user_id' in session:
        return f"user_{session['user_id']}"
    
    # Caso contrário, usar IP address
    return get_remote_address()


# Configurar limiter
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # Em produção, usar Redis: "redis://localhost:6379"
    strategy="fixed-window",
    headers_enabled=True,
)


class RateLimitConfig:
    """Configurações de rate limiting para diferentes ações"""
    
    # Limites gerais
    GENERAL_REQUESTS = "20 per minute"
    
    # Limites para pré-ordens
    PRE_ORDER_PROPOSALS = "10 per hour"  # Máximo 10 propostas por hora
    PRE_ORDER_CANCELLATIONS = "5 per day"  # Máximo 5 cancelamentos por dia
    PRE_ORDER_VIEW = "60 per minute"  # Visualizações
    
    # Limites para ações críticas
    ACCEPT_TERMS = "20 per hour"  # Aceitar termos
    REJECT_PROPOSAL = "30 per hour"  # Rejeitar propostas
    
    # Limites para autenticação
    LOGIN_ATTEMPTS = "5 per 15 minutes"
    PASSWORD_RESET = "3 per hour"
    
    # Limites para uploads
    FILE_UPLOADS = "10 per hour"
    
    # Limites para APIs
    API_CALLS = "100 per hour"


def get_rate_limit_message(limit_type: str) -> str:
    """
    Retorna mensagem amigável para cada tipo de limite
    
    Args:
        limit_type: Tipo de limite atingido
        
    Returns:
        str: Mensagem em português
    """
    messages = {
        'proposals': 'Você atingiu o limite de propostas por hora. Aguarde antes de enviar outra proposta.',
        'cancellations': 'Você atingiu o limite de cancelamentos por dia. Tente novamente amanhã.',
        'general': 'Muitas requisições. Por favor, aguarde alguns minutos antes de tentar novamente.',
        'login': 'Muitas tentativas de login. Aguarde 15 minutos antes de tentar novamente.',
        'api': 'Limite de requisições da API atingido. Aguarde antes de fazer novas requisições.',
    }
    
    return messages.get(limit_type, 'Limite de requisições atingido. Aguarde antes de tentar novamente.')


def log_rate_limit_exceeded(user_id: int = None, action: str = None, ip: str = None):
    """
    Registra quando um rate limit é excedido
    
    Args:
        user_id: ID do usuário (se autenticado)
        action: Ação que foi limitada
        ip: Endereço IP
    """
    identifier = f"User {user_id}" if user_id else f"IP {ip}"
    logger.warning(
        f"Rate limit excedido - {identifier} - Ação: {action or 'geral'}"
    )


# Decoradores customizados para rate limiting específico

def limit_pre_order_proposals():
    """Decorator para limitar propostas de pré-ordem"""
    return limiter.limit(
        RateLimitConfig.PRE_ORDER_PROPOSALS,
        error_message=get_rate_limit_message('proposals')
    )


def limit_pre_order_cancellations():
    """Decorator para limitar cancelamentos de pré-ordem"""
    return limiter.limit(
        RateLimitConfig.PRE_ORDER_CANCELLATIONS,
        error_message=get_rate_limit_message('cancellations')
    )


def limit_general_requests():
    """Decorator para limitar requisições gerais"""
    return limiter.limit(
        RateLimitConfig.GENERAL_REQUESTS,
        error_message=get_rate_limit_message('general')
    )


def limit_login_attempts():
    """Decorator para limitar tentativas de login"""
    return limiter.limit(
        RateLimitConfig.LOGIN_ATTEMPTS,
        error_message=get_rate_limit_message('login')
    )


def limit_api_calls():
    """Decorator para limitar chamadas de API"""
    return limiter.limit(
        RateLimitConfig.API_CALLS,
        error_message=get_rate_limit_message('api')
    )


# Handler de erro para rate limit
def rate_limit_error_handler(e):
    """
    Handler customizado para erros de rate limit
    
    Args:
        e: Exceção de rate limit
        
    Returns:
        Response apropriada (JSON ou HTML)
    """
    from flask import jsonify, render_template
    
    # Se for requisição AJAX/API, retornar JSON
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'error': 'rate_limit_exceeded',
            'message': str(e.description)
        }), 429
    
    # Caso contrário, renderizar página de erro
    return render_template(
        'errors/429.html',
        message=str(e.description)
    ), 429
