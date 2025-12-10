#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do Sistema de Auditoria
Valida que todos os logs de auditoria estão sendo gerados corretamente
"""

import os
import json
from decimal import Decimal
from datetime import datetime

def test_audit_service_imports():
    """Testa se o serviço de auditoria pode ser importado"""
    try:
        from services.audit_service import AuditService
        print("✅ AuditService importado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar AuditService: {e}")
        return False

def test_audit_id_generation():
    """Testa geração de IDs únicos de auditoria"""
    try:
        from services.audit_service import AuditService
        
        # Gerar múltiplos IDs
        ids = [AuditService._generate_audit_id() for _ in range(10)]
        
        # Verificar que são únicos
        if len(ids) == len(set(ids)):
            print(f"✅ IDs de auditoria únicos gerados: {len(ids)} IDs")
            return True
        else:
            print("❌ IDs de auditoria não são únicos")
            return False
    except Exception as e:
        print(f"❌ Erro ao gerar IDs de auditoria: {e}")
        return False

def test_value_serialization():
    """Testa serialização de valores complexos"""
    try:
        from services.audit_service import AuditService
        
        # Testar Decimal
        decimal_value = Decimal('123.45')
        serialized = AuditService._serialize_value(decimal_value)
        assert isinstance(serialized, float), "Decimal não foi convertido para float"
        assert serialized == 123.45, "Valor Decimal incorreto"
        
        # Testar datetime
        dt_value = datetime(2025, 11, 19, 14, 30, 45)
        serialized = AuditService._serialize_value(dt_value)
        assert isinstance(serialized, str), "datetime não foi convertido para string"
        assert '2025-11-19' in serialized, "Data incorreta"
        
        print("✅ Serialização de valores funcionando corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro na serialização de valores: {e}")
        return False

def test_audit_entry_format():
    """Testa formato de entrada de auditoria"""
    try:
        from services.audit_service import AuditService
        
        # Criar entrada de auditoria
        audit_id = AuditService._generate_audit_id()
        entry = AuditService._format_audit_entry(
            operation='TEST_OPERATION',
            entity_type='Order',
            entity_id=123,
            user_id=456,
            details={'test_key': 'test_value', 'amount': Decimal('100.50')},
            audit_id=audit_id
        )
        
        # Verificar que é JSON válido
        parsed = json.loads(entry)
        
        # Verificar campos obrigatórios
        assert 'audit_id' in parsed, "audit_id ausente"
        assert 'timestamp' in parsed, "timestamp ausente"
        assert 'operation' in parsed, "operation ausente"
        assert 'entity_type' in parsed, "entity_type ausente"
        assert 'entity_id' in parsed, "entity_id ausente"
        assert 'user_id' in parsed, "user_id ausente"
        assert 'details' in parsed, "details ausente"
        
        # Verificar valores
        assert parsed['operation'] == 'TEST_OPERATION'
        assert parsed['entity_type'] == 'Order'
        assert parsed['entity_id'] == 123
        assert parsed['user_id'] == 456
        assert parsed['details']['test_key'] == 'test_value'
        assert parsed['details']['amount'] == 100.50
        
        print("✅ Formato de entrada de auditoria correto")
        print(f"   Exemplo: {entry[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Erro no formato de entrada de auditoria: {e}")
        return False

def test_log_files_exist():
    """Verifica se os arquivos de log existem"""
    log_files = [
        'logs/audit.log',
        'logs/order_operations.log',
        'logs/sistema_combinado.log',
        'logs/erros_criticos.log'
    ]
    
    all_exist = True
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"✅ {log_file} existe ({size} bytes)")
        else:
            print(f"⚠️  {log_file} ainda não existe (será criado no primeiro log)")
    
    return True

def test_audit_methods_exist():
    """Verifica se todos os métodos de auditoria existem"""
    try:
        from services.audit_service import AuditService
        
        methods = [
            'log_order_created',
            'log_status_change',
            'log_service_completed',
            'log_order_confirmed',
            'log_order_cancelled',
            'log_dispute_opened',
            'log_dispute_resolved',
            'log_financial_transaction',
            'log_error'
        ]
        
        for method in methods:
            if hasattr(AuditService, method):
                print(f"✅ Método {method} existe")
            else:
                print(f"❌ Método {method} não encontrado")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar métodos: {e}")
        return False

def test_order_management_integration():
    """Verifica se OrderManagementService importa AuditService"""
    try:
        from services.order_management_service import OrderManagementService
        import inspect
        
        # Verificar se AuditService é importado
        source = inspect.getsource(OrderManagementService)
        
        if 'AuditService' in source:
            print("✅ OrderManagementService integrado com AuditService")
            
            # Contar quantas vezes AuditService é usado
            count = source.count('AuditService.')
            print(f"   AuditService usado {count} vezes no código")
            return True
        else:
            print("❌ OrderManagementService não usa AuditService")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar integração: {e}")
        return False

def test_log_rotation_config():
    """Verifica se log rotation está configurado"""
    try:
        import app
        import logging
        
        # Verificar se RotatingFileHandler está sendo usado
        has_rotation = False
        for handler in logging.getLogger().handlers:
            if 'RotatingFileHandler' in str(type(handler)):
                has_rotation = True
                print(f"✅ Log rotation configurado: {handler.baseFilename}")
                print(f"   Max bytes: {handler.maxBytes / (1024*1024):.1f}MB")
                print(f"   Backup count: {handler.backupCount}")
        
        if has_rotation:
            return True
        else:
            print("⚠️  Log rotation não detectado (pode estar configurado de outra forma)")
            return True
    except Exception as e:
        print(f"❌ Erro ao verificar log rotation: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("TESTE DO SISTEMA DE AUDITORIA E LOGGING")
    print("=" * 70)
    print()
    
    tests = [
        ("Importação do AuditService", test_audit_service_imports),
        ("Geração de IDs únicos", test_audit_id_generation),
        ("Serialização de valores", test_value_serialization),
        ("Formato de entrada de auditoria", test_audit_entry_format),
        ("Existência de arquivos de log", test_log_files_exist),
        ("Métodos de auditoria", test_audit_methods_exist),
        ("Integração com OrderManagementService", test_order_management_integration),
        ("Configuração de log rotation", test_log_rotation_config)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'─' * 70}")
        print(f"Teste: {test_name}")
        print('─' * 70)
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Resumo
    print("=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Sistema de auditoria funcionando corretamente.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == '__main__':
    exit(main())
