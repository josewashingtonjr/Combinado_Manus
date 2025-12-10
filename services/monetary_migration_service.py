#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Migração Monetária
Responsável por validar e migrar dados monetários de Float para Numeric(18,2)
"""

from decimal import Decimal, InvalidOperation
from sqlalchemy import text
from models import db, Wallet, Transaction, Order, TokenRequest
import logging

logger = logging.getLogger(__name__)

class MonetaryMigrationService:
    """Serviço para migração e validação de tipos monetários"""
    
    @staticmethod
    def validate_migration_integrity():
        """
        Valida a integridade dos dados após migração Float→Numeric
        Verifica se todos os valores monetários estão corretos
        """
        try:
            validation_results = {
                'wallets': MonetaryMigrationService._validate_wallet_data(),
                'transactions': MonetaryMigrationService._validate_transaction_data(),
                'orders': MonetaryMigrationService._validate_order_data(),
                'token_requests': MonetaryMigrationService._validate_token_request_data()
            }
            
            # Verificar se há algum erro
            has_errors = any(not result['valid'] for result in validation_results.values())
            
            return {
                'success': not has_errors,
                'results': validation_results,
                'summary': MonetaryMigrationService._generate_validation_summary(validation_results)
            }
            
        except Exception as e:
            logger.error(f"Erro durante validação de integridade: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': {}
            }
    
    @staticmethod
    def _validate_wallet_data():
        """Valida dados da tabela wallets"""
        try:
            wallets = Wallet.query.all()
            invalid_records = []
            
            for wallet in wallets:
                errors = []
                
                # Validar balance
                if not MonetaryMigrationService._is_valid_decimal(wallet.balance):
                    errors.append(f"balance inválido: {wallet.balance}")
                
                # Validar escrow_balance
                if not MonetaryMigrationService._is_valid_decimal(wallet.escrow_balance):
                    errors.append(f"escrow_balance inválido: {wallet.escrow_balance}")
                
                # Verificar se valores são não-negativos
                if wallet.balance < 0:
                    errors.append(f"balance negativo: {wallet.balance}")
                
                if wallet.escrow_balance < 0:
                    errors.append(f"escrow_balance negativo: {wallet.escrow_balance}")
                
                if errors:
                    invalid_records.append({
                        'id': wallet.id,
                        'user_id': wallet.user_id,
                        'errors': errors
                    })
            
            return {
                'valid': len(invalid_records) == 0,
                'total_records': len(wallets),
                'invalid_records': invalid_records,
                'table': 'wallets'
            }
            
        except Exception as e:
            logger.error(f"Erro validando wallets: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'table': 'wallets'
            }
    
    @staticmethod
    def _validate_transaction_data():
        """Valida dados da tabela transactions"""
        try:
            transactions = Transaction.query.all()
            invalid_records = []
            
            for transaction in transactions:
                errors = []
                
                # Validar amount
                if not MonetaryMigrationService._is_valid_decimal(transaction.amount):
                    errors.append(f"amount inválido: {transaction.amount}")
                
                # Verificar se amount não é zero
                if transaction.amount == 0:
                    errors.append("amount não pode ser zero")
                
                if errors:
                    invalid_records.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'amount': str(transaction.amount),
                        'errors': errors
                    })
            
            return {
                'valid': len(invalid_records) == 0,
                'total_records': len(transactions),
                'invalid_records': invalid_records,
                'table': 'transactions'
            }
            
        except Exception as e:
            logger.error(f"Erro validando transactions: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'table': 'transactions'
            }
    
    @staticmethod
    def _validate_order_data():
        """Valida dados da tabela orders"""
        try:
            orders = Order.query.all()
            invalid_records = []
            
            for order in orders:
                errors = []
                
                # Validar value
                if not MonetaryMigrationService._is_valid_decimal(order.value):
                    errors.append(f"value inválido: {order.value}")
                
                # Verificar se value é positivo
                if order.value <= 0:
                    errors.append(f"value deve ser positivo: {order.value}")
                
                if errors:
                    invalid_records.append({
                        'id': order.id,
                        'client_id': order.client_id,
                        'value': str(order.value),
                        'errors': errors
                    })
            
            return {
                'valid': len(invalid_records) == 0,
                'total_records': len(orders),
                'invalid_records': invalid_records,
                'table': 'orders'
            }
            
        except Exception as e:
            logger.error(f"Erro validando orders: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'table': 'orders'
            }
    
    @staticmethod
    def _validate_token_request_data():
        """Valida dados da tabela token_requests"""
        try:
            token_requests = TokenRequest.query.all()
            invalid_records = []
            
            for token_request in token_requests:
                errors = []
                
                # Validar amount
                if not MonetaryMigrationService._is_valid_decimal(token_request.amount):
                    errors.append(f"amount inválido: {token_request.amount}")
                
                # Verificar se amount é positivo
                if token_request.amount <= 0:
                    errors.append(f"amount deve ser positivo: {token_request.amount}")
                
                if errors:
                    invalid_records.append({
                        'id': token_request.id,
                        'user_id': token_request.user_id,
                        'amount': str(token_request.amount),
                        'errors': errors
                    })
            
            return {
                'valid': len(invalid_records) == 0,
                'total_records': len(token_requests),
                'invalid_records': invalid_records,
                'table': 'token_requests'
            }
            
        except Exception as e:
            logger.error(f"Erro validando token_requests: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'table': 'token_requests'
            }
    
    @staticmethod
    def _is_valid_decimal(value):
        """Verifica se um valor é um Decimal válido com até 2 casas decimais"""
        try:
            if value is None:
                return False
            
            # Converter para Decimal se não for
            if not isinstance(value, Decimal):
                decimal_value = Decimal(str(value))
            else:
                decimal_value = value
            
            # Verificar se tem no máximo 2 casas decimais
            # Multiplicar por 100 e verificar se é inteiro
            scaled = decimal_value * 100
            return scaled == int(scaled)
            
        except (InvalidOperation, ValueError, TypeError):
            return False
    
    @staticmethod
    def _generate_validation_summary(validation_results):
        """Gera resumo da validação"""
        summary = {
            'total_tables': len(validation_results),
            'valid_tables': sum(1 for result in validation_results.values() if result.get('valid', False)),
            'total_records': sum(result.get('total_records', 0) for result in validation_results.values()),
            'total_invalid_records': sum(len(result.get('invalid_records', [])) for result in validation_results.values()),
            'tables_with_errors': [
                table for table, result in validation_results.items() 
                if not result.get('valid', False)
            ]
        }
        
        summary['all_valid'] = summary['valid_tables'] == summary['total_tables']
        
        return summary
    
    @staticmethod
    def generate_migration_script():
        """
        Gera script SQL para migração de Float para Numeric(18,2)
        Útil como backup ou para aplicar em outros ambientes
        """
        
        postgresql_script = """
