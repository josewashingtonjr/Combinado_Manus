#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, Wallet, Transaction, db
from services.wallet_service import WalletService

class TestWalletOperations(unittest.TestCase):
    """Testes para operações básicas de carteira"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        # Criar app Flask isolado para testes
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Inicializar db com o app de teste
        db.init_app(self.app)
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Criar todas as tabelas
        db.create_all()
        
        # Criar usuário de teste
        self.user = User(
            nome='Teste User',
            email='teste@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        self.user.set_password('123456')
        db.session.add(self.user)
        db.session.commit()
        
        # Criar carteira para o usuário
        self.wallet = WalletService.ensure_user_has_wallet(self.user.id)
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_get_wallet_balance(self):
        """Testa obtenção do saldo da carteira"""
        balance = WalletService.get_wallet_balance(self.user.id)
        self.assertEqual(balance, 0.0)
    
    def test_get_wallet_info(self):
        """Testa obtenção de informações completas da carteira"""
        info = WalletService.get_wallet_info(self.user.id)
        
        self.assertIn('balance', info)
        self.assertIn('escrow_balance', info)
        self.assertIn('total_balance', info)
        self.assertIn('updated_at', info)
        
        self.assertEqual(info['balance'], 0.0)
        self.assertEqual(info['escrow_balance'], 0.0)
        self.assertEqual(info['total_balance'], 0.0)
    
    def test_has_sufficient_balance(self):
        """Testa verificação de saldo suficiente"""
        # Saldo inicial é 0
        self.assertFalse(WalletService.has_sufficient_balance(self.user.id, 10.0))
        
        # Depositar dinheiro
        WalletService.deposit(self.user.id, 100.0, "Depósito teste")
        
        # Agora deve ter saldo suficiente
        self.assertTrue(WalletService.has_sufficient_balance(self.user.id, 50.0))
        self.assertTrue(WalletService.has_sufficient_balance(self.user.id, 100.0))
        self.assertFalse(WalletService.has_sufficient_balance(self.user.id, 150.0))
    
    def test_credit_wallet(self):
        """Testa operação de crédito na carteira"""
        result = WalletService.credit_wallet(
            self.user.id, 
            50.0, 
            "Crédito teste", 
            "teste_credito"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], 50.0)
        self.assertIsNotNone(result['transaction_id'])
        
        # Verificar se a transação foi registrada
        transaction = Transaction.query.get(result['transaction_id'])
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.type, "teste_credito")
        self.assertEqual(transaction.amount, 50.0)
        self.assertEqual(transaction.description, "Crédito teste")
    
    def test_debit_wallet(self):
        """Testa operação de débito na carteira"""
        # Primeiro, adicionar saldo
        WalletService.credit_wallet(self.user.id, 100.0, "Saldo inicial")
        
        # Debitar valor
        result = WalletService.debit_wallet(
            self.user.id, 
            30.0, 
            "Débito teste", 
            "teste_debito"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], 70.0)
        self.assertIsNotNone(result['transaction_id'])
        
        # Verificar se a transação foi registrada
        transaction = Transaction.query.get(result['transaction_id'])
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.type, "teste_debito")
        self.assertEqual(transaction.amount, -30.0)  # Valor negativo para débito
        self.assertEqual(transaction.description, "Débito teste")
    
    def test_debit_wallet_insufficient_balance(self):
        """Testa débito com saldo insuficiente"""
        # Tentar debitar mais do que tem
        with self.assertRaises(ValueError) as context:
            WalletService.debit_wallet(self.user.id, 50.0, "Débito inválido")
        
        self.assertIn("Saldo insuficiente", str(context.exception))
    
    def test_debit_wallet_force(self):
        """Testa débito forçado mesmo com saldo insuficiente"""
        # Debitar com force=True
        result = WalletService.debit_wallet(
            self.user.id, 
            50.0, 
            "Débito forçado", 
            "teste_debito_forcado",
            force=True
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], -50.0)  # Saldo negativo
    
    def test_deposit(self):
        """Testa operação de depósito"""
        result = WalletService.deposit(self.user.id, 75.0, "Depósito teste")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], 75.0)
        
        # Verificar saldo
        balance = WalletService.get_wallet_balance(self.user.id)
        self.assertEqual(balance, 75.0)
    
    def test_withdraw(self):
        """Testa operação de saque"""
        # Primeiro depositar
        WalletService.deposit(self.user.id, 100.0, "Depósito inicial")
        
        # Sacar
        result = WalletService.withdraw(self.user.id, 40.0, "Saque teste")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], 60.0)
        
        # Verificar saldo
        balance = WalletService.get_wallet_balance(self.user.id)
        self.assertEqual(balance, 60.0)
    
    def test_transfer_to_escrow(self):
        """Testa transferência para escrow"""
        # Adicionar saldo inicial
        WalletService.deposit(self.user.id, 100.0, "Saldo inicial")
        
        # Transferir para escrow
        result = WalletService.transfer_to_escrow(self.user.id, 60.0, 1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_balance'], 40.0)
        self.assertEqual(result['new_escrow_balance'], 60.0)
        
        # Verificar saldos
        info = WalletService.get_wallet_info(self.user.id)
        self.assertEqual(info['balance'], 40.0)
        self.assertEqual(info['escrow_balance'], 60.0)
        self.assertEqual(info['total_balance'], 100.0)
    
    def test_transfer_to_escrow_insufficient_balance(self):
        """Testa transferência para escrow com saldo insuficiente"""
        with self.assertRaises(ValueError) as context:
            WalletService.transfer_to_escrow(self.user.id, 50.0, 1)
        
        self.assertIn("Saldo insuficiente para transferir para escrow", str(context.exception))
    
    def test_get_escrow_balance(self):
        """Testa obtenção do saldo em escrow"""
        # Saldo inicial em escrow deve ser 0
        escrow_balance = WalletService.get_escrow_balance(self.user.id)
        self.assertEqual(escrow_balance, 0.0)
        
        # Adicionar saldo e transferir para escrow
        WalletService.deposit(self.user.id, 100.0, "Saldo inicial")
        WalletService.transfer_to_escrow(self.user.id, 30.0, 1)
        
        # Verificar saldo em escrow
        escrow_balance = WalletService.get_escrow_balance(self.user.id)
        self.assertEqual(escrow_balance, 30.0)
    
    def test_has_sufficient_escrow(self):
        """Testa verificação de saldo suficiente em escrow"""
        # Inicialmente não tem saldo em escrow
        self.assertFalse(WalletService.has_sufficient_escrow(self.user.id, 10.0))
        
        # Adicionar saldo e transferir para escrow
        WalletService.deposit(self.user.id, 100.0, "Saldo inicial")
        WalletService.transfer_to_escrow(self.user.id, 50.0, 1)
        
        # Verificar saldo suficiente em escrow
        self.assertTrue(WalletService.has_sufficient_escrow(self.user.id, 30.0))
        self.assertTrue(WalletService.has_sufficient_escrow(self.user.id, 50.0))
        self.assertFalse(WalletService.has_sufficient_escrow(self.user.id, 60.0))
    
    def test_invalid_amounts(self):
        """Testa operações com valores inválidos"""
        # Valores negativos ou zero devem gerar erro
        with self.assertRaises(ValueError):
            WalletService.credit_wallet(self.user.id, -10.0, "Crédito inválido")
        
        with self.assertRaises(ValueError):
            WalletService.credit_wallet(self.user.id, 0.0, "Crédito zero")
        
        with self.assertRaises(ValueError):
            WalletService.debit_wallet(self.user.id, -10.0, "Débito inválido")
        
        with self.assertRaises(ValueError):
            WalletService.debit_wallet(self.user.id, 0.0, "Débito zero")
    
    def test_wallet_not_found(self):
        """Testa operações com carteira inexistente"""
        with self.assertRaises(ValueError) as context:
            WalletService.get_wallet_balance(999)
        
        self.assertIn("Carteira não encontrada", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            WalletService.credit_wallet(999, 10.0, "Teste")
        
        self.assertIn("Carteira não encontrada", str(context.exception))

if __name__ == '__main__':
    unittest.main()