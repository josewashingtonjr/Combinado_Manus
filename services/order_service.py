#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Order
from services.wallet_service import WalletService
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class OrderService:
    """Serviço para gerenciar ordens de serviço seguindo arquitetura de escrow"""

    @staticmethod
    def create_order(client_id, title, description, value):
        """
        Cria uma nova ordem de serviço com bloqueio automático de tokens em escrow
        
        Fluxo conforme Planta Arquitetônica seção 5.1:
        1. Validar saldo suficiente do cliente
        2. Criar ordem com status 'disponivel'
        3. Transferir tokens do saldo→escrow (transfer_to_escrow)
        4. Registrar transação de bloqueio
        """
        if value <= 0:
            raise ValueError("O valor da ordem deve ser positivo")

        # Garantir que o cliente tem carteira
        try:
            WalletService.ensure_user_has_wallet(client_id)
        except Exception as e:
            raise ValueError(f"Erro ao verificar carteira do cliente: {str(e)}")

        # Verificar se o cliente tem saldo suficiente para o escrow
        try:
            if not WalletService.has_sufficient_balance(client_id, value):
                current_balance = WalletService.get_wallet_balance(client_id)
                raise ValueError(f"Saldo insuficiente para criar a ordem. Saldo atual: R$ {current_balance:.2f}, valor necessário: R$ {value:.2f}")
        except Exception as e:
            raise ValueError(f"Erro ao verificar saldo: {str(e)}")

        try:
            # Criar ordem com status inicial 'disponivel'
            order = Order(
                client_id=client_id,
                title=title,
                description=description,
                value=value,
                status='disponivel',
                created_at=datetime.utcnow()
            )
            db.session.add(order)
            db.session.flush()  # Para obter o ID da ordem antes do commit

            # Transferir valor para escrow (saldo→escrow)
            # Tokens não saem do sistema, apenas mudam de estado
            escrow_result = WalletService.transfer_to_escrow(client_id, value, order.id)
            
            db.session.commit()

            return {
                'order': order,
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

        if order.status != 'disponivel':
            raise ValueError(f"Ordem não está disponível. Status atual: {order.status}")

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
            # Atualizar ordem com prestador e novo status
            order.provider_id = provider_id
            order.status = 'aceita'
            order.accepted_at = datetime.utcnow()
            
            db.session.commit()
            
            # TODO: Implementar notificação para o cliente sobre aceitação
            # NotificationService.notify_client_order_accepted(order.client_id, order_id, provider_id)
            
            return {
                'success': True,
                'order_id': order.id,
                'new_status': order.status,
                'accepted_at': order.accepted_at,
                'provider_id': provider_id
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao aceitar ordem: {str(e)}")

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

        if order.status not in ['aceita', 'em_andamento', 'aguardando_confirmacao']:
            raise ValueError(f"Ordem não pode ser concluída neste estado: {order.status}")

        try:
            # Se o prestador marca como concluída, aguarda confirmação do cliente
            if user_id == order.provider_id:
                if order.status in ['aceita', 'em_andamento']:
                    order.status = 'aguardando_confirmacao'
                    db.session.commit()
                    
                    # TODO: Implementar notificação para o cliente
                    # NotificationService.notify_client_completion_request(order.client_id, order_id)
                    
                    return {
                        'success': True,
                        'status': 'aguardando_confirmacao',
                        'message': 'Ordem marcada como concluída. Aguardando confirmação do cliente.',
                        'requires_client_confirmation': True
                    }
                else:
                    raise ValueError("Ordem já foi marcada como concluída pelo prestador")

            # Se o cliente confirma, a ordem é concluída e o pagamento liberado
            if user_id == order.client_id:
                if order.status != 'aguardando_confirmacao':
                    raise ValueError("Ordem não está aguardando confirmação do cliente")
                
                # Marcar ordem como concluída
                order.status = 'concluida'
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
                    'completed_at': order.completed_at
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

        # Verificar se ordem pode ser cancelada
        cancellable_statuses = ['disponivel', 'aceita', 'em_andamento']
        if order.status not in cancellable_statuses:
            raise ValueError(f"Ordem não pode ser cancelada neste estado: {order.status}")

        # Verificar prazos para cancelamento (implementação básica)
        from datetime import datetime, timedelta
        
        # Se ordem foi aceita há mais de 24h, só prestador pode cancelar
        if order.status in ['aceita', 'em_andamento'] and order.accepted_at:
            hours_since_accepted = (datetime.utcnow() - order.accepted_at).total_seconds() / 3600
            if hours_since_accepted > 24 and user_id == order.client_id:
                raise ValueError("Cliente não pode cancelar ordem aceita há mais de 24 horas. Entre em contato com o suporte.")

        try:
            # Marcar ordem como cancelada
            old_status = order.status
            order.status = 'cancelada'
            
            # Registrar motivo do cancelamento
            if reason:
                # TODO: Implementar modelo CancellationReason quando necessário
                pass
            
            db.session.commit()

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
                'reason': reason
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

        # Verificar se ordem pode ter disputa aberta
        disputable_statuses = ['aceita', 'em_andamento', 'aguardando_confirmacao']
        if order.status not in disputable_statuses:
            raise ValueError(f"Não é possível abrir disputa para ordem com status: {order.status}")

        if not reason or len(reason.strip()) < 10:
            raise ValueError("Motivo da disputa deve ter pelo menos 10 caracteres")

        try:
            # Marcar ordem como disputada
            old_status = order.status
            order.status = 'disputada'
            
            db.session.commit()

            # TODO: Implementar modelo Dispute para registrar detalhes
            # dispute = Dispute(
            #     order_id=order_id,
            #     opened_by=user_id,
            #     reason=reason,
            #     status='pendente',
            #     created_at=datetime.utcnow()
            # )
            # db.session.add(dispute)
            
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
                'message': 'Disputa aberta com sucesso. Aguarde análise administrativa.'
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

        if order.status != 'disputada':
            raise ValueError(f"Ordem não está em disputa. Status atual: {order.status}")

        # Verificar se usuário é admin
        from models import AdminUser
        admin = AdminUser.query.get(admin_id)
        if not admin:
            raise ValueError("Apenas administradores podem resolver disputas")

        valid_decisions = ['favor_cliente', 'favor_prestador', 'dividir_50_50']
        if decision not in valid_decisions:
            raise ValueError(f"Decisão inválida. Opções: {', '.join(valid_decisions)}")

        try:
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

            # Marcar ordem como resolvida
            order.status = 'resolvida'
            db.session.commit()

            # TODO: Implementar atualização do registro de disputa
            # dispute = Dispute.query.filter_by(order_id=order_id).first()
            # dispute.status = 'resolvida'
            # dispute.decision = decision
            # dispute.admin_notes = admin_notes
            # dispute.resolved_at = datetime.utcnow()
            # dispute.resolved_by = admin_id

            # TODO: Implementar notificações
            # NotificationService.notify_dispute_resolved(order.client_id, order.provider_id, order_id, decision)

            return {
                'success': True,
                'order_id': order.id,
                'decision': decision,
                'result_details': result_details,
                'admin_notes': admin_notes,
                'message': f'Disputa resolvida: {decision.replace("_", " ").title()}'
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
