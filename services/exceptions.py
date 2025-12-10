#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Exceções personalizadas para o sistema de convites e ordens

Este módulo define exceções específicas para diferentes tipos de erros
que podem ocorrer durante o processamento de convites e ordens.

Requirements: 7.4, 8.3, 8.4
"""

from decimal import Decimal


class InviteAcceptanceError(Exception):
    """Erro base para problemas na aceitação de convites"""
    pass


class InsufficientBalanceError(InviteAcceptanceError):
    """
    Erro quando usuário não tem saldo suficiente
    
    Attributes:
        user_id: ID do usuário com saldo insuficiente
        user_type: Tipo do usuário ('cliente' ou 'prestador')
        required_amount: Valor necessário
        current_balance: Saldo atual disponível
        message: Mensagem de erro formatada
        
    Requirements: 7.4, 8.3, 8.4
    """
    
    def __init__(self, user_id, user_type, required_amount, current_balance, purpose=None):
        self.user_id = user_id
        self.user_type = user_type
        self.required_amount = Decimal(str(required_amount))
        self.current_balance = Decimal(str(current_balance))
        self.purpose = purpose or "operação"
        
        # Mensagem clara com valores
        # Requirements: 7.4, 8.3, 8.4
        if user_type == 'cliente':
            self.message = (
                f"Saldo insuficiente para {self.purpose}. "
                f"Necessário: R$ {self.required_amount:.2f}, "
                f"Disponível: R$ {self.current_balance:.2f}. "
                f"Por favor, adicione R$ {(self.required_amount - self.current_balance):.2f} "
                f"à sua carteira antes de continuar."
            )
        else:  # prestador
            self.message = (
                f"Saldo insuficiente para {self.purpose}. "
                f"Necessário: R$ {self.required_amount:.2f}, "
                f"Disponível: R$ {self.current_balance:.2f}. "
                f"Por favor, adicione R$ {(self.required_amount - self.current_balance):.2f} "
                f"à sua carteira antes de aceitar o convite."
            )
        
        super().__init__(self.message)
    
    def get_deficit(self):
        """Retorna o valor que falta"""
        return self.required_amount - self.current_balance
    
    def to_dict(self):
        """Retorna representação em dicionário para logging"""
        return {
            'error_type': 'insufficient_balance',
            'user_id': self.user_id,
            'user_type': self.user_type,
            'required_amount': float(self.required_amount),
            'current_balance': float(self.current_balance),
            'deficit': float(self.get_deficit()),
            'purpose': self.purpose,
            'message': self.message
        }


class OrderCreationError(InviteAcceptanceError):
    """
    Erro durante a criação da ordem
    
    Attributes:
        invite_id: ID do convite
        reason: Motivo do erro
        original_exception: Exceção original que causou o erro
        
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    
    def __init__(self, invite_id, reason, original_exception=None):
        self.invite_id = invite_id
        self.reason = reason
        self.original_exception = original_exception
        
        # Mensagem clara para o usuário
        # Requirements: 7.4
        self.message = (
            f"Não foi possível criar a ordem de serviço: {reason}. "
            f"O convite permanece aceito e você pode tentar novamente. "
            f"Se o problema persistir, entre em contato com o suporte."
        )
        
        super().__init__(self.message)
    
    def to_dict(self):
        """Retorna representação em dicionário para logging"""
        return {
            'error_type': 'order_creation_error',
            'invite_id': self.invite_id,
            'reason': self.reason,
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'message': self.message
        }


class EscrowBlockError(InviteAcceptanceError):
    """
    Erro durante o bloqueio de valores em escrow
    
    Attributes:
        order_id: ID da ordem (se já foi criada)
        user_id: ID do usuário cujo valor não pôde ser bloqueado
        amount: Valor que deveria ser bloqueado
        reason: Motivo do erro
        
    Requirements: 7.2, 7.5
    """
    
    def __init__(self, order_id, user_id, amount, reason):
        self.order_id = order_id
        self.user_id = user_id
        self.amount = Decimal(str(amount))
        self.reason = reason
        
        # Mensagem clara para o usuário
        # Requirements: 7.4
        self.message = (
            f"Erro ao bloquear valores em garantia: {reason}. "
            f"A operação foi cancelada e nenhum valor foi debitado. "
            f"Por favor, tente novamente. Se o problema persistir, "
            f"entre em contato com o suporte."
        )
        
        super().__init__(self.message)
    
    def to_dict(self):
        """Retorna representação em dicionário para logging"""
        return {
            'error_type': 'escrow_block_error',
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'reason': self.reason,
            'message': self.message
        }


class InviteValidationError(InviteAcceptanceError):
    """
    Erro de validação durante aceitação de convite
    
    Usado para erros como convite expirado, já aceito, etc.
    
    Requirements: 7.4
    """
    
    def __init__(self, invite_id, reason):
        self.invite_id = invite_id
        self.reason = reason
        self.message = reason
        
        super().__init__(self.message)
    
    def to_dict(self):
        """Retorna representação em dicionário para logging"""
        return {
            'error_type': 'invite_validation_error',
            'invite_id': self.invite_id,
            'reason': self.reason,
            'message': self.message
        }
