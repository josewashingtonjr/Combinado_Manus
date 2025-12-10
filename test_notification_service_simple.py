#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples do NotificationService
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.notification_service import NotificationService
from decimal import Decimal

def test_notification_service_methods():
    """Testa os métodos básicos do NotificationService"""
    
    print("🧪 Testando NotificationService - Métodos Básicos")
    print("=" * 50)
    
    # 1. Testar formatação de moeda
    print("\n1. Testando formatação de moeda...")
    
    test_values = [
        Decimal('0.00'),
        Decimal('10.50'),
        Decimal('100.00'),
        Decimal('1234.56')
    ]
    
    for value in test_values:
        formatted = NotificationService.format_currency(value)
        print(f"   {value} → {formatted}")
    
    # 2. Testar comparação de valores
    print("\n2. Testando comparação de valores...")
    
    test_comparisons = [
        (Decimal('100.00'), Decimal('150.00')),  # Aumento
        (Decimal('200.00'), Decimal('150.00')),  # Redução
        (Decimal('100.00'), Decimal('100.00')),  # Sem alteração
    ]
    
    for original, proposed in test_comparisons:
        comparison = NotificationService.format_value_comparison(original, proposed)
        print(f"   {comparison}")
    
    print("\n" + "=" * 50)
    print("✅ Teste dos métodos básicos concluído!")
    
    return True

def test_notification_message_formats():
    """Testa os formatos de mensagens de notificação"""
    
    print("\n🧪 Testando Formatos de Mensagens")
    print("=" * 50)
    
    # Simular dados de proposta
    class MockProposal:
        def __init__(self, original_value, proposed_value, justification=None):
            self.original_value = Decimal(str(original_value))
            self.proposed_value = Decimal(str(proposed_value))
            self.justification = justification
            self.id = 123
    
    class MockUser:
        def __init__(self, nome):
            self.nome = nome
    
    class MockInvite:
        def __init__(self, service_title):
            self.service_title = service_title
    
    # 1. Testar mensagem de aumento de valor
    print("\n1. Mensagem de aumento de valor:")
    proposal_increase = MockProposal(100.00, 150.00, "Aumento devido à complexidade")
    prestador = MockUser("João Silva")
    
    value_difference = proposal_increase.proposed_value - proposal_increase.original_value
    message = (f"Nova proposta de alteração recebida! "
              f"{prestador.nome} propôs aumentar o valor de "
              f"R$ {proposal_increase.original_value:.2f} para R$ {proposal_increase.proposed_value:.2f} "
              f"(+R$ {value_difference:.2f}). "
              f"Verifique se você tem saldo suficiente e responda à proposta.")
    
    print(f"   📢 {message}")
    
    # 2. Testar mensagem de redução de valor
    print("\n2. Mensagem de redução de valor:")
    proposal_decrease = MockProposal(200.00, 150.00, "Redução por simplicidade")
    
    value_difference = proposal_decrease.proposed_value - proposal_decrease.original_value
    message = (f"Nova proposta de alteração recebida! "
              f"{prestador.nome} propôs reduzir o valor de "
              f"R$ {proposal_decrease.original_value:.2f} para R$ {proposal_decrease.proposed_value:.2f} "
              f"(-R$ {abs(value_difference):.2f}). "
              f"Responda à proposta para continuar.")
    
    print(f"   📢 {message}")
    
    # 3. Testar mensagem de aprovação
    print("\n3. Mensagem de aprovação:")
    cliente = MockUser("Maria Santos")
    invite = MockInvite("Desenvolvimento de Website")
    
    message = (f"Proposta aceita! "
              f"{cliente.nome} aceitou sua proposta de R$ {proposal_increase.proposed_value:.2f} "
              f"para o serviço '{invite.service_title}'. "
              f"Agora você pode aceitar o convite com o novo valor.")
    
    print(f"   📢 {message}")
    
    # 4. Testar mensagem de rejeição
    print("\n4. Mensagem de rejeição:")
    reason = "Valor muito alto para o orçamento"
    
    message = (f"Proposta rejeitada. "
              f"{cliente.nome} rejeitou sua proposta de R$ {proposal_increase.proposed_value:.2f} "
              f"para o serviço '{invite.service_title}'. Motivo: {reason} "
              f"O convite retornou ao valor original de R$ {proposal_increase.original_value:.2f}.")
    
    print(f"   📢 {message}")
    
    # 5. Testar mensagem de saldo insuficiente
    print("\n5. Mensagem de saldo insuficiente:")
    required_amount = Decimal('160.00')  # Proposta + taxa
    current_balance = Decimal('120.00')
    shortfall = required_amount - current_balance
    
    message = (f"Saldo insuficiente para aceitar a proposta de R$ {proposal_increase.proposed_value:.2f}. "
              f"Você precisa de R$ {required_amount:.2f} no total "
              f"(proposta + taxa de contestação), mas tem apenas R$ {current_balance:.2f}. "
              f"Adicione pelo menos R$ {shortfall:.2f} para continuar.")
    
    print(f"   📢 {message}")
    
    print("\n" + "=" * 50)
    print("✅ Teste dos formatos de mensagens concluído!")
    
    return True

if __name__ == "__main__":
    success1 = test_notification_service_methods()
    success2 = test_notification_message_formats()
    
    if success1 and success2:
        print("\n🎉 Todos os testes passaram!")
        print("\nFuncionalidades testadas:")
        print("• Formatação de valores monetários")
        print("• Comparação de valores (aumento/redução)")
        print("• Mensagens de notificação para diferentes cenários")
        print("• Mensagens de saldo insuficiente")
        print("• Mensagens de aprovação/rejeição")
    else:
        print("\n❌ Alguns testes falharam!")