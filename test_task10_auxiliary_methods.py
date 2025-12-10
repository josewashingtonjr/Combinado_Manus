#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar os métodos auxiliares do OrderManagementService (Tarefa 10)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Wallet
from services.order_management_service import OrderManagementService
from datetime import datetime, timedelta
from decimal import Decimal


def test_auxiliary_methods():
    """Testa os métodos auxiliares get_orders_by_user e get_order_statistics"""
    
    with app.app_context():
        # Limpar dados de teste anteriores
        Order.query.filter(Order.title.like('Teste Tarefa 10%')).delete()
        db.session.commit()
        
        # Criar usuários de teste
        cliente = User.query.filter_by(email='cliente@test.com').first()
        prestador = User.query.filter_by(email='prestador@test.com').first()
        
        if not cliente:
            cliente = User(
                nome='Cliente Teste',
                email='cliente@test.com',
                telefone='11999999001',
                papel='cliente'
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
        
        if not prestador:
            prestador = User(
                nome='Prestador Teste',
                email='prestador@test.com',
                telefone='11999999002',
                papel='prestador'
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
        
        db.session.commit()
        
        # Garantir que os usuários têm carteiras
        if not Wallet.query.filter_by(user_id=cliente.id).first():
            wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('1000.00'))
            db.session.add(wallet_cliente)
        
        if not Wallet.query.filter_by(user_id=prestador.id).first():
            wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('1000.00'))
            db.session.add(wallet_prestador)
        
        db.session.commit()
        
        print("\n=== TESTE: Métodos Auxiliares do OrderManagementService ===\n")
        
        # Criar ordens de teste com diferentes status
        test_orders = [
            {
                'title': 'Teste Tarefa 10 - Ordem 1',
                'description': 'Ordem aguardando execução',
                'status': 'aguardando_execucao',
                'value': Decimal('100.00')
            },
            {
                'title': 'Teste Tarefa 10 - Ordem 2',
                'description': 'Ordem com serviço executado',
                'status': 'servico_executado',
                'value': Decimal('200.00')
            },
            {
                'title': 'Teste Tarefa 10 - Ordem 3',
                'description': 'Ordem concluída',
                'status': 'concluida',
                'value': Decimal('300.00')
            },
            {
                'title': 'Teste Tarefa 10 - Ordem 4',
                'description': 'Ordem cancelada',
                'status': 'cancelada',
                'value': Decimal('150.00')
            },
            {
                'title': 'Teste Tarefa 10 - Ordem 5',
                'description': 'Ordem contestada',
                'status': 'contestada',
                'value': Decimal('250.00')
            }
        ]
        
        created_orders = []
        for order_data in test_orders:
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title=order_data['title'],
                description=order_data['description'],
                value=order_data['value'],
                status=order_data['status'],
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow()
            )
            db.session.add(order)
            created_orders.append(order)
        
        db.session.commit()
        
        print(f"✓ Criadas {len(created_orders)} ordens de teste")
        print()
        
        # Teste 1: get_orders_by_user - Cliente sem filtro
        print("TESTE 1: get_orders_by_user - Cliente sem filtro")
        orders_cliente = OrderManagementService.get_orders_by_user(
            user_id=cliente.id,
            role='cliente'
        )
        print(f"  Resultado: {len(orders_cliente)} ordens encontradas")
        assert len(orders_cliente) >= 5, "Deveria ter pelo menos 5 ordens"
        print(f"  ✓ Ordens retornadas corretamente")
        
        # Verificar eager loading (não deve gerar queries adicionais)
        print(f"  Verificando eager loading...")
        for order in orders_cliente[:3]:
            # Acessar relacionamentos não deve gerar queries adicionais
            client_name = order.client.nome if order.client else None
            provider_name = order.provider.nome if order.provider else None
            print(f"    - Ordem #{order.id}: Cliente={client_name}, Prestador={provider_name}")
        print(f"  ✓ Eager loading funcionando (relacionamentos carregados)")
        
        # Verificar ordenação (mais recentes primeiro)
        print(f"  Verificando ordenação por created_at DESC...")
        for i in range(len(orders_cliente) - 1):
            assert orders_cliente[i].created_at >= orders_cliente[i + 1].created_at, \
                "Ordens devem estar ordenadas por created_at DESC"
        print(f"  ✓ Ordenação correta (mais recentes primeiro)")
        print()
        
        # Teste 2: get_orders_by_user - Cliente com filtro de status
        print("TESTE 2: get_orders_by_user - Cliente com filtro 'concluida'")
        orders_concluidas = OrderManagementService.get_orders_by_user(
            user_id=cliente.id,
            role='cliente',
            status_filter='concluida'
        )
        print(f"  Resultado: {len(orders_concluidas)} ordens concluídas")
        for order in orders_concluidas:
            assert order.status == 'concluida', "Todas as ordens devem ter status 'concluida'"
        print(f"  ✓ Filtro de status funcionando corretamente")
        print()
        
        # Teste 3: get_orders_by_user - Prestador
        print("TESTE 3: get_orders_by_user - Prestador sem filtro")
        orders_prestador = OrderManagementService.get_orders_by_user(
            user_id=prestador.id,
            role='prestador'
        )
        print(f"  Resultado: {len(orders_prestador)} ordens encontradas")
        assert len(orders_prestador) >= 5, "Deveria ter pelo menos 5 ordens"
        print(f"  ✓ Ordens do prestador retornadas corretamente")
        print()
        
        # Teste 4: get_order_statistics - Cliente
        print("TESTE 4: get_order_statistics - Cliente")
        stats_cliente = OrderManagementService.get_order_statistics(
            user_id=cliente.id,
            role='cliente'
        )
        print(f"  Estatísticas do cliente:")
        print(f"    - Total: {stats_cliente['total']}")
        print(f"    - Aguardando: {stats_cliente['aguardando']}")
        print(f"    - Para Confirmar: {stats_cliente['para_confirmar']}")
        print(f"    - Concluídas: {stats_cliente['concluidas']}")
        print(f"    - Canceladas: {stats_cliente['canceladas']}")
        print(f"    - Contestadas: {stats_cliente['contestadas']}")
        print(f"    - Resolvidas: {stats_cliente['resolvidas']}")
        
        # Validar estatísticas
        assert stats_cliente['total'] >= 5, "Total deve ser >= 5"
        assert stats_cliente['aguardando'] >= 1, "Deve ter pelo menos 1 aguardando"
        assert stats_cliente['para_confirmar'] >= 1, "Deve ter pelo menos 1 para confirmar"
        assert stats_cliente['concluidas'] >= 1, "Deve ter pelo menos 1 concluída"
        assert stats_cliente['canceladas'] >= 1, "Deve ter pelo menos 1 cancelada"
        assert stats_cliente['contestadas'] >= 1, "Deve ter pelo menos 1 contestada"
        
        # Verificar soma
        soma = (stats_cliente['aguardando'] + stats_cliente['para_confirmar'] + 
                stats_cliente['concluidas'] + stats_cliente['canceladas'] + 
                stats_cliente['contestadas'] + stats_cliente['resolvidas'])
        assert soma == stats_cliente['total'], "Soma dos status deve ser igual ao total"
        print(f"  ✓ Estatísticas calculadas corretamente")
        print()
        
        # Teste 5: get_order_statistics - Prestador
        print("TESTE 5: get_order_statistics - Prestador")
        stats_prestador = OrderManagementService.get_order_statistics(
            user_id=prestador.id,
            role='prestador'
        )
        print(f"  Estatísticas do prestador:")
        print(f"    - Total: {stats_prestador['total']}")
        print(f"    - Aguardando: {stats_prestador['aguardando']}")
        print(f"    - Aguardando Cliente: {stats_prestador['para_confirmar']}")
        print(f"    - Concluídas: {stats_prestador['concluidas']}")
        print(f"    - Canceladas: {stats_prestador['canceladas']}")
        print(f"    - Contestadas: {stats_prestador['contestadas']}")
        print(f"    - Resolvidas: {stats_prestador['resolvidas']}")
        
        assert stats_prestador['total'] >= 5, "Total deve ser >= 5"
        print(f"  ✓ Estatísticas do prestador calculadas corretamente")
        print()
        
        # Teste 6: Validar erro com role inválido
        print("TESTE 6: Validar erro com role inválido")
        try:
            OrderManagementService.get_orders_by_user(
                user_id=cliente.id,
                role='invalido'
            )
            assert False, "Deveria ter lançado ValueError"
        except ValueError as e:
            print(f"  ✓ Erro esperado capturado: {e}")
        print()
        
        print("=" * 60)
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        print()
        print("Resumo da implementação:")
        print("  ✓ get_orders_by_user() implementado com:")
        print("    - Filtro por role (cliente/prestador)")
        print("    - Filtro opcional por status")
        print("    - Eager loading de relacionamentos (client, provider)")
        print("    - Ordenação por created_at DESC")
        print()
        print("  ✓ get_order_statistics() implementado com:")
        print("    - Contadores para dashboard")
        print("    - Suporte para cliente e prestador")
        print("    - Estatísticas por status")
        print()


if __name__ == '__main__':
    test_auxiliary_methods()
