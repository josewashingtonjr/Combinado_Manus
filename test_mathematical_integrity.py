#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, AdminUser, Wallet, Transaction, Order, db
from services.wallet_service import WalletService

class TestMathematicalIntegrity(unittest.TestCase):
    """Testes para validação de integridade matemática do sistema de tokenomics"""
    
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
        
        # Criar admin principal
        self.admin = AdminUser(
            id=0,
            email='admin@combinado.com',
            papel='super_admin'
        )
        self.admin.set_password('admin123')
        db.session.add(self.admin)
        
        # Criar usuários de teste
        self.users = []
        for i in range(5):
            user = User(
                nome=f'User {i+1}',
                email=f'user{i+1}@test.com',
                cpf=f'{str(i+1).zfill(11)}',
                roles='cliente' if i % 2 == 0 else 'prestador'
            )
            user.set_password('123456')
            self.users.append(user)
        
        db.session.add_all(self.users)
        db.session.commit()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_token_conservation_law(self):
        """Testa lei de conservação de tokens: tokens nunca desaparecem"""
        # Preparar sistema
        WalletService.ensure_admin_has_wallet()
        for user in self.users:
            WalletService.ensure_user_has_wallet(user.id)
        
        # Estado inicial
        initial_summary = WalletService.get_system_token_summary()
        initial_total = initial_summary['total_tokens_created']
        
        # Realizar múltiplas operações
        operations = [
            # Admin cria tokens
            lambda: WalletService.admin_create_tokens(50000.0, "Criação teste"),
            # Admin vende para usuários
            lambda: WalletService.admin_sell_tokens_to_user(self.users[0].id, 10000.0, "Venda 1"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[1].id, 15000.0, "Venda 2"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[2].id, 8000.0, "Venda 3"),
            # Usuários fazem saques
            lambda: WalletService.user_sell_tokens_to_admin(self.users[0].id, 3000.0, "Saque 1"),
            lambda: WalletService.user_sell_tokens_to_admin(self.users[1].id, 5000.0, "Saque 2"),
            # Transferências para escrow
            lambda: WalletService.transfer_to_escrow(self.users[0].id, 2000.0, 1),
            lambda: WalletService.transfer_to_escrow(self.users[2].id, 3000.0, 2),
        ]
        
        # Executar operações e verificar integridade após cada uma
        for i, operation in enumerate(operations):
            operation()
            
            # Verificar integridade após cada operação
            summary = WalletService.get_system_token_summary()
            
            # Lei de conservação: admin_balance + tokens_in_circulation = total_created
            calculated_total = summary['admin_balance'] + summary['tokens_in_circulation']
            
            self.assertAlmostEqual(
                calculated_total, 
                summary['total_tokens_created'], 
                places=2,
                msg=f"Falha na conservação após operação {i+1}"
            )
            
            # Verificar que total de tokens no sistema = total criado
            self.assertAlmostEqual(
                summary['total_tokens_in_system'],
                summary['total_tokens_created'],
                places=2,
                msg=f"Tokens desapareceram após operação {i+1}"
            )
    
    def test_individual_wallet_integrity(self):
        """Testa integridade individual de cada carteira"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        for user in self.users:
            WalletService.ensure_user_has_wallet(user.id)
        
        # Realizar operações complexas
        WalletService.admin_sell_tokens_to_user(self.users[0].id, 5000.0, "Compra inicial")
        WalletService.transfer_to_escrow(self.users[0].id, 2000.0, 1)
        WalletService.user_sell_tokens_to_admin(self.users[0].id, 1000.0, "Saque parcial")
        
        # Validar integridade de cada carteira
        for user in self.users:
            integrity = WalletService.validate_transaction_integrity(user.id)
            
            self.assertTrue(
                integrity['is_valid'], 
                f"Integridade falhou para usuário {user.id}: {integrity}"
            )
            self.assertTrue(
                integrity['balance_matches'],
                f"Saldo não confere para usuário {user.id}"
            )
            self.assertTrue(
                integrity['escrow_matches'],
                f"Escrow não confere para usuário {user.id}"
            )
        
        # Validar integridade do admin
        admin_integrity = WalletService.validate_transaction_integrity(WalletService.ADMIN_USER_ID)
        self.assertTrue(admin_integrity['is_valid'], f"Integridade do admin falhou: {admin_integrity}")
    
    def test_escrow_balance_integrity(self):
        """Testa integridade específica do sistema de escrow"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.users[0].id)
        
        # Dar tokens ao usuário
        WalletService.admin_sell_tokens_to_user(self.users[0].id, 10000.0, "Saldo inicial")
        
        # Estado inicial
        initial_info = WalletService.get_wallet_info(self.users[0].id)
        initial_total = initial_info['total_balance']
        
        # Transferir para escrow
        WalletService.transfer_to_escrow(self.users[0].id, 3000.0, 1)
        
        # Verificar que total não mudou (apenas redistribuição)
        after_escrow_info = WalletService.get_wallet_info(self.users[0].id)
        
        self.assertEqual(after_escrow_info['total_balance'], initial_total)
        self.assertEqual(after_escrow_info['balance'], 7000.0)  # 10K - 3K
        self.assertEqual(after_escrow_info['escrow_balance'], 3000.0)
        
        # Verificar integridade das transações
        integrity = WalletService.validate_transaction_integrity(self.users[0].id)
        self.assertTrue(integrity['is_valid'])
    
    def test_multiple_escrow_operations_integrity(self):
        """Testa integridade com múltiplas operações de escrow"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.users[0].id)
        
        # Dar tokens ao usuário
        WalletService.admin_sell_tokens_to_user(self.users[0].id, 20000.0, "Saldo inicial")
        
        # Múltiplas operações de escrow
        escrow_operations = [
            (5000.0, 1),
            (3000.0, 2),
            (2000.0, 3),
            (4000.0, 4)
        ]
        
        total_escrow_expected = 0
        
        for amount, order_id in escrow_operations:
            WalletService.transfer_to_escrow(self.users[0].id, amount, order_id)
            total_escrow_expected += amount
            
            # Verificar integridade após cada operação
            info = WalletService.get_wallet_info(self.users[0].id)
            integrity = WalletService.validate_transaction_integrity(self.users[0].id)
            
            self.assertTrue(integrity['is_valid'])
            self.assertEqual(info['escrow_balance'], total_escrow_expected)
            self.assertEqual(info['total_balance'], 20000.0)  # Total sempre o mesmo
    
    def test_system_wide_mathematical_consistency(self):
        """Testa consistência matemática em todo o sistema"""
        # Preparar sistema completo
        WalletService.ensure_admin_has_wallet()
        for user in self.users:
            WalletService.ensure_user_has_wallet(user.id)
        
        # Cenário complexo com múltiplas operações
        scenario_operations = [
            # Admin cria tokens adicionais
            lambda: WalletService.admin_create_tokens(100000.0, "Expansão monetária"),
            
            # Distribuir tokens para usuários
            lambda: WalletService.admin_sell_tokens_to_user(self.users[0].id, 25000.0, "Venda 1"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[1].id, 30000.0, "Venda 2"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[2].id, 20000.0, "Venda 3"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[3].id, 15000.0, "Venda 4"),
            
            # Operações de escrow
            lambda: WalletService.transfer_to_escrow(self.users[0].id, 10000.0, 1),
            lambda: WalletService.transfer_to_escrow(self.users[1].id, 8000.0, 2),
            lambda: WalletService.transfer_to_escrow(self.users[2].id, 5000.0, 3),
            
            # Saques parciais
            lambda: WalletService.user_sell_tokens_to_admin(self.users[0].id, 5000.0, "Saque 1"),
            lambda: WalletService.user_sell_tokens_to_admin(self.users[3].id, 7000.0, "Saque 2"),
        ]
        
        # Executar cenário
        for operation in scenario_operations:
            operation()
        
        # Verificações finais de integridade
        
        # 1. Verificar que soma de todos os saldos = total criado
        admin_info = WalletService.get_admin_wallet_info()
        total_admin = admin_info['balance'] + admin_info['escrow_balance']
        
        total_users = 0
        for user in self.users:
            user_info = WalletService.get_wallet_info(user.id)
            total_users += user_info['balance'] + user_info['escrow_balance']
        
        summary = WalletService.get_system_token_summary()
        
        self.assertAlmostEqual(
            total_admin + total_users,
            summary['total_tokens_created'],
            places=2,
            msg="Soma de saldos não confere com total criado"
        )
        
        # 2. Verificar integridade individual de cada carteira
        for user in self.users:
            integrity = WalletService.validate_transaction_integrity(user.id)
            self.assertTrue(
                integrity['is_valid'],
                f"Integridade falhou para usuário {user.id}"
            )
        
        # 3. Verificar integridade do admin
        admin_integrity = WalletService.validate_transaction_integrity(WalletService.ADMIN_USER_ID)
        self.assertTrue(admin_integrity['is_valid'], "Integridade do admin falhou")
        
        # 4. Verificar resumo do sistema
        self.assertEqual(
            summary['total_tokens_in_system'],
            summary['total_tokens_created']
        )
    
    def test_precision_and_rounding(self):
        """Testa precisão numérica e arredondamento"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.users[0].id)
        
        # Operações com valores decimais
        decimal_operations = [
            1000.01,
            999.99,
            0.01,
            1234.56,
            9876.54
        ]
        
        total_expected = 0
        
        for amount in decimal_operations:
            WalletService.admin_sell_tokens_to_user(self.users[0].id, amount, f"Venda {amount}")
            total_expected += amount
        
        # Verificar precisão
        user_info = WalletService.get_wallet_info(self.users[0].id)
        
        self.assertAlmostEqual(
            user_info['balance'],
            total_expected,
            places=2,
            msg="Precisão decimal falhou"
        )
        
        # Verificar integridade com decimais
        integrity = WalletService.validate_transaction_integrity(self.users[0].id)
        self.assertTrue(integrity['is_valid'], "Integridade falhou com valores decimais")
    
    def test_zero_sum_operations(self):
        """Testa operações que devem resultar em soma zero"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.users[0].id)
        
        # Estado inicial
        initial_summary = WalletService.get_system_token_summary()
        initial_admin_balance = initial_summary['admin_balance']
        initial_user_balance = WalletService.get_wallet_balance(self.users[0].id)
        
        # Operação: admin vende para usuário e usuário vende de volta
        amount = 5000.0
        
        WalletService.admin_sell_tokens_to_user(self.users[0].id, amount, "Venda teste")
        WalletService.user_sell_tokens_to_admin(self.users[0].id, amount, "Saque teste")
        
        # Estado final deve ser igual ao inicial
        final_summary = WalletService.get_system_token_summary()
        final_admin_balance = final_summary['admin_balance']
        final_user_balance = WalletService.get_wallet_balance(self.users[0].id)
        
        self.assertAlmostEqual(
            final_admin_balance,
            initial_admin_balance,
            places=2,
            msg="Saldo do admin não retornou ao estado inicial"
        )
        
        self.assertAlmostEqual(
            final_user_balance,
            initial_user_balance,
            places=2,
            msg="Saldo do usuário não retornou ao estado inicial"
        )
        
        # Total do sistema deve ser o mesmo
        self.assertEqual(
            final_summary['total_tokens_created'],
            initial_summary['total_tokens_created']
        )
    
    def test_concurrent_operations_integrity(self):
        """Testa integridade com operações 'concorrentes' simuladas"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        for user in self.users[:3]:  # Usar apenas 3 usuários
            WalletService.ensure_user_has_wallet(user.id)
        
        # Simular operações "concorrentes" (sequenciais mas intercaladas)
        operations = [
            lambda: WalletService.admin_sell_tokens_to_user(self.users[0].id, 1000.0, "Op 1"),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[1].id, 2000.0, "Op 2"),
            lambda: WalletService.transfer_to_escrow(self.users[0].id, 500.0, 1),
            lambda: WalletService.admin_sell_tokens_to_user(self.users[2].id, 1500.0, "Op 3"),
            lambda: WalletService.user_sell_tokens_to_admin(self.users[1].id, 800.0, "Op 4"),
            lambda: WalletService.transfer_to_escrow(self.users[2].id, 700.0, 2),
            lambda: WalletService.user_sell_tokens_to_admin(self.users[0].id, 200.0, "Op 5"),
        ]
        
        # Executar operações
        for operation in operations:
            operation()
        
        # Verificar integridade final
        summary = WalletService.get_system_token_summary()
        
        self.assertEqual(
            summary['total_tokens_in_system'],
            summary['total_tokens_created'],
            "Integridade falhou com operações concorrentes"
        )
        
        # Verificar cada carteira individualmente
        for user in self.users[:3]:
            integrity = WalletService.validate_transaction_integrity(user.id)
            self.assertTrue(
                integrity['is_valid'],
                f"Integridade falhou para usuário {user.id} em operações concorrentes"
            )

if __name__ == '__main__':
    unittest.main()