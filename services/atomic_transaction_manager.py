#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Sistema de Transações Atômicas para Operações Financeiras

Este módulo implementa um context manager para garantir atomicidade em operações
financeiras críticas, incluindo sistema de retry com backoff exponencial para
lidar com deadlocks e exceções específicas para integridade financeira.

Requisitos atendidos: 2.1, 2.2, 2.3
"""

from contextlib import contextmanager
from models import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import time
import logging
from datetime import datetime
from decimal import Decimal

# Configurar logging
logger = logging.getLogger(__name__)

# ==============================================================================
#  EXCEÇÕES ESPECÍFICAS PARA INTEGRIDADE FINANCEIRA
# ==============================================================================

class FinancialIntegrityError(Exception):
    """Exceção base para erros de integridade financeira"""
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class InsufficientBalanceError(FinancialIntegrityError):
    """Erro quando saldo é insuficiente para operação"""
    def __init__(self, current_balance, required_amount, user_id=None):
        message = f"Saldo insuficiente: disponível {current_balance}, necessário {required_amount}"
        details = {
            'current_balance': current_balance,
            'required_amount': required_amount,
            'user_id': user_id,
            'deficit': required_amount - current_balance
        }
        super().__init__(message, 'INSUFFICIENT_BALANCE', details)

class NegativeBalanceError(FinancialIntegrityError):
    """Erro quando operação resultaria em saldo negativo"""
    def __init__(self, attempted_balance, user_id=None):
        message = f"Operação resultaria em saldo negativo: {attempted_balance}"
        details = {
            'attempted_balance': attempted_balance,
            'user_id': user_id
        }
        super().__init__(message, 'NEGATIVE_BALANCE', details)

class TransactionIntegrityError(FinancialIntegrityError):
    """Erro de integridade em transações"""
    def __init__(self, message, transaction_data=None):
        details = {'transaction_data': transaction_data} if transaction_data else {}
        super().__init__(message, 'TRANSACTION_INTEGRITY', details)

class ConcurrentOperationError(FinancialIntegrityError):
    """Erro quando operações concorrentes causam conflito"""
    def __init__(self, message, retry_count=0):
        details = {'retry_count': retry_count}
        super().__init__(message, 'CONCURRENT_OPERATION', details)

class EscrowIntegrityError(FinancialIntegrityError):
    """Erro de integridade em operações de escrow"""
    def __init__(self, message, escrow_balance=None, required_amount=None):
        details = {
            'escrow_balance': escrow_balance,
            'required_amount': required_amount
        }
        super().__init__(message, 'ESCROW_INTEGRITY', details)

# ==============================================================================
#  GERENCIADOR DE TRANSAÇÕES ATÔMICAS
# ==============================================================================

class AtomicTransactionManager:
    """
    Gerenciador de transações atômicas para operações financeiras críticas
    
    Funcionalidades:
    - Context manager para transações atômicas
    - Sistema de retry com backoff exponencial
    - Tratamento específico de deadlocks e race conditions
    - Logging detalhado de operações
    """
    
    # Configurações padrão
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 0.1  # 100ms
    DEFAULT_MAX_DELAY = 2.0   # 2 segundos
    DEFAULT_BACKOFF_MULTIPLIER = 2
    
    def __init__(self, max_retries=None, base_delay=None, max_delay=None):
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.base_delay = base_delay or self.DEFAULT_BASE_DELAY
        self.max_delay = max_delay or self.DEFAULT_MAX_DELAY
        self.backoff_multiplier = self.DEFAULT_BACKOFF_MULTIPLIER
    
    @contextmanager
    def atomic_financial_operation(self, operation_name="financial_operation"):
        """
        Context manager para operações financeiras atômicas
        
        Args:
            operation_name: Nome da operação para logging
            
        Yields:
            None - permite execução do código dentro do contexto
            
        Raises:
            FinancialIntegrityError: Para erros de integridade financeira
            TransactionIntegrityError: Para erros de transação
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        logger.info(f"Iniciando operação atômica: {operation_id}")
        
        try:
            # Verificar se já existe uma transação ativa
            transaction_started = False
            try:
                # Tentar iniciar uma nova transação
                db.session.begin()
                transaction_started = True
                logger.debug(f"Transação iniciada para operação: {operation_id}")
            except Exception:
                # Se falhar, provavelmente já existe uma transação ativa
                logger.debug(f"Usando transação existente para operação: {operation_id}")
            
            yield
            
            # Commit se tudo correu bem e iniciamos a transação
            if transaction_started:
                db.session.commit()
                logger.info(f"Operação atômica concluída com sucesso: {operation_id}")
            else:
                logger.debug(f"Operação concluída (commit será feito pela transação pai): {operation_id}")
            
        except (InsufficientBalanceError, NegativeBalanceError, EscrowIntegrityError) as e:
            # Erros de integridade financeira - não fazer retry
            if transaction_started:
                db.session.rollback()
            logger.error(f"Erro de integridade financeira em {operation_id}: {e}")
            raise
            
        except IntegrityError as e:
            # Violação de constraint - pode ser race condition
            if transaction_started:
                db.session.rollback()
            error_msg = f"Violação de integridade em {operation_id}: {str(e)}"
            logger.error(error_msg)
            raise TransactionIntegrityError(error_msg, {'original_error': str(e)})
            
        except OperationalError as e:
            # Erro operacional (deadlock, timeout, etc.)
            if transaction_started:
                db.session.rollback()
            error_msg = f"Erro operacional em {operation_id}: {str(e)}"
            logger.error(error_msg)
            raise ConcurrentOperationError(error_msg)
            
        except SQLAlchemyError as e:
            # Outros erros do SQLAlchemy
            if transaction_started:
                db.session.rollback()
            error_msg = f"Erro de banco de dados em {operation_id}: {str(e)}"
            logger.error(error_msg)
            raise TransactionIntegrityError(error_msg, {'original_error': str(e)})
            
        except Exception as e:
            # Qualquer outro erro
            if transaction_started:
                db.session.rollback()
            error_msg = f"Erro inesperado em {operation_id}: {str(e)}"
            logger.error(error_msg)
            raise TransactionIntegrityError(error_msg, {'original_error': str(e)})
    
    def execute_with_retry(self, operation, operation_name="retry_operation", **kwargs):
        """
        Executa operação com retry automático em caso de deadlock/concorrência
        
        Args:
            operation: Função a ser executada
            operation_name: Nome da operação para logging
            **kwargs: Argumentos para a operação
            
        Returns:
            Resultado da operação
            
        Raises:
            FinancialIntegrityError: Após esgotar tentativas ou erro não recuperável
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 para incluir tentativa inicial
            try:
                logger.debug(f"Tentativa {attempt + 1}/{self.max_retries + 1} para {operation_name}")
                
                with self.atomic_financial_operation(f"{operation_name}_attempt_{attempt + 1}"):
                    result = operation(**kwargs)
                    
                logger.info(f"Operação {operation_name} bem-sucedida na tentativa {attempt + 1}")
                return result
                
            except (InsufficientBalanceError, NegativeBalanceError, EscrowIntegrityError) as e:
                # Erros de integridade financeira - não fazer retry
                logger.error(f"Erro de integridade não recuperável em {operation_name}: {e}")
                raise
                
            except (ConcurrentOperationError, TransactionIntegrityError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calcular delay com backoff exponencial
                    delay = min(
                        self.base_delay * (self.backoff_multiplier ** attempt),
                        self.max_delay
                    )
                    
                    logger.warning(
                        f"Tentativa {attempt + 1} falhou para {operation_name}: {e}. "
                        f"Tentando novamente em {delay:.3f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Todas as tentativas falharam para {operation_name}")
                    break
            
            except Exception as e:
                # Erro inesperado - não fazer retry
                logger.error(f"Erro inesperado não recuperável em {operation_name}: {e}")
                raise TransactionIntegrityError(
                    f"Erro inesperado em {operation_name}: {str(e)}",
                    {'original_error': str(e)}
                )
        
        # Se chegou aqui, todas as tentativas falharam
        raise ConcurrentOperationError(
            f"Operação {operation_name} falhou após {self.max_retries + 1} tentativas",
            retry_count=self.max_retries
        ) from last_exception
    
    @staticmethod
    def validate_balance_integrity(wallet, operation_amount, operation_type="debit"):
        """
        Valida integridade de saldo antes de operação
        
        Args:
            wallet: Objeto Wallet
            operation_amount: Valor da operação (positivo)
            operation_type: Tipo de operação ("debit", "credit", "escrow_transfer")
            
        Raises:
            InsufficientBalanceError: Se saldo insuficiente
            NegativeBalanceError: Se operação resultaria em saldo negativo
        """
        if operation_amount <= 0:
            raise ValueError("Valor da operação deve ser positivo")
        
        if operation_type == "debit":
            if wallet.balance < operation_amount:
                raise InsufficientBalanceError(
                    current_balance=wallet.balance,
                    required_amount=operation_amount,
                    user_id=wallet.user_id
                )
            
            # Verificar se não resultaria em saldo negativo
            new_balance = wallet.balance - operation_amount
            if new_balance < 0:
                raise NegativeBalanceError(
                    attempted_balance=new_balance,
                    user_id=wallet.user_id
                )
        
        elif operation_type == "escrow_transfer":
            # Transferência para escrow - verificar saldo principal
            if wallet.balance < operation_amount:
                raise InsufficientBalanceError(
                    current_balance=wallet.balance,
                    required_amount=operation_amount,
                    user_id=wallet.user_id
                )
        
        elif operation_type == "escrow_release":
            # Liberação de escrow - verificar saldo em escrow
            if wallet.escrow_balance < operation_amount:
                raise EscrowIntegrityError(
                    message=f"Saldo em escrow insuficiente: disponível {wallet.escrow_balance}, necessário {operation_amount}",
                    escrow_balance=wallet.escrow_balance,
                    required_amount=operation_amount
                )
    
    @staticmethod
    def log_financial_operation(operation_type, user_id, amount, details=None):
        """
        Registra operação financeira para auditoria
        
        Args:
            operation_type: Tipo da operação
            user_id: ID do usuário
            amount: Valor da operação
            details: Detalhes adicionais
        """
        log_data = {
            'operation_type': operation_type,
            'user_id': user_id,
            'amount': float(amount) if amount else None,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"Operação financeira registrada: {log_data}")

# ==============================================================================
#  INSTÂNCIA GLOBAL PARA CONVENIÊNCIA
# ==============================================================================

# Instância padrão para uso geral
atomic_manager = AtomicTransactionManager()

# Funções de conveniência para uso direto
def atomic_financial_operation(operation_name="financial_operation"):
    """Função de conveniência para context manager atômico"""
    return atomic_manager.atomic_financial_operation(operation_name)

def execute_with_retry(operation, operation_name="retry_operation", **kwargs):
    """Função de conveniência para execução com retry"""
    return atomic_manager.execute_with_retry(operation, operation_name, **kwargs)

def validate_balance_integrity(wallet, operation_amount, operation_type="debit"):
    """Função de conveniência para validação de integridade"""
    return AtomicTransactionManager.validate_balance_integrity(
        wallet, operation_amount, operation_type
    )

def log_financial_operation(operation_type, user_id, amount, details=None):
    """Função de conveniência para logging de operações"""
    return AtomicTransactionManager.log_financial_operation(
        operation_type, user_id, amount, details
    )