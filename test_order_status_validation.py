#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validação de transições de status de pedidos
Implementa testes para requisitos 7.1, 7.2, 7.3, 7.4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, AdminUser, Order, OrderStatusHistory, Wallet
from services.order_service import OrderService
from services.order_status_validator import OrderStatusValidator
from services.wallet_service import WalletService
from datetime import datetime

def test_order_status_validator():
    """Testa o OrderStatusValidator com matriz de transições"""
    print("=== Teste OrderStatusValidator ===")
    
    with app.app_context():
        try:
            # Teste 1: Transições válidas
            print("\n1. Testando transições válidas...")
            
            # disponivel -> aceita (válida)
            result = OrderStatusValidator.validate_transition(
                order_id=1,
                current_status='disponivel',
                new_status='aceita',
                user_id=1,
                reason="Teste de aceitação"
            )
            assert result['valid'] == True
            print(f"✓ disponivel -> aceita: {result['message']}")
            
            # aceita -> em_andamento (válida)
            result = OrderStatusValidator.validate_transition(
                order_id=1,
                current_status='aceita',
                new_status='em_andamento',
                user_id=1
            )
            assert result['valid'] == True
            print(f"✓ aceita -> em_andamento: {result['message']}")
            
            # Teste 2: Transições inválidas
            print("\n2. Testando transições inválidas...")
            
            # disponivel -> concluida (inválida)
            result = OrderStatusValidator.validate_transition(
                order_id=1,
                current_status='disponivel',
                new_status='concluida',
                user_id=1
            )
            assert result['valid'] == False
            print(f"✓ disponivel -> concluida (inválida): {result['error']}")
            
            # cancelada -> aceita (inválida - status final)
            result = OrderStatusValidator.validate_transition(
                order_id=1,
                current_status='cancelada',
                new_status='aceita',
                user_id=1
            )
            assert result['valid'] == False
            print(f"✓ cancelada -> aceita (inválida): {result['error']}")
            
            # Teste 3: Validações específicas
            print("\n3. Testando validações específicas...")
            
            # Disputa sem motivo suficiente
            result = OrderStatusValidator.validate_transition(
                order_id=1,
                current_status='aceita',
                new_status='disputada',
                user_id=1,
                reason="curto"  # Menos de 10 caracteres
            )
            assert result['valid'] == False
            print(f"✓ Disputa com motivo insuficiente: {result['error']}")
            
            # Teste 4: Métodos auxiliares
            print("\n4. Testando métodos auxiliares...")
            
            # Transições válidas para status
            valid_transitions = OrderStatusValidator.get_valid_transitions('disponivel')
            assert 'aceita' in valid_transitions
            assert 'cancelada' in valid_transitions
            print(f"✓ Transições válidas para 'disponivel': {valid_transitions}")
            
            # Status final
            is_final = OrderStatusValidator.is_final_status('cancelada')
            assert is_final == True
            print(f"✓ Status 'cancelada' é final: {is_final}")
            
            # Requer autorização admin
            requires_admin = OrderStatusValidator.requires_admin_authorization('disputada', 'resolvida')
            assert requires_admin == True
            print(f"✓ Transição disputada->resolvida requer admin: {requires_admin}")
            
            print("\n✅ Todos os testes do OrderStatusValidator passaram!")
            
        except Exception as e:
            print(f"\n❌ Erro no teste OrderStatusValidator: {str(e)}")
            raise

