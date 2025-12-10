#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste de integração para rotas de pré-ordem

Este teste valida:
- Criação de pré-ordem a partir de convite
- Acesso às rotas com autenticação
- Validações de permissão
- Fluxo completo de negociação
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, PreOrder, PreOrderStatus, Invite, Wallet
from services.pre_order_service import PreOrderService
from datetime import datetime, timedelta
from decimal import Decimal


def setup_test_data():
    """Cria dados de teste e retorna IDs"""
    # Limpar dados de teste anteriores
    PreOrder.query.filter(PreOrder.title.like('TESTE%')).delete()
    Invite.query.filter(Invite.service_title.like('TESTE%')).delete()
    db.session.commit()
    
    # Criar usuários de teste se não existirem
    cliente = User.query.filter_by(email='cliente_teste@test.com').first()
    if not cliente:
        cliente = User(
            nome='Cliente Teste',
            email='cliente_teste@test.com',
            phone='11999999001',
            roles=['cliente']
        )
        cliente.set_password('senha123')
        db.session.add(cliente)
    
    prestador = User.query.filter_by(email='prestador_teste@test.com').first()
    if not prestador:
        prestador = User(
            nome='Prestador Teste',
            email='prestador_teste@test.com',
            phone='11999999002',
            roles=['prestador']
        )
        prestador.set_password('senha123')
        db.session.add(prestador)
    
    db.session.commit()
    
    # Criar carteiras se não existirem
    if not Wallet.query.filter_by(user_id=cliente.id).first():
        wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('1000.00'))
        db.session.add(wallet_cliente)
    
    if not Wallet.query.filter_by(user_id=prestador.id).first():
        wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('500.00'))
        db.session.add(wallet_prestador)
    
    db.session.commit()
    
    # Criar convite de teste
    convite = Invite(
        client_id=cliente.id,
        invited_phone=prestador.phone,
        service_title='TESTE - Serviço de Teste',
        service_description='Descrição do serviço de teste',
        original_value=Decimal('100.00'),
        delivery_date=datetime.now() + timedelta(days=7),
        service_category='teste',
        status='aceito'
    )
    db.session.add(convite)
    db.session.commit()
    
    # Retornar IDs ao invés de objetos
    return cliente.id, prestador.id, convite.id


def test_create_pre_order_from_invite():
    """Testa criação de pré-ordem a partir de convite"""
    print("\n=== Testando Criação de Pré-Ordem ===\n")
    
    with app.app_context():
        cliente_id, prestador_id, convite_id = setup_test_data()
        
        # Criar pré-ordem
        result = PreOrderService.create_from_invite(convite_id)
        
        if result['success']:
            print(f"✅ Pré-ordem criada com sucesso!")
            print(f"   ID: {result['pre_order_id']}")
            print(f"   Cliente: {result['client_id']}")
            print(f"   Prestador: {result['provider_id']}")
            print(f"   Valor: R$ {result['current_value']:.2f}")
            print(f"   Status: {result['status']}")
            
            # Verificar se pré-ordem foi criada no banco
            pre_order = PreOrder.query.get(result['pre_order_id'])
            if pre_order:
                print(f"✅ Pré-ordem encontrada no banco de dados")
                return True, pre_order.id
            else:
                print(f"❌ Pré-ordem não encontrada no banco de dados")
                return False, None
        else:
            print(f"❌ Erro ao criar pré-ordem: {result.get('error')}")
            return False, None


def test_access_with_permission(pre_order_id):
    """Testa acesso à pré-ordem com permissão"""
    print("\n=== Testando Acesso Com Permissão ===\n")
    
    with app.test_client() as client:
        with app.app_context():
            cliente_id, prestador_id, _ = setup_test_data()
            
            # Login como cliente
            with client.session_transaction() as sess:
                sess['user_id'] = cliente_id
                sess['active_role'] = 'cliente'
            
            # Tentar acessar pré-ordem
            response = client.get(f'/pre-ordem/{pre_order_id}')
            
            if response.status_code == 200:
                print(f"✅ Cliente conseguiu acessar pré-ordem (status: {response.status_code})")
                return True
            else:
                print(f"❌ Cliente não conseguiu acessar pré-ordem (status: {response.status_code})")
                return False


