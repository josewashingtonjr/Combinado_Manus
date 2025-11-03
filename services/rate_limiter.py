#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rate Limiter Simples
Implementação de rate limiting sem dependências externas
"""

from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, flash, redirect, url_for
import logging

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """
    Rate limiter simples baseado em memória
    
    Nota: Para produção, considere usar Redis ou Flask-Limiter
    """
    
    def __init__(self):
        # Dicionário para armazenar tentativas: {key: [(timestamp, count)]}
        self.attempts = {}
        self.cleanup_interval = timedelta(hours=1)
        self.last_cleanup = datetime.utcnow()
    
    def _get_key(self, identifier, endpoint):
        """Gera chave única para identificador e endpoint"""
        return f"{identifier}:{endpoint}"
    
    def _cleanup_old_attempts(self):
        """Remove tentativas antigas para liberar memória"""
        now = datetime.utcnow()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff = now - timedelta(hours=24)
        keys_to_remove = []
        
        for key, attempts in self.attempts.items():
            # Remover tentativas antigas
            self.attempts[key] = [
                (timestamp, count) for timestamp, count in attempts
                if timestamp > cutoff
            ]
            # Se não sobrou nenhuma tentativa, marcar chave para remoção
            if not self.attempts[key]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.attempts[key]
        
        self.last_cleanup = now
        logger.info(f"Cleanup: {len(keys_to_remove)} chaves removidas")
    
    def is_rate_limited(self, identifier, endpoint, max_attempts, window_minutes):
        """
        Verifica se o identificador atingiu o limite de tentativas
        
        Args:
            identifier: IP, user_id, email, etc.
            endpoint: Nome do endpoint
            max_attempts: Número máximo de tentativas
            window_minutes: Janela de tempo em minutos
            
        Returns:
            tuple: (is_limited: bool, remaining: int, reset_at: datetime)
        """
        self._cleanup_old_attempts()
        
        key = self._get_key(identifier, endpoint)
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Obter tentativas dentro da janela de tempo
        if key not in self.attempts:
            self.attempts[key] = []
        
        # Filtrar tentativas dentro da janela
        recent_attempts = [
            (timestamp, count) for timestamp, count in self.attempts[key]
            if timestamp > window_start
        ]
        
        # Calcular total de tentativas
        total_attempts = sum(count for _, count in recent_attempts)
        
        # Verificar se atingiu o limite
        is_limited = total_attempts >= max_attempts
        remaining = max(0, max_attempts - total_attempts)
        
        # Calcular quando o limite será resetado
        if recent_attempts:
            oldest_attempt = min(timestamp for timestamp, _ in recent_attempts)
            reset_at = oldest_attempt + timedelta(minutes=window_minutes)
        else:
            reset_at = now + timedelta(minutes=window_minutes)
        
        return is_limited, remaining, reset_at
    
    def record_attempt(self, identifier, endpoint, count=1):
        """
        Registra uma tentativa
        
        Args:
            identifier: IP, user_id, email, etc.
            endpoint: Nome do endpoint
            count: Número de tentativas a registrar (padrão: 1)
        """
        key = self._get_key(identifier, endpoint)
        now = datetime.utcnow()
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        self.attempts[key].append((now, count))
        
        logger.debug(f"Tentativa registrada: {key} (+{count})")
    
    def reset_attempts(self, identifier, endpoint):
        """
        Reseta tentativas para um identificador e endpoint
        
        Args:
            identifier: IP, user_id, email, etc.
            endpoint: Nome do endpoint
        """
        key = self._get_key(identifier, endpoint)
        if key in self.attempts:
            del self.attempts[key]
            logger.info(f"Tentativas resetadas: {key}")
    
    def get_stats(self):
        """Retorna estatísticas do rate limiter"""
        total_keys = len(self.attempts)
        total_attempts = sum(
            sum(count for _, count in attempts)
            for attempts in self.attempts.values()
        )
        return {
            'total_keys': total_keys,
            'total_attempts': total_attempts,
            'last_cleanup': self.last_cleanup.isoformat()
        }


# Instância global do rate limiter
rate_limiter = SimpleRateLimiter()


# ==============================================================================
#  DECORADORES
# ==============================================================================

def rate_limit(max_attempts=5, window_minutes=15, identifier_func=None):
    """
    Decorador para aplicar rate limiting em rotas
    
    Args:
        max_attempts: Número máximo de tentativas
        window_minutes: Janela de tempo em minutos
        identifier_func: Função para obter identificador (padrão: IP)
        
    Exemplo:
        @rate_limit(max_attempts=5, window_minutes=15)
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Obter identificador
            if identifier_func:
                identifier = identifier_func()
            else:
                identifier = request.remote_addr
            
            endpoint = f.__name__
            
            # Verificar rate limit
            is_limited, remaining, reset_at = rate_limiter.is_rate_limited(
                identifier, endpoint, max_attempts, window_minutes
            )
            
            if is_limited:
                minutes_until_reset = int((reset_at - datetime.utcnow()).total_seconds() / 60)
                
                logger.warning(
                    f"Rate limit atingido: {identifier} em {endpoint} "
                    f"(reset em {minutes_until_reset} minutos)"
                )
                
                # Retornar erro apropriado
                if request.is_json:
                    return jsonify({
                        'error': 'rate_limit_exceeded',
                        'message': f'Muitas tentativas. Tente novamente em {minutes_until_reset} minutos.',
                        'reset_at': reset_at.isoformat(),
                        'remaining': 0
                    }), 429
                else:
                    flash(
                        f'Muitas tentativas. Tente novamente em {minutes_until_reset} minutos.',
                        'error'
                    )
                    return redirect(request.referrer or url_for('home.index'))
            
            # Registrar tentativa
            rate_limiter.record_attempt(identifier, endpoint)
            
            # Executar função
            return f(*args, **kwargs)
        
        return wrapped
    return decorator


def auth_rate_limit(max_attempts=5, window_minutes=15):
    """
    Decorador específico para rotas de autenticação
    Usa email como identificador quando disponível
    
    Args:
        max_attempts: Número máximo de tentativas
        window_minutes: Janela de tempo em minutos
    """
    def get_auth_identifier():
        # Tentar obter email do formulário
        email = request.form.get('email') or request.json.get('email') if request.is_json else None
        if email:
            return f"email:{email}"
        # Fallback para IP
        return f"ip:{request.remote_addr}"
    
    return rate_limit(
        max_attempts=max_attempts,
        window_minutes=window_minutes,
        identifier_func=get_auth_identifier
    )


def reset_auth_rate_limit(email=None):
    """
    Reseta rate limit de autenticação após login bem-sucedido
    
    Args:
        email: Email do usuário (opcional)
    """
    if email:
        identifier = f"email:{email}"
    else:
        identifier = f"ip:{request.remote_addr}"
    
    # Resetar para endpoints comuns de autenticação
    for endpoint in ['user_login', 'admin_login', 'login']:
        rate_limiter.reset_attempts(identifier, endpoint)

