#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script de Validação da Migração Monetária
Executa validação completa da migração Float → Numeric(18,2)
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.monetary_migration_service import MonetaryMigrationService
import json

def main():
    """Função principal para validação da migração"""
    print("=" * 80)
    print("VALIDAÇÃO DA MIGRAÇÃO MONETÁRIA")
    print("Sistema de Correções Críticas - Tarefa 1")
    print("=" * 80)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Usar aplicação Flask já configurada
    
    with app.app_context():
        try:
            # 1. Validar integridade dos dados
            print("1. VALIDANDO INTEGRIDADE DOS DADOS...")
            print("-" * 50)
            
            validation_result = MonetaryMigrationService.validate_migration_integrity()
            
            if validation_result['success']:
                print("✅ Validação de integridade: SUCESSO")
                
                summary = validation_result['summary']
                print(f"   • Total de tabelas: {summary['total_tables']}")
                print(f"   • Tabelas válidas: {summary['valid_tables']}")
                print(f"   • Total de registros: {summary['total_records']}")
                print(f"   • Registros inválidos: {summary['total_invalid_records']}")
                
                if summary['all_valid']:
                    print("   • Status: TODOS OS DADOS ESTÃO VÁLIDOS ✅")
                else:
                    print("   • Status: ENCONTRADOS DADOS INVÁLIDOS ❌")
                    print(f"   • Tabelas com erros: {', '.join(summary['tables_with_errors'])}")
                
            else:
                print("❌ Validação de integridade: FALHOU")
                if 'error' in validation_result:
                    print(f"   • Erro: {validation_result['error']}")
            
            print()
            
            # 2. Verificar constraints do banco
            print("2. VERIFICANDO CONSTRAINTS DO BANCO...")
            print("-" * 50)
            
            constraints_result = MonetaryMigrationService.check_database_constraints()
            
            if constraints_result['success']:
                print("✅ Verificação de constraints: SUCESSO")
                
                if constraints_result['all_constraints_active']:
                    print("   • Status: TODAS AS CONSTRAINTS ESTÃO ATIVAS ✅")
                else:
                    print("   • Status: ALGUMAS CONSTRAINTS NÃO ESTÃO ATIVAS ❌")
                
                for test in constraints_result['tests']:
                    status = "✅" if test['passed'] else "❌"
                    print(f"   • {test['test']}: {status} {test['message']}")
                    
            else:
                print("❌ Verificação de constraints: FALHOU")
                if 'error' in constraints_result:
                    print(f"   • Erro: {constraints_result['error']}")
            
            print()
            
            # 3. Gerar relatório detalhado se houver problemas
            if not validation_result.get('success', False) or \
               not validation_result.get('summary', {}).get('all_valid', False) or \
               not constraints_result.get('all_constraints_active', False):
                
                print("3. RELATÓRIO DETALHADO DE PROBLEMAS...")
                print("-" * 50)
                
                # Salvar relatório detalhado
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'validation_result': validation_result,
                    'constraints_result': constraints_result
                }
                
                report_filename = f"migration_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(report_filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"   • Relatório detalhado salvo em: {report_filename}")
                
                # Mostrar problemas específicos
                if 'results' in validation_result:
                    for table, result in validation_result['results'].items():
                        if not result.get('valid', False) and 'invalid_records' in result:
                            print(f"   • Problemas na tabela {table}:")
                            for record in result['invalid_records'][:5]:  # Mostrar apenas os primeiros 5
                                print(f"     - ID {record.get('id', 'N/A')}: {', '.join(record.get('errors', []))}")
                            
                            if len(result['invalid_records']) > 5:
                                print(f"     - ... e mais {len(result['invalid_records']) - 5} registros")
            
            else:
                print("3. RESULTADO FINAL...")
                print("-" * 50)
                print("✅ MIGRAÇÃO VALIDADA COM SUCESSO!")
                print("   • Todos os dados estão íntegros")
                print("   • Todas as constraints estão ativas")
                print("   • Sistema pronto para operação")
            
            print()
            print("=" * 80)
            print(f"Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ ERRO DURANTE VALIDAÇÃO: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

def show_migration_scripts():
    """Mostra os scripts de migração disponíveis"""
    print("=" * 80)
    print("SCRIPTS DE MIGRAÇÃO DISPONÍVEIS")
    print("=" * 80)
    
    scripts = MonetaryMigrationService.generate_migration_script()
    
    print("1. SCRIPT POSTGRESQL:")
    print("-" * 50)
    print(scripts['postgresql'])
    print()
    
    print("2. SCRIPT SQLITE:")
    print("-" * 50)
    print(scripts['sqlite'])
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show-scripts":
        show_migration_scripts()
    else:
        exit_code = main()
        sys.exit(exit_code)