#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderConversionService - Serviço para conversão de pré-ordens em ordens definitivas

Este serviço gerencia o processo crítico de conversão de uma pré-ordem (negociação)
em uma ordem definitiva com bloqueio de valores em escrow.

Requirements: 5.1-5.5, 6.2-6.5, 14.1-14.5
"""

from models import (
    db, PreOrder, PreOrderStatus, PreOrderHistory, Order, User
)
from services.pre_order_state_manager import PreOrderStateManager
from services.wallet_service import WalletService
from services.order_service import OrderService
from services.notification_service import NotificationService
from services.config_service import ConfigService
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from typing import Dict, Tuple
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class PreOrderConversionService:
    """
    Serviço para conversão de pré-ordens em ordens definitivas
    
    Responsável por:
    - Validar saldos antes da conversão
    - Converter pré-ordem em ordem com transação atômica
    - Bloquear valores em escrow
    - Tratar erros com rollback completo
    - Reverter estado em caso de falha
    """
    
    @staticmethod
    def validate_balances(pre_order_id: int) -> Dict:
        """
        Valida se cliente e prestador têm saldo suficiente para conversão
        
        Cliente precisa de: valor do serviço + taxa de contestação
        Prestador precisa de: taxa de contestação
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            dict: Resultado da validação com detalhes de saldo
            
        Raises:
            ValueError: Se a pré-ordem não for encontrada
            
        Requirements: 5.2, 6.2, 6.3
        """
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Obter taxa de contestação configurada
            contestation_fee = ConfigService.get_contestation_fee()
            
            # Validar saldo do cliente
            client_wallet = WalletService.get_wallet_info(pre_order.client_id)
            client_balance = Decimal(str(client_wallet['balance']))
            client_required = pre_order.current_value + contestation_fee
            client_has_sufficient = client_balance >= client_required
            client_shortfall = max(Decimal('0'), client_required - client_balance)
            
            # Validar saldo do prestador
            provider_wallet = WalletService.get_wallet_info(pre_order.provider_id)
            provider_balance = Decimal(str(provider_wallet['balance']))
            provider_required = contestation_fee
            provider_has_sufficient = provider_balance >= provider_required
            provider_shortfall = max(Decimal('0'), provider_required - provider_balance)
            
            # Determinar se ambos têm saldo suficiente
            both_sufficient = client_has_sufficient and provider_has_sufficient
            
            validation_result = {
                'success': both_sufficient,
                'pre_order_id': pre_order_id,
                'client': {
                    'user_id': pre_order.client_id,
                    'current_balance': float(client_balance),
                    'required_amount': float(client_required),
                    'service_value': float(pre_order.current_value),
                    'contestation_fee': float(contestation_fee),
                    'has_sufficient': client_has_sufficient,
                    'shortfall': float(client_shortfall)
                },
                'provider': {
                    'user_id': pre_order.provider_id,
                    'current_balance': float(provider_balance),
                    'required_amount': float(provider_required),
                    'contestation_fee': float(contestation_fee),
                    'has_sufficient': provider_has_sufficient,
                    'shortfall': float(provider_shortfall)
                }
            }
            
            if not both_sufficient:
                # Construir mensagem de erro detalhada
                error_parts = []
                if not client_has_sufficient:
                    error_parts.append(
                        f"Cliente precisa de R$ {client_required:.2f} "
                        f"(serviço: R$ {pre_order.current_value:.2f} + "
                        f"taxa de contestação: R$ {contestation_fee:.2f}), "
                        f"mas tem apenas R$ {client_balance:.2f}. "
                        f"Faltam R$ {client_shortfall:.2f}."
                    )
                if not provider_has_sufficient:
                    error_parts.append(
                        f"Prestador precisa de R$ {provider_required:.2f} "
                        f"para taxa de contestação, mas tem apenas R$ {provider_balance:.2f}. "
                        f"Faltam R$ {provider_shortfall:.2f}."
                    )
                
                validation_result['error'] = ' '.join(error_parts)
                
                logger.warning(
                    f"Validação de saldo falhou para pré-ordem {pre_order_id}: "
                    f"{validation_result['error']}"
                )
            else:
                logger.info(
                    f"Validação de saldo bem-sucedida para pré-ordem {pre_order_id}. "
                    f"Cliente: R$ {client_balance:.2f} >= R$ {client_required:.2f}, "
                    f"Prestador: R$ {provider_balance:.2f} >= R$ {provider_required:.2f}"
                )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Erro ao validar saldos da pré-ordem {pre_order_id}: {str(e)}")
            raise e
    
    @staticmethod
    def convert_to_order(pre_order_id: int) -> Dict:
        """
        Converte uma pré-ordem em ordem definitiva com transação atômica
        
        Fluxo completo:
        1. Validar aceitação mútua
        2. Validar saldos de ambas as partes
        3. Criar ordem definitiva
        4. Bloquear valores em escrow (cliente: serviço + taxa, prestador: taxa)
        5. Atualizar pré-ordem para status CONVERTIDA
        6. Registrar no histórico
        7. Notificar ambas as partes
        
        Em caso de erro em qualquer etapa, faz rollback completo e reverte estado.
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            dict: Resultado da conversão com detalhes da ordem criada
            
        Raises:
            ValueError: Se validações falharem
            SQLAlchemyError: Se houver erro no banco de dados
            
        Requirements: 5.1-5.5, 6.2-6.5, 14.1-14.5
        """
        pre_order = None
        original_status = None
        order_created = None
        escrow_blocked = False
        
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Guardar status original para possível reversão
            original_status = pre_order.status
            
            logger.info(
                f"Iniciando conversão da pré-ordem {pre_order_id} em ordem. "
                f"Status atual: {original_status}"
            )
            
            # Requirement 5.1: Validar aceitação mútua
            if not pre_order.has_mutual_acceptance:
                raise ValueError(
                    f"Conversão não permitida: aceitação mútua não alcançada. "
                    f"Cliente aceitou: {pre_order.client_accepted_terms}, "
                    f"Prestador aceitou: {pre_order.provider_accepted_terms}"
                )
            
            # Verificar se não há proposta pendente
            if pre_order.has_active_proposal:
                raise ValueError(
                    "Conversão não permitida: há uma proposta pendente. "
                    "Responda à proposta antes de converter."
                )
            
            # Verificar se pré-ordem está no estado correto
            if pre_order.status != PreOrderStatus.PRONTO_CONVERSAO.value:
                raise ValueError(
                    f"Conversão não permitida: pré-ordem não está no estado PRONTO_CONVERSAO. "
                    f"Estado atual: {pre_order.status_display}"
                )
            
            # Verificar se não expirou
            if pre_order.is_expired:
                raise ValueError(
                    f"Conversão não permitida: pré-ordem expirou em {pre_order.expires_at}"
                )
            
            # Requirement 5.2, 6.2, 6.3: Validar saldos
            validation_result = PreOrderConversionService.validate_balances(pre_order_id)
            if not validation_result['success']:
                raise ValueError(
                    f"Saldo insuficiente para conversão: {validation_result['error']}"
                )
            
            logger.info(f"Validação de saldos bem-sucedida para pré-ordem {pre_order_id}")
            
            # Requirement 5.4: Criar ordem definitiva
            # Usar OrderService.create_order que já faz o bloqueio em escrow
            order_result = OrderService.create_order(
                client_id=pre_order.client_id,
                title=pre_order.title,
                description=pre_order.description,
                value=float(pre_order.current_value),
                invite_id=pre_order.invite_id
            )
            
            order_created = order_result['order']
            escrow_blocked = True
            
            logger.info(
                f"Ordem {order_created.id} criada com sucesso. "
                f"Valor bloqueado em escrow: R$ {order_created.value:.2f}"
            )
            
            # Requirement 6.4: Bloquear taxa de contestação do prestador
            contestation_fee = ConfigService.get_contestation_fee()
            provider_escrow_result = WalletService.transfer_to_escrow(
                user_id=pre_order.provider_id,
                amount=Decimal(str(contestation_fee)),
                order_id=order_created.id
            )
            
            logger.info(
                f"Taxa de contestação do prestador bloqueada: R$ {contestation_fee:.2f}"
            )
            
            # Atribuir prestador à ordem
            order_created.provider_id = pre_order.provider_id
            order_created.status = 'aceita'
            order_created.accepted_at = datetime.utcnow()
            
            # Requirement 5.5: Atualizar pré-ordem
            pre_order.status = PreOrderStatus.CONVERTIDA.value
            pre_order.order_id = order_created.id
            pre_order.converted_at = datetime.utcnow()
            pre_order.updated_at = datetime.utcnow()
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type='converted',
                actor_id=pre_order.client_id,  # Sistema/ambas as partes
                description=f'Pré-ordem convertida em ordem #{order_created.id}',
                event_data={
                    'order_id': order_created.id,
                    'final_value': float(pre_order.current_value),
                    'original_value': float(pre_order.original_value),
                    'value_change': float(pre_order.value_difference_from_original),
                    'client_escrow': float(order_created.value),
                    'provider_escrow': float(contestation_fee),
                    'converted_at': datetime.utcnow().isoformat()
                }
            )
            db.session.add(history_entry)
            
            # Commit da transação
            db.session.commit()
            
            logger.info(
                f"Pré-ordem {pre_order_id} convertida com sucesso em ordem {order_created.id}. "
                f"Valores bloqueados: Cliente R$ {order_created.value:.2f}, "
                f"Prestador R$ {contestation_fee:.2f}"
            )
            
            # Notificar ambas as partes
            NotificationService.notify_pre_order_converted(
                pre_order_id=pre_order_id,
                order_id=order_created.id,
                client_id=pre_order.client_id,
                provider_id=pre_order.provider_id,
                value=float(pre_order.current_value)
            )
            
            return {
                'success': True,
                'pre_order_id': pre_order_id,
                'order_id': order_created.id,
                'order_status': order_created.status,
                'final_value': float(pre_order.current_value),
                'original_value': float(pre_order.original_value),
                'value_change': float(pre_order.value_difference_from_original),
                'client_escrow_blocked': float(order_created.value),
                'provider_escrow_blocked': float(contestation_fee),
                'converted_at': pre_order.converted_at.isoformat(),
                'message': (
                    f'Pré-ordem convertida com sucesso em ordem #{order_created.id}! '
                    f'Valores bloqueados em escrow. O serviço pode ser iniciado.'
                )
            }
            
        except ValueError as e:
            # Erro de validação - não precisa reverter estado do banco
            db.session.rollback()
            
            error_msg = str(e)
            logger.error(
                f"Erro de validação ao converter pré-ordem {pre_order_id}: {error_msg}"
            )
            
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'validation_error',
                'pre_order_id': pre_order_id
            }
            
        except SQLAlchemyError as e:
            # Erro no banco de dados - fazer rollback
            db.session.rollback()
            
            error_msg = f"Erro no banco de dados durante conversão: {str(e)}"
            logger.error(
                f"Erro SQL ao converter pré-ordem {pre_order_id}: {error_msg}",
                exc_info=True
            )
            
            # Requirement 14.2, 14.3: Reverter estado em caso de falha
            if pre_order and original_status:
                try:
                    PreOrderConversionService._revert_pre_order_state(
                        pre_order_id=pre_order_id,
                        original_status=original_status,
                        reason=f"Falha na conversão: {error_msg}"
                    )
                except Exception as revert_error:
                    logger.error(
                        f"Erro ao reverter estado da pré-ordem {pre_order_id}: {str(revert_error)}"
                    )
            
            # Requirement 14.4: Notificar partes sobre erro
            if pre_order:
                try:
                    NotificationService.notify_conversion_error(
                        pre_order_id=pre_order_id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id,
                        error_message="Erro técnico durante a conversão. Tente novamente."
                    )
                except Exception as notify_error:
                    logger.error(
                        f"Erro ao notificar sobre falha de conversão: {str(notify_error)}"
                    )
            
            return {
                'success': False,
                'error': 'Erro técnico durante a conversão. Por favor, tente novamente.',
                'error_type': 'database_error',
                'error_details': error_msg,
                'pre_order_id': pre_order_id,
                'state_reverted': True
            }
            
        except Exception as e:
            # Erro inesperado - fazer rollback e reverter
            db.session.rollback()
            
            error_msg = f"Erro inesperado durante conversão: {str(e)}"
            logger.error(
                f"Erro inesperado ao converter pré-ordem {pre_order_id}: {error_msg}",
                exc_info=True
            )
            
            # Requirement 14.2, 14.3: Reverter estado em caso de falha
            if pre_order and original_status:
                try:
                    PreOrderConversionService._revert_pre_order_state(
                        pre_order_id=pre_order_id,
                        original_status=original_status,
                        reason=f"Falha inesperada na conversão: {error_msg}"
                    )
                except Exception as revert_error:
                    logger.error(
                        f"Erro ao reverter estado da pré-ordem {pre_order_id}: {str(revert_error)}"
                    )
            
            # Requirement 14.4: Notificar partes sobre erro
            if pre_order:
                try:
                    NotificationService.notify_conversion_error(
                        pre_order_id=pre_order_id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id,
                        error_message="Erro inesperado durante a conversão. Tente novamente."
                    )
                except Exception as notify_error:
                    logger.error(
                        f"Erro ao notificar sobre falha de conversão: {str(notify_error)}"
                    )
            
            return {
                'success': False,
                'error': 'Erro inesperado durante a conversão. Por favor, tente novamente.',
                'error_type': 'unexpected_error',
                'error_details': error_msg,
                'pre_order_id': pre_order_id,
                'state_reverted': True
            }
    
    @staticmethod
    def _revert_pre_order_state(pre_order_id: int, original_status: str, reason: str) -> None:
        """
        Reverte o estado da pré-ordem em caso de falha na conversão
        
        Args:
            pre_order_id: ID da pré-ordem
            original_status: Status original antes da tentativa de conversão
            reason: Motivo da reversão
            
        Requirements: 14.2, 14.3
        """
        try:
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                logger.warning(f"Pré-ordem {pre_order_id} não encontrada para reversão")
                return
            
            # Reverter para estado original
            pre_order.status = original_status
            pre_order.order_id = None
            pre_order.converted_at = None
            pre_order.updated_at = datetime.utcnow()
            
            # Registrar reversão no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type='conversion_failed',
                actor_id=pre_order.client_id,  # Sistema
                description=f'Conversão falhou e estado foi revertido para {original_status}',
                event_data={
                    'original_status': original_status,
                    'reason': reason,
                    'reverted_at': datetime.utcnow().isoformat()
                }
            )
            db.session.add(history_entry)
            
            db.session.commit()
            
            logger.info(
                f"Estado da pré-ordem {pre_order_id} revertido para {original_status}. "
                f"Motivo: {reason}"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Erro crítico ao reverter estado da pré-ordem {pre_order_id}: {str(e)}",
                exc_info=True
            )
            raise e