-- Script de Migração: Float para Numeric(18,2)
-- PostgreSQL

BEGIN;

-- Migração da tabela wallets
ALTER TABLE wallets 
  ALTER COLUMN balance TYPE NUMERIC(18,2),
  ALTER COLUMN escrow_balance TYPE NUMERIC(18,2);

-- Migração da tabela transactions
ALTER TABLE transactions 
  ALTER COLUMN amount TYPE NUMERIC(18,2);

-- Migração da tabela orders
ALTER TABLE orders 
  ALTER COLUMN value TYPE NUMERIC(18,2);

-- Migração da tabela token_requests
ALTER TABLE token_requests 
  ALTER COLUMN amount TYPE NUMERIC(18,2);

-- Adicionar constraints de integridade
ALTER TABLE wallets 
  ADD CONSTRAINT check_balance_non_negative CHECK (balance >= 0),
  ADD CONSTRAINT check_escrow_balance_non_negative CHECK (escrow_balance >= 0);

ALTER TABLE transactions 
  ADD CONSTRAINT check_transaction_amount_not_zero CHECK (amount != 0);

ALTER TABLE orders 
  ADD CONSTRAINT check_order_value_positive CHECK (value > 0);

ALTER TABLE token_requests 
  ADD CONSTRAINT check_token_request_amount_positive CHECK (amount > 0);

COMMIT;
"""
        
        sqlite_script = """
-- Script de Migração: Float para Numeric(18,2)
-- SQLite (requer recriação de tabelas)

BEGIN TRANSACTION;

-- Backup das tabelas existentes
CREATE TABLE wallets_backup AS SELECT * FROM wallets;
CREATE TABLE transactions_backup AS SELECT * FROM transactions;
CREATE TABLE orders_backup AS SELECT * FROM orders;
CREATE TABLE token_requests_backup AS SELECT * FROM token_requests;

-- Recriar tabela wallets
DROP TABLE wallets;
CREATE TABLE wallets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    escrow_balance NUMERIC(18,2) NOT NULL DEFAULT 0.00,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    CHECK (balance >= 0),
    CHECK (escrow_balance >= 0)
);

