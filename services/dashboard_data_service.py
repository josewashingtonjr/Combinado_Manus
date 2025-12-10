#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, Order, User, Wallet, Transaction
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from decimal import Decimal

class DashboardDataService:
    """Serviço para agregar dados das dashboards de cliente e prestador"""
    
    @staticmethod
    def get_open_orders(user_id, role):
        """
        Retorna ordens em aberto para o usuário
        
        Args:
            user_id (int): ID do usuário
            role (str): 'cliente' ou 'prestador'
            
        Returns:
            list: Lista de ordens com status aceita, em_andamento ou aguardando_confirmacao
        """
        # Status que representam ordens em aberto
        open_statuses = ['aceita', 'em_andamento', 'aguardando_confirmacao']
        
        # Construir query baseada no papel
        if role == 'cliente':
            query = Order.query.filter(
                and_(
                    Order.client_id == user_id,
                    Order.status.in_(open_statuses)
                )
            ).order_by(Order.created_at.desc())  # Cliente: mais recentes primeiro
            
        elif role == 'prestador':
            query = Order.query.filter(
                and_(
                    Order.provider_id == user_id,
                    Order.status.in_(open_statuses)
                )
            ).order_by(Order.service_deadline.asc())  # Prestador: mais urgentes primeiro
            
        else:
            raise ValueError(f"Role inválido: {role}. Use 'cliente' ou 'prestador'")
        
        orders = query.all()
        
        # Formatar dados para retorno
        result = []
        for order in orders:
            # Obter informações da parte relacionada
            if role == 'cliente':
                # Cliente vê informações do prestador
                related_user = User.query.get(order.provider_id) if order.provider_id else None
                related_user_name = related_user.nome if related_user else "Aguardando prestador"
                related_user_id = order.provider_id
            else:
                # Prestador vê informações do cliente
                related_user = User.query.get(order.client_id)
                related_user_name = related_user.nome if related_user else "Cliente desconhecido"
                related_user_id = order.client_id
            
            result.append({
                'id': order.id,
                'title': order.title,
                'description': order.description,
                'value': float(order.value),
                'status': order.status,
                'status_display': order.status_display,
                'status_color_class': order.status_color_class,
                'status_icon_class': order.status_icon_class,
                'created_at': order.created_at,
                'service_deadline': order.service_deadline,
                'related_user_id': related_user_id,
                'related_user_name': related_user_name,
                'is_overdue': order.is_overdue,
                'can_be_cancelled': order.can_be_cancelled,
                'can_be_marked_completed': order.can_be_marked_completed if role == 'prestador' else False,
                'can_be_confirmed': order.can_be_confirmed if role == 'cliente' else False,
                'can_be_disputed': order.can_be_disputed,
                'hours_until_auto_confirmation': order.hours_until_auto_confirmation,
                'is_near_auto_confirmation': order.is_near_auto_confirmation
            })
        
        return result
    
    @staticmethod
    def get_blocked_funds_summary(user_id):
        """
        Retorna resumo de fundos bloqueados em escrow por usuário
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            dict: {
                'total_blocked': Decimal,
                'by_order': [{'order_id', 'amount', 'title', 'status'}]
            }
        """
        # Obter carteira do usuário
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            return {
                'total_blocked': Decimal('0.00'),
                'by_order': []
            }
        
        total_blocked = wallet.escrow_balance
        
        # Buscar ordens que têm valores bloqueados para este usuário
        # Cliente: ordens onde ele é o cliente e status indica valor em escrow
        # Prestador: ordens onde ele é o prestador e há taxa de contestação bloqueada
        
        by_order = []
        
        # Para cliente: buscar ordens em aberto onde ele é o cliente
        client_orders = Order.query.filter(
            and_(
                Order.client_id == user_id,
                Order.status.in_(['aceita', 'em_andamento', 'aguardando_confirmacao', 'contestada'])
            )
        ).all()
        
        for order in client_orders:
            # O valor da ordem está bloqueado no escrow do cliente
            by_order.append({
                'order_id': order.id,
                'title': order.title,
                'amount': float(order.value),
                'status': order.status,
                'status_display': order.status_display,
                'created_at': order.created_at,
                'service_deadline': order.service_deadline,
                'blocked_type': 'valor_servico'  # Tipo de bloqueio
            })
        
        # Para prestador: buscar ordens onde ele é o prestador e há taxa bloqueada
        provider_orders = Order.query.filter(
            and_(
                Order.provider_id == user_id,
                Order.status.in_(['aceita', 'em_andamento', 'aguardando_confirmacao', 'contestada']),
                Order.contestation_fee.isnot(None),
                Order.contestation_fee > 0
            )
        ).all()
        
        for order in provider_orders:
            # Taxa de contestação bloqueada
            by_order.append({
                'order_id': order.id,
                'title': order.title,
                'amount': float(order.contestation_fee),
                'status': order.status,
                'status_display': order.status_display,
                'created_at': order.created_at,
                'service_deadline': order.service_deadline,
                'blocked_type': 'taxa_contestacao'  # Tipo de bloqueio
            })
        
        return {
            'total_blocked': float(total_blocked),
            'by_order': by_order
        }
    
    @staticmethod
    def get_dashboard_metrics(user_id, role):
        """
        Retorna todas as métricas para a dashboard
        
        Args:
            user_id (int): ID do usuário
            role (str): 'cliente' ou 'prestador'
            
        Returns:
            dict: Métricas completas incluindo:
                - Saldo disponível e bloqueado
                - Ordens em aberto por status
                - Estatísticas do mês
                - Alertas baseados em saldo e ordens
        """
        # 1. Obter informações da carteira
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            # Se não tem carteira, criar uma
            from services.wallet_service import WalletService
            wallet = WalletService.ensure_user_has_wallet(user_id)
        
        balance_info = {
            'available': float(wallet.balance),
            'blocked': float(wallet.escrow_balance),
            'total': float(wallet.balance + wallet.escrow_balance)
        }
        
        # 2. Obter ordens em aberto
        open_orders = DashboardDataService.get_open_orders(user_id, role)
        
        # 3. Contar ordens por status
        orders_by_status = {}
        for order in open_orders:
            status = order['status']
            orders_by_status[status] = orders_by_status.get(status, 0) + 1
        
        # 4. Obter fundos bloqueados detalhados
        blocked_funds = DashboardDataService.get_blocked_funds_summary(user_id)
        
        # 5. Calcular estatísticas do mês atual
        now = datetime.utcnow()
        first_day_of_month = datetime(now.year, now.month, 1)
        
        if role == 'cliente':
            # Estatísticas do cliente
            # Ordens criadas este mês
            orders_created_this_month = Order.query.filter(
                and_(
                    Order.client_id == user_id,
                    Order.created_at >= first_day_of_month
                )
            ).count()
            
            # Ordens concluídas este mês
            orders_completed_this_month = Order.query.filter(
                and_(
                    Order.client_id == user_id,
                    Order.status == 'concluida',
                    Order.completed_at >= first_day_of_month
                )
            ).count()
            
            # Total gasto este mês (ordens concluídas)
            total_spent_query = db.session.query(
                func.sum(Order.value)
            ).filter(
                and_(
                    Order.client_id == user_id,
                    Order.status == 'concluida',
                    Order.completed_at >= first_day_of_month
                )
            ).scalar()
            
            total_spent_this_month = float(total_spent_query) if total_spent_query else 0.0
            
            month_stats = {
                'orders_created': orders_created_this_month,
                'orders_completed': orders_completed_this_month,
                'total_spent': total_spent_this_month
            }
            
        else:  # prestador
            # Estatísticas do prestador
            # Ordens aceitas este mês
            orders_accepted_this_month = Order.query.filter(
                and_(
                    Order.provider_id == user_id,
                    Order.accepted_at >= first_day_of_month
                )
            ).count()
            
            # Ordens concluídas este mês
            orders_completed_this_month = Order.query.filter(
                and_(
                    Order.provider_id == user_id,
                    Order.status == 'concluida',
                    Order.completed_at >= first_day_of_month
                )
            ).count()
            
            # Total recebido este mês (transações de recebimento)
            total_received_query = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.type == 'recebimento',
                    Transaction.created_at >= first_day_of_month
                )
            ).scalar()
            
            total_received_this_month = float(total_received_query) if total_received_query else 0.0
            
            month_stats = {
                'orders_accepted': orders_accepted_this_month,
                'orders_completed': orders_completed_this_month,
                'total_received': total_received_this_month
            }
        
        # 6. Gerar alertas baseados em saldo e ordens
        alerts = []
        
        # Alerta de saldo baixo
        if balance_info['available'] < 100.0:
            alerts.append({
                'type': 'warning',
                'title': 'Saldo Baixo',
                'message': f'Seu saldo disponível está baixo: R$ {balance_info["available"]:.2f}',
                'action': 'Adicionar saldo',
                'action_url': '/cliente/solicitar_tokens' if role == 'cliente' else '/prestador/solicitar_tokens'
            })
        
        # Alerta de ordens atrasadas (para prestador)
        if role == 'prestador':
            overdue_orders = [o for o in open_orders if o.get('is_overdue')]
            if overdue_orders:
                alerts.append({
                    'type': 'danger',
                    'title': 'Ordens Atrasadas',
                    'message': f'Você tem {len(overdue_orders)} ordem(ns) atrasada(s)',
                    'action': 'Ver ordens',
                    'action_url': '/prestador/ordens'
                })
        
        # Alerta de confirmação automática próxima (para cliente)
        if role == 'cliente':
            near_auto_confirm = [o for o in open_orders if o.get('is_near_auto_confirmation')]
            if near_auto_confirm:
                alerts.append({
                    'type': 'info',
                    'title': 'Confirmação Automática Próxima',
                    'message': f'{len(near_auto_confirm)} ordem(ns) será(ão) confirmada(s) automaticamente em breve',
                    'action': 'Ver ordens',
                    'action_url': '/cliente/ordens'
                })
        
        # Alerta de muitas ordens em aberto
        if len(open_orders) > 5:
            alerts.append({
                'type': 'info',
                'title': 'Muitas Ordens em Aberto',
                'message': f'Você tem {len(open_orders)} ordens em aberto',
                'action': 'Gerenciar ordens',
                'action_url': f'/{role}/ordens'
            })
        
        # 7. Montar resposta completa
        return {
            'balance': balance_info,
            'open_orders': open_orders,
            'open_orders_count': len(open_orders),
            'orders_by_status': orders_by_status,
            'blocked_funds': blocked_funds,
            'month_stats': month_stats,
            'alerts': alerts,
            'generated_at': datetime.utcnow()
        }
