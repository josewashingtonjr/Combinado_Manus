#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, Order, Transaction, db
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from services.wallet_service import WalletService

class PrestadorService:
    """Serviço para operações da área do prestador"""
    
    @staticmethod
    def get_dashboard_data(user_id):
        """Retorna dados reais para o dashboard do prestador com terminologia em R$"""
        from services.dashboard_data_service import DashboardDataService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Usar DashboardDataService para obter métricas completas
        metrics = DashboardDataService.get_dashboard_metrics(user_id, 'prestador')
        
        # Obter ordens em aberto usando DashboardDataService
        ordens_em_aberto = metrics['open_orders']
        
        # Obter fundos bloqueados detalhados
        fundos_bloqueados = metrics['blocked_funds']
        
        # Extrair informações de saldo
        saldo_disponivel = metrics['balance']['available']
        saldo_bloqueado = metrics['balance']['blocked']
        saldo_total = metrics['balance']['total']
        
        # Estatísticas do mês
        ordens_aceitas_mes = metrics['month_stats'].get('orders_accepted', 0)
        ordens_concluidas_mes = metrics['month_stats'].get('orders_completed', 0)
        ganhos_mes = metrics['month_stats'].get('total_received', 0.0)
        
        # Calcular ganhos totais
        ganhos_total_result = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'recebimento'
        ).scalar()
        ganhos_total = ganhos_total_result or 0.0
        
        # Contar ordens ativas (aceita + em_andamento)
        ordens_ativas = len([o for o in ordens_em_aberto if o['status'] in ['aceita', 'em_andamento']])
        
        # Contar ordens disponíveis para aceitar (não aceitas por ninguém)
        ordens_disponiveis = Order.query.filter(
            Order.status == 'disponivel',
            Order.provider_id.is_(None)
        ).count()
        
        # Formatar próximas ordens (primeiras 3 ordens em aberto)
        proximas_ordens = []
        for ordem in ordens_em_aberto[:3]:
            proximas_ordens.append({
                'id': ordem['id'],
                'titulo': ordem['title'],
                'data': ordem['created_at'].strftime('%d/%m/%Y') if ordem['created_at'] else '',
                'horario': ordem['created_at'].strftime('%H:%M') if ordem['created_at'] else '',
                'valor': ordem['value'],
                'status': ordem['status'],
                'cliente': ordem['related_user_name'],
                'prazo': ordem['service_deadline'].strftime('%d/%m/%Y') if ordem['service_deadline'] else ''
            })
        
        # Calcular média de avaliação (simulada por enquanto)
        # TODO: Implementar quando tivermos sistema de avaliações
        media_avaliacao = 4.5  # Simulado
        total_avaliacoes = ordens_concluidas_mes * 2  # Simulado
        
        # Converter alertas do DashboardDataService para formato legado
        alertas = []
        
        # Adicionar notificações de propostas
        from services.notification_service import NotificationService
        proposal_notifications = NotificationService.get_proposal_notifications_for_prestador(user_id)
        alertas.extend(proposal_notifications)
        
        # Adicionar alertas do DashboardDataService
        for alert in metrics['alerts']:
            alertas.append({
                'tipo': alert['type'],
                'mensagem': alert['message']
            })
        
        # Alerta de novas oportunidades
        if ordens_disponiveis > 0:
            alertas.append({
                'tipo': 'info',
                'mensagem': f'Há {ordens_disponiveis} novas oportunidades de trabalho disponíveis!'
            })
        
        # Alerta se não tem ordens ativas
        if ordens_ativas == 0 and ordens_disponiveis > 0:
            alertas.append({
                'tipo': 'warning',
                'mensagem': 'Você não tem ordens ativas. Que tal aceitar uma nova oportunidade?'
            })
        
        # Buscar pré-ordens ativas
        pre_orders_ativas = PrestadorService.get_active_pre_orders(user_id)
        pre_orders_count = len(pre_orders_ativas)
        pre_orders_needing_action = len([po for po in pre_orders_ativas if po['needs_action']])
        
        dashboard_data = {
            # Valores em formato numérico (serão convertidos para R$ no template)
            'saldo_atual': saldo_total,
            'saldo_disponivel': saldo_disponivel,
            'saldo_bloqueado': saldo_bloqueado,
            
            # Contadores
            'ordens_ativas': ordens_ativas,
            'ordens_concluidas_mes': ordens_concluidas_mes,
            'ordens_disponiveis': ordens_disponiveis,
            
            # Valores financeiros
            'ganhos_mes': ganhos_mes,
            'ganhos_total': ganhos_total,
            
            # Performance
            'media_avaliacao': media_avaliacao,
            'total_avaliacoes': total_avaliacoes,
            
            # Atividades
            'proximas_ordens': proximas_ordens,
            'alertas': alertas,
            
            # Métricas adicionais
            'taxa_conclusao': PrestadorService._calcular_taxa_conclusao(user_id),
            'ganho_medio_ordem': PrestadorService._calcular_ganho_medio_ordem(user_id),
            'clientes_atendidos': PrestadorService._contar_clientes_atendidos(user_id),
            
            # Novos dados do DashboardDataService
            'ordens_em_aberto': ordens_em_aberto,
            'fundos_bloqueados_detalhados': fundos_bloqueados['by_order'],
            
            # Pré-ordens
            'pre_orders_ativas': pre_orders_ativas,
            'pre_orders_count': pre_orders_count,
            'pre_orders_needing_action': pre_orders_needing_action
        }
        
        return dashboard_data
    
    @staticmethod
    def _calcular_taxa_conclusao(user_id):
        """Calcula a taxa de conclusão das ordens do prestador"""
        total_ordens = Order.query.filter_by(provider_id=user_id).count()
        ordens_concluidas = Order.query.filter_by(
            provider_id=user_id, 
            status='concluida'
        ).count()
        
        if total_ordens == 0:
            return 0.0
        
        return (ordens_concluidas / total_ordens) * 100
    
    @staticmethod
    def _calcular_ganho_medio_ordem(user_id):
        """Calcula o ganho médio por ordem do prestador"""
        ganho_medio = db.session.query(
            func.avg(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == 'recebimento'
        ).scalar()
        return ganho_medio or 0.0
    
    @staticmethod
    def _contar_clientes_atendidos(user_id):
        """Conta quantos clientes únicos o prestador já atendeu"""
        clientes_unicos = db.session.query(
            func.count(func.distinct(Order.client_id))
        ).filter(
            Order.provider_id == user_id,
            Order.status == 'concluida'
        ).scalar()
        return clientes_unicos or 0
    
    @staticmethod
    def get_wallet_data(user_id):
        """Retorna dados da carteira do prestador"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos o modelo Wallet
        wallet_data = {
            'saldo_atual': 0.00,
            'saldo_disponivel': 0.00,
            'saldo_bloqueado': 0.00,  # Em escrow
            'historico_saldos': [],   # Histórico dos últimos 30 dias
            'ganhos_recentes': [],    # Últimos 10 ganhos
            'estatisticas': {
                'total_ganho': 0.00,
                'total_sacado': 0.00,
                'media_mensal': 0.00,
                'maior_ganho': 0.00,
                'taxa_conclusao': 0.0  # % de ordens concluídas
            }
        }
        
        return wallet_data
    
    @staticmethod
    def get_open_orders_for_provider(user_id):
        """
        Retorna ordens em aberto para o prestador usando DashboardDataService
        
        Args:
            user_id (int): ID do prestador
            
        Returns:
            list: Lista formatada de ordens em aberto para exibição no template
        """
        from services.dashboard_data_service import DashboardDataService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        # Usar DashboardDataService para obter ordens em aberto
        open_orders = DashboardDataService.get_open_orders(user_id, 'prestador')
        
        # Formatar para template (já vem formatado do DashboardDataService)
        return open_orders
    
    @staticmethod
    def get_provider_orders(user_id, page=1, status_filter='todas', per_page=20):
        """Retorna ordens do prestador"""
        from services.order_service import OrderService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        return OrderService.get_provider_orders(user_id, page, per_page, status_filter)
    
    @staticmethod
    def get_available_orders(page=1, per_page=20):
        """Retorna ordens disponíveis para aceitar"""
        from services.order_service import OrderService
        return OrderService.get_available_orders(page, per_page)
    
    @staticmethod
    def get_earnings_history(user_id, page=1, periodo='mes', per_page=20):
        """Retorna histórico de ganhos do prestador"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos o modelo Transaction/Earnings
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
    def get_provider_profile(user_id):
        """Retorna dados do perfil do prestador"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos modelos completos
        profile_data = {
            'prestador_desde': user.created_at,
            'total_ordens': 0,
            'ordens_concluidas': 0,
            'taxa_conclusao': 0.0,
            'media_avaliacao': 0.0,
            'total_avaliacoes': 0,
            'especialidades': [],
            'certificacoes': [],
            'portfolio': [],
            'disponibilidade': 'Disponível',
            'tempo_resposta_medio': '2 horas'
        }
        
        return profile_data
    
    @staticmethod
    def accept_order(user_id, order_id):
        """Aceita uma ordem de serviço"""
        from services.order_service import OrderService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        # Verificar se o usuário tem papel de prestador
        if 'prestador' not in user.roles:
            raise ValueError('Usuário não tem permissão para aceitar ordens')
        
        # Usar OrderService para aceitar a ordem
        return OrderService.accept_order(user_id, order_id)
    
    @staticmethod
    def complete_order(user_id, order_id):
        """Marca uma ordem como concluída"""
        from services.order_service import OrderService
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        # Verificar se o usuário tem papel de prestador
        if 'prestador' not in user.roles:
            raise ValueError('Usuário não tem permissão para concluir ordens')
        
        # Usar OrderService para concluir a ordem
        return OrderService.complete_order(user_id, order_id)
    
    @staticmethod
    def create_withdrawal_request(user_id, amount, bank_info):
        """Cria uma solicitação de saque"""
        user = User.query.get(user_id)
        
        # TODO: Implementar modelo WithdrawalRequest
        # Validações:
        # - Verificar se tem saldo suficiente
        # - Verificar limite mínimo de saque
        # - Validar informações bancárias
        
        if amount <= 0:
            raise ValueError('Valor deve ser maior que zero')
        
        if amount < 10.00:  # Limite mínimo
            raise ValueError('Valor mínimo para saque é R$ 10,00')
        
        # TODO: Verificar saldo disponível
        # wallet = Wallet.query.filter_by(user_id=user_id).first()
        # if wallet.available_balance < amount:
        #     raise ValueError('Saldo insuficiente')
        
        # TODO: Criar registro na tabela withdrawal_requests
        # withdrawal_request = WithdrawalRequest(
        #     user_id=user_id,
        #     amount=amount,
        #     bank_info=bank_info,
        #     status='pending',
        #     created_at=datetime.utcnow()
        # )
        # db.session.add(withdrawal_request)
        # db.session.commit()
        
        return True
    
    @staticmethod
    def get_provider_statistics(user_id):
        """Retorna estatísticas detalhadas do prestador"""
        user = User.query.get(user_id)
        
        # TODO: Implementar quando tivermos os modelos completos
        stats = {
            'prestador_desde': user.created_at,
            'total_ordens': 0,
            'ordens_concluidas': 0,
            'taxa_conclusao': 0.0,
            'ganhos_totais': 0.00,
            'media_ganho_ordem': 0.00,
            'clientes_atendidos': 0,
            'avaliacoes_recebidas': 0,
            'media_avaliacao': 0.0,
            'tempo_resposta_medio': 0,
            'categorias_atendidas': []
        }
        
        return stats
    
    @staticmethod
    def can_accept_order(user_id, order_id):
        """Verifica se o prestador pode aceitar uma ordem"""
        # TODO: Implementar validações:
        # - Verificar disponibilidade de horário
        # - Verificar se não excede limite de ordens simultâneas
        # - Verificar se tem as habilidades necessárias
        
        return True
    
    @staticmethod
    def get_order_recommendations(user_id):
        """Retorna ordens recomendadas para o prestador"""
        # TODO: Implementar algoritmo de recomendação baseado em:
        # - Histórico de ordens
        # - Especialidades do prestador
        # - Localização
        # - Avaliações
        
        return []
    
    @staticmethod
    def get_active_pre_orders(user_id):
        """
        Retorna pré-ordens ativas do prestador
        
        Args:
            user_id (int): ID do prestador
            
        Returns:
            list: Lista de pré-ordens ativas formatadas
        """
        from models import PreOrder, PreOrderStatus, User
        
        # Buscar pré-ordens ativas (não convertidas, canceladas ou expiradas)
        active_statuses = [
            PreOrderStatus.EM_NEGOCIACAO.value,
            PreOrderStatus.AGUARDANDO_RESPOSTA.value,
            PreOrderStatus.PRONTO_CONVERSAO.value
        ]
        
        pre_orders = PreOrder.query.filter(
            PreOrder.provider_id == user_id,
            PreOrder.status.in_(active_statuses)
        ).order_by(PreOrder.updated_at.desc()).all()
        
        # Formatar para exibição
        formatted_pre_orders = []
        for po in pre_orders:
            # Determinar se precisa de ação do prestador
            needs_action = False
            if po.has_active_proposal:
                proposal = po.get_active_proposal()
                if proposal and proposal.proposed_by != user_id:
                    needs_action = True
            elif po.status == PreOrderStatus.EM_NEGOCIACAO.value and not po.provider_accepted_terms:
                needs_action = True
            
            formatted_pre_orders.append({
                'id': po.id,
                'title': po.title,
                'current_value': float(po.current_value),
                'original_value': float(po.original_value),
                'status': po.status,
                'status_display': po.status_display,
                'status_color_class': po.status_color_class,
                'client_name': po.client.nome if po.client else 'Desconhecido',
                'client_id': po.client_id,
                'has_active_proposal': po.has_active_proposal,
                'needs_action': needs_action,
                'client_accepted_terms': po.client_accepted_terms,
                'provider_accepted_terms': po.provider_accepted_terms,
                'days_until_expiration': po.days_until_expiration,
                'is_near_expiration': po.is_near_expiration,
                'updated_at': po.updated_at,
                'created_at': po.created_at
            })
        
        return formatted_pre_orders
