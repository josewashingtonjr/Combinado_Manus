#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Invite, Proposal, Wallet
from services.wallet_service import WalletService
from services.balance_validator import BalanceValidator, BalanceStatus
from services.invite_state_manager import InviteStateManager, InviteState
from services.notification_service import NotificationService
from services.security_validator import SecurityValidator
from services.proposal_audit_service import ProposalAuditService
from services.error_handling_middleware import (
    handle_proposal_errors, 
    handle_concurrent_access, 
    validate_data_integrity
)
from services.atomic_transaction_manager import (
    atomic_financial_operation,
    execute_with_retry,
    log_financial_operation,
    InsufficientBalanceError,
    ConcurrentOperationError,
    TransactionIntegrityError
)
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
import logging

# Manter BalanceCheck para compatibilidade com código existente
@dataclass
class BalanceCheck:
    """Resultado da verificação de saldo para propostas (compatibilidade)"""
    is_sufficient: bool
    current_balance: Decimal
    required_amount: Decimal
    shortfall: Decimal
    suggested_top_up: Decimal

class ProposalService:
    """Serviço para gerenciar propostas de alteração de convites"""
    
    # Taxa de contestação padrão (agora obtida do BalanceValidator)
    @property
    def CONTESTATION_FEE(self) -> Decimal:
        return BalanceValidator.get_contestation_fee()
    
    # Manter constante estática para compatibilidade
    CONTESTATION_FEE = Decimal('10.0')  # R$ 10,00 por convite (fallback)
    
    @staticmethod
    @handle_proposal_errors('proposal_creation')
    @handle_concurrent_access('invite', timeout=10)
    @validate_data_integrity('invite')
    def create_proposal(invite_id: int, prestador_id: int, proposed_value: Decimal, justification: str = None) -> dict:
        """
        Cria uma nova proposta de alteração para um convite
        
        Validações de segurança implementadas:
        - Autorização: apenas prestador destinatário pode criar propostas
        - Rate limiting: limites por convite, hora e dia
        - Validação de valores: limites mínimos, máximos e percentuais
        - Sanitização: justificativas são sanitizadas contra XSS e injection
        - Estado do convite: deve estar disponível para propostas
        
        Requirements: 1.1, 2.1, 2.2, 5.5, 8.5, 2.4, 1.5
        """
        # Executar validação completa de segurança
        security_result = SecurityValidator.validate_proposal_creation_complete(
            invite_id=invite_id,
            prestador_id=prestador_id,
            proposed_value=proposed_value,
            justification=justification
        )
        
        if not security_result.is_valid:
            logging.warning(f"Validação de segurança falhou - Prestador {prestador_id}, "
                          f"Convite {invite_id}: {security_result.error_message}")
            raise ValueError(security_result.error_message)
        
        # Obter dados sanitizados
        sanitized_justification = security_result.details.get('sanitized_justification')
        
        # Verificar se convite existe (já validado pelo SecurityValidator, mas necessário para lógica)
        invite = Invite.query.get(invite_id)
        if not invite:
            raise ValueError("Convite não encontrado")
        
        # Verificar se convite pode receber proposta usando o gerenciador de estados
        can_create, reason = InviteStateManager.can_create_proposal(invite)
        if not can_create:
            raise ValueError(reason)
        
        with atomic_financial_operation("create_proposal"):
            # Criar a proposta com dados sanitizados
            proposal = Proposal(
                invite_id=invite_id,
                prestador_id=prestador_id,
                original_value=invite.original_value,
                proposed_value=proposed_value,
                justification=sanitized_justification,
                status='pending'
            )
            
            db.session.add(proposal)
            db.session.flush()  # Para obter o ID da proposta
            
            # Atualizar o convite para indicar proposta ativa
            invite.set_active_proposal(proposal)
            
            # Não fazer commit ainda - será feito pela transição de estado
            db.session.flush()
            
            # Transicionar para estado PROPOSTA_ENVIADA
            invite.transition_to(InviteState.PROPOSTA_ENVIADA, prestador_id, 
                               f"Proposta criada: R$ {invite.original_value} -> R$ {proposed_value}")
            
            # Log de auditoria da criação da proposta
            ProposalAuditService.log_proposal_created(
                proposal_id=proposal.id,
                prestador_id=prestador_id,
                reason=sanitized_justification
            )
            
            # Log da ação com informações de segurança
            rate_info = security_result.details.get('rate_limiting_info', {})
            logging.info(f"Proposta criada - Prestador {prestador_id}, Convite {invite_id}, "
                        f"Valor original: {invite.original_value}, "
                        f"Valor proposto: {proposed_value}, "
                        f"Propostas restantes hoje: {rate_info.get('remaining_day', 'N/A')}")
            
            # Notificar o cliente sobre a nova proposta
            notification_result = NotificationService.notify_proposal_created(
                invite_id=invite_id,
                client_id=invite.client_id,
                proposal=proposal
            )
            
            return {
                'success': True,
                'proposal_id': proposal.id,
                'invite_id': invite_id,
                'original_value': float(proposal.original_value),
                'proposed_value': float(proposal.proposed_value),
                'value_difference': float(proposal.value_difference),
                'is_increase': proposal.is_increase,
                'status': proposal.status,
                'message': 'Proposta criada com sucesso. Cliente será notificado.',
                'notification_sent': notification_result.get('success', False)
            }
    
    @staticmethod
    @handle_proposal_errors('proposal_approval')
    @handle_concurrent_access('proposal', timeout=15)
    @validate_data_integrity('proposal')
    def approve_proposal(proposal_id: int, client_id: int, client_response_reason: str = None) -> dict:
        """
        Aprova uma proposta de alteração
        
        Validações de segurança implementadas:
        - Autorização: apenas cliente dono do convite pode aprovar
        - Sanitização: comentários são sanitizados contra XSS e injection
        - Validação de estado: proposta deve estar pendente
        - Verificação de saldo: para aumentos de valor
        
        Requirements: 1.1, 2.1, 2.2, 5.5, 8.5, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.4
        """
        # Executar validação completa de segurança
        security_result = SecurityValidator.validate_proposal_response_complete(
            proposal_id=proposal_id,
            client_id=client_id,
            response_reason=client_response_reason
        )
        
        if not security_result.is_valid:
            logging.warning(f"Validação de segurança falhou na aprovação - Cliente {client_id}, "
                          f"Proposta {proposal_id}: {security_result.error_message}")
            raise ValueError(security_result.error_message)
        
        # Obter dados sanitizados
        sanitized_response_reason = security_result.details.get('sanitized_response_reason')
        
        # Verificar se proposta existe (já validado pelo SecurityValidator, mas necessário para lógica)
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        # Verificar se proposta está pendente
        if not proposal.is_pending:
            raise ValueError(f"Proposta não pode ser aprovada. Status atual: {proposal.status}")
        
        # Verificar saldo se for aumento de valor
        if proposal.is_increase:
            balance_check = ProposalService.check_client_balance_sufficiency(
                client_id, proposal.proposed_value
            )
            if not balance_check.is_sufficient:
                # Notificar sobre saldo insuficiente
                NotificationService.notify_balance_insufficient(
                    client_id=client_id,
                    required_amount=balance_check.required_amount,
                    current_balance=balance_check.current_balance,
                    proposal=proposal
                )
                
                raise InsufficientBalanceError(
                    current_balance=balance_check.current_balance,
                    required_amount=balance_check.required_amount,
                    user_id=client_id
                )
        
        with atomic_financial_operation("approve_proposal"):
            # 1. Aceitar a proposta primeiro (seta effective_value no convite)
            proposal.accept(sanitized_response_reason)
            db.session.flush()
            
            # 2. Garantir que effective_value está setado antes da transição
            if proposal.invite.effective_value is None:
                raise ValueError("Erro interno: effective_value não foi setado após accept()")
            
            # 3. Transicionar para estado PROPOSTA_ACEITA (limpa has_active_proposal)
            proposal.invite.transition_to(InviteState.PROPOSTA_ACEITA, client_id,
                                        f"Proposta aprovada: R$ {proposal.proposed_value}")
            
            # Log de auditoria da aprovação
            ProposalAuditService.log_proposal_approved(
                proposal_id=proposal.id,
                client_id=client_id,
                reason=sanitized_response_reason
            )
            
            # Notificar o prestador sobre a aprovação
            notification_result = NotificationService.notify_proposal_response(
                invite_id=proposal.invite_id,
                prestador_id=proposal.prestador_id,
                status='accepted',
                proposal=proposal,
                client_response_reason=client_response_reason
            )
            
            # Validar que resultado retorna effective_value correto
            effective_value = proposal.invite.effective_value
            if effective_value != proposal.proposed_value:
                logging.error(f"Inconsistência detectada: effective_value ({effective_value}) "
                            f"diferente de proposed_value ({proposal.proposed_value})")
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'invite_id': proposal.invite_id,
                'original_value': float(proposal.original_value),
                'approved_value': float(proposal.proposed_value),
                'effective_value': float(effective_value),
                'status': proposal.status,
                'message': 'Proposta aprovada com sucesso. Prestador pode aceitar o convite.',
                'notification_sent': notification_result.get('success', False)
            }
    
    @staticmethod
    @handle_proposal_errors('proposal_rejection')
    @handle_concurrent_access('proposal', timeout=10)
    @validate_data_integrity('proposal')
    def reject_proposal(proposal_id: int, client_id: int, client_response_reason: str = None) -> dict:
        """
        Rejeita uma proposta de alteração
        
        Validações de segurança implementadas:
        - Autorização: apenas cliente dono do convite pode rejeitar
        - Sanitização: comentários são sanitizados contra XSS e injection
        - Validação de estado: proposta deve estar pendente
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3
        """
        # Executar validação completa de segurança
        security_result = SecurityValidator.validate_proposal_response_complete(
            proposal_id=proposal_id,
            client_id=client_id,
            response_reason=client_response_reason
        )
        
        if not security_result.is_valid:
            logging.warning(f"Validação de segurança falhou na rejeição - Cliente {client_id}, "
                          f"Proposta {proposal_id}: {security_result.error_message}")
            raise ValueError(security_result.error_message)
        
        # Obter dados sanitizados
        sanitized_response_reason = security_result.details.get('sanitized_response_reason')
        
        # Verificar se proposta existe (já validado pelo SecurityValidator, mas necessário para lógica)
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        # Verificar se proposta está pendente
        if not proposal.is_pending:
            raise ValueError(f"Proposta não pode ser rejeitada. Status atual: {proposal.status}")
        
        with atomic_financial_operation("reject_proposal"):
            # 1. Rejeitar a proposta primeiro (atualiza status e responded_at)
            proposal.reject(sanitized_response_reason)
            db.session.flush()
            
            # 2. Transicionar para estado PROPOSTA_REJEITADA (limpa campos de proposta)
            proposal.invite.transition_to(InviteState.PROPOSTA_REJEITADA, client_id,
                                        f"Proposta rejeitada: {client_response_reason or 'Sem motivo especificado'}")
            db.session.flush()
            
            # 3. Transicionar de volta para PENDENTE (estado final)
            proposal.invite.transition_to(InviteState.PENDENTE, client_id,
                                        "Convite retornou ao estado original")
            
            # 4. Log de auditoria da rejeição
            ProposalAuditService.log_proposal_rejected(
                proposal_id=proposal.id,
                client_id=client_id,
                reason=sanitized_response_reason
            )
            
            # 5. Notificar o prestador sobre a rejeição
            notification_result = NotificationService.notify_proposal_response(
                invite_id=proposal.invite_id,
                prestador_id=proposal.prestador_id,
                status='rejected',
                proposal=proposal,
                client_response_reason=client_response_reason
            )
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'invite_id': proposal.invite_id,
                'original_value': float(proposal.original_value),
                'rejected_value': float(proposal.proposed_value),
                'status': proposal.status,
                'rejection_reason': client_response_reason,
                'message': 'Proposta rejeitada. Convite retornou ao estado original.',
                'notification_sent': notification_result.get('success', False)
            }
    
    @staticmethod
    @handle_proposal_errors('proposal_cancellation')
    @handle_concurrent_access('proposal', timeout=10)
    @validate_data_integrity('proposal')
    def cancel_proposal(proposal_id: int, prestador_id: int) -> dict:
        """
        Cancela uma proposta de alteração (ação do prestador)
        
        Validações:
        - Proposta deve existir e estar pendente
        - Prestador deve ser o criador da proposta
        - Retornar convite ao estado original
        
        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        # Verificar se proposta existe
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        # Verificar se proposta está pendente
        if not proposal.is_pending:
            raise ValueError(f"Proposta não pode ser cancelada. Status atual: {proposal.status}")
        
        # Verificar se prestador é o criador da proposta
        if proposal.prestador_id != prestador_id:
            raise ValueError("Apenas o prestador criador da proposta pode cancelá-la")
        
        with atomic_financial_operation("cancel_proposal"):
            # 1. Cancelar a proposta primeiro (atualiza status e responded_at)
            proposal.cancel()
            db.session.flush()
            
            # 2. Transicionar diretamente para PENDENTE (limpa campos de proposta)
            proposal.invite.transition_to(InviteState.PENDENTE, prestador_id,
                                        "Proposta cancelada pelo prestador")
            
            # 3. Log de auditoria do cancelamento
            ProposalAuditService.log_proposal_cancelled(
                proposal_id=proposal.id,
                prestador_id=prestador_id,
                reason="Cancelado pelo prestador"
            )
            
            # 4. Notificar o cliente sobre o cancelamento
            notification_result = NotificationService.notify_proposal_cancelled(
                invite_id=proposal.invite_id,
                client_id=proposal.invite.client_id,
                proposal=proposal
            )
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'invite_id': proposal.invite_id,
                'original_value': float(proposal.original_value),
                'cancelled_value': float(proposal.proposed_value),
                'status': proposal.status,
                'message': 'Proposta cancelada. Convite retornou ao estado original.',
                'notification_sent': notification_result.get('success', False)
            }
    
    @staticmethod
    def check_client_balance_sufficiency(client_id: int, proposed_value: Decimal) -> BalanceCheck:
        """
        Verifica se o cliente tem saldo suficiente para aceitar uma proposta
        
        Agora usa o BalanceValidator para lógica centralizada de verificação de saldo
        
        Requirements: 1.1, 2.1, 2.2, 5.5
        """
        # Usar o BalanceValidator para validação completa
        balance_status = BalanceValidator.validate_proposal_balance(client_id, proposed_value)
        
        # Converter BalanceStatus para BalanceCheck para compatibilidade
        return BalanceCheck(
            is_sufficient=balance_status.is_sufficient,
            current_balance=balance_status.current_balance,
            required_amount=balance_status.required_amount,
            shortfall=balance_status.shortfall,
            suggested_top_up=balance_status.suggested_top_up
        )
    
    @staticmethod
    def get_proposal_by_id(proposal_id: int) -> dict:
        """Retorna informações detalhadas de uma proposta"""
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        return {
            'id': proposal.id,
            'invite_id': proposal.invite_id,
            'prestador_id': proposal.prestador_id,
            'prestador_name': proposal.prestador.nome if proposal.prestador else 'Prestador não encontrado',
            'original_value': float(proposal.original_value),
            'proposed_value': float(proposal.proposed_value),
            'value_difference': float(proposal.value_difference),
            'is_increase': proposal.is_increase,
            'is_decrease': proposal.is_decrease,
            'justification': proposal.justification,
            'status': proposal.status,
            'created_at': proposal.created_at,
            'responded_at': proposal.responded_at,
            'client_response_reason': proposal.client_response_reason,
            'invite_info': {
                'service_title': proposal.invite.service_title,
                'service_description': proposal.invite.service_description,
                'delivery_date': proposal.invite.delivery_date,
                'client_name': proposal.invite.client.nome if proposal.invite.client else 'Cliente não encontrado'
            }
        }
    
    @staticmethod
    def get_proposals_for_invite(invite_id: int) -> list:
        """Retorna todas as propostas de um convite (histórico)"""
        proposals = Proposal.query.filter_by(invite_id=invite_id).order_by(Proposal.created_at.desc()).all()
        
        return [{
            'id': p.id,
            'prestador_id': p.prestador_id,
            'prestador_name': p.prestador.nome if p.prestador else 'Prestador não encontrado',
            'original_value': float(p.original_value),
            'proposed_value': float(p.proposed_value),
            'value_difference': float(p.value_difference),
            'is_increase': p.is_increase,
            'justification': p.justification,
            'status': p.status,
            'created_at': p.created_at,
            'responded_at': p.responded_at,
            'client_response_reason': p.client_response_reason
        } for p in proposals]
    
    @staticmethod
    def get_proposals_by_prestador(prestador_id: int, status: str = None) -> list:
        """Retorna propostas criadas por um prestador"""
        query = Proposal.query.filter_by(prestador_id=prestador_id)
        
        if status:
            query = query.filter_by(status=status)
        
        proposals = query.order_by(Proposal.created_at.desc()).all()
        
        return [{
            'id': p.id,
            'invite_id': p.invite_id,
            'service_title': p.invite.service_title if p.invite else 'Convite não encontrado',
            'client_name': p.invite.client.nome if p.invite and p.invite.client else 'Cliente não encontrado',
            'original_value': float(p.original_value),
            'proposed_value': float(p.proposed_value),
            'value_difference': float(p.value_difference),
            'is_increase': p.is_increase,
            'justification': p.justification,
            'status': p.status,
            'created_at': p.created_at,
            'responded_at': p.responded_at,
            'client_response_reason': p.client_response_reason
        } for p in proposals]
    
    @staticmethod
    def get_proposals_for_client(client_id: int, status: str = None) -> list:
        """Retorna propostas recebidas por um cliente"""
        # Buscar propostas através dos convites do cliente
        from sqlalchemy import and_
        
        query = db.session.query(Proposal).join(Invite).filter(Invite.client_id == client_id)
        
        if status:
            query = query.filter(Proposal.status == status)
        
        proposals = query.order_by(Proposal.created_at.desc()).all()
        
        return [{
            'id': p.id,
            'invite_id': p.invite_id,
            'service_title': p.invite.service_title if p.invite else 'Convite não encontrado',
            'prestador_name': p.prestador.nome if p.prestador else 'Prestador não encontrado',
            'prestador_phone': p.invite.invited_phone if p.invite else None,
            'original_value': float(p.original_value),
            'proposed_value': float(p.proposed_value),
            'value_difference': float(p.value_difference),
            'is_increase': p.is_increase,
            'justification': p.justification,
            'status': p.status,
            'created_at': p.created_at,
            'responded_at': p.responded_at,
            'client_response_reason': p.client_response_reason
        } for p in proposals]
    
    @staticmethod
    def get_proposal_statistics(client_id: int = None, prestador_id: int = None) -> dict:
        """
        Retorna estatísticas de propostas
        
        Se client_id for fornecido, retorna estatísticas das propostas recebidas pelo cliente
        Se prestador_id for fornecido, retorna estatísticas das propostas criadas pelo prestador
        Senão, retorna estatísticas gerais do sistema
        """
        if client_id:
            # Estatísticas das propostas recebidas pelo cliente
            from sqlalchemy import and_
            proposals = db.session.query(Proposal).join(Invite).filter(Invite.client_id == client_id).all()
        elif prestador_id:
            # Estatísticas das propostas criadas pelo prestador
            proposals = Proposal.query.filter_by(prestador_id=prestador_id).all()
        else:
            # Estatísticas gerais do sistema
            proposals = Proposal.query.all()
        
        total_proposals = len(proposals)
        
        if total_proposals == 0:
            return {
                'total_proposals': 0,
                'by_status': {},
                'approval_rate': 0,
                'average_original_value': 0,
                'average_proposed_value': 0,
                'average_increase': 0,
                'increases_count': 0,
                'decreases_count': 0
            }
        
        # Contar por status
        status_count = {}
        total_original_value = Decimal('0.00')
        total_proposed_value = Decimal('0.00')
        increases_count = 0
        decreases_count = 0
        
        for proposal in proposals:
            status = proposal.status
            status_count[status] = status_count.get(status, 0) + 1
            
            total_original_value += proposal.original_value
            total_proposed_value += proposal.proposed_value
            
            if proposal.is_increase:
                increases_count += 1
            elif proposal.is_decrease:
                decreases_count += 1
        
        # Calcular taxa de aprovação
        approved = status_count.get('accepted', 0)
        responded = approved + status_count.get('rejected', 0)
        approval_rate = (approved / responded * 100) if responded > 0 else 0
        
        # Calcular aumento médio (apenas para propostas de aumento)
        increase_proposals = [p for p in proposals if p.is_increase]
        average_increase = 0
        if increase_proposals:
            total_increase = sum(p.value_difference for p in increase_proposals)
            average_increase = float(total_increase / len(increase_proposals))
        
        return {
            'total_proposals': total_proposals,
            'by_status': status_count,
            'approval_rate': approval_rate,
            'average_original_value': float(total_original_value / total_proposals),
            'average_proposed_value': float(total_proposed_value / total_proposals),
            'average_increase': average_increase,
            'increases_count': increases_count,
            'decreases_count': decreases_count,
            'pending_proposals': status_count.get('pending', 0)
        }
    
    @staticmethod
    @handle_proposal_errors('balance_addition_and_approval')
    @handle_concurrent_access('proposal', timeout=30)
    @validate_data_integrity('wallet')
    def add_balance_and_approve_proposal(
        proposal_id: int, 
        client_id: int, 
        amount_to_add: Decimal,
        payment_method: str = 'pix',
        description: str = None,
        client_response_reason: str = None
    ) -> dict:
        """
        Fluxo integrado: adicionar saldo e aprovar proposta automaticamente
        
        Este método executa uma operação atômica que:
        1. Verifica se a proposta é válida e o cliente tem autorização
        2. Adiciona o saldo especificado à carteira do cliente
        3. Verifica se o novo saldo é suficiente para a proposta
        4. Aprova a proposta automaticamente
        5. Registra todas as transações para auditoria
        
        Requirements: 3.4, 4.1, 4.3, 4.4, 4.5
        """
        with atomic_financial_operation("add_balance_and_approve_proposal"):
                # 1. Validar proposta
                proposal = Proposal.query.get(proposal_id)
                if not proposal:
                    raise ValueError("Proposta não encontrada")
                
                if proposal.status != 'pending':
                    raise ValueError("Proposta não está mais pendente")
                
                # Verificar se cliente é o dono do convite
                invite = Invite.query.get(proposal.invite_id)
                if not invite or invite.client_id != client_id:
                    raise ValueError("Você não tem permissão para esta proposta")
                
                # 2. Verificar saldo atual
                balance_status = BalanceValidator.validate_proposal_balance(
                    client_id=client_id,
                    proposed_value=proposal.proposed_value
                )
                
                # 3. Validar que o valor a adicionar é suficiente
                new_balance = balance_status.current_balance + amount_to_add
                if new_balance < balance_status.required_amount:
                    shortfall_after_addition = balance_status.required_amount - new_balance
                    raise ValueError(f"Valor insuficiente. Após adicionar R$ {amount_to_add:.2f}, "
                                   f"ainda faltarão R$ {shortfall_after_addition:.2f}")
                
                # 4. Adicionar saldo à carteira do cliente
                # Usar o sistema de solicitação de tokens existente para manter auditoria
                from services.cliente_service import ClienteService
                
                # Criar solicitação de tokens aprovada automaticamente
                token_request_result = ClienteService.create_token_request(
                    user_id=client_id,
                    amount=amount_to_add,
                    payment_method=payment_method,
                    description=f"Adição automática para aprovação de proposta #{proposal_id}" + 
                               (f" - {description}" if description else ""),
                    receipt_filename=None,  # Será processado pelo admin posteriormente
                    auto_approve=True  # Flag especial para aprovação automática
                )
                
                # Adicionar saldo diretamente (simulando aprovação do admin)
                balance_result = WalletService.admin_sell_tokens_to_user(
                    user_id=client_id,
                    amount=amount_to_add,
                    description=f"Compra automática para proposta #{proposal_id}"
                )
                
                # 5. Verificar novamente o saldo após adição
                updated_balance_status = BalanceValidator.validate_proposal_balance(
                    client_id=client_id,
                    proposed_value=proposal.proposed_value
                )
                
                if not updated_balance_status.is_sufficient:
                    raise ValueError("Erro interno: saldo ainda insuficiente após adição")
                
                # 6. Aprovar a proposta
                proposal.status = 'accepted'
                proposal.responded_at = datetime.utcnow()
                proposal.client_response_reason = client_response_reason
                
                # Atualizar estado do convite
                invite.has_active_proposal = False
                invite.current_proposal_id = None
                invite.effective_value = proposal.proposed_value
                
                # Atualizar estado usando InviteStateManager
                invite.transition_to(InviteState.PROPOSTA_ACEITA, client_id, "Proposta aprovada e saldo adicionado")
                
                # 7. Registrar log de auditoria
                from services.atomic_transaction_manager import log_financial_operation
                log_financial_operation(
                    operation_type="add_balance_and_approve_proposal",
                    user_id=client_id,
                    amount=amount_to_add,
                    details={
                        'proposal_id': proposal_id,
                        'invite_id': invite.id,
                        'original_value': float(proposal.original_value),
                        'approved_value': float(proposal.proposed_value),
                        'payment_method': payment_method,
                        'description': description,
                        'client_response_reason': client_response_reason,
                        'balance_before': float(balance_status.current_balance),
                        'balance_after': float(updated_balance_status.current_balance),
                        'token_request_id': token_request_result.get('request_id')
                    }
                )
                
                return {
                    'success': True,
                    'message': f'Saldo de R$ {amount_to_add:.2f} adicionado e proposta aprovada com sucesso!',
                    'proposal_id': proposal_id,
                    'invite_id': invite.id,
                    'original_value': float(proposal.original_value),
                    'approved_value': float(proposal.proposed_value),
                    'value_difference': float(proposal.value_difference),
                    'amount_added': float(amount_to_add),
                    'new_balance': float(updated_balance_status.current_balance),
                    'payment_method': payment_method,
                    'token_request_id': token_request_result.get('request_id'),
                    'balance_transaction_id': balance_result.get('user_transaction_id'),
                    'next_step': 'O prestador agora pode aceitar o convite com o novo valor'
                }
    
    @staticmethod
    def simulate_balance_addition(proposal_id: int, client_id: int, amount_to_add: Decimal) -> dict:
        """
        Simula a adição de saldo para verificar se será suficiente
        
        Usado para validação antes de executar o fluxo completo
        
        Requirements: 4.2, 4.3
        """
        # Validar proposta
        proposal = Proposal.query.get(proposal_id)
        if not proposal:
            raise ValueError("Proposta não encontrada")
        
        # Verificar autorização
        invite = Invite.query.get(proposal.invite_id)
        if not invite or invite.client_id != client_id:
            raise ValueError("Você não tem permissão para esta proposta")
        
        # Verificar saldo atual
        balance_status = BalanceValidator.validate_proposal_balance(
            client_id=client_id,
            proposed_value=proposal.proposed_value
        )
        
        # Simular novo saldo
        simulated_balance = balance_status.current_balance + amount_to_add
        will_be_sufficient = simulated_balance >= balance_status.required_amount
        
        remaining_shortfall = Decimal('0')
        if not will_be_sufficient:
            remaining_shortfall = balance_status.required_amount - simulated_balance
        
        return {
            'success': True,
            'proposal_id': proposal_id,
            'current_balance': float(balance_status.current_balance),
            'required_amount': float(balance_status.required_amount),
            'amount_to_add': float(amount_to_add),
            'simulated_balance': float(simulated_balance),
            'will_be_sufficient': will_be_sufficient,
            'remaining_shortfall': float(remaining_shortfall),
            'recommendation': 'sufficient' if will_be_sufficient else f'add_more_{remaining_shortfall:.2f}'
        }