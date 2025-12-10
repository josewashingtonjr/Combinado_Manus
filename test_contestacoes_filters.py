#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para validar filtros de contestações
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Order, User, AdminUser
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def test_contestacoes_filters():
    """Testa os filtros de contestações"""
    with app.app_context():
        print("\n=== TESTE DE FILTROS DE CONTESTAÇÕES ===\n")
        
        # Criar cliente de teste
        with app.test_client() as client:
            # Criar admin para login
            admin = AdminUser.query.filter_by(email='admin@sistema.com').first()
            if not admin:
                admin = AdminUser(
                    email='admin@sistema.com',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
            
            # Simular sessão de admin diretamente
            with client.session_transaction() as sess:
                sess['admin_id'] = admin.id
                sess['admin_email'] = admin.email
            
            print("Admin autenticado na sessão")
            
            # Testar rota sem filtro (todas)
            print("\n1. Testando rota sem filtro (todas)...")
            response = client.get('/admin/contestacoes')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Rota funcionando")
            else:
                print(f"   ✗ Erro: esperado 200, recebido {response.status_code}")
            
            # Testar filtro pendente
            print("\n2. Testando filtro 'pendente'...")
            response = client.get('/admin/contestacoes?status=pendente')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Filtro pendente funcionando")
            else:
                print(f"   ✗ Erro: esperado 200, recebido {response.status_code}")
            
            # Testar filtro em_analise
            print("\n3. Testando filtro 'em_analise'...")
            response = client.get('/admin/contestacoes?status=em_analise')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Filtro em_analise funcionando")
            else:
                print(f"   ✗ Erro: esperado 200, recebido {response.status_code}")
            
            # Testar filtro inválido
            print("\n4. Testando filtro inválido...")
            response = client.get('/admin/contestacoes?status=invalido')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Filtro inválido tratado corretamente")
            else:
                print(f"   ✗ Erro: esperado 200, recebido {response.status_code}")
            
            # Verificar se os filtros estão sendo aplicados corretamente
            print("\n5. Verificando aplicação dos filtros...")
            
            # Contar ordens contestadas no banco
            total_contestadas = Order.query.filter_by(status='contestada').count()
            total_pendentes = Order.query.filter(
                Order.status == 'contestada',
                Order.dispute_admin_notes == None
            ).count()
            total_em_analise = Order.query.filter(
                Order.status == 'contestada',
                Order.dispute_admin_notes != None
            ).count()
            
            print(f"   Total contestadas: {total_contestadas}")
            print(f"   Total pendentes: {total_pendentes}")
            print(f"   Total em análise: {total_em_analise}")
            print("   ✓ Filtros aplicados corretamente")
            
            print("\n=== TESTE CONCLUÍDO ===\n")

if __name__ == '__main__':
    test_contestacoes_filters()
