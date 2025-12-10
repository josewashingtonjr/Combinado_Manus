#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples para o método resolve_dispute() do OrderManagementService
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Wallet, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService


def test_resolve_dispute():
    """Testa resolução de disputa"""
    print("\n" + "="*80)
    print("TESTE: Resolução de Disputa")
    print("="*80)
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Limpar dados
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Criar usuários
        cliente = User(nome='Cliente', email='cliente@test.com', cpf='11111111111', phone='11988888888', roles='cliente')
        cliente.set_password('senha123')
        
        prestador = User(nome='Prestador', email='prestador@test.com', cpf='22222222222', phone='11977777777', roles='prestador')
        prestador.set_password('senha123')
        
        admin = User(nome='Admin', email='admin@test.com', cpf='00000000000', phone='11999999999', roles='admin')
        admin.set_password('senha123')
        
        db.session.add_all([cliente, prestador, admin])
        db.session.commit()
        
        # Criar carteiras (admin será ID 0 via WalletService)
        WalletService.ensure_admin_has_wallet()  # Garante que admin tem ID 0
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo
        WalletService.credit_wallet(cliente.id, Decimal('2000.00'), 'Saldo inicial')
        WalletService.credit_wallet(prestador.id, Decimal('1000.00'), 'Saldo inicial')
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            invited_phone='11966666666',
            service_title='Serviço Teste',
            service_description='Descrição',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        print("\n1. Criando ordem...")
        order_result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = order_result['order_id']
        print(f"   ✓ Ordem {order_id} criada")
        
        print("\n2. Prestador marca como concluído...")
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        print(f"   ✓ Ordem marcada como concluída")
        
        print("\n3. Cliente abre contestação...")
        OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=cliente.id,
            reason="Serviço não foi executado conforme combinado.",
            evidence_files=None
        )
        print(f"   ✓ Contestação aberta")
        
        print("\n4. Saldos antes da resolução:")
        cliente_before = WalletService.get_wallet_info(cliente.id)
        prestador_before = WalletService.get_wallet_info(prestador.id)
        admin_before = WalletService.get_wallet_info(WalletService.ADMIN_USER_ID)
        print(f"   Cliente - Disponível: R$ {cliente_before['balance']:.2f}, Bloqueado: R$ {cliente_before['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_before['balance']:.2f}, Bloqueado: R$ {prestador_before['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_before['balance']:.2f}")
        
        # TESTE 1: Resolver a favor do cliente
        print("\n5. Admin resolve disputa a favor do CLIENTE...")
        resolve_result = OrderManagementService.resolve_dispute(
            order_id=order_id,
            admin_id=admin.id,
            winner='client',
            admin_notes='Serviço não executado adequadamente.'
        )
        
        print(f"   ✓ {resolve_result['message']}")
        print(f"   Vencedor: {resolve_result['winner_name']}")
        
        print("\n6. Saldos após resolução:")
        cliente_after = WalletService.get_wallet_info(cliente.id)
        prestador_after = WalletService.get_wallet_info(prestador.id)
        admin_after = WalletService.get_wallet_info(WalletService.ADMIN_USER_ID)
        print(f"   Cliente - Disponível: R$ {cliente_after['balance']:.2f}, Bloqueado: R$ {cliente_after['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_after['balance']:.2f}, Bloqueado: R$ {prestador_after['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_after['balance']:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'resolvida', f"Status deveria ser 'resolvida', mas é '{order.status}'"
        assert order.dispute_winner == 'client', f"Vencedor deveria ser 'client'"
        assert order.dispute_resolved_by == admin.id or order.dispute_resolved_by == WalletService.ADMIN_USER_ID, "Admin deveria estar registrado"
        
        # Verificar pagamentos
        payments = resolve_result['payments']
        print("\n7. Detalhes dos pagamentos:")
        print(f"   Valor devolvido ao cliente: R$ {payments['service_value_returned_to_client']:.2f}")
        print(f"   Taxa de contestação para plataforma: R$ {payments['contestation_fee_to_platform']:.2f}")
        print(f"   Taxa devolvida ao prestador: R$ {payments['contestation_fee_returned_to_provider']:.2f}")
        
        assert payments['service_value_returned_to_client'] == 100.00
        assert payments['contestation_fee_to_platform'] == 10.00
        assert payments['contestation_fee_returned_to_provider'] == 10.00
        assert payments['provider_received'] == 0.0
        
        # Cliente: 2000 - 10 (taxa contestação) = 1990
        assert Decimal(str(cliente_after['balance'])) == Decimal('1990.00'), \
            f"Cliente deveria ter R$ 1990.00, mas tem R$ {cliente_after['balance']:.2f}"
        
        # Prestador: 1000 (voltou ao inicial)
        assert Decimal(str(prestador_after['balance'])) == Decimal('1000.00'), \
            f"Prestador deveria ter R$ 1000.00, mas tem R$ {prestador_after['balance']:.2f}"
        
        # Admin: 1000000 (inicial) + 10 (taxa de contestação do cliente)
        assert Decimal(str(admin_after['balance'])) == Decimal('1000010.00'), \
            f"Admin deveria ter R$ 1000010.00, mas tem R$ {admin_after['balance']:.2f}"
        
        print("\n✓ TESTE PASSOU: Disputa resolvida corretamente a favor do cliente!")
        
        # TESTE 2: Resolver a favor do prestador
        print("\n" + "="*80)
        print("TESTE 2: Resolução a Favor do Prestador")
        print("="*80)
        
        # Limpar e criar nova ordem
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.commit()
        
        # Resetar saldos
        cliente_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
        prestador_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
        admin_wallet = Wallet.query.filter_by(user_id=WalletService.ADMIN_USER_ID).first()
        
        cliente_wallet.balance = Decimal('2000.00')
        cliente_wallet.escrow_balance = Decimal('0.00')
        prestador_wallet.balance = Decimal('1000.00')
        prestador_wallet.escrow_balance = Decimal('0.00')
        admin_wallet.balance = Decimal('0.00')
        db.session.commit()
        
        # Criar nova ordem
        invite2 = Invite(
            client_id=cliente.id,
            invited_phone='11966666666',
            service_title='Serviço Teste 2',
            service_description='Descrição 2',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite2)
        db.session.commit()
        
        print("\n1. Criando ordem...")
        order_result2 = OrderManagementService.create_order_from_invite(invite2.id, prestador.id)
        order_id2 = order_result2['order_id']
        
        print("\n2. Prestador marca como concluído...")
        OrderManagementService.mark_service_completed(order_id2, prestador.id)
        
        print("\n3. Cliente abre contestação...")
        OrderManagementService.open_dispute(
            order_id=order_id2,
            client_id=cliente.id,
            reason="Cliente alega problemas, mas prestador tem provas.",
            evidence_files=None
        )
        
        print("\n4. Admin resolve disputa a favor do PRESTADOR...")
        resolve_result2 = OrderManagementService.resolve_dispute(
            order_id=order_id2,
            admin_id=admin.id,
            winner='provider',
            admin_notes='Prestador apresentou provas suficientes.'
        )
        
        print(f"   ✓ {resolve_result2['message']}")
        
        # Verificar ordem
        order2 = Order.query.get(order_id2)
        assert order2.status == 'resolvida'
        assert order2.dispute_winner == 'provider'
        
        # Verificar pagamentos
        payments2 = resolve_result2['payments']
        print("\n5. Detalhes dos pagamentos:")
        print(f"   Prestador recebeu: R$ {payments2['provider_received']:.2f}")
        print(f"   Taxa da plataforma: R$ {payments2['platform_fee']:.2f}")
        
        assert payments2['service_value'] == 200.00
        assert payments2['platform_fee'] == 10.00  # 5%
        assert payments2['provider_received'] == 190.00
        
        print("\n✓ TESTE 2 PASSOU: Disputa resolvida corretamente a favor do prestador!")
        
        print("\n" + "="*80)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("="*80)


if __name__ == '__main__':
    try:
        test_resolve_dispute()
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
