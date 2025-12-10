#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste básico para validar rotas de pré-ordem

Este teste verifica:
- Rotas foram registradas corretamente
- Endpoints estão acessíveis (com autenticação)
- Validações de permissão funcionam
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, PreOrder, PreOrderStatus, Invite
from datetime import datetime, timedelta
from decimal import Decimal


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
                    'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                    'path': rule.rule
                })
        
        print(f"✅ Total de rotas de pré-ordem registradas: {len(routes)}\n")
        
        # Rotas esperadas
        expected_routes = [
            'pre_ordem.ver_detalhes',
            'pre_ordem.propor_alteracao',
            'pre_ordem.aceitar_proposta',
            'pre_ordem.rejeitar_proposta',
            'pre_ordem.aceitar_termos',
            'pre_ordem.cancelar',
            'pre_ordem.consultar_historico',
            'pre_ordem.verificar_saldo',
            'pre_ordem.obter_status'
        ]
        
        registered_endpoints = [r['endpoint'] for r in routes]
        
        print("Rotas esperadas:")
        for expected in expected_routes:
            if expected in registered_endpoints:
                route = next(r for r in routes if r['endpoint'] == expected)
                print(f"  ✅ {expected}")
                print(f"     Métodos: {route['methods']}")
                print(f"     Path: {route['path']}")
            else:
                print(f"  ❌ {expected} - NÃO ENCONTRADA")
        
        # Verificar se todas as rotas esperadas foram registradas
        missing = set(expected_routes) - set(registered_endpoints)
        if missing:
            print(f"\n❌ Rotas faltando: {missing}")
            return False
        
        print("\n✅ Todas as rotas esperadas foram registradas!")
        return True


def test_route_access_without_auth():
    """Testa acesso às rotas sem autenticação"""
    print("\n=== Testando Acesso Sem Autenticação ===\n")
    
    with app.test_client() as client:
        # Tentar acessar rota sem autenticação
        response = client.get('/pre-ordem/1')
        
        # Deve redirecionar para login (302) ou retornar 401
        if response.status_code in [302, 401]:
            print(f"✅ Rota protegida corretamente (status: {response.status_code})")
            return True
        else:
            print(f"❌ Rota não está protegida (status: {response.status_code})")
            return False


def test_route_structure():
    """Testa estrutura das rotas"""
    print("\n=== Testando Estrutura das Rotas ===\n")
    
    with app.app_context():
        # Verificar prefixo das rotas
        pre_ordem_routes = [
            rule for rule in app.url_map.iter_rules()
            if 'pre_ordem' in rule.endpoint
        ]
        
        # Todas as rotas devem começar com /pre-ordem
        all_correct_prefix = all(
            rule.rule.startswith('/pre-ordem')
            for rule in pre_ordem_routes
        )
        
        if all_correct_prefix:
            print("✅ Todas as rotas têm o prefixo correto (/pre-ordem)")
        else:
            print("❌ Algumas rotas não têm o prefixo correto")
            return False
        
        # Verificar métodos HTTP
        method_checks = {
            'pre_ordem.ver_detalhes': ['GET'],
            'pre_ordem.propor_alteracao': ['POST'],
            'pre_ordem.aceitar_proposta': ['POST'],
            'pre_ordem.rejeitar_proposta': ['POST'],
            'pre_ordem.aceitar_termos': ['POST'],
            'pre_ordem.cancelar': ['POST'],
            'pre_ordem.consultar_historico': ['GET'],
            'pre_ordem.verificar_saldo': ['GET'],
            'pre_ordem.obter_status': ['GET']
        }
        
        print("\nVerificando métodos HTTP:")
        all_methods_correct = True
        for endpoint, expected_methods in method_checks.items():
            route = next(
                (r for r in pre_ordem_routes if r.endpoint == endpoint),
                None
            )
            if route:
                actual_methods = route.methods - {'HEAD', 'OPTIONS'}
                if set(expected_methods).issubset(actual_methods):
                    print(f"  ✅ {endpoint}: {expected_methods}")
                else:
                    print(f"  ❌ {endpoint}: esperado {expected_methods}, obtido {actual_methods}")
                    all_methods_correct = False
            else:
                print(f"  ❌ {endpoint}: rota não encontrada")
                all_methods_correct = False
        
        if all_methods_correct:
            print("\n✅ Todos os métodos HTTP estão corretos")
            return True
        else:
            print("\n❌ Alguns métodos HTTP estão incorretos")
            return False


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTE DE ROTAS DE PRÉ-ORDEM")
    print("=" * 60)
    
    results = []
    
    # Teste 1: Rotas registradas
    results.append(("Registro de Rotas", test_routes_registered()))
    
    # Teste 2: Acesso sem autenticação
    results.append(("Proteção de Autenticação", test_route_access_without_auth()))
    
    # Teste 3: Estrutura das rotas
    results.append(("Estrutura das Rotas", test_route_structure()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
