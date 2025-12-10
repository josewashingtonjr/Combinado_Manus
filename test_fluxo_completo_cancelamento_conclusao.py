#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do Fluxo Completo de Cancelamento e Conclusão de Ordens

Este script testa todos os cenários:
1. Prestador marca como concluído
2. Cliente confirma
3. Cliente contesta
4. Prestador responde contestação
5. Cancelamento pelo prestador
6. Cancelamento pelo cliente
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from services.config_service import ConfigService
from decimal import Decimal

def setup_test_data():
    """Cria dados de teste"""
    with app.app_context():
        # Criar usuários de teste
        cliente = User.query.filter_by(email='cliente_test@example.com').first()
        if not cliente:
            cliente = User(
                email='cliente_test@example.com',
                nome='Cliente Teste',
                cpf='111.111.111-11',
                phone='11999999999',
                roles='cliente'
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
        
        prestador = User.query.filter_by(email='prestador_test@example.com').first()
        if not prestador:
            prestador = User(
                email='prestador_test@example.com',
                nome='Prestador Teste',
                cpf='222.222.222-22',
                phone='11988888888',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
        
        db.session.commit()
        
        # Garantir carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo
        WalletService.add_tokens(cliente.id, Decimal('1000.00'), 'Saldo inicial para testes')
        WalletService.add_tokens(prestador.id, Decimal('100.00'), 'Saldo inicial para testes')
        
        return cliente, prestador

def test_marcar_como_concluido():
    """Testa prestador marcando ordem como concluída"""
    print("\n" + "="*80)
    print("TESTE 1: Prestador Marca como Concluído")
    print("="*80)
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar convite aceito
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Teste Marcar Concluído',
            service_description='Descrição do teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar ordem
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = result['order_id']
        
        print(f"✓ Ordem {order_id} criada com sucesso")
        print(f"  Status inicial: aguardando_execucao")
        
        # Marcar como concluído
        result = OrderManagementService.mark_service_completed(order_id, prestador.id)
        
        print(f"✓ Ordem marcada como concluída")
        print(f"  Novo status: {result['status']}")
        print(f"  Prazo para confirmação: {result['hours_to_confirm']} horas")
        print(f"  Deadline: {result['confirmation_deadline']}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'servico_executado', "Status deveria ser servico_executado"
        assert order.completed_at is not None, "completed_at deveria estar preenchido"
        assert order.confirmation_deadline is not None, "confirmation_deadline deveria estar preenchido"
        assert order.can_be_confirmed, "Cliente deveria poder confirmar"
        assert order.can_be_disputed, "Cliente deveria poder contestar"
        assert not order.can_be_cancelled, "Não deveria poder cancelar após marcar como concluído"
        
        print("\n✅ TESTE 1 PASSOU - Prestador pode marcar como concluído corretamente")
        return order_id

def test_cliente_confirma(order_id):
    """Testa cliente confirmando serviço"""
    print("\n" + "="*80)
    print("TESTE 2: Cliente Confirma Serviço")
    print("="*80)
    
    with app.app_context():
        order = Order.query.get(order_id)
        cliente_id = order.client_id
        
        print(f"✓ Ordem {order_id} em status: {order.status}")
        
        # Confirmar serviço
        result = OrderManagementService.confirm_service(order_id, cliente_id)
        
        print(f"✓ Serviço confirmado")
        print(f"  Novo status: {result['status']}")
        print(f"  Tipo de confirmação: {result['confirmation_type']}")
        print(f"  Prestador recebeu: R$ {result['payments']['provider_net_amount']:.2f}")
        print(f"  Taxa plataforma: R$ {result['payments']['platform_fee']:.2f}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'concluida', "Status deveria ser concluida"
        assert order.confirmed_at is not None, "confirmed_at deveria estar preenchido"
        assert not order.auto_confirmed, "Não deveria ser confirmação automática"
        
        print("\n✅ TESTE 2 PASSOU - Cliente pode confirmar serviço corretamente")

def test_cliente_contesta():
    """Testa cliente contestando serviço"""
    print("\n" + "="*80)
    print("TESTE 3: Cliente Contesta Serviço")
    print("="*80)
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar nova ordem
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Teste Contestação',
            service_description='Descrição do teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = result['order_id']
        
        # Marcar como concluído
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        
        print(f"✓ Ordem {order_id} marcada como concluída")
        
        # Cliente contesta
        reason = "O serviço não foi executado conforme combinado. Faltaram várias etapas importantes."
        result = OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=cliente.id,
            reason=reason,
            evidence_files=None
        )
        
        print(f"✓ Contestação aberta")
        print(f"  Novo status: {result['status']}")
        print(f"  Motivo: {reason[:50]}...")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'contestada', "Status deveria ser contestada"
        assert order.dispute_opened_at is not None, "dispute_opened_at deveria estar preenchido"
        assert order.dispute_client_statement == reason, "Motivo deveria estar salvo"
        assert not order.dispute_provider_response, "Prestador ainda não respondeu"
        
        print("\n✅ TESTE 3 PASSOU - Cliente pode contestar serviço corretamente")
        return order_id

def test_prestador_responde_contestacao(order_id):
    """Testa prestador respondendo contestação"""
    print("\n" + "="*80)
    print("TESTE 4: Prestador Responde Contestação")
    print("="*80)
    
    with app.app_context():
        order = Order.query.get(order_id)
        prestador_id = order.provider_id
        
        print(f"✓ Ordem {order_id} em status: {order.status}")
        print(f"  Contestação do cliente: {order.dispute_client_statement[:50]}...")
        
        # Prestador responde
        response = "O serviço foi executado conforme combinado. Todas as etapas foram concluídas e o cliente aprovou durante a execução."
        result = OrderManagementService.provider_respond_to_dispute(
            order_id=order_id,
            provider_id=prestador_id,
            response=response,
            evidence_files=None
        )
        
        print(f"✓ Resposta enviada")
        print(f"  Resposta: {response[:50]}...")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'contestada', "Status ainda deveria ser contestada"
        assert order.dispute_provider_response == response, "Resposta deveria estar salva"
        
        print("\n✅ TESTE 4 PASSOU - Prestador pode responder contestação corretamente")

def test_cancelamento_prestador():
    """Testa cancelamento pelo prestador"""
    print("\n" + "="*80)
    print("TESTE 5: Cancelamento pelo Prestador")
    print("="*80)
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar nova ordem
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Teste Cancelamento Prestador',
            service_description='Descrição do teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = result['order_id']
        
        print(f"✓ Ordem {order_id} criada")
        
        # Verificar que pode cancelar
        order = Order.query.get(order_id)
        assert order.can_be_cancelled, "Deveria poder cancelar em aguardando_execucao"
        
        # Cancelar
        reason = "Motivo superior não permite concluir o serviço no prazo"
        result = OrderManagementService.cancel_order(order_id, prestador.id, reason)
        
        print(f"✓ Ordem cancelada pelo prestador")
        print(f"  Novo status: {result['status']}")
        print(f"  Multa aplicada: R$ {result['cancellation_fee']:.2f}")
        print(f"  Parte prejudicada: {result['injured_party']}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'cancelada', "Status deveria ser cancelada"
        assert order.cancelled_by == prestador.id, "cancelled_by deveria ser o prestador"
        assert order.cancellation_reason == reason, "Motivo deveria estar salvo"
        assert order.cancellation_fee is not None, "Multa deveria estar calculada"
        
        print("\n✅ TESTE 5 PASSOU - Prestador pode cancelar ordem corretamente")

def test_cancelamento_cliente():
    """Testa cancelamento pelo cliente"""
    print("\n" + "="*80)
    print("TESTE 6: Cancelamento pelo Cliente")
    print("="*80)
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar nova ordem
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Teste Cancelamento Cliente',
            service_description='Descrição do teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = result['order_id']
        
        print(f"✓ Ordem {order_id} criada")
        
        # Verificar que pode cancelar
        order = Order.query.get(order_id)
        assert order.can_be_cancelled, "Deveria poder cancelar em aguardando_execucao"
        
        # Cancelar
        reason = "Não preciso mais do serviço"
        result = OrderManagementService.cancel_order(order_id, cliente.id, reason)
        
        print(f"✓ Ordem cancelada pelo cliente")
        print(f"  Novo status: {result['status']}")
        print(f"  Multa aplicada: R$ {result['cancellation_fee']:.2f}")
        print(f"  Parte prejudicada: {result['injured_party']}")
        
        # Verificar ordem
        order = Order.query.get(order_id)
        assert order.status == 'cancelada', "Status deveria ser cancelada"
        assert order.cancelled_by == cliente.id, "cancelled_by deveria ser o cliente"
        assert order.cancellation_reason == reason, "Motivo deveria estar salvo"
        assert order.cancellation_fee is not None, "Multa deveria estar calculada"
        
        print("\n✅ TESTE 6 PASSOU - Cliente pode cancelar ordem corretamente")

def test_nao_pode_cancelar_apos_concluido():
    """Testa que não pode cancelar após marcar como concluído"""
    print("\n" + "="*80)
    print("TESTE 7: Não Pode Cancelar Após Marcar como Concluído")
    print("="*80)
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar nova ordem
        invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Teste Não Cancelar',
            service_description='Descrição do teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        result = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
        order_id = result['order_id']
        
        # Marcar como concluído
        OrderManagementService.mark_service_completed(order_id, prestador.id)
        
        print(f"✓ Ordem {order_id} marcada como concluída")
        
        # Verificar que NÃO pode cancelar
        order = Order.query.get(order_id)
        assert not order.can_be_cancelled, "NÃO deveria poder cancelar após marcar como concluído"
        
        # Tentar cancelar (deve falhar)
        try:
            OrderManagementService.cancel_order(order_id, prestador.id, "Tentando cancelar")
            assert False, "Deveria ter lançado exceção"
        except ValueError as e:
            print(f"✓ Cancelamento bloqueado corretamente: {str(e)}")
        
        print("\n✅ TESTE 7 PASSOU - Não pode cancelar após marcar como concluído")

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("INICIANDO TESTES DO FLUXO COMPLETO DE CANCELAMENTO E CONCLUSÃO")
    print("="*80)
    
    try:
        # Teste 1: Marcar como concluído
        order_id_1 = test_marcar_como_concluido()
        
        # Teste 2: Cliente confirma
        test_cliente_confirma(order_id_1)
        
        # Teste 3: Cliente contesta
        order_id_3 = test_cliente_contesta()
        
        # Teste 4: Prestador responde contestação
        test_prestador_responde_contestacao(order_id_3)
        
        # Teste 5: Cancelamento pelo prestador
        test_cancelamento_prestador()
        
        # Teste 6: Cancelamento pelo cliente
        test_cancelamento_cliente()
        
        # Teste 7: Não pode cancelar após concluído
        test_nao_pode_cancelar_apos_concluido()
        
        print("\n" + "="*80)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*80)
        print("\nResumo:")
        print("  ✓ Prestador pode marcar como concluído")
        print("  ✓ Cliente pode confirmar serviço")
        print("  ✓ Cliente pode contestar serviço")
        print("  ✓ Prestador pode responder contestação")
        print("  ✓ Prestador pode cancelar (com multa)")
        print("  ✓ Cliente pode cancelar (com multa)")
        print("  ✓ Não pode cancelar após marcar como concluído")
        print("\n🎉 Sistema de cancelamento e conclusão funcionando perfeitamente!")
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERRO NOS TESTES")
        print("="*80)
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
