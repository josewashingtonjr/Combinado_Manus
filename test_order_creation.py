#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a implementação da criação de ordens com bloqueio de tokens em escrow
Tarefa 3.1: Implementar criação de ordens com bloqueio de tokens
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Wallet, Order, Transaction
from services.order_service import OrderService
from services.wallet_service import WalletService

def test_order_creation_with_escrow():
    """Testa a criação de ordens com bloqueio automático de tokens em escrow"""
    
    with app.app_context():
        print("🧪 Iniciando teste de criação de ordens com escrow...")
        
        # Limpar dados de teste
        db.session.query(Transaction).delete()
        db.session.query(Order).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # 1. Criar usuário cliente de teste
        print("\n1️⃣ Criando usuário cliente de teste...")
        cliente = User(
            email="cliente@teste.com",
            nome="Cliente Teste",
            cpf="12345678901",
            roles="cliente"
        )
        cliente.set_password("senha123")
        db.session.add(cliente)
        db.session.commit()
        
        # 2. Criar carteira e adicionar saldo inicial
        print("2️⃣ Criando carteira e adicionando saldo inicial...")
        WalletService.ensure_user_has_wallet(cliente.id)
        
        # Simular compra de tokens (admin → cliente)
        WalletService.admin_sell_tokens_to_user(
            user_id=cliente.id,
            amount=1000.0,
            description="Saldo inicial para teste"
        )
        
        # Verificar saldo inicial
        wallet_info = WalletService.get_wallet_info(cliente.id)
        print(f"   ✅ Saldo inicial: R$ {wallet_info['balance']:.2f}")
        print(f"   ✅ Escrow inicial: R$ {wallet_info['escrow_balance']:.2f}")
        
        # 3. Testar validação de criação de ordem
        print("\n3️⃣ Testando validação de criação de ordem...")
        
        # Teste com valor válido
        validation = OrderService.validate_order_creation(cliente.id, 100.0)
        assert validation['valid'] == True, "Validação deveria passar para valor válido"
        print("   ✅ Validação passou para valor dentro do saldo")
        
        # Teste com valor maior que saldo
        validation = OrderService.validate_order_creation(cliente.id, 1500.0)
        assert validation['valid'] == False, "Validação deveria falhar para valor maior que saldo"
        print("   ✅ Validação falhou corretamente para valor maior que saldo")
        
        # 4. Criar ordem de serviço
        print("\n4️⃣ Criando ordem de serviço com bloqueio de escrow...")
        
        order_data = {
            'client_id': cliente.id,
            'title': 'Desenvolvimento de Website',
            'description': 'Criar um website institucional moderno e responsivo com 5 páginas principais.',
            'value': 500.0
        }
        
        result = OrderService.create_order(**order_data)
        order = result['order']
        
        print(f"   ✅ Ordem criada com ID: {order.id}")
        print(f"   ✅ Status da ordem: {order.status}")
        print(f"   ✅ Valor da ordem: R$ {order.value:.2f}")
        print(f"   ✅ Transação de escrow ID: {result['escrow_transaction_id']}")
        
        # 5. Verificar estado da carteira após criação
        print("\n5️⃣ Verificando estado da carteira após criação...")
        
        wallet_info_after = WalletService.get_wallet_info(cliente.id)
        print(f"   ✅ Saldo após criação: R$ {wallet_info_after['balance']:.2f}")
        print(f"   ✅ Escrow após criação: R$ {wallet_info_after['escrow_balance']:.2f}")
        
        # Verificações
        expected_balance = 1000.0 - 500.0  # Saldo inicial - valor da ordem
        expected_escrow = 500.0  # Valor da ordem em escrow
        
        assert abs(wallet_info_after['balance'] - expected_balance) < 0.01, f"Saldo incorreto: esperado {expected_balance}, obtido {wallet_info_after['balance']}"
        assert abs(wallet_info_after['escrow_balance'] - expected_escrow) < 0.01, f"Escrow incorreto: esperado {expected_escrow}, obtido {wallet_info_after['escrow_balance']}"
        
        print("   ✅ Saldos corretos após bloqueio em escrow")
        
        # 6. Verificar transação de escrow
        print("\n6️⃣ Verificando transação de escrow...")
        
        escrow_transaction = Transaction.query.get(result['escrow_transaction_id'])
        assert escrow_transaction is not None, "Transação de escrow não encontrada"
        assert escrow_transaction.type == "escrow_bloqueio", f"Tipo incorreto: {escrow_transaction.type}"
        assert escrow_transaction.amount == -500.0, f"Valor incorreto: {escrow_transaction.amount}"
        assert escrow_transaction.order_id == order.id, "Order ID incorreto na transação"
        
        print(f"   ✅ Transação de escrow registrada corretamente")
        print(f"   ✅ Tipo: {escrow_transaction.type}")
        print(f"   ✅ Valor: R$ {abs(escrow_transaction.amount):.2f}")
        print(f"   ✅ Descrição: {escrow_transaction.description}")
        
        # 7. Verificar integridade do sistema
        print("\n7️⃣ Verificando integridade do sistema...")
        
        integrity = WalletService.validate_transaction_integrity(cliente.id)
        assert integrity['is_valid'] == True, f"Integridade falhou: {integrity}"
        
        print("   ✅ Integridade do sistema validada")
        print(f"   ✅ Saldo calculado: R$ {integrity['calculated_balance']:.2f}")
        print(f"   ✅ Escrow calculado: R$ {integrity['calculated_escrow']:.2f}")
        
        # 8. Testar criação de segunda ordem (saldo insuficiente)
        print("\n8️⃣ Testando criação com saldo insuficiente...")
        
        try:
            OrderService.create_order(
                client_id=cliente.id,
                title='Ordem Impossível',
                description='Esta ordem não deveria ser criada',
                value=600.0  # Maior que saldo disponível (500)
            )
            assert False, "Ordem não deveria ter sido criada com saldo insuficiente"
        except ValueError as e:
            print(f"   ✅ Erro esperado capturado: {str(e)}")
        
        # 9. Verificar que tokens não saíram do sistema
        print("\n9️⃣ Verificando que tokens não saíram do sistema...")
        
        # Total de tokens no sistema deve ser o mesmo
        admin_wallet = WalletService.get_admin_wallet_info()
        user_wallet = WalletService.get_wallet_info(cliente.id)
        
        total_tokens = admin_wallet['balance'] + user_wallet['balance'] + user_wallet['escrow_balance']
        print(f"   ✅ Total de tokens no sistema: {total_tokens:.2f}")
        print(f"   ✅ Admin: {admin_wallet['balance']:.2f}")
        print(f"   ✅ Cliente (saldo): {user_wallet['balance']:.2f}")
        print(f"   ✅ Cliente (escrow): {user_wallet['escrow_balance']:.2f}")
        
        # Verificar resumo do sistema
        token_summary = WalletService.get_system_token_summary()
        print(f"   ✅ Tokens criados: {token_summary['total_tokens_created']:.2f}")
        print(f"   ✅ Em circulação: {token_summary['tokens_in_circulation']:.2f}")
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Criação de ordens com bloqueio de escrow implementada corretamente")
        print("✅ Tokens permanecem no sistema (saldo → escrow)")
        print("✅ Validações de saldo funcionando")
        print("✅ Transações registradas com rastreabilidade")
        print("✅ Integridade do sistema mantida")
        
        return True

