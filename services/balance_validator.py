#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
from models import db, Wallet, User
from services.wallet_service import WalletService
from services.config_service import ConfigService
import logging

@dataclass
class BalanceStatus:
    """Status da verificação de saldo"""
    is_sufficient: bool
    current_balance: Decimal
    required_amount: Decimal
    shortfall: Decimal
    suggested_top_up: Decimal
    contestation_fee: Decimal

class BalanceValidator:
    """
    Validador de saldo para verificação de suficiência em propostas de alteração
    
    Este serviço implementa as funcionalidades necessárias para:
    - Calcular valor total necessário (valor + taxa de contestação)
    - Verificar suficiência de saldo
    - Sugerir valores de recarga
    - Reservar fundos automaticamente
    
    Requirements: 3.1, 3.2, 3.3, 4.2
    """
    
    # Taxa de contestação padrão - pode ser configurável via SystemConfig
    DEFAULT_CONTESTATION_FEE = Decimal('10.00')  # R$ 10,00
    
    @staticmethod
    def get_contestation_fee() -> Decimal:
        """
        Obtém a taxa de contestação atual do sistema
        
        Verifica primeiro nas configurações do sistema, senão usa o valor padrão
        """
        try:
            fee = ConfigService.get_config('taxa_contestacao', float(BalanceValidator.DEFAULT_CONTESTATION_FEE))
            return Decimal(str(fee))
        except Exception as e:
            logging.warning(f"Erro ao obter taxa de contestação das configurações: {e}")
            return BalanceValidator.DEFAULT_CONTESTATION_FEE
    
    @staticmethod
    def calculate_required_balance(proposed_value: Decimal) -> Decimal:
        """
        Calcula o saldo total necessário para aceitar uma proposta
        
        Fórmula: valor_proposto + taxa_contestacao
        
        Args:
            proposed_value: Valor proposto pelo prestador
            
        Returns:
            Decimal: Valor total necessário na carteira do cliente
            
        Requirements: 3.1
        """
        if not isinstance(proposed_value, Decimal):
            proposed_value = Decimal(str(proposed_value))
        
        if proposed_value <= 0:
            raise ValueError("Valor proposto deve ser positivo")
        
        contestation_fee = BalanceValidator.get_contestation_fee()
        required_amount = proposed_value + contestation_fee
        
        logging.info(f"Calculando saldo necessário: {proposed_value} + {contestation_fee} = {required_amount}")
        
        return required_amount
    
    @staticmethod
    def check_sufficiency(client_id: int, required_amount: Decimal) -> BalanceStatus:
        """
        Verifica se o cliente tem saldo suficiente para o valor necessário
        
        Args:
            client_id: ID do cliente
            required_amount: Valor total necessário
            
        Returns:
            BalanceStatus: Status completo da verificação de saldo
            
        Requirements: 3.2
        """
        if not isinstance(required_amount, Decimal):
            required_amount = Decimal(str(required_amount))
        
        if required_amount <= 0:
            raise ValueError("Valor necessário deve ser positivo")
        
        # Obter saldo atual do cliente
        try:
            current_balance = Decimal(str(WalletService.get_wallet_balance(client_id)))
        except ValueError:
            # Cliente não tem carteira - criar uma vazia
            try:
                WalletService.ensure_user_has_wallet(client_id)
                current_balance = Decimal('0.00')
            except Exception as e:
                logging.error(f"Erro ao criar carteira para cliente {client_id}: {e}")
                current_balance = Decimal('0.00')
        
        # Verificar suficiência
        is_sufficient = current_balance >= required_amount
        shortfall = max(Decimal('0.00'), required_amount - current_balance)
        
        # Calcular sugestão de recarga
        suggested_top_up = BalanceValidator.suggest_top_up_amount(current_balance, required_amount)
        
        # Obter taxa de contestação para referência
        contestation_fee = BalanceValidator.get_contestation_fee()
        
        logging.info(f"Verificação de saldo - Cliente {client_id}: "
                    f"Saldo atual: {current_balance}, "
                    f"Necessário: {required_amount}, "
                    f"Suficiente: {is_sufficient}")
        
        return BalanceStatus(
            is_sufficient=is_sufficient,
            current_balance=current_balance,
            required_amount=required_amount,
            shortfall=shortfall,
            suggested_top_up=suggested_top_up,
            contestation_fee=contestation_fee
        )
    
    @staticmethod
    def suggest_top_up_amount(current_balance: Decimal, required_amount: Decimal) -> Decimal:
        """
        Calcula o valor sugerido para recarga da carteira
        
        Estratégia:
        - Se não há déficit, retorna 0
        - Se há déficit, arredonda para múltiplos de R$ 10,00
        - Adiciona uma margem de segurança de 10% ou mínimo R$ 5,00
        
        Args:
            current_balance: Saldo atual do cliente
            required_amount: Valor total necessário
            
        Returns:
            Decimal: Valor sugerido para recarga
            
        Requirements: 3.3
        """
        if not isinstance(current_balance, Decimal):
            current_balance = Decimal(str(current_balance))
        
        if not isinstance(required_amount, Decimal):
            required_amount = Decimal(str(required_amount))
        
        # Se já tem saldo suficiente, não precisa recarregar
        if current_balance >= required_amount:
            return Decimal('0.00')
        
        # Calcular déficit
        shortfall = required_amount - current_balance
        
        # Adicionar margem de segurança (10% ou mínimo R$ 5,00)
        safety_margin = max(shortfall * Decimal('0.10'), Decimal('5.00'))
        total_needed = shortfall + safety_margin
        
        # Arredondar para múltiplos de R$ 10,00 (para cima)
        suggested_amount = ((total_needed // Decimal('10.00')) + 1) * Decimal('10.00')
        
        logging.info(f"Sugestão de recarga: Déficit {shortfall} + Margem {safety_margin} = "
                    f"Total {total_needed} → Sugerido {suggested_amount}")
        
        return suggested_amount
    
    @staticmethod
    def reserve_funds(client_id: int, amount: Decimal, description: str = "Reserva para proposta") -> dict:
        """
        Reserva fundos na carteira do cliente (transfere para escrow)
        
        Esta função move o valor do saldo principal para o saldo em escrow,
        garantindo que os fundos estejam reservados para a transação.
        
        Args:
            client_id: ID do cliente
            amount: Valor a ser reservado
            description: Descrição da reserva
            
        Returns:
            dict: Resultado da operação de reserva
            
        Requirements: 4.2
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Valor a reservar deve ser positivo")
        
        # Verificar se cliente tem saldo suficiente antes de reservar
        balance_status = BalanceValidator.check_sufficiency(client_id, amount)
        
        if not balance_status.is_sufficient:
            raise ValueError(f"Saldo insuficiente para reserva. "
                           f"Necessário: {amount}, "
                           f"Disponível: {balance_status.current_balance}, "
                           f"Déficit: {balance_status.shortfall}")
        
        try:
            # Usar o WalletService para transferir para escrow
            # Nota: Como não temos order_id ainda (proposta ainda não aceita),
            # usamos um ID temporário ou None
            result = WalletService.transfer_to_escrow(
                user_id=client_id,
                amount=amount,
                order_id=None  # Será atualizado quando a ordem for criada
            )
            
            logging.info(f"Fundos reservados com sucesso - Cliente {client_id}: "
                        f"Valor {amount}, Novo saldo: {result['new_balance']}, "
                        f"Novo escrow: {result['new_escrow_balance']}")
            
            return {
                'success': True,
                'reserved_amount': amount,
                'new_balance': result['new_balance'],
                'new_escrow_balance': result['new_escrow_balance'],
                'transaction_id': result['transaction_id'],
                'description': description
            }
            
        except Exception as e:
            logging.error(f"Erro ao reservar fundos para cliente {client_id}: {e}")
            raise ValueError(f"Falha na reserva de fundos: {str(e)}")
    
    @staticmethod
    def validate_proposal_balance(client_id: int, proposed_value: Decimal) -> BalanceStatus:
        """
        Validação completa de saldo para uma proposta específica
        
        Combina o cálculo do valor necessário com a verificação de suficiência
        
        Args:
            client_id: ID do cliente
            proposed_value: Valor proposto pelo prestador
            
        Returns:
            BalanceStatus: Status completo da validação
            
        Requirements: 3.1, 3.2, 3.3
        """
        # Calcular valor total necessário
        required_amount = BalanceValidator.calculate_required_balance(proposed_value)
        
        # Verificar suficiência
        balance_status = BalanceValidator.check_sufficiency(client_id, required_amount)
        
        logging.info(f"Validação completa de proposta - Cliente {client_id}: "
                    f"Valor proposto: {proposed_value}, "
                    f"Total necessário: {required_amount}, "
                    f"Status: {'✓' if balance_status.is_sufficient else '✗'}")
        
        return balance_status
    
    @staticmethod
    def get_balance_summary(client_id: int) -> dict:
        """
        Retorna um resumo completo do saldo do cliente
        
        Útil para exibir informações na interface do usuário
        
        Args:
            client_id: ID do cliente
            
        Returns:
            dict: Resumo completo do saldo
        """
        try:
            wallet_info = WalletService.get_wallet_info(client_id)
            contestation_fee = BalanceValidator.get_contestation_fee()
            
            return {
                'client_id': client_id,
                'balance': wallet_info['balance'],
                'escrow_balance': wallet_info['escrow_balance'],
                'total_balance': wallet_info['total_balance'],
                'available_for_proposals': wallet_info['balance'],  # Apenas saldo principal
                'contestation_fee': contestation_fee,
                'updated_at': wallet_info['updated_at']
            }
            
        except Exception as e:
            logging.error(f"Erro ao obter resumo de saldo para cliente {client_id}: {e}")
            return {
                'client_id': client_id,
                'balance': Decimal('0.00'),
                'escrow_balance': Decimal('0.00'),
                'total_balance': Decimal('0.00'),
                'available_for_proposals': Decimal('0.00'),
                'contestation_fee': BalanceValidator.get_contestation_fee(),
                'updated_at': None,
                'error': str(e)
            }