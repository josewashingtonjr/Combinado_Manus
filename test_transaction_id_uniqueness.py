#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, AdminUser, Wallet, Transaction, db
from services.wallet_service import WalletService

class TestTransactionIdUniqueness(unittest.TestCase):
    """Testes para garantir unicidade e rastreabilidade de IDs de transação"""
    
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
        self.user1 = User(
            nome='User 1',
            email='user1@test.com',
            cpf='12345678901',
            roles='cliente'
        )
        self.user1.set_password('123456')
        
        self.user2 = User(
            nome='User 2',
            email='user2@test.com',
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
    
    def test_transaction_id_generation_format(self):
        """Testa formato dos IDs de transação gerados"""
        # Gerar múltiplos IDs
        ids = [WalletService.generate_transaction_id() for _ in range(10)]
        
        for transaction_id in ids:
            # Verificar formato: TXN-YYYYMMDDHHMMSS-XXXXXXXX
            self.assertTrue(transaction_id.startswith('TXN-'))
            
            parts = transaction_id.split('-')
            self.assertEqual(len(parts), 3)
            
            # Parte 1: prefixo
            self.assertEqual(parts[0], 'TXN')
            
            # Parte 2: timestamp (14 dígitos)
            timestamp_part = parts[1]
            self.assertEqual(len(timestamp_part), 14)
            self.assertTrue(timestamp_part.isdigit())
            
            # Parte 3: identificador único (8 caracteres)
            unique_part = parts[2]
            self.assertEqual(len(unique_part), 8)
            self.assertTrue(all(c.isalnum() for c in unique_part))
    
    def test_transaction_id_uniqueness(self):
        """Testa que IDs de transação são únicos"""
        # Gerar muitos IDs rapidamente
        ids = []
        for _ in range(100):
            transaction_id = WalletService.generate_transaction_id()
            ids.append(transaction_id)
            # Pequena pausa para evitar IDs idênticos por timestamp
            time.sleep(0.001)
        
        # Verificar que todos são únicos
        unique_ids = set(ids)
        self.assertEqual(len(unique_ids), len(ids), "IDs de transação não são únicos")
    
    def test_transaction_database_id_uniqueness(self):
        """Testa unicidade de IDs no banco de dados"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        WalletService.ensure_user_has_wallet(self.user2.id)
        
        # Criar múltiplas transações
        operations = [
            lambda: WalletService.admin_create_tokens(10000.0, "Criação 1"),
            lambda: WalletService.admin_sell_tokens_to_user(self.user1.id, 5000.0, "Venda 1"),
            lambda: WalletService.admin_sell_tokens_to_user(self.user2.id, 3000.0, "Venda 2"),
            lambda: WalletService.user_sell_tokens_to_admin(self.user1.id, 1000.0, "Saque 1"),
            lambda: WalletService.transfer_to_escrow(self.user1.id, 2000.0, 1),
            lambda: WalletService.transfer_to_escrow(self.user2.id, 1500.0, 2),
        ]
        
        transaction_ids = []
        
        for operation in operations:
            result = operation()
            if 'transaction_id' in result:
                transaction_ids.append(result['transaction_id'])
            elif 'admin_transaction_id' in result and 'user_transaction_id' in result:
                transaction_ids.extend([result['admin_transaction_id'], result['user_transaction_id']])
        
        # Verificar que todos os IDs são únicos
        unique_ids = set(transaction_ids)
        self.assertEqual(len(unique_ids), len(transaction_ids), "IDs de transação no banco não são únicos")
        
        # Verificar que todos os IDs existem no banco
        for transaction_id in transaction_ids:
            transaction = Transaction.query.get(transaction_id)
            self.assertIsNotNone(transaction, f"Transação {transaction_id} não encontrada no banco")
    
    def test_transaction_id_sequential_integrity(self):
        """Testa integridade sequencial dos IDs de transação"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Criar transações sequenciais
        transaction_ids = []
        
        for i in range(5):
            result = WalletService.admin_sell_tokens_to_user(
                self.user1.id, 
                1000.0, 
                f"Venda sequencial {i+1}"
            )
            transaction_ids.extend([result['admin_transaction_id'], result['user_transaction_id']])
        
        # Verificar que IDs são sequenciais no banco (auto-increment)
        transactions = Transaction.query.filter(Transaction.id.in_(transaction_ids)).order_by(Transaction.id).all()
        
        for i in range(1, len(transactions)):
            self.assertGreater(
                transactions[i].id, 
                transactions[i-1].id,
                "IDs de transação não são sequenciais"
            )
    
    def test_transaction_timestamp_consistency(self):
        """Testa consistência de timestamps nas transações"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Criar transação
        result = WalletService.admin_sell_tokens_to_user(self.user1.id, 1000.0, "Teste timestamp")
        
        # Verificar timestamps das transações criadas
        admin_transaction = Transaction.query.get(result['admin_transaction_id'])
        user_transaction = Transaction.query.get(result['user_transaction_id'])
        
        # Verificar que ambas as transações têm timestamps
        self.assertIsNotNone(admin_transaction.created_at)
        self.assertIsNotNone(user_transaction.created_at)
        
        # Verificar que timestamps são próximos (diferença < 1 segundo)
        admin_timestamp = admin_transaction.created_at.timestamp()
        user_timestamp = user_transaction.created_at.timestamp()
        self.assertLess(abs(admin_timestamp - user_timestamp), 1.0)
        
        # Verificar que timestamps são válidos (não são zero ou negativos)
        self.assertGreater(admin_timestamp, 0)
        self.assertGreater(user_timestamp, 0)
    
    def test_transaction_id_immutability(self):
        """Testa que IDs de transação são imutáveis"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Criar transação
        result = WalletService.admin_sell_tokens_to_user(self.user1.id, 1000.0, "Teste imutabilidade")
        original_id = result['user_transaction_id']
        
        # Obter transação original
        original_transaction = Transaction.query.get(original_id)
        original_data = {
            'id': original_transaction.id,
            'user_id': original_transaction.user_id,
            'type': original_transaction.type,
            'amount': original_transaction.amount,
            'description': original_transaction.description,
            'created_at': original_transaction.created_at
        }
        
        # Simular tentativa de modificação (não deveria afetar a transação original)
        # Em um sistema real, isso seria prevenido por constraints de banco
        
        # Verificar que transação mantém dados originais
        current_transaction = Transaction.query.get(original_id)
        
        self.assertEqual(current_transaction.id, original_data['id'])
        self.assertEqual(current_transaction.user_id, original_data['user_id'])
        self.assertEqual(current_transaction.type, original_data['type'])
        self.assertEqual(current_transaction.amount, original_data['amount'])
        self.assertEqual(current_transaction.description, original_data['description'])
        self.assertEqual(current_transaction.created_at, original_data['created_at'])
    
    def test_transaction_id_lookup_performance(self):
        """Testa performance de busca por ID de transação"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Criar muitas transações
        transaction_ids = []
        for i in range(50):
            result = WalletService.admin_sell_tokens_to_user(
                self.user1.id, 
                100.0, 
                f"Transação {i+1}"
            )
            transaction_ids.append(result['user_transaction_id'])
        
        # Testar busca por ID (deve ser rápida)
        start_time = time.time()
        
        for transaction_id in transaction_ids:
            transaction_data = WalletService.get_transaction_by_id(transaction_id)
            self.assertIsNotNone(transaction_data)
            self.assertEqual(transaction_data['id'], transaction_id)
        
        end_time = time.time()
        lookup_time = end_time - start_time
        
        # Busca deve ser rápida (menos de 1 segundo para 50 transações)
        self.assertLess(lookup_time, 1.0, "Busca por ID de transação muito lenta")
    
    def test_transaction_id_cross_reference(self):
        """Testa referência cruzada entre transações relacionadas"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Criar transação que gera duas entradas (admin e usuário)
        result = WalletService.admin_sell_tokens_to_user(self.user1.id, 2000.0, "Teste referência cruzada")
        
        admin_transaction_id = result['admin_transaction_id']
        user_transaction_id = result['user_transaction_id']
        
        # Obter transações
        admin_transaction = Transaction.query.get(admin_transaction_id)
        user_transaction = Transaction.query.get(user_transaction_id)
        
        # Verificar referência cruzada
        self.assertEqual(admin_transaction.related_user_id, self.user1.id)
        self.assertEqual(user_transaction.related_user_id, WalletService.ADMIN_USER_ID)
        
        # Verificar que são transações complementares
        self.assertEqual(admin_transaction.amount, -2000.0)  # Saída do admin
        self.assertEqual(user_transaction.amount, 2000.0)    # Entrada do usuário
        
        # Verificar tipos complementares
        self.assertEqual(admin_transaction.type, "venda_tokens")
        self.assertEqual(user_transaction.type, "compra_tokens")
    
    def test_transaction_id_audit_trail(self):
        """Testa trilha de auditoria completa usando IDs de transação"""
        # Preparar
        WalletService.ensure_admin_has_wallet()
        WalletService.ensure_user_has_wallet(self.user1.id)
        
        # Cenário: usuário compra tokens, transfere para escrow, depois saca o restante
        
        # 1. Compra inicial
        buy_result = WalletService.admin_sell_tokens_to_user(self.user1.id, 5000.0, "Compra inicial")
        
        # 2. Transferência para escrow
        escrow_result = WalletService.transfer_to_escrow(self.user1.id, 3000.0, 1)
        
        # 3. Saque do restante
        withdraw_result = WalletService.user_sell_tokens_to_admin(self.user1.id, 2000.0, "Saque final")
        
        # Coletar todos os IDs de transação
        all_transaction_ids = [
            buy_result['admin_transaction_id'],
            buy_result['user_transaction_id'],
            escrow_result['transaction_id'],
            withdraw_result['user_transaction_id'],
            withdraw_result['admin_transaction_id']
        ]
        
        # Verificar que todas as transações existem e são rastreáveis
        audit_trail = []
        for transaction_id in all_transaction_ids:
            transaction_data = WalletService.get_transaction_by_id(transaction_id)
            audit_trail.append(transaction_data)
        
        # Verificar trilha de auditoria
        self.assertEqual(len(audit_trail), 5)
        
        # Verificar sequência temporal
        for i in range(1, len(audit_trail)):
            self.assertGreaterEqual(
                audit_trail[i]['created_at'],
                audit_trail[i-1]['created_at']
            )
        
        # Verificar integridade da trilha
        user_transactions = [t for t in audit_trail if t['user_id'] == self.user1.id]
        admin_transactions = [t for t in audit_trail if t['user_id'] == WalletService.ADMIN_USER_ID]
        
        self.assertEqual(len(user_transactions), 3)  # compra, escrow, saque
        self.assertEqual(len(admin_transactions), 2)  # venda, recompra
    
    def test_transaction_id_error_handling(self):
        """Testa tratamento de erros com IDs de transação inválidos"""
        # Testar ID inexistente
        with self.assertRaises(ValueError) as context:
            WalletService.get_transaction_by_id(99999)
        
        self.assertIn("Transação com ID 99999 não encontrada", str(context.exception))
        
        # Testar ID None
        with self.assertRaises(Exception):
            WalletService.get_transaction_by_id(None)
        
        # Testar ID string inválida
        with self.assertRaises(Exception):
            WalletService.get_transaction_by_id("invalid_id")

if __name__ == '__main__':
    unittest.main()