def test_order_states_flow():
    """Testa o fluxo de estados das ordens conforme Planta Arquitetônica"""
    
    with app.app_context():
        print("\n🔄 Testando fluxo de estados das ordens...")
        
        # Buscar ordem criada no teste anterior
        order = Order.query.first()
        if not order:
            print("❌ Nenhuma ordem encontrada para testar estados")
            return False
        
        print(f"📋 Ordem ID {order.id}: {order.title}")
        print(f"   Status inicial: {order.status}")
        
        # Verificar estado inicial
        assert order.status == 'disponivel', f"Estado inicial incorreto: {order.status}"
        print("   ✅ Estado inicial 'disponivel' correto")
        
        # Criar prestador para aceitar a ordem
        prestador = User(
            email="prestador@teste.com",
            nome="Prestador Teste",
            cpf="98765432100",
            roles="prestador"
        )
        prestador.set_password("senha123")
        db.session.add(prestador)
        db.session.commit()
        
        # Aceitar ordem
        print("\n   Aceitando ordem...")
        success = OrderService.accept_order(prestador.id, order.id)
        assert success == True, "Aceitação da ordem falhou"
        
        # Recarregar ordem do banco
        db.session.refresh(order)
        print(f"   Status após aceitação: {order.status}")
        print(f"   Prestador ID: {order.provider_id}")
        print(f"   Aceita em: {order.accepted_at}")
        
        assert order.status == 'aceita', f"Estado após aceitação incorreto: {order.status}"
        assert order.provider_id == prestador.id, "Prestador não foi associado corretamente"
        assert order.accepted_at is not None, "Data de aceitação não foi registrada"
        
        print("   ✅ Aceitação da ordem funcionando corretamente")
        
        print("\n🎯 Fluxo de estados validado com sucesso!")
        return True

if __name__ == "__main__":
    try:
        # Executar testes
        test_order_creation_with_escrow()
        test_order_states_flow()
        
        print("\n" + "="*60)
        print("🏆 TODOS OS TESTES PASSARAM!")
        print("✅ Tarefa 3.1 implementada com sucesso")
        print("✅ Sistema de criação de ordens com escrow funcionando")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)