#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Demonstração do Sistema de Configuração de Taxas
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from services.config_service import ConfigService
from decimal import Decimal

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_fees(title="Taxas Atuais"):
    fees = ConfigService.get_all_fees()
    print(f"\n{title}:")
    print(f"  • Taxa da Plataforma: {fees['platform_fee_percentage']}%")
    print(f"  • Taxa de Contestação: R$ {fees['contestation_fee']}")
    print(f"  • Taxa de Cancelamento: {fees['cancellation_fee_percentage']}%")

def calculate_example(order_value=1000):
    fees = ConfigService.get_all_fees()
    
    platform_amount = order_value * float(fees['platform_fee_percentage']) / 100
    contestation_amount = float(fees['contestation_fee'])
    cancellation_amount = order_value * float(fees['cancellation_fee_percentage']) / 100
    provider_receives = order_value - platform_amount
    
    print(f"\n💰 Exemplo de Cálculo (Ordem de R$ {order_value:.2f}):")
    print(f"  • Taxa da plataforma ({fees['platform_fee_percentage']}%): R$ {platform_amount:.2f}")
    print(f"  • Taxa de contestação (cada parte): R$ {contestation_amount:.2f}")
    print(f"  • Multa de cancelamento ({fees['cancellation_fee_percentage']}%): R$ {cancellation_amount:.2f}")
    print(f"  • Prestador recebe (ordem concluída): R$ {provider_receives:.2f}")

def demo():
    with app.app_context():
        print_header("DEMONSTRAÇÃO: Sistema de Configuração de Taxas")
        
        # Inicializar configurações padrão
        ConfigService.initialize_default_configs()
        
        # Mostrar taxas iniciais
        print_fees("📊 Taxas Padrão do Sistema")
        calculate_example()
        
        # Simular alteração de taxas
        print_header("Simulando Alteração de Taxas pelo Admin")
        
        print("\n🔧 Admin alterando taxas...")
        print("  • Nova taxa da plataforma: 7.5%")
        print("  • Nova taxa de contestação: R$ 15.00")
        print("  • Nova taxa de cancelamento: 12.0%")
        
        # Atualizar taxas
        ConfigService.set_platform_fee_percentage(Decimal('7.5'), admin_id=1)
        ConfigService.set_contestation_fee(Decimal('15.00'), admin_id=1)
        ConfigService.set_cancellation_fee_percentage(Decimal('12.0'), admin_id=1)
        
        print("\n✅ Taxas atualizadas com sucesso!")
        
        # Mostrar taxas atualizadas
        print_fees("📊 Taxas Após Atualização")
        calculate_example()
        
        # Demonstrar impacto
        print_header("Impacto das Alterações")
        
        print("\n📈 Comparação:")
        print("  Antes (5.0%):  Plataforma recebia R$ 50.00")
        print("  Depois (7.5%): Plataforma recebe R$ 75.00")
        print("  Diferença:     +R$ 25.00 (+50%)")
        
        print("\n  Antes (R$ 10.00):  Garantia de R$ 10.00")
        print("  Depois (R$ 15.00): Garantia de R$ 15.00")
        print("  Diferença:         +R$ 5.00 (+50%)")
        
        print("\n  Antes (10.0%):  Multa de R$ 100.00")
        print("  Depois (12.0%): Multa de R$ 120.00")
        print("  Diferença:      +R$ 20.00 (+20%)")
        
        # Demonstrar validações
        print_header("Demonstração de Validações")
        
        print("\n🔍 Testando validações...")
        
        # Teste 1: Taxa > 100%
        success, msg = ConfigService.set_platform_fee_percentage(Decimal('150'), admin_id=1)
        print(f"\n  Taxa 150%: {'❌ Rejeitada' if not success else '✅ Aceita'}")
        print(f"  Mensagem: {msg}")
        
        # Teste 2: Taxa negativa
        success, msg = ConfigService.set_platform_fee_percentage(Decimal('-5'), admin_id=1)
        print(f"\n  Taxa -5%: {'❌ Rejeitada' if not success else '✅ Aceita'}")
        print(f"  Mensagem: {msg}")
        
        # Teste 3: Taxa de contestação zero
        success, msg = ConfigService.set_contestation_fee(Decimal('0'), admin_id=1)
        print(f"\n  Taxa R$ 0: {'❌ Rejeitada' if not success else '✅ Aceita'}")
        print(f"  Mensagem: {msg}")
        
        # Teste 4: Taxa válida
        success, msg = ConfigService.set_platform_fee_percentage(Decimal('5.0'), admin_id=1)
        print(f"\n  Taxa 5.0%: {'✅ Aceita' if success else '❌ Rejeitada'}")
        print(f"  Mensagem: {msg}")
        
        # Informações finais
        print_header("Informações Importantes")
        
        print("\n📌 Pontos-Chave:")
        print("  1. Taxas são armazenadas em cada ordem no momento da criação")
        print("  2. Ordens antigas mantêm suas taxas originais")
        print("  3. Novas ordens usam as taxas atualizadas")
        print("  4. Todas as alterações são registradas em logs")
        print("  5. Cache de 5 minutos para melhor performance")
        
        print("\n🔗 Acesso:")
        print("  URL: /admin/configuracoes/taxas")
        print("  Menu: Configurações > Taxas de Ordens")
        
        print("\n" + "="*70)
        print("  Demonstração Concluída!")
        print("="*70 + "\n")

if __name__ == '__main__':
    demo()
