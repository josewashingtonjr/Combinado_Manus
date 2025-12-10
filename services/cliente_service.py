#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, Order, Transaction, db
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from services.wallet_service import WalletService
from services.dashboard_data_service import DashboardDataService

class ClienteService:
    """Serviço para operações da área do cliente"""
    
    @staticmethod
    def get_dashboard_data(user_id):
        """Retorna dados reais para o dashboard do cliente com terminologia em R$"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Usar DashboardDataService para obter métricas completas
        metrics = DashboardDataService.get_dashboard_metrics(user_id, 'cliente')
        
        # Obter ordens em aberto formatadas
        open_orders = metrics['open_orders']
        
        # Obter fundos bloqueados detalhados
        blocked_funds = metrics['blocked_funds']
        
        # Início do mês atual para filtros
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Contar transações do mês atual
        transacoes_mes = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= inicio_mes
        ).count()
        
        # Contar ordens concluídas (total histórico)
        ordens_concluidas = Order.query.filter(
            Order.client_id == user_id,
            Order.status == 'concluida'
        ).count()
        
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
        
        # Formatar próximas ordens (primeiras 3 ordens em aberto)
        proximas_ordens = []
        for ordem in open_orders[:3]:
            proximas_ordens.append({
                'id': ordem['id'],
                'titulo': ordem['title'],
                'data': ordem['created_at'].strftime('%d/%m/%Y'),
                'status': ordem['status'],
                'status_display': ordem['status_display'],
                'valor': ordem['value'],
                'prestador': ordem['related_user_name']
            })
        
        # Converter alertas do DashboardDataService para formato legado
        alertas = []
        
        # Adicionar notificações de propostas pendentes
        from services.notification_service import NotificationService
        proposal_notifications = NotificationService.get_proposal_notifications_for_client(user_id)
        alertas.extend(proposal_notifications)
        
        # Adicionar alertas do DashboardDataService
        for alert in metrics['alerts']:
            alertas.append({
                'tipo': alert['type'],
                'mensagem': alert['message'],
                'titulo': alert.get('title', ''),
                'action': alert.get('action', ''),
                'action_url': alert.get('action_url', '')
            })
        
        # Alerta adicional se tem saldo bloqueado
        if metrics['balance']['blocked'] > 0:
            alertas.append({
                'tipo': 'info',
                'mensagem': f'Você tem R$ {metrics["balance"]["blocked"]:.2f} em garantia para ordens ativas.'
            })
        
        # Alerta se não tem ordens ativas há muito tempo
        if metrics['open_orders_count'] == 0 and metrics['balance']['available'] > 0:
            alertas.append({
                'tipo': 'info',
                'mensagem': 'Que tal criar uma nova ordem de serviço?'
            })
        
        # Buscar pré-ordens ativas
        pre_orders_ativas = ClienteService.get_active_pre_orders(user_id)
        pre_orders_count = len(pre_orders_ativas)
        pre_orders_needing_action = len([po for po in pre_orders_ativas if po['needs_action']])
        
        dashboard_data = {
            # Valores em formato numérico (serão convertidos para R$ no template)
            'saldo_atual': metrics['balance']['available'],
            'tokens_disponiveis': metrics['balance']['available'],  # Terminologia interna, será exibido como "Saldo Disponível"
            'saldo_bloqueado': metrics['balance']['blocked'],
            
            # Contadores
            'transacoes_mes': transacoes_mes,
            'ordens_ativas': metrics['open_orders_count'],
            'ordens_concluidas': ordens_concluidas,
            
            # Valores financeiros
            'gasto_total_mes': metrics['month_stats']['total_spent'],
            'economia_mes': 0.0,  # TODO: Implementar cálculo de economia
            
            # Atividades
            'ultima_transacao': ultima_transacao,
            'proximas_ordens': proximas_ordens,
            'alertas': alertas,
            
            # Novos dados do DashboardDataService
            'ordens_em_aberto': open_orders,  # Lista completa de ordens em aberto
            'fundos_bloqueados_detalhados': blocked_funds['by_order'],  # Detalhamento por ordem
            'ordens_por_status': metrics['orders_by_status'],  # Contagem por status
            
            # Pré-ordens
            'pre_orders_ativas': pre_orders_ativas,
            'pre_orders_count': pre_orders_count,
            'pre_orders_needing_action': pre_orders_needing_action,
            
            # Estatísticas adicionais
            'total_gasto_historico': ClienteService._calcular_gasto_total(user_id),
            'media_valor_ordem': ClienteService._calcular_media_valor_ordem(user_id),
            'taxa_conclusao': ClienteService._calcular_taxa_conclusao(user_id)
        }
        
        return dashboard_data
    
    @staticmethod
    def get_open_orders_for_client(user_id):
        """
        Retorna lista de ordens em aberto para o cliente
        
        Args:
            user_id (int): ID do cliente
            
        Returns:
            list: Lista formatada de ordens em aberto
        """
        # Usar DashboardDataService para obter ordens em aberto
        open_orders = DashboardDataService.get_open_orders(user_id, 'cliente')
        
        # Formatar para template (já vem formatado do DashboardDataService)
        return open_orders
    
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
    def create_token_request(user_id, amount, description, auto_approve=False):
        """Cria uma solicitação de tokens para aprovação do admin"""
        from models import TokenRequest
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        # Validações
        if amount <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        
        if amount > 10000:  # Limite máximo por solicitação
            raise ValueError('Quantidade excede o limite máximo de 10.000 tokens')
        
        # Criar registro na tabela token_requests
        status = 'approved' if auto_approve else 'pending'
        token_request = TokenRequest(
            user_id=user_id,
            amount=amount,
            description=description or 'Solicitação de tokens',
            status=status
        )
        
        # Se auto_approve, definir data de processamento
        if auto_approve:
            token_request.processed_at = datetime.utcnow()
        
        db.session.add(token_request)
        db.session.commit()
        
        return {
            'request_id': token_request.id,
            'status': token_request.status,
            'amount': token_request.amount,
            'auto_approved': auto_approve
        }
    
    @staticmethod
    def create_token_request_with_receipt(user_id, amount, description, payment_method, receipt_file):
        """Cria uma solicitação de tokens com upload de comprovante"""
        from models import TokenRequest
        from datetime import datetime
        import os
        import uuid
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')
        
        # Validações
        if amount <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        
        if amount > 10000:  # Limite máximo por solicitação
            raise ValueError('Quantidade excede o limite máximo de 10.000 tokens')
        
        # Processar upload do arquivo
        receipt_filename = None
        receipt_original_name = None
        
        if receipt_file and receipt_file.filename:
            # Criar diretório se não existir
            upload_dir = 'uploads/receipts'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Gerar nome único para o arquivo
            file_extension = receipt_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}.{file_extension}"
            
            # Salvar arquivo
            file_path = os.path.join(upload_dir, unique_filename)
            receipt_file.save(file_path)
            
            receipt_filename = unique_filename
            receipt_original_name = receipt_file.filename
        
        # Criar registro na tabela token_requests
        token_request = TokenRequest(
            user_id=user_id,
            amount=amount,
            description=description or f'Solicitação via {payment_method.upper()}',
            status='pending',
            payment_method=payment_method,
            receipt_filename=receipt_filename,
            receipt_original_name=receipt_original_name,
            receipt_uploaded_at=datetime.utcnow() if receipt_filename else None
        )
        
        db.session.add(token_request)
        db.session.commit()
        
        return token_request
    
    @staticmethod
    def get_user_token_requests(user_id, limit=10):
        """Obtém as solicitações de tokens do usuário"""
        from models import TokenRequest
        
        requests = TokenRequest.query.filter_by(user_id=user_id)\
                                   .order_by(TokenRequest.created_at.desc())\
                                   .limit(limit).all()
        
        return requests
    
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
    
    @staticmethod
    def get_active_pre_orders(user_id):
        """
        Retorna pré-ordens ativas do cliente
        
        Args:
            user_id (int): ID do cliente
            
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
            PreOrder.client_id == user_id,
            PreOrder.status.in_(active_statuses)
        ).order_by(PreOrder.updated_at.desc()).all()
        
        # Formatar para exibição
        formatted_pre_orders = []
        for po in pre_orders:
            # Determinar se precisa de ação do cliente
            needs_action = False
            if po.has_active_proposal:
                proposal = po.get_active_proposal()
                if proposal and proposal.proposed_by != user_id:
                    needs_action = True
            elif po.status == PreOrderStatus.EM_NEGOCIACAO.value and not po.client_accepted_terms:
                needs_action = True
            
            formatted_pre_orders.append({
                'id': po.id,
                'title': po.title,
                'current_value': float(po.current_value),
                'original_value': float(po.original_value),
                'status': po.status,
                'status_display': po.status_display,
                'status_color_class': po.status_color_class,
                'provider_name': po.provider.nome if po.provider else 'Desconhecido',
                'provider_id': po.provider_id,
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
