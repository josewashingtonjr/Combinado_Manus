#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para popular transaction_ids em transações existentes
Executa após a migração do campo transaction_id
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Transaction
from services.transaction_id_generator import TransactionIdGenerator


def populate_existing_transaction_ids():
    """
    Popula transaction_ids para todas as transações existentes que não possuem
    """
    with app.app_context():
        try:
            print("Iniciando população de transaction_ids...")
            
            # Buscar todas as transações sem transaction_id
            transactions_without_id = Transaction.query.filter(
                (Transaction.transaction_id == None) | 
                (Transaction.transaction_id == '')
            ).all()
            
            total_transactions = len(transactions_without_id)
            print(f"Encontradas {total_transactions} transações sem transaction_id")
            
            if total_transactions == 0:
                print("Todas as transações já possuem transaction_id")
                return True
            
            updated_count = 0
            
            for i, transaction in enumerate(transactions_without_id, 1):
                try:
                    # Gerar transaction_id único
                    transaction_id = TransactionIdGenerator.generate_unique_id()
                    
                    # Atualizar a transação
                    transaction.transaction_id = transaction_id
                    
                    # Commit a cada 100 transações para evitar transações muito longas
                    if i % 100 == 0:
                        db.session.commit()
                        print(f"Processadas {i}/{total_transactions} transações...")
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"Erro ao processar transação ID {transaction.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            # Commit final
            db.session.commit()
            
            print(f"População concluída! {updated_count} transações atualizadas.")
            return True
            
        except Exception as e:
            print(f"Erro durante a população: {str(e)}")
            db.session.rollback()
            return False


def add_not_null_constraint():
    """
    Adiciona constraint NOT NULL ao campo transaction_id após população
    """
    with app.app_context():
        try:
            print("Adicionando constraint NOT NULL ao campo transaction_id...")
            
            # Executar SQL para adicionar constraint
            db.session.execute("""
                ALTER TABLE transactions 
                ALTER COLUMN transaction_id SET NOT NULL
            """)
            
            db.session.commit()
            print("Constraint NOT NULL adicionada com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar constraint: {str(e)}")
            db.session.rollback()
            return False


def validate_transaction_ids():
    """
    Valida se todos os transaction_ids estão no formato correto e são únicos
    """
    with app.app_context():
        try:
            print("Validando transaction_ids...")
            
            # Buscar todas as transações
            all_transactions = Transaction.query.all()
            total_count = len(all_transactions)
            
            print(f"Validando {total_count} transações...")
            
            invalid_format_count = 0
            duplicate_count = 0
            transaction_ids_seen = set()
            
            for transaction in all_transactions:
                # Verificar formato
                if not TransactionIdGenerator.validate_format(transaction.transaction_id):
                    print(f"Formato inválido na transação ID {transaction.id}: {transaction.transaction_id}")
                    invalid_format_count += 1
                
                # Verificar duplicatas
                if transaction.transaction_id in transaction_ids_seen:
                    print(f"Transaction_id duplicado: {transaction.transaction_id}")
                    duplicate_count += 1
                else:
                    transaction_ids_seen.add(transaction.transaction_id)
            
            print(f"Validação concluída:")
            print(f"- Total de transações: {total_count}")
            print(f"- Formatos inválidos: {invalid_format_count}")
            print(f"- Duplicatas encontradas: {duplicate_count}")
            
            return invalid_format_count == 0 and duplicate_count == 0
            
        except Exception as e:
            print(f"Erro durante validação: {str(e)}")
            return False


if __name__ == "__main__":
    print("=== Script de População de Transaction IDs ===")
    print(f"Executado em: {datetime.now()}")
    
    # Etapa 1: Popular transaction_ids existentes
    if populate_existing_transaction_ids():
        print("✓ População de transaction_ids concluída")
        
        # Etapa 2: Adicionar constraint NOT NULL
        if add_not_null_constraint():
            print("✓ Constraint NOT NULL adicionada")
            
            # Etapa 3: Validar resultados
            if validate_transaction_ids():
                print("✓ Validação bem-sucedida - Todos os transaction_ids estão corretos")
                print("\n=== MIGRAÇÃO CONCLUÍDA COM SUCESSO ===")
            else:
                print("✗ Validação falhou - Verificar logs acima")
                sys.exit(1)
        else:
            print("✗ Falha ao adicionar constraint NOT NULL")
            sys.exit(1)
    else:
        print("✗ Falha na população de transaction_ids")
        sys.exit(1)