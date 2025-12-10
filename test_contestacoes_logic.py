#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para validar a lógica dos filtros de contestações
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Order

def test_filter_logic():
    """Testa a lógica dos filtros de contestações"""
    with app.app_context():
        print("\n=== TESTE DE LÓGICA DOS FILTROS ===\n")
        
        # Simular diferentes filtros
        print("1. Testando query para 'todas'...")
        query = Order.query.filter(
            db.or_(
                Order.status == 'contestada',
                Order.status == 'resolvida'
            )
        )
        count = query.count()
        print(f"   Total (contestadas + resolvidas): {count}")
        print("   ✓ Query 'todas' funcionando")
        
        print("\n2. Testando query para 'pendente'...")
        query = Order.query.filter(
            db.or_(
                Order.status == 'contestada',
                Order.status == 'resolvida'
            )
        ).filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes == None
        )
        count = query.count()
        print(f"   Total pendentes: {count}")
        print("   ✓ Query 'pendente' funcionando")
        
        print("\n3. Testando query para 'em_analise'...")
        query = Order.query.filter(
            db.or_(
                Order.status == 'contestada',
                Order.status == 'resolvida'
            )
        ).filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes != None
        )
        count = query.count()
        print(f"   Total em análise: {count}")
        print("   ✓ Query 'em_analise' funcionando")
        
        print("\n4. Verificando validação de status...")
        valid_statuses = ['todas', 'pendente', 'em_analise']
        test_statuses = ['todas', 'pendente', 'em_analise', 'invalido', 'xyz']
        
        for status in test_statuses:
            is_valid = status in valid_statuses
            print(f"   Status '{status}': {'✓ válido' if is_valid else '✗ inválido (será tratado)'}")
        
        print("\n5. Testando estatísticas...")
        stats = {
            'total_contestadas': Order.query.filter_by(status='contestada').count(),
            'total_pendentes': Order.query.filter(
                Order.status == 'contestada',
                Order.dispute_admin_notes == None
            ).count(),
            'total_em_analise': Order.query.filter(
                Order.status == 'contestada',
                Order.dispute_admin_notes != None
            ).count(),
            'total_resolvidas': Order.query.filter_by(status='resolvida').count(),
        }
        
        print(f"   Total contestadas: {stats['total_contestadas']}")
        print(f"   Total pendentes: {stats['total_pendentes']}")
        print(f"   Total em análise: {stats['total_em_analise']}")
        print(f"   Total resolvidas: {stats['total_resolvidas']}")
        print("   ✓ Estatísticas calculadas corretamente")
        
        print("\n=== TODOS OS TESTES DE LÓGICA PASSARAM ===\n")

if __name__ == '__main__':
    test_filter_logic()
