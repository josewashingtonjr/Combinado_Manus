#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples para validar o DashboardDataService
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Order, Wallet, Transaction
from services.dashboard_data_service import DashboardDataService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def test_dashboard_data_service():
    """Testa os métodos do DashboardDataService"""
    
    with app.app_context():
        print("\n=== Teste do DashboardDataService ===\n")
        
        # 1. Criar usuários de teste
        print("1. Criando usuários de teste...")
        
        # Cliente
        cliente = User.query.filter_by(email='cliente_test@test.com').first()
        if not cliente:
            cliente = User(
                email='cliente_test@test.com',
                nome='Cliente Teste',
                cpf='12345678901',
                phone='11999999999',
                roles='cliente'
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
            db.session.commit()
        
        # Prestador
        prestador = User.query.filter_by(email='prestador_test@test.com').first()
        if not prestador:
            prestador = User(
                email='prestador_test@test.com',
                nome='Prestador Teste',
                cpf='98765432109',
                phone='11888888888',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
            db.session.commit()
        
        print(f"   Cliente ID: {cliente.id}")
        print(f"   Prestador ID: {prestador.id}")
        
        # 2. Garantir que ambos têm carteiras
        print("\n2. Garantindo carteiras...")
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo ao cliente
        WalletService.credit_wallet(
            cliente.id,
            1000.0,
            "Saldo inicial para teste",
            transaction_type="credito"
        )
        print(f"   Saldo do cliente: R$ 1000.00")
        
        # 3. Criar ordem de teste
        print("\n3. Criando ordem de teste...")
        
        ordem = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Serviço de Teste',
            description='Descrição do serviço de teste',
            value=Decimal('500.00'),
            status='aceita',
            service_deadline=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow(),
            accepted_at=datetime.utcnow()
        )
        db.session.add(ordem)
        db.session.commit()
        
        print(f"   Ordem ID: {ordem.id}")
        print(f"   Status: {ordem.status}")
        print(f"   Valor: R$ {ordem.value}")
        
        # Bloquear valor no escrow
        WalletService.transfer_to_escrow(cliente.id, Decimal('500.00'), ordem.id)
        print(f"   Valor bloqueado no escrow do cliente")
        
        # 4. Testar get_open_orders para cliente
        print("\n4. Testando get_open_orders (cliente)...")
        open_orders_cliente = DashboardDataService.get_open_orders(cliente.id, 'cliente')
        print(f"   Ordens em aberto: {len(open_orders_cliente)}")
        
        if open_orders_cliente:
            ordem_info = open_orders_cliente[0]
            print(f"   - ID: {ordem_info['id']}")
            print(f"   - Título: {ordem_info['title']}")
            print(f"   - Valor: R$ {ordem_info['value']:.2f}")
            print(f"   - Status: {ordem_info['status_display']}")
            print(f"   - Prestador: {ordem_info['related_user_name']}")
        
        # 5. Testar get_open_orders para prestador
        print("\n5. Testando get_open_orders (prestador)...")
        open_orders_prestador = DashboardDataService.get_open_orders(prestador.id, 'prestador')
        print(f"   Ordens em aberto: {len(open_orders_prestador)}")
        
        if open_orders_prestador:
            ordem_info = open_orders_prestador[0]
            print(f"   - ID: {ordem_info['id']}")
            print(f"   - Título: {ordem_info['title']}")
            print(f"   - Valor: R$ {ordem_info['value']:.2f}")
            print(f"   - Status: {ordem_info['status_display']}")
            print(f"   - Cliente: {ordem_info['related_user_name']}")
        
        # 6. Testar get_blocked_funds_summary
        print("\n6. Testando get_blocked_funds_summary...")
        blocked_funds = DashboardDataService.get_blocked_funds_summary(cliente.id)
        print(f"   Total bloqueado: R$ {blocked_funds['total_blocked']:.2f}")
        print(f"   Ordens com fundos bloqueados: {len(blocked_funds['by_order'])}")
        
        for item in blocked_funds['by_order']:
            print(f"   - Ordem #{item['order_id']}: R$ {item['amount']:.2f} ({item['blocked_type']})")
        
        # 7. Testar get_dashboard_metrics para cliente
        print("\n7. Testando get_dashboard_metrics (cliente)...")
        metrics_cliente = DashboardDataService.get_dashboard_metrics(cliente.id, 'cliente')
        
        print(f"   Saldo disponível: R$ {metrics_cliente['balance']['available']:.2f}")
        print(f"   Saldo bloqueado: R$ {metrics_cliente['balance']['blocked']:.2f}")
        print(f"   Saldo total: R$ {metrics_cliente['balance']['total']:.2f}")
        print(f"   Ordens em aberto: {metrics_cliente['open_orders_count']}")
        print(f"   Ordens por status: {metrics_cliente['orders_by_status']}")
        print(f"   Estatísticas do mês:")
        print(f"     - Ordens criadas: {metrics_cliente['month_stats']['orders_created']}")
        print(f"     - Ordens concluídas: {metrics_cliente['month_stats']['orders_completed']}")
        print(f"     - Total gasto: R$ {metrics_cliente['month_stats']['total_spent']:.2f}")
        print(f"   Alertas: {len(metrics_cliente['alerts'])}")
        
        for alert in metrics_cliente['alerts']:
            print(f"     - [{alert['type']}] {alert['title']}: {alert['message']}")
        
        # 8. Testar get_dashboard_metrics para prestador
        print("\n8. Testando get_dashboard_metrics (prestador)...")
        metrics_prestador = DashboardDataService.get_dashboard_metrics(prestador.id, 'prestador')
        
        print(f"   Saldo disponível: R$ {metrics_prestador['balance']['available']:.2f}")
        print(f"   Saldo bloqueado: R$ {metrics_prestador['balance']['blocked']:.2f}")
        print(f"   Saldo total: R$ {metrics_prestador['balance']['total']:.2f}")
        print(f"   Ordens em aberto: {metrics_prestador['open_orders_count']}")
        print(f"   Ordens por status: {metrics_prestador['orders_by_status']}")
        print(f"   Estatísticas do mês:")
        print(f"     - Ordens aceitas: {metrics_prestador['month_stats']['orders_accepted']}")
        print(f"     - Ordens concluídas: {metrics_prestador['month_stats']['orders_completed']}")
        print(f"     - Total recebido: R$ {metrics_prestador['month_stats']['total_received']:.2f}")
        print(f"   Alertas: {len(metrics_prestador['alerts'])}")
        
        for alert in metrics_prestador['alerts']:
            print(f"     - [{alert['type']}] {alert['title']}: {alert['message']}")
        
        print("\n=== Todos os testes passaram com sucesso! ===\n")
        
        return True

if __name__ == '__main__':
    try:
        test_dashboard_data_service()
    except Exception as e:
        print(f"\n❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
