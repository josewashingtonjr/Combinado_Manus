#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simplificado para validação de transições de status de pedidos
Foca na lógica de validação sem acesso ao banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.order_status_validator import OrderStatusValidator

def test_order_status_validator_logic():
    """Testa a lógica do OrderStatusValidator sem banco de dados"""
    print("=== Teste Lógica OrderStatusValidator ===")
    
    try:
        # Teste 1: Matriz de transições válidas
        print("\n1. Testando matriz de transições...")
        
        # Verificar transições válidas para cada status
        expected_transitions = {
            'disponivel': ['aceita', 'cancelada'],
            'aceita': ['em_andamento', 'cancelada', 'disputada'],
            'em_andamento': ['aguardando_confirmacao', 'cancelada', 'disputada'],
            'aguardando_confirmacao': ['concluida', 'cancelada', 'disputada'],
            'concluida': ['disputada'],
            'disputada': ['concluida', 'cancelada', 'resolvida'],
            'cancelada': [],
            'resolvida': []
        }
        
        for status, expected in expected_transitions.items():
            actual = OrderStatusValidator.get_valid_transitions(status)
            assert actual == expected, f"Transições para {status}: esperado {expected}, obtido {actual}"
            print(f"✓ {status}: {actual}")
        
        # Teste 2: Métodos auxiliares
        print("\n2. Testando métodos auxiliares...")
        
        # Status finais
        final_statuses = ['cancelada', 'resolvida']
        for status in final_statuses:
            assert OrderStatusValidator.is_final_status(status) == True
            print(f"✓ {status} é status final")
        
        # Status não finais
        non_final_statuses = ['disponivel', 'aceita', 'em_andamento']
        for status in non_final_statuses:
            assert OrderStatusValidator.is_final_status(status) == False
            print(f"✓ {status} não é status final")
        
        # Transições que requerem admin
        admin_transitions = [
            ('disputada', 'concluida'),
            ('disputada', 'cancelada'),
            ('disputada', 'resolvida')
        ]
        
        for current, new in admin_transitions:
            assert OrderStatusValidator.requires_admin_authorization(current, new) == True
            print(f"✓ {current} -> {new} requer admin")
        
        # Transições que não requerem admin
        user_transitions = [
            ('disponivel', 'aceita'),
            ('aceita', 'em_andamento'),
            ('em_andamento', 'aguardando_confirmacao')
        ]
        
        for current, new in user_transitions:
            assert OrderStatusValidator.requires_admin_authorization(current, new) == False
            print(f"✓ {current} -> {new} não requer admin")
        
        # Teste 3: Descrições de transições
        print("\n3. Testando descrições de transições...")
        
        description = OrderStatusValidator.get_transition_description('disponivel', 'aceita')
        assert 'Prestador aceitou a ordem' in description
        print(f"✓ Descrição disponivel->aceita: {description}")
        
        description = OrderStatusValidator.get_transition_description('em_andamento', 'aguardando_confirmacao')
        assert 'Prestador marcou ordem como concluída' in description
        print(f"✓ Descrição em_andamento->aguardando_confirmacao: {description}")
        
        # Teste 4: Validação básica de transições (sem banco)
        print("\n4. Testando validação básica...")
        
        # Transição válida
        valid_transitions = [
            ('disponivel', 'aceita'),
            ('aceita', 'em_andamento'),
            ('em_andamento', 'cancelada'),
            ('concluida', 'disputada')
        ]
        
        for current, new in valid_transitions:
            if current in OrderStatusValidator.VALID_TRANSITIONS:
                valid_next = OrderStatusValidator.VALID_TRANSITIONS[current]
                assert new in valid_next, f"Transição {current}->{new} deveria ser válida"
                print(f"✓ {current} -> {new} é válida")
        
        # Transições inválidas
        invalid_transitions = [
            ('disponivel', 'concluida'),
            ('cancelada', 'aceita'),
            ('resolvida', 'em_andamento'),
            ('aceita', 'resolvida')
        ]
        
        for current, new in invalid_transitions:
            if current in OrderStatusValidator.VALID_TRANSITIONS:
                valid_next = OrderStatusValidator.VALID_TRANSITIONS[current]
                assert new not in valid_next, f"Transição {current}->{new} deveria ser inválida"
                print(f"✓ {current} -> {new} é inválida (correto)")
        
        print("\n✅ Todos os testes de lógica passaram!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste de lógica: {str(e)}")
        return False

