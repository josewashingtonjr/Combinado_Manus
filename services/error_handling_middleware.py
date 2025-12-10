#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Middleware de Tratamento de Erros para Sistema de Propostas

Este módulo implementa um middleware que intercepta erros em operações críticas
e aplica tratamento automático, incluindo retry, rollback e mensagens amigáveis.

Requirements: 3.3, 4.4, 7.4
"""

from functools import wraps
from flask import request, jsonify, current_app
from services.error_recovery_service import ErrorRecoveryService
from services.atomic_transaction_manager import (
    FinancialIntegrityError,
    InsufficientBalanceError,
    ConcurrentOperationError,
    TransactionIntegrityError,
    EscrowIntegrityError,
    log_financial_operation
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from datetime import datetime
import logging
import traceback
import json

# Configurar logging
logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    """
    Middleware para tratamento automático de erros em operações de proposta
    
    Funcionalidades:
    - Interceptação automática de erros
    - Aplicação de retry para erros recuperáveis
    - Rollback automático em falhas
    - Geração de mensagens amigáveis
    - Logging detalhado para auditoria
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o middleware com a aplicação Flask"""
        app.teardown_appcontext(self.teardown)
        app.errorhandler(FinancialIntegrityError)(self.handle_financial_error)
        app.errorhandler(SQLAlchemyError)(self.handle_database_error)
        app.errorhandler(Exception)(self.handle_generic_error)
    
    def teardown(self, exception):
        """Cleanup após cada request"""
        if exception:
            logger.error(f"Request teardown com exceção: {exception}")
    
    def handle_financial_error(self, error):
        """Trata erros de integridade financeira"""
        logger.error(f"Erro financeiro: {error}")
        
        # Gerar mensagem amigável
        user_message = ErrorRecoveryService.generate_user_friendly_error_message(
            error, 
            context={'entity_type': 'operação financeira'}
        )
        
        # Log para auditoria
        log_financial_operation(
            operation_type="financial_error",
            user_id=getattr(error, 'user_id', None),
            amount=None,
            details={
                'error_type': error.__class__.__name__,
                'error_code': getattr(error, 'error_code', None),
                'error_message': str(error),
                'error_details': getattr(error, 'details', {}),
                'request_path': request.path if request else None,
                'request_method': request.method if request else None
            }
        )
        
        return jsonify({
            'success': False,
            'error': 'financial_integrity_error',
            'message': user_message,
            'error_code': getattr(error, 'error_code', 'FINANCIAL_ERROR'),
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    def handle_database_error(self, error):
        """Trata erros de banco de dados"""
        logger.error(f"Erro de banco de dados: {error}")
        
        # Determinar se é erro recuperável
        is_recoverable = isinstance(error, (OperationalError, IntegrityError))
        
        if is_recoverable:
            user_message = (
                "Ocorreu um conflito temporário. "
                "Aguarde alguns segundos e tente novamente."
            )
            status_code = 409  # Conflict
        else:
            user_message = (
                "Erro interno do sistema. "
                "Tente novamente em alguns minutos."
            )
            status_code = 500  # Internal Server Error
        
        return jsonify({
            'success': False,
            'error': 'database_error',
            'message': user_message,
            'recoverable': is_recoverable,
            'timestamp': datetime.utcnow().isoformat()
        }), status_code
    
    def handle_generic_error(self, error):
        """Trata erros genéricos não capturados"""
        logger.error(f"Erro genérico: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Não expor detalhes técnicos para o usuário
        user_message = ErrorRecoveryService.generate_user_friendly_error_message(error)
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': user_message,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def handle_proposal_errors(operation_type: str = None):
    """
    Decorator para tratamento automático de erros em operações de proposta
    
    Args:
        operation_type: Tipo da operação para logging e rollback
    
    Usage:
        @handle_proposal_errors('proposal_creation')
        def create_proposal(...):
            # código da função
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = operation_type or func.__name__
            start_time = datetime.utcnow()
            
            # Dados para possível rollback
            rollback_data = {
                'operation_type': operation_name,
                'function_name': func.__name__,
                'args': args,
                'kwargs': kwargs,
                'start_time': start_time.isoformat()
            }
            
            try:
                logger.info(f"Iniciando operação: {operation_name}")
                
                # Executar função original
                result = func(*args, **kwargs)
                
                # Log de sucesso
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Operação {operation_name} concluída com sucesso em {duration:.3f}s")
                
                return result
                
            except InsufficientBalanceError as e:
                logger.warning(f"Saldo insuficiente em {operation_name}: {e}")
                
                return {
                    'success': False,
                    'error': 'insufficient_balance',
                    'message': ErrorRecoveryService.generate_user_friendly_error_message(e),
                    'balance_info': e.details,
                    'suggested_action': 'add_balance'
                }
                
            except ConcurrentOperationError as e:
                logger.warning(f"Operação concorrente em {operation_name}: {e}")
                
                return {
                    'success': False,
                    'error': 'concurrent_operation',
                    'message': ErrorRecoveryService.generate_user_friendly_error_message(e),
                    'retry_after': 2,
                    'suggested_action': 'retry'
                }
                
            except TransactionIntegrityError as e:
                logger.error(f"Erro de integridade em {operation_name}: {e}")
                
                # Tentar rollback automático
                try:
                    rollback_data.update({
                        'error_type': 'transaction_integrity',
                        'error_message': str(e),
                        'entity_id': kwargs.get('invite_id') or kwargs.get('proposal_id') or 0
                    })
                    
                    rollback_result = ErrorRecoveryService.rollback_failed_operation(
                        operation_name, rollback_data
                    )
                    
                    logger.info(f"Rollback executado para {operation_name}: {rollback_result.message}")
                    
                except Exception as rollback_error:
                    logger.error(f"Falha no rollback de {operation_name}: {rollback_error}")
                
                return {
                    'success': False,
                    'error': 'transaction_integrity',
                    'message': ErrorRecoveryService.generate_user_friendly_error_message(e),
                    'rollback_attempted': True
                }
                
            except FinancialIntegrityError as e:
                logger.error(f"Erro financeiro em {operation_name}: {e}")
                
                return {
                    'success': False,
                    'error': 'financial_integrity',
                    'message': ErrorRecoveryService.generate_user_friendly_error_message(e),
                    'error_code': e.error_code
                }
                
            except ValueError as e:
                logger.warning(f"Erro de validação em {operation_name}: {e}")
                
                return {
                    'success': False,
                    'error': 'validation_error',
                    'message': str(e)
                }
                
            except Exception as e:
                logger.error(f"Erro inesperado em {operation_name}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Tentar rollback para erros inesperados
                try:
                    rollback_data.update({
                        'error_type': 'unexpected',
                        'error_message': str(e),
                        'entity_id': kwargs.get('invite_id') or kwargs.get('proposal_id') or 0
                    })
                    
                    rollback_result = ErrorRecoveryService.rollback_failed_operation(
                        operation_name, rollback_data
                    )
                    
                    logger.info(f"Rollback de emergência executado para {operation_name}")
                    
                except Exception as rollback_error:
                    logger.error(f"Falha no rollback de emergência: {rollback_error}")
                
                return {
                    'success': False,
                    'error': 'internal_error',
                    'message': ErrorRecoveryService.generate_user_friendly_error_message(e),
                    'rollback_attempted': True
                }
        
        return wrapper
    return decorator

def handle_concurrent_access(resource_type: str, timeout: int = 30):
    """
    Decorator para tratamento de acesso concorrente a recursos
    
    Args:
        resource_type: Tipo do recurso (invite, proposal, wallet)
        timeout: Timeout em segundos para aguardar lock
    
    Usage:
        @handle_concurrent_access('invite', timeout=10)
        def update_invite(...):
            # código da função
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resource_id = kwargs.get(f'{resource_type}_id') or (args[0] if args else None)
            
            if not resource_id:
                logger.warning(f"ID do recurso {resource_type} não encontrado para controle de concorrência")
                return func(*args, **kwargs)
            
            lock_key = f"{resource_type}_{resource_id}"
            
            try:
                # Implementar controle de concorrência usando ErrorRecoveryService
                if resource_type == 'invite' and 'proposal' in func.__name__.lower():
                    # Usar método específico para propostas
                    if 'create' in func.__name__.lower():
                        return ErrorRecoveryService.handle_concurrent_proposal_creation(
                            invite_id=kwargs.get('invite_id'),
                            prestador_id=kwargs.get('prestador_id'),
                            proposed_value=kwargs.get('proposed_value'),
                            justification=kwargs.get('justification', '')
                        )
                    elif 'respond' in func.__name__.lower() or 'approve' in func.__name__.lower() or 'reject' in func.__name__.lower():
                        action = 'approve' if 'approve' in func.__name__.lower() else 'reject'
                        return ErrorRecoveryService.handle_concurrent_proposal_response(
                            proposal_id=kwargs.get('proposal_id'),
                            client_id=kwargs.get('client_id'),
                            action=action,
                            response_reason=kwargs.get('response_reason')
                        )
                
                # Para outros casos, executar normalmente com logging
                logger.debug(f"Acessando recurso {lock_key} com controle de concorrência")
                return func(*args, **kwargs)
                
            except ConcurrentOperationError as e:
                logger.warning(f"Acesso concorrente detectado para {lock_key}: {e}")
                return {
                    'success': False,
                    'error': 'concurrent_access',
                    'message': f'Outro usuário está modificando este {resource_type}. Tente novamente em alguns segundos.',
                    'retry_after': 3
                }
            except Exception as e:
                logger.error(f"Erro no controle de concorrência para {lock_key}: {e}")
                raise
        
        return wrapper
    return decorator

def validate_data_integrity(entity_type: str):
    """
    Decorator para validação automática de integridade de dados
    
    Args:
        entity_type: Tipo da entidade (invite, proposal, wallet)
    
    Usage:
        @validate_data_integrity('proposal')
        def update_proposal(...):
            # código da função
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            entity_id = kwargs.get(f'{entity_type}_id') or (args[0] if args else None)
            
            try:
                # Executar função original
                result = func(*args, **kwargs)
                
                # Validar integridade após operação (se bem-sucedida)
                if isinstance(result, dict) and result.get('success', True):
                    try:
                        # Executar verificação de integridade específica
                        if entity_type == 'invite' and entity_id:
                            ErrorRecoveryService._validate_invite_integrity(entity_id)
                        elif entity_type == 'proposal' and entity_id:
                            ErrorRecoveryService._validate_proposal_integrity(entity_id)
                        elif entity_type == 'wallet' and entity_id:
                            ErrorRecoveryService._validate_wallet_integrity(entity_id)
                            
                    except Exception as validation_error:
                        logger.error(f"Validação de integridade falhou para {entity_type} {entity_id}: {validation_error}")
                        
                        # Se a validação falhar, registrar para correção posterior
                        # mas não falhar a operação principal
                        log_financial_operation(
                            operation_type="integrity_validation_failed",
                            user_id=kwargs.get('user_id'),
                            amount=None,
                            details={
                                'entity_type': entity_type,
                                'entity_id': entity_id,
                                'function': func.__name__,
                                'validation_error': str(validation_error)
                            }
                        )
                
                return result
                
            except Exception as e:
                logger.error(f"Erro na validação de integridade para {entity_type}: {e}")
                raise
        
        return wrapper
    return decorator

# Extensões para ErrorRecoveryService com validações específicas
def _validate_invite_integrity(invite_id: int):
    """Valida integridade específica de convite"""
    from models import Invite, Proposal
    
    invite = Invite.query.get(invite_id)
    if not invite:
        return
    
    # Verificar consistência de proposta ativa
    if invite.has_active_proposal:
        if not invite.current_proposal_id:
            raise ValueError(f"Convite {invite_id} marcado com proposta ativa mas sem proposal_id")
        
        active_proposal = Proposal.query.get(invite.current_proposal_id)
        if not active_proposal or active_proposal.invite_id != invite_id:
            raise ValueError(f"Proposta ativa {invite.current_proposal_id} não corresponde ao convite {invite_id}")
    
    # Verificar valor efetivo
    if invite.effective_value is not None:
        active_proposal = invite.get_active_proposal()
        if active_proposal and active_proposal.status == 'accepted':
            if invite.effective_value != active_proposal.proposed_value:
                raise ValueError(f"Valor efetivo inconsistente no convite {invite_id}")

def _validate_proposal_integrity(proposal_id: int):
    """Valida integridade específica de proposta"""
    from models import Proposal
    
    proposal = Proposal.query.get(proposal_id)
    if not proposal:
        return
    
    # Verificar se convite está marcado corretamente
    invite = proposal.invite
    if proposal.status == 'pending':
        if not invite.has_active_proposal or invite.current_proposal_id != proposal_id:
            raise ValueError(f"Proposta {proposal_id} pendente mas convite não está marcado corretamente")

def _validate_wallet_integrity(wallet_id: int):
    """Valida integridade específica de carteira"""
    from models import Wallet
    
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        return
    
    # Verificar saldos não negativos
    if wallet.balance < 0:
        raise ValueError(f"Saldo negativo detectado na carteira {wallet_id}: {wallet.balance}")
    
    if wallet.escrow_balance < 0:
        raise ValueError(f"Saldo de escrow negativo detectado na carteira {wallet_id}: {wallet.escrow_balance}")

# Adicionar métodos ao ErrorRecoveryService
ErrorRecoveryService._validate_invite_integrity = staticmethod(_validate_invite_integrity)
ErrorRecoveryService._validate_proposal_integrity = staticmethod(_validate_proposal_integrity)
ErrorRecoveryService._validate_wallet_integrity = staticmethod(_validate_wallet_integrity)