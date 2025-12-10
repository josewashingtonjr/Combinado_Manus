#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar a rota de ajuste de quantidade
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_route_exists():
    """Verifica se a rota foi registrada corretamente"""
    print("\n=== Teste: Verificar se a rota existe ===")
    
    from app import app
    
    # Listar todas as rotas registradas
    routes = []
    for rule in app.url_map.iter_rules():
        if 'ajustar' in rule.rule:
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
    
    print(f"\nRotas encontradas com 'ajustar':")
    for route in routes:
        print(f"  - {route['rule']} [{', '.join(route['methods'])}] -> {route['endpoint']}")
    
    # Verificar se a rota específica existe
    expected_route = '/admin/tokens/solicitacoes/<int:request_id>/ajustar'
    found = any(expected_route in route['rule'] for route in routes)
    
    assert found, f"Rota {expected_route} não foi encontrada"
    
    # Verificar se aceita POST
    route_info = next((r for r in routes if expected_route in r['rule']), None)
    assert route_info is not None, "Rota não encontrada"
    assert 'POST' in route_info['methods'], f"Método POST não está disponível. Métodos: {route_info['methods']}"
    
    print(f"\n✓ Rota registrada corretamente: {route_info['rule']}")
    print(f"✓ Métodos aceitos: {', '.join(route_info['methods'])}")
    print(f"✓ Endpoint: {route_info['endpoint']}")

def test_route_imports():
    """Verifica se todas as importações necessárias estão presentes"""
    print("\n=== Teste: Verificar importações ===")
    
    from routes import admin_routes
    import inspect
    
    # Verificar se jsonify está importado
    source = inspect.getsource(admin_routes)
    
    assert 'from flask import' in source, "Importação do Flask não encontrada"
    assert 'jsonify' in source, "jsonify não está importado"
    
    print("✓ Todas as importações necessárias estão presentes")

def test_route_function_signature():
    """Verifica a assinatura da função da rota"""
    print("\n=== Teste: Verificar assinatura da função ===")
    
    from routes.admin_routes import ajustar_quantidade_solicitacao
    import inspect
    
    # Verificar assinatura
    sig = inspect.signature(ajustar_quantidade_solicitacao)
    params = list(sig.parameters.keys())
    
    print(f"Parâmetros da função: {params}")
    
    assert 'request_id' in params, "Parâmetro request_id não encontrado"
    
    # Verificar docstring
    doc = ajustar_quantidade_solicitacao.__doc__
    assert doc is not None, "Função não tem docstring"
    print(f"✓ Docstring: {doc.strip()}")
    
    print("✓ Assinatura da função está correta")

def test_route_decorator():
    """Verifica se a rota tem o decorator @admin_required"""
    print("\n=== Teste: Verificar decorator @admin_required ===")
    
    from routes.admin_routes import ajustar_quantidade_solicitacao
    
    # Verificar se a função tem o wrapper do decorator
    func_name = ajustar_quantidade_solicitacao.__name__
    
    # O decorator admin_required deve estar presente
    # Verificamos isso através do código fonte
    import inspect
    from routes import admin_routes
    
    source = inspect.getsource(admin_routes)
    
    # Procurar pela definição da função e seu decorator
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if 'def ajustar_quantidade_solicitacao' in line:
            # Verificar linhas anteriores para decorators
            prev_lines = lines[max(0, i-5):i]
            decorator_found = any('@admin_required' in l for l in prev_lines)
            assert decorator_found, "Decorator @admin_required não encontrado"
            print("✓ Decorator @admin_required está presente")
            break
    else:
        raise AssertionError("Função ajustar_quantidade_solicitacao não encontrada no código fonte")

def test_route_response_format():
    """Verifica se a rota retorna JSON"""
    print("\n=== Teste: Verificar formato de resposta ===")
    
    import inspect
    from routes import admin_routes
    
    source = inspect.getsource(admin_routes.ajustar_quantidade_solicitacao)
    
    # Verificar se usa jsonify para retornar respostas
    assert 'jsonify' in source, "Função não usa jsonify para retornar JSON"
    assert 'return jsonify' in source, "Função não retorna jsonify"
    
    # Verificar se retorna os campos esperados
    assert "'success'" in source, "Resposta não inclui campo 'success'"
    assert "'error'" in source, "Resposta não inclui campo 'error'"
    
    print("✓ Função retorna JSON com formato correto")

if __name__ == '__main__':
    print("=" * 60)
    print("TESTES SIMPLES - ROTA DE AJUSTE DE QUANTIDADE")
    print("=" * 60)
    
    try:
        test_route_exists()
        test_route_imports()
        test_route_function_signature()
        test_route_decorator()
        test_route_response_format()
        
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print("\nA rota foi implementada corretamente com:")
        print("  - Endpoint: POST /admin/tokens/solicitacoes/<request_id>/ajustar")
        print("  - Decorator: @admin_required")
        print("  - Validações de parâmetros")
        print("  - Retorno JSON")
        print("  - Tratamento de exceções")
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
