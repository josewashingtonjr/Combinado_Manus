#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Recuperação de Erros e Tratamento de Casos Extremos

Este módulo implementa tratamento robusto para ações simultâneas, recovery para
estados inconsistentes, validação de integridade de dados e rollback automático
em falhas de transação para o sistema de propostas.

Requirements: 3.3, 4.4, 7.4
"""

from models import db, Invite, Proposal, Wallet, User
from services.atomic_transaction_manager import (
    AtomicTransactionManager, 
    FinancialIntegrityError,
    InsufficientBalanceError,
    ConcurrentOperationError,
    TransactionIntegrityError,
    atomic_financial_operation,
    execute_with_retry,
    log_financial_operation
)
from services.invite_state_manager import InviteStateManager, InviteState
from services.balance_validator import BalanceValidator
from services.notification_service import NotificationService
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import time

# Configurar logging
logger = logging.getLogger(__name__)

class RecoveryAction(Enum):
    """Ações de recuperação disponíveis"""
    ROLLBACK_PROPOSAL = "rollback_proposal"
    RESET_INVITE_STATE = "reset_invite_state"
    RECONCILE_BALANCE = "reconcile_balance"
    CLEAR_ORPHANED_PROPOSALS = "clear_orphaned_proposals"
    RESTORE_CONSISTENCY = "restore_consistency"
    NOTIFY_USERS = "notify_users"

@dataclass
class InconsistencyReport:
    """Relatório de inconsistência detectada"""
    entity_type: str
    entity_id: int
    inconsistency_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    suggested_actions: List[RecoveryAction]
    details: Dict
    detected_at: datetime

@dataclass
class RecoveryResult:
    """Resultado de operação de recuperação"""
    success: bool
    action_taken: RecoveryAction
    entity_id: int
    message: str
    details: Dict
    timestamp: datetime

class ErrorRecoveryService:
    """
    Serviço para tratamento de erros e recuperação de estados inconsistentes
    
    Funcionalidades:
    - Detecção de inconsistências de dados
    - Recuperação automática de estados inválidos
    - Tratamento de concorrência e race conditions
    - Rollback inteligente de operações falhadas
    - Validação de integridade contínua
    """
    
    # Configurações de timeout e retry
    LOCK_TIMEOUT = 30  # segundos
    MAX_RECOVERY_ATTEMPTS = 3
    CONSISTENCY_CHECK_INTERVAL = 300  # 5 minutos
    
    @staticmethod
    def handle_concurrent_proposal_creation(invite_id: int, prestador_id: int, 
                                          proposed_value: Decimal, justification: str) -> Dict:
        """
        Trata criação simultânea de propostas com proteção contra race conditions
        
        Requirements: 3.3 - Tratamento para ações simultâneas (concorrência)
        """
        def _create_proposal_operation():
            # Usar lock otimista no convite
            invite = db.session.query(Invite).filter(
                Invite.id == invite_id
            ).with_for_update().first()
            
            if not invite:
                raise ValueError("Convite não encontrado")
            
            # Verificar se já existe proposta ativa (double-check com lock)
            if invite.has_active_proposal:
                active_proposal = invite.get_active_proposal()
                if active_proposal and active_proposal.status == 'pending':
                    raise ConcurrentOperationError(
                        f"Já existe uma proposta pendente para este convite (ID: {active_proposal.id})"
                    )
            
            # Verificar se prestador pode criar proposta
            can_create, reason = InviteStateManager.can_create_proposal(invite)
            if not can_create:
                raise ValueError(reason)
            
            # Criar proposta com proteção contra duplicação
            existing_pending = Proposal.query.filter(
                and_(
                    Proposal.invite_id == invite_id,
                    Proposal.prestador_id == prestador_id,
                    Proposal.status == 'pending'
                )
            ).first()
            
            if existing_pending:
                raise ConcurrentOperationError(
                    f"Você já tem uma proposta pendente para este convite (ID: {existing_pending.id})"
                )
            
            # Criar nova proposta
            proposal = Proposal(
                invite_id=invite_id,
                prestador_id=prestador_id,
                original_value=invite.original_value,
                proposed_value=proposed_value,
                justification=justification,
                status='pending'
            )
            
            db.session.add(proposal)
            db.session.flush()
            
            # Atualizar convite
            invite.set_active_proposal(proposal)
            
            # Transicionar para estado PROPOSTA_ENVIADA
            invite.transition_to(InviteState.PROPOSTA_ENVIADA, prestador_id, 
                               f"Proposta criada: R$ {invite.original_value} -> R$ {proposed_value}")
            
            return {
                'success': True,
                'proposal_id': proposal.id,
                'invite_id': invite_id,
                'original_value': float(invite.original_value),
                'proposed_value': float(proposed_value),
                'value_difference': float(proposed_value - invite.original_value),
                'is_increase': proposed_value > invite.original_value,
                'status': proposal.status,
                'message': 'Proposta criada com sucesso. Cliente será notificado.',
                'notification_sent': False
            }
        
        try:
            return execute_with_retry(
                _create_proposal_operation,
                operation_name="concurrent_proposal_creation"
            )
        except ConcurrentOperationError as e:
            logger.warning(f"Operação concorrente detectada na criação de proposta: {e}")
            return {
                'success': False,
                'error': 'concurrent_operation',
                'message': 'Outra proposta está sendo processada. Tente novamente em alguns segundos.',
                'retry_after': 2
            }
        except Exception as e:
            logger.error(f"Erro na criação concorrente de proposta: {e}")
            return {
                'success': False,
                'error': 'creation_failed',
                'message': f'Erro ao criar proposta: {str(e)}'
            }
    
    @staticmethod
    def handle_concurrent_proposal_response(proposal_id: int, client_id: int, 
                                          action: str, response_reason: str = None) -> Dict:
        """
        Trata resposta simultânea a propostas (aprovação/rejeição concorrente)
        
        Requirements: 3.3 - Tratamento para ações simultâneas (concorrência)
        """
        def _respond_proposal_operation():
            # Lock otimista na proposta
            proposal = db.session.query(Proposal).filter(
                Proposal.id == proposal_id
            ).with_for_update().first()
            
            if not proposal:
                raise ValueError("Proposta não encontrada")
            
            # Verificar se proposta ainda está pendente
            if proposal.status != 'pending':
                raise ConcurrentOperationError(
                    f"Proposta já foi respondida. Status atual: {proposal.status}"
                )
            
            # Verificar autorização
            invite = proposal.invite
            if invite.client_id != client_id:
                raise ValueError("Você não tem permissão para responder esta proposta")
            
            # Executar ação
            if action == 'approve':
                # Verificar saldo se for aumento
                if proposal.is_increase:
                    balance_status = BalanceValidator.validate_proposal_balance(
                        client_id, proposal.proposed_value
                    )
                    if not balance_status.is_sufficient:
                        raise InsufficientBalanceError(
                            current_balance=balance_status.current_balance,
                            required_amount=balance_status.required_amount,
                            user_id=client_id
                        )
                
                proposal.accept(response_reason)
                invite.transition_to(InviteState.PROPOSTA_ACEITA, client_id,
                                   f"Proposta aprovada: R$ {proposal.proposed_value}")
                
            elif action == 'reject':
                proposal.reject(response_reason)
                invite.transition_to(InviteState.PROPOSTA_REJEITADA, client_id,
                                   f"Proposta rejeitada: {response_reason or 'Sem motivo'}")
            else:
                raise ValueError(f"Ação inválida: {action}")
            
            return {
                'proposal_id': proposal_id,
                'action': action,
                'status': proposal.status,
                'message': f'Proposta {action}d com sucesso'
            }
        
        try:
            return execute_with_retry(
                _respond_proposal_operation,
                operation_name=f"concurrent_proposal_{action}",
                max_retries=ErrorRecoveryService.MAX_RECOVERY_ATTEMPTS
            )
        except ConcurrentOperationError as e:
            logger.warning(f"Resposta concorrente detectada: {e}")
            return {
                'success': False,
                'error': 'concurrent_response',
                'message': 'Proposta já foi respondida por outra operação.',
                'retry_after': 1
            }
        except InsufficientBalanceError as e:
            return {
                'success': False,
                'error': 'insufficient_balance',
                'message': f'Saldo insuficiente: {e.details["current_balance"]:.2f} disponível, {e.details["required_amount"]:.2f} necessário',
                'balance_info': e.details
            }
        except Exception as e:
            logger.error(f"Erro na resposta concorrente de proposta: {e}")
            return {
                'success': False,
                'error': 'response_failed',
                'message': f'Erro ao responder proposta: {str(e)}'
            }
    
    @staticmethod
    def detect_data_inconsistencies() -> List[InconsistencyReport]:
        """
        Detecta inconsistências de dados no sistema de propostas
        
        Requirements: 4.4 - Criar validação de integridade de dados
        """
        inconsistencies = []
        
        try:
            # 1. Convites com proposta ativa mas sem proposal_id
            orphaned_active_flags = db.session.query(Invite).filter(
                and_(
                    Invite.has_active_proposal == True,
                    Invite.current_proposal_id.is_(None)
                )
            ).all()
            
            for invite in orphaned_active_flags:
                inconsistencies.append(InconsistencyReport(
                    entity_type="invite",
                    entity_id=invite.id,
                    inconsistency_type="orphaned_active_flag",
                    description=f"Convite {invite.id} marcado com proposta ativa mas sem proposal_id",
                    severity="medium",
                    suggested_actions=[RecoveryAction.RESET_INVITE_STATE],
                    details={'invite_id': invite.id, 'has_active_proposal': True, 'current_proposal_id': None},
                    detected_at=datetime.utcnow()
                ))
            
            # 2. Propostas pendentes sem convite correspondente marcado como ativo
            unlinked_proposals = db.session.query(Proposal).join(Invite).filter(
                and_(
                    Proposal.status == 'pending',
                    or_(
                        Invite.has_active_proposal == False,
                        Invite.current_proposal_id != Proposal.id
                    )
                )
            ).all()
            
            for proposal in unlinked_proposals:
                inconsistencies.append(InconsistencyReport(
                    entity_type="proposal",
                    entity_id=proposal.id,
                    inconsistency_type="unlinked_proposal",
                    description=f"Proposta {proposal.id} pendente mas convite não está marcado corretamente",
                    severity="high",
                    suggested_actions=[RecoveryAction.RESTORE_CONSISTENCY],
                    details={
                        'proposal_id': proposal.id,
                        'invite_id': proposal.invite_id,
                        'proposal_status': proposal.status,
                        'invite_has_active': proposal.invite.has_active_proposal,
                        'invite_proposal_id': proposal.invite.current_proposal_id
                    },
                    detected_at=datetime.utcnow()
                ))
            
            # 3. Múltiplas propostas pendentes para o mesmo convite
            duplicate_proposals = db.session.query(
                Proposal.invite_id,
                func.count(Proposal.id).label('count')
            ).filter(
                Proposal.status == 'pending'
            ).group_by(
                Proposal.invite_id
            ).having(
                func.count(Proposal.id) > 1
            ).all()
            
            for invite_id, count in duplicate_proposals:
                inconsistencies.append(InconsistencyReport(
                    entity_type="invite",
                    entity_id=invite_id,
                    inconsistency_type="multiple_pending_proposals",
                    description=f"Convite {invite_id} tem {count} propostas pendentes simultâneas",
                    severity="critical",
                    suggested_actions=[RecoveryAction.CLEAR_ORPHANED_PROPOSALS],
                    details={'invite_id': invite_id, 'pending_count': count},
                    detected_at=datetime.utcnow()
                ))
            
            # 4. Convites com effective_value diferente da proposta aceita
            value_mismatches = db.session.query(Invite).join(Proposal).filter(
                and_(
                    Invite.current_proposal_id == Proposal.id,
                    Proposal.status == 'accepted',
                    Invite.effective_value != Proposal.proposed_value
                )
            ).all()
            
            for invite in value_mismatches:
                proposal = invite.get_active_proposal()
                inconsistencies.append(InconsistencyReport(
                    entity_type="invite",
                    entity_id=invite.id,
                    inconsistency_type="value_mismatch",
                    description=f"Convite {invite.id} com effective_value inconsistente com proposta aceita",
                    severity="high",
                    suggested_actions=[RecoveryAction.RESTORE_CONSISTENCY],
                    details={
                        'invite_id': invite.id,
                        'effective_value': float(invite.effective_value) if invite.effective_value else None,
                        'proposal_value': float(proposal.proposed_value) if proposal else None,
                        'proposal_id': proposal.id if proposal else None
                    },
                    detected_at=datetime.utcnow()
                ))
            
            # 5. Propostas antigas sem resposta (possível timeout)
            old_proposals = db.session.query(Proposal).filter(
                and_(
                    Proposal.status == 'pending',
                    Proposal.created_at < datetime.utcnow() - timedelta(days=7)
                )
            ).all()
            
            for proposal in old_proposals:
                inconsistencies.append(InconsistencyReport(
                    entity_type="proposal",
                    entity_id=proposal.id,
                    inconsistency_type="stale_proposal",
                    description=f"Proposta {proposal.id} pendente há mais de 7 dias",
                    severity="low",
                    suggested_actions=[RecoveryAction.NOTIFY_USERS],
                    details={
                        'proposal_id': proposal.id,
                        'created_at': proposal.created_at.isoformat(),
                        'days_pending': (datetime.utcnow() - proposal.created_at).days
                    },
                    detected_at=datetime.utcnow()
                ))
            
            logger.info(f"Verificação de integridade concluída: {len(inconsistencies)} inconsistências detectadas")
            return inconsistencies
            
        except Exception as e:
            logger.error(f"Erro na detecção de inconsistências: {e}")
            return []
    
    @staticmethod
    def recover_from_inconsistency(inconsistency: InconsistencyReport) -> RecoveryResult:
        """
        Executa recuperação automática de inconsistência detectada
        
        Requirements: 4.4 - Adicionar recovery para estados inconsistentes
        """
        try:
            with atomic_financial_operation(f"recovery_{inconsistency.inconsistency_type}"):
                
                if inconsistency.inconsistency_type == "orphaned_active_flag":
                    return ErrorRecoveryService._recover_orphaned_active_flag(inconsistency)
                
                elif inconsistency.inconsistency_type == "unlinked_proposal":
                    return ErrorRecoveryService._recover_unlinked_proposal(inconsistency)
                
                elif inconsistency.inconsistency_type == "multiple_pending_proposals":
                    return ErrorRecoveryService._recover_multiple_pending_proposals(inconsistency)
                
                elif inconsistency.inconsistency_type == "value_mismatch":
                    return ErrorRecoveryService._recover_value_mismatch(inconsistency)
                
                elif inconsistency.inconsistency_type == "stale_proposal":
                    return ErrorRecoveryService._recover_stale_proposal(inconsistency)
                
                else:
                    return RecoveryResult(
                        success=False,
                        action_taken=RecoveryAction.RESTORE_CONSISTENCY,
                        entity_id=inconsistency.entity_id,
                        message=f"Tipo de inconsistência não suportado: {inconsistency.inconsistency_type}",
                        details={},
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            logger.error(f"Erro na recuperação de inconsistência {inconsistency.entity_id}: {e}")
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESTORE_CONSISTENCY,
                entity_id=inconsistency.entity_id,
                message=f"Falha na recuperação: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow()
            )
    
    @staticmethod
    def _recover_orphaned_active_flag(inconsistency: InconsistencyReport) -> RecoveryResult:
        """Recupera convites com flag ativa órfã"""
        invite = Invite.query.get(inconsistency.entity_id)
        if not invite:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESET_INVITE_STATE,
                entity_id=inconsistency.entity_id,
                message="Convite não encontrado",
                details={},
                timestamp=datetime.utcnow()
            )
        
        # Verificar se existe proposta pendente real
        pending_proposal = Proposal.query.filter(
            and_(
                Proposal.invite_id == invite.id,
                Proposal.status == 'pending'
            )
        ).first()
        
        if pending_proposal:
            # Existe proposta pendente - corrigir link
            invite.has_active_proposal = True
            invite.current_proposal_id = pending_proposal.id
            message = f"Link da proposta {pending_proposal.id} restaurado"
        else:
            # Não existe proposta pendente - limpar flag
            invite.has_active_proposal = False
            invite.current_proposal_id = None
            message = "Flag de proposta ativa removida (sem proposta pendente)"
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RESET_INVITE_STATE,
            entity_id=invite.id,
            message=message,
            details={'corrected_state': {'has_active_proposal': invite.has_active_proposal, 'current_proposal_id': invite.current_proposal_id}},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _recover_unlinked_proposal(inconsistency: InconsistencyReport) -> RecoveryResult:
        """Recupera propostas não linkadas corretamente"""
        proposal = Proposal.query.get(inconsistency.entity_id)
        if not proposal or proposal.status != 'pending':
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESTORE_CONSISTENCY,
                entity_id=inconsistency.entity_id,
                message="Proposta não encontrada ou não está mais pendente",
                details={},
                timestamp=datetime.utcnow()
            )
        
        invite = proposal.invite
        
        # Verificar se não há outra proposta pendente mais recente
        newer_proposal = Proposal.query.filter(
            and_(
                Proposal.invite_id == invite.id,
                Proposal.status == 'pending',
                Proposal.id > proposal.id
            )
        ).first()
        
        if newer_proposal:
            # Existe proposta mais recente - cancelar esta
            proposal.status = 'cancelled'
            message = f"Proposta {proposal.id} cancelada (existe proposta mais recente {newer_proposal.id})"
        else:
            # Esta é a proposta válida - corrigir link no convite
            invite.has_active_proposal = True
            invite.current_proposal_id = proposal.id
            message = f"Link da proposta {proposal.id} restaurado no convite {invite.id}"
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RESTORE_CONSISTENCY,
            entity_id=proposal.id,
            message=message,
            details={'proposal_status': proposal.status, 'invite_state': {'has_active_proposal': invite.has_active_proposal, 'current_proposal_id': invite.current_proposal_id}},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _recover_multiple_pending_proposals(inconsistency: InconsistencyReport) -> RecoveryResult:
        """Recupera convites com múltiplas propostas pendentes"""
        invite_id = inconsistency.entity_id
        
        # Buscar todas as propostas pendentes ordenadas por data
        pending_proposals = Proposal.query.filter(
            and_(
                Proposal.invite_id == invite_id,
                Proposal.status == 'pending'
            )
        ).order_by(Proposal.created_at.desc()).all()
        
        if len(pending_proposals) <= 1:
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.CLEAR_ORPHANED_PROPOSALS,
                entity_id=invite_id,
                message="Não há múltiplas propostas pendentes (já resolvido)",
                details={},
                timestamp=datetime.utcnow()
            )
        
        # Manter apenas a mais recente, cancelar as outras
        latest_proposal = pending_proposals[0]
        cancelled_proposals = []
        
        for proposal in pending_proposals[1:]:
            proposal.status = 'cancelled'
            cancelled_proposals.append(proposal.id)
        
        # Atualizar convite para apontar para a proposta mais recente
        invite = Invite.query.get(invite_id)
        invite.has_active_proposal = True
        invite.current_proposal_id = latest_proposal.id
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.CLEAR_ORPHANED_PROPOSALS,
            entity_id=invite_id,
            message=f"Mantida proposta {latest_proposal.id}, canceladas {len(cancelled_proposals)} propostas antigas",
            details={'kept_proposal': latest_proposal.id, 'cancelled_proposals': cancelled_proposals},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _recover_value_mismatch(inconsistency: InconsistencyReport) -> RecoveryResult:
        """Recupera inconsistências de valor efetivo"""
        invite = Invite.query.get(inconsistency.entity_id)
        if not invite:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.RESTORE_CONSISTENCY,
                entity_id=inconsistency.entity_id,
                message="Convite não encontrado",
                details={},
                timestamp=datetime.utcnow()
            )
        
        proposal = invite.get_active_proposal()
        if not proposal or proposal.status != 'accepted':
            # Não há proposta aceita - usar valor original
            invite.effective_value = invite.original_value
            message = f"Valor efetivo restaurado para valor original: R$ {invite.original_value}"
        else:
            # Há proposta aceita - usar valor da proposta
            invite.effective_value = proposal.proposed_value
            message = f"Valor efetivo corrigido para valor da proposta aceita: R$ {proposal.proposed_value}"
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RESTORE_CONSISTENCY,
            entity_id=invite.id,
            message=message,
            details={'corrected_effective_value': float(invite.effective_value)},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _recover_stale_proposal(inconsistency: InconsistencyReport) -> RecoveryResult:
        """Recupera propostas antigas sem resposta"""
        proposal = Proposal.query.get(inconsistency.entity_id)
        if not proposal or proposal.status != 'pending':
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.NOTIFY_USERS,
                entity_id=inconsistency.entity_id,
                message="Proposta não está mais pendente",
                details={},
                timestamp=datetime.utcnow()
            )
        
        # Notificar cliente sobre proposta pendente há muito tempo
        try:
            NotificationService.notify_stale_proposal(
                proposal_id=proposal.id,
                client_id=proposal.invite.client_id,
                days_pending=inconsistency.details.get('days_pending', 0)
            )
            
            return RecoveryResult(
                success=True,
                action_taken=RecoveryAction.NOTIFY_USERS,
                entity_id=proposal.id,
                message=f"Cliente notificado sobre proposta pendente há {inconsistency.details.get('days_pending', 0)} dias",
                details={'notification_sent': True},
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erro ao notificar sobre proposta antiga {proposal.id}: {e}")
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.NOTIFY_USERS,
                entity_id=proposal.id,
                message=f"Falha ao notificar cliente: {str(e)}",
                details={'notification_sent': False, 'error': str(e)},
                timestamp=datetime.utcnow()
            )
    
    @staticmethod
    def rollback_failed_operation(operation_type: str, operation_data: Dict) -> RecoveryResult:
        """
        Executa rollback inteligente de operação falhada
        
        Requirements: 7.4 - Implementar rollback automático em falhas de transação
        """
        try:
            with atomic_financial_operation(f"rollback_{operation_type}"):
                
                if operation_type == "proposal_creation":
                    return ErrorRecoveryService._rollback_proposal_creation(operation_data)
                
                elif operation_type == "proposal_approval":
                    return ErrorRecoveryService._rollback_proposal_approval(operation_data)
                
                elif operation_type == "balance_addition":
                    return ErrorRecoveryService._rollback_balance_addition(operation_data)
                
                elif operation_type == "invite_acceptance":
                    return ErrorRecoveryService._rollback_invite_acceptance(operation_data)
                
                else:
                    return RecoveryResult(
                        success=False,
                        action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
                        entity_id=operation_data.get('entity_id', 0),
                        message=f"Tipo de rollback não suportado: {operation_type}",
                        details={},
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            logger.error(f"Erro no rollback de {operation_type}: {e}")
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
                entity_id=operation_data.get('entity_id', 0),
                message=f"Falha no rollback: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow()
            )
    
    @staticmethod
    def _rollback_proposal_creation(operation_data: Dict) -> RecoveryResult:
        """Rollback de criação de proposta falhada"""
        proposal_id = operation_data.get('proposal_id')
        invite_id = operation_data.get('invite_id')
        
        if proposal_id:
            proposal = Proposal.query.get(proposal_id)
            if proposal:
                db.session.delete(proposal)
        
        if invite_id:
            invite = Invite.query.get(invite_id)
            if invite:
                invite.clear_active_proposal()
                invite.transition_to(InviteState.PENDENTE, None, "Rollback de criação de proposta falhada")
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
            entity_id=proposal_id or invite_id,
            message="Criação de proposta revertida com sucesso",
            details={'proposal_removed': proposal_id is not None, 'invite_reset': invite_id is not None},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _rollback_proposal_approval(operation_data: Dict) -> RecoveryResult:
        """Rollback de aprovação de proposta falhada"""
        proposal_id = operation_data.get('proposal_id')
        
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
                entity_id=proposal_id,
                message="Proposta não encontrada para rollback",
                details={},
                timestamp=datetime.utcnow()
            )
        
        # Reverter status da proposta
        proposal.status = 'pending'
        proposal.responded_at = None
        proposal.client_response_reason = None
        
        # Reverter estado do convite
        invite = proposal.invite
        invite.transition_to(InviteState.PROPOSTA_ENVIADA, None, "Rollback de aprovação falhada")
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
            entity_id=proposal_id,
            message="Aprovação de proposta revertida com sucesso",
            details={'proposal_status': 'pending', 'invite_state': 'proposta_enviada'},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _rollback_balance_addition(operation_data: Dict) -> RecoveryResult:
        """Rollback de adição de saldo falhada"""
        # Este rollback é mais complexo pois envolve transações financeiras
        # Por segurança, apenas registrar o problema para revisão manual
        
        user_id = operation_data.get('user_id')
        amount = operation_data.get('amount')
        transaction_id = operation_data.get('transaction_id')
        
        log_financial_operation(
            operation_type="rollback_balance_addition_required",
            user_id=user_id,
            amount=amount,
            details={
                'transaction_id': transaction_id,
                'reason': 'Rollback automático de adição de saldo falhada',
                'requires_manual_review': True,
                'operation_data': operation_data
            }
        )
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RECONCILE_BALANCE,
            entity_id=user_id,
            message="Rollback de saldo registrado para revisão manual",
            details={'requires_manual_review': True, 'transaction_id': transaction_id},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def _rollback_invite_acceptance(operation_data: Dict) -> RecoveryResult:
        """Rollback de aceitação de convite falhada"""
        invite_id = operation_data.get('invite_id')
        
        invite = Invite.query.get(invite_id)
        if not invite:
            return RecoveryResult(
                success=False,
                action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
                entity_id=invite_id,
                message="Convite não encontrado para rollback",
                details={},
                timestamp=datetime.utcnow()
            )
        
        # Reverter para estado anterior baseado na presença de proposta aceita
        active_proposal = invite.get_active_proposal()
        if active_proposal and active_proposal.status == 'accepted':
            invite.transition_to(InviteState.PROPOSTA_ACEITA, None, "Rollback de aceitação falhada")
            target_state = "proposta_aceita"
        else:
            invite.transition_to(InviteState.PENDENTE, None, "Rollback de aceitação falhada")
            target_state = "pendente"
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.ROLLBACK_PROPOSAL,
            entity_id=invite_id,
            message=f"Aceitação de convite revertida para estado {target_state}",
            details={'reverted_to_state': target_state},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def generate_user_friendly_error_message(error: Exception, context: Dict = None) -> str:
        """
        Gera mensagens de erro claras e acionáveis para usuários
        
        Requirements: 7.4 - Adicionar mensagens de erro claras para usuários
        """
        context = context or {}
        
        if isinstance(error, InsufficientBalanceError):
            current = error.details.get('current_balance', 0)
            required = error.details.get('required_amount', 0)
            deficit = error.details.get('deficit', 0)
            
            return (
                f"Saldo insuficiente para esta operação. "
                f"Você tem R$ {current:.2f} disponível, mas precisa de R$ {required:.2f}. "
                f"Adicione pelo menos R$ {deficit:.2f} à sua carteira para continuar."
            )
        
        elif isinstance(error, ConcurrentOperationError):
            retry_count = error.details.get('retry_count', 0)
            if retry_count > 0:
                return (
                    "Outra operação está sendo processada simultaneamente. "
                    "Aguarde alguns segundos e tente novamente."
                )
            else:
                return (
                    "Esta ação já foi executada por outra operação. "
                    "Atualize a página para ver o estado atual."
                )
        
        elif isinstance(error, TransactionIntegrityError):
            return (
                "Ocorreu um erro interno durante o processamento. "
                "A operação foi cancelada para manter a integridade dos dados. "
                "Tente novamente em alguns minutos."
            )
        
        elif isinstance(error, FinancialIntegrityError):
            if error.error_code == 'NEGATIVE_BALANCE':
                return (
                    "Esta operação resultaria em saldo negativo, o que não é permitido. "
                    "Verifique seu saldo atual e tente novamente."
                )
            elif error.error_code == 'ESCROW_INTEGRITY':
                return (
                    "Erro no processamento de fundos reservados. "
                    "Entre em contato com o suporte para resolver esta situação."
                )
            else:
                return (
                    "Erro de integridade financeira detectado. "
                    "A operação foi cancelada para proteger seus dados."
                )
        
        elif "already exists" in str(error).lower():
            return (
                "Esta ação já foi executada anteriormente. "
                "Atualize a página para ver o estado atual."
            )
        
        elif "not found" in str(error).lower():
            entity_type = context.get('entity_type', 'item')
            return f"O {entity_type} solicitado não foi encontrado ou foi removido."
        
        elif "permission" in str(error).lower() or "unauthorized" in str(error).lower():
            return "Você não tem permissão para executar esta ação."
        
        elif "expired" in str(error).lower():
            return "Este item expirou e não pode mais ser modificado."
        
        elif "timeout" in str(error).lower():
            return (
                "A operação demorou mais que o esperado e foi cancelada. "
                "Tente novamente em alguns minutos."
            )
        
        else:
            # Erro genérico - não expor detalhes técnicos
            return (
                "Ocorreu um erro inesperado. "
                "Tente novamente em alguns minutos ou entre em contato com o suporte se o problema persistir."
            )
    
    @staticmethod
    def run_consistency_check() -> Dict:
        """
        Executa verificação completa de consistência e recuperação automática
        
        Requirements: 4.4 - Validação de integridade de dados contínua
        """
        start_time = datetime.utcnow()
        
        try:
            # Detectar inconsistências
            inconsistencies = ErrorRecoveryService.detect_data_inconsistencies()
            
            # Tentar recuperar automaticamente
            recovery_results = []
            for inconsistency in inconsistencies:
                if inconsistency.severity in ['high', 'critical']:
                    # Recuperar automaticamente apenas problemas críticos
                    result = ErrorRecoveryService.recover_from_inconsistency(inconsistency)
                    recovery_results.append(result)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'success': True,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'inconsistencies_detected': len(inconsistencies),
                'automatic_recoveries': len(recovery_results),
                'successful_recoveries': sum(1 for r in recovery_results if r.success),
                'inconsistencies': [
                    {
                        'type': inc.inconsistency_type,
                        'entity_id': inc.entity_id,
                        'severity': inc.severity,
                        'description': inc.description
                    }
                    for inc in inconsistencies
                ],
                'recovery_results': [
                    {
                        'success': r.success,
                        'action': r.action_taken.value,
                        'entity_id': r.entity_id,
                        'message': r.message
                    }
                    for r in recovery_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação de consistência: {e}")
            return {
                'success': False,
                'error': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.utcnow().isoformat()
            }