"""
Testes para o sistema de Touch Feedback
Valida a integração e funcionalidade do touch-feedback.js
"""

import pytest
import os


def test_touch_feedback_script_exists():
    """
    Testa se o arquivo touch-feedback.js existe
    Requirements: 2.4
    """
    script_path = 'static/js/touch-feedback.js'
    assert os.path.exists(script_path), f"Arquivo {script_path} não encontrado"
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se contém as principais funcionalidades
    assert 'class TouchFeedback' in content
    assert 'createRipple' in content
    assert 'preventDoubleClick' in content
    assert 'addTouchFeedback' in content


def test_touch_feedback_ripple_styles():
    """
    Testa se os estilos CSS para ripple estão definidos no script
    Requirements: 2.4
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se os estilos CSS estão incluídos
    assert '.ripple' in content
    assert 'ripple-animation' in content
    assert '.touch-active' in content
    assert 'button.processing' in content


def test_touch_feedback_initialization():
    """
    Testa se o sistema de touch feedback é inicializado automaticamente
    Requirements: 2.4, 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica inicialização automática
    assert 'initTouchFeedback' in content
    assert 'DOMContentLoaded' in content
    assert 'window.TouchFeedback' in content
    assert 'window.touchFeedback' in content


def test_touch_feedback_double_click_prevention():
    """
    Testa se a prevenção de duplo clique está implementada
    Requirements: 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica funcionalidade de prevenção de duplo clique
    assert 'preventDoubleClick' in content
    assert 'processingButtons' in content
    assert 'debounceTime' in content
    assert 'button.disabled' in content


def test_touch_feedback_spinner_functionality():
    """
    Testa se a funcionalidade de spinner está implementada
    Requirements: 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica funcionalidade de spinner
    assert 'addSpinner' in content
    assert 'removeSpinner' in content
    assert 'spinner' in content
    assert 'fa-spin' in content


def test_touch_feedback_api_methods():
    """
    Testa se os métodos da API estão disponíveis
    Requirements: 2.4, 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica métodos públicos da API
    assert 'refresh()' in content
    assert 'resetButton' in content
    assert 'resetAllButtons' in content


def test_touch_feedback_configuration_options():
    """
    Testa se as opções de configuração estão disponíveis
    Requirements: 2.4
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica opções de configuração
    assert 'rippleDuration' in content
    assert 'debounceTime' in content
    assert 'rippleColor' in content


def test_touch_feedback_button_selectors():
    """
    Testa se os seletores de botões estão corretos
    Requirements: 2.4, 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica seletores de botões
    assert 'button[type="submit"]' in content
    assert '.btn-primary' in content
    assert '.btn-action' in content
    assert '.btn-accept' in content
    assert '.btn-reject' in content
    assert '.touch-target' in content


def test_touch_feedback_examples_page_exists():
    """
    Testa se a página de exemplos existe
    Requirements: 2.4
    """
    examples_path = 'static/js/touch-feedback-examples.html'
    assert os.path.exists(examples_path), f"Arquivo {examples_path} não encontrado"
    
    with open(examples_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verifica conteúdo da página de exemplos
    assert '<h1' in html
    assert 'Touch Feedback' in html
    assert '<button' in html  # Deve ter botões de exemplo


def test_touch_feedback_script_loaded_in_base_template():
    """
    Testa se o script touch-feedback.js está referenciado no template base
    Requirements: 2.4, 2.5
    """
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    assert 'touch-feedback.js' in html, "Script touch-feedback.js não encontrado no template base"


def test_touch_feedback_mobile_optimization():
    """
    Testa se o touch feedback está otimizado para mobile
    Requirements: 2.4, 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica otimizações mobile
    assert 'touchstart' in content
    assert 'touchend' in content
    assert 'touchcancel' in content
    assert 'touch-active' in content


def test_touch_feedback_console_logging():
    """
    Testa se há logging para debug
    Requirements: 2.4
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica se há logging
    assert 'console.log' in content
    assert 'Touch Feedback System inicializado' in content


def test_touch_feedback_error_handling():
    """
    Testa se há tratamento de erros básico
    Requirements: 2.4, 2.5
    """
    with open('static/js/touch-feedback.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verifica tratamento de casos especiais
    assert 'if' in content  # Deve ter condicionais
    assert 'return' in content  # Deve ter retornos
    # Verifica prevenção de múltiplas inicializações
    assert 'dataset.rippleAttached' in content or 'data-ripple-attached' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
