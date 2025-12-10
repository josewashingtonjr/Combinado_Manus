#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para Task 19: Criar rotas de ordens - APIs JSON

Testa:
- Rota GET /ordens/<id>/status (API)
- Retorno JSON com status, hours_remaining, can_confirm, can_dispute
- Rota GET /ordens/estatisticas (API)
- Retorno JSON com estatísticas do dashboard
- Decorador @login_required em todas as rotas
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, Order, Wallet, Invite
from services.wallet_service import WalletService
from services.order_management_service import OrderManagementService
from datetime import datetime, timedelta
from decimal import Decimal
import json


def test_api_order_status():
    """Testa API GET /ordens/<id>/status"""
    print("\n" + "="*80)
    print("TESTE: API GET /ordens/<id>/status")
    print("="*80)
    
    with app.app_context():
        # Limpar dados de teste
        Order.query.filter(Order.title.like('Teste API%')).delete()
        User.query.filter(User.email.like('teste_api%')).delete()
        db.session.commit()
        
        # Criar usuários de teste
        cliente = User(
            nome='Cliente API',
            email='teste_api_cliente@test.com',
            cpf='11111111001',
            phone='11999999001',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            nome='Prestador API',
            email='teste_api_prestador@test.com',
            cpf='22222222002',
            phone='11999999002',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo
        WalletService.admin_sell_tokens_to_user(cliente.id, Decimal('1000.00'), 'Crédito inicial')
        WalletService.admin_sell_tokens_to_user(prestador.id, Decimal('100.00'), 'Crédito inicial')
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            invited_phone='11999999999',
            service_title='Teste API Status',
            service_description='Teste de API',
            service_category='Instalação',
            original_value=Decimal('500.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'  # Convite precisa estar aceito
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar ordem a partir do convite
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order = result['order']
        
        print(f"\n✓ Ordem criada: ID {order.id}, Status: {order.status}")
        
        # Testar API com cliente logado
        with app.test_client() as client_test:
            # Login como cliente
            response = client_test.post('/auth/login', data={
                'email': 'teste_api_cliente@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            # Chamar API de status
            response = client_test.get(f'/ordens/{order.id}/status')
            
            assert response.status_code == 200, f"Status code esperado 200, recebido {response.status_code}"
            
            data = json.loads(response.data)
            print(f"\n✓ Resposta da API: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Validar campos obrigatórios
            assert 'success' in data, "Campo 'success' não encontrado"
            assert data['success'] == True, "Campo 'success' deve ser True"
            
            assert 'status' in data, "Campo 'status' não encontrado"
            assert data['status'] == 'aguardando_execucao', f"Status esperado 'aguardando_execucao', recebido '{data['status']}'"
            
            assert 'hours_remaining' in data, "Campo 'hours_remaining' não encontrado"
            assert 'can_confirm' in data, "Campo 'can_confirm' não encontrado"
            assert 'can_dispute' in data, "Campo 'can_dispute' não encontrado"
            
            print(f"✓ Status: {data['status']}")
            print(f"✓ Horas restantes: {data['hours_remaining']}")
            print(f"✓ Pode confirmar: {data['can_confirm']}")
            print(f"✓ Pode contestar: {data['can_dispute']}")
            print(f"✓ Pode cancelar: {data['can_cancel']}")
            
        # Testar com ordem em status servico_executado
        OrderManagementService.mark_service_completed(order.id, prestador.id)
        
        with app.test_client() as client_test:
            # Login como cliente
            client_test.post('/auth/login', data={
                'email': 'teste_api_cliente@test.com',
                'password': 'senha123'
            })
            
            response = client_test.get(f'/ordens/{order.id}/status')
            data = json.loads(response.data)
            
            print(f"\n✓ Após marcar como concluído:")
            print(f"  Status: {data['status']}")
            print(f"  Horas restantes: {data['hours_remaining']}")
            print(f"  Pode confirmar: {data['can_confirm']}")
            print(f"  Pode contestar: {data['can_dispute']}")
            
            assert data['status'] == 'servico_executado', "Status deve ser 'servico_executado'"
            assert data['can_confirm'] == True, "Cliente deve poder confirmar"
            assert data['can_dispute'] == True, "Cliente deve poder contestar"
            assert data['hours_remaining'] is not None, "Deve ter horas restantes"
        
        print("\n✅ TESTE PASSOU: API /ordens/<id>/status funcionando corretamente")


def test_api_estatisticas():
    """Testa API GET /ordens/estatisticas"""
    print("\n" + "="*80)
    print("TESTE: API GET /ordens/estatisticas")
    print("="*80)
    
    with app.app_context():
        # Limpar dados de teste
        Order.query.filter(Order.title.like('Teste Estatísticas%')).delete()
        User.query.filter(User.email.like('teste_stats%')).delete()
        db.session.commit()
        
        # Criar usuários de teste
        cliente = User(
            nome='Cliente Stats',
            email='teste_stats_cliente@test.com',
            cpf='33333333003',
            phone='11999999003',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            nome='Prestador Stats',
            email='teste_stats_prestador@test.com',
            cpf='44444444004',
            phone='11999999004',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo
        WalletService.admin_sell_tokens_to_user(cliente.id, Decimal('5000.00'), 'Crédito inicial')
        WalletService.admin_sell_tokens_to_user(prestador.id, Decimal('500.00'), 'Crédito inicial')
        
        # Criar múltiplas ordens com diferentes status
        orders_created = []
        
        for i in range(3):
            invite = Invite(
                client_id=cliente.id,
                invited_phone='11999999999',
                service_title=f'Teste Estatísticas {i+1}',
                service_description='Teste',
                service_category='Instalação',
                original_value=Decimal('300.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'  # Convite precisa estar aceito
            )
            db.session.add(invite)
            db.session.commit()
            
            result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
            orders_created.append(result['order'])
        
        # Marcar uma como concluída
        OrderManagementService.mark_service_completed(orders_created[0].id, prestador.id)
        
        # Marcar outra como concluída e confirmar
        OrderManagementService.mark_service_completed(orders_created[1].id, prestador.id)
        OrderManagementService.confirm_service(orders_created[1].id, cliente.id)
        
        print(f"\n✓ Criadas 3 ordens:")
        print(f"  - Ordem 1: {orders_created[0].status}")
        print(f"  - Ordem 2: {orders_created[1].status}")
        print(f"  - Ordem 3: {orders_created[2].status}")
        
        # Testar API com cliente logado
        with app.test_client() as client_test:
            # Login como cliente
            response = client_test.post('/auth/login', data={
                'email': 'teste_stats_cliente@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            # Definir papel ativo como cliente
            with client_test.session_transaction() as sess:
                sess['active_role'] = 'cliente'
            
            # Chamar API de estatísticas
            response = client_test.get('/ordens/estatisticas')
            
            assert response.status_code == 200, f"Status code esperado 200, recebido {response.status_code}"
            
            data = json.loads(response.data)
            print(f"\n✓ Resposta da API: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Validar estrutura
            assert 'success' in data, "Campo 'success' não encontrado"
            assert data['success'] == True, "Campo 'success' deve ser True"
            
            assert 'statistics' in data, "Campo 'statistics' não encontrado"
            stats = data['statistics']
            
            print(f"\n✓ Estatísticas do cliente:")
            print(f"  Total: {stats.get('total', 0)}")
            print(f"  Aguardando: {stats.get('aguardando', 0)}")
            print(f"  Para confirmar: {stats.get('para_confirmar', 0)}")
            print(f"  Concluídas: {stats.get('concluidas', 0)}")
            print(f"  Canceladas: {stats.get('canceladas', 0)}")
            print(f"  Contestadas: {stats.get('contestadas', 0)}")
            
            # Validar valores esperados
            assert stats['total'] >= 3, f"Total deve ser >= 3, recebido {stats['total']}"
            assert stats['aguardando'] >= 1, f"Aguardando deve ser >= 1, recebido {stats['aguardando']}"
            assert stats['para_confirmar'] >= 1, f"Para confirmar deve ser >= 1, recebido {stats['para_confirmar']}"
            assert stats['concluidas'] >= 1, f"Concluídas deve ser >= 1, recebido {stats['concluidas']}"
        
        # Testar API com prestador logado
        with app.test_client() as client_test:
            # Login como prestador
            client_test.post('/auth/login', data={
                'email': 'teste_stats_prestador@test.com',
                'password': 'senha123'
            })
            
            # Definir papel ativo como prestador
            with client_test.session_transaction() as sess:
                sess['active_role'] = 'prestador'
            
            response = client_test.get('/ordens/estatisticas')
            data = json.loads(response.data)
            
            print(f"\n✓ Estatísticas do prestador:")
            stats = data['statistics']
            print(f"  Total: {stats.get('total', 0)}")
            print(f"  Aguardando: {stats.get('aguardando', 0)}")
            print(f"  Aguardando cliente: {stats.get('aguardando_cliente', 0)}")
            print(f"  Concluídas: {stats.get('concluidas', 0)}")
            
            assert stats['total'] >= 3, "Prestador deve ter >= 3 ordens"
        
        print("\n✅ TESTE PASSOU: API /ordens/estatisticas funcionando corretamente")


def test_api_requires_login():
    """Testa que as APIs exigem login (@login_required)"""
    print("\n" + "="*80)
    print("TESTE: APIs exigem login (@login_required)")
    print("="*80)
    
    with app.app_context():
        with app.test_client() as client_test:
            # Tentar acessar API de status sem login
            response = client_test.get('/ordens/1/status')
            
            # Deve redirecionar para login ou retornar 401/403
            assert response.status_code in [302, 401, 403], \
                f"API sem login deve retornar 302/401/403, recebido {response.status_code}"
            
            print(f"✓ API /ordens/<id>/status sem login: {response.status_code}")
            
            # Tentar acessar API de estatísticas sem login
            response = client_test.get('/ordens/estatisticas')
            
            assert response.status_code in [302, 401, 403], \
                f"API sem login deve retornar 302/401/403, recebido {response.status_code}"
            
            print(f"✓ API /ordens/estatisticas sem login: {response.status_code}")
    
    print("\n✅ TESTE PASSOU: Todas as APIs exigem login")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("INICIANDO TESTES DA TASK 19: APIs JSON")
    print("="*80)
    
    try:
        test_api_requires_login()
        test_api_order_status()
        test_api_estatisticas()
        
        print("\n" + "="*80)
        print("✅ TODOS OS TESTES DA TASK 19 PASSARAM!")
        print("="*80)
        print("\nResumo:")
        print("✓ API GET /ordens/<id>/status implementada")
        print("✓ Retorna JSON com status, hours_remaining, can_confirm, can_dispute")
        print("✓ API GET /ordens/estatisticas implementada")
        print("✓ Retorna JSON com estatísticas do dashboard")
        print("✓ Todas as rotas têm @login_required")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
