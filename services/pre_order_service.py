#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderService - Serviço principal para gerenciamento de pré-ordens

Este serviço gerencia o ciclo de vida completo das pré-ordens, desde a criação
a partir de convites aceitos até o cancelamento ou conversão em ordem definitiva.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 7.1, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5
"""

from models import (
    db, PreOrder, PreOrderStatus, PreOrderHistory, Invite, User
)
from services.pre_order_state_manager import PreOrderStateManager
from services.notification_service import NotificationService
from services.wallet_service import WalletService
from services.pre_order_cache_service import PreOrderCacheService
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from typing import Optional, Dict, Tuple, List
from decimal import Decimal
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class PreOrderService:
    """
    Serviço principal para gerenciamento de pré-ordens
    
    Responsável por:
    - Criar pré-ordens a partir de convites aceitos
    - Gerenciar aceitação de termos pelas partes
    - Cancelar pré-ordens
    - Validar saldos antes de aceitação
    - Integrar com NotificationService e PreOrderStateManager
    """
    
    # Prazo padrão de negociação (7 dias)
    DEFAULT_NEGOTIATION_DAYS = 7
    
    @staticmethod
    def create_from_invite(invite_id: int) -> Dict:
        """
        Cria uma pré-ordem a partir de um convite aceito
        
        Quando um convite é aceito, ao invés de criar uma ordem imediatamente,
        criamos uma pré-ordem que permite negociação antes do compromisso financeiro.
        
        Args:
            invite_id: ID do convite aceito
            
        Returns:
            dict: Resultado da criação com detalhes da pré-ordem
            
        Raises:
            ValueError: Se o convite não for encontrado ou já tiver pré-ordem
            SQLAlchemyError: Se houver erro no banco de dados
            
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        try:
            # Buscar convite
            invite = Invite.query.get(invite_id)
            if not invite:
                raise ValueError(f"Convite {invite_id} não encontrado")
            
            # Verificar se já existe pré-ordem para este convite
            existing_pre_order = PreOrder.query.filter_by(invite_id=invite_id).first()
            if existing_pre_order:
                logger.warning(f"Convite {invite_id} já possui pré-ordem {existing_pre_order.id}")
                return {
                    'success': False,
                    'error': 'Convite já possui pré-ordem associada',
                    'pre_order_id': existing_pre_order.id
                }
            
            # Identificar cliente e prestador
            client_id = invite.client_id
            
            # Buscar prestador pelo telefone do convite
            provider = User.query.filter_by(phone=invite.invited_phone).first()
            if not provider:
                raise ValueError(f"Prestador não encontrado para o telefone {invite.invited_phone}")
            
            provider_id = provider.id
            
            # Calcular data de expiração (7 dias a partir de agora)
            expires_at = datetime.utcnow() + timedelta(days=PreOrderService.DEFAULT_NEGOTIATION_DAYS)
            
            # Criar pré-ordem copiando dados do convite
            # Requirement 1.2: Copiar todos os dados do convite
            pre_order = PreOrder(
                invite_id=invite_id,
                client_id=client_id,
                provider_id=provider_id,
                title=invite.service_title,
                description=invite.service_description,
                current_value=invite.current_value,  # Valor atual (pode ter sido modificado por proposta)
                original_value=invite.original_value,  # Valor original do convite
                delivery_date=invite.delivery_date,
                service_category=invite.service_category,
                status=PreOrderStatus.EM_NEGOCIACAO.value,
                expires_at=expires_at,
                client_accepted_terms=False,
                provider_accepted_terms=False,
                has_active_proposal=False
            )
            
            db.session.add(pre_order)
            db.session.flush()  # Para obter o ID da pré-ordem
            
            # Requirement 1.3: Marcar convite como convertido
            invite.status = 'convertido_pre_ordem'
            
            # Registrar criação no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='created',
                actor_id=client_id,  # Cliente é quem iniciou o convite
                description=f'Pré-ordem criada a partir do convite #{invite_id}',
                event_data={
                    'invite_id': invite_id,
                    'initial_value': float(pre_order.current_value),
                    'delivery_date': pre_order.delivery_date.isoformat(),
                    'expires_at': expires_at.isoformat()
                }
            )
            db.session.add(history_entry)
            
            # Commit da transação
            db.session.commit()
            
            # Invalidar cache dos usuários
            PreOrderCacheService.invalidate_user_pre_orders(client_id)
            PreOrderCacheService.invalidate_user_pre_orders(provider_id)
            
            # Requirement 1.4: Notificar ambas as partes
            # Notificar cliente
            NotificationService.notify_pre_order_created(
                pre_order_id=pre_order.id,
                user_id=client_id,
                user_type='cliente'
            )
            
            # Notificar prestador
            NotificationService.notify_pre_order_created(
                pre_order_id=pre_order.id,
                user_id=provider_id,
                user_type='prestador'
            )
            
            logger.info(
                f"Pré-ordem {pre_order.id} criada a partir do convite {invite_id}. "
                f"Cliente: {client_id}, Prestador: {provider_id}, "
                f"Valor: R$ {pre_order.current_value:.2f}, Expira em: {expires_at}"
            )
            
            # Requirement 1.5: NÃO bloquear valores neste estágio
            # (valores só serão bloqueados na conversão para ordem)
            
            return {
                'success': True,
                'pre_order_id': pre_order.id,
                'invite_id': invite_id,
                'client_id': client_id,
                'provider_id': provider_id,
                'current_value': float(pre_order.current_value),
                'original_value': float(pre_order.original_value),
                'status': pre_order.status,
                'expires_at': expires_at.isoformat(),
                'message': 'Pré-ordem criada com sucesso. Valores não foram bloqueados.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao criar pré-ordem do convite {invite_id}: {str(e)}")
            raise e
    
    @staticmethod
    def get_pre_order_details(pre_order_id: int, user_id: int, use_cache: bool = True) -> Dict:
        """
        Retorna detalhes completos de uma pré-ordem com validação de permissão
        
        Apenas o cliente ou prestador envolvidos podem visualizar a pré-ordem.
        Usa cache para otimizar consultas frequentes (TTL: 3 min).
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário solicitante
            use_cache: Se deve usar cache (padrão: True)
            
        Returns:
            dict: Detalhes completos da pré-ordem
            
        Raises:
            ValueError: Se a pré-ordem não for encontrada
            PermissionError: Se o usuário não tiver permissão
            
        Requirements: 1.1, 1.2, 1.3, 1.4
        """
        # Tentar obter do cache
        if use_cache:
            cached_details = PreOrderCacheService.get_pre_order_details(pre_order_id, user_id)
            if cached_details is not None:
                logger.debug(f"Cache HIT: detalhes da pré-ordem {pre_order_id}")
                return cached_details
        
        # Buscar pré-ordem
        pre_order = PreOrder.query.get(pre_order_id)
        if not pre_order:
            raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
        
        # Validar permissão: apenas cliente ou prestador podem visualizar
        if user_id not in [pre_order.client_id, pre_order.provider_id]:
            logger.warning(
                f"Usuário {user_id} tentou acessar pré-ordem {pre_order_id} "
                f"sem permissão (cliente: {pre_order.client_id}, prestador: {pre_order.provider_id})"
            )
            raise PermissionError("Você não tem permissão para visualizar esta pré-ordem")
        
        # Obter informações das partes
        client = User.query.get(pre_order.client_id)
        provider = User.query.get(pre_order.provider_id)
        
        # Obter histórico
        history = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order_id
        ).order_by(PreOrderHistory.created_at.desc()).all()
        
        # Obter proposta ativa se existir
        active_proposal = pre_order.get_active_proposal()
        
        # Obter descrição do estado
        state_description = PreOrderStateManager.get_state_description(pre_order)
        
        # Determinar se usuário é cliente ou prestador
        is_client = (user_id == pre_order.client_id)
        user_role = 'cliente' if is_client else 'prestador'
        
        result = {
            'success': True,
            'pre_order': {
                'id': pre_order.id,
                'invite_id': pre_order.invite_id,
                'title': pre_order.title,
                'description': pre_order.description,
                'current_value': float(pre_order.current_value),
                'original_value': float(pre_order.original_value),
                'value_difference': float(pre_order.value_difference_from_original),
                'value_change_percentage': float(pre_order.value_change_percentage),
                'delivery_date': pre_order.delivery_date.isoformat(),
                'service_category': pre_order.service_category,
                'status': pre_order.status,
                'status_display': pre_order.status_display,
                'status_color_class': pre_order.status_color_class,
                'client_accepted_terms': pre_order.client_accepted_terms,
                'provider_accepted_terms': pre_order.provider_accepted_terms,
                'has_mutual_acceptance': pre_order.has_mutual_acceptance,
                'pending_acceptance_from': pre_order.pending_acceptance_from,
                'has_active_proposal': pre_order.has_active_proposal,
                'created_at': pre_order.created_at.isoformat(),
                'updated_at': pre_order.updated_at.isoformat(),
                'expires_at': pre_order.expires_at.isoformat(),
                'is_expired': pre_order.is_expired,
                'days_until_expiration': pre_order.days_until_expiration,
                'is_near_expiration': pre_order.is_near_expiration,
                'can_be_converted': pre_order.can_be_converted,
                'cancelled_at': pre_order.cancelled_at.isoformat() if pre_order.cancelled_at else None,
                'cancellation_reason': pre_order.cancellation_reason,
                'converted_at': pre_order.converted_at.isoformat() if pre_order.converted_at else None,
                'order_id': pre_order.order_id
            },
            'client': {
                'id': client.id,
                'nome': client.nome,
                'email': client.email
            } if client else None,
            'provider': {
                'id': provider.id,
                'nome': provider.nome,
                'email': provider.email
            } if provider else None,
            'active_proposal': {
                'id': active_proposal.id,
                'proposed_by': active_proposal.proposed_by,
                'proposed_value': float(active_proposal.proposed_value) if active_proposal.proposed_value else None,
                'proposed_delivery_date': active_proposal.proposed_delivery_date.isoformat() if active_proposal.proposed_delivery_date else None,
                'proposed_description': active_proposal.proposed_description,
                'justification': active_proposal.justification,
                'status': active_proposal.status,
                'created_at': active_proposal.created_at.isoformat()
            } if active_proposal else None,
            'history': [
                {
                    'id': h.id,
                    'event_type': h.event_type,
                    'event_type_display': h.event_type_display,
                    'actor_id': h.actor_id,
                    'actor_name': h.actor.nome if h.actor else 'Sistema',
                    'description': h.description,
                    'event_data': h.event_data,
                    'created_at': h.created_at.isoformat()
                } for h in history
            ],
            'state_description': state_description,
            'user_role': user_role,
            'user_message': state_description.get('client_message' if is_client else 'provider_message')
        }
        
        # Armazenar no cache
        if use_cache:
            PreOrderCacheService.set_pre_order_details(pre_order_id, user_id, result)
            logger.debug(f"Cache SET: detalhes da pré-ordem {pre_order_id}")
        
        return result
    
    @staticmethod
    def accept_terms(pre_order_id: int, user_id: int) -> Dict:
        """
        Marca aceitação de termos por uma das partes com validação de saldo
        
        Quando ambas as partes aceitam os termos, a pré-ordem fica pronta para conversão.
        Antes de aceitar, valida se o usuário tem saldo suficiente.
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário que está aceitando
            
        Returns:
            dict: Resultado da aceitação
            
        Raises:
            ValueError: Se a pré-ordem não for encontrada ou usuário não tiver permissão
            PermissionError: Se o usuário não for parte da pré-ordem
            
        Requirements: 5.1, 7.1, 7.5
        """
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Validar permissão
            if user_id not in [pre_order.client_id, pre_order.provider_id]:
                raise PermissionError("Você não tem permissão para aceitar termos desta pré-ordem")
            
            # Verificar se pré-ordem está em estado válido para aceitação
            if pre_order.status not in [PreOrderStatus.EM_NEGOCIACAO.value, PreOrderStatus.AGUARDANDO_RESPOSTA.value]:
                return {
                    'success': False,
                    'error': f'Não é possível aceitar termos no estado {pre_order.status_display}',
                    'current_status': pre_order.status
                }
            
            # Verificar se há proposta pendente
            if pre_order.has_active_proposal:
                return {
                    'success': False,
                    'error': 'Há uma proposta pendente. Responda à proposta antes de aceitar os termos.',
                    'has_active_proposal': True
                }
            
            # Determinar se é cliente ou prestador
            is_client = (user_id == pre_order.client_id)
            user_role = 'cliente' if is_client else 'prestador'
            
            # Requirement 7.1: Validar saldo antes de aceitar
            if is_client:
                # Cliente precisa ter saldo para o valor do serviço + taxa de contestação
                from services.config_service import ConfigService
                contestation_fee = ConfigService.get_contestation_fee()
                required_amount = pre_order.current_value + contestation_fee
                
                wallet_info = WalletService.get_wallet_info(user_id)
                current_balance = Decimal(str(wallet_info['balance']))
                
                if current_balance < required_amount:
                    shortfall = required_amount - current_balance
                    logger.warning(
                        f"Cliente {user_id} tentou aceitar termos da pré-ordem {pre_order_id} "
                        f"com saldo insuficiente. Necessário: R$ {required_amount:.2f}, "
                        f"Atual: R$ {current_balance:.2f}, Faltam: R$ {shortfall:.2f}"
                    )
                    return {
                        'success': False,
                        'error': 'Saldo insuficiente',
                        'required_amount': float(required_amount),
                        'current_balance': float(current_balance),
                        'shortfall': float(shortfall),
                        'message': (
                            f'Saldo insuficiente para aceitar os termos. '
                            f'Você precisa de R$ {required_amount:.2f} '
                            f'(serviço + taxa de contestação), mas tem apenas R$ {current_balance:.2f}. '
                            f'Adicione pelo menos R$ {shortfall:.2f} para continuar.'
                        )
                    }
            else:
                # Prestador precisa ter saldo para a taxa de contestação
                from services.config_service import ConfigService
                contestation_fee = ConfigService.get_contestation_fee()
                required_amount = contestation_fee
                
                wallet_info = WalletService.get_wallet_info(user_id)
                current_balance = Decimal(str(wallet_info['balance']))
                
                if current_balance < required_amount:
                    shortfall = required_amount - current_balance
                    logger.warning(
                        f"Prestador {user_id} tentou aceitar termos da pré-ordem {pre_order_id} "
                        f"com saldo insuficiente. Necessário: R$ {required_amount:.2f}, "
                        f"Atual: R$ {current_balance:.2f}, Faltam: R$ {shortfall:.2f}"
                    )
                    return {
                        'success': False,
                        'error': 'Saldo insuficiente',
                        'required_amount': float(required_amount),
                        'current_balance': float(current_balance),
                        'shortfall': float(shortfall),
                        'message': (
                            f'Saldo insuficiente para aceitar os termos. '
                            f'Você precisa de R$ {required_amount:.2f} para a taxa de contestação, '
                            f'mas tem apenas R$ {current_balance:.2f}. '
                            f'Adicione pelo menos R$ {shortfall:.2f} para continuar.'
                        )
                    }
            
            # Requirement 7.5: Marcar aceitação
            if is_client:
                pre_order.client_accepted_terms = True
                pre_order.client_accepted_at = datetime.utcnow()
                event_type = 'terms_accepted_client'
                description = 'Cliente aceitou os termos finais'
            else:
                pre_order.provider_accepted_terms = True
                pre_order.provider_accepted_at = datetime.utcnow()
                event_type = 'terms_accepted_provider'
                description = 'Prestador aceitou os termos finais'
            
            pre_order.updated_at = datetime.utcnow()
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type=event_type,
                actor_id=user_id,
                description=description,
                event_data={
                    'user_role': user_role,
                    'current_value': float(pre_order.current_value),
                    'client_accepted': pre_order.client_accepted_terms,
                    'provider_accepted': pre_order.provider_accepted_terms
                }
            )
            db.session.add(history_entry)
            
            # Requirement 5.1: Verificar aceitação mútua
            has_mutual_acceptance = PreOrderStateManager.check_mutual_acceptance(pre_order_id)
            
            # Se ambos aceitaram, transicionar para PRONTO_CONVERSAO e converter automaticamente
            if has_mutual_acceptance:
                PreOrderStateManager.transition_to(
                    pre_order_id=pre_order_id,
                    new_status=PreOrderStatus.PRONTO_CONVERSAO,
                    actor_id=user_id,
                    reason='Ambas as partes aceitaram os termos finais'
                )
                
                db.session.commit()
                
                # Converter automaticamente para ordem
                from services.pre_order_conversion_service import PreOrderConversionService
                conversion_result = PreOrderConversionService.convert_to_order(pre_order_id)
                
                if conversion_result.get('success'):
                    logger.info(
                        f"Pré-ordem {pre_order_id} convertida automaticamente em ordem {conversion_result.get('order_id')}"
                    )
                    
                    # Invalidar cache
                    PreOrderService.invalidate_pre_order_cache(
                        pre_order_id=pre_order_id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id
                    )
                    
                    return {
                        'success': True,
                        'pre_order_id': pre_order_id,
                        'user_id': user_id,
                        'user_role': user_role,
                        'client_accepted': True,
                        'provider_accepted': True,
                        'has_mutual_acceptance': True,
                        'new_status': 'convertida',
                        'order_created': True,
                        'order_id': conversion_result.get('order_id'),
                        'message': f'Ambas as partes aceitaram! Ordem #{conversion_result.get("order_id")} criada automaticamente.'
                    }
                else:
                    # Se falhou a conversão, notificar e retornar erro
                    logger.error(
                        f"Falha ao converter pré-ordem {pre_order_id}: {conversion_result.get('error')}"
                    )
                    
                    # Notificar ambas as partes sobre o erro
                    NotificationService.notify_pre_order_ready_for_conversion(
                        pre_order_id=pre_order_id,
                        client_id=pre_order.client_id,
                        provider_id=pre_order.provider_id
                    )
                    
                    return {
                        'success': True,
                        'pre_order_id': pre_order_id,
                        'user_id': user_id,
                        'user_role': user_role,
                        'client_accepted': True,
                        'provider_accepted': True,
                        'has_mutual_acceptance': True,
                        'new_status': pre_order.status,
                        'order_created': False,
                        'conversion_error': conversion_result.get('error'),
                        'message': 'Ambas as partes aceitaram os termos! Houve um erro na conversão automática, tente novamente.'
                    }
            else:
                # Notificar a outra parte que uma aceitação foi registrada
                other_party_id = pre_order.provider_id if is_client else pre_order.client_id
                NotificationService.notify_terms_accepted(
                    pre_order_id=pre_order_id,
                    acceptor_id=user_id,
                    acceptor_role=user_role,
                    other_party_id=other_party_id
                )
            
            db.session.commit()
            
            # Invalidar cache
            PreOrderService.invalidate_pre_order_cache(
                pre_order_id=pre_order_id,
                client_id=pre_order.client_id,
                provider_id=pre_order.provider_id
            )
            
            logger.info(
                f"Pré-ordem {pre_order_id}: {user_role} {user_id} aceitou os termos. "
                f"Aceitação mútua: {has_mutual_acceptance}"
            )
            
            return {
                'success': True,
                'pre_order_id': pre_order_id,
                'user_id': user_id,
                'user_role': user_role,
                'client_accepted': pre_order.client_accepted_terms,
                'provider_accepted': pre_order.provider_accepted_terms,
                'has_mutual_acceptance': has_mutual_acceptance,
                'new_status': pre_order.status,
                'message': 'Termos aceitos com sucesso! Aguardando aceitação da outra parte.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao aceitar termos da pré-ordem {pre_order_id}: {str(e)}")
            raise e
    
    @staticmethod
    def cancel_pre_order(pre_order_id: int, user_id: int, reason: str) -> Dict:
        """
        Cancela uma pré-ordem com validação de motivo obrigatório
        
        Qualquer uma das partes pode cancelar a pré-ordem durante a negociação.
        O motivo é obrigatório para auditoria.
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário que está cancelando
            reason: Motivo do cancelamento (obrigatório)
            
        Returns:
            dict: Resultado do cancelamento
            
        Raises:
            ValueError: Se a pré-ordem não for encontrada ou motivo não for fornecido
            PermissionError: Se o usuário não tiver permissão
            
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
        """
        try:
            # Requirement 8.2: Validar motivo obrigatório
            if not reason or len(reason.strip()) < 10:
                raise ValueError("Motivo do cancelamento é obrigatório e deve ter pelo menos 10 caracteres")
            
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Requirement 8.1: Validar permissão (apenas cliente ou prestador)
            if user_id not in [pre_order.client_id, pre_order.provider_id]:
                raise PermissionError("Você não tem permissão para cancelar esta pré-ordem")
            
            # Verificar se pré-ordem pode ser cancelada
            if pre_order.status in [PreOrderStatus.CONVERTIDA.value, PreOrderStatus.CANCELADA.value, PreOrderStatus.EXPIRADA.value]:
                return {
                    'success': False,
                    'error': f'Não é possível cancelar pré-ordem no estado {pre_order.status_display}',
                    'current_status': pre_order.status
                }
            
            # Determinar quem está cancelando
            is_client = (user_id == pre_order.client_id)
            user_role = 'cliente' if is_client else 'prestador'
            other_party_id = pre_order.provider_id if is_client else pre_order.client_id
            
            # Requirement 8.4: Transicionar para CANCELADA
            PreOrderStateManager.transition_to(
                pre_order_id=pre_order_id,
                new_status=PreOrderStatus.CANCELADA,
                actor_id=user_id,
                reason=f'Cancelado por {user_role}: {reason}'
            )
            
            # Atualizar campos de cancelamento
            pre_order.cancelled_by = user_id
            pre_order.cancellation_reason = reason
            pre_order.cancelled_at = datetime.utcnow()
            pre_order.updated_at = datetime.utcnow()
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type='cancelled',
                actor_id=user_id,
                description=f'Pré-ordem cancelada por {user_role}',
                event_data={
                    'cancelled_by': user_id,
                    'user_role': user_role,
                    'reason': reason,
                    'previous_status': PreOrderStatus.EM_NEGOCIACAO.value
                }
            )
            db.session.add(history_entry)
            
            db.session.commit()
            
            # Invalidar cache
            PreOrderService.invalidate_pre_order_cache(
                pre_order_id=pre_order_id,
                client_id=pre_order.client_id,
                provider_id=pre_order.provider_id
            )
            
            # Requirement 8.3: Notificar a outra parte
            NotificationService.notify_pre_order_cancelled(
                pre_order_id=pre_order_id,
                cancelled_by_id=user_id,
                cancelled_by_role=user_role,
                other_party_id=other_party_id,
                reason=reason
            )
            
            logger.info(
                f"Pré-ordem {pre_order_id} cancelada por {user_role} {user_id}. "
                f"Motivo: {reason}"
            )
            
            # Requirement 8.5: NÃO criar ordem
            return {
                'success': True,
                'pre_order_id': pre_order_id,
                'cancelled_by': user_id,
                'user_role': user_role,
                'reason': reason,
                'cancelled_at': pre_order.cancelled_at.isoformat(),
                'new_status': pre_order.status,
                'message': 'Pré-ordem cancelada com sucesso. Nenhuma ordem foi criada.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao cancelar pré-ordem {pre_order_id}: {str(e)}")
            raise e

    
    # =========================================================================
    # Métodos com Cache e Paginação (Task 22)
    # =========================================================================
    
    @staticmethod
    def get_active_pre_orders_paginated(
        user_id: int,
        user_role: str,
        page: int = 1,
        per_page: int = 20,
        status_filter: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Retorna pré-ordens ativas de um usuário com paginação e cache
        
        Args:
            user_id: ID do usuário
            user_role: 'cliente' ou 'prestador'
            page: Número da página (padrão: 1)
            per_page: Itens por página (padrão: 20)
            status_filter: Filtro de status opcional
            use_cache: Se deve usar cache (padrão: True)
            
        Returns:
            dict: Pré-ordens paginadas com metadados
            
        Requirements: Performance considerations (Task 22)
        """
        # Validar role
        if user_role not in ['cliente', 'prestador']:
            raise ValueError("user_role deve ser 'cliente' ou 'prestador'")
        
        # Gerar chave de cache incluindo filtros
        cache_key_suffix = f"{status_filter}" if status_filter else "all"
        
        # Tentar obter do cache (apenas primeira página sem filtro)
        if use_cache and page == 1 and not status_filter:
            cached_data = PreOrderCacheService.get_active_pre_orders(user_id, user_role)
            if cached_data is not None:
                logger.debug(f"Cache HIT: pré-ordens ativas do usuário {user_id}")
                return cached_data
        
        # Construir query base
        if user_role == 'cliente':
            query = PreOrder.query.filter_by(client_id=user_id)
        else:
            query = PreOrder.query.filter_by(provider_id=user_id)
        
        # Aplicar filtro de status se fornecido
        if status_filter:
            query = query.filter_by(status=status_filter)
        else:
            # Por padrão, excluir convertidas, canceladas e expiradas
            query = query.filter(
                PreOrder.status.notin_([
                    PreOrderStatus.CONVERTIDA.value,
                    PreOrderStatus.CANCELADA.value,
                    PreOrderStatus.EXPIRADA.value
                ])
            )
        
        # Ordenar por data de atualização (mais recentes primeiro)
        query = query.order_by(PreOrder.updated_at.desc())
        
        # Aplicar paginação
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serializar pré-ordens
        pre_orders = []
        for pre_order in pagination.items:
            pre_orders.append({
                'id': pre_order.id,
                'title': pre_order.title,
                'current_value': float(pre_order.current_value),
                'original_value': float(pre_order.original_value),
                'status': pre_order.status,
                'status_display': pre_order.status_display,
                'status_color_class': pre_order.status_color_class,
                'client_id': pre_order.client_id,
                'provider_id': pre_order.provider_id,
                'client_name': pre_order.client.nome if pre_order.client else None,
                'provider_name': pre_order.provider.nome if pre_order.provider else None,
                'has_active_proposal': pre_order.has_active_proposal,
                'client_accepted_terms': pre_order.client_accepted_terms,
                'provider_accepted_terms': pre_order.provider_accepted_terms,
                'pending_acceptance_from': pre_order.pending_acceptance_from,
                'created_at': pre_order.created_at.isoformat(),
                'updated_at': pre_order.updated_at.isoformat(),
                'expires_at': pre_order.expires_at.isoformat(),
                'days_until_expiration': pre_order.days_until_expiration,
                'is_near_expiration': pre_order.is_near_expiration
            })
        
        result = {
            'success': True,
            'pre_orders': pre_orders,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_page': pagination.prev_num,
                'next_page': pagination.next_num
            },
            'user_id': user_id,
            'user_role': user_role,
            'status_filter': status_filter
        }
        
        # Armazenar no cache (apenas primeira página sem filtro)
        if use_cache and page == 1 and not status_filter:
            PreOrderCacheService.set_active_pre_orders(user_id, user_role, result)
            logger.debug(f"Cache SET: pré-ordens ativas do usuário {user_id}")
        
        return result
    
    @staticmethod
    def get_pre_order_history_paginated(
        pre_order_id: int,
        user_id: int,
        page: int = 1,
        per_page: int = 50,
        use_cache: bool = True
    ) -> Dict:
        """
        Retorna histórico de uma pré-ordem com paginação e cache
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário solicitante (para validação)
            page: Número da página (padrão: 1)
            per_page: Itens por página (padrão: 50)
            use_cache: Se deve usar cache (padrão: True)
            
        Returns:
            dict: Histórico paginado com metadados
            
        Raises:
            ValueError: Se a pré-ordem não for encontrada
            PermissionError: Se o usuário não tiver permissão
            
        Requirements: Performance considerations (Task 22)
        """
        # Validar pré-ordem e permissão
        pre_order = PreOrder.query.get(pre_order_id)
        if not pre_order:
            raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
        
        if user_id not in [pre_order.client_id, pre_order.provider_id]:
            raise PermissionError("Você não tem permissão para visualizar o histórico desta pré-ordem")
        
        # Tentar obter do cache (apenas primeira página)
        if use_cache and page == 1:
            cached_history = PreOrderCacheService.get_pre_order_history(pre_order_id)
            if cached_history is not None:
                logger.debug(f"Cache HIT: histórico da pré-ordem {pre_order_id}")
                return cached_history
        
        # Consultar histórico com paginação
        pagination = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order_id
        ).order_by(
            PreOrderHistory.created_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serializar histórico
        history_items = []
        for item in pagination.items:
            history_items.append({
                'id': item.id,
                'event_type': item.event_type,
                'event_type_display': item.event_type_display,
                'actor_id': item.actor_id,
                'actor_name': item.actor.nome if item.actor else 'Sistema',
                'description': item.description,
                'event_data': item.event_data,
                'created_at': item.created_at.isoformat()
            })
        
        result = {
            'success': True,
            'pre_order_id': pre_order_id,
            'history': history_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_page': pagination.prev_num,
                'next_page': pagination.next_num
            }
        }
        
        # Armazenar no cache (apenas primeira página)
        if use_cache and page == 1:
            PreOrderCacheService.set_pre_order_history(pre_order_id, result)
            logger.debug(f"Cache SET: histórico da pré-ordem {pre_order_id}")
        
        return result
    
    @staticmethod
    def invalidate_pre_order_cache(pre_order_id: int, client_id: int, provider_id: int):
        """
        Invalida todo o cache relacionado a uma pré-ordem
        
        Deve ser chamado sempre que a pré-ordem for modificada.
        
        Args:
            pre_order_id: ID da pré-ordem
            client_id: ID do cliente
            provider_id: ID do prestador
            
        Requirements: Performance considerations (Task 22)
        """
        PreOrderCacheService.invalidate_pre_order_for_users(
            pre_order_id=pre_order_id,
            client_id=client_id,
            provider_id=provider_id
        )
        logger.info(f"Cache invalidado para pré-ordem {pre_order_id}")
