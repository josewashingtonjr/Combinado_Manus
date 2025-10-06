#!/usr/bin/env python3
"""
Script para criar ordens de teste para verificar o menu de contratos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, AdminUser, Order, Wallet
from datetime import datetime, timedelta

def create_test_orders():
    """Cria ordens de teste com diferentes status"""
    
    with app.app_context():
        print("🏗️  Criando ordens de teste...")
        
        try:
            # Verificar se já existem usuários
            users = User.query.all()
            if len(users) < 2:
                print("⚠️  Criando usuários de teste...")
                
                # Criar cliente de teste
                cliente = User(
                    nome="Cliente Teste",
                    email="cliente@teste.com",
                    cpf="12345678901",
                    phone="(11) 99999-9999",
                    roles="cliente"
                )
                cliente.set_password("123456")
                db.session.add(cliente)
                
                # Criar prestador de teste
                prestador = User(
                    nome="Prestador Teste",
                    email="prestador@teste.com",
                    cpf="10987654321",
                    phone="(11) 88888-8888",
                    roles="prestador"
                )
                prestador.set_password("123456")
                db.session.add(prestador)
                
                db.session.commit()
                print("✅ Usuários de teste criados")
            
            # Obter usuários para as ordens
            cliente = User.query.filter_by(roles="cliente").first()
            prestador = User.query.filter_by(roles="prestador").first()
            
            if not cliente or not prestador:
                print("❌ Não foi possível encontrar usuários para criar ordens")
                return
            
            # Criar ordens com diferentes status
            orders_data = [
                {
                    "title": "Desenvolvimento de Website",
                    "description": "Criação de website responsivo com React",
                    "value": 1500.00,
                    "status": "disponivel",
                    "client_id": cliente.id,
                    "provider_id": None
                },
                {
                    "title": "Design de Logo",
                    "description": "Criação de identidade visual completa",
                    "value": 800.00,
                    "status": "aceita",
                    "client_id": cliente.id,
                    "provider_id": prestador.id
                },
                {
                    "title": "Consultoria em Marketing",
                    "description": "Estratégia de marketing digital",
                    "value": 2000.00,
                    "status": "em_andamento",
                    "client_id": cliente.id,
                    "provider_id": prestador.id
                },
                {
                    "title": "Tradução de Documentos",
                    "description": "Tradução de documentos técnicos",
                    "value": 500.00,
                    "status": "concluida",
                    "client_id": cliente.id,
                    "provider_id": prestador.id
                },
                {
                    "title": "Aulas de Programação",
                    "description": "Curso particular de Python",
                    "value": 1200.00,
                    "status": "cancelada",
                    "client_id": cliente.id,
                    "provider_id": None
                },
                {
                    "title": "Edição de Vídeo",
                    "description": "Edição profissional de vídeo promocional",
                    "value": 900.00,
                    "status": "disputada",
                    "client_id": cliente.id,
                    "provider_id": prestador.id
                }
            ]
            
            # Verificar se já existem ordens
            existing_orders = Order.query.count()
            if existing_orders > 0:
                print(f"⚠️  Já existem {existing_orders} ordens no banco. Limpando...")
                Order.query.delete()
                db.session.commit()
            
            # Criar as ordens
            for order_data in orders_data:
                order = Order(
                    title=order_data["title"],
                    description=order_data["description"],
                    value=order_data["value"],
                    status=order_data["status"],
                    client_id=order_data["client_id"],
                    provider_id=order_data["provider_id"],
                    created_at=datetime.utcnow() - timedelta(days=len(orders_data) - orders_data.index(order_data))
                )
                db.session.add(order)
            
            db.session.commit()
            
            # Verificar criação
            total_orders = Order.query.count()
            print(f"✅ {total_orders} ordens de teste criadas com sucesso!")
            
            # Mostrar estatísticas
            print("\n📊 Distribuição por status:")
            status_counts = {}
            orders = Order.query.all()
            for order in orders:
                status = order.status or 'sem_status'
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
                
        except Exception as e:
            print(f"❌ Erro ao criar ordens de teste: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("🧪 Criação de Ordens de Teste para Menu de Contratos")
    print("=" * 55)
    
    create_test_orders()
    
    print("\n✨ Script concluído!")