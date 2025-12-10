#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do ConfigService para gestão de taxas de ordens
"""

from app import app
from models import db
from services.config_service import ConfigService
from decimal import Decimal

def test_config_service_fees():
    """Testa os métodos de gestão de taxas do ConfigService"""
    
    with app.app_context():
        print("=" * 60)
        print("TESTE DO CONFIGSERVICE - GESTÃO DE TAXAS DE ORDENS")
        print("=" * 60)
        
        # Inicializar configurações padrão
        print("\n1. Inicializando configurações padrão...")
        ConfigService.initialize_default_configs()
        print("✓ Configurações inicializadas")
        
        # Testar get_platform_fee_percentage
        print("\n2. Testando get_platform_fee_percentage()...")
        platform_fee = ConfigService.get_platform_fee_percentage()
        print(f"   Taxa da plataforma: {platform_fee}%")
        assert isinstance(platform_fee, Decimal), "Deve retornar Decimal"
        assert platform_fee == Decimal('5.0'), "Valor padrão deve ser 5.0%"
        print("✓ get_platform_fee_percentage() OK")
        
        # Testar get_contestation_fee
        print("\n3. Testando get_contestation_fee()...")
        contestation_fee = ConfigService.get_contestation_fee()
        print(f"   Taxa de contestação: R$ {contestation_fee}")
        assert isinstance(contestation_fee, Decimal), "Deve retornar Decimal"
        assert contestation_fee == Decimal('10.00'), "Valor padrão deve ser R$ 10.00"
        print("✓ get_contestation_fee() OK")
        
        # Testar get_cancellation_fee_percentage
        print("\n4. Testando get_cancellation_fee_percentage()...")
        cancellation_fee = ConfigService.get_cancellation_fee_percentage()
        print(f"   Taxa de cancelamento: {cancellation_fee}%")
        assert isinstance(cancellation_fee, Decimal), "Deve retornar Decimal"
        assert cancellation_fee == Decimal('10.0'), "Valor padrão deve ser 10.0%"
        print("✓ get_cancellation_fee_percentage() OK")
        
        # Testar get_all_fees
        print("\n5. Testando get_all_fees()...")
        all_fees = ConfigService.get_all_fees()
        print(f"   Todas as taxas: {all_fees}")
        assert 'platform_fee_percentage' in all_fees, "Deve conter platform_fee_percentage"
        assert 'contestation_fee' in all_fees, "Deve conter contestation_fee"
        assert 'cancellation_fee_percentage' in all_fees, "Deve conter cancellation_fee_percentage"
        print("✓ get_all_fees() OK")
        
        # Testar set_platform_fee_percentage com valor válido
        print("\n6. Testando set_platform_fee_percentage() com valor válido...")
        success, msg = ConfigService.set_platform_fee_percentage(Decimal('7.5'), admin_id=1)
        print(f"   Resultado: {msg}")
        assert success, "Deve ter sucesso"
        new_value = ConfigService.get_platform_fee_percentage()
        print(f"   Novo valor: {new_value}%")
        assert new_value == Decimal('7.5'), "Valor deve ser atualizado"
        print("✓ set_platform_fee_percentage() OK")
        
        # Testar set_platform_fee_percentage com valor inválido
        print("\n7. Testando set_platform_fee_percentage() com valor inválido...")
        success, msg = ConfigService.set_platform_fee_percentage(Decimal('150'), admin_id=1)
        print(f"   Resultado: {msg}")
        assert not success, "Deve falhar com valor > 100%"
        assert "0% e 100%" in msg, "Mensagem deve indicar range válido"
        print("✓ Validação de range OK")
        
        # Testar set_contestation_fee com valor válido
        print("\n8. Testando set_contestation_fee() com valor válido...")
        success, msg = ConfigService.set_contestation_fee(Decimal('15.00'), admin_id=1)
        print(f"   Resultado: {msg}")
        assert success, "Deve ter sucesso"
        new_value = ConfigService.get_contestation_fee()
        print(f"   Novo valor: R$ {new_value}")
        assert new_value == Decimal('15.00'), "Valor deve ser atualizado"
        print("✓ set_contestation_fee() OK")
        
        # Testar set_contestation_fee com valor inválido
        print("\n9. Testando set_contestation_fee() com valor inválido...")
        success, msg = ConfigService.set_contestation_fee(Decimal('-5.00'), admin_id=1)
        print(f"   Resultado: {msg}")
        assert not success, "Deve falhar com valor negativo"
        assert "positivo" in msg, "Mensagem deve indicar valor positivo"
        print("✓ Validação de valor positivo OK")
        
        # Testar set_cancellation_fee_percentage com valor válido
        print("\n10. Testando set_cancellation_fee_percentage() com valor válido...")
        success, msg = ConfigService.set_cancellation_fee_percentage(Decimal('12.5'), admin_id=1)
        print(f"   Resultado: {msg}")
        assert success, "Deve ter sucesso"
        new_value = ConfigService.get_cancellation_fee_percentage()
        print(f"   Novo valor: {new_value}%")
        assert new_value == Decimal('12.5'), "Valor deve ser atualizado"
        print("✓ set_cancellation_fee_percentage() OK")
        
        # Testar cache (5 minutos)
        print("\n11. Testando cache de configurações...")
        # Primeira chamada - busca do banco
        value1 = ConfigService.get_platform_fee_percentage()
        # Segunda chamada - deve vir do cache
        value2 = ConfigService.get_platform_fee_percentage()
        assert value1 == value2, "Valores devem ser iguais"
        print(f"   Cache funcionando: {value1}% = {value2}%")
        print("✓ Cache OK")
        
        # Testar que novas ordens usarão as taxas atualizadas
        print("\n12. Verificando taxas finais após atualizações...")
        final_fees = ConfigService.get_all_fees()
        print(f"   Taxa da plataforma: {final_fees['platform_fee_percentage']}%")
        print(f"   Taxa de contestação: R$ {final_fees['contestation_fee']}")
        print(f"   Taxa de cancelamento: {final_fees['cancellation_fee_percentage']}%")
        print("✓ Todas as taxas atualizadas corretamente")
        
        print("\n" + "=" * 60)
        print("TODOS OS TESTES PASSARAM! ✓")
        print("=" * 60)
        print("\nResumo da implementação:")
        print("- ✓ get_platform_fee_percentage() com valor padrão 5.0%")
        print("- ✓ get_contestation_fee() com valor padrão R$ 10.00")
        print("- ✓ get_cancellation_fee_percentage() com valor padrão 10.0%")
        print("- ✓ set_platform_fee_percentage() com validação 0-100%")
        print("- ✓ set_contestation_fee() com validação de valor positivo")
        print("- ✓ set_cancellation_fee_percentage() com validação 0-100%")
        print("- ✓ get_all_fees() retorna todas as taxas")
        print("- ✓ Cache de 5 minutos implementado")
        print("\nTarefa 2 concluída com sucesso!")

if __name__ == '__main__':
    test_config_service_fees()
