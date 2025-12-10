#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar a estrutura do template da dashboard do cliente
Tarefa 8: Atualizar template da dashboard do cliente
"""

def test_template_has_open_orders_section():
    """Verifica se o template tem a seção de ordens em aberto"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar seção de ordens em aberto
    assert 'Ordens em Aberto' in content
    assert 'ordens_em_aberto' in content
    assert 'Ver Detalhes' in content
    assert 'não tem ordens em aberto no momento' in content
    print("✓ Seção de ordens em aberto encontrada")


def test_template_has_blocked_funds_section():
    """Verifica se o template tem a seção de fundos bloqueados"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar seção de fundos bloqueados
    assert 'Fundos em Garantia' in content
    assert 'saldo_bloqueado' in content
    assert 'Bloqueado em Garantia' in content
    assert 'Detalhamento por Ordem' in content
    assert 'fundos_bloqueados_detalhados' in content
    print("✓ Seção de fundos bloqueados encontrada")


def test_template_has_updated_statistics_cards():
    """Verifica se os cards de estatísticas foram atualizados"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar cards atualizados
    assert 'Saldo Disponível' in content
    assert 'Ordens em Aberto' in content
    assert 'Saldo Total' in content
    assert 'ordens_por_status' in content
    assert 'bloqueado' in content
    print("✓ Cards de estatísticas atualizados")


def test_template_has_proper_table_structure():
    """Verifica se a tabela de ordens tem a estrutura correta"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar estrutura da tabela
    assert '<table class="table table-hover">' in content
    assert '<th>ID</th>' in content
    assert '<th>Título</th>' in content
    assert '<th>Prestador</th>' in content
    assert '<th>Status</th>' in content
    assert '<th>Valor</th>' in content
    assert '<th>Data de Criação</th>' in content
    assert '<th>Ações</th>' in content
    print("✓ Estrutura da tabela correta")


def test_template_has_blocked_funds_table():
    """Verifica se a tabela de fundos bloqueados existe"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar tabela de fundos bloqueados
    assert 'Detalhamento por Ordem' in content
    assert 'Valor Bloqueado' in content
    assert 'Total Bloqueado' in content
    print("✓ Tabela de fundos bloqueados encontrada")


def test_template_has_proper_formatting():
    """Verifica se o template tem formatação adequada"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar formatação de valores
    assert 'R$ {{ "%.2f"|format(' in content
    assert 'badge bg-' in content
    assert 'btn btn-sm btn-outline-primary' in content
    print("✓ Formatação adequada")


def test_template_has_empty_state_messages():
    """Verifica se o template tem mensagens de estado vazio"""
    with open('templates/cliente/dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar mensagens de estado vazio
    assert 'não tem ordens em aberto no momento' in content
    assert 'Criar Novo Convite' in content
    print("✓ Mensagens de estado vazio encontradas")


if __name__ == '__main__':
    print("\nTestando estrutura do template da dashboard do cliente...")
    print("=" * 60)
    
    try:
        test_template_has_open_orders_section()
        test_template_has_blocked_funds_section()
        test_template_has_updated_statistics_cards()
        test_template_has_proper_table_structure()
        test_template_has_blocked_funds_table()
        test_template_has_proper_formatting()
        test_template_has_empty_state_messages()
        
        print("=" * 60)
        print("\n✅ Todos os testes passaram! Template atualizado corretamente.")
    except AssertionError as e:
        print(f"\n❌ Teste falhou: {e}")
        exit(1)
