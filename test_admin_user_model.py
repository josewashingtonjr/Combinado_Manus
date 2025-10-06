#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, AdminUser, Wallet, Transaction, db
from services.wallet_service import WalletService

class TestAdminUserModel(unittest.TestCase):
    """Testes específicos para modelo AdminUser e relacionamento com carteira ID 0"""
    
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
    
    def test_admin_user_creation(self):
        """Testa criação do modelo AdminUser"""
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        # Verificar que admin foi criado corretamente
        saved_admin = AdminUser.query.get(0)
        self.assertIsNotNone(saved_admin)
        self.assertEqual(saved_admin.email, 'admin@test.com')
        self.assertEqual(saved_admin.papel, 'super_admin')
        self.assertTrue(saved_admin.check_password('admin123'))
        self.assertFalse(saved_admin.check_password('wrong_password'))
    
    def test_admin_user_id_zero_reserved(self):
        """Testa que ID 0 é reservado para admin principal"""
        # Criar admin com ID 0
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Verificar que ID 0 está ocupado
        self.assertEqual(AdminUser.query.get(0).id, 0)
        
        # Verificar que é o único admin com ID 0
        admins_with_id_zero = AdminUser.query.filter_by(id=0).all()
        self.assertEqual(len(admins_with_id_zero), 1)
    
    def test_admin_user_password_hashing(self):
        """Testa hash de senhas do AdminUser"""
        admin = AdminUser(
            email='admin@test.com',
            papel='admin'
        )
        
        # Testar set_password
        admin.set_password('my_secure_password')
        self.assertIsNotNone(admin.password_hash)
        self.assertNotEqual(admin.password_hash, 'my_secure_password')  # Deve estar hasheada
        
        # Testar check_password
        self.assertTrue(admin.check_password('my_secure_password'))
        self.assertFalse(admin.check_password('wrong_password'))
        self.assertFalse(admin.check_password(''))
    
    def test_admin_user_different_roles(self):
        """Testa diferentes papéis de AdminUser"""
        # Admin regular
        admin1 = AdminUser(
            email='admin1@test.com',
            papel='admin'
        )
        admin1.set_password('123456')
        
        # Super admin
        admin2 = AdminUser(
            email='admin2@test.com',
            papel='super_admin'
        )
        admin2.set_password('123456')
        
        # Admin financeiro
        admin3 = AdminUser(
            email='admin3@test.com',
            papel='admin_financeiro'
        )
        admin3.set_password('123456')
        
        db.session.add_all([admin1, admin2, admin3])
        db.session.commit()
        
        # Verificar que todos foram salvos com papéis corretos
        self.assertEqual(AdminUser.query.filter_by(papel='admin').count(), 1)
        self.assertEqual(AdminUser.query.filter_by(papel='super_admin').count(), 1)
        self.assertEqual(AdminUser.query.filter_by(papel='admin_financeiro').count(), 1)
    
    def test_admin_user_wallet_relationship(self):
        """Testa relacionamento entre AdminUser e Wallet"""
        # Criar admin
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Criar carteira do admin
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar relacionamento
        self.assertEqual(admin_wallet.user_id, admin.id)
        self.assertEqual(admin_wallet.user_id, 0)
        
        # Verificar que carteira foi criada corretamente
        self.assertIsNotNone(admin_wallet)
        self.assertEqual(admin_wallet.balance, 1000000.0)  # Saldo inicial
    
    def test_admin_user_unique_email(self):
        """Testa que email do AdminUser deve ser único"""
        # Criar primeiro admin
        admin1 = AdminUser(
            email='admin@test.com',
            papel='admin'
        )
        admin1.set_password('123456')
        db.session.add(admin1)
        db.session.commit()
        
        # Tentar criar segundo admin com mesmo email
        admin2 = AdminUser(
            email='admin@test.com',  # Email duplicado
            papel='super_admin'
        )
        admin2.set_password('654321')
        db.session.add(admin2)
        
        # Deve gerar erro de integridade
        with self.assertRaises(Exception):  # SQLAlchemy IntegrityError
            db.session.commit()
    
    def test_admin_user_repr(self):
        """Testa representação string do AdminUser"""
        admin = AdminUser(
            email='admin@test.com',
            papel='super_admin'
        )
        
        expected_repr = '<AdminUser admin@test.com>'
        self.assertEqual(repr(admin), expected_repr)
    
    def test_admin_user_vs_regular_user_distinction(self):
        """Testa distinção entre AdminUser e User regular"""
        # Criar AdminUser
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        
        # Criar User regular
        user = User(
            nome='User Regular',
            email='user@test.com',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('user123')
        
        db.session.add_all([admin, user])
        db.session.commit()
        
        # Verificar que são modelos diferentes
        self.assertIsInstance(admin, AdminUser)
        self.assertIsInstance(user, User)
        self.assertNotIsInstance(admin, User)
        self.assertNotIsInstance(user, AdminUser)
        
        # Verificar que têm tabelas diferentes
        self.assertEqual(AdminUser.query.count(), 1)
        self.assertEqual(User.query.count(), 1)
        
        # Verificar que admin tem ID 0 e user tem ID diferente
        self.assertEqual(admin.id, 0)
        self.assertNotEqual(user.id, 0)
    
    def test_admin_wallet_creation_automatic(self):
        """Testa criação automática de carteira para admin"""
        # Criar admin sem carteira
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Verificar que não tem carteira inicialmente
        self.assertIsNone(Wallet.query.filter_by(user_id=0).first())
        
        # Chamar ensure_admin_has_wallet
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar que carteira foi criada
        self.assertIsNotNone(admin_wallet)
        self.assertEqual(admin_wallet.user_id, 0)
        self.assertEqual(admin_wallet.balance, 1000000.0)
        
        # Verificar que transação inicial foi criada
        initial_transaction = Transaction.query.filter_by(
            user_id=0,
            type="criacao_tokens"
        ).first()
        self.assertIsNotNone(initial_transaction)
        self.assertEqual(initial_transaction.amount, 1000000.0)
    
    def test_admin_wallet_not_duplicated(self):
        """Testa que carteira do admin não é duplicada"""
        # Criar admin
        admin = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Criar carteira múltiplas vezes
        wallet1 = WalletService.ensure_admin_has_wallet()
        wallet2 = WalletService.ensure_admin_has_wallet()
        wallet3 = WalletService.ensure_admin_has_wallet()
        
        # Verificar que é sempre a mesma carteira
        self.assertEqual(wallet1.id, wallet2.id)
        self.assertEqual(wallet2.id, wallet3.id)
        
        # Verificar que só existe uma carteira para admin
        admin_wallets = Wallet.query.filter_by(user_id=0).all()
        self.assertEqual(len(admin_wallets), 1)
    
    def test_admin_user_without_admin_in_database(self):
        """Testa erro quando admin não existe no banco"""
        # Não criar admin no banco
        
        # Tentar criar carteira do admin
        with self.assertRaises(ValueError) as context:
            WalletService.ensure_admin_has_wallet()
        
        self.assertIn("Admin principal não encontrado", str(context.exception))
    
    def test_admin_user_fields_validation(self):
        """Testa validação de campos obrigatórios do AdminUser"""
        # Testar criação sem email
        with self.assertRaises(Exception):
            admin = AdminUser(papel='admin')
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
    
    def test_admin_user_default_papel(self):
        """Testa valor padrão do campo papel"""
        admin = AdminUser(email='admin@test.com')
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
        
        # Verificar valor padrão após salvar no banco
        saved_admin = AdminUser.query.filter_by(email='admin@test.com').first()
        self.assertEqual(saved_admin.papel, 'admin')
    
    def test_multiple_admin_users_different_ids(self):
        """Testa criação de múltiplos AdminUsers com IDs diferentes"""
        # Admin principal (ID 0)
        admin_principal = AdminUser(
            id=0,
            email='admin@test.com',
            papel='super_admin'
        )
        admin_principal.set_password('admin123')
        
        # Admin secundário (ID automático)
        admin_secundario = AdminUser(
            email='admin2@test.com',
            papel='admin'
        )
        admin_secundario.set_password('admin456')
        
        db.session.add_all([admin_principal, admin_secundario])
        db.session.commit()
        
        # Verificar que foram criados com IDs diferentes
        self.assertEqual(admin_principal.id, 0)
        self.assertNotEqual(admin_secundario.id, 0)
        self.assertIsNotNone(admin_secundario.id)
        
        # Verificar que ambos existem
        self.assertEqual(AdminUser.query.count(), 2)
        
        # Verificar que apenas o admin principal (ID 0) pode ter carteira de tokens
        admin_wallet = WalletService.ensure_admin_has_wallet()
        self.assertEqual(admin_wallet.user_id, 0)

if __name__ == '__main__':
    unittest.main()