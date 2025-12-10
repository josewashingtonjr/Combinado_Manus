# -*- coding: utf-8 -*-
"""
Serviço de Atualizações em Tempo Real
Implementa Server-Sent Events (SSE) para atualizações de dashboard
"""

import json
import time
import logging
from datetime import datetime
from flask import Response, stream_with_context
from models import db, Order, Wallet
from services.dashboard_data_service import DashboardDataService
from services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class RealtimeService:
    """Serviço para gerenciar atualizações em tempo real via SSE"""
    
    # Cache de último estado conhecido por usuário
    _last_state = {}
    
    @staticmethod
    def create_sse_stream(user_id, role):
        """
        Cria stream SSE para atualizações em tempo real
        
        Args:
            user_id: ID do usuário
            role: 'cliente' ou 'prestador'
            
        Yields:
            Eventos SSE formatados
        """
        @stream_with_context
        def generate():
            # Enviar evento inicial de conexão
            yield RealtimeService._format_sse_message({
                'type': 'connected',
                'message': 'Conexão estabelecida',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Loop de verificação de atualizações
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    # Verificar se há atualizações
                    updates = RealtimeService.check_for_updates(user_id, role)
                    
                    if updates:
                        # Enviar cada atualização
                        for update in updates:
                            yield RealtimeService._format_sse_message(update)
                    
                    # Enviar heartbeat a cada 30 segundos
                    yield RealtimeService._format_sse_message({
                        'type': 'heartbeat',
                        'timestamp': datetime.utcnow().isoformat()
                    }, event='heartbeat')
                    
                    # Aguardar antes da próxima verificação
                    time.sleep(15)  # Verificar a cada 15 segundos
                    retry_count = 0  # Reset contador em caso de sucesso
                    
                except GeneratorExit:
                    # Cliente desconectou
                    logger.info(f"Cliente desconectou - User: {user_id}, Role: {role}")
                    break
                    
                except Exception as e:
                    logger.error(f"Erro no stream SSE: {e}")
                    retry_count += 1
                    
                    # Enviar evento de erro
                    yield RealtimeService._format_sse_message({
                        'type': 'error',
                        'message': 'Erro temporário na conexão',
                        'retry': True
                    }, event='error')
                    
                    time.sleep(5)  # Aguardar antes de retry
            
            # Enviar evento de desconexão
            yield RealtimeService._format_sse_message({
                'type': 'disconnected',
                'message': 'Conexão encerrada'
            })
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @staticmethod
    def check_for_updates(user_id, role):
        """
        Verifica se há atualizações para o usuário
        
        Args:
            user_id: ID do usuário
            role: 'cliente' ou 'prestador'
            
        Returns:
            list: Lista de atualizações encontradas
        """
        updates = []
        
        try:
            # Obter estado atual
            current_state = RealtimeService._get_current_state(user_id, role)
            
            # Obter último estado conhecido
            cache_key = f"{user_id}_{role}"
            last_state = RealtimeService._last_state.get(cache_key, {})
            
            # Verificar mudanças no saldo
            if last_state.get('balance') != current_state.get('balance'):
                updates.append({
                    'type': 'balance_updated',
                    'data': {
                        'available': float(current_state['balance']['available']),
                        'blocked': float(current_state['balance']['blocked']),
                        'total': float(current_state['balance']['total'])
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Verificar mudanças nas ordens
            if last_state.get('orders_count') != current_state.get('orders_count'):
                updates.append({
                    'type': 'orders_updated',
                    'data': {
                        'count': current_state['orders_count'],
                        'orders': current_state['orders']
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Verificar novas ordens criadas
            new_orders = RealtimeService._find_new_orders(
                last_state.get('orders', []),
                current_state.get('orders', [])
            )
            
            for order in new_orders:
                updates.append({
                    'type': 'order_created',
                    'data': order,
                    'message': f'Nova ordem #{order["id"]} criada',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Verificar mudanças de status em ordens
            status_changes = RealtimeService._find_status_changes(
                last_state.get('orders', []),
                current_state.get('orders', [])
            )
            
            for change in status_changes:
                updates.append({
                    'type': 'order_status_changed',
                    'data': change,
                    'message': f'Ordem #{change["order_id"]} mudou para {change["new_status"]}',
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Atualizar cache com estado atual
            RealtimeService._last_state[cache_key] = current_state
            
        except Exception as e:
            logger.error(f"Erro ao verificar atualizações: {e}")
        
        return updates
    
    @staticmethod
    def _get_current_state(user_id, role):
        """
        Obtém estado atual do usuário
        
        Returns:
            dict: Estado atual com saldo e ordens
        """
        try:
            # Obter saldo
            wallet_info = WalletService.get_wallet_info(user_id)
            balance = {
                'available': wallet_info['balance'],
                'blocked': wallet_info['escrow_balance'],
                'total': wallet_info['balance'] + wallet_info['escrow_balance']
            }
            
            # Obter ordens em aberto
            orders = DashboardDataService.get_open_orders(user_id, role)
            
            # Simplificar dados das ordens para comparação
            orders_simple = [
                {
                    'id': order['id'],
                    'status': order['status'],
                    'value': float(order['value'])  # Corrigido: usar 'value' ao invés de 'valor_efetivo'
                }
                for order in orders
            ]
            
            return {
                'balance': balance,
                'orders': orders_simple,
                'orders_count': len(orders_simple)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estado atual: {e}")
            return {
                'balance': {'available': 0, 'blocked': 0, 'total': 0},
                'orders': [],
                'orders_count': 0
            }
    
    @staticmethod
    def _find_new_orders(old_orders, new_orders):
        """Encontra ordens que foram criadas"""
        old_ids = {order['id'] for order in old_orders}
        return [order for order in new_orders if order['id'] not in old_ids]
    
    @staticmethod
    def _find_status_changes(old_orders, new_orders):
        """Encontra ordens que mudaram de status"""
        changes = []
        
        # Criar mapa de ordens antigas
        old_map = {order['id']: order for order in old_orders}
        
        for new_order in new_orders:
            old_order = old_map.get(new_order['id'])
            if old_order and old_order['status'] != new_order['status']:
                changes.append({
                    'order_id': new_order['id'],
                    'old_status': old_order['status'],
                    'new_status': new_order['status']
                })
        
        return changes
    
    @staticmethod
    def _format_sse_message(data, event='message'):
        """
        Formata mensagem no formato SSE
        
        Args:
            data: Dados a enviar
            event: Nome do evento (opcional)
            
        Returns:
            str: Mensagem formatada para SSE
        """
        message = f"event: {event}\n"
        message += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        return message
    
    @staticmethod
    def notify_order_created(order_id):
        """
        Notifica criação de ordem (para invalidar cache)
        
        Args:
            order_id: ID da ordem criada
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return
            
            # Invalidar cache do cliente
            client_key = f"{order.client_id}_cliente"
            if client_key in RealtimeService._last_state:
                del RealtimeService._last_state[client_key]
            
            # Invalidar cache do prestador
            provider_key = f"{order.provider_id}_prestador"
            if provider_key in RealtimeService._last_state:
                del RealtimeService._last_state[provider_key]
            
            logger.info(f"Cache invalidado para ordem #{order_id}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de ordem: {e}")
    
    @staticmethod
    def notify_order_status_changed(order_id):
        """
        Notifica mudança de status de ordem (para invalidar cache)
        
        Args:
            order_id: ID da ordem
        """
        # Usar mesma lógica de notify_order_created
        RealtimeService.notify_order_created(order_id)
    
    @staticmethod
    def notify_balance_changed(user_id):
        """
        Notifica mudança de saldo (para invalidar cache)
        
        Args:
            user_id: ID do usuário
        """
        try:
            # Invalidar cache para ambos os papéis
            for role in ['cliente', 'prestador']:
                cache_key = f"{user_id}_{role}"
                if cache_key in RealtimeService._last_state:
                    del RealtimeService._last_state[cache_key]
            
            logger.info(f"Cache de saldo invalidado para usuário #{user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar mudança de saldo: {e}")
