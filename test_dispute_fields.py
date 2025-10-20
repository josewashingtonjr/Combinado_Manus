#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Teste para validar campos de disputa no modelo Order
Task 11.4
"""

from app import app, db
from models import User, Order
from services.order_service import OrderService
from services.wallet_service import WalletService
from datetime import datetime

def test_dispute_fields():
    """Testar campos de disputa"""
    with app.app_context():
        print("=" * 60)
        print("TESTE: Campos de Disputa no Modelo Order")
        print("=" * 60)
        
        # 1. Criar usuários de teste
        print("\n1. Criando usuários de teste...")
        client = User.query.filter_by(email='cliente@teste.com').first()
        provider = User.query.filter_by(email='prestador@teste.com').first()
        
        if not client or not provider:
            print("❌ Usuários de teste não encontrados")
            return
        
        print(f"✅ Cliente: {client.nome} (ID: {client.id})")
        print(f"✅ Prestador: {provider.nome} (ID: {provider.id})")
        
        # 2. Garantir saldo para o cliente
        print("\n2. Garantindo saldo para o cliente...")
        WalletService.ensure_user_has_wallet(client.id)
        wallet = WalletService.get_wallet_info(client.id)
        
        if wallet['balance'] < 100:
            # Adicionar saldo
            WalletService.deposit(client.id, 200, "Depósito para teste")
            print("✅ Saldo adicionado")
        
        wallet = WalletService.get_wallet_info(client.id)
        print(f"✅ Saldo atual: R$ {wallet['balance']:.2f}")
        
        # 3. Criar ordem
        print("\n3. Criando ordem de serviço...")
        order_result = OrderService.create_order(
            client_id=client.id,
            title="Serviço de Teste para Disputa",
            description="Ordem criada para testar sistema de disputas",
            value=50.0
        )
        order = order_result['order']
        print(f"✅ Ordem criada (ID: {order.id})")
        print(f"   Status: {order.status}")
        print(f"   Valor: R$ {order.value:.2f}")
        
        # 4. Aceitar ordem
        print("\n4. Prestador aceitando ordem...")
        OrderService.accept_order(provider.id, order.id)
        db.session.refresh(order)
        print(f"✅ Ordem aceita")
        print(f"   Status: {order.status}")
        
        # 5. Abrir disputa
        print("\n5. Abrindo disputa...")
        dispute_result = OrderService.open_dispute(
            user_id=client.id,
            order_id=order.id,
            reason="Serviço não foi entregue conforme combinado. Qualidade abaixo do esperado."
        )
        db.session.refresh(order)
        
        print(f"✅ Disputa aberta")
        print(f"   Status: {order.status}")
        print(f"   Motivo: {order.dispute_reason}")
        print(f"   Aberta por: User ID {order.dispute_opened_by}")
        print(f"   Aberta em: {order.dispute_opened_at}")
        
        # 6. Verificar campos de disputa
        print("\n6. Verificando campos de disputa...")
        assert order.dispute_reason is not None, "dispute_reason deve estar preenchido"
        assert order.dispute_opened_by == client.id, "dispute_opened_by deve ser o cliente"
        assert order.dispute_opened_at is not None, "dispute_opened_at deve estar preenchido"
        assert order.dispute_resolved_at is None, "dispute_resolved_at deve estar vazio"
        assert order.dispute_resolution is None, "dispute_resolution deve estar vazio"
        print("✅ Todos os campos de disputa estão corretos")
        
        # 7. Resolver disputa (simular admin)
        print("\n7. Resolvendo disputa (favor do cliente)...")
        from models import AdminUser
        admin = AdminUser.query.first()
        
        if not admin:
            print("❌ Admin não encontrado")
            return
        
        resolve_result = OrderService.resolve_dispute(
            admin_id=admin.id,
            order_id=order.id,
            decision='favor_cliente',
            admin_notes="Cliente tem razão. Serviço não foi entregue conforme acordado."
        )
        db.session.refresh(order)
        
        print(f"✅ Disputa resolvida")
        print(f"   Status: {order.status}")
        print(f"   Resolvida em: {order.dispute_resolved_at}")
        print(f"   Resolução: {order.dispute_resolution}")
        
        # 8. Verificar campos após resolução
        print("\n8. Verificando campos após resolução...")
        assert order.dispute_resolved_at is not None, "dispute_resolved_at deve estar preenchido"
        assert order.dispute_resolution is not None, "dispute_resolution deve estar preenchido"
        assert order.status == 'resolvida', "status deve ser 'resolvida'"
        print("✅ Todos os campos de resolução estão corretos")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("\nResumo:")
        print(f"  - Ordem ID: {order.id}")
        print(f"  - Status final: {order.status}")
        print(f"  - Disputa aberta em: {order.dispute_opened_at}")
        print(f"  - Disputa resolvida em: {order.dispute_resolved_at}")
        print(f"  - Decisão: {resolve_result['decision']}")
        print(f"  - Cliente recebeu: R$ {resolve_result['result_details']['client_amount']:.2f}")

if __name__ == '__main__':
    test_dispute_fields()
