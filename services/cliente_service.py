#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, db
from datetime import datetime, timedelta
from sqlalchemy import desc

class ClienteService:
    """Serviço para operações da área do cliente"""
    
    @staticmethod
    def get_dashboard_data(user_id):
        """Retorna dados para o dashboard do cliente"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos os modelos de Wallet, Transaction, Order
        dashboard_data = {
            'saldo_atual': 0.00,  # TODO: Buscar do modelo Wallet
            'tokens_disponiveis': 0.00,
            'transacoes_mes': 0,  # TODO: Contar transações do mês atual
            'ordens_ativas': 0,   # TODO: Contar ordens ativas
            'ordens_concluidas': 0,  # TODO: Contar ordens concluídas
            'gasto_total_mes': 0.00,  # TODO: Somar gastos do mês
            'economia_mes': 0.00,     # TODO: Calcular economia
            'ultima_transacao': None,  # TODO: Buscar última transação
            'proximas_ordens': [],     # TODO: Buscar próximas ordens
            'alertas': [],             # TODO: Verificar alertas (saldo baixo, etc.)
        }
        
        # Verificar alertas
        if dashboard_data['saldo_atual'] < 10.00:
            dashboard_data['alertas'].append({
                'tipo': 'warning',
                'mensagem': 'Saldo baixo. Considere solicitar mais tokens.'
            })
        
        return dashboard_data
    
    @staticmethod
    def get_wallet_data(user_id):
        """Retorna dados da carteira do cliente"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos o modelo Wallet
        wallet_data = {
            'saldo_atual': 0.00,
            'tokens_bloqueados': 0.00,  # Em escrow
            'tokens_disponiveis': 0.00,
            'historico_saldos': [],     # Histórico dos últimos 30 dias
            'transacoes_recentes': [],  # Últimas 10 transações
            'estatisticas': {
                'total_recebido': 0.00,
                'total_gasto': 0.00,
                'media_mensal': 0.00,
                'maior_transacao': 0.00
            }
        }
        
        return wallet_data
    
    @staticmethod
    def get_transactions_history(user_id, page=1, per_page=20):
        """Retorna histórico de transações do cliente"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos o modelo Transaction
        # Por enquanto, retornar estrutura vazia
        class MockPagination:
            def __init__(self):
                self.items = []
                self.page = page
                self.pages = 1
                self.per_page = per_page
                self.total = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
        
        return MockPagination()
    
    @staticmethod
    def get_client_orders(user_id, page=1, per_page=20):
        """Retorna ordens de serviço do cliente"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos o modelo Order
        # Por enquanto, retornar estrutura vazia
        class MockPagination:
            def __init__(self):
                self.items = []
                self.page = page
                self.pages = 1
                self.per_page = per_page
                self.total = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
        
        return MockPagination()
    
    @staticmethod
    def create_token_request(user_id, amount, description):
        """Cria uma solicitação de tokens para aprovação do admin"""
        user = User.query.get(user_id)
        
        # TODO: Implementar modelo TokenRequest
        # Por enquanto, apenas simular a operação
        
        # Validações
        if amount <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        
        if amount > 10000:  # Limite máximo por solicitação
            raise ValueError('Quantidade excede o limite máximo de 10.000 tokens')
        
        # TODO: Criar registro na tabela token_requests
        # token_request = TokenRequest(
        #     user_id=user_id,
        #     amount=amount,
        #     description=description,
        #     status='pending',
        #     created_at=datetime.utcnow()
        # )
        # db.session.add(token_request)
        # db.session.commit()
        
        return True
    
    @staticmethod
    def get_user_statistics(user_id):
        """Retorna estatísticas detalhadas do cliente"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos os modelos completos
        stats = {
            'membro_desde': user.created_at,
            'total_transacoes': 0,
            'volume_total': 0.00,
            'economia_total': 0.00,
            'prestadores_favoritos': [],
            'categorias_mais_usadas': [],
            'media_avaliacao_dada': 0.0,
            'media_avaliacao_recebida': 0.0
        }
        
        return stats
    
    @staticmethod
    def can_create_order(user_id, order_value):
        """Verifica se o cliente pode criar uma ordem com o valor especificado"""
        wallet_data = ClienteService.get_wallet_data(user_id)
        
        # Verificar se tem saldo suficiente (valor + taxa)
        taxa_sistema = 0.05  # 5% - TODO: Buscar da configuração
        valor_total = order_value * (1 + taxa_sistema)
        
        return wallet_data['tokens_disponiveis'] >= valor_total
    
    @staticmethod
    def get_available_providers():
        """Retorna lista de prestadores disponíveis"""
        # TODO: Implementar busca de prestadores ativos
        providers = User.query.filter(
            User.roles.contains('prestador'),
            User.active == True
        ).all()
        
        return providers
