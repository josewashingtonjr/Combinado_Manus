#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para validar filtros de status no menu de Ordens (Tarefa 6)
Foco: Validação de código e estrutura, não autenticação
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_route_code_validation():
    """Testa se o código da rota tem validação de status"""
    with open('routes/admin_routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se a validação de status está presente
    assert 'valid_statuses' in content, "Validação de status não encontrada"
    assert 'aguardando_execucao' in content, "Status 'aguardando_execucao' não encontrado"
    assert 'servico_executado' in content, "Status 'servico_executado' não encontrado"
    assert 'concluida' in content, "Status 'concluida' não encontrado"
    assert 'cancelada' in content, "Status 'cancelada' não encontrado"
    assert 'contestada' in content, "Status 'contestada' não encontrado"
    assert 'resolvida' in content, "Status 'resolvida' não encontrado"
    
    print("✅ Código da rota contém validação de todos os status")


def test_route_has_flash_message():
    """Testa se a rota tem mensagem flash para status inválido"""
    with open('routes/admin_routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há mensagem flash para status inválido
    assert 'flash' in content and 'Status inválido' in content, "Mensagem flash não encontrada"
    print("✅ Rota contém mensagem flash para status inválido")


def test_menu_ordens_structure():
    """Testa se o menu de Ordens tem todos os filtros"""
    with open('templates/admin/base_admin.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar se todos os filtros estão presentes no menu
    expected_filters = [
        ('Todas', 'admin.ordens'),
        ('Aguardando', 'status=aguardando_execucao'),
        ('Executadas', 'status=servico_executado'),
        ('Concluídas', 'status=concluida'),
        ('Canceladas', 'status=cancelada'),
        ('Contestadas', 'status=contestada'),
        ('Resolvidas', 'status=resolvida')
    ]
    
    for filter_name, filter_param in expected_filters:
        assert filter_name in html, f"Filtro '{filter_name}' não encontrado no menu"
        assert filter_param in html, f"Parâmetro '{filter_param}' não encontrado no menu"
        print(f"✅ Filtro '{filter_name}' presente no menu com parâmetro correto")


def test_no_duplicate_menu_items():
    """Testa se não há itens duplicados no menu de Ordens"""
    with open('templates/admin/base_admin.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar se menuOrdens aparece apenas uma vez
    count = html.count('id="menuOrdens"')
    assert count == 1, f"Menu de Ordens aparece {count} vezes (esperado: 1)"
    print(f"✅ Menu de Ordens não está duplicado (aparece {count} vez)")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTE DE VALIDAÇÃO - TAREFA 6: OTIMIZAR MENU DE ORDENS")
    print("="*60 + "\n")
    
    try:
        print("Teste 1: Validar código da rota")
        test_route_code_validation()
        print()
        
        print("Teste 2: Validar mensagem flash")
        test_route_has_flash_message()
        print()
        
        print("Teste 3: Verificar estrutura do menu")
        test_menu_ordens_structure()
        print()
        
        print("Teste 4: Verificar ausência de duplicações")
        test_no_duplicate_menu_items()
        print()
        
        print("="*60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {str(e)}")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
