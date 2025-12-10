#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para Task 4: Implementar OrderManagementService - Marcação de Conclusão
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Wallet, Transaction
from services.order_management_service import OrderManagementService

def setup_test_data():
    """Cria dados de teste"""
    # Limpar dados existentes
    Transaction.query.delete()
    Order.query.delete()
    Wallet.query.delete()
    User.query.delete()
    db.session.commit()
    
    # Criar cliente
    cliente = User(
        email='cliente@test.com',
        nome='Cliente Teste',
        cpf='111.111.111-11',
        roles='cliente'
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    
    # Criar prestador
    prestador = User(
        email='prestador@test.com',
        nome='Prestador Teste',
        cpf='222.222.222-22',
        roles='prestador'
    )
    prestador.set_password('senha123')
    db.session.add(prestador)
    
    db.session.commit()
    
    # Criar carteiras
    wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('1000.00'))
    wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('500.00'))
    db.session.add(wallet_cliente)
    db.session.add(wallet_prestador)
    db.session.commit()
    
    # Criar ordem em status aguardando_execucao
    ordem = Order(
        client_id=cliente.id,
        provider_id=prestador.id,
        title='Instalação Elétrica',
        description='Instalação de tomadas e interruptores',
        value=Decimal('500.00'),
        status='aguardando_execucao',
        service_deadline=datetime.utcnow() + timedelta(days=7),
        platform_fee_percentage_at_creation=Decimal('5.0'),
        contestation_fee_at_creation=Decimal('10.00'),
        cancellation_fee_percentage_at_creation=Decimal('10.0')
    )
    db.session.add(ordem)
    db.session.commit()
    
    return cliente, prestador, ordem

def test_mark_service_completed():
    """Testa marcação de serviço como concluído"""
    print("\n" + "="*80)
    print("TESTE: Marcação de Serviço como Concluído")
    print("="*80)
    
    with app.app_context():
        cliente, prestador, ordem = setup_test_data()
        
        print(f"\n✓ Dados de teste criados:")
        print(f"  - Cliente: {cliente.nome} (ID: {cliente.id})")
        print(f"  - Prestador: {prestador.nome} (ID: {prestador.id})")
        print(f"  - Ordem: {ordem.title} (ID: {ordem.id})")
        print(f"  - Status inicial: {ordem.status}")
        print(f"  - Valor: R$ {ordem.value}")
        
        # Teste 1: Marcar como concluído
        print("\n" + "-"*80)
        print("TESTE 1: Prestador marca serviço como concluído")
        print("-"*80)
        
        try:
            result = OrderManagementService.mark_service_completed(
                order_id=ordem.id,
                provider_id=prestador.id
            )
            
            print(f"\n✓ Serviço marcado como concluído com sucesso!")
            print(f"  - Status: {result['status']}")
            print(f"  - Prazo para confirmação: {result['confirmation_deadline']}")
            print(f"  - Horas para confirmar: {result['hours_to_confirm']}h")
            print(f"  - Mensagem: {result['message']}")
            
            # Verificar ordem no banco
            db.session.refresh(ordem)
            print(f"\n✓ Verificação da ordem no banco:")
            print(f"  - Status: {ordem.status}")
            print(f"  - completed_at: {ordem.completed_at}")
            print(f"  - confirmation_deadline: {ordem.confirmation_deadline}")
            print(f"  - dispute_deadline: {ordem.dispute_deadline}")
            
            # Verificar se os prazos foram calculados corretamente (36 horas)
            if ordem.completed_at and ordem.confirmation_deadline:
                diff = ordem.confirmation_deadline - ordem.completed_at
                hours = diff.total_seconds() / 3600
                print(f"  - Diferença entre completed_at e confirmation_deadline: {hours:.1f}h")
                
                if abs(hours - 36) < 0.1:  # Tolerância de 0.1h
                    print(f"  ✓ Prazo de 36 horas calculado corretamente!")
                else:
                    print(f"  ✗ ERRO: Prazo deveria ser 36h, mas é {hours:.1f}h")
            
            # Verificar propriedades
            print(f"\n✓ Propriedades da ordem:")
            print(f"  - can_be_marked_completed: {ordem.can_be_marked_completed}")
            print(f"  - can_be_confirmed: {ordem.can_be_confirmed}")
            print(f"  - can_be_disputed: {ordem.can_be_disputed}")
            print(f"  - can_be_cancelled: {ordem.can_be_cancelled}")
            print(f"  - hours_until_auto_confirmation: {ordem.hours_until_auto_confirmation:.1f}h")
            
        except Exception as e:
            print(f"\n✗ ERRO ao marcar como concluído: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Teste 2: Tentar marcar novamente (deve falhar)
        print("\n" + "-"*80)
        print("TESTE 2: Tentar marcar novamente (deve falhar)")
        print("-"*80)
        
        try:
            result = OrderManagementService.mark_service_completed(
                order_id=ordem.id,
                provider_id=prestador.id
            )
            print(f"\n✗ ERRO: Deveria ter falhado mas não falhou!")
            return False
        except ValueError as e:
            print(f"\n✓ Falhou corretamente: {e}")
        
        # Teste 3: Usuário errado tentando marcar (deve falhar)
        print("\n" + "-"*80)
        print("TESTE 3: Cliente tentando marcar como concluído (deve falhar)")
        print("-"*80)
        
        # Criar nova ordem para este teste
        ordem2 = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Outro Serviço',
            description='Teste',
            value=Decimal('300.00'),
            status='aguardando_execucao',
            service_deadline=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(ordem2)
        db.session.commit()
        
        try:
            result = OrderManagementService.mark_service_completed(
                order_id=ordem2.id,
                provider_id=cliente.id  # Cliente tentando marcar
            )
            print(f"\n✗ ERRO: Deveria ter falhado mas não falhou!")
            return False
        except ValueError as e:
            print(f"\n✓ Falhou corretamente: {e}")
        
        # Teste 4: Ordem inexistente (deve falhar)
        print("\n" + "-"*80)
        print("TESTE 4: Ordem inexistente (deve falhar)")
        print("-"*80)
        
        try:
            result = OrderManagementService.mark_service_completed(
                order_id=99999,
                provider_id=prestador.id
            )
            print(f"\n✗ ERRO: Deveria ter falhado mas não falhou!")
            return False
        except ValueError as e:
            print(f"\n✓ Falhou corretamente: {e}")
        
        print("\n" + "="*80)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("="*80)
        return True

if __name__ == '__main__':
    success = test_mark_service_completed()
    sys.exit(0 if success else 1)
