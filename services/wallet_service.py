#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Wallet, Transaction, Order
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class WalletService:
    """Serviço para gerenciar carteiras e transações"""
    
    @staticmethod
    def create_wallet_for_user(user):
        """Cria uma carteira para um novo usuário"""
        if not user.wallet:
            wallet = Wallet(user_id=user.id)
            db.session.add(wallet)
            db.session.commit()
            return wallet
        return user.wallet

    @staticmethod
    def get_wallet_balance(user_id):
        """Retorna o saldo da carteira de um usuário"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        return wallet.balance

    @staticmethod
    def deposit(user_id, amount, description):
        """Deposita um valor na carteira de um usuário"""
        if amount <= 0:
            raise ValueError("Valor do depósito deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        try:
            wallet.balance += amount
            
            transaction = Transaction(
                user_id=user_id,
                type="deposito",
                amount=amount,
                description=description
            )
            db.session.add(transaction)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def withdraw(user_id, amount, description):
        """Saca um valor da carteira de um usuário"""
        if amount <= 0:
            raise ValueError("Valor do saque deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        if wallet.balance < amount:
            raise ValueError("Saldo insuficiente")
        
        try:
            wallet.balance -= amount
            
            transaction = Transaction(
                user_id=user_id,
                type="saque",
                amount=-amount, # Valor negativo para saque
                description=description
            )
            db.session.add(transaction)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def transfer_to_escrow(user_id, amount, order_id):
        """Transfere um valor do saldo principal para o saldo em escrow"""
        if amount <= 0:
            raise ValueError("Valor deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        if wallet.balance < amount:
            raise ValueError("Saldo insuficiente para transferir para escrow")
        
        try:
            wallet.balance -= amount
            wallet.escrow_balance += amount
            
            transaction = Transaction(
                user_id=user_id,
                type="escrow_bloqueio",
                amount=-amount,
                description=f"Bloqueio para ordem #{order_id}",
                order_id=order_id
            )
            db.session.add(transaction)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def release_from_escrow(order_id):
        """Libera o valor em escrow para o prestador e a taxa para o admin"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
        provider_wallet = Wallet.query.filter_by(user_id=order.provider_id).first()
        admin_wallet = Wallet.query.filter_by(user_id=1).first() # TODO: Mudar para um ID de admin dinâmico
        
        if not client_wallet or not provider_wallet or not admin_wallet:
            raise ValueError("Carteira não encontrada")
        
        # TODO: Buscar taxa do SystemConfig
        system_fee_percent = 0.05 # 5%
        system_fee = order.value * system_fee_percent
        provider_amount = order.value - system_fee
        
        if client_wallet.escrow_balance < order.value:
            raise ValueError("Saldo em escrow insuficiente")
        
        try:
            # Libera do escrow do cliente
            client_wallet.escrow_balance -= order.value
            
            # Paga o prestador
            provider_wallet.balance += provider_amount
            
            # Paga a taxa do sistema
            admin_wallet.balance += system_fee
            
            # Registrar transações
            # 1. Liberação do escrow do cliente
            t1 = Transaction(
                user_id=order.client_id,
                type="escrow_liberacao",
                amount=-order.value,
                description=f"Liberação de escrow para ordem #{order_id}",
                order_id=order_id
            )
            
            # 2. Pagamento ao prestador
            t2 = Transaction(
                user_id=order.provider_id,
                type="recebimento",
                amount=provider_amount,
                description=f"Pagamento pela ordem #{order_id}",
                order_id=order_id,
                related_user_id=order.client_id
            )
            
            # 3. Taxa do sistema
            t3 = Transaction(
                user_id=1, # TODO: Mudar para um ID de admin dinâmico
                type="taxa",
                amount=system_fee,
                description=f"Taxa da ordem #{order_id}",
                order_id=order_id
            )
            
            db.session.add_all([t1, t2, t3])
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def refund_from_escrow(order_id):
        """Reembolsa o valor em escrow para o cliente em caso de cancelamento"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
        if not client_wallet:
            raise ValueError("Carteira do cliente não encontrada")
        
        if client_wallet.escrow_balance < order.value:
            raise ValueError("Saldo em escrow insuficiente para reembolso")
        
        try:
            client_wallet.escrow_balance -= order.value
            client_wallet.balance += order.value
            
            transaction = Transaction(
                user_id=order.client_id,
                type="escrow_reembolso",
                amount=order.value,
                description=f"Reembolso de escrow da ordem #{order_id}",
                order_id=order_id
            )
            db.session.add(transaction)
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

