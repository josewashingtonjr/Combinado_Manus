#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste dos novos métodos de aceitação do InviteService
Testa accept_invite_as_client e accept_invite_as_provider
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, Invite
from services.invite_service import InviteService
from services.wallet_service import WalletService
from services.admin_service import AdminService
from datetime import datetime, timedelta
from decimal import Decimal

def setup_test_data():
    """Cria dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # Criar cliente
        cliente = User(
            nome='Cliente Teste',
            email='cliente@test.com',
            cpf='11111111111',
            phone='11999999999',
            roles='cliente'
        )
        cliente.set_password('senha123')
        db.session.add(cliente)
        db.session.flush()
        
        # Criar prestador
        prestador = User(
            nome='Prestador Teste',
            email='prestador@test.com',
            cpf='22222222222',
            phone='11888888888',
            roles='prestador'
        )
        prestador.set_password('senha123')
        db.session.add(prestador)
        db.session.flush()
        
        # Criar carteiras para os usuários
        WalletService.create_wallet_for_user(cliente)
        WalletService.create_wallet_for_user(prestador)
        
        # Adicionar saldo aos usuários
        AdminService.add_tokens_to_user(cliente, Decimal('500.00'), 'Saldo inicial para teste')
        AdminService.add_tokens_to_user(prestador, Decimal('100.00'), 'Saldo inicial para teste')
        
        # Criar convite
        delivery_date = datetime.utcnow() + timedelta(days=7)
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            delivery_date=delivery_date,
            expires_at=delivery_date
        )
        db.session.add(invite)
        db.session.commit()
        
        # Retornar IDs para evitar problemas de sessão
        return cliente.id, prestador.id, invite.id

def test_accept_invite_as_client():
    """Testa aceitação do convite pelo cliente"""
    print("\n=== Teste: Cliente aceita convite ===")
    
    with app.app_context():
        cliente_id, prestador_id, invite_id = setup_test_data()
        
        # Recarregar objetos na sessão atual
        invite = Invite.query.get(invite_id)
        
        print(f"Convite ID: {invite.id}")
        print(f"Cliente ID: {cliente_id}")
        print(f"Prestador ID: {prestador_id}")
        print(f"Valor do serviço: R$ {invite.original_value}")
        print(f"Saldo do cliente: R$ {WalletService.get_wallet_balance(cliente_id)}")
        
        # Cliente aceita o convite
        try:
            result = InviteService.accept_invite_as_client(invite.id, cliente_id)
            
            print(f"\n✓ Cliente aceitou o convite com sucesso!")
            print(f"  - Ordem criada: {result.get('order_created', False)}")
            print(f"  - Mensagem: {result.get('message', 'N/A')}")
            
            if result.get('order_created'):
                print(f"  - Order ID: {result.get('order_id')}")
            else:
                print(f"  - Aguardando: {result.get('pending_acceptance_from', 'N/A')}")
            
            # Verificar estado do convite
            db.session.refresh(invite)
            print(f"\nEstado do convite após aceitação do cliente:")
            print(f"  - client_accepted: {invite.client_accepted}")
            print(f"  - provider_accepted: {invite.provider_accepted}")
            print(f"  - is_mutually_accepted: {invite.is_mutually_accepted}")
            print(f"  - pending_acceptance_from: {invite.pending_acceptance_from}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Erro ao aceitar convite como cliente: {str(e)}")
            return False

def test_accept_invite_as_provider():
    """Testa aceitação do convite pelo prestador"""
    print("\n=== Teste: Prestador aceita convite ===")
    
    with app.app_context():
        cliente_id, prestador_id, invite_id = setup_test_data()
        
        # Recarregar objetos
        invite = Invite.query.get(invite_id)
        
        print(f"Convite ID: {invite.id}")
        print(f"Cliente ID: {cliente_id}")
        print(f"Prestador ID: {prestador_id}")
        print(f"Taxa de contestação: R$ {InviteService.CONTESTATION_FEE}")
        print(f"Saldo do prestador: R$ {WalletService.get_wallet_balance(prestador_id)}")
        
        # Prestador aceita o convite
        try:
            result = InviteService.accept_invite_as_provider(invite.id, prestador_id)
            
            print(f"\n✓ Prestador aceitou o convite com sucesso!")
            print(f"  - Ordem criada: {result.get('order_created', False)}")
            print(f"  - Mensagem: {result.get('message', 'N/A')}")
            
            if result.get('order_created'):
                print(f"  - Order ID: {result.get('order_id')}")
            else:
                print(f"  - Aguardando: {result.get('pending_acceptance_from', 'N/A')}")
            
            # Verificar estado do convite
            db.session.refresh(invite)
            print(f"\nEstado do convite após aceitação do prestador:")
            print(f"  - client_accepted: {invite.client_accepted}")
            print(f"  - provider_accepted: {invite.provider_accepted}")
            print(f"  - is_mutually_accepted: {invite.is_mutually_accepted}")
            print(f"  - pending_acceptance_from: {invite.pending_acceptance_from}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Erro ao aceitar convite como prestador: {str(e)}")
            return False

def test_mutual_acceptance():
    """Testa aceitação mútua (ambas as partes aceitam)"""
    print("\n=== Teste: Aceitação Mútua ===")
    
    with app.app_context():
        cliente_id, prestador_id, invite_id = setup_test_data()
        
        # Recarregar objetos
        invite = Invite.query.get(invite_id)
        
        print(f"Convite ID: {invite.id}")
        print(f"Cliente ID: {cliente_id}")
        print(f"Prestador ID: {prestador_id}")
        print(f"Valor do serviço: R$ {invite.original_value}")
        print(f"Saldo do cliente: R$ {WalletService.get_wallet_balance(cliente_id)}")
        print(f"Saldo do prestador: R$ {WalletService.get_wallet_balance(prestador_id)}")
        
        try:
            # 1. Cliente aceita primeiro
            print("\n1. Cliente aceita o convite...")
            result1 = InviteService.accept_invite_as_client(invite.id, cliente_id)
            print(f"   ✓ {result1.get('message')}")
            print(f"   - Ordem criada: {result1.get('order_created', False)}")
            
            # 2. Prestador aceita depois
            print("\n2. Prestador aceita o convite...")
            result2 = InviteService.accept_invite_as_provider(invite.id, prestador_id)
            print(f"   ✓ {result2.get('message')}")
            print(f"   - Ordem criada: {result2.get('order_created', False)}")
            
            if result2.get('order_created'):
                print(f"\n✓ SUCESSO! Ordem #{result2.get('order_id')} criada automaticamente!")
                
                # Verificar estado final do convite
                db.session.refresh(invite)
                print(f"\nEstado final do convite:")
                print(f"  - client_accepted: {invite.client_accepted}")
                print(f"  - provider_accepted: {invite.provider_accepted}")
                print(f"  - is_mutually_accepted: {invite.is_mutually_accepted}")
                print(f"  - status: {invite.status}")
                print(f"  - order_id: {invite.order_id}")
                
                return True
            else:
                print(f"\n✗ Ordem não foi criada após aceitação mútua")
                return False
            
        except Exception as e:
            print(f"\n✗ Erro no teste de aceitação mútua: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_insufficient_balance_client():
    """Testa erro de saldo insuficiente do cliente"""
    print("\n=== Teste: Saldo Insuficiente do Cliente ===")
    
    with app.app_context():
        cliente_id, prestador_id, invite_id = setup_test_data()
        
        # Recarregar objetos
        invite = Invite.query.get(invite_id)
        
        # Remover saldo do cliente (transferir para escrow temporariamente)
        from models import Wallet
        wallet = Wallet.query.filter_by(user_id=cliente_id).first()
        wallet.balance -= Decimal('450.00')
        db.session.commit()
        
        print(f"Convite ID: {invite.id}")
        print(f"Valor do serviço: R$ {invite.original_value}")
        print(f"Saldo do cliente: R$ {WalletService.get_wallet_balance(cliente_id)}")
        
        try:
            result = InviteService.accept_invite_as_client(invite.id, cliente_id)
            print(f"\n✗ Deveria ter falhado por saldo insuficiente!")
            return False
            
        except ValueError as e:
            if 'Saldo insuficiente' in str(e):
                print(f"\n✓ Erro esperado capturado: {str(e)}")
                return True
            else:
                print(f"\n✗ Erro inesperado: {str(e)}")
                return False

def test_insufficient_balance_provider():
    """Testa erro de saldo insuficiente do prestador"""
    print("\n=== Teste: Saldo Insuficiente do Prestador ===")
    
    with app.app_context():
        cliente_id, prestador_id, invite_id = setup_test_data()
        
        # Recarregar objetos
        invite = Invite.query.get(invite_id)
        
        # Remover saldo do prestador
        from models import Wallet
        wallet = Wallet.query.filter_by(user_id=prestador_id).first()
        wallet.balance -= Decimal('95.00')
        db.session.commit()
        
        print(f"Convite ID: {invite.id}")
        print(f"Taxa de contestação: R$ {InviteService.CONTESTATION_FEE}")
        print(f"Saldo do prestador: R$ {WalletService.get_wallet_balance(prestador_id)}")
        
        try:
            result = InviteService.accept_invite_as_provider(invite.id, prestador_id)
            print(f"\n✗ Deveria ter falhado por saldo insuficiente!")
            return False
            
        except ValueError as e:
            if 'Saldo insuficiente' in str(e):
                print(f"\n✓ Erro esperado capturado: {str(e)}")
                return True
            else:
                print(f"\n✗ Erro inesperado: {str(e)}")
                return False

if __name__ == '__main__':
    print("=" * 70)
    print("TESTES DOS NOVOS MÉTODOS DE ACEITAÇÃO DO INVITESERVICE")
    print("=" * 70)
    
    results = []
    
    # Executar testes
    results.append(("Cliente aceita convite", test_accept_invite_as_client()))
    results.append(("Prestador aceita convite", test_accept_invite_as_provider()))
    results.append(("Aceitação mútua", test_mutual_acceptance()))
    results.append(("Saldo insuficiente - Cliente", test_insufficient_balance_client()))
    results.append(("Saldo insuficiente - Prestador", test_insufficient_balance_provider()))
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n✓ TODOS OS TESTES PASSARAM!")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} TESTE(S) FALHARAM")
        sys.exit(1)
