#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderProposalService - Serviço para gerenciamento de propostas de pré-ordens

Este serviço gerencia o ciclo de vida completo das propostas de alteração em pré-ordens,
incluindo criação, aceitação, rejeição e validações.

Requirements: 2.1-2.5, 3.1-3.5, 4.1-4.5, 19.1-19.3, 19.5
"""

from models import (
    db, PreOrder, PreOrderStatus, PreOrderProposal, ProposalStatus,
    PreOrderHistory, User
)
from services.pre_order_state_manager import PreOrderStateManager
from services.notification_service import NotificationService
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict
from decimal import Decimal
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class PreOrderProposalService:
    """
    Serviço para gerenciamento de propostas de alteração em pré-ordens
    
    Responsável por:
    - Criar propostas de alteração com validações
    - Aceitar propostas atualizando valores da pré-ordem
    - Rejeitar propostas mantendo valores anteriores
    - Validar justificativas e mudanças propostas
    - Detectar propostas extremas
    - Integrar com NotificationService e PreOrderStateManager
    - Registrar todas as ações no histórico
    """
    
    # Limites para propostas extremas
    EXTREME_INCREASE_THRESHOLD = 100  # >100% de aumento
    EXTREME_DECREASE_THRESHOLD = -50  # >50% de redução
    MIN_JUSTIFICATION_LENGTH = 50  # Caracteres mínimos
    EXTREME_JUSTIFICATION_MIN_LENGTH = 100  # Para propostas extremas
    
    @staticmethod
    def create_proposal(
        pre_order_id: int,
        user_id: int,
        proposed_value: Optional[Decimal] = None,
        proposed_delivery_date: Optional[datetime] = None,
        proposed_description: Optional[str] = None,
        justification: str = None
    ) -> Dict:
        """
        Cria uma proposta de alteração para uma pré-ordem
        
        Valida que:
        - Usuário tem permissão (é cliente ou prestador)
        - Pré-ordem está em estado válido
        - Pelo menos um campo foi alterado
        - Justificativa tem tamanho mínimo
        - Propostas extremas têm justificativa detalhada
        
        Args:
            pre_order_id: ID da pré-ordem
            user_id: ID do usuário que está propondo
            proposed_value: Novo valor proposto (opcional)
            proposed_delivery_date: Nova data de entrega proposta (opcional)
            proposed_description: Nova descrição proposta (opcional)
            justification: Justificativa da proposta (obrigatório)
            
        Returns:
            dict: Resultado da criação com detalhes da proposta
            
        Raises:
            ValueError: Se validações falharem
            PermissionError: Se usuário não tiver permissão
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 19.1, 19.2, 19.3, 19.5
        """
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Requirement 2.1: Validar permissão (apenas cliente ou prestador)
            if user_id not in [pre_order.client_id, pre_order.provider_id]:
                raise PermissionError("Você não tem permissão para propor alterações nesta pré-ordem")
            
            # Verificar se pré-ordem está em estado válido para propostas
            if pre_order.status not in [PreOrderStatus.EM_NEGOCIACAO.value, PreOrderStatus.AGUARDANDO_RESPOSTA.value]:
                return {
                    'success': False,
                    'error': f'Não é possível criar proposta no estado {pre_order.status_display}',
                    'current_status': pre_order.status
                }
            
            # Verificar se já existe proposta pendente
            if pre_order.has_active_proposal:
                active_proposal = pre_order.get_active_proposal()
                if active_proposal and active_proposal.is_pending:
                    return {
                        'success': False,
                        'error': 'Já existe uma proposta pendente. Aguarde resposta antes de criar nova proposta.',
                        'active_proposal_id': active_proposal.id
                    }
            
            # Requirement 2.4: Validar justificativa obrigatória
            if not justification or len(justification.strip()) < PreOrderProposalService.MIN_JUSTIFICATION_LENGTH:
                raise ValueError(
                    f"Justificativa é obrigatória e deve ter pelo menos "
                    f"{PreOrderProposalService.MIN_JUSTIFICATION_LENGTH} caracteres"
                )
            
            # Validar que pelo menos um campo foi alterado
            has_changes = False
            changes_description = []
            
            if proposed_value is not None and proposed_value != pre_order.current_value:
                has_changes = True
                diff = proposed_value - pre_order.current_value
                changes_description.append(
                    f"Valor: R$ {pre_order.current_value:.2f} → R$ {proposed_value:.2f} "
                    f"({'+'if diff > 0 else ''}{diff:.2f})"
                )
            
            if proposed_delivery_date is not None and proposed_delivery_date != pre_order.delivery_date:
                has_changes = True
                changes_description.append(
                    f"Prazo: {pre_order.delivery_date.strftime('%d/%m/%Y')} → "
                    f"{proposed_delivery_date.strftime('%d/%m/%Y')}"
                )
            
            if proposed_description is not None and proposed_description.strip() != pre_order.description.strip():
                has_changes = True
                changes_description.append("Descrição alterada")
            
            if not has_changes:
                raise ValueError("Pelo menos um campo deve ser alterado (valor, prazo ou descrição)")
            
            # Requirements 19.1, 19.2, 19.3: Detectar propostas extremas
            is_extreme = False
            extreme_reason = None
            
            if proposed_value is not None:
                current_value = pre_order.current_value
                if current_value > 0:
                    change_percent = ((proposed_value - current_value) / current_value) * 100
                    
                    if change_percent > PreOrderProposalService.EXTREME_INCREASE_THRESHOLD:
                        is_extreme = True
                        extreme_reason = f"Aumento de {change_percent:.1f}% (>{PreOrderProposalService.EXTREME_INCREASE_THRESHOLD}%)"
                    elif change_percent < PreOrderProposalService.EXTREME_DECREASE_THRESHOLD:
                        is_extreme = True
                        extreme_reason = f"Redução de {abs(change_percent):.1f}% (>{abs(PreOrderProposalService.EXTREME_DECREASE_THRESHOLD)}%)"
            
            # Requirement 19.5: Exigir justificativa detalhada para propostas extremas
            if is_extreme and len(justification.strip()) < PreOrderProposalService.EXTREME_JUSTIFICATION_MIN_LENGTH:
                raise ValueError(
                    f"Proposta extrema detectada ({extreme_reason}). "
                    f"Justificativa deve ter pelo menos {PreOrderProposalService.EXTREME_JUSTIFICATION_MIN_LENGTH} caracteres. "
                    f"Explique detalhadamente o motivo desta alteração significativa."
                )
            
            # Determinar papel do usuário
            is_client = (user_id == pre_order.client_id)
            user_role = 'cliente' if is_client else 'prestador'
            other_party_id = pre_order.provider_id if is_client else pre_order.client_id
            
            # Criar proposta
            proposal = PreOrderProposal(
                pre_order_id=pre_order_id,
                proposed_by=user_id,
                proposed_value=proposed_value,
                proposed_delivery_date=proposed_delivery_date,
                proposed_description=proposed_description,
                justification=justification.strip(),
                status=ProposalStatus.PENDENTE.value
            )
            
            db.session.add(proposal)
            db.session.flush()  # Para obter o ID da proposta
            
            # Atualizar pré-ordem
            pre_order.has_active_proposal = True
            pre_order.active_proposal_id = proposal.id
            pre_order.updated_at = datetime.utcnow()
            
            # Requirement 2.5: Resetar aceitações quando há nova proposta
            PreOrderStateManager.reset_acceptances(pre_order_id)
            
            # Requirement 2.5: Transicionar para AGUARDANDO_RESPOSTA
            PreOrderStateManager.transition_to(
                pre_order_id=pre_order_id,
                new_status=PreOrderStatus.AGUARDANDO_RESPOSTA,
                actor_id=user_id,
                reason=f'Proposta enviada por {user_role}: {", ".join(changes_description)}'
            )
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type='proposal_sent',
                actor_id=user_id,
                description=f'{user_role.title()} enviou proposta de alteração',
                event_data={
                    'proposal_id': proposal.id,
                    'user_role': user_role,
                    'proposed_value': float(proposed_value) if proposed_value else None,
                    'proposed_delivery_date': proposed_delivery_date.isoformat() if proposed_delivery_date else None,
                    'proposed_description': proposed_description,
                    'justification': justification,
                    'is_extreme': is_extreme,
                    'extreme_reason': extreme_reason,
                    'changes': changes_description
                }
            )
            db.session.add(history_entry)
            
            db.session.commit()
            
            # Requirement 2.2: Notificar a outra parte
            PreOrderProposalService._notify_proposal_created(
                pre_order=pre_order,
                proposal=proposal,
                proposer_id=user_id,
                proposer_role=user_role,
                recipient_id=other_party_id,
                is_extreme=is_extreme
            )
            
            logger.info(
                f"Proposta {proposal.id} criada para pré-ordem {pre_order_id} por {user_role} {user_id}. "
                f"Alterações: {', '.join(changes_description)}. Extrema: {is_extreme}"
            )
            
            return {
                'success': True,
                'proposal_id': proposal.id,
                'pre_order_id': pre_order_id,
                'proposed_by': user_id,
                'user_role': user_role,
                'proposed_value': float(proposed_value) if proposed_value else None,
                'proposed_delivery_date': proposed_delivery_date.isoformat() if proposed_delivery_date else None,
                'proposed_description': proposed_description,
                'justification': justification,
                'is_extreme': is_extreme,
                'extreme_reason': extreme_reason,
                'changes': changes_description,
                'new_status': pre_order.status,
                'message': f'Proposta enviada com sucesso! Aguardando resposta da outra parte.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao criar proposta para pré-ordem {pre_order_id}: {str(e)}")
            raise e
    
    @staticmethod
    def accept_proposal(proposal_id: int, user_id: int) -> Dict:
        """
        Aceita uma proposta, atualizando os valores da pré-ordem
        
        Quando uma proposta é aceita:
        - Valores da pré-ordem são atualizados
        - Status da proposta muda para ACEITA
        - Aceitações são resetadas (ambas as partes precisam aceitar novos termos)
        - Estado volta para EM_NEGOCIACAO
        - Histórico é registrado
        - Notificações são enviadas
        
        Args:
            proposal_id: ID da proposta
            user_id: ID do usuário que está aceitando
            
        Returns:
            dict: Resultado da aceitação
            
        Raises:
            ValueError: Se proposta não for encontrada ou não puder ser aceita
            PermissionError: Se usuário não tiver permissão
            
        Requirements: 3.4, 4.1, 4.2, 4.3, 4.5
        """
        try:
            # Buscar proposta
            proposal = PreOrderProposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            pre_order = proposal.pre_order
            if not pre_order:
                raise ValueError(f"Pré-ordem associada à proposta {proposal_id} não encontrada")
            
            # Validar permissão: apenas a outra parte pode aceitar
            proposer_id = proposal.proposed_by
            if user_id == proposer_id:
                raise PermissionError("Você não pode aceitar sua própria proposta")
            
            if user_id not in [pre_order.client_id, pre_order.provider_id]:
                raise PermissionError("Você não tem permissão para aceitar esta proposta")
            
            # Verificar se proposta está pendente
            if not proposal.is_pending:
                return {
                    'success': False,
                    'error': f'Proposta já foi respondida: {proposal.status_display}',
                    'current_status': proposal.status
                }
            
            # Determinar papéis
            is_client = (user_id == pre_order.client_id)
            user_role = 'cliente' if is_client else 'prestador'
            proposer_role = 'prestador' if is_client else 'cliente'
            
            # Guardar valores anteriores para histórico
            old_value = pre_order.current_value
            old_delivery_date = pre_order.delivery_date
            old_description = pre_order.description
            
            # Requirement 4.2: Atualizar valores da pré-ordem
            changes_applied = []
            
            if proposal.proposed_value is not None:
                pre_order.current_value = proposal.proposed_value
                changes_applied.append(
                    f"Valor: R$ {old_value:.2f} → R$ {proposal.proposed_value:.2f}"
                )
            
            if proposal.proposed_delivery_date is not None:
                pre_order.delivery_date = proposal.proposed_delivery_date
                changes_applied.append(
                    f"Prazo: {old_delivery_date.strftime('%d/%m/%Y')} → "
                    f"{proposal.proposed_delivery_date.strftime('%d/%m/%Y')}"
                )
            
            if proposal.proposed_description is not None:
                pre_order.description = proposal.proposed_description
                changes_applied.append("Descrição atualizada")
            
            pre_order.updated_at = datetime.utcnow()
            
            # Atualizar status da proposta
            proposal.status = ProposalStatus.ACEITA.value
            proposal.responded_at = datetime.utcnow()
            
            # Limpar proposta ativa
            pre_order.has_active_proposal = False
            pre_order.active_proposal_id = None
            
            # Requirement 4.5: Resetar aceitações (ambas as partes precisam aceitar novos termos)
            PreOrderStateManager.reset_acceptances(pre_order_id=pre_order.id)
            
            # Requirement 4.5: Transicionar de volta para EM_NEGOCIACAO
            PreOrderStateManager.transition_to(
                pre_order_id=pre_order.id,
                new_status=PreOrderStatus.EM_NEGOCIACAO,
                actor_id=user_id,
                reason=f'Proposta aceita por {user_role}. Termos atualizados, aguardando aceitação mútua.'
            )
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='proposal_accepted',
                actor_id=user_id,
                description=f'{user_role.title()} aceitou proposta de {proposer_role}',
                event_data={
                    'proposal_id': proposal.id,
                    'user_role': user_role,
                    'proposer_role': proposer_role,
                    'old_value': float(old_value),
                    'new_value': float(pre_order.current_value),
                    'changes_applied': changes_applied
                }
            )
            db.session.add(history_entry)
            
            db.session.commit()
            
            # Notificar o autor da proposta
            PreOrderProposalService._notify_proposal_accepted(
                pre_order=pre_order,
                proposal=proposal,
                acceptor_id=user_id,
                acceptor_role=user_role,
                proposer_id=proposer_id,
                proposer_role=proposer_role
            )
            
            logger.info(
                f"Proposta {proposal_id} aceita por {user_role} {user_id}. "
                f"Pré-ordem {pre_order.id} atualizada. Alterações: {', '.join(changes_applied)}"
            )
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'pre_order_id': pre_order.id,
                'accepted_by': user_id,
                'user_role': user_role,
                'proposer_role': proposer_role,
                'changes_applied': changes_applied,
                'new_value': float(pre_order.current_value),
                'new_status': pre_order.status,
                'message': (
                    f'Proposta aceita! Os termos foram atualizados. '
                    f'Ambas as partes precisam aceitar os novos termos para prosseguir.'
                )
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao aceitar proposta {proposal_id}: {str(e)}")
            raise e
    
    @staticmethod
    def reject_proposal(proposal_id: int, user_id: int, rejection_reason: Optional[str] = None) -> Dict:
        """
        Rejeita uma proposta, mantendo os valores anteriores da pré-ordem
        
        Quando uma proposta é rejeitada:
        - Valores da pré-ordem NÃO são alterados
        - Status da proposta muda para REJEITADA
        - Estado volta para EM_NEGOCIACAO
        - Proposta ativa é limpa
        - Histórico é registrado
        - Notificações são enviadas
        
        Args:
            proposal_id: ID da proposta
            user_id: ID do usuário que está rejeitando
            rejection_reason: Motivo da rejeição (opcional)
            
        Returns:
            dict: Resultado da rejeição
            
        Raises:
            ValueError: Se proposta não for encontrada ou não puder ser rejeitada
            PermissionError: Se usuário não tiver permissão
            
        Requirements: 4.1, 4.4, 4.5
        """
        try:
            # Buscar proposta
            proposal = PreOrderProposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            pre_order = proposal.pre_order
            if not pre_order:
                raise ValueError(f"Pré-ordem associada à proposta {proposal_id} não encontrada")
            
            # Validar permissão: apenas a outra parte pode rejeitar
            proposer_id = proposal.proposed_by
            if user_id == proposer_id:
                raise PermissionError("Você não pode rejeitar sua própria proposta. Use cancelar ao invés disso.")
            
            if user_id not in [pre_order.client_id, pre_order.provider_id]:
                raise PermissionError("Você não tem permissão para rejeitar esta proposta")
            
            # Verificar se proposta está pendente
            if not proposal.is_pending:
                return {
                    'success': False,
                    'error': f'Proposta já foi respondida: {proposal.status_display}',
                    'current_status': proposal.status
                }
            
            # Determinar papéis
            is_client = (user_id == pre_order.client_id)
            user_role = 'cliente' if is_client else 'prestador'
            proposer_role = 'prestador' if is_client else 'cliente'
            
            # Requirement 4.4: Atualizar status da proposta (valores da pré-ordem permanecem)
            proposal.status = ProposalStatus.REJEITADA.value
            proposal.responded_at = datetime.utcnow()
            
            # Limpar proposta ativa
            pre_order.has_active_proposal = False
            pre_order.active_proposal_id = None
            pre_order.updated_at = datetime.utcnow()
            
            # Requirement 4.5: Transicionar de volta para EM_NEGOCIACAO
            PreOrderStateManager.transition_to(
                pre_order_id=pre_order.id,
                new_status=PreOrderStatus.EM_NEGOCIACAO,
                actor_id=user_id,
                reason=f'Proposta rejeitada por {user_role}. Valores anteriores mantidos.'
            )
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order.id,
                event_type='proposal_rejected',
                actor_id=user_id,
                description=f'{user_role.title()} rejeitou proposta de {proposer_role}',
                event_data={
                    'proposal_id': proposal.id,
                    'user_role': user_role,
                    'proposer_role': proposer_role,
                    'rejection_reason': rejection_reason,
                    'current_value_maintained': float(pre_order.current_value)
                }
            )
            db.session.add(history_entry)
            
            db.session.commit()
            
            # Notificar o autor da proposta
            PreOrderProposalService._notify_proposal_rejected(
                pre_order=pre_order,
                proposal=proposal,
                rejector_id=user_id,
                rejector_role=user_role,
                proposer_id=proposer_id,
                proposer_role=proposer_role,
                rejection_reason=rejection_reason
            )
            
            logger.info(
                f"Proposta {proposal_id} rejeitada por {user_role} {user_id}. "
                f"Pré-ordem {pre_order.id} mantém valores anteriores. "
                f"Motivo: {rejection_reason or 'Não informado'}"
            )
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'pre_order_id': pre_order.id,
                'rejected_by': user_id,
                'user_role': user_role,
                'proposer_role': proposer_role,
                'rejection_reason': rejection_reason,
                'current_value': float(pre_order.current_value),
                'new_status': pre_order.status,
                'message': (
                    f'Proposta rejeitada. Os valores anteriores foram mantidos. '
                    f'Você pode continuar negociando ou aceitar os termos atuais.'
                )
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao rejeitar proposta {proposal_id}: {str(e)}")
            raise e
    
    # ==================== MÉTODOS AUXILIARES DE NOTIFICAÇÃO ====================
    
    @staticmethod
    def _notify_proposal_created(
        pre_order: PreOrder,
        proposal: PreOrderProposal,
        proposer_id: int,
        proposer_role: str,
        recipient_id: int,
        is_extreme: bool
    ):
        """
        Notifica a outra parte sobre nova proposta
        
        Requirements: 2.2, 11.2
        """
        try:
            proposer = User.query.get(proposer_id)
            proposer_name = proposer.nome if proposer else proposer_role.title()
            
            recipient = User.query.get(recipient_id)
            recipient_name = recipient.nome if recipient else "Usuário"
            
            # Construir mensagem
            changes = []
            if proposal.proposed_value:
                diff = proposal.proposed_value - pre_order.current_value
                changes.append(
                    f"Valor: R$ {pre_order.current_value:.2f} → R$ {proposal.proposed_value:.2f} "
                    f"({'+'if diff > 0 else ''}{diff:.2f})"
                )
            if proposal.proposed_delivery_date:
                changes.append(
                    f"Prazo: {proposal.proposed_delivery_date.strftime('%d/%m/%Y')}"
                )
            if proposal.proposed_description:
                changes.append("Descrição alterada")
            
            extreme_warning = " ⚠️ PROPOSTA EXTREMA" if is_extreme else ""
            
            message = (
                f"📝 Nova proposta recebida{extreme_warning}! "
                f"{proposer_name} propôs alterações: {', '.join(changes)}. "
                f"Justificativa: {proposal.justification[:100]}... "
                f"Acesse a pré-ordem para aceitar ou rejeitar."
            )
            
            # TODO: Integrar com NotificationService quando métodos de pré-ordem forem adicionados
            logger.info(
                f"Notificação de proposta criada - Pré-ordem: {pre_order.id}, "
                f"Proposta: {proposal.id}, Destinatário: {recipient_id}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de proposta {proposal.id}: {str(e)}")
    
    @staticmethod
    def _notify_proposal_accepted(
        pre_order: PreOrder,
        proposal: PreOrderProposal,
        acceptor_id: int,
        acceptor_role: str,
        proposer_id: int,
        proposer_role: str
    ):
        """
        Notifica o autor da proposta sobre aceitação
        
        Requirements: 11.3
        """
        try:
            acceptor = User.query.get(acceptor_id)
            acceptor_name = acceptor.nome if acceptor else acceptor_role.title()
            
            message = (
                f"✅ Proposta aceita! "
                f"{acceptor_name} aceitou sua proposta para '{pre_order.title}'. "
                f"Os termos foram atualizados. Agora ambas as partes precisam aceitar os novos termos."
            )
            
            # TODO: Integrar com NotificationService quando métodos de pré-ordem forem adicionados
            logger.info(
                f"Notificação de proposta aceita - Pré-ordem: {pre_order.id}, "
                f"Proposta: {proposal.id}, Autor: {proposer_id}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar aceitação de proposta {proposal.id}: {str(e)}")
    
    @staticmethod
    def _notify_proposal_rejected(
        pre_order: PreOrder,
        proposal: PreOrderProposal,
        rejector_id: int,
        rejector_role: str,
        proposer_id: int,
        proposer_role: str,
        rejection_reason: Optional[str]
    ):
        """
        Notifica o autor da proposta sobre rejeição
        
        Requirements: 11.3
        """
        try:
            rejector = User.query.get(rejector_id)
            rejector_name = rejector.nome if rejector else rejector_role.title()
            
            reason_text = f" Motivo: {rejection_reason}" if rejection_reason else ""
            
            message = (
                f"❌ Proposta rejeitada. "
                f"{rejector_name} rejeitou sua proposta para '{pre_order.title}'.{reason_text} "
                f"Os valores anteriores foram mantidos. Você pode criar uma nova proposta."
            )
            
            # TODO: Integrar com NotificationService quando métodos de pré-ordem forem adicionados
            logger.info(
                f"Notificação de proposta rejeitada - Pré-ordem: {pre_order.id}, "
                f"Proposta: {proposal.id}, Autor: {proposer_id}"
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar rejeição de proposta {proposal.id}: {str(e)}")