def test_access_without_permission(pre_order_id):
    """Testa acesso à pré-ordem sem permissão"""
    print("\n=== Testando Acesso Sem Permissão ===\n")
    
    with app.test_client() as client:
        with app.app_context():
            # Criar usuário não relacionado
            outro_usuario = User.query.filter_by(email='outro@test.com').first()
            if not outro_usuario:
                outro_usuario = User(
                    nome='Outro Usuário',
                    email='outro@test.com',
                    phone='11999999003',
                    roles=['cliente']
                )
                outro_usuario.set_password('senha123')
                db.session.add(outro_usuario)
                db.session.commit()
            
            # Login como usuário não relacionado
            with client.session_transaction() as sess:
                sess['user_id'] = outro_usuario.id
                sess['active_role'] = 'cliente'
            
            # Tentar acessar pré-ordem
            response = client.get(f'/pre-ordem/{pre_order_id}')
            
            # Deve redirecionar ou retornar 403
            if response.status_code in [302, 403]:
                print(f"✅ Acesso negado corretamente (status: {response.status_code})")
                return True
            else:
                print(f"❌ Acesso não foi negado (status: {response.status_code})")
                return False


def test_api_endpoints(pre_order_id):
    """Testa endpoints de API"""
    print("\n=== Testando Endpoints de API ===\n")
    
    with app.test_client() as client:
        with app.app_context():
            cliente_id, prestador_id, _ = setup_test_data()
            
            # Login como cliente
            with client.session_transaction() as sess:
                sess['user_id'] = cliente_id
                sess['active_role'] = 'cliente'
            
            # Testar endpoint de status
            response = client.get(f'/pre-ordem/{pre_order_id}/status')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print(f"✅ Endpoint /status funcionando")
                    print(f"   Status: {data.get('status')}")
                else:
                    print(f"❌ Endpoint /status retornou erro")
                    return False
            else:
                print(f"❌ Endpoint /status falhou (status: {response.status_code})")
                return False
            
            # Testar endpoint de verificar saldo
            response = client.get(f'/pre-ordem/{pre_order_id}/verificar-saldo')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print(f"✅ Endpoint /verificar-saldo funcionando")
                    balance_check = data.get('balance_check', {})
                    print(f"   Saldo suficiente: {balance_check.get('is_sufficient')}")
                else:
                    print(f"❌ Endpoint /verificar-saldo retornou erro")
                    return False
            else:
                print(f"❌ Endpoint /verificar-saldo falhou (status: {response.status_code})")
                return False
            
            # Testar endpoint de histórico
            response = client.get(f'/pre-ordem/{pre_order_id}/historico')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print(f"✅ Endpoint /historico funcionando")
                    print(f"   Total de eventos: {data.get('total_events')}")
                else:
                    print(f"❌ Endpoint /historico retornou erro")
                    return False
            else:
                print(f"❌ Endpoint /historico falhou (status: {response.status_code})")
                return False
            
            return True


def main():
    """Executa todos os testes de integração"""
    print("=" * 60)
    print("TESTE DE INTEGRAÇÃO - ROTAS DE PRÉ-ORDEM")
    print("=" * 60)
    
    results = []
    pre_order_id = None
    
    # Teste 1: Criar pré-ordem
    success, pre_order_id = test_create_pre_order_from_invite()
    results.append(("Criação de Pré-Ordem", success))
    
    if pre_order_id:
        # Teste 2: Acesso com permissão
        results.append(("Acesso Com Permissão", test_access_with_permission(pre_order_id)))
        
        # Teste 3: Acesso sem permissão
        results.append(("Acesso Sem Permissão", test_access_without_permission(pre_order_id)))
        
        # Teste 4: Endpoints de API
        results.append(("Endpoints de API", test_api_endpoints(pre_order_id)))
    else:
        print("\n⚠️  Pulando testes que dependem de pré-ordem criada")
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
