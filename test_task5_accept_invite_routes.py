#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para validar as rotas de aceitação de convites (Tarefa 5)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, Invite, Order, Wallet
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def setup_test_data():
    """Configurar dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        Order.query.delete()
        Invite.query.delete()
        Wallet.query.delete()
        User.query.delete()
        db.session.commit()
        
        # Criar cliente
        cliente = User(
            nome='Cliente Test',
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
            nome='Prestador Test',
            email='prestador@test.com',
            cpf='22222222222',
            phone='11888888888',
            roles='prestador'
        )
        prestador.set_password('senha123')
        db.session.add(prestador)
        db.session.flush()
        
        # Criar carteiras com saldo suficiente
        wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('1000.00'))
        wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('1000.00'))
        db.session.add(wallet_cliente)
        db.session.add(wallet_prestador)
        db.session.commit()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste',
            service_description='Descrição do serviço',
            service_category='Tecnologia',
            original_value=Decimal('100.00'),
            current_value=Decimal('100.00'),
            delivery_date=datetime.now() + timedelta(days=7),
            status='pendente',
            token='test_token_123',
            client_accepted=False,
            provider_accepted=False
        )
        db.session.add(invite)
        db.session.commit()
        
        return cliente, prestador, invite

def test_cliente_aceitar_convite():
    """Testar rota de aceitação do cliente"""
    print("\n=== Teste: Cliente Aceitar Convite ===")
    
    with app.app_context():
        cliente, prestador, invite = setup_test_data()
        
        # Simular requisição POST para aceitar convite
        with app.test_client() as client:
            # Login como cliente
            client.post('/auth/user-login', data={
                'email': 'cliente@test.com',
                'password': 'senha123'
            })
            
            # Aceitar convite
            response = client.post(f'/cliente/convites/{invite.id}/aceitar', follow_redirects=True)
            
            # Verificar resposta
            assert response.status_code == 200, f"Status code esperado 200, obtido {response.status_code}"
            
            # Verificar se o convite foi marcado como aceito pelo cliente
            db.session.refresh(invite)
            assert invite.client_accepted == True, "Cliente deveria ter aceitado o convite"
            assert invite.client_accepted_at is not None, "Data de aceitação do cliente deveria estar preenchida"
            
            print("✓ Cliente aceitou o convite com sucesso")
            print(f"  - client_accepted: {invite.client_accepted}")
            print(f"  - client_accepted_at: {invite.client_accepted_at}")
            print(f"  - Status do convite: {invite.status}")

def test_prestador_aceitar_convite():
    """Testar rota de aceitação do prestador"""
    print("\n=== Teste: Prestador Aceitar Convite ===")
    
    with app.app_context():
        cliente, prestador, invite = setup_test_data()
        
        # Simular requisição POST para aceitar convite
        with app.test_client() as client:
            # Login como prestador
            client.post('/auth/user-login', data={
                'email': 'prestador@test.com',
                'password': 'senha123'
            })
            
            # Aceitar convite
            response = client.post(f'/prestador/convites/{invite.token}/aceitar', follow_redirects=True)
            
            # Verificar resposta
            assert response.status_code == 200, f"Status code esperado 200, obtido {response.status_code}"
            
            # Verificar se o convite foi marcado como aceito pelo prestador
            db.session.refresh(invite)
            assert invite.provider_accepted == True, "Prestador deveria ter aceitado o convite"
            assert invite.provider_accepted_at is not None, "Data de aceitação do prestador deveria estar preenchida"
            
            print("✓ Prestador aceitou o convite com sucesso")
            print(f"  - provider_accepted: {invite.provider_accepted}")
            print(f"  - provider_accepted_at: {invite.provider_accepted_at}")
            print(f"  - Status do convite: {invite.status}")

def test_aceitacao_mutua_cria_ordem():
    """Testar que aceitação mútua cria ordem automaticamente"""
    print("\n=== Teste: Aceitação Mútua Cria Ordem ===")
    
    with app.app_context():
        cliente, prestador, invite = setup_test_data()
        
        with app.test_client() as client:
            # Login como prestador e aceitar
            client.post('/auth/user-login', data={
                'email': 'prestador@test.com',
                'password': 'senha123'
            })
            client.post(f'/prestador/convites/{invite.token}/aceitar')
            
            # Logout e login como cliente
            client.get('/auth/logout')
            client.post('/auth/user-login', data={
                'email': 'cliente@test.com',
                'password': 'senha123'
            })
            
            # Cliente aceita (segunda aceitação - deve criar ordem)
            response = client.post(f'/cliente/convites/{invite.id}/aceitar', follow_redirects=True)
            
            # Verificar se ordem foi criada
            db.session.refresh(invite)
            orders = Order.query.filter_by(invite_id=invite.id).all()
            
            assert len(orders) > 0, "Ordem deveria ter sido criada após aceitação mútua"
            assert invite.status == 'convertido', f"Status do convite deveria ser 'convertido', mas é '{invite.status}'"
            
            order = orders[0]
            print("✓ Ordem criada automaticamente após aceitação mútua")
            print(f"  - Ordem ID: {order.id}")
            print(f"  - Status da ordem: {order.status}")
            print(f"  - Valor: {order.value}")
            print(f"  - Cliente ID: {order.client_id}")
            print(f"  - Prestador ID: {order.provider_id}")

def test_saldo_insuficiente_cliente():
    """Testar erro de saldo insuficiente do cliente"""
    print("\n=== Teste: Saldo Insuficiente Cliente ===")
    
    with app.app_context():
        cliente, prestador, invite = setup_test_data()
        
        # Remover saldo do cliente
        wallet = Wallet.query.filter_by(user_id=cliente.id).first()
        wallet.balance = Decimal('0.00')
        db.session.commit()
        
        with app.test_client() as client:
            # Login como cliente
            client.post('/auth/user-login', data={
                'email': 'cliente@test.com',
                'password': 'senha123'
            })
            
            # Tentar aceitar convite
            response = client.post(f'/cliente/convites/{invite.id}/aceitar', follow_redirects=True)
            
            # Verificar que o convite não foi aceito
            db.session.refresh(invite)
            assert invite.client_accepted == False, "Cliente não deveria ter conseguido aceitar sem saldo"
            
            # Verificar mensagem de erro na resposta
            assert b'saldo' in response.data.lower() or b'insuficiente' in response.data.lower(), \
                "Mensagem de erro sobre saldo deveria aparecer"
            
            print("✓ Erro de saldo insuficiente tratado corretamente")
            print(f"  - Convite não foi aceito")
            print(f"  - Mensagem de erro exibida ao usuário")

def test_saldo_insuficiente_prestador():
    """Testar erro de saldo insuficiente do prestador"""
    print("\n=== Teste: Saldo Insuficiente Prestador ===")
    
    with app.app_context():
        cliente, prestador, invite = setup_test_data()
        
        # Remover saldo do prestador
        wallet = Wallet.query.filter_by(user_id=prestador.id).first()
        wallet.balance = Decimal('0.00')
        db.session.commit()
        
        with app.test_client() as client:
            # Login como prestador
            client.post('/auth/user-login', data={
                'email': 'prestador@test.com',
                'password': 'senha123'
            })
            
            # Tentar aceitar convite
            response = client.post(f'/prestador/convites/{invite.token}/aceitar', follow_redirects=True)
            
            # Verificar que o convite não foi aceito
            db.session.refresh(invite)
            assert invite.provider_accepted == False, "Prestador não deveria ter conseguido aceitar sem saldo"
            
            # Verificar mensagem de erro na resposta
            assert b'saldo' in response.data.lower() or b'insuficiente' in response.data.lower(), \
                "Mensagem de erro sobre saldo deveria aparecer"
            
            print("✓ Erro de saldo insuficiente tratado corretamente")
            print(f"  - Convite não foi aceito")
            print(f"  - Mensagem de erro exibida ao usuário")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTE DAS ROTAS DE ACEITAÇÃO DE CONVITES (TAREFA 5)")
    print("=" * 60)
    
    try:
        test_cliente_aceitar_convite()
        test_prestador_aceitar_convite()
        test_aceitacao_mutua_cria_ordem()
        test_saldo_insuficiente_cliente()
        test_saldo_insuficiente_prestador()
        
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
