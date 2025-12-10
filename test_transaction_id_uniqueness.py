#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para o sistema de identificação única de transações
Valida geração, formato e unicidade dos transaction_ids
"""

import pytest
import sys
import os
from datetime import datetime
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Wallet, Transaction
from services.transaction_id_generator import TransactionIdGenerator
from services.wallet_service import WalletService


class TestTransactionIdGenerator:
    """Testes para o gerador de IDs únicos"""
    
    def test_generate_unique_id_format(self):
        """Testa se o ID gerado está no formato correto"""
        transaction_id = TransactionIdGenerator.generate_unique_id()
        
        # Verificar formato: TXN-YYYYMMDD-HHMMSS-UUID8
        assert TransactionIdGenerator.validate_format(transaction_id)
        
        # Verificar partes específicas
        parts = transaction_id.split('-')
        assert len(parts) == 4
        assert parts[0] == 'TXN'
        assert len(parts[1]) == 8  # Data YYYYMMDD
        assert len(parts[2]) == 6  # Hora HHMMSS
        assert len(parts[3]) == 8  # UUID 8 chars
        assert parts[3].isupper()  # UUID em maiúsculo
        assert parts[3].isalnum()  # UUID alfanumérico
    
    def test_generate_multiple_unique_ids(self):
        """Testa se múltiplos IDs gerados são únicos"""
        ids = set()
        
        # Gerar 100 IDs
        for _ in range(100):
            transaction_id = TransactionIdGenerator.generate_unique_id()
            assert transaction_id not in ids, f"ID duplicado encontrado: {transaction_id}"
            ids.add(transaction_id)
        
        # Todos devem ter formato válido
        for transaction_id in ids:
            assert TransactionIdGenerator.validate_format(transaction_id)
    
    def test_validate_format_valid_cases(self):
        """Testa validação de formato com casos válidos"""
        valid_ids = [
            "TXN-20241106-143052-A1B2C3D4",
            "TXN-20250101-000000-FFFFFFFF",
            "TXN-19991231-235959-12345678"
        ]
        
        for transaction_id in valid_ids:
            assert TransactionIdGenerator.validate_format(transaction_id)
    
    def test_validate_format_invalid_cases(self):
        """Testa validação de formato com casos inválidos"""
        invalid_ids = [
            "TXN-2024110-143052-A1B2C3D4",  # Data com 7 dígitos
            "TXN-20241106-14305-A1B2C3D4",  # Hora com 5 dígitos
            "TXN-20241106-143052-A1B2C3D",  # UUID com 7 chars
            "TXN-20241106-143052-a1b2c3d4",  # UUID em minúsculo
            "TXN-20241106-143052-A1B2C3D@",  # UUID com caractere especial
            "TRN-20241106-143052-A1B2C3D4",  # Prefixo errado
            "TXN20241106-143052-A1B2C3D4",   # Sem separador após TXN
            "TXN-20241106143052-A1B2C3D4",   # Sem separador entre data e hora
            "",                              # String vazia
            None                             # None
        ]
        
        for transaction_id in invalid_ids:
            assert not TransactionIdGenerator.validate_format(transaction_id)


class TestTransactionModel:
    """Testes para o modelo Transaction com transaction_id"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Configurar banco de dados para testes"""
        with app.app_context():
            db.create_all()
            
            # Criar usuário de teste
            self.test_user = User(
                email="test@example.com",
                nome="Usuário Teste",
                cpf="12345678901",
                roles="cliente"
            )
            self.test_user.set_password("senha123")
            db.session.add(self.test_user)
            db.session.commit()
            
            # Criar carteira
            self.test_wallet = Wallet(
                user_id=self.test_user.id,
                balance=Decimal('100.00')
            )
            db.session.add(self.test_wallet)
            db.session.commit()
            
            yield
            
            # Limpeza
            db.session.remove()
            db.drop_all()
    
    def test_transaction_auto_generates_id(self):
        """Testa se Transaction gera transaction_id automaticamente"""
        with app.app_context():
            transaction = Transaction(
                user_id=self.test_user.id,
                type="deposito",
                amount=Decimal('50.00'),
                description="Teste de transaction_id"
            )
            
            # Verificar se transaction_id foi gerado
            assert transaction.transaction_id is not None
            assert TransactionIdGenerator.validate_format(transaction.transaction_id)
            
            # Salvar no banco
            db.session.add(transaction)
            db.session.commit()
            
            # Verificar se foi salvo corretamente
            saved_transaction = Transaction.query.get(transaction.id)
            assert saved_transaction.transaction_id == transaction.transaction_id
    
    def test_transaction_custom_id_preserved(self):
        """Testa se transaction_id customizado é preservado"""
        with app.app_context():
            custom_id = "TXN-20241106-120000-CUSTOM01"
            
            transaction = Transaction(
                user_id=self.test_user.id,
                type="deposito",
                amount=Decimal('50.00'),
                description="Teste com ID customizado",
                transaction_id=custom_id
            )
            
            # Verificar se ID customizado foi preservado
            assert transaction.transaction_id == custom_id
            
            # Salvar no banco
            db.session.add(transaction)
            db.session.commit()
            
            # Verificar se foi salvo corretamente
            saved_transaction = Transaction.query.get(transaction.id)
            assert saved_transaction.transaction_id == custom_id
    
    def test_transaction_id_uniqueness_constraint(self):
        """Testa se constraint de unicidade funciona"""
        with app.app_context():
            transaction_id = "TXN-20241106-120000-UNIQUE01"
            
            # Primeira transação
            transaction1 = Transaction(
                user_id=self.test_user.id,
                type="deposito",
                amount=Decimal('50.00'),
                description="Primeira transação",
                transaction_id=transaction_id
            )
            db.session.add(transaction1)
            db.session.commit()
            
            # Segunda transação com mesmo ID (deve falhar)
            transaction2 = Transaction(
                user_id=self.test_user.id,
                type="saque",
                amount=Decimal('25.00'),
                description="Segunda transação",
                transaction_id=transaction_id
            )
            db.session.add(transaction2)
            
            # Deve gerar erro de integridade
            with pytest.raises(Exception):  # IntegrityError ou similar
                db.session.commit()
            
            db.session.rollback()


