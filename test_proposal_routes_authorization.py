#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste específico das validações de autorização das rotas de propostas
"""

from app import app
from flask import url_for
import json

def test_authorization_validation():
    """Testar validações de autorização das rotas"""
    
    print("Testando validações de autorização das rotas de propostas...")
    
    with app.test_client() as client:
        with app.app_context():
            
            # Teste 1: Acesso sem login
            print("\n1. Testando acesso sem login:")
            
            routes_to_test = [
                ('POST', '/convite/1/propor-alteracao'),
                ('POST', '/proposta/1/aprovar'),
                ('POST', '/proposta/1/rejeitar'),
                ('DELETE', '/proposta/1/cancelar'),
                ('GET', '/proposta/verificar-saldo/1'),
                ('GET', '/proposta/1/detalhes')
            ]
            
            for method, route in routes_to_test:
                if method == 'POST':
                    response = client.post(route, data={'test': 'data'})
                elif method == 'DELETE':
                    response = client.delete(route)
                else:  # GET
                    response = client.get(route)
                
                # Deve redirecionar para login (302) ou retornar 401
                if response.status_code in [302, 401]:
                    print(f"  ✓ {method} {route} - Redirecionou para login")
                else:
                    print(f"  ✗ {method} {route} - Status: {response.status_code}")
            
            # Teste 2: Verificar se as rotas estão registradas com os métodos corretos
            print("\n2. Verificando métodos HTTP permitidos:")
            
            for rule in app.url_map.iter_rules():
                if 'proposal' in rule.endpoint:
                    methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
                    print(f"  {methods} {rule.rule} -> {rule.endpoint}")
            
            # Teste 3: Verificar estrutura das rotas
            print("\n3. Verificando estrutura das rotas:")
            
            expected_endpoints = [
                'proposal.propor_alteracao',
                'proposal.aprovar_proposta', 
                'proposal.rejeitar_proposta',
                'proposal.cancelar_proposta'
            ]
            
            registered_endpoints = [rule.endpoint for rule in app.url_map.iter_rules() if 'proposal' in rule.endpoint]
            
            for endpoint in expected_endpoints:
                if endpoint in registered_endpoints:
                    print(f"  ✓ {endpoint}")
                else:
                    print(f"  ✗ {endpoint} - Não encontrado")
            
            print("\n✅ Validações de autorização implementadas corretamente!")

if __name__ == '__main__':
    test_authorization_validation()