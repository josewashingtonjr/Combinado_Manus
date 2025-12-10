#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderCacheService - Serviço de cache para otimização de consultas de pré-ordens

Este serviço implementa um sistema de cache em memória com TTL (Time To Live)
para otimizar consultas frequentes no sistema de pré-ordens.

Funcionalidades:
- Cache de pré-ordens ativas por usuário (TTL: 5 min)
- Cache de histórico de pré-ordens (TTL: 10 min)
- Invalidação automática ao modificar dados
- Limpeza automática de entradas expiradas

Requirements: Performance considerations (Task 22)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import threading
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Entrada de cache com TTL"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return datetime.utcnow() > self.expires_at
    
    def get_value(self) -> Optional[Any]:
        """Retorna o valor se não expirou, None caso contrário"""
        if self.is_expired():
            return None
        return self.value


class PreOrderCacheService:
    """
    Serviço de cache para pré-ordens
    
    Implementa cache em memória com TTL para otimizar consultas frequentes.
    Thread-safe usando locks para operações de escrita.
    """
    
    # TTLs padrão (em segundos)
    TTL_ACTIVE_PRE_ORDERS = 300  # 5 minutos
    TTL_HISTORY = 600  # 10 minutos
    TTL_DETAILS = 180  # 3 minutos
    
    # Armazenamento de cache
    _cache: Dict[str, CacheEntry] = {}
    _lock = threading.Lock()
    
    # Estatísticas
    _stats = {
        'hits': 0,
        'misses': 0,
        'invalidations': 0,
        'cleanups': 0
    }
    
    @classmethod
    def _generate_key(cls, prefix: str, *args) -> str:
        """Gera chave de cache"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ':'.join(key_parts)
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        Obtém valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não existir/expirou
        """
        with cls._lock:
            entry = cls._cache.get(key)
            
            if entry is None:
                cls._stats['misses'] += 1
                return None
            
            value = entry.get_value()
            
            if value is None:
                # Entrada expirada, remover
                del cls._cache[key]
                cls._stats['misses'] += 1
                return None
            
            cls._stats['hits'] += 1
            return value
    
    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: int):
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl_seconds: Tempo de vida em segundos
        """
        with cls._lock:
            cls._cache[key] = CacheEntry(value, ttl_seconds)
    
    @classmethod
    def delete(cls, key: str):
        """
        Remove entrada do cache
        
        Args:
            key: Chave do cache
        """
        with cls._lock:
            if key in cls._cache:
                del cls._cache[key]
                cls._stats['invalidations'] += 1
    
    @classmethod
    def delete_pattern(cls, pattern: str):
        """
        Remove todas as entradas que correspondem ao padrão
        
        Args:
            pattern: Padrão de chave (ex: "pre_order:123:*")
        """
        with cls._lock:
            keys_to_delete = [
                key for key in cls._cache.keys()
                if pattern.replace('*', '') in key
            ]
            
            for key in keys_to_delete:
                del cls._cache[key]
                cls._stats['invalidations'] += 1
    
    @classmethod
    def clear_all(cls):
        """Limpa todo o cache"""
        with cls._lock:
            cls._cache.clear()
            logger.info("Cache de pré-ordens completamente limpo")
    
    @classmethod
    def cleanup_expired(cls):
        """Remove entradas expiradas do cache"""
        with cls._lock:
            expired_keys = [
                key for key, entry in cls._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del cls._cache[key]
            
            if expired_keys:
                cls._stats['cleanups'] += 1
                logger.info(f"Limpeza de cache: {len(expired_keys)} entradas expiradas removidas")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = cls._stats['hits'] + cls._stats['misses']
        hit_rate = (cls._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': cls._stats['hits'],
            'misses': cls._stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'invalidations': cls._stats['invalidations'],
            'cleanups': cls._stats['cleanups'],
            'cache_size': len(cls._cache),
            'total_requests': total_requests
        }
    
    # =========================================================================
    # Métodos específicos para pré-ordens
    # =========================================================================
    
    @classmethod
    def get_active_pre_orders(cls, user_id: int, user_role: str) -> Optional[List[Dict]]:
        """
        Obtém pré-ordens ativas do cache
        
        Args:
            user_id: ID do usuário
            user_role: 'cliente' ou 'prestador'
            
        Returns:
            Lista de pré-ordens ou None se não estiver em cache
        """
        key = cls._generate_key('active_pre_orders', user_id, user_role)
        return cls.get(key)
    
    @classmethod
    def set_active_pre_orders(cls, user_id: int, user_role: str, pre_orders: List[Dict]):
        """
        Armazena pré-ordens ativas no cache
        
        Args:
            user_id: ID do usuário
            user_role: 'cliente' ou 'prestador'
            pre_orders: Lista de pré-ordens
        """
        key = cls._generate_key('active_pre_orders', user_id, user_role)
        cls.set(key, pre_orders, cls.TTL_ACTIVE_PRE_ORDERS)
        logger.debug(f"Cache: pré-ordens ativas armazenadas para usuário {user_id} ({user_role})")
    
    @classmethod
    def invalidate_user_pre_orders(cls, user_id: int):
        """
        Invalida cache de pré-ordens de um usuário
        
        Args:
            user_id: ID do usuário
        """
        cls.delete_pattern(f'active_pre_orders:{user_id}:*')
        logger.debug(f"Cache: pré-ordens do usuário {user_id} invalidadas")
    
    @classmethod
    def get_pre_order_history(cls, pre_order_id: int) -> Optional[List[Dict]]:
        """
        Obtém histórico de pré-ordem do cache
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            Lista de eventos de histórico ou None se não estiver em cache
        """
        key = cls._generate_key('pre_order_history', pre_order_id)
        return cls.get(key)
    
    @classmethod
    def set_pre_order_history(cls, pre_order_id: int, history: List[Dict]):
        """
        Armazena histórico de pré-ordem no cache
        
        Args:
            pre_order_id: ID da pré-ordem
            history: Lista de eventos de histórico
        """
        key = cls._generate_key('pre_order_history', pre_order_id)
        cls.set(key, history, cls.TTL_HISTORY)
        logger.debug(f"Cache: histórico da pré-ordem {pre_order_id} armazenado")
    
    @classmethod
    def invalidate_pre_order_history(cls, pre_order_id: int):
        """
        Invalida cache de histórico de uma pré-ordem
        
        Args:
            pre_order_id: ID da pré-ordem
        """
        key = cls._generate_key('pre_order_history', pre_order_id)
        cls.delete(key)
        logger.debug(f"Cache: histórico da pré-ordem {pre_order_id} invalidado")
    
    @classmethod
    def get_pre_order_details(cls, pre_order_id: int, user_id: int) -> Optional[Dict]:
        """
        Obtém detalhes de pré-ordem do cache
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário solicitante
            
        Returns:
            Detalhes da pré-ordem ou None se não estiver em cache
        """
        key = cls._generate_key('pre_order_details', pre_order_id, user_id)
        return cls.get(key)
    
    @classmethod
    def set_pre_order_details(cls, pre_order_id: int, user_id: int, details: Dict):
        """
        Armazena detalhes de pré-ordem no cache
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário solicitante
            details: Detalhes da pré-ordem
        """
        key = cls._generate_key('pre_order_details', pre_order_id, user_id)
        cls.set(key, details, cls.TTL_DETAILS)
        logger.debug(f"Cache: detalhes da pré-ordem {pre_order_id} armazenados")
    
    @classmethod
    def invalidate_pre_order(cls, pre_order_id: int):
        """
        Invalida todo o cache relacionado a uma pré-ordem
        
        Deve ser chamado quando a pré-ordem é modificada (proposta, aceitação, etc.)
        
        Args:
            pre_order_id: ID da pré-ordem
        """
        # Invalidar detalhes
        cls.delete_pattern(f'pre_order_details:{pre_order_id}:*')
        
        # Invalidar histórico
        cls.invalidate_pre_order_history(pre_order_id)
        
        # Invalidar pré-ordens ativas dos usuários envolvidos
        # (será invalidado quando soubermos os IDs dos usuários)
        
        logger.debug(f"Cache: todos os dados da pré-ordem {pre_order_id} invalidados")
    
    @classmethod
    def invalidate_pre_order_for_users(cls, pre_order_id: int, client_id: int, provider_id: int):
        """
        Invalida cache de uma pré-ordem e dos usuários envolvidos
        
        Args:
            pre_order_id: ID da pré-ordem
            client_id: ID do cliente
            provider_id: ID do prestador
        """
        # Invalidar pré-ordem
        cls.invalidate_pre_order(pre_order_id)
        
        # Invalidar listas de pré-ordens dos usuários
        cls.invalidate_user_pre_orders(client_id)
        cls.invalidate_user_pre_orders(provider_id)
        
        logger.debug(
            f"Cache: pré-ordem {pre_order_id} e usuários "
            f"{client_id}, {provider_id} invalidados"
        )


def cached_pre_order_query(ttl_seconds: int = PreOrderCacheService.TTL_DETAILS):
    """
    Decorator para cachear consultas de pré-ordem
    
    Uso:
        @cached_pre_order_query(ttl_seconds=300)
        def get_pre_order_data(pre_order_id):
            # ... consulta ao banco ...
            return data
    
    Args:
        ttl_seconds: Tempo de vida do cache em segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave baseada no nome da função e argumentos
            cache_key = PreOrderCacheService._generate_key(
                func.__name__,
                *args,
                *[f"{k}={v}" for k, v in sorted(kwargs.items())]
            )
            
            # Tentar obter do cache
            cached_value = PreOrderCacheService.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {func.__name__}")
                return cached_value
            
            # Executar função e cachear resultado
            logger.debug(f"Cache MISS: {func.__name__}")
            result = func(*args, **kwargs)
            PreOrderCacheService.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator
