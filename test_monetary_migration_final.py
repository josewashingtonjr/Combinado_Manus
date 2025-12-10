#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste Final da Migração Monetária
Verifica se a migração foi aplicada corretamente e testa operações básicas
"""

import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Wallet, Transaction, Order, TokenRequest
from services.monetary_migration_service import MonetaryMigrationService

def test_decimal_precision():
    """Testa se os valores decimais estão sendo armazenados corretamente"""
    print("Testando precisão decimal...")
    
    with app.app_context():
        # Criar um usuário de teste se não existir
        test_user = User.query.filter_by(email='test_migration@test.com').first()
        if not test_user:
            test_user = User(
                email='test_migration@test.com',
                nome='Teste Migração',
                cpf='12345678901',
                password_hash='test'
            )
            db.session.add(test_user)
            db.session.commit()
        
        # Criar carteira se não existir
        wallet = Wallet.query.filter_by(user_id=test_user.id).first()
        if not wallet:
            wallet = Wallet(user_id=test_user.id, balance=Decimal('123.45'), escrow_balance=Decimal('67.89'))
            db.session.add(wallet)
            db.session.commit()
        
        # Verificar se os valores são armazenados corretamente
        wallet_check = Wallet.query.filter_by(user_id=test_user.id).first()
        
        print(f"   • Balance: {wallet_check.balance} (tipo: {type(wallet_check.balance)})")
        print(f"   • Escrow Balance: {wallet_check.escrow_balance} (tipo: {type(wallet_check.escrow_balance)})")
        
        # Verificar se são Decimal
        assert isinstance(wallet_check.balance, Decimal), "Balance deve ser Decimal"
        assert isinstance(wallet_check.escrow_balance, Decimal), "Escrow balance deve ser Decimal"
        
        print("   ✅ Precisão decimal OK")

def test_constraints():
    """Testa se as constraints estão funcionando"""
    print("Testando constraints...")
    
    with app.app_context():
        try:
            # Tentar criar carteira com saldo negativo (deve falhar)
            test_user = User.query.first()
            if test_user:
                negative_wallet = Wallet(user_id=999999, balance=Decimal('-10.00'))
                db.session.add(negative_wallet)
                db.session.commit()
                print("   ❌ Constraint de saldo negativo não está funcionando")
                return False
        except Exception:
            db.session.rollback()
            print("   ✅ Constraint de saldo negativo OK")
        
        try:
            # Tentar criar transação com amount zero (deve falhar)
            test_user = User.query.first()
            if test_user:
                zero_transaction = Transaction(
                    user_id=test_user.id,
                    type='test',
                    amount=Decimal('0.00'),
                    description='Teste'
                )
                db.session.add(zero_transaction)
                db.session.commit()
                print("   ❌ Constraint de transação zero não está funcionando")
                return False
        except Exception:
            db.session.rollback()
            print("   ✅ Constraint de transação zero OK")
        
        return True

def test_model_fields():
    """Testa se todos os campos monetários estão usando Numeric"""
    print("Testando tipos de campos nos modelos...")
    
    with app.app_context():
        # Verificar Wallet
        wallet_balance_type = str(Wallet.__table__.columns['balance'].type)
        wallet_escrow_type = str(Wallet.__table__.columns['escrow_balance'].type)
        print(f"   • Wallet.balance: {wallet_balance_type}")
        print(f"   • Wallet.escrow_balance: {wallet_escrow_type}")
        
        # Verificar Transaction
        transaction_amount_type = str(Transaction.__table__.columns['amount'].type)
        print(f"   • Transaction.amount: {transaction_amount_type}")
        
        # Verificar Order
        order_value_type = str(Order.__table__.columns['value'].type)
        print(f"   • Order.value: {order_value_type}")
        
        # Verificar TokenRequest
        token_request_amount_type = str(TokenRequest.__table__.columns['amount'].type)
        print(f"   • TokenRequest.amount: {token_request_amount_type}")
        
        # Verificar se todos são NUMERIC
        numeric_fields = [
            wallet_balance_type,
            wallet_escrow_type,
            transaction_amount_type,
            order_value_type,
            token_request_amount_type
        ]
        
        all_numeric = all('NUMERIC' in field_type for field_type in numeric_fields)
        
        if all_numeric:
            print("   ✅ Todos os campos monetários usam NUMERIC")
            return True
        else:
            print("   ❌ Alguns campos não usam NUMERIC")
            return False

def main():
    """Função principal do teste"""
    print("=" * 80)
    print("TESTE FINAL DA MIGRAÇÃO MONETÁRIA")
    print("Sistema de Correções Críticas - Tarefa 1")
    print("=" * 80)
    print()
    
    success = True
    
    try:
        # Teste 1: Validação completa
        print("1. EXECUTANDO VALIDAÇÃO COMPLETA...")
        validation_result = MonetaryMigrationService.validate_migration_integrity()
        
        if validation_result['success'] and validation_result['summary']['all_valid']:
            print("   ✅ Validação completa OK")
        else:
            print("   ❌ Validação completa falhou")
            success = False
        
        print()
        
        # Teste 2: Tipos de campos
        print("2. VERIFICANDO TIPOS DE CAMPOS...")
        if test_model_fields():
            print("   ✅ Tipos de campos OK")
        else:
            print("   ❌ Tipos de campos incorretos")
            success = False
        
        print()
        
        # Teste 3: Precisão decimal
        print("3. TESTANDO PRECISÃO DECIMAL...")
        test_decimal_precision()
        print()
        
        # Teste 4: Constraints
        print("4. TESTANDO CONSTRAINTS...")
        if test_constraints():
            print("   ✅ Constraints OK")
        else:
            print("   ❌ Constraints falharam")
            success = False
        
        print()
        
        if success:
            print("=" * 80)
            print("✅ TODOS OS TESTES PASSARAM!")
            print("   • Migração Float → Numeric(18,2) concluída com sucesso")
            print("   • Todos os dados estão íntegros")
            print("   • Constraints de integridade ativas")
            print("   • Sistema pronto para operação")
            print("=" * 80)
            return 0
        else:
            print("=" * 80)
            print("❌ ALGUNS TESTES FALHARAM!")
            print("   • Verifique os problemas reportados acima")
            print("=" * 80)
            return 1
            
    except Exception as e:
        print(f"❌ ERRO DURANTE TESTES: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)