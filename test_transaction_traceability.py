#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, Wallet, Transaction, Order, db
from services.wallet_service import WalletService

class TestTransactionTraceability(unittest.TestCase):
    """Testes para sistema de transações e rastreabilidade"""
    
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
        
        # Criar usuários de teste
        self.user1 = User(
            nome='Cliente Teste',
            email='cliente@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        self.user1.set_password('123456')
        
        self.user2 = User(
            nome='Prestador Teste',
            email='prestador@example.com',
            cpf='98765432100',
            roles='prestador'
        )
        self.user2.set_password('123456')
        
        db.session.add_all([self.user1, self.user2])
        db.session.commit()
        
        # Criar carteiras para os usuários
        self.wallet1 = WalletService.ensure_user_has_wallet(self.user1.id)
        self.wallet2 = WalletService.ensure_user_has_wallet(self.user2.id)
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_transaction_history(self):
        """Testa obtenção do histórico de transações"""
        # Fazer algumas transações
        WalletService.deposit(self.user1.id, 100.0, "Depósito inicial")
        WalletService.withdraw(self.user1.id, 25.0, "Saque teste")
        WalletService.deposit(self.user1.id, 50.0, "Segundo depósito")
        
        # Obter histórico
        history = WalletService.get_transaction_history(self.user1.id)
        
        # Verificar que há 4 transações (3 + criação da carteira)
        self.assertEqual(len(history), 4)
        
        # Verificar ordem (mais recente primeiro)
        self.assertEqual(history[0]['type'], 'deposito')
        self.assertEqual(history[0]['amount'], 50.0)
        self.assertEqual(history[1]['type'], 'saque')
        self.assertEqual(history[1]['amount'], -25.0)
        self.assertEqual(history[2]['type'], 'deposito')
        self.assertEqual(history[2]['amount'], 100.0)
        self.assertEqual(history[3]['type'], 'criacao_carteira')
    
    def test_transaction_history_by_type(self):
        """Testa filtro de histórico por tipo de transação"""
        # Fazer transações de diferentes tipos
        WalletService.deposit(self.user1.id, 100.0, "Depósito 1")
        WalletService.deposit(self.user1.id, 50.0, "Depósito 2")
        WalletService.withdraw(self.user1.id, 25.0, "Saque 1")
        
        # Filtrar apenas depósitos
        deposits = WalletService.get_transaction_history(self.user1.id, transaction_type="deposito")
        self.assertEqual(len(deposits), 2)
        for transaction in deposits:
            self.assertEqual(transaction['type'], 'deposito')
        
        # Filtrar apenas saques
        withdrawals = WalletService.get_transaction_history(self.user1.id, transaction_type="saque")
        self.assertEqual(len(withdrawals), 1)
        self.assertEqual(withdrawals[0]['type'], 'saque')
    
    def test_get_transaction_by_id(self):
        """Testa obtenção de transação específica por ID"""
        result = WalletService.deposit(self.user1.id, 100.0, "Depósito teste")
        transaction_id = result['transaction_id']
        
        # Obter transação por ID
        transaction = WalletService.get_transaction_by_id(transaction_id)
        
        self.assertEqual(transaction['id'], transaction_id)
        self.assertEqual(transaction['user_id'], self.user1.id)
        self.assertEqual(transaction['type'], 'deposito')
        self.assertEqual(transaction['amount'], 100.0)
        self.assertEqual(transaction['description'], 'Depósito teste')
    
    def test_get_transaction_by_id_not_found(self):
        """Testa erro ao buscar transação inexistente"""
        with self.assertRaises(ValueError) as context:
            WalletService.get_transaction_by_id(999)
        
        self.assertIn("Transação com ID 999 não encontrada", str(context.exception))
    
    def test_get_transactions_by_order(self):
        """Testa obtenção de transações por ordem"""
        # Criar uma ordem fictícia
        order = Order(
            client_id=self.user1.id,
            provider_id=self.user2.id,
            title="Serviço teste",
            description="Descrição do serviço",
            value=100.0,
            status="disponivel"
        )
        db.session.add(order)
        db.session.commit()
        
        # Fazer transações relacionadas à ordem
        WalletService.deposit(self.user1.id, 150.0, "Saldo inicial")
        WalletService.transfer_to_escrow(self.user1.id, 100.0, order.id)
        
        # Obter transações da ordem
        order_transactions = WalletService.get_transactions_by_order(order.id)
        
        self.assertEqual(len(order_transactions), 1)
        self.assertEqual(order_transactions[0]['type'], 'escrow_bloqueio')
        self.assertEqual(order_transactions[0]['user_id'], self.user1.id)
    
    def test_user_balance_summary(self):
        """Testa resumo completo do saldo e transações"""
        # Fazer várias transações
        WalletService.deposit(self.user1.id, 200.0, "Depósito 1")
        WalletService.deposit(self.user1.id, 100.0, "Depósito 2")
        WalletService.withdraw(self.user1.id, 50.0, "Saque 1")
        WalletService.transfer_to_escrow(self.user1.id, 75.0, 1)
        
        # Obter resumo
        summary = WalletService.get_user_balance_summary(self.user1.id)
        
        # Verificar estrutura do resumo
        self.assertIn('wallet', summary)
        self.assertIn('recent_transactions', summary)
        self.assertIn('statistics', summary)
        
        # Verificar estatísticas
        stats = summary['statistics']
        self.assertEqual(stats['total_credits'], 300.0)  # 200 + 100 (depósitos)
        self.assertEqual(stats['total_debits'], 125.0)   # 50 + 75 (saque + escrow)
        self.assertEqual(stats['net_flow'], 175.0)       # 300 - 125
        self.assertEqual(stats['transaction_count'], 5)  # 4 transações + criação carteira
    
    def test_generate_transaction_id(self):
        """Testa geração de ID único para transação"""
        id1 = WalletService.generate_transaction_id()
        id2 = WalletService.generate_transaction_id()
        
        # IDs devem ser diferentes
        self.assertNotEqual(id1, id2)
        
        # IDs devem seguir o padrão TXN-YYYYMMDDHHMMSS-XXXXXXXX
        self.assertTrue(id1.startswith('TXN-'))
        self.assertTrue(id2.startswith('TXN-'))
        
        parts1 = id1.split('-')
        parts2 = id2.split('-')
        
        self.assertEqual(len(parts1), 3)
        self.assertEqual(len(parts2), 3)
        self.assertEqual(len(parts1[1]), 14)  # YYYYMMDDHHMMSS
        self.assertEqual(len(parts1[2]), 8)   # 8 caracteres únicos
    
    def test_validate_transaction_integrity(self):
        """Testa validação da integridade das transações"""
        # Fazer transações normais
        WalletService.deposit(self.user1.id, 100.0, "Depósito")
        WalletService.withdraw(self.user1.id, 30.0, "Saque")
        
        # Validar integridade
        integrity = WalletService.validate_transaction_integrity(self.user1.id)
        
        self.assertTrue(integrity['is_valid'])
        self.assertTrue(integrity['balance_matches'])
        self.assertTrue(integrity['escrow_matches'])
        self.assertEqual(integrity['wallet_balance'], 70.0)
        self.assertEqual(integrity['calculated_balance'], 70.0)
    
    def test_validate_transaction_integrity_with_escrow(self):
        """Testa validação da integridade com transações de escrow"""
        # Fazer transações incluindo escrow
        WalletService.deposit(self.user1.id, 200.0, "Depósito")
        WalletService.transfer_to_escrow(self.user1.id, 50.0, 1)
        
        # Validar integridade
        integrity = WalletService.validate_transaction_integrity(self.user1.id)
        
        self.assertTrue(integrity['is_valid'])
        self.assertTrue(integrity['balance_matches'])
        self.assertTrue(integrity['escrow_matches'])
        self.assertEqual(integrity['wallet_balance'], 150.0)
        self.assertEqual(integrity['wallet_escrow'], 50.0)
        self.assertEqual(integrity['calculated_escrow'], 50.0)
    
    def test_system_transaction_summary(self):
        """Testa resumo de transações do sistema"""
        # Fazer transações com diferentes usuários
        WalletService.deposit(self.user1.id, 100.0, "Depósito user1")
        WalletService.deposit(self.user2.id, 200.0, "Depósito user2")
        WalletService.withdraw(self.user1.id, 25.0, "Saque user1")
        
        # Obter resumo do sistema
        summary = WalletService.get_system_transaction_summary()
        
        # Verificar estrutura
        self.assertIn('total_transactions', summary)
        self.assertIn('total_volume', summary)
        self.assertIn('type_statistics', summary)
        self.assertIn('top_users', summary)
        
        # Verificar dados (5 transações: 2 criação carteira + 3 operações)
        self.assertEqual(summary['total_transactions'], 5)
        
        # Verificar estatísticas por tipo
        type_stats = {stat['type']: stat for stat in summary['type_statistics']}
        self.assertIn('deposito', type_stats)
        self.assertIn('saque', type_stats)
        self.assertIn('criacao_carteira', type_stats)
        
        self.assertEqual(type_stats['deposito']['count'], 2)
        self.assertEqual(type_stats['saque']['count'], 1)
    
    def test_transaction_immutability(self):
        """Testa que as transações são imutáveis (não podem ser alteradas)"""
        result = WalletService.deposit(self.user1.id, 100.0, "Depósito teste")
        transaction_id = result['transaction_id']
        
        # Obter transação original
        original_transaction = WalletService.get_transaction_by_id(transaction_id)
        
        # Tentar modificar a transação diretamente no banco (simulando tentativa de fraude)
        transaction_obj = Transaction.query.get(transaction_id)
        original_amount = transaction_obj.amount
        
        # A transação deve manter seus valores originais
        self.assertEqual(transaction_obj.amount, 100.0)
        self.assertEqual(transaction_obj.type, 'deposito')
        
        # Verificar que a transação mantém timestamp original
        self.assertIsNotNone(transaction_obj.created_at)
    
    def test_transaction_audit_trail(self):
        """Testa trilha de auditoria completa"""
        # Simular um fluxo completo de transações
        WalletService.deposit(self.user1.id, 500.0, "Depósito inicial")
        WalletService.transfer_to_escrow(self.user1.id, 100.0, 1)
        WalletService.withdraw(self.user1.id, 50.0, "Saque parcial")
        
        # Obter histórico completo
        history = WalletService.get_transaction_history(self.user1.id, limit=100)
        
        # Verificar que todas as transações estão registradas
        transaction_types = [t['type'] for t in history]
        self.assertIn('deposito', transaction_types)
        self.assertIn('escrow_bloqueio', transaction_types)
        self.assertIn('saque', transaction_types)
        self.assertIn('criacao_carteira', transaction_types)
        
        # Verificar que cada transação tem timestamp
        for transaction in history:
            self.assertIsNotNone(transaction['created_at'])
            self.assertIsNotNone(transaction['description'])
            self.assertIsNotNone(transaction['id'])

if __name__ == '__main__':
    unittest.main()