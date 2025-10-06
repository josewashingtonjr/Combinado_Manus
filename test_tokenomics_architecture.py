#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, AdminUser, Wallet, Transaction, Order, db
from services.wallet_service import WalletService

class TestTokenomicsArchitecture(unittest.TestCase):
    """Testes específicos para arquitetura de tokenomics com admin como fonte central"""
    
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
        
        # Criar admin principal (ID 0)
        self.admin = AdminUser(
            id=0,  # ID 0 reservado para admin principal
            email='admin@combinado.com',
            papel='super_admin'
        )
        self.admin.set_password('admin123')
        db.session.add(self.admin)
        
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
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_admin_wallet_creation_with_initial_tokens(self):
        """Testa criação da carteira do admin com tokens iniciais"""
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar que carteira foi criada com saldo inicial
        self.assertIsNotNone(admin_wallet)
        self.assertEqual(admin_wallet.user_id, WalletService.ADMIN_USER_ID)
        self.assertEqual(admin_wallet.balance, 1000000.0)  # 1 milhão de tokens
        self.assertEqual(admin_wallet.escrow_balance, 0.0)
        
        # Verificar que transação de criação inicial foi registrada
        creation_transaction = Transaction.query.filter_by(
            user_id=WalletService.ADMIN_USER_ID,
            type="criacao_tokens"
        ).first()
        
        self.assertIsNotNone(creation_transaction)
        self.assertEqual(creation_transaction.amount, 1000000.0)
        self.assertEqual(creation_transaction.description, "Criação inicial de tokens do sistema")
    
    def test_admin_as_unique_token_creator(self):
        """Testa que apenas o admin pode criar tokens do zero"""
        # Admin cria tokens
        result = WalletService.admin_create_tokens(50000.0, "Criação adicional de tokens")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['tokens_created'], 50000.0)
        
        # Verificar que saldo do admin aumentou
        admin_wallet = WalletService.get_admin_wallet_info()
        self.assertEqual(admin_wallet['balance'], 1050000.0)  # 1M inicial + 50K criados
        
        # Verificar que transação foi registrada
        transaction = Transaction.query.get(result['transaction_id'])
        self.assertEqual(transaction.type, "criacao_tokens")
        self.assertEqual(transaction.user_id, WalletService.ADMIN_USER_ID)
    
    def test_admin_to_user_token_flow(self):
        """Testa fluxo de tokens do admin para usuário (venda)"""
        # Garantir que admin tem carteira
        WalletService.ensure_admin_has_wallet()
        
        # Garantir que usuário tem carteira
        user_wallet = WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Admin vende tokens para usuário
        result = WalletService.admin_sell_tokens_to_user(
            self.user1.id, 
            1000.0, 
            "Compra de tokens pelo usuário"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['tokens_transferred'], 1000.0)
        self.assertEqual(result['admin_new_balance'], 999000.0)  # 1M - 1K
        self.assertEqual(result['user_new_balance'], 1000.0)
        
        # Verificar transações registradas
        admin_transaction = Transaction.query.get(result['admin_transaction_id'])
        user_transaction = Transaction.query.get(result['user_transaction_id'])
        
        self.assertEqual(admin_transaction.type, "venda_tokens")
        self.assertEqual(admin_transaction.amount, -1000.0)  # Saída do admin
        self.assertEqual(admin_transaction.related_user_id, self.user1.id)
        
        self.assertEqual(user_transaction.type, "compra_tokens")
        self.assertEqual(user_transaction.amount, 1000.0)  # Entrada do usuário
        self.assertEqual(user_transaction.related_user_id, WalletService.ADMIN_USER_ID)
    
    def test_user_to_admin_token_flow(self):
        """Testa fluxo de tokens do usuário para admin (saque)"""
        # Preparar: admin vende tokens para usuário primeiro
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.admin_sell_tokens_to_user(self.user1.id, 2000.0, "Compra inicial")
        
        # Usuário vende tokens de volta para admin
        result = WalletService.user_sell_tokens_to_admin(
            self.user1.id,
            500.0,
            "Saque de tokens"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['tokens_transferred'], 500.0)
        self.assertEqual(result['user_new_balance'], 1500.0)  # 2K - 500
        self.assertEqual(result['admin_new_balance'], 998500.0)  # 998K + 500
        
        # Verificar transações registradas
        user_transaction = Transaction.query.get(result['user_transaction_id'])
        admin_transaction = Transaction.query.get(result['admin_transaction_id'])
        
        self.assertEqual(user_transaction.type, "saque_tokens")
        self.assertEqual(user_transaction.amount, -500.0)  # Saída do usuário
        self.assertEqual(user_transaction.related_user_id, WalletService.ADMIN_USER_ID)
        
        self.assertEqual(admin_transaction.type, "recompra_tokens")
        self.assertEqual(admin_transaction.amount, 500.0)  # Entrada do admin
        self.assertEqual(admin_transaction.related_user_id, self.user1.id)
    
    def test_admin_insufficient_tokens_error(self):
        """Testa erro quando admin não tem tokens suficientes"""
        # Garantir que admin tem carteira
        WalletService.ensure_admin_has_wallet()
        
        # Tentar vender mais tokens do que o admin possui
        with self.assertRaises(ValueError) as context:
            WalletService.admin_sell_tokens_to_user(
                self.user1.id,
                2000000.0,  # 2 milhões (mais que o saldo inicial de 1M)
                "Tentativa de venda excessiva"
            )
        
        self.assertIn("Admin não tem tokens suficientes", str(context.exception))
    
    def test_user_insufficient_tokens_error(self):
        """Testa erro quando usuário não tem tokens suficientes para saque"""
        # Preparar usuário com poucos tokens
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.admin_sell_tokens_to_user(self.user1.id, 100.0, "Compra pequena")
        
        # Tentar sacar mais do que possui
        with self.assertRaises(ValueError) as context:
            WalletService.user_sell_tokens_to_admin(
                self.user1.id,
                500.0,  # Mais que os 100 que possui
                "Tentativa de saque excessivo"
            )
        
        self.assertIn("Saldo insuficiente", str(context.exception))
    
    def test_system_token_summary_integrity(self):
        """Testa integridade matemática do resumo de tokens do sistema"""
        # Preparar cenário com múltiplas transações
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.ensure_user_has_wallet(self.user2.id)
        
        # Admin cria tokens adicionais
        WalletService.admin_create_tokens(100000.0, "Criação adicional")
        
        # Admin vende tokens para usuários
        WalletService.admin_sell_tokens_to_user(self.user1.id, 50000.0, "Venda para user1")
        WalletService.admin_sell_tokens_to_user(self.user2.id, 30000.0, "Venda para user2")
        
        # Usuário 1 faz saque parcial
        WalletService.user_sell_tokens_to_admin(self.user1.id, 10000.0, "Saque user1")
        
        # Obter resumo do sistema
        summary = WalletService.get_system_token_summary()
        
        # Verificar integridade matemática
        expected_admin_balance = 1100000.0 - 50000.0 - 30000.0 + 10000.0  # 1030000.0
        expected_circulation = 50000.0 + 30000.0 - 10000.0  # 70000.0
        expected_total_created = 1000000.0 + 100000.0  # 1100000.0
        
        self.assertEqual(summary['admin_balance'], expected_admin_balance)
        self.assertEqual(summary['tokens_in_circulation'], expected_circulation)
        self.assertEqual(summary['total_tokens_created'], expected_total_created)
        self.assertEqual(
            summary['total_tokens_in_system'], 
            expected_admin_balance + expected_circulation
        )
        
        # Verificar que tokens nunca "desaparecem"
        self.assertEqual(summary['total_tokens_in_system'], summary['total_tokens_created'])
    
    def test_deposit_withdraw_wrapper_functions(self):
        """Testa funções wrapper deposit() e withdraw()"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Testar deposit (wrapper para admin_sell_tokens_to_user)
        deposit_result = WalletService.deposit(self.user1.id, 1500.0, "Depósito via wrapper")
        
        self.assertTrue(deposit_result['success'])
        self.assertEqual(deposit_result['user_new_balance'], 1500.0)
        self.assertEqual(deposit_result['admin_new_balance'], 998500.0)
        
        # Testar withdraw (wrapper para user_sell_tokens_to_admin)
        withdraw_result = WalletService.withdraw(self.user1.id, 500.0, "Saque via wrapper")
        
        self.assertTrue(withdraw_result['success'])
        self.assertEqual(withdraw_result['user_new_balance'], 1000.0)
        self.assertEqual(withdraw_result['admin_new_balance'], 999000.0)
    
    def test_multiple_users_token_flows(self):
        """Testa fluxos de tokens com múltiplos usuários"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.ensure_user_has_wallet(self.user2.id)
        
        # Cenário: Admin vende para ambos os usuários
        WalletService.admin_sell_tokens_to_user(self.user1.id, 2000.0, "Venda para user1")
        WalletService.admin_sell_tokens_to_user(self.user2.id, 3000.0, "Venda para user2")
        
        # Verificar saldos
        user1_info = WalletService.get_wallet_info(self.user1.id)
        user2_info = WalletService.get_wallet_info(self.user2.id)
        admin_info = WalletService.get_admin_wallet_info()
        
        self.assertEqual(user1_info['balance'], 2000.0)
        self.assertEqual(user2_info['balance'], 3000.0)
        self.assertEqual(admin_info['balance'], 995000.0)  # 1M - 2K - 3K
        
        # Usuário 1 faz saque
        WalletService.user_sell_tokens_to_admin(self.user1.id, 500.0, "Saque user1")
        
        # Verificar saldos finais
        user1_info_final = WalletService.get_wallet_info(self.user1.id)
        admin_info_final = WalletService.get_admin_wallet_info()
        
        self.assertEqual(user1_info_final['balance'], 1500.0)  # 2K - 500
        self.assertEqual(admin_info_final['balance'], 995500.0)  # 995K + 500
        
        # Verificar integridade total
        summary = WalletService.get_system_token_summary()
        self.assertEqual(summary['total_tokens_in_system'], summary['total_tokens_created'])
    
    def test_admin_user_relationship_with_wallet_id_zero(self):
        """Testa relacionamento específico do AdminUser com carteira ID 0"""
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar que carteira tem user_id = 0 (ADMIN_USER_ID)
        self.assertEqual(admin_wallet.user_id, 0)
        self.assertEqual(admin_wallet.user_id, WalletService.ADMIN_USER_ID)
        
        # Verificar que é a única carteira com user_id = 0
        admin_wallets = Wallet.query.filter_by(user_id=0).all()
        self.assertEqual(len(admin_wallets), 1)
        self.assertEqual(admin_wallets[0].id, admin_wallet.id)
    
    def test_transaction_types_for_tokenomics(self):
        """Testa tipos específicos de transação para tokenomics"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Testar todos os tipos de transação de tokenomics
        WalletService.admin_create_tokens(10000.0, "Teste criação")
        WalletService.admin_sell_tokens_to_user(self.user1.id, 5000.0, "Teste venda")
        WalletService.user_sell_tokens_to_admin(self.user1.id, 1000.0, "Teste recompra")
        
        # Verificar tipos de transação registrados
        admin_transactions = Transaction.query.filter_by(user_id=WalletService.ADMIN_USER_ID).all()
        user_transactions = Transaction.query.filter_by(user_id=self.user1.id).all()
        
        admin_types = [t.type for t in admin_transactions]
        user_types = [t.type for t in user_transactions]
        
        # Admin deve ter: criacao_tokens (inicial + teste), venda_tokens, recompra_tokens
        self.assertIn("criacao_tokens", admin_types)
        self.assertIn("venda_tokens", admin_types)
        self.assertIn("recompra_tokens", admin_types)
        
        # Usuário deve ter: criacao_carteira, compra_tokens, saque_tokens
        self.assertIn("criacao_carteira", user_types)
        self.assertIn("compra_tokens", user_types)
        self.assertIn("saque_tokens", user_types)
    
    def test_tokenomics_with_escrow_integration(self):
        """Testa integração de tokenomics com sistema de escrow"""
        # Preparar usuário com tokens
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.admin_sell_tokens_to_user(self.user1.id, 2000.0, "Compra inicial")
        
        # Transferir tokens para escrow
        escrow_result = WalletService.transfer_to_escrow(self.user1.id, 1000.0, 1)
        
        self.assertTrue(escrow_result['success'])
        self.assertEqual(escrow_result['new_balance'], 1000.0)
        self.assertEqual(escrow_result['new_escrow_balance'], 1000.0)
        
        # Verificar que tokens em escrow não afetam circulação total
        summary = WalletService.get_system_token_summary()
        expected_circulation = 2000.0  # Tokens ainda pertencem ao usuário (saldo + escrow)
        
        self.assertEqual(summary['tokens_in_circulation'], expected_circulation)
        self.assertEqual(summary['total_tokens_in_system'], summary['total_tokens_created'])
    
    def test_admin_wallet_persistence(self):
        """Testa que carteira do admin persiste entre chamadas"""
        # Primeira chamada - criar carteira
        wallet1 = WalletService.ensure_admin_has_wallet()
        original_balance = wallet1.balance
        
        # Modificar saldo
        WalletService.admin_create_tokens(5000.0, "Teste persistência")
        
        # Segunda chamada - deve retornar a mesma carteira
        wallet2 = WalletService.ensure_admin_has_wallet()
        
        self.assertEqual(wallet1.id, wallet2.id)
        self.assertEqual(wallet2.balance, original_balance + 5000.0)
        
        # Verificar que não criou carteira duplicada
        admin_wallets = Wallet.query.filter_by(user_id=WalletService.ADMIN_USER_ID).all()
        self.assertEqual(len(admin_wallets), 1)

if __name__ == '__main__':
    unittest.main()