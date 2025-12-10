#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a migração de tipos monetários
"""

import unittest
import os
import tempfile
from decimal import Decimal
from flask import Flask
from config import TestConfig
from models import db, User, Wallet, Transaction, Order, TokenRequest
from services.monetary_migration_service import MonetaryMigrationService

class TestMonetaryMigration(unittest.TestCase):
    """Testes para migração de tipos monetários"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.app = Flask(__name__)
        self.app.config.from_object(TestConfig)
        
        db.init_app(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Cria as tabelas
        db.create_all()
        
        # Cria usuário de teste
        self.test_user = User(
            email='test@example.com',
            nome='Test User',
            cpf='12345678901'
        )
        self.test_user.set_password('password123')
        db.session.add(self.test_user)
        db.session.commit()
    
    def tearDown(self):
        """Limpeza após os testes"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_decimal_conversion(self):
        """Testa conversão de Float para Decimal"""
        # Testa valores diversos
        test_values = [0.0, 1.5, 100.99, 1000.00, 0.01]
        
        for value in test_values:
            decimal_value = MonetaryMigrationService.convert_float_to_decimal(value)
            self.assertIsInstance(decimal_value, Decimal)
            self.assertEqual(decimal_value, Decimal(str(value)).quantize(Decimal('0.01')))
    
    def test_wallet_numeric_fields(self):
        """Testa se os campos da Wallet são Numeric"""
        wallet = Wallet(
            user_id=self.test_user.id,
            balance=Decimal('100.50'),
            escrow_balance=Decimal('25.75')
        )
        db.session.add(wallet)
        db.session.commit()
        
        # Verifica se os valores foram salvos corretamente
        saved_wallet = db.session.query(Wallet).filter_by(user_id=self.test_user.id).first()
        self.assertEqual(saved_wallet.balance, Decimal('100.50'))
        self.assertEqual(saved_wallet.escrow_balance, Decimal('25.75'))
    
    def test_transaction_numeric_fields(self):
        """Testa se os campos da Transaction são Numeric"""
        transaction = Transaction(
            user_id=self.test_user.id,
            type='deposito',
            amount=Decimal('50.25'),
            description='Teste de depósito'
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Verifica se o valor foi salvo corretamente
        saved_transaction = db.session.query(Transaction).filter_by(user_id=self.test_user.id).first()
        self.assertEqual(saved_transaction.amount, Decimal('50.25'))
    
    def test_order_numeric_fields(self):
        """Testa se os campos da Order são Numeric"""
        order = Order(
            client_id=self.test_user.id,
            title='Serviço de teste',
            description='Descrição do serviço',
            value=Decimal('150.00')
        )
        db.session.add(order)
        db.session.commit()
        
        # Verifica se o valor foi salvo corretamente
        saved_order = db.session.query(Order).filter_by(client_id=self.test_user.id).first()
        self.assertEqual(saved_order.value, Decimal('150.00'))
    
    def test_token_request_numeric_fields(self):
        """Testa se os campos da TokenRequest são Numeric"""
        token_request = TokenRequest(
            user_id=self.test_user.id,
            amount=Decimal('200.75'),
            description='Solicitação de teste'
        )
        db.session.add(token_request)
        db.session.commit()
        
        # Verifica se o valor foi salvo corretamente
        saved_request = db.session.query(TokenRequest).filter_by(user_id=self.test_user.id).first()
        self.assertEqual(saved_request.amount, Decimal('200.75'))
    
    def test_backup_and_restore(self):
        """Testa backup e restauração de dados"""
        # Cria dados de teste
        wallet = Wallet(user_id=self.test_user.id, balance=Decimal('100.00'))
        transaction = Transaction(
            user_id=self.test_user.id,
            type='deposito',
            amount=Decimal('50.00'),
            description='Teste'
        )
        db.session.add_all([wallet, transaction])
        db.session.commit()
        
        # Faz backup
        backup_data = MonetaryMigrationService.backup_data_before_migration()
        
        # Verifica se o backup contém os dados
        self.assertEqual(len(backup_data['wallets']), 1)
        self.assertEqual(len(backup_data['transactions']), 1)
        self.assertEqual(backup_data['wallets'][0]['balance'], 100.0)
        self.assertEqual(backup_data['transactions'][0]['amount'], 50.0)
    
    def test_database_type_detection(self):
        """Testa detecção do tipo de banco"""
        db_type = MonetaryMigrationService.get_database_type()
        self.assertIn(db_type, ['sqlite', 'postgresql', 'mysql'])
    
    def test_precision_preservation(self):
        """Testa se a precisão decimal é preservada"""
        # Testa valores com diferentes precisões
        test_values = [
            (1.1, Decimal('1.10')),
            (1.99, Decimal('1.99')),
            (0.01, Decimal('0.01')),
            (999.99, Decimal('999.99'))
        ]
        
        for float_val, expected_decimal in test_values:
            converted = MonetaryMigrationService.convert_float_to_decimal(float_val)
            self.assertEqual(converted, expected_decimal)

if __name__ == '__main__':
    # Cria diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    # Executa os testes
    unittest.main(verbosity=2)