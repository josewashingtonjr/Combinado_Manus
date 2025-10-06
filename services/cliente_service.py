#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, Order, Transaction, db
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from services.wallet_service import WalletService

class ClienteService:
    """Serviço para operações da área do cliente"""
    
    @staticmethod
    def get_dashboard_data(user_id):
        """Retorna dados reais para o dashboard do cliente com terminologia em R$"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Obter informações da carteira (dados reais)
        try:
            wallet_info = WalletService.get_wallet_info(user_id)
            saldo_atual = wallet_info['balance']
            saldo_bloqueado = wallet_info['escrow_balance']
            saldo_disponivel = saldo_atual  # Saldo disponível para uso
        except Exception:
            # Fallback se carteira não existir
            WalletService.ensure_user_has_wallet(user_id)
            saldo_atual = 0.0
            saldo_bloqueado = 0.0
            saldo_disponivel = 0.0
        
        # Início do mês atual para filtros
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Contar transações do mês atual
        transacoes_mes = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= inicio_mes
        ).count()
        
        # Contar ordens ativas (criadas pelo cliente)
        ordens_ativas = Order.query.filter(
            Order.client_id == user_id,
            Order.status.in_(['disponivel', 'aceita', 'em_andamento'])
        ).count()
        
        # Contar ordens concluídas
        ordens_concluidas = Order.query.filter(
            Order.client_id == user_id,
            Order.status == 'concluida'
        ).count()
        
        # Calcular gasto total do mês (transações negativas)
        gasto_mes_result = db.session.query(
            func.sum(func.abs(Transaction.amount))
        ).filter(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.created_at >= inicio_mes
        ).scalar()
        gasto_total_mes = gasto_mes_result or 0.0
        
        # Buscar última transação
        ultima_transacao_obj = Transaction.query.filter_by(
            user_id=user_id
        ).order_by(desc(Transaction.created_at)).first()
        
        ultima_transacao = None
        if ultima_transacao_obj:
            ultima_transacao = {
                'data': ultima_transacao_obj.created_at.strftime('%d/%m/%Y %H:%M'),
                'valor': abs(ultima_transacao_obj.amount),
                'tipo': ultima_transacao_obj.type,
                'descricao': ultima_transacao_obj.description
            }
        
        # Buscar próximas ordens (ordens ativas com data futura)
        proximas_ordens_obj = Order.query.filter(
            Order.client_id == user_id,
            Order.status.in_(['aceita', 'em_andamento'])
        ).order_by(Order.created_at.desc()).limit(3).all()
        
        proximas_ordens = []
        for ordem in proximas_ordens_obj:
            proximas_ordens.append({
                'titulo': ordem.title,
                'data': ordem.created_at.strftime('%d/%m/%Y'),
                'status': ordem.status,
                'valor': ordem.value
            })
        
        # Verificar alertas baseados em dados reais
        alertas = []
        
        # Alerta de saldo baixo (menos de R$ 50,00)
        if saldo_disponivel < 50.0:
            alertas.append({
                'tipo': 'warning',
                'mensagem': 'Saldo baixo. Considere adicionar mais saldo à sua conta.'
            })
        
        # Alerta se tem saldo bloqueado
        if saldo_bloqueado > 0:
            alertas.append({
                'tipo': 'info',
                'mensagem': f'Você tem R$ {saldo_bloqueado:.2f} em garantia para ordens ativas.'
            })
        
        # Alerta se não tem ordens ativas há muito tempo
        if ordens_ativas == 0 and saldo_disponivel > 0:
            alertas.append({
                'tipo': 'info',
                'mensagem': 'Que tal criar uma nova ordem de serviço?'
            })
        
        dashboard_data = {
            # Valores em formato numérico (serão convertidos para R$ no template)
            'saldo_atual': saldo_atual,
            'tokens_disponiveis': saldo_disponivel,  # Terminologia interna, será exibido como "Saldo Disponível"
            'saldo_bloqueado': saldo_bloqueado,
            
            # Contadores
            'transacoes_mes': transacoes_mes,
            'ordens_ativas': ordens_ativas,
            'ordens_concluidas': ordens_concluidas,
            
            # Valores financeiros
            'gasto_total_mes': gasto_total_mes,
            'economia_mes': 0.0,  # TODO: Implementar cálculo de economia
            
            # Atividades
            'ultima_transacao': ultima_transacao,
            'proximas_ordens': proximas_ordens,
            'alertas': alertas,
            
            # Estatísticas adicionais
            'total_gasto_historico': ClienteService._calcular_gasto_total(user_id),
            'media_valor_ordem': ClienteService._calcular_media_valor_ordem(user_id),
            'taxa_conclusao': ClienteService._calcular_taxa_conclusao(user_id)
        }
        
        return dashboard_data
    
    @staticmethod
    def _calcular_gasto_total(user_id):
        """Calcula o gasto total histórico do cliente"""
        gasto_total = db.session.query(
            func.sum(func.abs(Transaction.amount))
        ).filter(
            Transaction.user_id == user_id,
            Transaction.amount < 0,
            Transaction.type.in_(['escrow_bloqueio', 'pagamento', 'taxa_sistema'])
        ).scalar()
        return gasto_total or 0.0
    
    @staticmethod
    def _calcular_media_valor_ordem(user_id):
        """Calcula o valor médio das ordens do cliente"""
        media = db.session.query(
            func.avg(Order.value)
        ).filter(
            Order.client_id == user_id
        ).scalar()
        return media or 0.0
    
    @staticmethod
    def _calcular_taxa_conclusao(user_id):
        """Calcula a taxa de conclusão das ordens do cliente"""
        total_ordens = Order.query.filter_by(client_id=user_id).count()
        ordens_concluidas = Order.query.filter_by(
            client_id=user_id, 
            status='concluida'
        ).count()
        
        if total_ordens == 0:
            return 0.0
        
        return (ordens_concluidas / total_ordens) * 100
    
    @staticmethod
    def get_wallet_data(user_id):
        """Retorna dados reais da carteira do cliente com terminologia em R$"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Obter informações da carteira
        try:
            wallet_info = WalletService.get_wallet_info(user_id)
            saldo_atual = wallet_info['balance']
            saldo_bloqueado = wallet_info['escrow_balance']
            saldo_disponivel = saldo_atual
        except Exception:
            WalletService.ensure_user_has_wallet(user_id)
            saldo_atual = 0.0
            saldo_bloqueado = 0.0
            saldo_disponivel = 0.0
        
        # Obter transações recentes (últimas 10)
        transacoes_recentes_obj = Transaction.query.filter_by(
            user_id=user_id
        ).order_by(desc(Transaction.created_at)).limit(10).all()
        
        transacoes_recentes = []
        for t in transacoes_recentes_obj:
            transacoes_recentes.append({
                'id': t.id,
                'data': t.created_at.strftime('%d/%m/%Y %H:%M'),
                'tipo': t.type,
                'valor': t.amount,
                'descricao': t.description,
                'status': 'Concluída'
            })
        
        # Calcular estatísticas
        total_recebido = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.amount > 0
        ).scalar() or 0.0
        
        total_gasto = db.session.query(
            func.sum(func.abs(Transaction.amount))
        ).filter(
            Transaction.user_id == user_id,
            Transaction.amount < 0
        ).scalar() or 0.0
        
        # Maior transação (em valor absoluto)
        maior_transacao = db.session.query(
            func.max(func.abs(Transaction.amount))
        ).filter(
            Transaction.user_id == user_id
        ).scalar() or 0.0
        
        # Média mensal (últimos 3 meses)
        tres_meses_atras = datetime.utcnow() - timedelta(days=90)
        transacoes_3_meses = db.session.query(
            func.sum(func.abs(Transaction.amount))
        ).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= tres_meses_atras
        ).scalar() or 0.0
        media_mensal = transacoes_3_meses / 3
        
        wallet_data = {
            # Valores principais (serão exibidos como R$ no template)
            'saldo_atual': saldo_atual,
            'tokens_bloqueados': saldo_bloqueado,  # Será exibido como "Saldo em Garantia"
            'tokens_disponiveis': saldo_disponivel,  # Será exibido como "Saldo Disponível"
            
            # Histórico e transações
            'historico_saldos': [],  # TODO: Implementar histórico diário
            'transacoes_recentes': transacoes_recentes,
            
            # Estatísticas financeiras
            'estatisticas': {
                'total_recebido': total_recebido,
                'total_gasto': total_gasto,
                'media_mensal': media_mensal,
                'maior_transacao': maior_transacao,
                'saldo_total': saldo_atual + saldo_bloqueado
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
