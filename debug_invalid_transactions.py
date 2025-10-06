#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Debug para investigar transações inválidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Transaction

def debug_invalid_transactions():
    """Investiga transações inválidas"""
    
    with app.app_context():
        print("🔍 Investigando transações inválidas...")
        
        # Buscar todas as transações
        all_transactions = Transaction.query.all()
        print(f"📊 Total de transações: {len(all_transactions)}")
        
        # Verificar transações inválidas
        invalid_transactions = []
        for transaction in all_transactions:
            issues = []
            
            if not transaction.user_id:
                issues.append("user_id vazio")
            if not transaction.type:
                issues.append("type vazio")
            if not transaction.description:
                issues.append("description vazia")
            if transaction.amount is None:
                issues.append("amount None")
                
            if issues:
                invalid_transactions.append({
                    'id': transaction.id,
                    'user_id': transaction.user_id,
                    'type': transaction.type,
                    'description': transaction.description,
                    'amount': transaction.amount,
                    'created_at': transaction.created_at,
                    'issues': issues
                })
        
        print(f"❌ Transações inválidas encontradas: {len(invalid_transactions)}")
        
        if invalid_transactions:
            print("\n🔍 Detalhes das transações inválidas:")
            for i, invalid in enumerate(invalid_transactions[:10]):  # Mostrar apenas as primeiras 10
                print(f"\n   Transação {invalid['id']}:")
                print(f"      - user_id: {invalid['user_id']}")
                print(f"      - type: '{invalid['type']}'")
                print(f"      - description: '{invalid['description']}'")
                print(f"      - amount: {invalid['amount']}")
                print(f"      - created_at: {invalid['created_at']}")
                print(f"      - Problemas: {', '.join(invalid['issues'])}")
        
        # Verificar padrões
        print(f"\n📊 Análise de padrões:")
        
        # Contar por tipo
        type_counts = {}
        for t in all_transactions:
            type_counts[t.type] = type_counts.get(t.type, 0) + 1
        
        print("   Tipos de transação:")
        for type_name, count in type_counts.items():
            print(f"      - {type_name}: {count}")
        
        # Verificar user_ids
        user_ids = [t.user_id for t in all_transactions if t.user_id]
        unique_user_ids = set(user_ids)
        print(f"   Usuários únicos com transações: {len(unique_user_ids)}")
        
        # Verificar transações sem user_id
        no_user_id = [t for t in all_transactions if not t.user_id]
        print(f"   Transações sem user_id: {len(no_user_id)}")
        
        if no_user_id:
            print("   Primeiras transações sem user_id:")
            for t in no_user_id[:5]:
                print(f"      - ID {t.id}: type='{t.type}', desc='{t.description}', amount={t.amount}")

if __name__ == "__main__":
    debug_invalid_transactions()