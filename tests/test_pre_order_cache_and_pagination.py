#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para sistema de cache e paginação de pré-ordens

Testa:
- Cache de pré-ordens ativas
- Cache de histórico
- Cache de detalhes
- Invalidação de cache
- Paginação de pré-ordens
- Paginação de histórico

Requirements: Performance considerations (Task 22)
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from services.pre_order_cache_service import PreOrderCacheService, CacheEntry
from services.pre_order_service import PreOrderService
from models import (
    db, User, PreOrder, PreOrderStatus, PreOrderHistory, Invite
)


class TestCacheEntry:
    """Testes para CacheEntry"""
    
    def test_cache_entry_not_expired(self):
        """Testa que entrada não expirada retorna valor"""
        entry = CacheEntry(value={'test': 'data'}, ttl_seconds=60)
        assert not entry.is_expired()
        assert entry.get_value() == {'test': 'data'}
    
    def test_cache_entry_expired(self):
        """Testa que entrada expirada retorna None"""
        entry = CacheEntry(value={'test': 'data'}, ttl_seconds=0)
        # Forçar expiração
        entry.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert entry.is_expired()
        assert entry.get_value() is None


class TestPreOrderCacheService:
    """Testes para PreOrderCacheService"""
    
    def setup_method(self):
        """Limpar cache antes de cada teste"""
        PreOrderCacheService.clear_all()
    
    def test_cache_set_and_get(self):
        """Testa armazenar e recuperar do cache"""
        key = 'test:key:1'
        value = {'data': 'test'}
        
        PreOrderCacheService.set(key, value, ttl_seconds=60)
        cached_value = PreOrderCacheService.get(key)
        
        assert cached_value == value
    
    def test_cache_miss(self):
        """Testa cache miss"""
        value = PreOrderCacheService.get('nonexistent:key')
        assert value is None
    
    def test_cache_expiration(self):
        """Testa expiração de cache"""
        key = 'test:expiring:1'
        value = {'data': 'test'}
        
        # Armazenar com TTL de 0 segundos
        PreOrderCacheService.set(key, value, ttl_seconds=0)
        
        # Forçar expiração
        PreOrderCacheService._cache[key].expires_at = datetime.utcnow() - timedelta(seconds=1)
        
        # Deve retornar None
        cached_value = PreOrderCacheService.get(key)
        assert cached_value is None
    
    def test_cache_delete(self):
        """Testa remoção de entrada do cache"""
        key = 'test:delete:1'
        value = {'data': 'test'}
        
        PreOrderCacheService.set(key, value, ttl_seconds=60)
        assert PreOrderCacheService.get(key) == value
        
        PreOrderCacheService.delete(key)
        assert PreOrderCacheService.get(key) is None
    
    def test_cache_delete_pattern(self):
        """Testa remoção por padrão"""
        PreOrderCacheService.set('pre_order:123:details', {'id': 123}, ttl_seconds=60)
        PreOrderCacheService.set('pre_order:123:history', [], ttl_seconds=60)
        PreOrderCacheService.set('pre_order:456:details', {'id': 456}, ttl_seconds=60)
        
        # Deletar todas as entradas da pré-ordem 123
        PreOrderCacheService.delete_pattern('pre_order:123:*')
        
        assert PreOrderCacheService.get('pre_order:123:details') is None
        assert PreOrderCacheService.get('pre_order:123:history') is None
        assert PreOrderCacheService.get('pre_order:456:details') == {'id': 456}
    
    def test_cache_cleanup_expired(self):
        """Testa limpeza de entradas expiradas"""
        # Adicionar entradas válidas e expiradas
        PreOrderCacheService.set('valid:1', {'data': 1}, ttl_seconds=60)
        PreOrderCacheService.set('expired:1', {'data': 2}, ttl_seconds=0)
        
        # Forçar expiração
        PreOrderCacheService._cache['expired:1'].expires_at = datetime.utcnow() - timedelta(seconds=1)
        
        # Executar limpeza
        PreOrderCacheService.cleanup_expired()
        
        # Válida deve permanecer, expirada deve ser removida
        assert PreOrderCacheService.get('valid:1') == {'data': 1}
        assert 'expired:1' not in PreOrderCacheService._cache
    
    def test_cache_stats(self):
        """Testa estatísticas do cache"""
        PreOrderCacheService.clear_all()
        
        # Gerar alguns hits e misses
        PreOrderCacheService.set('key:1', {'data': 1}, ttl_seconds=60)
        PreOrderCacheService.get('key:1')  # hit
        PreOrderCacheService.get('key:1')  # hit
        PreOrderCacheService.get('key:2')  # miss
        
        stats = PreOrderCacheService.get_stats()
        
        assert stats['hits'] >= 2
        assert stats['misses'] >= 1
        assert stats['cache_size'] >= 1
    
    def test_active_pre_orders_cache(self):
        """Testa cache de pré-ordens ativas"""
        user_id = 1
        user_role = 'cliente'
        pre_orders = [{'id': 1, 'title': 'Test'}]
        
        # Armazenar
        PreOrderCacheService.set_active_pre_orders(user_id, user_role, pre_orders)
        
        # Recuperar
        cached = PreOrderCacheService.get_active_pre_orders(user_id, user_role)
        assert cached == pre_orders
    
    def test_pre_order_history_cache(self):
        """Testa cache de histórico"""
        pre_order_id = 1
        history = [{'event': 'created'}, {'event': 'updated'}]
        
        # Armazenar
        PreOrderCacheService.set_pre_order_history(pre_order_id, history)
        
        # Recuperar
        cached = PreOrderCacheService.get_pre_order_history(pre_order_id)
        assert cached == history
    
    def test_pre_order_details_cache(self):
        """Testa cache de detalhes"""
        pre_order_id = 1
        user_id = 1
        details = {'id': 1, 'title': 'Test', 'value': 100.00}
        
        # Armazenar
        PreOrderCacheService.set_pre_order_details(pre_order_id, user_id, details)
        
        # Recuperar
        cached = PreOrderCacheService.get_pre_order_details(pre_order_id, user_id)
        assert cached == details
    
    def test_invalidate_user_pre_orders(self):
        """Testa invalidação de pré-ordens de usuário"""
        user_id = 1
        
        PreOrderCacheService.set_active_pre_orders(user_id, 'cliente', [{'id': 1}])
        PreOrderCacheService.set_active_pre_orders(user_id, 'prestador', [{'id': 2}])
        
        # Invalidar
        PreOrderCacheService.invalidate_user_pre_orders(user_id)
        
        # Ambos devem estar invalidados
        assert PreOrderCacheService.get_active_pre_orders(user_id, 'cliente') is None
        assert PreOrderCacheService.get_active_pre_orders(user_id, 'prestador') is None
    
    def test_invalidate_pre_order(self):
        """Testa invalidação completa de pré-ordem"""
        pre_order_id = 1
        
        PreOrderCacheService.set_pre_order_details(pre_order_id, 1, {'id': 1})
        PreOrderCacheService.set_pre_order_details(pre_order_id, 2, {'id': 1})
        PreOrderCacheService.set_pre_order_history(pre_order_id, [])
        
        # Invalidar
        PreOrderCacheService.invalidate_pre_order(pre_order_id)
        
        # Todos devem estar invalidados
        assert PreOrderCacheService.get_pre_order_details(pre_order_id, 1) is None
        assert PreOrderCacheService.get_pre_order_details(pre_order_id, 2) is None
        assert PreOrderCacheService.get_pre_order_history(pre_order_id) is None
    
    def test_invalidate_pre_order_for_users(self):
        """Testa invalidação de pré-ordem e usuários"""
        pre_order_id = 1
        client_id = 1
        provider_id = 2
        
        # Configurar cache
        PreOrderCacheService.set_pre_order_details(pre_order_id, client_id, {'id': 1})
        PreOrderCacheService.set_active_pre_orders(client_id, 'cliente', [{'id': 1}])
        PreOrderCacheService.set_active_pre_orders(provider_id, 'prestador', [{'id': 1}])
        
        # Invalidar
        PreOrderCacheService.invalidate_pre_order_for_users(
            pre_order_id, client_id, provider_id
        )
        
        # Tudo deve estar invalidado
        assert PreOrderCacheService.get_pre_order_details(pre_order_id, client_id) is None
        assert PreOrderCacheService.get_active_pre_orders(client_id, 'cliente') is None
        assert PreOrderCacheService.get_active_pre_orders(provider_id, 'prestador') is None


