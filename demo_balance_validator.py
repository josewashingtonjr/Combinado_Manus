#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Demonstração do BalanceValidator
Mostra como usar as funcionalidades implementadas
"""

from decimal import Decimal
from services.balance_validator import BalanceValidator

def demo_calculate_required_balance():
    """Demonstra o cálculo do saldo necessário"""
    print("=== Cálculo do Saldo Necessário ===")
    
    valores_propostos = [Decimal('50.00'), Decimal('100.00'), Decimal('250.00')]
    
    for valor in valores_propostos:
        necessario = BalanceValidator.calculate_required_balance(valor)
        taxa = BalanceValidator.get_contestation_fee()
        
        print(f"Valor proposto: R$ {valor}")
        print(f"Taxa contestação: R$ {taxa}")
        print(f"Total necessário: R$ {necessario}")
        print(f"Fórmula: {valor} + {taxa} = {necessario}")
        print("-" * 40)

def demo_suggest_top_up():
    """Demonstra sugestões de recarga"""
    print("\n=== Sugestões de Recarga ===")
    
    cenarios = [
        (Decimal('100.00'), Decimal('80.00')),   # Saldo suficiente
        (Decimal('45.00'), Decimal('60.00')),    # Déficit pequeno
        (Decimal('20.00'), Decimal('100.00')),   # Déficit grande
        (Decimal('0.00'), Decimal('50.00')),     # Sem saldo
    ]
    
    for saldo_atual, valor_necessario in cenarios:
        sugestao = BalanceValidator.suggest_top_up_amount(saldo_atual, valor_necessario)
        deficit = max(Decimal('0.00'), valor_necessario - saldo_atual)
        
        print(f"Saldo atual: R$ {saldo_atual}")
        print(f"Valor necessário: R$ {valor_necessario}")
        print(f"Déficit: R$ {deficit}")
        print(f"Sugestão de recarga: R$ {sugestao}")
        
        if sugestao == 0:
            print("✓ Saldo suficiente - não precisa recarregar")
        else:
            print(f"💡 Recarregue R$ {sugestao} para ter margem de segurança")
        
        print("-" * 40)

def demo_validation_scenarios():
    """Demonstra cenários de validação"""
    print("\n=== Cenários de Validação ===")
    
    # Simular diferentes cenários sem usar banco de dados
    print("Nota: Esta demonstração simula cenários sem conectar ao banco de dados")
    print("Em uso real, o BalanceValidator consultaria o saldo real do cliente")
    
    cenarios = [
        ("Cliente com saldo alto", Decimal('500.00'), Decimal('100.00')),
        ("Cliente com saldo justo", Decimal('110.00'), Decimal('100.00')),
        ("Cliente com saldo insuficiente", Decimal('50.00'), Decimal('100.00')),
        ("Cliente sem saldo", Decimal('0.00'), Decimal('75.00')),
    ]
    
    for descricao, saldo_simulado, valor_proposto in cenarios:
        print(f"\n{descricao}:")
        print(f"  Saldo simulado: R$ {saldo_simulado}")
        print(f"  Valor proposto: R$ {valor_proposto}")
        
        # Calcular o que seria necessário
        necessario = BalanceValidator.calculate_required_balance(valor_proposto)
        suficiente = saldo_simulado >= necessario
        deficit = max(Decimal('0.00'), necessario - saldo_simulado)
        sugestao = BalanceValidator.suggest_top_up_amount(saldo_simulado, necessario)
        
        print(f"  Total necessário: R$ {necessario}")
        print(f"  Saldo suficiente: {'✓ Sim' if suficiente else '✗ Não'}")
        
        if not suficiente:
            print(f"  Déficit: R$ {deficit}")
            print(f"  Sugestão de recarga: R$ {sugestao}")
        
        print("-" * 50)

def main():
    """Executa todas as demonstrações"""
    print("🏦 DEMONSTRAÇÃO DO BALANCE VALIDATOR 🏦")
    print("=" * 60)
    
    try:
        demo_calculate_required_balance()
        demo_suggest_top_up()
        demo_validation_scenarios()
        
        print("\n" + "=" * 60)
        print("✅ Demonstração concluída com sucesso!")
        print("\nO BalanceValidator implementa:")
        print("• ✓ Cálculo de saldo necessário (valor + taxa)")
        print("• ✓ Verificação de suficiência de saldo")
        print("• ✓ Sugestão inteligente de recarga")
        print("• ✓ Reserva automática de fundos")
        print("• ✓ Integração com sistema de configurações")
        
    except Exception as e:
        print(f"\n❌ Erro na demonstração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()