#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Auditoria e Logging
Registra todas as operações críticas do sistema para rastreabilidade
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

# Configurar logger específico para auditoria
audit_logger = logging.getLogger('sistema_combinado.audit')
audit_logger.setLevel(logging.INFO)

# Handler para arquivo de auditoria separado
audit_handler = logging.FileHandler('logs/audit.log', encoding='utf-8')
audit_handler.setLevel(logging.INFO)
audit_formatter = logging.Formatter(
    '%(asctime)s - AUDIT - %(message)s'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)


class AuditService:
    """Serviço para registro de auditoria de operações críticas"""
    
    @staticmethod
    def _generate_audit_id() -> str:
        """Gera um ID único para rastreabilidade"""
        return str(uuid.uuid4())
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serializa valores para JSON (converte Decimal, datetime, etc)"""
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif hasattr(value, '__dict__'):
            return str(value)
        return value
    
    @staticmethod
    def _format_audit_entry(
        operation: str,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int],
        details: Dict[str, Any],
        audit_id: str
    ) -> str:
        """Formata entrada de auditoria em JSON estruturado"""
        entry = {
            'audit_id': audit_id,
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'details': {k: AuditService._serialize_value(v) for k, v in details.items()}
        }
        return json.dumps(entry, ensure_ascii=False)
    
    @staticmethod
    def log_order_created(
        order_id: int,
        client_id: int,
        provider_id: int,
        value: Decimal,
        invite_id: int,
        escrow_details: Dict[str, Any]
    ) -> str:
        """Registra criação de ordem"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'client_id': client_id,
            'provider_id': provider_id,
            'value': value,
            'invite_id': invite_id,
            'client_escrow_amount': escrow_details.get('client_escrow_amount'),
            'provider_escrow_amount': escrow_details.get('provider_escrow_amount'),
            'platform_fee_percentage': escrow_details.get('platform_fee_percentage'),
            'contestation_fee': escrow_details.get('contestation_fee'),
            'cancellation_fee_percentage': escrow_details.get('cancellation_fee_percentage')
        }
        
        entry = AuditService._format_audit_entry(
            operation='ORDER_CREATED',
            entity_type='Order',
            entity_id=order_id,
            user_id=client_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_status_change(
        order_id: int,
        user_id: int,
        old_status: str,
        new_status: str,
        reason: Optional[str] = None
    ) -> str:
        """Registra mudança de status de ordem"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason
        }
        
        entry = AuditService._format_audit_entry(
            operation='STATUS_CHANGED',
            entity_type='Order',
            entity_id=order_id,
            user_id=user_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_service_completed(
        order_id: int,
        provider_id: int,
        completed_at: datetime,
        confirmation_deadline: datetime
    ) -> str:
        """Registra marcação de serviço como concluído"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'provider_id': provider_id,
            'completed_at': completed_at,
            'confirmation_deadline': confirmation_deadline,
            'hours_to_confirm': 36
        }
        
        entry = AuditService._format_audit_entry(
            operation='SERVICE_COMPLETED',
            entity_type='Order',
            entity_id=order_id,
            user_id=provider_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_order_confirmed(
        order_id: int,
        client_id: int,
        is_auto_confirmed: bool,
        payment_details: Dict[str, Any]
    ) -> str:
        """Registra confirmação de ordem (manual ou automática)"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'client_id': client_id,
            'confirmation_type': 'automatic' if is_auto_confirmed else 'manual',
            'service_value': payment_details.get('service_value'),
            'platform_fee': payment_details.get('platform_fee'),
            'provider_net_amount': payment_details.get('provider_net_amount'),
            'contestation_fee_returned_client': payment_details.get('contestation_fee_returned_client'),
            'contestation_fee_returned_provider': payment_details.get('contestation_fee_returned_provider')
        }
        
        entry = AuditService._format_audit_entry(
            operation='ORDER_CONFIRMED_AUTO' if is_auto_confirmed else 'ORDER_CONFIRMED_MANUAL',
            entity_type='Order',
            entity_id=order_id,
            user_id=client_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_order_cancelled(
        order_id: int,
        cancelled_by_id: int,
        cancelled_by_role: str,
        reason: str,
        payment_details: Dict[str, Any]
    ) -> str:
        """Registra cancelamento de ordem"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'cancelled_by_id': cancelled_by_id,
            'cancelled_by_role': cancelled_by_role,
            'reason': reason,
            'cancellation_fee': payment_details.get('cancellation_fee'),
            'platform_share': payment_details.get('platform_share'),
            'injured_party_share': payment_details.get('injured_party_share'),
            'injured_party': payment_details.get('injured_party'),
            'amount_returned': payment_details.get('amount_returned_to_cancelling_party')
        }
        
        entry = AuditService._format_audit_entry(
            operation='ORDER_CANCELLED',
            entity_type='Order',
            entity_id=order_id,
            user_id=cancelled_by_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_dispute_opened(
        order_id: int,
        client_id: int,
        reason: str,
        evidence_count: int
    ) -> str:
        """Registra abertura de contestação"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'client_id': client_id,
            'reason': reason[:200],  # Limitar tamanho do motivo no log
            'evidence_files_count': evidence_count
        }
        
        entry = AuditService._format_audit_entry(
            operation='DISPUTE_OPENED',
            entity_type='Order',
            entity_id=order_id,
            user_id=client_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_dispute_response(
        order_id: int,
        provider_id: int,
        response: str,
        evidence_count: int
    ) -> str:
        """Registra resposta do prestador à contestação"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'provider_id': provider_id,
            'response': response[:200],  # Limitar tamanho da resposta no log
            'evidence_files_count': evidence_count
        }
        
        entry = AuditService._format_audit_entry(
            operation='DISPUTE_RESPONSE',
            entity_type='Order',
            entity_id=order_id,
            user_id=provider_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_dispute_resolved(
        order_id: int,
        admin_id: int,
        winner: str,
        admin_notes: Optional[str],
        payment_details: Dict[str, Any]
    ) -> str:
        """Registra resolução de contestação"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'admin_id': admin_id,
            'winner': winner,
            'admin_notes': admin_notes[:200] if admin_notes else None,
            'payment_details': payment_details
        }
        
        entry = AuditService._format_audit_entry(
            operation='DISPUTE_RESOLVED',
            entity_type='Order',
            entity_id=order_id,
            user_id=admin_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_financial_transaction(
        transaction_type: str,
        from_user_id: int,
        to_user_id: int,
        amount: Decimal,
        order_id: int,
        description: str,
        transaction_id: Optional[str] = None
    ) -> str:
        """Registra transação financeira"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'transaction_type': transaction_type,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
            'amount': amount,
            'order_id': order_id,
            'description': description,
            'transaction_id': transaction_id
        }
        
        entry = AuditService._format_audit_entry(
            operation='FINANCIAL_TRANSACTION',
            entity_type='Transaction',
            entity_id=order_id,
            user_id=from_user_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.info(entry)
        return audit_id
    
    @staticmethod
    def log_error(
        operation: str,
        entity_type: str,
        entity_id: Optional[int],
        user_id: Optional[int],
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Registra erro em operação"""
        audit_id = AuditService._generate_audit_id()
        
        details = {
            'error_message': error_message,
            'error_details': error_details or {}
        }
        
        entry = AuditService._format_audit_entry(
            operation=f'ERROR_{operation}',
            entity_type=entity_type,
            entity_id=entity_id or 0,
            user_id=user_id,
            details=details,
            audit_id=audit_id
        )
        
        audit_logger.error(entry)
        return audit_id
