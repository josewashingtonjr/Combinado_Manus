#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a implementação do cancelamento de ordem com multa
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Order, Wallet, Transaction, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from services.config_service import ConfigService


def setup_test_data():
    """Configura dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        Transaction.query.delete()
        Order.query.delete()
        Invite.query.delete()
        Wallet.query.delete()
        User.query.filter(User.id > 1).delete()
        
        # Criar usuários de teste
        cliente = User(
            id=100,
            email='cliente_test@test.com',
            nome='Cliente Teste',
            cpf='11111111111',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            id=200,
            email='prestador_test@test.com',
            nome='Prestador Teste',
            cpf='22222222222',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add(cliente)
        db.session.add(prestador)
        db.session.flush()
        
        # Criar carteiras com saldo
        cliente_wallet = Wallet(user_id=100, balance=Decimal('1000.00'), escrow_balance=Decimal('0.00'))
        prestador_wallet = Wallet(user_id=200, balance=Decimal('500.00'), escrow_balance=Decimal('0.00'))
        
        db.session.add(cliente_wallet)
        db.session.add(prestador_wallet)
        
        # Garantir que admin tem carteira
        WalletService.ensure_admin_has_wallet()
        
        db.session.commit()
        
        print("✓ Dados de teste criados com sucesso")
        print(f"  Cliente ID: {cliente.id}, Saldo: R$ {cliente_wallet.balance}")
        print(f"  Prestador ID: {prestador.id}, Saldo: R$ {prestador_wallet.balance}")


def test_cancel_order_by_client():
    """Testa cancelamento de ordem pelo cliente"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE 1: Cancelamento de ordem pelo CLIENTE")
        print("="*80)
        
        # Criar convite
        invite = Invite(
            client_id=100,
            invited_phone='11999999999',
            service_title='Instalação Elétrica',
            service_description='Instalação de tomadas',
            service_category='eletricista',
            original_value=Decimal('500.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar ordem a partir do convite
        result = OrderManagementService.create_order_from_invite(
            invite_id=invite.id,
            provider_id=200
        )
        
        order_id = result['order_id']
        print(f"\n✓ Ordem {order_id} criada com sucesso")
        print(f"  Valor do serviço: R$ {result['effective_value']:.2f}")
        print(f"  Bloqueado cliente: R$ {result['client_escrow_amount']:.2f}")
        print(f"  Bloqueado prestador: R$ {result['provider_escrow_amount']:.2f}")
        
        # Verificar saldos antes do cancelamento
        cliente_wallet = Wallet.query.filter_by(user_id=100).first()
        prestador_wallet = Wallet.query.filter_by(user_id=200).first()
        
        print(f"\nSaldos ANTES do cancelamento:")
        print(f"  Cliente - Disponível: R$ {cliente_wallet.balance:.2f}, Escrow: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"  Prestador - Disponível: R$ {prestador_wallet.balance:.2f}, Escrow: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # Cancelar ordem pelo cliente
        cancel_result = OrderManagementService.cancel_order(
            order_id=order_id,
            user_id=100,
            reason="Mudança de planos, não preciso mais do serviço"
        )
        
        print(f"\n✓ Ordem cancelada com sucesso pelo CLIENTE")
        print(f"  Multa aplicada: R$ {cancel_result['cancellation_fee']:.2f} ({cancel_result['cancellation_fee_percentage']:.1f}%)")
        print(f"  Plataforma recebeu: R$ {cancel_result['platform_share']:.2f}")
        print(f"  Prestador recebeu (compensação): R$ {cancel_result['injured_party_share']:.2f}")
        
        # Verificar saldos após cancelamento
        db.session.refresh(cliente_wallet)
        db.session.refresh(prestador_wallet)
        
        print(f"\nSaldos DEPOIS do cancelamento:")
        print(f"  Cliente - Disponível: R$ {cliente_wallet.balance:.2f}, Escrow: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"  Prestador - Disponível: R$ {prestador_wallet.balance:.2f}, Escrow: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        print(f"\nStatus da ordem: {order.status}")
        print(f"Cancelada por: user_id {order.cancelled_by}")
        print(f"Motivo: {order.cancellation_reason}")
        
        return True


def test_cancel_order_by_provider():
    """Testa cancelamento de ordem pelo prestador"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE 2: Cancelamento de ordem pelo PRESTADOR")
        print("="*80)
        
        # Criar convite
        invite = Invite(
            client_id=100,
            invited_phone='11999999999',
            service_title='Conserto de Encanamento',
            service_description='Conserto de vazamento',
            service_category='encanador',
            original_value=Decimal('300.00'),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            status='aceito'
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar ordem a partir do convite
        result = OrderManagementService.create_order_from_invite(
            invite_id=invite.id,
            provider_id=200
        )
        
        order_id = result['order_id']
        print(f"\n✓ Ordem {order_id} criada com sucesso")
        print(f"  Valor do serviço: R$ {result['effective_value']:.2f}")
        
        # Verificar saldos antes do cancelamento
        cliente_wallet = Wallet.query.filter_by(user_id=100).first()
        prestador_wallet = Wallet.query.filter_by(user_id=200).first()
        
        print(f"\nSaldos ANTES do cancelamento:")
        print(f"  Cliente - Disponível: R$ {cliente_wallet.balance:.2f}, Escrow: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"  Prestador - Disponível: R$ {prestador_wallet.balance:.2f}, Escrow: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # Cancelar ordem pelo prestador
        cancel_result = OrderManagementService.cancel_order(
            order_id=order_id,
            user_id=200,
            reason="Imprevisto pessoal, não poderei realizar o serviço"
        )
        
        print(f"\n✓ Ordem cancelada com sucesso pelo PRESTADOR")
        print(f"  Multa aplicada: R$ {cancel_result['cancellation_fee']:.2f} ({cancel_result['cancellation_fee_percentage']:.1f}%)")
        print(f"  Plataforma recebeu: R$ {cancel_result['platform_share']:.2f}")
        print(f"  Cliente recebeu (compensação): R$ {cancel_result['injured_party_share']:.2f}")
        
        # Verificar saldos após cancelamento
        db.session.refresh(cliente_wallet)
        db.session.refresh(prestador_wallet)
        
        print(f"\nSaldos DEPOIS do cancelamento:")
        print(f"  Cliente - Disponível: R$ {cliente_wallet.balance:.2f}, Escrow: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"  Prestador - Disponível: R$ {prestador_wallet.balance:.2f}, Escrow: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        print(f"\nStatus da ordem: {order.status}")
        print(f"Cancelada por: user_id {order.cancelled_by}")
        print(f"Motivo: {order.cancellation_reason}")
        
        return True


def test_validation_errors():
    """Testa validações de erro"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE 3: Validações de erro")
        print("="*80)
        
        # Criar uma ordem para testar
        invite = Invite(
            client_id=100,
            invited_phone='11999999999',
            service_title='Pintura',
            service_description='Pintura de parede',
            service_category='pintor',
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=3),
            status='aceito'
        )
        db.session.add(invite)
        db.session.flush()
        
        result = OrderManagementService.create_order_from_invite(
            invite_id=invite.id,
            provider_id=200
        )
        order_id = result['order_id']
        
        # Teste 1: Motivo vazio
        print("\n1. Testando cancelamento sem motivo...")
        try:
            OrderManagementService.cancel_order(order_id=order_id, user_id=100, reason="")
            print("  ✗ ERRO: Deveria ter lançado exceção")
            return False
        except ValueError as e:
            print(f"  ✓ Exceção esperada: {e}")
        
        # Teste 2: Usuário não autorizado
        print("\n2. Testando cancelamento por usuário não autorizado...")
        try:
            OrderManagementService.cancel_order(order_id=order_id, user_id=999, reason="Teste")
            print("  ✗ ERRO: Deveria ter lançado exceção")
            return False
        except ValueError as e:
            print(f"  ✓ Exceção esperada: {e}")
        
        # Teste 3: Ordem não encontrada
        print("\n3. Testando cancelamento de ordem inexistente...")
        try:
            OrderManagementService.cancel_order(order_id=99999, user_id=100, reason="Teste")
            print("  ✗ ERRO: Deveria ter lançado exceção")
            return False
        except ValueError as e:
            print(f"  ✓ Exceção esperada: {e}")
        
        # Teste 4: Cancelar ordem já concluída
        print("\n4. Testando cancelamento de ordem com status inválido...")
        order = Order.query.get(order_id)
        order.status = 'servico_executado'
        db.session.commit()
        
        try:
            OrderManagementService.cancel_order(order_id=order_id, user_id=100, reason="Teste")
            print("  ✗ ERRO: Deveria ter lançado exceção")
            return False
        except ValueError as e:
            print(f"  ✓ Exceção esperada: {e}")
        
        print("\n✓ Todas as validações funcionaram corretamente")
        return True


def main():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("INICIANDO TESTES DE CANCELAMENTO DE ORDEM COM MULTA")
    print("="*80)
    
    try:
        setup_test_data()
        
        success = True
        success = test_cancel_order_by_client() and success
        success = test_cancel_order_by_provider() and success
        success = test_validation_errors() and success
        
        if success:
            print("\n" + "="*80)
            print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
            print("="*80)
            return 0
        else:
            print("\n" + "="*80)
            print("✗ ALGUNS TESTES FALHARAM")
            print("="*80)
            return 1
            
    except Exception as e:
        print(f"\n✗ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
