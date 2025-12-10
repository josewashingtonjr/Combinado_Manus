#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste rápido para verificar se as rotas estão registradas
"""

from app import app

print("\n" + "="*70)
print("VERIFICANDO ROTAS REGISTRADAS")
print("="*70)

# Listar todas as rotas relacionadas a configurações de taxas
print("\nRotas de configuração de taxas:")
for rule in app.url_map.iter_rules():
    if 'taxas' in rule.rule or 'configuracoes' in rule.rule:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {rule.rule:50s} [{methods}]")

print("\n" + "="*70)