class TestWalletServiceWithTransactionId:
    """Testes para WalletService com sistema de transaction_id"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Configurar banco de dados para testes"""
        with app.app_context():
            db.create_all()
            
            # Criar usuário de teste
            self.test_user = User(
                email="test@example.com",
                nome="Usuário Teste",
                cpf="12345678901",
                roles="cliente"
            )
            self.test_user.set_password("senha123")
            db.session.add(self.test_user)
            db.session.commit()
            
            yield
            
            # Limpeza
            db.session.remove()
            db.drop_all()
    
    def test_credit_wallet_generates_transaction_id(self):
        """Testa se crédito na carteira gera transaction_id válido"""
        with app.app_context():
            # Garantir que usuário tem carteira
            WalletService.ensure_user_has_wallet(self.test_user.id)
            
            # Creditar valor
            result = WalletService.credit_wallet(
                user_id=self.test_user.id,
                amount=100.00,
                description="Teste de crédito com transaction_id"
            )
            
            # Verificar resultado
            assert result['success'] is True
            transaction_id = result['transaction_id']
            
            # Buscar transação criada
            transaction = Transaction.query.get(transaction_id)
            assert transaction is not None
            assert transaction.transaction_id is not None
            assert TransactionIdGenerator.validate_format(transaction.transaction_id)
    
    def test_debit_wallet_generates_transaction_id(self):
        """Testa se débito na carteira gera transaction_id válido"""
        with app.app_context():
            # Garantir que usuário tem carteira com saldo
            WalletService.ensure_user_has_wallet(self.test_user.id)
            WalletService.credit_wallet(
                user_id=self.test_user.id,
                amount=100.00,
                description="Saldo inicial"
            )
            
            # Debitar valor
            result = WalletService.debit_wallet(
                user_id=self.test_user.id,
                amount=50.00,
                description="Teste de débito com transaction_id"
            )
            
            # Verificar resultado
            assert result['success'] is True
            transaction_id = result['transaction_id']
            
            # Buscar transação criada
            transaction = Transaction.query.get(transaction_id)
            assert transaction is not None
            assert transaction.transaction_id is not None
            assert TransactionIdGenerator.validate_format(transaction.transaction_id)
    
    def test_transfer_to_escrow_generates_transaction_id(self):
        """Testa se transferência para escrow gera transaction_id válido"""
        with app.app_context():
            # Garantir que usuário tem carteira com saldo
            WalletService.ensure_user_has_wallet(self.test_user.id)
            WalletService.credit_wallet(
                user_id=self.test_user.id,
                amount=100.00,
                description="Saldo inicial"
            )
            
            # Transferir para escrow
            result = WalletService.transfer_to_escrow(
                user_id=self.test_user.id,
                amount=50.00,
                order_id=1
            )
            
            # Verificar resultado
            assert result['success'] is True
            transaction_id = result['transaction_id']
            
            # Buscar transação criada
            transaction = Transaction.query.get(transaction_id)
            assert transaction is not None
            assert transaction.transaction_id is not None
            assert TransactionIdGenerator.validate_format(transaction.transaction_id)
    
    def test_all_transactions_have_unique_ids(self):
        """Testa se todas as transações têm IDs únicos"""
        with app.app_context():
            # Garantir que usuário tem carteira
            WalletService.ensure_user_has_wallet(self.test_user.id)
            
            # Realizar múltiplas operações
            operations = [
                lambda: WalletService.credit_wallet(self.test_user.id, 100.00, "Crédito 1"),
                lambda: WalletService.credit_wallet(self.test_user.id, 50.00, "Crédito 2"),
                lambda: WalletService.debit_wallet(self.test_user.id, 25.00, "Débito 1"),
                lambda: WalletService.transfer_to_escrow(self.test_user.id, 25.00, 1),
            ]
            
            transaction_ids = set()
            
            for operation in operations:
                result = operation()
                transaction_id = result['transaction_id']
                
                # Buscar transação
                transaction = Transaction.query.get(transaction_id)
                assert transaction.transaction_id not in transaction_ids
                transaction_ids.add(transaction.transaction_id)
            
            # Verificar que todos os IDs são únicos e válidos
            assert len(transaction_ids) == len(operations)
            for transaction_id in transaction_ids:
                assert TransactionIdGenerator.validate_format(transaction_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])