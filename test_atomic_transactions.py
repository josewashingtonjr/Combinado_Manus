#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste básico do sistema de transações atômicas implementado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, Wallet, Transaction
from services.wallet_service import WalletService
from services.atomic_transaction_manager import (
    InsufficientBalanceError,
    NegativeBalanceError,
    atomic_financial_operation
)
from datetime import datetime
from decimal import Decimal

def create_test_app():
    """Cria aplicação Flask para teste"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    db.init_app(app)
    return app

def test_atomic_transactions():
    """Testa o sistema de transações atômicas"""
    app = create_test_app()
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Criar usuário de teste
        user = User(
            email="teste@exemplo.com",
            nome="Usuário Teste",
            cpf="12345678901",
            roles="cliente"
        )
        user.set_password("senha123")
        db.session.add(user)
        db.session.commit()
        
        print("✓ Usuário de teste criado")
        
        # Criar carteira para o usuário
        wallet = WalletService.ensure_user_has_wallet(user.id)
        print(f"✓ Carteira criada - Saldo inicial: {wallet.balance}")
        
        # Testar crédito atômico usando context manager diretamente
        try:
            with atomic_financial_operation("test_credit"):
                wallet = Wallet.query.filter_by(user_id=user.id).first()
                wallet.balance += Decimal('100.00')
                wallet.updated_at = datetime.utcnow()
                
                transaction = Transaction(
                    user_id=user.id,
                    type="credito",
                    amount=Decimal('100.00'),
                    description="Teste de crédito atômico"
                )
                db.session.add(transaction)
            
            # Verificar resultado
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            print(f"✓ Crédito atômico realizado - Novo saldo: {wallet.balance}")
        except Exception as e:
            print(f"✗ Erro no crédito atômico: {e}")
            return False
        
        # Testar débito atômico com saldo suficiente
        try:
            with atomic_financial_operation("test_debit"):
                wallet = Wallet.query.filter_by(user_id=user.id).first()
                if wallet.balance < Decimal('50.00'):
                    raise InsufficientBalanceError(wallet.balance, Decimal('50.00'), user.id)
                
                wallet.balance -= Decimal('50.00')
                wallet.updated_at = datetime.utcnow()
                
                transaction = Transaction(
                    user_id=user.id,
                    type="debito",
                    amount=Decimal('-50.00'),
                    description="Teste de débito atômico"
                )
                db.session.add(transaction)
            
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            print(f"✓ Débito atômico realizado - Novo saldo: {wallet.balance}")
        except Exception as e:
            print(f"✗ Erro no débito atômico: {e}")
            return False
        
        # Testar validação de saldo insuficiente
        try:
            with atomic_financial_operation("test_insufficient"):
                wallet = Wallet.query.filter_by(user_id=user.id).first()
                if wallet.balance < Decimal('200.00'):
                    raise InsufficientBalanceError(wallet.balance, Decimal('200.00'), user.id)
                
                wallet.balance -= Decimal('200.00')
            
            print("✗ Deveria ter falhado por saldo insuficiente")
            return False
        except InsufficientBalanceError as e:
            print(f"✓ Validação de saldo insuficiente funcionando: {e}")
        except Exception as e:
            print(f"✗ Erro inesperado na validação de saldo: {e}")
            return False
        
        # Testar transferência para escrow
        try:
            with atomic_financial_operation("test_escrow"):
                wallet = Wallet.query.filter_by(user_id=user.id).first()
                if wallet.balance < Decimal('30.00'):
                    raise InsufficientBalanceError(wallet.balance, Decimal('30.00'), user.id)
                
                wallet.balance -= Decimal('30.00')
                wallet.escrow_balance += Decimal('30.00')
                wallet.updated_at = datetime.utcnow()
                
                transaction = Transaction(
                    user_id=user.id,
                    type="escrow_bloqueio",
                    amount=Decimal('-30.00'),
                    description="Bloqueio para ordem #1",
                    order_id=1
                )
                db.session.add(transaction)
            
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            print(f"✓ Transferência para escrow - Saldo: {wallet.balance}, Escrow: {wallet.escrow_balance}")
        except Exception as e:
            print(f"✗ Erro na transferência para escrow: {e}")
            return False
        
        # Verificar integridade das transações
        try:
            integrity = WalletService.validate_transaction_integrity(user.id)
            if integrity['is_valid']:
                print("✓ Integridade das transações validada")
            else:
                print(f"✗ Integridade das transações falhou: {integrity}")
                return False
        except Exception as e:
            print(f"✗ Erro na validação de integridade: {e}")
            return False
        
        print("\n🎉 Todos os testes de transações atômicas passaram!")
        return True

if __name__ == "__main__":
    print("Testando sistema de transações atômicas...\n")
    success = test_atomic_transactions()
    
    if success:
        print("\n✅ Sistema de transações atômicas implementado com sucesso!")
    else:
        print("\n❌ Falhas encontradas no sistema de transações atômicas")
        sys.exit(1)