def test_validation_rules():
    """Testa regras específicas de validação"""
    print("\n=== Teste Regras de Validação ===")
    
    try:
        # Teste 1: Verificar cobertura completa da matriz
        print("\n1. Verificando cobertura da matriz...")
        
        all_statuses = [
            'disponivel', 'aceita', 'em_andamento', 'aguardando_confirmacao',
            'concluida', 'disputada', 'cancelada', 'resolvida'
        ]
        
        for status in all_statuses:
            assert status in OrderStatusValidator.VALID_TRANSITIONS, f"Status {status} não está na matriz"
            print(f"✓ Status {status} está na matriz")
        
        # Teste 2: Verificar que estados finais não têm transições
        print("\n2. Verificando estados finais...")
        
        final_states = ['cancelada', 'resolvida']
        for state in final_states:
            transitions = OrderStatusValidator.VALID_TRANSITIONS[state]
            assert len(transitions) == 0, f"Estado final {state} não deveria ter transições: {transitions}"
            print(f"✓ Estado final {state} não tem transições")
        
        # Teste 3: Verificar fluxo principal
        print("\n3. Verificando fluxo principal...")
        
        main_flow = [
            ('disponivel', 'aceita'),
            ('aceita', 'em_andamento'),
            ('em_andamento', 'aguardando_confirmacao'),
            ('aguardando_confirmacao', 'concluida')
        ]
        
        for current, next_status in main_flow:
            valid_next = OrderStatusValidator.VALID_TRANSITIONS[current]
            assert next_status in valid_next, f"Fluxo principal quebrado em {current}->{next_status}"
            print(f"✓ Fluxo principal {current} -> {next_status}")
        
        # Teste 4: Verificar fluxos de exceção
        print("\n4. Verificando fluxos de exceção...")
        
        exception_flows = [
            ('disponivel', 'cancelada'),  # Cancelamento antes de aceitar
            ('aceita', 'disputada'),      # Disputa após aceitação
            ('em_andamento', 'disputada'), # Disputa durante execução
            ('concluida', 'disputada')    # Disputa após conclusão
        ]
        
        for current, next_status in exception_flows:
            valid_next = OrderStatusValidator.VALID_TRANSITIONS[current]
            assert next_status in valid_next, f"Fluxo de exceção quebrado em {current}->{next_status}"
            print(f"✓ Fluxo de exceção {current} -> {next_status}")
        
        print("\n✅ Todas as regras de validação estão corretas!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nas regras de validação: {str(e)}")
        return False

def test_comprehensive_coverage():
    """Testa cobertura abrangente do sistema de validação"""
    print("\n=== Teste Cobertura Abrangente ===")
    
    try:
        # Teste 1: Todos os status têm pelo menos uma entrada
        print("\n1. Verificando entradas para todos os status...")
        
        all_statuses = set(OrderStatusValidator.VALID_TRANSITIONS.keys())
        
        # Verificar se todos os status que aparecem como destino também têm entrada
        all_destinations = set()
        for transitions in OrderStatusValidator.VALID_TRANSITIONS.values():
            all_destinations.update(transitions)
        
        for dest in all_destinations:
            assert dest in all_statuses, f"Status de destino {dest} não tem entrada na matriz"
            print(f"✓ Status {dest} tem entrada na matriz")
        
        # Teste 2: Verificar descrições para transições principais
        print("\n2. Verificando descrições...")
        
        key_transitions = [
            ('disponivel', 'aceita'),
            ('aceita', 'em_andamento'),
            ('em_andamento', 'aguardando_confirmacao'),
            ('aguardando_confirmacao', 'concluida'),
            ('aceita', 'disputada'),
            ('disputada', 'resolvida')
        ]
        
        for current, new in key_transitions:
            description = OrderStatusValidator.get_transition_description(current, new)
            assert len(description) > 10, f"Descrição muito curta para {current}->{new}: {description}"
            print(f"✓ Descrição para {current}->{new}: {description[:50]}...")
        
        # Teste 3: Verificar consistência de autorização admin
        print("\n3. Verificando consistência de autorização admin...")
        
        # Todas as transições saindo de 'disputada' devem requerer admin
        disputed_transitions = OrderStatusValidator.VALID_TRANSITIONS['disputada']
        for next_status in disputed_transitions:
            requires_admin = OrderStatusValidator.requires_admin_authorization('disputada', next_status)
            assert requires_admin == True, f"Transição disputada->{next_status} deveria requerer admin"
            print(f"✓ disputada -> {next_status} requer admin")
        
        print("\n✅ Cobertura abrangente verificada!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na cobertura abrangente: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes simplificados de validação de status...")
    
    success = True
    
    try:
        success &= test_order_status_validator_logic()
        success &= test_validation_rules()
        success &= test_comprehensive_coverage()
        
        if success:
            print("\n🎉 Todos os testes simplificados passaram!")
            print("\n📋 Resumo da validação:")
            print("✅ Matriz de transições implementada corretamente")
            print("✅ Estados finais identificados")
            print("✅ Transições que requerem admin identificadas")
            print("✅ Descrições de transições implementadas")
            print("✅ Fluxo principal de ordem validado")
            print("✅ Fluxos de exceção (cancelamento/disputa) validados")
            print("✅ Cobertura completa de todos os status")
            print("✅ Consistência de regras de autorização")
            
            print("\n🔧 Próximos passos para teste completo:")
            print("- Executar teste com banco de dados configurado")
            print("- Testar integração com OrderService")
            print("- Validar histórico de mudanças de status")
            
        else:
            print("\n💥 Alguns testes falharam!")
            
    except Exception as e:
        print(f"\n💥 Erro geral nos testes: {str(e)}")
        success = False
    
    sys.exit(0 if success else 1)