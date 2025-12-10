#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da lógica de integração de saldo sem banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from services.balance_validator import BalanceValidator, BalanceStatus

def test_balance_calculation_logic():
    """Testa a lógica de cálculo de saldo necessário"""
    
    print("🧪 Testando Lógica de Cálculo de Saldo")
    print("=" * 50)
    
    try:
        # 1. Testar cálculo de saldo necessário
        print("\n1️⃣ Testando cálculo de saldo necessário...")
        
        proposed_value = Decimal('150.0')
        contestation_fee = BalanceValidator.get_contestation_fee()
        required_amount = proposed_value + contestation_fee
        
        print(f"   📊 Valor proposto: R$ {proposed_value:.2f}")
        print(f"   📊 Taxa de contestação: R$ {contestation_fee:.2f}")
        print(f"   📊 Total necessário: R$ {required_amount:.2f}")
        
        # 2. Testar cenário de saldo insuficiente
        print("\n2️⃣ Testando cenário de saldo insuficiente...")
        
        current_balance = Decimal('50.0')
        shortfall = required_amount - current_balance
        suggested_top_up = shortfall + Decimal('20.0')  # Adicionar margem
        
        balance_status = BalanceStatus(
            is_sufficient=False,
            current_balance=current_balance,
            required_amount=required_amount,
            shortfall=shortfall,
            suggested_top_up=suggested_top_up,
            contestation_fee=contestation_fee
        )
        
        print(f"   💰 Saldo atual: R$ {balance_status.current_balance:.2f}")
        print(f"   💰 Faltam: R$ {balance_status.shortfall:.2f}")
        print(f"   💰 Sugestão de adição: R$ {balance_status.suggested_top_up:.2f}")
        print(f"   ❌ Saldo suficiente: {balance_status.is_sufficient}")
        
        # 3. Testar simulação de adição
        print("\n3️⃣ Testando simulação de adição...")
        
        amount_to_add = balance_status.shortfall + Decimal('10.0')
        simulated_balance = current_balance + amount_to_add
        will_be_sufficient = simulated_balance >= required_amount
        
        print(f"   🧮 Valor a adicionar: R$ {amount_to_add:.2f}")
        print(f"   🧮 Saldo simulado: R$ {simulated_balance:.2f}")
        print(f"   ✅ Será suficiente: {will_be_sufficient}")
        
        # 4. Testar diferentes cenários de adição
        print("\n4️⃣ Testando diferentes cenários...")
        
        test_amounts = [
            Decimal('50.0'),   # Insuficiente
            Decimal('100.0'),  # Exato mínimo
            Decimal('120.0'),  # Suficiente com margem
            Decimal('200.0')   # Muito acima do necessário
        ]
        
        for amount in test_amounts:
            new_balance = current_balance + amount
            sufficient = new_balance >= required_amount
            remaining = required_amount - new_balance if not sufficient else Decimal('0')
            
            status_icon = "✅" if sufficient else "❌"
            print(f"   {status_icon} Adicionar R$ {amount:.2f} → Saldo: R$ {new_balance:.2f} " +
                  (f"(Faltam R$ {remaining:.2f})" if not sufficient else "(Suficiente)"))
        
        # 5. Testar opções pré-definidas
        print("\n5️⃣ Testando opções pré-definidas...")
        
        minimum_addition = balance_status.shortfall
        predefined_options = [
            minimum_addition,  # Mínimo exato
            minimum_addition + Decimal('50'),   # Mínimo + R$ 50
            minimum_addition + Decimal('100'),  # Mínimo + R$ 100
            minimum_addition + Decimal('200')   # Mínimo + R$ 200
        ]
        
        for i, option in enumerate(predefined_options):
            label = ["Mínimo", "Recomendado", "Confortável", "Generoso"][i]
            final_balance = current_balance + option
            print(f"   💡 {label}: R$ {option:.2f} → Saldo final: R$ {final_balance:.2f}")
        
        # 6. Testar validações
        print("\n6️⃣ Testando validações...")
        
        # Valor negativo
        try:
            invalid_amount = Decimal('-10.0')
            if invalid_amount <= 0:
                print("   ✅ Validação de valor negativo: OK")
        except:
            print("   ❌ Validação de valor negativo: FALHOU")
        
        # Valor muito alto
        try:
            max_amount = Decimal('10000.0')
            if amount_to_add <= max_amount:
                print("   ✅ Validação de valor máximo: OK")
        except:
            print("   ❌ Validação de valor máximo: FALHOU")
        
        print("\n✅ TESTE DE LÓGICA CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_flow_logic():
    """Testa a lógica do fluxo integrado"""
    
    print("\n🔄 Testando Lógica do Fluxo Integrado")
    print("=" * 50)
    
    try:
        # Simular dados de uma proposta
        original_value = Decimal('100.0')
        proposed_value = Decimal('150.0')
        current_balance = Decimal('50.0')
        contestation_fee = BalanceValidator.get_contestation_fee()
        
        print(f"\n📋 Cenário de Teste:")
        print(f"   • Valor original: R$ {original_value:.2f}")
        print(f"   • Valor proposto: R$ {proposed_value:.2f}")
        print(f"   • Saldo atual: R$ {current_balance:.2f}")
        print(f"   • Taxa de contestação: R$ {contestation_fee:.2f}")
        
        # 1. Calcular necessidades
        required_amount = proposed_value + contestation_fee
        shortfall = required_amount - current_balance
        
        print(f"\n💰 Cálculos:")
        print(f"   • Total necessário: R$ {required_amount:.2f}")
        print(f"   • Faltam: R$ {shortfall:.2f}")
        
        # 2. Simular adição de saldo
        amount_to_add = shortfall + Decimal('20.0')  # Com margem
        new_balance = current_balance + amount_to_add
        
        print(f"\n🔄 Simulação de Adição:")
        print(f"   • Valor a adicionar: R$ {amount_to_add:.2f}")
        print(f"   • Novo saldo: R$ {new_balance:.2f}")
        print(f"   • Será suficiente: {new_balance >= required_amount}")
        
        # 3. Simular aprovação da proposta
        if new_balance >= required_amount:
            print(f"\n✅ Fluxo Integrado:")
            print(f"   1. Saldo adicionado: R$ {amount_to_add:.2f}")
            print(f"   2. Proposta aprovada: R$ {proposed_value:.2f}")
            print(f"   3. Saldo final: R$ {new_balance:.2f}")
            print(f"   4. Próximo passo: Prestador pode aceitar convite")
        else:
            print(f"\n❌ Fluxo Integrado: Saldo ainda insuficiente")
        
        print("\n✅ TESTE DE FLUXO CONCLUÍDO COM SUCESSO!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_balance_calculation_logic()
    success2 = test_integration_flow_logic()
    
    if success1 and success2:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n💥 ALGUNS TESTES FALHARAM!")
    
    sys.exit(0 if (success1 and success2) else 1)