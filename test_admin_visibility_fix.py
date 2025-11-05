#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para verificar a correção da visibilidade do admin para recebimento de tokens
Tarefa 9.6: Corrigir visibilidade do admin para recebimento de tokens
"""

import unittest
from app import app
from models import db, User, AdminUser, Wallet, Transaction
from services.wallet_service import WalletService

class TestAdminVisibilityFix(unittest.TestCase):
    """Testes para verificar a correção da visibilidade do admin"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Criar admin principal (ID 0)
        admin_principal = AdminUser(
            id=0,
            email='admin@sistema.com',
            papel='super_admin'
        )
        admin_principal.set_password('admin123')
        db.session.add(admin_principal)
        
        # Criar outros admins
        admin1 = AdminUser(email='admin1@teste.com', papel='admin')
        admin1.set_password('admin123')
        db.session.add(admin1)
        
        admin2 = AdminUser(email='admin2@teste.com', papel='admin')
        admin2.set_password('admin123')
        db.session.add(admin2)
        
        # Criar usuários normais
        user1 = User(
            nome='Cliente Teste',
            email='cliente@teste.com',
            cpf='12345678901',
            roles='cliente'
        )
        user1.set_password('user123')
        db.session.add(user1)
        
        user2 = User(
            nome='Prestador Teste',
            email='prestador@teste.com',
            cpf='10987654321',
            roles='prestador'
        )
        user2.set_password('user123')
        db.session.add(user2)
        
        db.session.commit()
        
        # Garantir que admin principal tem carteira
        WalletService.ensure_admin_has_wallet()
        
        # Criar carteiras para outros usuários
        WalletService.ensure_user_has_wallet(user1.id)
        WalletService.ensure_user_has_wallet(user2.id)
        WalletService.ensure_user_has_wallet(admin1.id)
        WalletService.ensure_user_has_wallet(admin2.id)
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_admin_principal_exists(self):
        """Testa se admin principal (ID 0) existe"""
        admin = AdminUser.query.get(0)
        self.assertIsNotNone(admin)
        self.assertEqual(admin.email, 'admin@sistema.com')
        self.assertEqual(admin.papel, 'super_admin')
    
    def test_admin_principal_has_wallet(self):
        """Testa se admin principal tem carteira com tokens iniciais"""
        admin_wallet = Wallet.query.filter_by(user_id=0).first()
        self.assertIsNotNone(admin_wallet)
        self.assertEqual(admin_wallet.balance, 1000000.0)  # 1 milhão de tokens iniciais
    
    def test_admin_appears_in_user_list(self):
        """Testa se AdminUsers aparecem na lista de usuários para receber tokens"""
        # Simular lógica da rota de adicionar tokens
        user_choices = [(u.id, f'{u.nome} ({u.email})') for u in User.query.filter_by(active=True).all()]
        admin_choices = [(a.id, f'[ADMIN] {a.email}') for a in AdminUser.query.all() if a.id != 0]
        all_choices = user_choices + admin_choices
        
        # Verificar se há usuários normais
        self.assertTrue(len(user_choices) >= 2)
        
        # Verificar se há AdminUsers (excluindo o principal)
        self.assertTrue(len(admin_choices) >= 2)
        
        # Verificar se AdminUsers estão marcados corretamente
        admin_emails = [choice[1] for choice in admin_choices]
        self.assertTrue(any('[ADMIN] admin1@teste.com' in email for email in admin_emails))
        self.assertTrue(any('[ADMIN] admin2@teste.com' in email for email in admin_emails))
        
        # Verificar que admin principal (ID 0) não aparece na lista
        admin_ids = [choice[0] for choice in admin_choices]
        self.assertNotIn(0, admin_ids)
    
    def test_transfer_tokens_between_admins(self):
        """Testa transferência de tokens entre admins"""
        # Dar tokens para admin1 primeiro
        admin1 = AdminUser.query.filter_by(email='admin1@teste.com').first()
        WalletService.admin_sell_tokens_to_user(admin1.id, 5000, 'Tokens iniciais')
        
        # Verificar saldos antes
        admin_principal_antes = WalletService.get_admin_wallet_info()
        admin1_antes = WalletService.get_wallet_info(admin1.id)
        
        # Transferir tokens do admin1 para admin principal
        result = WalletService.transfer_tokens_between_users(
            from_user_id=admin1.id,
            to_user_id=0,
            amount=1000,
            description='Teste de transferência'
        )
        
        # Verificar resultado
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['from_transaction_id'])
        self.assertIsNotNone(result['to_transaction_id'])
        
        # Verificar saldos depois
        admin_principal_depois = WalletService.get_admin_wallet_info()
        admin1_depois = WalletService.get_wallet_info(admin1.id)
        
        self.assertEqual(admin_principal_depois['balance'], admin_principal_antes['balance'] + 1000)
        self.assertEqual(admin1_depois['balance'], admin1_antes['balance'] - 1000)
    
    def test_transfer_validation(self):
        """Testa validações na transferência de tokens"""
        admin1 = AdminUser.query.filter_by(email='admin1@teste.com').first()
        
        # Teste 1: Valor negativo
        with self.assertRaises(ValueError):
            WalletService.transfer_tokens_between_users(admin1.id, 0, -100, 'Teste')
        
        # Teste 2: Mesmo usuário
        with self.assertRaises(ValueError):
            WalletService.transfer_tokens_between_users(admin1.id, admin1.id, 100, 'Teste')
        
        # Teste 3: Saldo insuficiente
        with self.assertRaises(ValueError):
            WalletService.transfer_tokens_between_users(admin1.id, 0, 10000, 'Teste')
    
    def test_transaction_logging(self):
        """Testa se as transações são registradas corretamente"""
        admin1 = AdminUser.query.filter_by(email='admin1@teste.com').first()
        
        # Dar tokens para admin1
        WalletService.admin_sell_tokens_to_user(admin1.id, 2000, 'Tokens para teste')
        
        # Transferir para admin principal
        result = WalletService.transfer_tokens_between_users(
            from_user_id=admin1.id,
            to_user_id=0,
            amount=500,
            description='Teste de logging'
        )
        
        # Verificar transações registradas
        from_transaction = Transaction.query.get(result['from_transaction_id'])
        to_transaction = Transaction.query.get(result['to_transaction_id'])
        
        # Verificar transação de saída
        self.assertEqual(from_transaction.user_id, admin1.id)
        self.assertEqual(from_transaction.type, 'transferencia_enviada')
        self.assertEqual(from_transaction.amount, -500)
        self.assertEqual(from_transaction.related_user_id, 0)
        
        # Verificar transação de entrada
        self.assertEqual(to_transaction.user_id, 0)
        self.assertEqual(to_transaction.type, 'transferencia_recebida')
        self.assertEqual(to_transaction.amount, 500)
        self.assertEqual(to_transaction.related_user_id, admin1.id)
    
    def test_admin_wallet_creation_for_existing_admins(self):
        """Testa criação de carteiras para AdminUsers existentes"""
        admin1 = AdminUser.query.filter_by(email='admin1@teste.com').first()
        admin2 = AdminUser.query.filter_by(email='admin2@teste.com').first()
        
        # Verificar se carteiras foram criadas
        wallet1 = Wallet.query.filter_by(user_id=admin1.id).first()
        wallet2 = Wallet.query.filter_by(user_id=admin2.id).first()
        
        self.assertIsNotNone(wallet1)
        self.assertIsNotNone(wallet2)
        self.assertEqual(wallet1.balance, 0.0)  # Admins secundários começam com 0
        self.assertEqual(wallet2.balance, 0.0)

if __name__ == '__main__':
    print("🧪 Executando testes da correção de visibilidade do admin...")
    unittest.main(verbosity=2)