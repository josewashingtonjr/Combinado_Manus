#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Gestão de Ordens de Serviço
Gerencia todo o ciclo de vida das ordens: execução, cancelamento e contestação
"""

from models import db, Order, User, Transaction, Invite
from services.wallet_service import WalletService
from services.config_service import ConfigService
from services.audit_service import AuditService
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Logger específico para operações de ordem
order_operations_logger = logging.getLogger('sistema_combinado.order_operations')
order_operations_logger.setLevel(logging.INFO)


class OrderManagementService:
    """Serviço para gerenciar ordens de serviço"""
    
    # Configurações padrão (podem ser sobrescritas por configurações do admin)
    PLATFORM_FEE_PERCENTAGE = Decimal('5.0')  # 5% de taxa da plataforma
    CONTESTATION_FEE = Decimal('10.00')  # R$ 10,00 taxa de contestação
    CANCELLATION_FEE_PERCENTAGE = Decimal('10.0')  # 10% multa de cancelamento
    CONFIRMATION_DEADLINE_HOURS = 36  # 36 horas para confirmar/contestar
    
    @staticmethod
    def create_order_from_invite(invite_id: int, provider_id: int) -> dict:
        """
        Cria uma ordem a partir de um convite aceito
        
        Args:
            invite_id: ID do convite
            provider_id: ID do prestador que aceitou
            
        Returns:
            dict: Resultado da operação com ordem criada e detalhes
            
        Process:
            1. Validar convite (existe, não expirado, não convertido)
            2. Obter taxas atuais do ConfigService
            3. Calcular valores (serviço, taxas, bloqueios)
            4. Bloquear valores nas carteiras (cliente e prestador)
            5. Criar ordem com status aguardando_execucao
            6. Atualizar convite (status=convertido, order_id)
            7. Enviar notificações
            8. Commit transação atômica
        """
        try:
            # 1. Validar convite
            invite = Invite.query.get(invite_id)
            if not invite:
                raise ValueError("Convite não encontrado")
            
            if invite.status == 'convertido':
                raise ValueError("Convite já foi convertido em ordem")
            
            if invite.status != 'aceito':
                raise ValueError(f"Convite não está aceito. Status atual: {invite.status}")
            
            if invite.is_expired:
                raise ValueError("Convite expirado")
            
            # 2. Obter taxas atuais do ConfigService
            platform_fee_percentage = ConfigService.get_platform_fee_percentage()
            contestation_fee = ConfigService.get_contestation_fee()
            cancellation_fee_percentage = ConfigService.get_cancellation_fee_percentage()
            
            # 3. Calcular valores
            # Usar o valor efetivo do convite (pode ter sido alterado por proposta)
            service_value = Decimal(str(invite.current_value))
            
            # Valores a bloquear:
            # Cliente: valor do serviço + taxa de contestação
            client_escrow_amount = service_value + contestation_fee
            
            # Prestador: taxa de contestação (garantia)
            provider_escrow_amount = contestation_fee
            
            # 4. Bloquear valores nas carteiras usando WalletService
            # Verificar saldos antes de bloquear
            if not WalletService.has_sufficient_balance(invite.client_id, client_escrow_amount):
                raise ValueError(
                    f"Cliente não possui saldo suficiente. "
                    f"Necessário: R$ {client_escrow_amount:.2f} "
                    f"(Serviço: R$ {service_value:.2f} + Taxa de contestação: R$ {contestation_fee:.2f})"
                )
            
            if not WalletService.has_sufficient_balance(provider_id, provider_escrow_amount):
                raise ValueError(
                    f"Prestador não possui saldo suficiente. "
                    f"Necessário: R$ {provider_escrow_amount:.2f} "
                    f"(Taxa de contestação)"
                )
            
            # Criar ordem temporária para usar o ID nas transações de escrow
            order = Order(
                client_id=invite.client_id,
                provider_id=provider_id,
                title=invite.service_title,
                description=invite.service_description,
                value=service_value,
                status='aguardando_execucao',
                service_deadline=invite.delivery_date,
                invite_id=invite_id,
                accepted_at=datetime.utcnow(),
                # Armazenar taxas vigentes no momento da criação
                platform_fee_percentage_at_creation=platform_fee_percentage,
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=cancellation_fee_percentage,
                created_at=datetime.utcnow()
            )
            
            db.session.add(order)
            db.session.flush()  # Obter o ID da ordem sem fazer commit
            
            # Bloquear valores do cliente
            client_escrow_result = WalletService.transfer_to_escrow(
                user_id=invite.client_id,
                amount=client_escrow_amount,
                order_id=order.id
            )
            
            # Bloquear taxa de contestação do prestador
            provider_escrow_result = WalletService.transfer_to_escrow(
                user_id=provider_id,
                amount=provider_escrow_amount,
                order_id=order.id
            )
            
            # 5. Atualizar convite
            invite.status = 'convertido'
            invite.order_id = order.id
            invite.responded_at = datetime.utcnow()
            
            # 6. Commit da transação atômica
            db.session.commit()
            
            # Registrar auditoria da criação da ordem
            audit_id = AuditService.log_order_created(
                order_id=order.id,
                client_id=invite.client_id,
                provider_id=provider_id,
                value=service_value,
                invite_id=invite_id,
                escrow_details={
                    'client_escrow_amount': client_escrow_amount,
                    'provider_escrow_amount': provider_escrow_amount,
                    'platform_fee_percentage': platform_fee_percentage,
                    'contestation_fee': contestation_fee,
                    'cancellation_fee_percentage': cancellation_fee_percentage
                }
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Ordem {order.id} criada com sucesso a partir do convite {invite_id}. "
                f"Cliente: {invite.client_id}, Prestador: {provider_id}, "
                f"Valor: R$ {service_value:.2f}, "
                f"Bloqueado cliente: R$ {client_escrow_amount:.2f}, "
                f"Bloqueado prestador: R$ {provider_escrow_amount:.2f}"
            )
            
            order_operations_logger.info(
                f"ORDEM_CRIADA | ID: {order.id} | Cliente: {invite.client_id} | "
                f"Prestador: {provider_id} | Valor: {service_value} | Audit: {audit_id}"
            )
            
            # Enviar notificações
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_order_created(order)
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação de ordem criada: {e}")
            
            mensagem = (
                f"Ordem criada com sucesso! "
                f"Valor do serviço: R$ {service_value:.2f}. "
                f"Valores bloqueados em garantia até a conclusão."
            )
            
            return {
                'success': True,
                'order': order,
                'order_id': order.id,
                'effective_value': float(service_value),
                'original_value': float(invite.original_value),
                'client_escrow_amount': float(client_escrow_amount),
                'provider_escrow_amount': float(provider_escrow_amount),
                'platform_fee_percentage': float(platform_fee_percentage),
                'contestation_fee': float(contestation_fee),
                'cancellation_fee_percentage': float(cancellation_fee_percentage),
                'escrow_details': {
                    'client_transaction_id': client_escrow_result['transaction_id'],
                    'provider_transaction_id': provider_escrow_result['transaction_id'],
                    'client_new_balance': float(client_escrow_result['new_balance']),
                    'client_new_escrow_balance': float(client_escrow_result['new_escrow_balance']),
                    'provider_new_balance': float(provider_escrow_result['new_balance']),
                    'provider_new_escrow_balance': float(provider_escrow_result['new_escrow_balance'])
                },
                'message': mensagem
            }
            
        except ValueError as e:
            db.session.rollback()
            logger.error(f"Erro de validação ao criar ordem do convite {invite_id}: {e}")
            AuditService.log_error(
                operation='CREATE_ORDER',
                entity_type='Order',
                entity_id=None,
                user_id=None,
                error_message=str(e),
                error_details={'invite_id': invite_id}
            )
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco de dados ao criar ordem do convite {invite_id}: {e}")
            AuditService.log_error(
                operation='CREATE_ORDER',
                entity_type='Order',
                entity_id=None,
                user_id=None,
                error_message=f"Erro de banco de dados: {str(e)}",
                error_details={'invite_id': invite_id}
            )
            raise ValueError(f"Erro ao criar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao criar ordem do convite {invite_id}: {e}")
            AuditService.log_error(
                operation='CREATE_ORDER',
                entity_type='Order',
                entity_id=None,
                user_id=None,
                error_message=f"Erro inesperado: {str(e)}",
                error_details={'invite_id': invite_id}
            )
            raise ValueError(f"Erro inesperado ao criar ordem: {str(e)}")
    
    @staticmethod
    def mark_service_completed(order_id: int, provider_id: int) -> dict:
        """
        Prestador marca o serviço como concluído
        
        Args:
            order_id: ID da ordem
            provider_id: ID do prestador
            
        Returns:
            dict com resultado da operação
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        # Verificar se é o prestador correto
        if order.provider_id != provider_id:
            raise ValueError("Você não é o prestador desta ordem")
        
        # Verificar se pode marcar como concluído
        if not order.can_be_marked_completed:
            raise ValueError(f"Ordem não pode ser marcada como concluída. Status atual: {order.status}")
        
        try:
            old_status = order.status
            
            # Atualizar status e datas
            order.status = 'servico_executado'
            order.completed_at = datetime.utcnow()
            
            # Definir prazo de 36 horas para confirmação/contestação
            order.confirmation_deadline = order.completed_at + timedelta(
                hours=OrderManagementService.CONFIRMATION_DEADLINE_HOURS
            )
            order.dispute_deadline = order.confirmation_deadline
            
            db.session.commit()
            
            # Registrar auditoria da mudança de status
            audit_id = AuditService.log_status_change(
                order_id=order_id,
                user_id=provider_id,
                old_status=old_status,
                new_status='servico_executado'
            )
            
            # Registrar auditoria específica de conclusão de serviço
            AuditService.log_service_completed(
                order_id=order_id,
                provider_id=provider_id,
                completed_at=order.completed_at,
                confirmation_deadline=order.confirmation_deadline
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Ordem {order_id} marcada como concluída pelo prestador {provider_id}. "
                f"Prazo para confirmação: {order.confirmation_deadline}"
            )
            
            order_operations_logger.info(
                f"SERVICO_CONCLUIDO | ID: {order_id} | Prestador: {provider_id} | "
                f"Prazo: {order.confirmation_deadline} | Audit: {audit_id}"
            )
            
            # Enviar notificação para o cliente
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_service_completed(order)
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação de serviço concluído: {e}")
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'confirmation_deadline': order.confirmation_deadline,
                'hours_to_confirm': OrderManagementService.CONFIRMATION_DEADLINE_HOURS,
                'message': f'Serviço marcado como concluído! O cliente tem {OrderManagementService.CONFIRMATION_DEADLINE_HOURS}h para confirmar ou contestar.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao marcar ordem {order_id} como concluída: {e}")
            AuditService.log_error(
                operation='MARK_SERVICE_COMPLETED',
                entity_type='Order',
                entity_id=order_id,
                user_id=provider_id,
                error_message=str(e)
            )
            raise
    
    @staticmethod
    def confirm_service(order_id: int, client_id: int) -> dict:
        """
        Cliente confirma que o serviço foi bem executado (Confirmação Manual)
        
        Args:
            order_id: ID da ordem
            client_id: ID do cliente
            
        Returns:
            dict com resultado da operação e detalhes dos pagamentos
            
        Process:
            1. Validar ordem (existe, pertence ao cliente, status=servico_executado)
            2. Validar prazo (confirmation_deadline não expirado)
            3. Processar pagamentos via _process_order_payments()
            4. Atualizar status para concluida
            5. Registrar confirmed_at
            6. Usar transação atômica
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        # Verificar se é o cliente correto
        if order.client_id != client_id:
            raise ValueError("Você não é o cliente desta ordem")
        
        # Verificar status
        if order.status != 'servico_executado':
            raise ValueError(f"Ordem não pode ser confirmada. Status atual: {order.status}")
        
        # Verificar prazo de confirmação
        if order.confirmation_deadline and datetime.utcnow() > order.confirmation_deadline:
            raise ValueError("Prazo para confirmação expirado (36 horas)")
        
        try:
            # Obter taxas vigentes no momento da criação da ordem
            platform_fee_percentage = order.platform_fee_percentage_at_creation or OrderManagementService.PLATFORM_FEE_PERCENTAGE
            contestation_fee = order.contestation_fee_at_creation or OrderManagementService.CONTESTATION_FEE
            
            # Processar pagamentos
            payment_result = OrderManagementService._process_order_payments(
                order=order,
                platform_fee_percentage=platform_fee_percentage,
                contestation_fee=contestation_fee
            )
            
            old_status = order.status
            
            # Atualizar status da ordem
            order.status = 'concluida'
            order.confirmed_at = datetime.utcnow()
            order.platform_fee = payment_result['platform_fee']
            order.platform_fee_percentage = platform_fee_percentage
            
            db.session.commit()
            
            # Registrar auditoria da confirmação
            audit_id = AuditService.log_status_change(
                order_id=order_id,
                user_id=client_id,
                old_status=old_status,
                new_status='concluida',
                reason='Confirmação manual pelo cliente'
            )
            
            AuditService.log_order_confirmed(
                order_id=order_id,
                client_id=client_id,
                is_auto_confirmed=False,
                payment_details=payment_result
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Ordem {order_id} confirmada manualmente pelo cliente {client_id}. "
                f"Prestador recebeu: R$ {payment_result['provider_net_amount']:.2f}, "
                f"Taxa plataforma: R$ {payment_result['platform_fee']:.2f}"
            )
            
            order_operations_logger.info(
                f"ORDEM_CONFIRMADA_MANUAL | ID: {order_id} | Cliente: {client_id} | "
                f"Valor Prestador: {payment_result['provider_net_amount']} | "
                f"Taxa: {payment_result['platform_fee']} | Audit: {audit_id}"
            )
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'confirmation_type': 'manual',
                'confirmed_at': order.confirmed_at,
                'payments': payment_result,
                'message': 'Serviço confirmado com sucesso! Pagamentos processados.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao confirmar ordem {order_id}: {e}")
            AuditService.log_error(
                operation='CONFIRM_SERVICE',
                entity_type='Order',
                entity_id=order_id,
                user_id=client_id,
                error_message=str(e)
            )
            raise ValueError(f"Erro ao confirmar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao confirmar ordem {order_id}: {e}")
            AuditService.log_error(
                operation='CONFIRM_SERVICE',
                entity_type='Order',
                entity_id=order_id,
                user_id=client_id,
                error_message=str(e)
            )
            raise
    
    @staticmethod
    def _process_order_payments(order: Order, platform_fee_percentage: Decimal, contestation_fee: Decimal) -> dict:
        """
        Processa os pagamentos da ordem após confirmação
        
        Args:
            order: Objeto Order
            platform_fee_percentage: Percentual da taxa da plataforma
            contestation_fee: Valor da taxa de contestação
            
        Returns:
            dict com detalhes dos pagamentos processados
            
        Process:
            1. Calcular valor líquido prestador (valor - taxa_plataforma)
            2. Transferir valor líquido para prestador (do escrow do cliente)
            3. Transferir taxa_plataforma para admin (do escrow do cliente)
            4. Devolver taxa_contestação para cliente (do escrow do cliente)
            5. Devolver taxa_contestação para prestador (do escrow do prestador)
        """
        # Converter valores para Decimal
        service_value = Decimal(str(order.value))
        platform_fee_percentage = Decimal(str(platform_fee_percentage))
        contestation_fee = Decimal(str(contestation_fee))
        
        # Calcular valores
        platform_fee = service_value * (platform_fee_percentage / Decimal('100'))
        provider_net_amount = service_value - platform_fee
        
        # 1. Transferir valor líquido do escrow do cliente para o prestador
        WalletService.transfer_from_escrow_to_user(
            from_user_id=order.client_id,
            to_user_id=order.provider_id,
            amount=provider_net_amount,
            order_id=order.id,
            description=f"Pagamento pelo serviço da ordem #{order.id}"
        )
        
        # 2. Transferir taxa da plataforma do escrow do cliente para o admin
        WalletService.transfer_from_escrow_to_user(
            from_user_id=order.client_id,
            to_user_id=WalletService.ADMIN_USER_ID,
            amount=platform_fee,
            order_id=order.id,
            description=f"Taxa da plataforma ({platform_fee_percentage}%) da ordem #{order.id}"
        )
        
        # 3. Devolver taxa de contestação para o cliente (do escrow do cliente)
        WalletService.release_escrow_to_balance(
            user_id=order.client_id,
            amount=contestation_fee,
            order_id=order.id,
            description=f"Devolução da taxa de contestação da ordem #{order.id}"
        )
        
        # 4. Devolver taxa de contestação para o prestador (do escrow do prestador)
        WalletService.release_escrow_to_balance(
            user_id=order.provider_id,
            amount=contestation_fee,
            order_id=order.id,
            description=f"Devolução da taxa de contestação da ordem #{order.id}"
        )
        
        logger.info(
            f"Pagamentos processados para ordem {order.id}: "
            f"Prestador: R$ {provider_net_amount:.2f}, "
            f"Plataforma: R$ {platform_fee:.2f}, "
            f"Devoluções: R$ {contestation_fee:.2f} (cliente) + R$ {contestation_fee:.2f} (prestador)"
        )
        
        return {
            'service_value': float(service_value),
            'platform_fee': float(platform_fee),
            'platform_fee_percentage': float(platform_fee_percentage),
            'provider_net_amount': float(provider_net_amount),
            'contestation_fee_returned_client': float(contestation_fee),
            'contestation_fee_returned_provider': float(contestation_fee),
            'total_processed': float(service_value + contestation_fee + contestation_fee)
        }
    
    @staticmethod
    def _process_cancellation_payments(order: Order, cancelled_by_user_id: int, 
                                      cancellation_fee: Decimal, contestation_fee: Decimal) -> dict:
        """
        Processa os pagamentos de cancelamento de uma ordem
        
        Args:
            order: Objeto Order
            cancelled_by_user_id: ID do usuário que cancelou
            cancellation_fee: Valor da multa de cancelamento
            contestation_fee: Valor da taxa de contestação
            
        Returns:
            dict com detalhes dos pagamentos processados
            
        Process:
            1. Identificar parte prejudicada (se cliente cancelou, prestador é prejudicado e vice-versa)
            2. Calcular distribuição da multa (50% plataforma, 50% parte prejudicada)
            3. Transferir 50% da multa para plataforma
            4. Transferir 50% da multa para parte prejudicada
            5. Devolver valor do serviço menos multa para quem cancelou
            6. Devolver taxas de contestação para ambos
            7. Registrar todas as transações
        """
        # Converter valores para Decimal
        service_value = Decimal(str(order.value))
        cancellation_fee = Decimal(str(cancellation_fee))
        contestation_fee = Decimal(str(contestation_fee))
        
        # 1. Identificar parte prejudicada
        is_client_cancelling = (cancelled_by_user_id == order.client_id)
        
        if is_client_cancelling:
            cancelling_user_id = order.client_id
            injured_party_id = order.provider_id
            cancelling_party_name = "cliente"
            injured_party_name = "prestador"
        else:
            cancelling_user_id = order.provider_id
            injured_party_id = order.client_id
            cancelling_party_name = "prestador"
            injured_party_name = "cliente"
        
        # 2. Calcular distribuição da multa
        platform_share = cancellation_fee / Decimal('2')
        injured_party_share = cancellation_fee / Decimal('2')
        
        # 3-5. Processar pagamentos de acordo com quem cancelou
        if is_client_cancelling:
            # Cliente cancelou: multa deduzida do escrow do cliente
            # 3. Transferir 50% da multa para plataforma (do escrow do cliente)
            WalletService.transfer_from_escrow_to_user(
                from_user_id=cancelling_user_id,
                to_user_id=WalletService.ADMIN_USER_ID,
                amount=platform_share,
                order_id=order.id,
                description=f"Taxa de cancelamento (50%) da ordem #{order.id} - cancelada por {cancelling_party_name}"
            )
            
            # 4. Transferir 50% da multa para parte prejudicada (do escrow do cliente)
            WalletService.transfer_from_escrow_to_user(
                from_user_id=cancelling_user_id,
                to_user_id=injured_party_id,
                amount=injured_party_share,
                order_id=order.id,
                description=f"Compensação por cancelamento da ordem #{order.id}"
            )
            
            # 5. Devolver valor do serviço menos multa para o cliente
            amount_to_return = service_value - cancellation_fee
            if amount_to_return > 0:
                WalletService.release_escrow_to_balance(
                    user_id=cancelling_user_id,
                    amount=amount_to_return,
                    order_id=order.id,
                    description=f"Devolução do valor da ordem #{order.id} (menos multa de cancelamento)"
                )
        else:
            # Prestador cancelou: devolver valor completo para cliente, multa deduzida do saldo do prestador
            # 5. Devolver valor completo do serviço para o cliente
            WalletService.release_escrow_to_balance(
                user_id=order.client_id,
                amount=service_value,
                order_id=order.id,
                description=f"Devolução do valor da ordem #{order.id} (cancelada pelo prestador)"
            )
            
            # 3. Transferir 50% da multa para plataforma (do saldo disponível do prestador)
            WalletService.transfer_tokens_between_users(
                from_user_id=cancelling_user_id,
                to_user_id=WalletService.ADMIN_USER_ID,
                amount=platform_share,
                description=f"Taxa de cancelamento (50%) da ordem #{order.id} - cancelada por {cancelling_party_name}"
            )
            
            # 4. Transferir 50% da multa para parte prejudicada (do saldo disponível do prestador)
            WalletService.transfer_tokens_between_users(
                from_user_id=cancelling_user_id,
                to_user_id=injured_party_id,
                amount=injured_party_share,
                description=f"Compensação por cancelamento da ordem #{order.id}"
            )
            
            amount_to_return = Decimal('0')  # Prestador não recebe devolução, pagou a multa
        
        # 6. Devolver taxas de contestação para ambos
        # Devolver taxa de contestação do cliente
        WalletService.release_escrow_to_balance(
            user_id=order.client_id,
            amount=contestation_fee,
            order_id=order.id,
            description=f"Devolução da taxa de contestação da ordem #{order.id} (cancelada)"
        )
        
        # Devolver taxa de contestação do prestador
        WalletService.release_escrow_to_balance(
            user_id=order.provider_id,
            amount=contestation_fee,
            order_id=order.id,
            description=f"Devolução da taxa de contestação da ordem #{order.id} (cancelada)"
        )
        
        logger.info(
            f"Pagamentos de cancelamento processados para ordem {order.id}: "
            f"Multa total: R$ {cancellation_fee:.2f}, "
            f"Plataforma: R$ {platform_share:.2f}, "
            f"Parte prejudicada ({injured_party_name}): R$ {injured_party_share:.2f}, "
            f"Devolvido para {cancelling_party_name}: R$ {amount_to_return:.2f}, "
            f"Taxas de contestação devolvidas: R$ {contestation_fee:.2f} (cada)"
        )
        
        return {
            'service_value': float(service_value),
            'cancellation_fee': float(cancellation_fee),
            'platform_share': float(platform_share),
            'injured_party_share': float(injured_party_share),
            'amount_returned_to_cancelling_party': float(amount_to_return),
            'contestation_fee_returned_client': float(contestation_fee),
            'contestation_fee_returned_provider': float(contestation_fee),
            'cancelling_party': cancelling_party_name,
            'injured_party': injured_party_name,
            'total_processed': float(service_value + contestation_fee + contestation_fee)
        }
    
    @staticmethod
    def auto_confirm_expired_orders() -> dict:
        """
        Job automático: Confirma ordens que ultrapassaram o prazo de 36h
        Deve ser executado periodicamente (ex: a cada hora)
        
        Returns:
            dict com estatísticas da execução: {
                'processed': int,  # Total de ordens processadas
                'confirmed': int,  # Ordens confirmadas com sucesso
                'errors': List[str]  # Lista de erros encontrados
            }
            
        Process:
            1. Buscar ordens com status=servico_executado
            2. Filtrar onde confirmation_deadline <= datetime.utcnow()
            3. Para cada ordem expirada, processar pagamentos usando _process_order_payments()
            4. Atualizar status para concluida
            5. Registrar confirmed_at e auto_confirmed=True
            6. Retornar estatísticas (processed, confirmed, errors)
            7. Registrar logs detalhados de cada operação
            8. Tratar erros individualmente sem interromper o processamento de outras ordens
        """
        now = datetime.utcnow()
        
        logger.info(f"Iniciando job de confirmação automática às {now.isoformat()}")
        
        # 1 e 2. Buscar ordens com serviço executado e prazo expirado
        expired_orders = Order.query.filter(
            Order.status == 'servico_executado',
            Order.confirmation_deadline <= now
        ).all()
        
        processed_count = 0
        confirmed_count = 0
        errors = []
        
        logger.info(f"Encontradas {len(expired_orders)} ordens expiradas para processar")
        
        # 3-8. Processar cada ordem individualmente
        for order in expired_orders:
            processed_count += 1
            
            try:
                logger.info(
                    f"Processando ordem {order.id}: "
                    f"Cliente: {order.client_id}, Prestador: {order.provider_id}, "
                    f"Valor: R$ {order.value:.2f}, "
                    f"Prazo expirado em: {order.confirmation_deadline.isoformat()}"
                )
                
                # Obter taxas vigentes no momento da criação da ordem
                platform_fee_percentage = order.platform_fee_percentage_at_creation or OrderManagementService.PLATFORM_FEE_PERCENTAGE
                contestation_fee = order.contestation_fee_at_creation or OrderManagementService.CONTESTATION_FEE
                
                # 3. Processar pagamentos usando _process_order_payments()
                payment_result = OrderManagementService._process_order_payments(
                    order=order,
                    platform_fee_percentage=platform_fee_percentage,
                    contestation_fee=contestation_fee
                )
                
                old_status = order.status
                
                # 4. Atualizar status para concluida
                order.status = 'concluida'
                
                # 5. Registrar confirmed_at e auto_confirmed=True
                order.confirmed_at = now
                order.auto_confirmed = True
                order.platform_fee = payment_result['platform_fee']
                order.platform_fee_percentage = platform_fee_percentage
                
                # Commit da transação para esta ordem
                db.session.commit()
                
                confirmed_count += 1
                
                # Registrar auditoria da confirmação automática
                audit_id = AuditService.log_status_change(
                    order_id=order.id,
                    user_id=order.client_id,
                    old_status=old_status,
                    new_status='concluida',
                    reason='Confirmação automática após 36 horas'
                )
                
                AuditService.log_order_confirmed(
                    order_id=order.id,
                    client_id=order.client_id,
                    is_auto_confirmed=True,
                    payment_details=payment_result
                )
                
                logger.info(
                    f"[AUDIT_ID: {audit_id}] Ordem {order.id} confirmada automaticamente com sucesso. "
                    f"Prestador recebeu: R$ {payment_result['provider_net_amount']:.2f}, "
                    f"Taxa plataforma: R$ {payment_result['platform_fee']:.2f}, "
                    f"Devoluções: R$ {payment_result['contestation_fee_returned_client']:.2f} (cliente) + "
                    f"R$ {payment_result['contestation_fee_returned_provider']:.2f} (prestador)"
                )
                
                order_operations_logger.info(
                    f"ORDEM_CONFIRMADA_AUTO | ID: {order.id} | Cliente: {order.client_id} | "
                    f"Valor Prestador: {payment_result['provider_net_amount']} | "
                    f"Taxa: {payment_result['platform_fee']} | Audit: {audit_id}"
                )
                
                # Enviar notificação para ambas as partes
                from services.notification_service import NotificationService
                try:
                    NotificationService.notify_auto_confirmed(order)
                except Exception as e:
                    logger.warning(f"Erro ao enviar notificação de confirmação automática: {e}")
                
            except Exception as e:
                # 8. Tratar erros individualmente sem interromper o processamento
                error_msg = f"Ordem {order.id}: {str(e)}"
                logger.error(f"Erro ao confirmar automaticamente ordem {order.id}: {e}", exc_info=True)
                errors.append(error_msg)
                
                # Registrar erro na auditoria
                AuditService.log_error(
                    operation='AUTO_CONFIRM_ORDER',
                    entity_type='Order',
                    entity_id=order.id,
                    user_id=order.client_id,
                    error_message=str(e),
                    error_details={
                        'confirmation_deadline': order.confirmation_deadline.isoformat() if order.confirmation_deadline else None
                    }
                )
                
                # Rollback apenas desta transação
                db.session.rollback()
                
                # Continuar processando as próximas ordens
                continue
        
        # 6 e 7. Retornar estatísticas e registrar logs finais
        result = {
            'processed': processed_count,
            'confirmed': confirmed_count,
            'errors': errors,
            'timestamp': now.isoformat()
        }
        
        logger.info(
            f"Job de confirmação automática concluído: "
            f"{confirmed_count}/{processed_count} ordens confirmadas, "
            f"{len(errors)} erros"
        )
        
        if errors:
            logger.warning(f"Erros encontrados durante confirmação automática: {errors}")
        
        return result
    
    @staticmethod
    def cancel_order(order_id: int, user_id: int, reason: str) -> dict:
        """
        Cancela uma ordem com aplicação de multa
        
        Args:
            order_id: ID da ordem
            user_id: ID do usuário que está cancelando
            reason: Motivo do cancelamento (obrigatório)
            
        Returns:
            dict com resultado da operação
            
        Process:
            1. Validar ordem (existe, status=aguardando_execucao)
            2. Validar usuário (é cliente ou prestador da ordem)
            3. Validar motivo (obrigatório)
            4. Obter taxa de cancelamento do ConfigService
            5. Calcular multa (valor * cancellation_fee_percentage / 100)
            6. Processar pagamentos de cancelamento via _process_cancellation_payments()
            7. Atualizar ordem (status, cancelled_by, cancelled_at, cancellation_reason, cancellation_fee)
            8. Usar transação atômica
        """
        # 1. Validar ordem
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if not order.can_be_cancelled:
            raise ValueError(f"Ordem não pode ser cancelada. Status atual: {order.status}")
        
        # 2. Validar usuário (é cliente ou prestador da ordem)
        is_client = (order.client_id == user_id)
        is_provider = (order.provider_id == user_id)
        
        if not (is_client or is_provider):
            raise ValueError("Você não tem permissão para cancelar esta ordem")
        
        # 3. Validar motivo (obrigatório)
        if not reason or not reason.strip():
            raise ValueError("Motivo do cancelamento é obrigatório")
        
        try:
            # 4. Obter taxa de cancelamento do ConfigService
            cancellation_fee_percentage = order.cancellation_fee_percentage_at_creation or ConfigService.get_cancellation_fee_percentage()
            contestation_fee = order.contestation_fee_at_creation or ConfigService.get_contestation_fee()
            
            # 5. Calcular multa
            service_value = Decimal(str(order.value))
            cancellation_fee = service_value * (cancellation_fee_percentage / Decimal('100'))
            
            # 6. Processar pagamentos de cancelamento
            payment_result = OrderManagementService._process_cancellation_payments(
                order=order,
                cancelled_by_user_id=user_id,
                cancellation_fee=cancellation_fee,
                contestation_fee=contestation_fee
            )
            
            old_status = order.status
            
            # 7. Atualizar ordem
            order.status = 'cancelada'
            order.cancelled_by = user_id
            order.cancelled_at = datetime.utcnow()
            order.cancellation_reason = reason
            order.cancellation_fee = cancellation_fee
            order.cancellation_fee_percentage = cancellation_fee_percentage
            
            # 8. Commit da transação atômica
            db.session.commit()
            
            cancelled_by_name = "cliente" if is_client else "prestador"
            injured_party_name = "prestador" if is_client else "cliente"
            
            # Registrar auditoria do cancelamento
            audit_id = AuditService.log_status_change(
                order_id=order_id,
                user_id=user_id,
                old_status=old_status,
                new_status='cancelada',
                reason=reason
            )
            
            AuditService.log_order_cancelled(
                order_id=order_id,
                cancelled_by_id=user_id,
                cancelled_by_role=cancelled_by_name,
                reason=reason,
                payment_details=payment_result
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Ordem {order_id} cancelada por {cancelled_by_name} (user {user_id}). "
                f"Multa: R$ {cancellation_fee:.2f}, "
                f"Motivo: {reason[:100]}"
            )
            
            order_operations_logger.info(
                f"ORDEM_CANCELADA | ID: {order_id} | Cancelado por: {cancelled_by_name} ({user_id}) | "
                f"Multa: {cancellation_fee} | Parte prejudicada: {injured_party_name} | Audit: {audit_id}"
            )
            
            # Enviar notificação para a parte prejudicada
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_order_cancelled(
                    order=order,
                    cancellation_fee=cancellation_fee
                )
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação de cancelamento: {e}")
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'cancelled_by': cancelled_by_name,
                'cancellation_fee': float(cancellation_fee),
                'cancellation_fee_percentage': float(cancellation_fee_percentage),
                'platform_share': float(payment_result['platform_share']),
                'injured_party_share': float(payment_result['injured_party_share']),
                'injured_party': injured_party_name,
                'payments': payment_result,
                'message': f'Ordem cancelada com sucesso. Multa de R$ {cancellation_fee:.2f} aplicada.'
            }
            
        except ValueError as e:
            db.session.rollback()
            logger.error(f"Erro de validação ao cancelar ordem {order_id}: {e}")
            AuditService.log_error(
                operation='CANCEL_ORDER',
                entity_type='Order',
                entity_id=order_id,
                user_id=user_id,
                error_message=str(e),
                error_details={'reason': reason}
            )
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco de dados ao cancelar ordem {order_id}: {e}")
            AuditService.log_error(
                operation='CANCEL_ORDER',
                entity_type='Order',
                entity_id=order_id,
                user_id=user_id,
                error_message=f"Erro de banco de dados: {str(e)}",
                error_details={'reason': reason}
            )
            raise ValueError(f"Erro ao cancelar ordem: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao cancelar ordem {order_id}: {e}")
            AuditService.log_error(
                operation='CANCEL_ORDER',
                entity_type='Order',
                entity_id=order_id,
                user_id=user_id,
                error_message=f"Erro inesperado: {str(e)}",
                error_details={'reason': reason}
            )
            raise ValueError(f"Erro inesperado ao cancelar ordem: {str(e)}")
    
    @staticmethod
    def open_dispute(order_id: int, client_id: int, reason: str, evidence_files=None) -> dict:
        """
        Cliente abre uma contestação sobre o serviço
        
        Args:
            order_id: ID da ordem
            client_id: ID do cliente
            reason: Motivo da contestação (mínimo 20 caracteres)
            evidence_files: Lista de arquivos FileStorage do Flask (opcional)
            
        Returns:
            dict com resultado da operação
            
        Process:
            1. Validar ordem (existe, pertence ao cliente, status=servico_executado)
            2. Validar prazo (dispute_deadline não expirado)
            3. Validar motivo (mínimo 20 caracteres)
            4. Implementar upload de arquivos de prova
            5. Validar tipos de arquivo (jpg, png, pdf, mp4)
            6. Validar tamanho (máximo 10MB por arquivo, máximo 5 arquivos)
            7. Sanitizar nomes de arquivo
            8. Salvar arquivos em diretório seguro
            9. Armazenar URLs dos arquivos em dispute_evidence_urls
            10. Atualizar ordem (status=contestada, dispute_opened_by, dispute_opened_at, dispute_client_statement)
            11. Bloquear confirmação automática
        """
        import os
        from services.security_validator import SecurityValidator
        
        # 1. Validar ordem (existe, pertence ao cliente, status=servico_executado)
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if order.client_id != client_id:
            raise ValueError("Apenas o cliente pode abrir contestação")
        
        if order.status != 'servico_executado':
            raise ValueError(f"Ordem não pode ser contestada. Status atual: {order.status}")
        
        # 2. Validar prazo (dispute_deadline não expirado)
        if not order.can_be_disputed:
            raise ValueError("Prazo para contestação expirado (36 horas)")
        
        # 3. Validar motivo (mínimo 20 caracteres)
        if not reason or len(reason.strip()) < 20:
            raise ValueError("O motivo da contestação deve ter no mínimo 20 caracteres")
        
        try:
            evidence_urls = []
            
            # 4-9. Processar upload de arquivos de prova usando SecurityValidator
            if evidence_files:
                # Configurações de upload
                UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'disputes')
                
                # Criar diretório se não existir
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                for file in evidence_files:
                    if file and file.filename:
                        # 5-6. Validar arquivo (tipo e tamanho) usando SecurityValidator
                        is_valid, error_msg = SecurityValidator.validate_file_upload(file)
                        if not is_valid:
                            raise ValueError(error_msg)
                        
                        # Obter tamanho do arquivo
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)  # Voltar ao início
                        
                        # Obter extensão
                        filename = file.filename.lower()
                        file_ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
                        
                        # 7. Sanitizar nome do arquivo usando SecurityValidator
                        unique_filename = SecurityValidator.sanitize_filename(file.filename, order_id)
                        
                        # 8. Salvar arquivo em diretório seguro
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        file.save(file_path)
                        
                        # 9. Armazenar URL relativa do arquivo
                        relative_url = f"/uploads/disputes/{unique_filename}"
                        evidence_urls.append({
                            'filename': file.filename,
                            'url': relative_url,
                            'uploaded_at': datetime.utcnow().isoformat(),
                            'size': file_size,
                            'type': file_ext
                        })
                        
                        logger.info(
                            f"Arquivo de prova salvo: {unique_filename} "
                            f"({file_size / 1024:.2f}KB) para ordem {order_id}"
                        )
            
            old_status = order.status
            
            # 10. Atualizar ordem
            order.status = 'contestada'
            order.dispute_opened_by = client_id
            order.dispute_opened_at = datetime.utcnow()
            order.dispute_reason = reason
            order.dispute_client_statement = reason
            order.dispute_evidence_urls = evidence_urls  # Usar o novo campo
            
            # Manter compatibilidade com campo antigo
            order.dispute_evidence = [item['url'] for item in evidence_urls]
            
            # Armazenar taxa de contestação
            contestation_fee = order.contestation_fee_at_creation or OrderManagementService.CONTESTATION_FEE
            order.contestation_fee = contestation_fee
            
            # 11. Bloquear confirmação automática (já bloqueado pelo status 'contestada')
            # O job de auto_confirm_expired_orders só processa ordens com status 'servico_executado'
            
            db.session.commit()
            
            # Registrar auditoria da abertura de contestação
            audit_id = AuditService.log_status_change(
                order_id=order_id,
                user_id=client_id,
                old_status=old_status,
                new_status='contestada',
                reason=reason[:200]
            )
            
            AuditService.log_dispute_opened(
                order_id=order_id,
                client_id=client_id,
                reason=reason,
                evidence_count=len(evidence_urls)
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Contestação aberta na ordem {order_id} pelo cliente {client_id}. "
                f"Motivo: {reason[:100]}... "
                f"Arquivos de prova: {len(evidence_urls)}"
            )
            
            order_operations_logger.info(
                f"CONTESTACAO_ABERTA | ID: {order_id} | Cliente: {client_id} | "
                f"Provas: {len(evidence_urls)} | Audit: {audit_id}"
            )
            
            # Enviar notificação para admin e prestador
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_dispute_opened(order)
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação de contestação aberta: {e}")
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'dispute_opened_at': order.dispute_opened_at,
                'contestation_fee': float(contestation_fee),
                'evidence_files_count': len(evidence_urls),
                'evidence_urls': evidence_urls,
                'message': 'Contestação aberta com sucesso. O admin irá analisar o caso e as provas apresentadas.'
            }
            
        except ValueError as e:
            db.session.rollback()
            logger.error(f"Erro de validação ao abrir contestação na ordem {order_id}: {e}")
            AuditService.log_error(
                operation='OPEN_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=client_id,
                error_message=str(e),
                error_details={'reason': reason[:200] if reason else None}
            )
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco de dados ao abrir contestação na ordem {order_id}: {e}")
            AuditService.log_error(
                operation='OPEN_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=client_id,
                error_message=f"Erro de banco de dados: {str(e)}",
                error_details={'reason': reason[:200] if reason else None}
            )
            raise ValueError(f"Erro ao abrir contestação: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao abrir contestação na ordem {order_id}: {e}")
            AuditService.log_error(
                operation='OPEN_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=client_id,
                error_message=f"Erro inesperado: {str(e)}",
                error_details={'reason': reason[:200] if reason else None}
            )
            raise ValueError(f"Erro inesperado ao abrir contestação: {str(e)}")
    
    @staticmethod
    def provider_respond_to_dispute(order_id: int, provider_id: int, response: str, evidence_files=None) -> dict:
        """
        Prestador responde à contestação do cliente
        
        Args:
            order_id: ID da ordem
            provider_id: ID do prestador
            response: Resposta/justificativa do prestador
            evidence_files: Lista de arquivos de prova (opcional)
            
        Returns:
            dict com resultado da operação
        """
        import os
        from services.security_validator import SecurityValidator
        
        # Validar ordem
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if order.provider_id != provider_id:
            raise ValueError("Você não é o prestador desta ordem")
        
        if order.status != 'contestada':
            raise ValueError("Esta ordem não está contestada")
        
        if order.dispute_provider_response:
            raise ValueError("Você já respondeu a esta contestação")
        
        # Validar resposta (mínimo 20 caracteres)
        if not response or len(response.strip()) < 20:
            raise ValueError("A resposta deve ter no mínimo 20 caracteres")
        
        try:
            evidence_urls = []
            
            # Processar upload de arquivos de prova
            if evidence_files:
                UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'disputes')
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                for file in evidence_files:
                    if file and file.filename:
                        # Validar arquivo
                        is_valid, error_msg = SecurityValidator.validate_file_upload(file)
                        if not is_valid:
                            raise ValueError(error_msg)
                        
                        # Obter tamanho do arquivo
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)
                        
                        # Obter extensão
                        filename = file.filename.lower()
                        file_ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
                        
                        # Sanitizar nome do arquivo
                        unique_filename = SecurityValidator.sanitize_filename(file.filename, order_id)
                        
                        # Salvar arquivo
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        file.save(file_path)
                        
                        # Armazenar URL relativa
                        evidence_urls.append({
                            'filename': file.filename,
                            'url': f"/uploads/disputes/{unique_filename}",
                            'uploaded_at': datetime.utcnow().isoformat(),
                            'uploaded_by': 'provider',
                            'size': file_size,
                            'type': file_ext
                        })
                        
                        logger.info(
                            f"Arquivo de prova do prestador salvo: {unique_filename} "
                            f"({file_size / 1024:.2f}KB) para ordem {order_id}"
                        )
            
            # Atualizar ordem com resposta do prestador
            order.dispute_provider_response = response
            
            # Adicionar evidências do prestador ao campo existente
            if evidence_urls:
                existing_evidence = order.dispute_evidence_urls or []
                order.dispute_evidence_urls = existing_evidence + evidence_urls
            
            db.session.commit()
            
            # Registrar auditoria
            AuditService.log_dispute_response(
                order_id=order_id,
                provider_id=provider_id,
                response=response,
                evidence_count=len(evidence_urls)
            )
            
            logger.info(
                f"Prestador {provider_id} respondeu contestação da ordem {order_id}. "
                f"Arquivos de prova: {len(evidence_urls)}"
            )
            
            order_operations_logger.info(
                f"CONTESTACAO_RESPONDIDA | ID: {order_id} | Prestador: {provider_id} | "
                f"Provas: {len(evidence_urls)}"
            )
            
            # Notificar admin que a resposta foi enviada
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_admin_dispute_response(order)
            except Exception as e:
                logger.warning(f"Erro ao notificar admin sobre resposta da contestação: {e}")
            
            return {
                'success': True,
                'order_id': order.id,
                'evidence_files_count': len(evidence_urls),
                'evidence_urls': evidence_urls,
                'message': 'Resposta enviada com sucesso! O administrador analisará a contestação com as informações de ambas as partes.'
            }
            
        except ValueError as e:
            db.session.rollback()
            logger.error(f"Erro de validação ao responder contestação {order_id}: {e}")
            AuditService.log_error(
                operation='PROVIDER_RESPOND_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=provider_id,
                error_message=str(e)
            )
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco de dados ao responder contestação {order_id}: {e}")
            AuditService.log_error(
                operation='PROVIDER_RESPOND_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=provider_id,
                error_message=f"Erro de banco de dados: {str(e)}"
            )
            raise ValueError(f"Erro ao responder contestação: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao responder contestação {order_id}: {e}")
            AuditService.log_error(
                operation='PROVIDER_RESPOND_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=provider_id,
                error_message=f"Erro inesperado: {str(e)}"
            )
            raise ValueError(f"Erro inesperado ao responder contestação: {str(e)}")
    
    @staticmethod
    def resolve_dispute(order_id: int, admin_id: int, winner: str, admin_notes: str = None) -> dict:
        """
        Admin arbitra uma contestação e resolve a disputa
        
        Args:
            order_id: ID da ordem
            admin_id: ID do admin que está resolvendo
            winner: 'client' ou 'provider' (quem ganhou a disputa)
            admin_notes: Notas/justificativa da decisão do admin (opcional)
            
        Returns:
            dict com resultado da operação e detalhes dos pagamentos
            
        Process:
            1. Validar ordem (existe, status=contestada)
            2. Validar winner ('client' ou 'provider')
            3. Se winner='client': devolver valor para cliente, transferir taxa_contestação do cliente para plataforma, prestador não recebe
            4. Se winner='provider': transferir valor menos taxa_plataforma para prestador, devolver taxa_contestação do prestador, transferir taxa_contestação do cliente para plataforma
            5. Atualizar ordem (status=resolvida, dispute_winner, dispute_resolved_at, dispute_admin_notes)
            6. Usar transação atômica
        """
        # 1. Validar ordem (existe, status=contestada)
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if order.status != 'contestada':
            raise ValueError(f"Ordem não está contestada. Status atual: {order.status}")
        
        # 2. Validar winner ('client' ou 'provider')
        if winner not in ['client', 'provider']:
            raise ValueError("Winner deve ser 'client' ou 'provider'")
        
        try:
            # Obter taxas vigentes no momento da criação da ordem
            platform_fee_percentage = order.platform_fee_percentage_at_creation or OrderManagementService.PLATFORM_FEE_PERCENTAGE
            contestation_fee = order.contestation_fee_at_creation or OrderManagementService.CONTESTATION_FEE
            
            # Converter valores para Decimal
            service_value = Decimal(str(order.value))
            contestation_fee = Decimal(str(contestation_fee))
            platform_fee_percentage = Decimal(str(platform_fee_percentage))
            
            # Calcular taxa da plataforma
            platform_fee = service_value * (platform_fee_percentage / Decimal('100'))
            provider_net_amount = service_value - platform_fee
            
            payment_details = {}
            
            # 3 e 4. Processar pagamentos conforme o vencedor
            if winner == 'client':
                # Cliente ganhou a disputa
                # - Devolver valor do serviço para o cliente (do escrow do cliente)
                # - Transferir taxa de contestação do cliente para a plataforma (do escrow do cliente)
                # - Devolver taxa de contestação do prestador (do escrow do prestador)
                # - Prestador não recebe nada
                
                # Devolver valor do serviço para o cliente
                WalletService.release_escrow_to_balance(
                    user_id=order.client_id,
                    amount=service_value,
                    order_id=order.id,
                    description=f"Devolução do valor da ordem #{order.id} (disputa resolvida a favor do cliente)"
                )
                
                # Transferir taxa de contestação do cliente para a plataforma
                WalletService.transfer_from_escrow_to_user(
                    from_user_id=order.client_id,
                    to_user_id=WalletService.ADMIN_USER_ID,
                    amount=contestation_fee,
                    order_id=order.id,
                    description=f"Taxa de contestação da ordem #{order.id} (disputa resolvida a favor do cliente)"
                )
                
                # Devolver taxa de contestação do prestador
                WalletService.release_escrow_to_balance(
                    user_id=order.provider_id,
                    amount=contestation_fee,
                    order_id=order.id,
                    description=f"Devolução da taxa de contestação da ordem #{order.id} (disputa resolvida a favor do cliente)"
                )
                
                payment_details = {
                    'winner': 'client',
                    'service_value_returned_to_client': float(service_value),
                    'contestation_fee_to_platform': float(contestation_fee),
                    'contestation_fee_returned_to_provider': float(contestation_fee),
                    'provider_received': 0.0,
                    'platform_received': float(contestation_fee),
                    'total_processed': float(service_value + contestation_fee + contestation_fee)
                }
                
                logger.info(
                    f"Disputa da ordem {order_id} resolvida a favor do CLIENTE. "
                    f"Valor devolvido ao cliente: R$ {service_value:.2f}, "
                    f"Taxa de contestação para plataforma: R$ {contestation_fee:.2f}, "
                    f"Taxa de contestação devolvida ao prestador: R$ {contestation_fee:.2f}"
                )
                
            else:  # winner == 'provider'
                # Prestador ganhou a disputa
                # - Transferir valor do serviço menos taxa da plataforma para o prestador (do escrow do cliente)
                # - Transferir taxa da plataforma para o admin (do escrow do cliente)
                # - Devolver taxa de contestação do prestador (do escrow do prestador)
                # - Transferir taxa de contestação do cliente para a plataforma (do escrow do cliente)
                
                # Transferir valor líquido para o prestador
                WalletService.transfer_from_escrow_to_user(
                    from_user_id=order.client_id,
                    to_user_id=order.provider_id,
                    amount=provider_net_amount,
                    order_id=order.id,
                    description=f"Pagamento pelo serviço da ordem #{order.id} (disputa resolvida a favor do prestador)"
                )
                
                # Transferir taxa da plataforma para o admin
                WalletService.transfer_from_escrow_to_user(
                    from_user_id=order.client_id,
                    to_user_id=WalletService.ADMIN_USER_ID,
                    amount=platform_fee,
                    order_id=order.id,
                    description=f"Taxa da plataforma ({platform_fee_percentage}%) da ordem #{order.id} (disputa resolvida a favor do prestador)"
                )
                
                # Devolver taxa de contestação do prestador
                WalletService.release_escrow_to_balance(
                    user_id=order.provider_id,
                    amount=contestation_fee,
                    order_id=order.id,
                    description=f"Devolução da taxa de contestação da ordem #{order.id} (disputa resolvida a favor do prestador)"
                )
                
                # Transferir taxa de contestação do cliente para a plataforma
                WalletService.transfer_from_escrow_to_user(
                    from_user_id=order.client_id,
                    to_user_id=WalletService.ADMIN_USER_ID,
                    amount=contestation_fee,
                    order_id=order.id,
                    description=f"Taxa de contestação da ordem #{order.id} (disputa resolvida a favor do prestador)"
                )
                
                payment_details = {
                    'winner': 'provider',
                    'service_value': float(service_value),
                    'platform_fee': float(platform_fee),
                    'platform_fee_percentage': float(platform_fee_percentage),
                    'provider_received': float(provider_net_amount),
                    'contestation_fee_returned_to_provider': float(contestation_fee),
                    'contestation_fee_to_platform': float(contestation_fee),
                    'platform_received': float(platform_fee + contestation_fee),
                    'total_processed': float(service_value + contestation_fee + contestation_fee)
                }
                
                logger.info(
                    f"Disputa da ordem {order_id} resolvida a favor do PRESTADOR. "
                    f"Prestador recebeu: R$ {provider_net_amount:.2f}, "
                    f"Taxa da plataforma: R$ {platform_fee:.2f}, "
                    f"Taxa de contestação devolvida ao prestador: R$ {contestation_fee:.2f}, "
                    f"Taxa de contestação do cliente para plataforma: R$ {contestation_fee:.2f}"
                )
            
            old_status = order.status
            
            # 5. Atualizar ordem (status=resolvida, dispute_winner, dispute_resolved_at, dispute_admin_notes)
            order.status = 'resolvida'
            order.dispute_winner = winner
            order.dispute_resolved_at = datetime.utcnow()
            order.dispute_resolved_by = admin_id
            order.dispute_admin_notes = admin_notes
            order.platform_fee = platform_fee if winner == 'provider' else Decimal('0')
            order.platform_fee_percentage = platform_fee_percentage if winner == 'provider' else Decimal('0')
            
            # 6. Commit da transação atômica
            db.session.commit()
            
            winner_name = "cliente" if winner == 'client' else "prestador"
            
            # Registrar auditoria da resolução de disputa
            audit_id = AuditService.log_status_change(
                order_id=order_id,
                user_id=admin_id,
                old_status=old_status,
                new_status='resolvida',
                reason=f"Disputa resolvida a favor do {winner_name}"
            )
            
            AuditService.log_dispute_resolved(
                order_id=order_id,
                admin_id=admin_id,
                winner=winner,
                admin_notes=admin_notes,
                payment_details=payment_details
            )
            
            logger.info(
                f"[AUDIT_ID: {audit_id}] Disputa da ordem {order_id} resolvida com sucesso pelo admin {admin_id}. "
                f"Vencedor: {winner_name}"
            )
            
            order_operations_logger.info(
                f"DISPUTA_RESOLVIDA | ID: {order_id} | Admin: {admin_id} | "
                f"Vencedor: {winner_name} | Audit: {audit_id}"
            )
            
            # Enviar notificações para ambas as partes
            from services.notification_service import NotificationService
            try:
                NotificationService.notify_dispute_resolved(order, winner=winner)
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação de disputa resolvida: {e}")
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'winner': winner,
                'winner_name': winner_name,
                'dispute_resolved_at': order.dispute_resolved_at,
                'dispute_resolved_by': admin_id,
                'admin_notes': admin_notes,
                'payments': payment_details,
                'message': f'Disputa resolvida a favor do {winner_name}. Pagamentos processados com sucesso.'
            }
            
        except ValueError as e:
            db.session.rollback()
            logger.error(f"Erro de validação ao resolver disputa da ordem {order_id}: {e}")
            AuditService.log_error(
                operation='RESOLVE_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=admin_id,
                error_message=str(e),
                error_details={'winner': winner, 'admin_notes': admin_notes[:200] if admin_notes else None}
            )
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco de dados ao resolver disputa da ordem {order_id}: {e}")
            AuditService.log_error(
                operation='RESOLVE_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=admin_id,
                error_message=f"Erro de banco de dados: {str(e)}",
                error_details={'winner': winner, 'admin_notes': admin_notes[:200] if admin_notes else None}
            )
            raise ValueError(f"Erro ao resolver disputa: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao resolver disputa da ordem {order_id}: {e}")
            AuditService.log_error(
                operation='RESOLVE_DISPUTE',
                entity_type='Order',
                entity_id=order_id,
                user_id=admin_id,
                error_message=f"Erro inesperado: {str(e)}",
                error_details={'winner': winner, 'admin_notes': admin_notes[:200] if admin_notes else None}
            )
            raise ValueError(f"Erro inesperado ao resolver disputa: {str(e)}")
    
    @staticmethod
    def get_orders_by_user(user_id: int, role: str, status_filter: str = None) -> list:
        """
        Retorna ordens de um usuário (como cliente ou prestador) com filtros de status
        
        Args:
            user_id: ID do usuário
            role: 'cliente' ou 'prestador'
            status_filter: Filtro de status (opcional)
            
        Returns:
            Lista de ordens ordenadas por data de criação (mais recentes primeiro)
            
        Features:
            - Eager loading de relacionamentos (client, provider) para otimização
            - Ordenação por created_at DESC
            - Filtro opcional por status
        """
        if role == 'cliente':
            query = Order.query.filter_by(client_id=user_id)
        elif role == 'prestador':
            query = Order.query.filter_by(provider_id=user_id)
        else:
            raise ValueError("Role deve ser 'cliente' ou 'prestador'")
        
        # Adicionar filtro de status se fornecido
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Adicionar eager loading de relacionamentos para otimização
        query = query.options(
            db.joinedload(Order.client),
            db.joinedload(Order.provider)
        )
        
        # Ordenar por created_at DESC (mais recentes primeiro)
        orders = query.order_by(Order.created_at.desc()).all()
        
        logger.info(
            f"Buscadas {len(orders)} ordens para usuário {user_id} "
            f"(role: {role}, filtro: {status_filter or 'todos'})"
        )
        
        return orders
    
    @staticmethod
    def get_order_statistics(user_id: int, role: str) -> dict:
        """
        Retorna estatísticas de ordens para o dashboard do usuário
        
        Args:
            user_id: ID do usuário
            role: 'cliente' ou 'prestador'
            
        Returns:
            Dict com contadores para o dashboard: {
                'total': int,                    # Total de ordens
                'aguardando': int,               # Aguardando execução
                'para_confirmar': int,           # Para confirmar (cliente) / Aguardando cliente (prestador)
                'concluidas': int,               # Concluídas
                'canceladas': int,               # Canceladas
                'contestadas': int,              # Contestadas
                'resolvidas': int                # Resolvidas
            }
        """
        if role == 'cliente':
            base_query = Order.query.filter_by(client_id=user_id)
        elif role == 'prestador':
            base_query = Order.query.filter_by(provider_id=user_id)
        else:
            raise ValueError("Role deve ser 'cliente' ou 'prestador'")
        
        # Contar total de ordens
        total = base_query.count()
        
        # Contar por status
        aguardando = base_query.filter_by(status='aguardando_execucao').count()
        para_confirmar = base_query.filter_by(status='servico_executado').count()
        concluidas = base_query.filter_by(status='concluida').count()
        canceladas = base_query.filter_by(status='cancelada').count()
        contestadas = base_query.filter_by(status='contestada').count()
        resolvidas = base_query.filter_by(status='resolvida').count()
        
        statistics = {
            'total': total,
            'aguardando': aguardando,
            'para_confirmar': para_confirmar,  # Cliente: "Para Confirmar", Prestador: "Aguardando Cliente"
            'concluidas': concluidas,
            'canceladas': canceladas,
            'contestadas': contestadas,
            'resolvidas': resolvidas
        }
        
        logger.info(
            f"Estatísticas de ordens para usuário {user_id} (role: {role}): "
            f"Total: {total}, Aguardando: {aguardando}, Para Confirmar: {para_confirmar}, "
            f"Concluídas: {concluidas}, Canceladas: {canceladas}, Contestadas: {contestadas}"
        )
        
        return statistics
