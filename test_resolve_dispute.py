#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para o método resolve_dispute() do OrderManagementService
Testa a arbitragem de contestações pelo admin
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Wallet, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService


def setup_test_data():
    """Cria dados de teste"""
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        # Limpar dados existentes
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Criar usuários
        admin = User(
            nome='Admin',
            email='admin@test.com',
            cpf='00000000000',
            phone='11999999999',
            roles='admin'
        )
        admin.set_password('senha123')
        
        cliente = User(
            nome='Cliente Teste',
            email='cliente@test.com',
            cpf='11111111111',
            phone='11988888888',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            nome='Prestador Teste',
            email='prestador@test.com',
            cpf='22222222222',
            phone='11977777777',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([admin, cliente, prestador])
        db.session.commit()
        
        # Criar carteiras com saldo
        WalletService.ensure_user_has_wallet(admin.id)
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo para cliente e prestador
        WalletService.credit_wallet(cliente.id, Decimal('2000.00'), 'Saldo inicial')
        WalletService.credit_wallet(prestador.id, Decimal('1000.00'), 'Saldo inicial')
        
        return admin, cliente, prestador


def test_resolve_dispute_client_wins():
    """Testa resolução de disputa a favor do cliente"""
    print("\n" + "="*80)
    print("TESTE 1: Resolução de Disputa a Favor do Cliente")
    print("="*80)
    
    with app.app_context():
        admin, cliente, prestador = setup_test_data()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            invited_phone='11966666666',
            service_title='Serviço Teste',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar ordem
        print("\n1. Criando ordem...")
        order_result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = order_result['order_id']
        print(f"   ✓ Ordem {order_id} criada")
        
        # Marcar como concluído
        print("\n2. Prestador marca como concluído...")
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        print(f"   ✓ Ordem marcada como concluída")
        
        # Abrir contestação
        print("\n3. Cliente abre contestação...")
        OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=cliente.id,
            reason="Serviço não foi executado conforme combinado. Problemas graves na execução.",
            evidence_files=None
        )
        print(f"   ✓ Contestação aberta")
        
        # Verificar saldos antes da resolução
        print("\n4. Saldos antes da resolução:")
        cliente_wallet_before = WalletService.get_wallet_info(cliente.id)
        prestador_wallet_before = WalletService.get_wallet_info(prestador.id)
        admin_wallet_before = WalletService.get_wallet_info(admin.id)
        
        print(f"   Cliente - Disponível: R$ {cliente_wallet_before['balance']:.2f}, Bloqueado: R$ {cliente_wallet_before['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_wallet_before['balance']:.2f}, Bloqueado: R$ {prestador_wallet_before['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_wallet_before['balance']:.2f}")
        
        # Resolver disputa a favor do cliente
        print("\n5. Admin resolve disputa a favor do CLIENTE...")
        resolve_result = OrderManagementService.resolve_dispute(
            order_id=order_id,
            admin_id=admin.id,
            winner='client',
            admin_notes='Serviço não foi executado adequadamente conforme evidências apresentadas.'
        )
        
        print(f"   ✓ Disputa resolvida: {resolve_result['message']}")
        print(f"   Vencedor: {resolve_result['winner_name']}")
        
        # Verificar saldos após resolução
        print("\n6. Saldos após resolução:")
        cliente_wallet_after = WalletService.get_wallet_info(cliente.id)
        prestador_wallet_after = WalletService.get_wallet_info(prestador.id)
        admin_wallet_after = WalletService.get_wallet_info(admin.id)
        
        print(f"   Cliente - Disponível: R$ {cliente_wallet_after['balance']:.2f}, Bloqueado: R$ {cliente_wallet_after['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_wallet_after['balance']:.2f}, Bloqueado: R$ {prestador_wallet_after['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_wallet_after['balance']:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'resolvida', f"Status deveria ser 'resolvida', mas é '{order.status}'"
        assert order.dispute_winner == 'client', f"Vencedor deveria ser 'client', mas é '{order.dispute_winner}'"
        assert order.dispute_resolved_by == admin.id, "Admin deveria estar registrado como quem resolveu"
        assert order.dispute_resolved_at is not None, "Data de resolução deveria estar preenchida"
        
        # Verificar pagamentos
        payments = resolve_result['payments']
        print("\n7. Detalhes dos pagamentos:")
        print(f"   Valor devolvido ao cliente: R$ {payments['service_value_returned_to_client']:.2f}")
        print(f"   Taxa de contestação para plataforma: R$ {payments['contestation_fee_to_platform']:.2f}")
        print(f"   Taxa de contestação devolvida ao prestador: R$ {payments['contestation_fee_returned_to_provider']:.2f}")
        print(f"   Prestador recebeu: R$ {payments['provider_received']:.2f}")
        
        # Validações
        assert payments['service_value_returned_to_client'] == 100.00, "Cliente deveria receber R$ 100.00"
        assert payments['contestation_fee_to_platform'] == 10.00, "Plataforma deveria receber R$ 10.00"
        assert payments['contestation_fee_returned_to_provider'] == 10.00, "Prestador deveria receber R$ 10.00 de volta"
        assert payments['provider_received'] == 0.0, "Prestador não deveria receber pagamento pelo serviço"
        
        # Cliente deveria ter recebido o valor do serviço de volta
        expected_client_balance = Decimal('2000.00') - Decimal('10.00')  # Perdeu apenas a taxa de contestação
        assert Decimal(str(cliente_wallet_after['balance'])) == expected_client_balance, \
            f"Cliente deveria ter R$ {expected_client_balance:.2f}, mas tem R$ {cliente_wallet_after['balance']:.2f}"
        
        # Prestador deveria ter recebido a taxa de contestação de volta
        expected_provider_balance = Decimal('1000.00')  # Voltou ao saldo inicial
        assert Decimal(str(prestador_wallet_after['balance'])) == expected_provider_balance, \
            f"Prestador deveria ter R$ {expected_provider_balance:.2f}, mas tem R$ {prestador_wallet_after['balance']:.2f}"
        
        # Admin deveria ter recebido a taxa de contestação do cliente
        expected_admin_balance = Decimal('10.00')
        assert Decimal(str(admin_wallet_after['balance'])) == expected_admin_balance, \
            f"Admin deveria ter R$ {expected_admin_balance:.2f}, mas tem R$ {admin_wallet_after['balance']:.2f}"
        
        print("\n✓ TESTE 1 PASSOU: Disputa resolvida corretamente a favor do cliente")


def test_resolve_dispute_provider_wins():
    """Testa resolução de disputa a favor do prestador"""
    print("\n" + "="*80)
    print("TESTE 2: Resolução de Disputa a Favor do Prestador")
    print("="*80)
    
    with app.app_context():
        admin, cliente, prestador = setup_test_data()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            invited_phone='11966666666',
            service_title='Serviço Teste 2',
            service_description='Descrição do serviço 2',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar ordem
        print("\n1. Criando ordem...")
        order_result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = order_result['order_id']
        print(f"   ✓ Ordem {order_id} criada")
        
        # Marcar como concluído
        print("\n2. Prestador marca como concluído...")
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        print(f"   ✓ Ordem marcada como concluída")
        
        # Abrir contestação
        print("\n3. Cliente abre contestação...")
        OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=cliente.id,
            reason="Cliente alega problemas, mas prestador tem provas de que executou corretamente.",
            evidence_files=None
        )
        print(f"   ✓ Contestação aberta")
        
        # Verificar saldos antes da resolução
        print("\n4. Saldos antes da resolução:")
        cliente_wallet_before = WalletService.get_wallet_info(cliente.id)
        prestador_wallet_before = WalletService.get_wallet_info(prestador.id)
        admin_wallet_before = WalletService.get_wallet_info(admin.id)
        
        print(f"   Cliente - Disponível: R$ {cliente_wallet_before['balance']:.2f}, Bloqueado: R$ {cliente_wallet_before['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_wallet_before['balance']:.2f}, Bloqueado: R$ {prestador_wallet_before['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_wallet_before['balance']:.2f}")
        
        # Resolver disputa a favor do prestador
        print("\n5. Admin resolve disputa a favor do PRESTADOR...")
        resolve_result = OrderManagementService.resolve_dispute(
            order_id=order_id,
            admin_id=admin.id,
            winner='provider',
            admin_notes='Prestador apresentou provas suficientes de que o serviço foi executado corretamente.'
        )
        
        print(f"   ✓ Disputa resolvida: {resolve_result['message']}")
        print(f"   Vencedor: {resolve_result['winner_name']}")
        
        # Verificar saldos após resolução
        print("\n6. Saldos após resolução:")
        cliente_wallet_after = WalletService.get_wallet_info(cliente.id)
        prestador_wallet_after = WalletService.get_wallet_info(prestador.id)
        admin_wallet_after = WalletService.get_wallet_info(admin.id)
        
        print(f"   Cliente - Disponível: R$ {cliente_wallet_after['balance']:.2f}, Bloqueado: R$ {cliente_wallet_after['escrow_balance']:.2f}")
        print(f"   Prestador - Disponível: R$ {prestador_wallet_after['balance']:.2f}, Bloqueado: R$ {prestador_wallet_after['escrow_balance']:.2f}")
        print(f"   Admin - Disponível: R$ {admin_wallet_after['balance']:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'resolvida', f"Status deveria ser 'resolvida', mas é '{order.status}'"
        assert order.dispute_winner == 'provider', f"Vencedor deveria ser 'provider', mas é '{order.dispute_winner}'"
        assert order.dispute_resolved_by == admin.id, "Admin deveria estar registrado como quem resolveu"
        assert order.dispute_resolved_at is not None, "Data de resolução deveria estar preenchida"
        
        # Verificar pagamentos
        payments = resolve_result['payments']
        print("\n7. Detalhes dos pagamentos:")
        print(f"   Valor do serviço: R$ {payments['service_value']:.2f}")
        print(f"   Taxa da plataforma: R$ {payments['platform_fee']:.2f}")
        print(f"   Prestador recebeu: R$ {payments['provider_received']:.2f}")
        print(f"   Taxa de contestação devolvida ao prestador: R$ {payments['contestation_fee_returned_to_provider']:.2f}")
        print(f"   Taxa de contestação do cliente para plataforma: R$ {payments['contestation_fee_to_platform']:.2f}")
        
        # Validações
        assert payments['service_value'] == 200.00, "Valor do serviço deveria ser R$ 200.00"
        assert payments['platform_fee'] == 10.00, "Taxa da plataforma deveria ser R$ 10.00 (5%)"
        assert payments['provider_received'] == 190.00, "Prestador deveria receber R$ 190.00"
        assert payments['contestation_fee_returned_to_provider'] == 10.00, "Prestador deveria receber R$ 10.00 de volta"
        assert payments['contestation_fee_to_platform'] == 10.00, "Plataforma deveria receber R$ 10.00 do cliente"
        
        # Cliente perdeu o valor do serviço e a taxa de contestação
        expected_client_balance = Decimal('2000.00') - Decimal('200.00') - Decimal('10.00')
        assert Decimal(str(cliente_wallet_after['balance'])) == expected_client_balance, \
            f"Cliente deveria ter R$ {expected_client_balance:.2f}, mas tem R$ {cliente_wallet_after['balance']:.2f}"
        
        # Prestador recebeu o valor líquido do serviço + taxa de contestação de volta
        expected_provider_balance = Decimal('1000.00') + Decimal('190.00') + Decimal('10.00')
        assert Decimal(str(prestador_wallet_after['balance'])) == expected_provider_balance, \
            f"Prestador deveria ter R$ {expected_provider_balance:.2f}, mas tem R$ {prestador_wallet_after['balance']:.2f}"
        
        # Admin recebeu taxa da plataforma + taxa de contestação do cliente
        expected_admin_balance = Decimal('10.00') + Decimal('10.00')
        assert Decimal(str(admin_wallet_after['balance'])) == expected_admin_balance, \
            f"Admin deveria ter R$ {expected_admin_balance:.2f}, mas tem R$ {admin_wallet_after['balance']:.2f}"
        
        print("\n✓ TESTE 2 PASSOU: Disputa resolvida corretamente a favor do prestador")


def test_resolve_dispute_validations():
    """Testa validações do método resolve_dispute"""
    print("\n" + "="*80)
    print("TESTE 3: Validações do resolve_dispute")
    print("="*80)
    
    with app.app_context():
        admin, cliente, prestador = setup_test_data()
        
        # Criar convite e ordem
        invite = Invite(
            client_id=cliente.id,
            invited_phone='11966666666',
            service_title='Serviço Teste 3',
            service_description='Descrição do serviço 3',
            original_value=Decimal('150.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.commit()
        
        order_result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = order_result['order_id']
        
        # Teste 1: Tentar resolver ordem que não está contestada
        print("\n1. Tentando resolver ordem que não está contestada...")
        try:
            OrderManagementService.resolve_dispute(order_id, admin.id, 'client')
            assert False, "Deveria ter lançado erro"
        except ValueError as e:
            print(f"   ✓ Erro esperado: {e}")
            assert "não está contestada" in str(e).lower()
        
        # Marcar como concluído e abrir contestação
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=cliente.id,
            reason="Motivo da contestação para teste de validações.",
            evidence_files=None
        )
        
        # Teste 2: Tentar resolver com winner inválido
        print("\n2. Tentando resolver com winner inválido...")
        try:
            OrderManagementService.resolve_dispute(order_id, admin.id, 'invalid_winner')
            assert False, "Deveria ter lançado erro"
        except ValueError as e:
            print(f"   ✓ Erro esperado: {e}")
            assert "client" in str(e) and "provider" in str(e)
        
        # Teste 3: Resolver corretamente
        print("\n3. Resolvendo corretamente...")
        resolve_result = OrderManagementService.resolve_dispute(order_id, admin.id, 'client', 'Notas do admin')
        print(f"   ✓ Disputa resolvida com sucesso")
        
        # Teste 4: Tentar resolver ordem já resolvida
        print("\n4. Tentando resolver ordem já resolvida...")
        try:
            OrderManagementService.resolve_dispute(order_id, admin.id, 'provider')
            assert False, "Deveria ter lançado erro"
        except ValueError as e:
            print(f"   ✓ Erro esperado: {e}")
            assert "não está contestada" in str(e).lower()
        
        # Teste 5: Tentar resolver ordem inexistente
        print("\n5. Tentando resolver ordem inexistente...")
        try:
            OrderManagementService.resolve_dispute(99999, admin.id, 'client')
            assert False, "Deveria ter lançado erro"
        except ValueError as e:
            print(f"   ✓ Erro esperado: {e}")
            assert "não encontrada" in str(e).lower()
        
        print("\n✓ TESTE 3 PASSOU: Todas as validações funcionando corretamente")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("INICIANDO TESTES DO MÉTODO resolve_dispute()")
    print("="*80)
    
    try:
        test_resolve_dispute_client_wins()
        test_resolve_dispute_provider_wins()
        test_resolve_dispute_validations()
        
        print("\n" + "="*80)
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