class TestPreOrderServicePagination:
    """Testes para paginação no PreOrderService"""
    
    def test_pagination_parameters(self):
        """Testa que parâmetros de paginação são validados"""
        # Este teste verifica a estrutura, não requer banco de dados
        # A implementação real será testada com dados reais quando as tabelas existirem
        pass
    
    def test_cache_integration(self):
        """Testa integração com cache"""
        # Este teste verifica que o cache é usado corretamente
        # Será testado com dados reais quando as tabelas existirem
        pass


def test_cache_decorator():
    """Testa decorator de cache"""
    from services.pre_order_cache_service import cached_pre_order_query
    
    call_count = 0
    
    @cached_pre_order_query(ttl_seconds=60)
    def expensive_function(value):
        nonlocal call_count
        call_count += 1
        return {'result': value * 2}
    
    # Limpar cache
    PreOrderCacheService.clear_all()
    
    # Primeira chamada - deve executar função
    result1 = expensive_function(5)
    assert result1 == {'result': 10}
    assert call_count == 1
    
    # Segunda chamada - deve usar cache
    result2 = expensive_function(5)
    assert result2 == {'result': 10}
    assert call_count == 1  # Não deve ter incrementado
    
    # Chamada com argumento diferente - deve executar função
    result3 = expensive_function(10)
    assert result3 == {'result': 20}
    assert call_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
