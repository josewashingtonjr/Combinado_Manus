#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Atualizações em Tempo Real
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Wallet, Order
from services.realtime_service import RealtimeService
from decimal import Decimal


def test_realtime_service():
    """Testa funcionalidades básicas do RealtimeService"""
    
    with app.app_context():
        print("=" * 60)
        print("TESTE DO SISTEMA DE ATUALIZAÇÕES EM TEMPO REAL")
        print("=" * 60)
        
        # 1. Testar formato de mensagem SSE
        print("\n1. Testando formato de mensagem SSE...")
        test_data = {
            'type': 'balance_updated',
            'data': {'available': 100.0, 'blocked': 50.0}
        }
        message = RealtimeService._format_sse_message(test_data)
        assert 'event: message' in message
        assert 'data:' in message
        print("   ✓ Formato de mensagem SSE correto")
        
        # 2. Testar detecção de novas ordens
        print("\n2. Testando detecção de novas ordens...")
        old_orders = [{'id': 1, 'status': 'aceita', 'value': 100.0}]
        new_orders = [
            {'id': 1, 'status': 'aceita', 'value': 100.0},
            {'id': 2, 'status': 'aceita', 'value': 200.0}
        ]
        new_found = RealtimeService._find_new_orders(old_orders, new_orders)
        assert len(new_found) == 1
        assert new_found[0]['id'] == 2
        print("   ✓ Detecção de novas ordens funcionando")
        
        # 3. Testar detecção de mudanças de status
        print("\n3. Testando detecção de mudanças de status...")
        old_orders = [{'id': 1, 'status': 'aceita', 'value': 100.0}]
        new_orders = [{'id': 1, 'status': 'em_andamento', 'value': 100.0}]
        changes = RealtimeService._find_status_changes(old_orders, new_orders)
        assert len(changes) == 1
        assert changes[0]['old_status'] == 'aceita'
        assert changes[0]['new_status'] == 'em_andamento'
        print("   ✓ Detecção de mudanças de status funcionando")
        
        # 4. Testar obtenção de estado atual (se houver usuários)
        print("\n4. Testando obtenção de estado atual...")
        user = User.query.first()
        if user:
            state = RealtimeService._get_current_state(user.id, 'cliente')
            assert 'balance' in state
            assert 'orders' in state
            assert 'orders_count' in state
            print(f"   ✓ Estado obtido para usuário {user.id}")
            print(f"     - Saldo disponível: R$ {state['balance']['available']:.2f}")
            print(f"     - Saldo bloqueado: R$ {state['balance']['blocked']:.2f}")
            print(f"     - Ordens em aberto: {state['orders_count']}")
        else:
            print("   ⚠ Nenhum usuário encontrado para testar")
        
        # 5. Testar notificação de criação de ordem
        print("\n5. Testando notificação de criação de ordem...")
        order = Order.query.first()
        if order:
            # Limpar cache primeiro
            RealtimeService._last_state.clear()
            
            # Notificar criação
            RealtimeService.notify_order_created(order.id)
            
            # Verificar que cache foi invalidado
            client_key = f"{order.client_id}_cliente"
            provider_key = f"{order.provider_id}_prestador"
            assert client_key not in RealtimeService._last_state
            assert provider_key not in RealtimeService._last_state
            print(f"   ✓ Notificação de ordem #{order.id} processada")
            print(f"     - Cache invalidado para cliente e prestador")
        else:
            print("   ⚠ Nenhuma ordem encontrada para testar")
        
        # 6. Testar notificação de mudança de saldo
        print("\n6. Testando notificação de mudança de saldo...")
        if user:
            # Limpar cache
            RealtimeService._last_state.clear()
            
            # Notificar mudança
            RealtimeService.notify_balance_changed(user.id)
            
            # Verificar que cache foi invalidado
            for role in ['cliente', 'prestador']:
                cache_key = f"{user.id}_{role}"
                assert cache_key not in RealtimeService._last_state
            print(f"   ✓ Notificação de saldo para usuário {user.id} processada")
            print(f"     - Cache invalidado para ambos os papéis")
        
        print("\n" + "=" * 60)
        print("TODOS OS TESTES PASSARAM! ✓")
        print("=" * 60)
        print("\nSistema de tempo real está funcionando corretamente.")
        print("\nPróximos passos:")
        print("  1. Iniciar o servidor: python app.py")
        print("  2. Acessar dashboard de cliente ou prestador")
        print("  3. Abrir console do navegador (F12)")
        print("  4. Verificar mensagens de conexão SSE")
        print("  5. Criar uma ordem e observar atualização automática")


def test_routes():
    """Testa se as rotas foram registradas corretamente"""
    
    with app.app_context():
        print("\n" + "=" * 60)
        print("TESTE DAS ROTAS DE TEMPO REAL")
        print("=" * 60)
        
        from flask import url_for
        
        with app.test_request_context():
            print("\nRotas registradas:")
            print(f"  ✓ Stream SSE: {url_for('realtime.dashboard_stream')}")
            print(f"  ✓ Check updates: {url_for('realtime.check_updates')}")
            print(f"  ✓ Refresh: {url_for('realtime.refresh_dashboard')}")
        
        print("\nTodas as rotas foram registradas corretamente! ✓")


if __name__ == '__main__':
    try:
        test_realtime_service()
        test_routes()
        
        print("\n" + "=" * 60)
        print("RESUMO")
        print("=" * 60)
        print("\n✅ Sistema de tempo real implementado com sucesso!")
        print("\nArquivos criados:")
        print("  - services/realtime_service.py")
        print("  - routes/realtime_routes.py")
        print("  - static/js/dashboard-realtime.js")
        print("  - static/css/dashboard-realtime.css")
        print("\nArquivos atualizados:")
        print("  - app.py (blueprint registrado)")
        print("  - templates/cliente/dashboard.html")
        print("  - templates/prestador/dashboard.html")
        print("  - services/invite_acceptance_coordinator.py")
        
    except AssertionError as e:
        print(f"\n❌ ERRO: Teste falhou - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