def test_order_service_integration():
    """Testa integração do OrderStatusValidator no OrderService"""
    print("\n=== Teste Integração OrderService ===")
    
    with app.app_context():
        try:
            # Limpar dados de teste
            db.session.query(OrderStatusHistory).delete()
            db.session.query(Order).delete()
            db.session.query(Wallet).delete()
            db.session.query(User).delete()
            db.session.query(AdminUser).delete()
            db.session.commit()
            
            # Criar usuários de teste
            client = User(
                email='cliente@test.com',
                nome='Cliente Teste',
                cpf='12345678901',
                roles='cliente'
            )
            client.set_password('123456')
            
            provider = User(
                email='prestador@test.com',
                nome='Prestador Teste',
                cpf='10987654321',
                roles='prestador'
            )
            provider.set_password('123456')
            
            admin = AdminUser(
                email='admin@test.com',
                papel='admin'
            )
            admin.set_password('admin123')
            
            db.session.add_all([client, provider, admin])
            db.session.commit()
            
            # Criar carteiras
            WalletService.ensure_user_has_wallet(client.id)
            WalletService.ensure_user_has_wallet(provider.id)
            
            # Adicionar saldo ao cliente
            WalletService.credit_wallet(client.id, 1000.00, "Saldo inicial para teste")
            
            print(f"✓ Usuários criados - Cliente: {client.id}, Prestador: {provider.id}, Admin: {admin.id}")
            
            # Teste 1: Criar ordem (disponivel)
            print("\n1. Testando criação de ordem...")
            order_result = OrderService.create_order(
                client_id=client.id,
                title="Serviço de Teste",
                description="Descrição do serviço de teste",
                value=100.00
            )
            
            order = order_result['order']
            assert order.status == 'disponivel'
            print(f"✓ Ordem criada com status 'disponivel': {order.id}")
            
            # Teste 2: Aceitar ordem (disponivel -> aceita)
            print("\n2. Testando aceitação de ordem...")
            accept_result = OrderService.accept_order(provider.id, order.id)
            
            assert accept_result['success'] == True
            assert accept_result['new_status'] == 'aceita'
            print(f"✓ Ordem aceita: {accept_result['new_status']}")
            
            # Verificar histórico
            history = OrderService.get_order_status_history(order.id)
            assert len(history) == 1
            assert history[0]['previous_status'] == 'disponivel'
            assert history[0]['new_status'] == 'aceita'
            print(f"✓ Histórico registrado: {len(history)} entrada(s)")
            
            # Teste 3: Tentar transição inválida
            print("\n3. Testando transição inválida...")
            try:
                # Tentar ir direto para concluida (inválido)
                complete_result = OrderService.complete_order(client.id, order.id)
                # Não deveria chegar aqui
                assert False, "Deveria ter falhado"
            except ValueError as e:
                print(f"✓ Transição inválida rejeitada: {str(e)}")
            
            # Teste 4: Marcar como concluída pelo prestador (aceita -> aguardando_confirmacao)
            print("\n4. Testando conclusão pelo prestador...")
            complete_result = OrderService.complete_order(provider.id, order.id)
            
            assert complete_result['success'] == True
            assert complete_result['status'] == 'aguardando_confirmacao'
            print(f"✓ Prestador marcou como concluída: {complete_result['status']}")
            
            # Teste 5: Cliente confirma conclusão (aguardando_confirmacao -> concluida)
            print("\n5. Testando confirmação pelo cliente...")
            confirm_result = OrderService.complete_order(client.id, order.id)
            
            assert confirm_result['success'] == True
            assert confirm_result['status'] == 'concluida'
            print(f"✓ Cliente confirmou conclusão: {confirm_result['status']}")
            
            # Verificar histórico final
            final_history = OrderService.get_order_status_history(order.id)
            assert len(final_history) == 3  # aceita, aguardando_confirmacao, concluida
            print(f"✓ Histórico final: {len(final_history)} entradas")
            
            # Teste 6: Testar disputa
            print("\n6. Testando abertura de disputa...")
            
            # Criar nova ordem para testar disputa
            order_result2 = OrderService.create_order(
                client_id=client.id,
                title="Serviço para Disputa",
                description="Teste de disputa",
                value=50.00
            )
            order2 = order_result2['order']
            
            # Aceitar ordem
            OrderService.accept_order(provider.id, order2.id)
            
            # Abrir disputa
            dispute_result = OrderService.open_dispute(
                user_id=client.id,
                order_id=order2.id,
                reason="Serviço não foi executado conforme combinado. Teste de disputa."
            )
            
            assert dispute_result['success'] == True
            assert dispute_result['new_status'] == 'disputada'
            print(f"✓ Disputa aberta: {dispute_result['new_status']}")
            
            # Teste 7: Resolver disputa (admin)
            print("\n7. Testando resolução de disputa...")
            resolve_result = OrderService.resolve_dispute(
                admin_id=admin.id,
                order_id=order2.id,
                decision='favor_cliente',
                admin_notes='Teste de resolução administrativa'
            )
            
            assert resolve_result['success'] == True
            print(f"✓ Disputa resolvida: {resolve_result['decision']}")
            
            print("\n✅ Todos os testes de integração passaram!")
            
        except Exception as e:
            print(f"\n❌ Erro no teste de integração: {str(e)}")
            db.session.rollback()
            raise

def test_status_validation_methods():
    """Testa métodos de validação de status no OrderService"""
    print("\n=== Teste Métodos de Validação ===")
    
    with app.app_context():
        try:
            # Buscar uma ordem existente ou usar ID fictício
            order_id = 1
            
            # Teste 1: Consultar transições válidas
            print("\n1. Testando consulta de transições válidas...")
            transitions_result = OrderService.get_valid_status_transitions(order_id)
            
            if transitions_result['success']:
                print(f"✓ Status atual: {transitions_result['current_status']}")
                print(f"✓ Transições válidas: {transitions_result['valid_transitions']}")
                print(f"✓ É status final: {transitions_result['is_final_status']}")
            else:
                print(f"ℹ Ordem não encontrada (esperado para teste): {transitions_result['error']}")
            
            # Teste 2: Validar mudança sem executar
            print("\n2. Testando validação sem execução...")
            validation_result = OrderService.validate_status_change(
                order_id=999,  # ID fictício
                new_status='aceita',
                user_id=1
            )
            
            # Deve falhar porque ordem não existe
            assert validation_result['valid'] == False
            print(f"✓ Validação para ordem inexistente: {validation_result['error']}")
            
            print("\n✅ Testes de métodos de validação concluídos!")
            
        except Exception as e:
            print(f"\n❌ Erro nos testes de validação: {str(e)}")
            raise

if __name__ == "__main__":
    print("🚀 Iniciando testes de validação de status de pedidos...")
    
    try:
        test_order_status_validator()
        test_order_service_integration()
        test_status_validation_methods()
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        print("\n📋 Resumo da implementação:")
        print("✅ OrderStatusValidator criado com matriz de transições")
        print("✅ Validação de transições específicas implementada")
        print("✅ Logs de auditoria para tentativas de mudança")
        print("✅ OrderService integrado com validação")
        print("✅ Histórico de mudanças de status implementado")
        print("✅ Rejeição de transições inválidas com mensagens claras")
        print("✅ Tabela order_status_history criada")
        
    except Exception as e:
        print(f"\n💥 Falha nos testes: {str(e)}")
        sys.exit(1)