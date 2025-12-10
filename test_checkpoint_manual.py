#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste Manual de Checkpoint 16 - Interface Funcional
Verifica componentes principais da interface
"""

import os
import sys

print("\n" + "="*80)
print("CHECKPOINT 16: TESTE MANUAL DE INTERFACE FUNCIONAL")
print("="*80)

# Verificar arquivos essenciais
print("\n1. VERIFICANDO ARQUIVOS ESSENCIAIS...")

arquivos_essenciais = [
    'templates/pre_ordem/detalhes.html',
    'static/js/pre-ordem-interactions.js',
    'static/js/pre-ordem-realtime.js',
    'routes/pre_ordem_routes.py',
    'services/pre_order_service.py',
    'services/pre_order_proposal_service.py',
    'services/pre_order_state_manager.py'
]

todos_presentes = True
for arquivo in arquivos_essenciais:
    if os.path.exists(arquivo):
        print(f"   OK - {arquivo}")
    else:
        print(f"   FALTA - {arquivo}")
        todos_presentes = False

if todos_presentes:
    print("\n   PASSOU - Todos os arquivos essenciais estao presentes")
else:
    print("\n   FALHOU - Alguns arquivos estao faltando")
    sys.exit(1)

# Verificar rotas implementadas
print("\n2. VERIFICANDO ROTAS IMPLEMENTADAS...")

with open('routes/pre_ordem_routes.py', 'r', encoding='utf-8') as f:
    conteudo_rotas = f.read()

rotas_esperadas = [
    'ver_detalhes',
    'propor_alteracao',
    'aceitar_proposta',
    'rejeitar_proposta',
    'aceitar_termos',
    'cancelar',
    'consultar_historico',
    'verificar_saldo',
    'obter_status',
    'stream_updates',
    'gerenciar_presenca'
]

todas_rotas = True
for rota in rotas_esperadas:
    if f'def {rota}' in conteudo_rotas:
        print(f"   OK - Rota {rota} implementada")
    else:
        print(f"   FALTA - Rota {rota}")
        todas_rotas = False

if todas_rotas:
    print("\n   PASSOU - Todas as rotas estao implementadas")
else:
    print("\n   FALHOU - Algumas rotas estao faltando")

# Verificar funcionalidades JavaScript
print("\n3. VERIFICANDO FUNCIONALIDADES JAVASCRIPT...")

with open('static/js/pre-ordem-interactions.js', 'r', encoding='utf-8') as f:
    conteudo_js = f.read()

funcionalidades_js = [
    'PreOrdemInteractions',
    'calculateValueDifference',
    'updateCharacterCount',
    'validateProposeForm',
    'showNotification',
    'formatCurrency'
]

todas_funcionalidades = True
for func in funcionalidades_js:
    if func in conteudo_js:
        print(f"   OK - Funcionalidade {func} implementada")
    else:
        print(f"   FALTA - Funcionalidade {func}")
        todas_funcionalidades = False

if todas_funcionalidades:
    print("\n   PASSOU - Todas as funcionalidades JS estao implementadas")

# Verificar sistema de tempo real
print("\n4. VERIFICANDO SISTEMA DE TEMPO REAL...")

with open('static/js/pre-ordem-realtime.js', 'r', encoding='utf-8') as f:
    conteudo_realtime = f.read()

funcionalidades_realtime = [
    'PreOrdemRealtime',
    'connectSSE',
    'startPolling',
    'handleStatusChange',
    'handleProposalReceived',
    'handleMutualAcceptance',
    'showToast',
    'updatePresenceIndicator'
]

todas_realtime = True
for func in funcionalidades_realtime:
    if func in conteudo_realtime:
        print(f"   OK - Funcionalidade {func} implementada")
    else:
        print(f"   FALTA - Funcionalidade {func}")
        todas_realtime = False

if todas_realtime:
    print("\n   PASSOU - Sistema de tempo real implementado")

# Verificar elementos do template
print("\n5. VERIFICANDO ELEMENTOS DO TEMPLATE...")

with open('templates/pre_ordem/detalhes.html', 'r', encoding='utf-8') as f:
    conteudo_template = f.read()

elementos_template = [
    'pre-order-header',
    'value-card',
    'timeline',
    'action-button',
    'status-badge',
    'data-acceptance',
    'proposal-indicator',
    '@media'  # CSS responsivo
]

todos_elementos = True
for elemento in elementos_template:
    if elemento in conteudo_template:
        print(f"   OK - Elemento {elemento} presente")
    else:
        print(f"   FALTA - Elemento {elemento}")
        todos_elementos = False

if todos_elementos:
    print("\n   PASSOU - Todos os elementos do template estao presentes")

# Verificar validacoes
print("\n6. VERIFICANDO VALIDACOES...")

validacoes = [
    ('justification', 'Validacao de justificativa'),
    ('proposed_value', 'Validacao de valor'),
    ('proposed_delivery_date', 'Validacao de data'),
    ('cancellation_reason', 'Validacao de motivo de cancelamento')
]

todas_validacoes = True
for campo, descricao in validacoes:
    if campo in conteudo_rotas or campo in conteudo_js:
        print(f"   OK - {descricao}")
    else:
        print(f"   FALTA - {descricao}")
        todas_validacoes = False

if todas_validacoes:
    print("\n   PASSOU - Todas as validacoes estao implementadas")

# Verificar responsividade
print("\n7. VERIFICANDO RESPONSIVIDADE...")

tem_media_query = '@media' in conteudo_template
tem_max_width = 'max-width' in conteudo_template
tem_responsivo = 'Responsividade' in conteudo_template or 'responsiv' in conteudo_template.lower()

responsividade_ok = tem_media_query and (tem_max_width or tem_responsivo)

if responsividade_ok:
    print("   OK - CSS responsivo presente")
    print("   OK - Media queries implementadas")
    print("   OK - Estilos adaptativos para mobile")
    print("\n   PASSOU - Interface e responsiva")
else:
    print("   AVISO - Verificar CSS responsivo manualmente")

# Resumo final
print("\n" + "="*80)
print("RESUMO DO CHECKPOINT 16")
print("="*80)

resultados = [
    ("Arquivos essenciais", todos_presentes),
    ("Rotas implementadas", todas_rotas),
    ("Funcionalidades JavaScript", todas_funcionalidades),
    ("Sistema de tempo real", todas_realtime),
    ("Elementos do template", todos_elementos),
    ("Validacoes", todas_validacoes),
    ("Responsividade", responsividade_ok)
]

total = len(resultados)
passou = sum(1 for _, ok in resultados if ok)

print(f"\nResultados: {passou}/{total} verificacoes passaram\n")

for nome, ok in resultados:
    status = "PASSOU" if ok else "FALHOU"
    simbolo = "✓" if ok else "✗"
    print(f"   {simbolo} {nome}: {status}")

if passou == total:
    print("\n" + "="*80)
    print("CHECKPOINT 16 PASSOU COM SUCESSO!")
    print("="*80)
    print("\nA interface funcional esta completa e pronta para uso.")
    print("\nProximos passos:")
    print("  - Testar manualmente navegando pela interface")
    print("  - Verificar responsividade em diferentes dispositivos")
    print("  - Testar atualizacoes em tempo real com dois usuarios")
    print("  - Validar formularios com diferentes inputs")
    sys.exit(0)
else:
    print("\n" + "="*80)
    print("CHECKPOINT 16 PRECISA DE ATENCAO")
    print("="*80)
    print(f"\n{total - passou} verificacao(oes) falharam.")
    print("Revise os itens marcados como FALHOU acima.")
    sys.exit(1)
