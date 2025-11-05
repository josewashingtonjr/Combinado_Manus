#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, Wallet, Transaction, db
from services.wallet_service import WalletService

class TestWalletCreation(unittest.TestCase):
    """Testes para criação automática de carteiras"""
    
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
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_wallet_for_new_user(self):
        """Testa criação de carteira para novo usuário"""
        # Criar usuário
        user = User(
            nome='Teste User',
            email='teste@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Verificar que não tem carteira inicialmente
        self.assertIsNone(Wallet.query.filter_by(user_id=user.id).first())
        
        # Criar carteira
        wallet = WalletService.ensure_user_has_wallet(user.id)
        
        # Verificar que carteira foi criada
        self.assertIsNotNone(wallet)
        self.assertEqual(wallet.user_id, user.id)
        self.assertEqual(wallet.balance, 0.0)
        self.assertEqual(wallet.escrow_balance, 0.0)
        
        # Verificar que transação inicial foi criada
        transaction = Transaction.query.filter_by(
            user_id=user.id, 
            type="criacao_carteira"
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, 0.0)
        self.assertEqual(transaction.description, "Carteira criada automaticamente")
    
    def test_ensure_wallet_for_existing_wallet(self):
        """Testa que não cria carteira duplicada para usuário que já tem"""
        # Criar usuário
        user = User(
            nome='Teste User',
            email='teste@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira manualmente
        wallet1 = Wallet(user_id=user.id, balance=100.0)
        db.session.add(wallet1)
        db.session.commit()
        
        # Tentar criar carteira novamente
        wallet2 = WalletService.ensure_user_has_wallet(user.id)
        
        # Verificar que retornou a mesma carteira
        self.assertEqual(wallet1.id, wallet2.id)
        self.assertEqual(wallet2.balance, 100.0)
        
        # Verificar que só existe uma carteira
        wallets = Wallet.query.filter_by(user_id=user.id).all()
        self.assertEqual(len(wallets), 1)
    
    def test_ensure_wallet_invalid_user(self):
        """Testa erro ao tentar criar carteira para usuário inexistente"""
        with self.assertRaises(ValueError) as context:
            WalletService.ensure_user_has_wallet(999)
        
        self.assertIn("Usuário com ID 999 não encontrado", str(context.exception))
    
    def test_validate_all_users_have_wallets(self):
        """Testa validação de usuários sem carteiras"""
        # Criar usuários
        user1 = User(nome='User 1', email='user1@test.com', cpf='11111111111', roles='cliente')
        user1.set_password('123456')
        
        user2 = User(nome='User 2', email='user2@test.com', cpf='22222222222', roles='prestador')
        user2.set_password('123456')
        
        user3 = User(nome='User 3', email='user3@test.com', cpf='33333333333', roles='cliente', active=False)
        user3.set_password('123456')
        
        db.session.add_all([user1, user2, user3])
        db.session.commit()
        
        # Criar carteira apenas para user1
        wallet1 = Wallet(user_id=user1.id)
        db.session.add(wallet1)
        db.session.commit()
        
        # Validar usuários sem carteiras
        users_without_wallets = WalletService.validate_all_users_have_wallets()
        
        # Deve retornar apenas user2 (user3 está inativo)
        self.assertEqual(len(users_without_wallets), 1)
        self.assertEqual(users_without_wallets[0].id, user2.id)
    
    def test_create_missing_wallets(self):
        """Testa criação de carteiras faltantes em lote"""
        # Criar usuários
        user1 = User(nome='User 1', email='user1@test.com', cpf='11111111111', roles='cliente')
        user1.set_password('123456')
        
        user2 = User(nome='User 2', email='user2@test.com', cpf='22222222222', roles='prestador')
        user2.set_password('123456')
        
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Verificar que não têm carteiras
        self.assertEqual(len(Wallet.query.all()), 0)
        
        # Criar carteiras faltantes
        created_count = WalletService.create_missing_wallets()
        
        # Verificar que foram criadas 2 carteiras
        self.assertEqual(created_count, 2)
        self.assertEqual(len(Wallet.query.all()), 2)
        
        # Verificar que todos os usuários agora têm carteiras
        users_without_wallets = WalletService.validate_all_users_have_wallets()
        self.assertEqual(len(users_without_wallets), 0)
    
    def test_wallet_relationship_with_user(self):
        """Testa relacionamento entre usuário e carteira"""
        # Criar usuário
        user = User(
            nome='Teste User',
            email='teste@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('123456')
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira
        wallet = WalletService.ensure_user_has_wallet(user.id)
        
        # Verificar relacionamento
        self.assertEqual(user.wallet.id, wallet.id)
        self.assertEqual(wallet.user.id, user.id)

if __name__ == '__main__':
    unittest.main()