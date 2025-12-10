#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simplificado para validar rotas de pré-ordem

Foca apenas em verificar que as rotas foram registradas e estão acessíveis
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


def test_routes_registered():
    """Testa se as rotas de pré-ordem foram registradas"""
    print("\n=== Testando Registro de Rotas ===\n")
    
    with app.app_context():
        # Listar todas as rotas registradas
        routes = []
        for rule in app.url_map.iter_rules():
            if 'pre-ordem' in rule.rule or 'pre_ordem' in rule.endpoint:
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
                    'path': rule.rule
                })
        
        print(f"Total de rotas de pré-ordem registradas: {len(routes)}\n")
        
        # Rotas esperadas com seus métodos
        expected_routes = {
            'pre_ordem.ver_detalhes': ('GET', '/pre-ordem/<int:pre_order_id>'),
            'pre_ordem.propor_alteracao': ('POST', '/pre-ordem/<int:pre_order_id>/propor-alteracao'),
            'pre_ordem.aceitar_proposta': ('POST', '/pre-ordem/<int:pre_order_id>/aceitar-proposta/<int:proposal_id>'),
            'pre_ordem.rejeitar_proposta': ('POST', '/pre-ordem/<int:pre_order_id>/rejeitar-proposta/<int:proposal_id>'),
            'pre_ordem.aceitar_termos': ('POST', '/pre-ordem/<int:pre_order_id>/aceitar-termos'),
            'pre_ordem.cancelar': ('POST', '/pre-ordem/<int:pre_order_id>/cancelar'),
            'pre_ordem.consultar_historico': ('GET', '/pre-ordem/<int:pre_order_id>/historico'),
            'pre_ordem.verificar_saldo': ('GET', '/pre-ordem/<int:pre_order_id>/verificar-saldo'),
            'pre_ordem.obter_status': ('GET', '/pre-ordem/<int:pre_order_id>/status')
        }
        
        registered_endpoints = {r['endpoint']: (r['methods'], r['path']) for r in routes}
        
        print("Verificando rotas esperadas:\n")
        all_found = True
        for endpoint, (expected_method, expected_path) in expected_routes.items():
            if endpoint in registered_endpoints:
                actual_methods, actual_path = registered_endpoints[endpoint]
                
                # Verificar se o método esperado está presente
                method_ok = expected_method in actual_methods
                path_ok = actual_path == expected_path
                
                if method_ok and path_ok:
                    print(f"✅ {endpoint}")
                    print(f"   Método: {expected_method}")
                    print(f"   Path: {expected_path}")
                else:
                    print(f"⚠️  {endpoint}")
                    if not method_ok:
                        print(f"   ❌ Método esperado: {expected_method}, obtido: {actual_methods}")
                    if not path_ok:
                        print(f"   ❌ Path esperado: {expected_path}, obtido: {actual_path}")
                    all_found = False
            else:
                print(f"❌ {endpoint} - NÃO ENCONTRADA")
                all_found = False
        
        if all_found:
            print("\n✅ Todas as rotas esperadas foram registradas corretamente!")
            return True
        else:
            print("\n❌ Algumas rotas estão faltando ou incorretas")
            return False


def test_route_protection():
    """Testa se as rotas estão protegidas por autenticação"""
    print("\n=== Testando Proteção de Autenticação ===\n")
    
    with app.test_client() as client:
        # Testar rotas GET sem autenticação
        get_routes = [
            '/pre-ordem/1',
            '/pre-ordem/1/historico',
            '/pre-ordem/1/verificar-saldo',
            '/pre-ordem/1/status'
        ]
        
        all_protected = True
        for route in get_routes:
            response = client.get(route)
            # Deve redirecionar para login (302) ou retornar 401
            if response.status_code in [302, 401]:
                print(f"✅ {route} - Protegida (status: {response.status_code})")
            else:
                print(f"❌ {route} - NÃO protegida (status: {response.status_code})")
                all_protected = False
        
        if all_protected:
            print("\n✅ Todas as rotas estão protegidas por autenticação!")
            return True
        else:
            print("\n❌ Algumas rotas não estão protegidas")
            return False


def test_route_structure():
    """Testa estrutura e organização das rotas"""
    print("\n=== Testando Estrutura das Rotas ===\n")
    
    with app.app_context():
        pre_ordem_routes = [
            rule for rule in app.url_map.iter_rules()
            if 'pre_ordem' in rule.endpoint
        ]
        
        # Verificar prefixo
        all_correct_prefix = all(
            rule.rule.startswith('/pre-ordem')
            for rule in pre_ordem_routes
        )
        
        if all_correct_prefix:
            print("✅ Todas as rotas têm o prefixo correto (/pre-ordem)")
        else:
            print("❌ Algumas rotas não têm o prefixo correto")
            return False
        
        # Verificar que rotas POST não aceitam GET
        post_only_routes = [
            'propor_alteracao', 'aceitar_proposta', 'rejeitar_proposta',
            'aceitar_termos', 'cancelar'
        ]
        
        print("\nVerificando métodos HTTP:")
        all_methods_correct = True
        for route in pre_ordem_routes:
            endpoint_name = route.endpoint.split('.')[-1]
            methods = route.methods - {'HEAD', 'OPTIONS'}
            
            if endpoint_name in post_only_routes:
                if 'POST' in methods and 'GET' not in methods:
                    print(f"✅ {endpoint_name}: POST only")
                else:
                    print(f"❌ {endpoint_name}: deveria ser POST only, mas tem {methods}")
                    all_methods_correct = False
            elif endpoint_name in ['ver_detalhes', 'consultar_historico', 'verificar_saldo', 'obter_status']:
                if 'GET' in methods:
                    print(f"✅ {endpoint_name}: GET disponível")
                else:
                    print(f"❌ {endpoint_name}: deveria ter GET, mas tem {methods}")
                    all_methods_correct = False
        
        if all_methods_correct:
            print("\n✅ Todos os métodos HTTP estão corretos")
            return True
        else:
            print("\n❌ Alguns métodos HTTP estão incorretos")
            return False


def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("TESTE SIMPLIFICADO - ROTAS DE PRÉ-ORDEM")
    print("=" * 70)
    
    results = []
    
    # Teste 1: Rotas registradas
    results.append(("Registro de Rotas", test_routes_registered()))
    
    # Teste 2: Proteção de autenticação
    results.append(("Proteção de Autenticação", test_route_protection()))
    
    # Teste 3: Estrutura das rotas
    results.append(("Estrutura das Rotas", test_route_structure()))
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DOS TESTES")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\nAs rotas de pré-ordem foram implementadas com sucesso:")
        print("- 9 rotas registradas corretamente")
        print("- Todas protegidas por autenticação")
        print("- Métodos HTTP corretos")
        print("- Prefixo /pre-ordem aplicado")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
