#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Order, OrderStatusHistory, Invite
from services.wallet_service import WalletService
from services.order_status_validator import OrderStatusValidator
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from flask import request

class OrderService:
    """Serviço para gerenciar ordens de serviço seguindo arquitetura de escrow"""
    
    @staticmethod
    def _change_order_status(order_id, new_status, user_id=None, admin_id=None, reason=None):
        """
        Método auxiliar para mudança de status com validação e histórico
        
        Args:
            order_id (int): ID da ordem
            new_status (str): Novo status desejado
            user_id (int, optional): ID do usuário fazendo a mudança
            admin_id (int, optional): ID do admin fazendo a mudança
            reason (str, optional): Motivo da mudança
            
        Returns:
            dict: Resultado da operação com sucesso/erro
        """
        try:
            # Buscar ordem atual
            order = Order.query.get(order_id)
            if not order:
                return {
                    'success': False,
                    'error': f"Ordem {order_id} não encontrada",
                    'error_code': 'ORDER_NOT_FOUND'
                }
            
            current_status = order.status
            
            # Validar transição usando OrderStatusValidator
            validation_result = OrderStatusValidator.validate_transition(
                order_id=order_id,
                current_status=current_status,
                new_status=new_status,
                user_id=user_id,
                admin_id=admin_id,
                reason=reason
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'error_code': validation_result.get('error_code', 'VALIDATION_FAILED'),
                    'valid_transitions': validation_result.get('valid_transitions', [])
                }
            
            # Realizar mudança de status
            order.status = new_status
            
            # Registrar no histórico
            OrderService._record_status_change(
                order_id=order_id,
                previous_status=current_status,
                new_status=new_status,
                user_id=user_id,
                admin_id=admin_id,
                reason=reason
            )
            
            # Commit das mudanças
            db.session.commit()
            
            return {
                'success': True,
                'previous_status': current_status,
                'new_status': new_status,
                'message': validation_result.get('message', f'Status alterado para {new_status}'),
                'description': validation_result.get('description', '')
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Erro no banco de dados: {str(e)}",
                'error_code': 'DATABASE_ERROR'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Erro interno: {str(e)}",
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def _record_status_change(order_id, previous_status, new_status, user_id=None, admin_id=None, reason=None):
        """
        Registra mudança de status no histórico
        
        Args:
            order_id (int): ID da ordem
            previous_status (str): Status anterior
            new_status (str): Novo status
            user_id (int, optional): ID do usuário
            admin_id (int, optional): ID do admin
            reason (str, optional): Motivo da mudança
        """
        try:
            # Capturar informações da requisição se disponível
            ip_address = None
            user_agent = None
            
            if request:
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')[:255]  # Limitar tamanho
            
            # Criar registro no histórico
            history_record = OrderStatusHistory(
                order_id=order_id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by_user_id=user_id,
                changed_by_admin_id=admin_id,
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.add(history_record)
            
        except Exception as e:
            # Não falhar a operação principal por erro de histórico
            print(f"Erro ao registrar histórico de status: {str(e)}")
    
    @staticmethod
    def get_order_status_history(order_id):
        """
        Retorna o histórico de mudanças de status de uma ordem
        
        Args:
            order_id (int): ID da ordem
            
        Returns:
            list: Lista de mudanças de status ordenada por data
        """
        try:
            history = OrderStatusHistory.query.filter_by(order_id=order_id)\
                                            .order_by(OrderStatusHistory.created_at.desc())\
                                            .all()
            
            return [{
                'id': record.id,
                'previous_status': record.previous_status,
                'new_status': record.new_status,
                'changed_by_user_id': record.changed_by_user_id,
                'changed_by_admin_id': record.changed_by_admin_id,
                'reason': record.reason,
                'created_at': record.created_at,
                'ip_address': record.ip_address
            } for record in history]
            
        except Exception as e:
            return []

    @staticmethod
    def create_order(client_id, title, description, value, invite_id=None, proposal_id=None):
        """
        Cria uma nova ordem de serviço com bloqueio automático de tokens em escrow
        
        Fluxo conforme Planta Arquitetônica seção 5.1:
        1. Validar saldo suficiente do cliente
        2. Criar ordem com status 'disponivel'
        3. Transferir tokens do saldo→escrow (transfer_to_escrow)
        4. Registrar transação de bloqueio
        5. Incluir histórico de proposta se aplicável
        """
        if value <= 0:
            raise ValueError("O valor da ordem deve ser positivo")

        # Garantir que o cliente tem carteira
        try:
            WalletService.ensure_user_has_wallet(client_id)
        except Exception as e:
            raise ValueError(f"Erro ao verificar carteira do cliente: {str(e)}")

        # Se há um convite associado, usar o valor efetivo
        effective_value = value
        proposal_history = None
        
        if invite_id:
            from models import Invite, Proposal
            invite = Invite.query.get(invite_id)
            if invite:
                # Se o convite foi convertido para pré-ordem, usar o valor passado
                # (que vem da pré-ordem com valor negociado)
                # Caso contrário, usar valor efetivo do convite
                if invite.status != 'convertido_pre_ordem':
                    effective_value = invite.current_value
                
                # Se há uma proposta aceita, incluir no histórico
                if invite.current_proposal_id:
                    proposal = Proposal.query.get(invite.current_proposal_id)
                    if proposal and proposal.status == 'accepted':
                        proposal_history = {
                            'proposal_id': proposal.id,
                            'original_value': float(proposal.original_value),
                            'proposed_value': float(proposal.proposed_value),
                            'justification': proposal.justification,
                            'created_at': proposal.created_at.isoformat(),
                            'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None
                        }

        # Verificar se o cliente tem saldo suficiente para o escrow
        try:
            if not WalletService.has_sufficient_balance(client_id, effective_value):
                current_balance = WalletService.get_wallet_balance(client_id)
                raise ValueError(f"Saldo insuficiente para criar a ordem. Saldo atual: R$ {current_balance:.2f}, valor necessário: R$ {effective_value:.2f}")
        except Exception as e:
            raise ValueError(f"Erro ao verificar saldo: {str(e)}")

        try:
            # Determinar service_deadline
            # Se há convite, usar a data de entrega do convite
            service_deadline = None
            if invite_id:
                invite = Invite.query.get(invite_id)
                if invite:
                    service_deadline = invite.delivery_date
            
            # Se não há convite ou data, usar 7 dias a partir de agora
            if not service_deadline:
                service_deadline = datetime.utcnow() + timedelta(days=7)
            
            # Criar ordem com status inicial 'disponivel'
            order = Order(
                client_id=client_id,
                title=title,
                description=description,
                value=effective_value,  # Usar valor efetivo
                status='disponivel',
                created_at=datetime.utcnow(),
                service_deadline=service_deadline,
                invite_id=invite_id  # Referência ao convite se aplicável
            )
            
            # Adicionar histórico de proposta como metadados se existir
            if proposal_history:
                # Armazenar histórico no campo de descrição ou criar campo específico
                order.description = f"{description}\n\n--- Histórico da Proposta ---\nValor Original: R$ {proposal_history['original_value']:.2f}\nValor Proposto: R$ {proposal_history['proposed_value']:.2f}\nJustificativa: {proposal_history['justification']}"
            
            db.session.add(order)
            db.session.flush()  # Para obter o ID da ordem antes do commit

            # Transferir valor efetivo para escrow (saldo→escrow)
            # Tokens não saem do sistema, apenas mudam de estado
            escrow_result = WalletService.transfer_to_escrow(client_id, effective_value, order.id)
            
            db.session.commit()

            return {
                'order': order,
                'effective_value': effective_value,
                'original_value': value,
                'proposal_history': proposal_history,
                'escrow_transaction_id': escrow_result['transaction_id'],
                'new_balance': escrow_result['new_balance'],
                'new_escrow_balance': escrow_result['new_escrow_balance']
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao criar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def accept_order(provider_id, order_id):
        """
        Aceita uma ordem de serviço seguindo o fluxo de estados conforme design:
        disponivel → aceita → em_andamento
        
        Validações implementadas:
        - Verificar se ordem existe e está disponível
        - Verificar se prestador não é o mesmo cliente
        - Validar disponibilidade do prestador
        - Atualizar status e registrar prestador responsável
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        # Verificar se o prestador não é o mesmo cliente que criou a ordem
        if order.client_id == provider_id:
            raise ValueError("Você não pode aceitar sua própria ordem")

        # Verificar se o prestador existe e tem papel correto
        from models import User
        provider = User.query.get(provider_id)
        if not provider:
            raise ValueError("Prestador não encontrado")
        
        if 'prestador' not in provider.roles:
            raise ValueError("Usuário não tem permissão para aceitar ordens")

        # Verificar conflitos de horário (implementação básica)
        # TODO: Implementar verificação mais sofisticada quando tivermos datas/horários específicos
        active_orders = Order.query.filter_by(
            provider_id=provider_id,
            status='em_andamento'
        ).count()
        
        # Limite de ordens simultâneas (configurável)
        max_concurrent_orders = 5
        if active_orders >= max_concurrent_orders:
            raise ValueError(f"Você já tem {active_orders} ordens em andamento. Limite máximo: {max_concurrent_orders}")

        try:
            # Validar transição de status usando OrderStatusValidator
            status_change_result = OrderService._change_order_status(
                order_id=order_id,
                new_status='aceita',
                user_id=provider_id,
                reason=f"Ordem aceita pelo prestador {provider_id}"
            )
            
            if not status_change_result['success']:
                raise ValueError(status_change_result['error'])
            
            # Atualizar ordem com prestador
            order.provider_id = provider_id
            order.accepted_at = datetime.utcnow()
            
            db.session.commit()
            
            # TODO: Implementar notificação para o cliente sobre aceitação
            # NotificationService.notify_client_order_accepted(order.client_id, order_id, provider_id)
            
            return {
                'success': True,
                'order_id': order.id,
                'new_status': order.status,
                'accepted_at': order.accepted_at,
                'provider_id': provider_id,
                'status_change_details': status_change_result
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao aceitar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def complete_order(user_id, order_id):
        """
        Marca uma ordem como concluída seguindo o fluxo de confirmação
        
        Fluxo conforme Planta Arquitetônica seção 7.5:
        1. Prestador marca como concluída → status 'aguardando_confirmacao'
        2. Cliente confirma → status 'concluida' + liberação de pagamento
        3. Pagamento: tokens→prestador, taxa→admin (release_from_escrow)
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if user_id not in [order.client_id, order.provider_id]:
            raise ValueError("Usuário não autorizado a concluir esta ordem")

        try:
            # Se o prestador marca como concluída, aguarda confirmação do cliente
            if user_id == order.provider_id:
                if order.status in ['aceita', 'em_andamento']:
                    # Validar transição para aguardando_confirmacao
                    status_change_result = OrderService._change_order_status(
                        order_id=order_id,
                        new_status='aguardando_confirmacao',
                        user_id=user_id,
                        reason=f"Prestador {user_id} marcou ordem como concluída"
                    )
                    
                    if not status_change_result['success']:
                        raise ValueError(status_change_result['error'])
                    
                    # TODO: Implementar notificação para o cliente
                    # NotificationService.notify_client_completion_request(order.client_id, order_id)
                    
                    return {
                        'success': True,
                        'status': 'aguardando_confirmacao',
                        'message': 'Ordem marcada como concluída. Aguardando confirmação do cliente.',
                        'requires_client_confirmation': True,
                        'status_change_details': status_change_result
                    }
                else:
                    raise ValueError("Ordem já foi marcada como concluída pelo prestador")

            # Se o cliente confirma, a ordem é concluída e o pagamento liberado
            if user_id == order.client_id:
                # Validar transição para concluida
                status_change_result = OrderService._change_order_status(
                    order_id=order_id,
                    new_status='concluida',
                    user_id=user_id,
                    reason=f"Cliente {user_id} confirmou conclusão da ordem"
                )
                
                if not status_change_result['success']:
                    raise ValueError(status_change_result['error'])
                
                # Marcar data de conclusão
                order.completed_at = datetime.utcnow()
                db.session.commit()

                # Liberar pagamento do escrow com taxa configurável
                from services.wallet_service import WalletService
                payment_result = WalletService.release_from_escrow(order.id, system_fee_percent=0.05)
                
                # TODO: Implementar notificação para o prestador sobre pagamento
                # NotificationService.notify_provider_payment_released(order.provider_id, order_id, payment_result)
                
                return {
                    'success': True,
                    'status': 'concluida',
                    'message': 'Ordem concluída e pagamento liberado com sucesso!',
                    'payment_details': {
                        'total_value': payment_result['order_value'],
                        'provider_amount': payment_result['provider_amount'],
                        'system_fee': payment_result['system_fee'],
                        'fee_percentage': payment_result['system_fee_percent'] * 100
                    },
                    'completed_at': order.completed_at,
                    'status_change_details': status_change_result
                }

        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao concluir ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def cancel_order(user_id, order_id, reason=""):
        """
        Cancela uma ordem de serviço com devolução de escrow
        
        Fluxo conforme Planta Arquitetônica seção 7.4:
        1. Validar se ordem pode ser cancelada
        2. Verificar prazos e motivos válidos
        3. Devolver tokens do escrow para o cliente (refund_from_escrow)
        4. Garantir que tokens sempre retornam ao estado correto
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if user_id not in [order.client_id, order.provider_id]:
            raise ValueError("Usuário não autorizado a cancelar esta ordem")

        try:
            # Validar transição para cancelada usando OrderStatusValidator
            status_change_result = OrderService._change_order_status(
                order_id=order_id,
                new_status='cancelada',
                user_id=user_id,
                reason=reason or f"Ordem cancelada pelo usuário {user_id}"
            )
            
            if not status_change_result['success']:
                raise ValueError(status_change_result['error'])
            
            old_status = status_change_result['previous_status']

            # Se havia valor em escrow, reembolsar o cliente
            refund_result = None
            if old_status in ['aceita', 'em_andamento']:
                from services.wallet_service import WalletService
                refund_result = WalletService.refund_from_escrow(order.id)
                
                # TODO: Implementar notificação sobre cancelamento
                # NotificationService.notify_cancellation(order.client_id, order.provider_id, order_id, reason)

            return {
                'success': True,
                'order_id': order.id,
                'previous_status': old_status,
                'new_status': order.status,
                'refund_processed': refund_result is not None,
                'refund_amount': refund_result['refunded_amount'] if refund_result else 0,
                'reason': reason,
                'status_change_details': status_change_result
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao cancelar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def open_dispute(user_id, order_id, reason):
        """
        Abre uma disputa para uma ordem com bloqueio de tokens até resolução admin
        
        Fluxo conforme Planta Arquitetônica seção 7.4:
        1. Validar se disputa pode ser aberta
        2. Bloquear tokens em escrow até resolução
        3. Criar registro de disputa para análise admin
        4. Notificar ambas as partes e admin
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if user_id not in [order.client_id, order.provider_id]:
            raise ValueError("Usuário não autorizado a abrir disputa para esta ordem")

        if not reason or len(reason.strip()) < 10:
            raise ValueError("Motivo da disputa deve ter pelo menos 10 caracteres")

        try:
            # Validar transição para disputada usando OrderStatusValidator
            status_change_result = OrderService._change_order_status(
                order_id=order_id,
                new_status='disputada',
                user_id=user_id,
                reason=reason
            )
            
            if not status_change_result['success']:
                raise ValueError(status_change_result['error'])
            
            old_status = status_change_result['previous_status']
            
            # Registrar detalhes da disputa
            order.dispute_reason = reason
            order.dispute_opened_by = user_id
            order.dispute_opened_at = datetime.utcnow()
            
            db.session.commit()
            
            # TODO: Implementar notificações
            # NotificationService.notify_dispute_opened(order.client_id, order.provider_id, order_id, reason)
            # NotificationService.notify_admin_dispute_pending(order_id, user_id, reason)

            return {
                'success': True,
                'order_id': order.id,
                'previous_status': old_status,
                'new_status': order.status,
                'opened_by': user_id,
                'reason': reason,
                'message': 'Disputa aberta com sucesso. Aguarde análise administrativa.',
                'status_change_details': status_change_result
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao abrir disputa: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def resolve_dispute(admin_id, order_id, decision, admin_notes=""):
        """
        Resolve uma disputa com decisão administrativa
        
        Decisões possíveis:
        - 'favor_cliente': Reembolso total para o cliente
        - 'favor_prestador': Pagamento total para o prestador
        - 'dividir_50_50': Dividir valor meio a meio
        - 'dividir_custom': Divisão personalizada (requer percentuais)
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        # Verificar se usuário é admin
        from models import AdminUser
        admin = AdminUser.query.get(admin_id)
        if not admin:
            raise ValueError("Apenas administradores podem resolver disputas")

        valid_decisions = ['favor_cliente', 'favor_prestador', 'dividir_50_50']
        if decision not in valid_decisions:
            raise ValueError(f"Decisão inválida. Opções: {', '.join(valid_decisions)}")

        try:
            # Determinar novo status baseado na decisão
            if decision == 'favor_cliente':
                new_status = 'cancelada'  # Reembolso = cancelamento
            elif decision == 'favor_prestador':
                new_status = 'concluida'  # Pagamento = conclusão
            else:  # dividir_50_50
                new_status = 'resolvida'  # Status específico para divisão
            
            # Validar transição usando OrderStatusValidator
            status_change_result = OrderService._change_order_status(
                order_id=order_id,
                new_status=new_status,
                admin_id=admin_id,
                reason=f"Disputa resolvida: {decision}. Notas: {admin_notes}"
            )
            
            if not status_change_result['success']:
                raise ValueError(status_change_result['error'])
            
            # Processar decisão conforme tipo
            if decision == 'favor_cliente':
                # Reembolso total para o cliente
                from services.wallet_service import WalletService
                refund_result = WalletService.refund_from_escrow(order.id)
                
                result_details = {
                    'client_amount': refund_result['refunded_amount'],
                    'provider_amount': 0,
                    'admin_fee': 0
                }
                
            elif decision == 'favor_prestador':
                # Pagamento total para o prestador (com taxa admin)
                from services.wallet_service import WalletService
                payment_result = WalletService.release_from_escrow(order.id, system_fee_percent=0.05)
                
                result_details = {
                    'client_amount': 0,
                    'provider_amount': payment_result['provider_amount'],
                    'admin_fee': payment_result['system_fee']
                }
                
            elif decision == 'dividir_50_50':
                # Dividir valor meio a meio (sem taxa admin neste caso)
                half_value = order.value / 2
                
                # Implementar divisão 50/50
                from services.wallet_service import WalletService
                client_wallet = WalletService.get_wallet_info(order.client_id)
                
                if client_wallet['escrow_balance'] < order.value:
                    raise ValueError("Saldo em escrow insuficiente para divisão")
                
                # Liberar escrow e dividir
                # TODO: Implementar método específico para divisão personalizada
                # Por enquanto, usar métodos existentes
                
                result_details = {
                    'client_amount': half_value,
                    'provider_amount': half_value,
                    'admin_fee': 0
                }

            # Registrar detalhes da resolução
            order.dispute_resolved_at = datetime.utcnow()
            order.dispute_resolution = f"Decisão: {decision}. Notas: {admin_notes}"
            db.session.commit()

            # TODO: Implementar notificações
            # NotificationService.notify_dispute_resolved(order.client_id, order.provider_id, order_id, decision)

            return {
                'success': True,
                'order_id': order.id,
                'decision': decision,
                'result_details': result_details,
                'admin_notes': admin_notes,
                'message': f'Disputa resolvida: {decision.replace("_", " ").title()}',
                'status_change_details': status_change_result
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao resolver disputa: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise e

    # ==============================================================================
    #  MÉTODOS AUXILIARES PARA CONSULTAS
    # ==============================================================================

    @staticmethod
    def get_available_orders(page=1, per_page=10):
        """Retorna ordens disponíveis para prestadores"""
        orders = Order.query.filter_by(status='disponivel')\
                           .order_by(Order.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
        return orders

    @staticmethod
    def get_client_orders(client_id, page=1, per_page=10):
        """Retorna ordens criadas por um cliente"""
        orders = Order.query.filter_by(client_id=client_id)\
                           .order_by(Order.created_at.desc())\
                           .paginate(page=page, per_page=per_page, error_out=False)
        return orders

    @staticmethod
    def get_provider_orders(provider_id, page=1, per_page=10, status_filter=None):
        """Retorna ordens aceitas por um prestador"""
        query = Order.query.filter_by(provider_id=provider_id)
        
        if status_filter and status_filter != 'todas':
            query = query.filter_by(status=status_filter)
            
        orders = query.order_by(Order.created_at.desc())\
                     .paginate(page=page, per_page=per_page, error_out=False)
        return orders

    @staticmethod
    def get_order_by_id(order_id):
        """Retorna uma ordem específica por ID"""
        return Order.query.get(order_id)

    @staticmethod
    def validate_order_creation(client_id, value):
        """Valida se uma ordem pode ser criada"""
        try:
            # Verificar se usuário existe e tem carteira
            WalletService.ensure_user_has_wallet(client_id)
            
            # Verificar saldo suficiente
            if not WalletService.has_sufficient_balance(client_id, value):
                current_balance = WalletService.get_wallet_balance(client_id)
                return {
                    'valid': False,
                    'error': f'Saldo insuficiente. Saldo atual: R$ {current_balance:.2f}, necessário: R$ {value:.2f}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro na validação: {str(e)}'
            }
    
    @staticmethod
    def get_valid_status_transitions(order_id):
        """
        Retorna as transições de status válidas para uma ordem
        
        Args:
            order_id (int): ID da ordem
            
        Returns:
            dict: Transições válidas e informações da ordem
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return {
                    'success': False,
                    'error': 'Ordem não encontrada'
                }
            
            valid_transitions = OrderStatusValidator.get_valid_transitions(order.status)
            
            return {
                'success': True,
                'order_id': order_id,
                'current_status': order.status,
                'valid_transitions': valid_transitions,
                'is_final_status': OrderStatusValidator.is_final_status(order.status)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao consultar transições: {str(e)}'
            }
    
    @staticmethod
    def validate_status_change(order_id, new_status, user_id=None, admin_id=None, reason=None):
        """
        Valida uma mudança de status sem executá-la
        
        Args:
            order_id (int): ID da ordem
            new_status (str): Novo status desejado
            user_id (int, optional): ID do usuário
            admin_id (int, optional): ID do admin
            reason (str, optional): Motivo da mudança
            
        Returns:
            dict: Resultado da validação
        """
        try:
            order = Order.query.get(order_id)
            if not order:
                return {
                    'valid': False,
                    'error': 'Ordem não encontrada'
                }
            
            # Usar OrderStatusValidator para validar sem executar
            validation_result = OrderStatusValidator.validate_transition(
                order_id=order_id,
                current_status=order.status,
                new_status=new_status,
                user_id=user_id,
                admin_id=admin_id,
                reason=reason
            )
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro na validação: {str(e)}'
            }

    @staticmethod
    def create_order_from_invite(invite_id, provider_id):
        """
        Cria uma ordem de serviço a partir de um convite aceito
        
        Este método é específico para conversão de convites e garante que:
        1. O valor efetivo (original ou proposto aceito) seja usado
        2. O histórico da proposta seja incluído na ordem
        3. O saldo correto seja reservado
        4. A referência à proposta aceita seja mantida
        
        Args:
            invite_id (int): ID do convite aceito
            provider_id (int): ID do prestador que aceitou
            
        Returns:
            dict: Resultado da criação da ordem
        """
        from models import Invite, Proposal
        
        invite = Invite.query.get(invite_id)
        if not invite:
            raise ValueError("Convite não encontrado")
        
        if invite.status != 'aceito':
            raise ValueError("Apenas convites aceitos podem ser convertidos em ordens")
        
        # Usar valor efetivo (original ou proposto aceito)
        effective_value = invite.current_value
        
        # Preparar histórico de proposta se existir
        proposal_history = None
        proposal_reference = None
        
        if invite.current_proposal_id:
            proposal = Proposal.query.get(invite.current_proposal_id)
            if proposal and proposal.status == 'accepted':
                proposal_history = {
                    'proposal_id': proposal.id,
                    'original_value': float(proposal.original_value),
                    'proposed_value': float(proposal.proposed_value),
                    'justification': proposal.justification,
                    'created_at': proposal.created_at.isoformat(),
                    'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None
                }
                proposal_reference = proposal.id
        
        try:
            # Log início da criação
            # Requirements: 9.1, 9.2, 9.4
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(
                f"INICIANDO CRIAÇÃO ORDEM: Convite {invite_id}, "
                f"Cliente: {invite.client_id}, Prestador: {provider_id}, "
                f"Valor efetivo: R$ {effective_value:.2f}, "
                f"Valor original: R$ {invite.original_value:.2f}, "
                f"Tem proposta: {proposal_reference is not None}"
            )
            
            # Criar ordem usando o método principal com todas as validações
            order_result = OrderService.create_order(
                client_id=invite.client_id,
                title=invite.service_title,
                description=invite.service_description,
                value=effective_value,
                invite_id=invite_id,
                proposal_id=proposal_reference
            )
            
            order = order_result['order']
            
            # Log do bloqueio de valores
            # Requirements: 9.1, 9.2, 9.4
            logger.info(
                f"VALORES BLOQUEADOS: Ordem #{order.id}, "
                f"Valor bloqueado: R$ {effective_value:.2f}, "
                f"Transaction ID: {order_result['escrow_transaction_id']}, "
                f"Novo saldo cliente: R$ {order_result['new_balance']:.2f}, "
                f"Novo escrow cliente: R$ {order_result['new_escrow_balance']:.2f}"
            )
            
            # Atualizar ordem com prestador e status aceita
            order.provider_id = provider_id
            order.status = 'aceita'
            order.accepted_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log final de sucesso
            # Requirements: 9.1, 9.2, 9.4
            logger.info(
                f"ORDEM CRIADA COM SUCESSO: Ordem #{order.id} criada a partir do convite {invite_id}. "
                f"Cliente: {invite.client_id}, Prestador: {provider_id}, "
                f"Valor: R$ {effective_value:.2f}, Status: aceita, "
                f"Timestamp: {order.accepted_at.isoformat()}, "
                f"Proposta ID: {proposal_reference if proposal_reference else 'N/A'}"
            )
            
            return {
                'success': True,
                'order': order,
                'order_id': order.id,
                'effective_value': effective_value,
                'original_value': float(invite.original_value),
                'proposal_history': proposal_history,
                'escrow_details': {
                    'transaction_id': order_result['escrow_transaction_id'],
                    'new_balance': order_result['new_balance'],
                    'new_escrow_balance': order_result['new_escrow_balance']
                },
                'message': f'Ordem #{order.id} criada com sucesso a partir do convite'
            }
            
        except Exception as e:
            db.session.rollback()
            # Log de erro detalhado
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO CRIAÇÃO ORDEM: Falha ao criar ordem do convite {invite_id}. "
                f"Cliente: {invite.client_id}, Prestador: {provider_id}, "
                f"Valor: R$ {effective_value:.2f}, Erro: {str(e)}",
                exc_info=True
            )
            raise e
