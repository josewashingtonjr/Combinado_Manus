#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a implementação da Tarefa 18: Rota de Cancelamento de Ordem
"""

from app import app, db
from models import User, Wallet, Invite, Order
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from decimal import Decimal
from datetime import datetime, timedelta


def test_cancel_order_route():
    """Testa a rota POST /ordens/<id>/cancelar"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Rota POST /ordens/<id>/cancelar")
        print("="*80)
        
        # Limpar dados de teste
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(Transaction).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).filter(User.id >= 100).delete()
        db.session.commit()
        
        # Criar usuários de teste
        import json
        cliente = User(
            id=100,
            nome="Cliente Teste",
            email="cliente@test.com",
            cpf="11111111111",
            phone="11999999001",
            password_hash="hash",
            roles=json.dumps(['cliente'])
        )
        
        prestador = User(
            id=200,
            nome="Prestador Teste",
            email="prestador@test.com",
            cpf="22222222222",
            phone="11999999002",
            password_hash="hash",
            roles=json.dumps(['prestador'])
        )
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        WalletService.credit_wallet(cliente.id, Decimal('1000.00'), 'Saldo inicial', 'credito')
        WalletService.credit_wallet(prestador.id, Decimal('500.00'), 'Saldo inicial', 'credito')
        
        # Criar convite
        convite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="Serviço de Teste",
            service_description="Teste de cancelamento via rota",
            service_category="Manutenção",
            original_value=Decimal('500.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(convite)
        db.session.flush()
        
        # Criar ordem
        result = OrderManagementService.create_order_from_invite(
            invite_id=convite.id,
            provider_id=prestador.id
        )
        
        order_id = result['order_id']
        print(f"\n✓ Ordem {order_id} criada com sucesso")
        
        # Testar rota de cancelamento
        print("\n1. Testando cancelamento via rota HTTP...")
        
        # Desabilitar CSRF para testes
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            # Fazer login como cliente
            with client.session_transaction() as sess:
                sess['user_id'] = cliente.id
                sess['active_role'] = 'cliente'
            
            # Enviar requisição POST para cancelar
            response = client.post(
                f'/ordens/{order_id}/cancelar',
                data={'reason': 'Teste de cancelamento via rota HTTP'},
                follow_redirects=False
            )
            
            print(f"  Status Code: {response.status_code}")
            print(f"  Redirect: {response.location if response.status_code == 302 else 'N/A'}")
            
            # Verificar se redirecionou corretamente
            assert response.status_code == 302, "Deveria redirecionar após cancelamento"
            assert f'/ordens/{order_id}' in response.location, "Deveria redirecionar para detalhes da ordem"
            
            print("  ✓ Redirecionamento correto")
        
        # Verificar se a ordem foi cancelada
        order = Order.query.get(order_id)
        assert order.status == 'cancelada', f"Status deveria ser 'cancelada', mas é '{order.status}'"
        assert order.cancelled_by == cliente.id, "Deveria ter sido cancelada pelo cliente"
        assert order.cancellation_reason == 'Teste de cancelamento via rota HTTP'
        
        print("  ✓ Ordem cancelada com sucesso")
        print(f"  Status: {order.status}")
        print(f"  Cancelada por: user_id {order.cancelled_by}")
        print(f"  Motivo: {order.cancellation_reason}")
        
        # Testar validação: cancelamento sem motivo
        print("\n2. Testando validação: cancelamento sem motivo...")
        
        # Criar nova ordem para teste
        convite2 = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="Serviço de Teste 2",
            service_description="Teste de validação",
            service_category="Manutenção",
            original_value=Decimal('300.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito'
        )
        db.session.add(convite2)
        db.session.flush()
        
        result2 = OrderManagementService.create_order_from_invite(
            invite_id=convite2.id,
            provider_id=prestador.id
        )
        order_id2 = result2['order_id']
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = cliente.id
                sess['active_role'] = 'cliente'
            
            # Tentar cancelar sem motivo
            response = client.post(
                f'/ordens/{order_id2}/cancelar',
                data={'reason': ''},  # Motivo vazio
                follow_redirects=True
            )
            
            # Verificar que a ordem NÃO foi cancelada
            order2 = Order.query.get(order_id2)
            assert order2.status == 'aguardando_execucao', "Ordem não deveria ter sido cancelada"
            
            print("  ✓ Validação funcionou: ordem não foi cancelada sem motivo")
        
        # Testar cancelamento pelo prestador
        print("\n3. Testando cancelamento pelo prestador...")
        
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = prestador.id
                sess['active_role'] = 'prestador'
            
            response = client.post(
                f'/ordens/{order_id2}/cancelar',
                data={'reason': 'Prestador cancelando por imprevisto'},
                follow_redirects=False
            )
            
            assert response.status_code == 302, "Deveria redirecionar"
            
            order2 = Order.query.get(order_id2)
            assert order2.status == 'cancelada', "Ordem deveria estar cancelada"
            assert order2.cancelled_by == prestador.id, "Deveria ter sido cancelada pelo prestador"
            
            print("  ✓ Prestador cancelou com sucesso")
            print(f"  Cancelada por: user_id {order2.cancelled_by}")
        
        print("\n" + "="*80)
        print("✓ TODOS OS TESTES DA ROTA DE CANCELAMENTO PASSARAM!")
        print("="*80)
        
        return True


if __name__ == '__main__':
    try:
        # Importar Transaction aqui para evitar erro
        from models import Transaction
        
        success = test_cancel_order_route()
        print("\n✅ Tarefa 18 implementada e testada com sucesso!")
        exit(0)
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