-- Recriar tabela transactions
DROP TABLE transactions;
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    order_id INTEGER,
    related_user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (related_user_id) REFERENCES users (id),
    CHECK (amount != 0)
);

-- Recriar tabela orders
DROP TABLE orders;
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    provider_id INTEGER,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    value NUMERIC(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'disponivel',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    accepted_at DATETIME,
    completed_at DATETIME,
    invite_id INTEGER,
    dispute_reason TEXT,
    dispute_opened_by INTEGER,
    dispute_opened_at DATETIME,
    dispute_resolved_at DATETIME,
    dispute_resolution TEXT,
    FOREIGN KEY (client_id) REFERENCES users (id),
    FOREIGN KEY (provider_id) REFERENCES users (id),
    FOREIGN KEY (invite_id) REFERENCES invites (id),
    FOREIGN KEY (dispute_opened_by) REFERENCES users (id),
    CHECK (value > 0)
);

-- Recriar tabela token_requests
DROP TABLE token_requests;
CREATE TABLE token_requests (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    processed_by INTEGER,
    admin_notes TEXT,
    payment_method VARCHAR(50) DEFAULT 'pix',
    receipt_filename VARCHAR(255),
    receipt_original_name VARCHAR(255),
    receipt_uploaded_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (processed_by) REFERENCES admin_users (id),
    CHECK (amount > 0)
);

-- Restaurar dados das tabelas backup
INSERT INTO wallets SELECT * FROM wallets_backup;
INSERT INTO transactions SELECT * FROM transactions_backup;
INSERT INTO orders SELECT * FROM orders_backup;
INSERT INTO token_requests SELECT * FROM token_requests_backup;

-- Remover tabelas de backup
DROP TABLE wallets_backup;
DROP TABLE transactions_backup;
DROP TABLE orders_backup;
DROP TABLE token_requests_backup;

COMMIT;
"""
        
        return {
            'postgresql': postgresql_script,
            'sqlite': sqlite_script
        }
    
    @staticmethod
    def check_database_constraints():
        """Verifica se as constraints de integridade estão ativas no banco"""
        try:
            # Tentar inserir um valor inválido para testar constraints
            # Isso deve falhar se as constraints estiverem ativas
            
            constraint_tests = []
            
            # Teste 1: Tentar saldo negativo (deve falhar)
            try:
                db.session.execute(
                    text("INSERT INTO wallets (user_id, balance, escrow_balance) VALUES (-999, -1.00, 0.00)")
                )
                db.session.rollback()
                constraint_tests.append({
                    'test': 'negative_balance',
                    'passed': False,
                    'message': 'Constraint de saldo negativo não está ativa'
                })
            except Exception:
                db.session.rollback()
                constraint_tests.append({
                    'test': 'negative_balance',
                    'passed': True,
                    'message': 'Constraint de saldo negativo está ativa'
                })
            
            # Teste 2: Tentar transação com amount zero (deve falhar)
            try:
                db.session.execute(
                    text("INSERT INTO transactions (user_id, type, amount, description) VALUES (-999, 'test', 0.00, 'test')")
                )
                db.session.rollback()
                constraint_tests.append({
                    'test': 'zero_transaction',
                    'passed': False,
                    'message': 'Constraint de transação zero não está ativa'
                })
            except Exception:
                db.session.rollback()
                constraint_tests.append({
                    'test': 'zero_transaction',
                    'passed': True,
                    'message': 'Constraint de transação zero está ativa'
                })
            
            # Teste 3: Tentar order com valor negativo (deve falhar)
            try:
                db.session.execute(
                    text("INSERT INTO orders (client_id, title, description, value) VALUES (-999, 'test', 'test', -1.00)")
                )
                db.session.rollback()
                constraint_tests.append({
                    'test': 'negative_order_value',
                    'passed': False,
                    'message': 'Constraint de valor negativo em orders não está ativa'
                })
            except Exception:
                db.session.rollback()
                constraint_tests.append({
                    'test': 'negative_order_value',
                    'passed': True,
                    'message': 'Constraint de valor negativo em orders está ativa'
                })
            
            all_passed = all(test['passed'] for test in constraint_tests)
            
            return {
                'success': True,
                'all_constraints_active': all_passed,
                'tests': constraint_tests
            }
            
        except Exception as e:
            logger.error(f"Erro verificando constraints: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }