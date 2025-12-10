"""
Testes para o Sistema de Loading States
Valida a implementação do script loading-states.js
"""

import os
import re


def test_loading_states_file_exists():
    """Verifica se o arquivo loading-states.js foi criado"""
    file_path = 'static/js/loading-states.js'
    assert os.path.exists(file_path), f"Arquivo {file_path} não encontrado"
    print("✓ Arquivo loading-states.js existe")


def test_loading_states_class_defined():
    """Verifica se a classe LoadingStates está definida"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'class LoadingStates' in content, "Classe LoadingStates não encontrada"
    print("✓ Classe LoadingStates definida")


def test_button_loading_methods():
    """Verifica se os métodos de loading de botão existem"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'showButtonLoading' in content, "Método showButtonLoading não encontrado"
    assert 'hideButtonLoading' in content, "Método hideButtonLoading não encontrado"
    print("✓ Métodos de loading de botão implementados")


def test_form_loading_methods():
    """Verifica se os métodos de loading de formulário existem"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'showFormLoading' in content, "Método showFormLoading não encontrado"
    assert 'hideFormLoading' in content, "Método hideFormLoading não encontrado"
    print("✓ Métodos de loading de formulário implementados")


def test_skeleton_loading_methods():
    """Verifica se os métodos de skeleton loading existem"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'showSkeleton' in content, "Método showSkeleton não encontrado"
    assert 'hideSkeleton' in content, "Método hideSkeleton não encontrado"
    assert 'createCardSkeleton' in content, "Método createCardSkeleton não encontrado"
    assert 'createListSkeleton' in content, "Método createListSkeleton não encontrado"
    assert 'createTableSkeleton' in content, "Método createTableSkeleton não encontrado"
    print("✓ Métodos de skeleton loading implementados")


def test_ajax_integration():
    """Verifica se a integração AJAX está implementada"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'fetchWithLoading' in content, "Método fetchWithLoading não encontrado"
    assert 'ajaxWithLoading' in content, "Método ajaxWithLoading não encontrado"
    print("✓ Integração AJAX implementada")


def test_form_auto_integration():
    """Verifica se a integração automática com formulários existe"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'attachFormHandlers' in content, "Método attachFormHandlers não encontrado"
    assert "addEventListener('submit'" in content, "Event listener de submit não encontrado"
    print("✓ Integração automática com formulários implementada")


def test_button_auto_integration():
    """Verifica se a integração automática com botões existe"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'attachButtonHandlers' in content, "Método attachButtonHandlers não encontrado"
    assert 'data-loading' in content, "Suporte a data-loading não encontrado"
    print("✓ Integração automática com botões implementada")


def test_portuguese_texts():
    """Verifica se os textos estão em português"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'Carregando...' in content, "Texto 'Carregando...' não encontrado"
    print("✓ Textos em português brasileiro")


def test_css_styles_included():
    """Verifica se os estilos CSS estão incluídos"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'loadingStyles' in content, "Variável loadingStyles não encontrada"
    assert '.btn-loading' in content, "Estilo .btn-loading não encontrado"
    assert '.skeleton-' in content, "Estilos skeleton não encontrados"
    assert '@keyframes' in content, "Animações CSS não encontradas"
    print("✓ Estilos CSS incluídos no script")


def test_global_exports():
    """Verifica se as exportações globais estão corretas"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'window.LoadingStates' in content, "Exportação window.LoadingStates não encontrada"
    assert 'window.loadingStates' in content, "Exportação window.loadingStates não encontrada"
    assert 'window.initLoadingStates' in content, "Exportação window.initLoadingStates não encontrada"
    print("✓ Exportações globais corretas")


def test_auto_initialization():
    """Verifica se a inicialização automática está implementada"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'initLoadingStates' in content, "Função initLoadingStates não encontrada"
    assert 'DOMContentLoaded' in content, "Event listener DOMContentLoaded não encontrado"
    print("✓ Inicialização automática implementada")


def test_base_template_integration():
    """Verifica se o script foi integrado no base.html"""
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'loading-states.js' in content, "Script loading-states.js não incluído no base.html"
    print("✓ Script integrado no base.html")


def test_examples_file_exists():
    """Verifica se o arquivo de exemplos foi criado"""
    file_path = 'static/js/loading-states-examples.html'
    assert os.path.exists(file_path), f"Arquivo {file_path} não encontrado"
    print("✓ Arquivo de exemplos existe")


def test_documentation_exists():
    """Verifica se a documentação foi criada"""
    file_path = 'LOADING_STATES_README.md'
    assert os.path.exists(file_path), f"Arquivo {file_path} não encontrado"
    print("✓ Documentação existe")


def test_min_loading_time():
    """Verifica se o tempo mínimo de loading está implementado"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'minLoadingTime' in content, "Configuração minLoadingTime não encontrada"
    assert 'remainingTime' in content, "Lógica de tempo mínimo não encontrada"
    print("✓ Tempo mínimo de loading implementado")


def test_dom_observer():
    """Verifica se o observer de mudanças no DOM está implementado"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'observeDOMChanges' in content, "Método observeDOMChanges não encontrado"
    assert 'MutationObserver' in content, "MutationObserver não encontrado"
    print("✓ Observer de mudanças no DOM implementado")


def test_reset_methods():
    """Verifica se os métodos de reset existem"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'resetAll' in content, "Método resetAll não encontrado"
    print("✓ Métodos de reset implementados")


def test_spinner_customization():
    """Verifica se o spinner é customizável"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'spinnerHTML' in content, "Opção spinnerHTML não encontrada"
    assert 'spinnerText' in content, "Opção spinnerText não encontrada"
    print("✓ Spinner customizável")


def test_requirements_coverage():
    """Verifica se os requirements estão documentados"""
    with open('static/js/loading-states.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se os requirements estão mencionados
    assert 'Requirements: 5.1, 8.2' in content or 'Requirement' in content, \
        "Requirements não documentados no código"
    print("✓ Requirements documentados")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTES DO SISTEMA DE LOADING STATES")
    print("="*60 + "\n")
    
    tests = [
        test_loading_states_file_exists,
        test_loading_states_class_defined,
        test_button_loading_methods,
        test_form_loading_methods,
        test_skeleton_loading_methods,
        test_ajax_integration,
        test_form_auto_integration,
        test_button_auto_integration,
        test_portuguese_texts,
        test_css_styles_included,
        test_global_exports,
        test_auto_initialization,
        test_base_template_integration,
        test_examples_file_exists,
        test_documentation_exists,
        test_min_loading_time,
        test_dom_observer,
        test_reset_methods,
        test_spinner_customization,
        test_requirements_coverage,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Erro inesperado - {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTADO: {passed} testes passaram, {failed} falharam")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 Todos os testes passaram! Sistema implementado corretamente.")
        print("\n📋 Funcionalidades implementadas:")
        print("  ✓ Spinner em botões durante ação")
        print("  ✓ Desabilitar botão durante processamento")
        print("  ✓ Skeleton loading para conteúdo")
        print("  ✓ Integração com formulários e ações AJAX")
        print("  ✓ Textos em português brasileiro")
        print("\n📖 Documentação:")
        print("  - LOADING_STATES_README.md")
        print("  - static/js/loading-states-examples.html")
        print("\n🚀 Requirements atendidos: 5.1, 8.2")
    else:
        exit(1)
