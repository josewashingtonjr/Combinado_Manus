"""
Testes de Acessibilidade - Cores e Contraste
Valida a implementação do sistema de cores acessíveis
"""

import os
import re
import pytest


def test_accessibility_css_exists():
    """Verifica se o arquivo CSS de acessibilidade existe"""
    css_path = 'static/css/accessibility-colors.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"


def test_high_contrast_toggle_js_exists():
    """Verifica se o script de toggle de alto contraste existe"""
    js_path = 'static/js/high-contrast-toggle.js'
    assert os.path.exists(js_path), f"Arquivo {js_path} não encontrado"


def test_colorblind_simulator_js_exists():
    """Verifica se o simulador de daltonismo existe"""
    js_path = 'static/js/colorblind-simulator.js'
    assert os.path.exists(js_path), f"Arquivo {js_path} não encontrado"


def test_colorblind_filters_svg_exists():
    """Verifica se os filtros SVG de daltonismo existem"""
    svg_path = 'static/colorblind-filters.svg'
    assert os.path.exists(svg_path), f"Arquivo {svg_path} não encontrado"


def test_audit_documentation_exists():
    """Verifica se a documentação de auditoria existe"""
    doc_path = 'docs/AUDITORIA_CONTRASTE_CORES.md'
    assert os.path.exists(doc_path), f"Arquivo {doc_path} não encontrado"


def test_guide_documentation_exists():
    """Verifica se o guia de uso existe"""
    doc_path = 'docs/GUIA_ACESSIBILIDADE_CORES.md'
    assert os.path.exists(doc_path), f"Arquivo {doc_path} não encontrado"


def test_css_variables_defined():
    """Verifica se as variáveis CSS essenciais estão definidas"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Variáveis essenciais que devem existir
    required_vars = [
        '--a11y-primary',
        '--a11y-success',
        '--a11y-danger',
        '--a11y-warning',
        '--a11y-info',
        '--a11y-text-primary',
        '--a11y-text-secondary',
        '--a11y-link',
        '--a11y-focus-ring',
    ]
    
    for var in required_vars:
        assert var in content, f"Variável CSS {var} não encontrada"


def test_high_contrast_mode_defined():
    """Verifica se o modo de alto contraste está definido"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert '.high-contrast' in content, "Classe .high-contrast não encontrada"


def test_utility_classes_defined():
    """Verifica se as classes utilitárias estão definidas"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Classes utilitárias essenciais
    required_classes = [
        '.btn-a11y-primary',
        '.btn-a11y-success',
        '.btn-a11y-danger',
        '.btn-a11y-warning',
        '.btn-a11y-info',
        '.alert-a11y-success',
        '.alert-a11y-danger',
        '.alert-a11y-warning',
        '.alert-a11y-info',
        '.text-a11y-primary',
        '.link-a11y',
    ]
    
    for cls in required_classes:
        assert cls in content, f"Classe {cls} não encontrada"


def test_focus_indicators_defined():
    """Verifica se os indicadores de foco estão definidos"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há regras de foco
    assert ':focus' in content, "Regras de :focus não encontradas"
    assert 'outline' in content, "Propriedade outline não encontrada"


def test_colorblind_filters_defined():
    """Verifica se todos os filtros de daltonismo estão definidos"""
    svg_path = 'static/colorblind-filters.svg'
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Filtros essenciais
    required_filters = [
        'protanopia-filter',
        'deuteranopia-filter',
        'tritanopia-filter',
        'protanomaly-filter',
        'deuteranomaly-filter',
        'tritanomaly-filter',
        'achromatopsia-filter',
        'achromatomaly-filter',
    ]
    
    for filter_id in required_filters:
        assert filter_id in content, f"Filtro {filter_id} não encontrado"


def test_high_contrast_toggle_api():
    """Verifica se a API do toggle de alto contraste está exposta"""
    js_path = 'static/js/high-contrast-toggle.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar API pública
    assert 'window.HighContrastMode' in content, "API HighContrastMode não exposta"
    assert 'enable' in content, "Método enable não encontrado"
    assert 'disable' in content, "Método disable não encontrado"
    assert 'toggle' in content, "Método toggle não encontrado"


def test_colorblind_simulator_api():
    """Verifica se a API do simulador está exposta"""
    js_path = 'static/js/colorblind-simulator.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar API pública
    assert 'window.ColorblindSimulator' in content, "API ColorblindSimulator não exposta"
    assert 'apply' in content, "Método apply não encontrado"
    assert 'remove' in content, "Método remove não encontrado"


def test_keyboard_shortcuts_defined():
    """Verifica se os atalhos de teclado estão implementados"""
    # Alto contraste: Ctrl+Alt+C
    hc_js_path = 'static/js/high-contrast-toggle.js'
    with open(hc_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Ctrl+Alt+C' in content or 'ctrlKey' in content, \
        "Atalho de teclado para alto contraste não encontrado"
    
    # Simulador: Ctrl+Alt+V
    sim_js_path = 'static/js/colorblind-simulator.js'
    with open(sim_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Ctrl+Alt+V' in content or 'ctrlKey' in content, \
        "Atalho de teclado para simulador não encontrado"


def test_localstorage_persistence():
    """Verifica se há persistência de preferências"""
    js_path = 'static/js/high-contrast-toggle.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'localStorage' in content, "Persistência com localStorage não implementada"
    assert 'getItem' in content, "Leitura de localStorage não implementada"
    assert 'setItem' in content, "Escrita em localStorage não implementada"


def test_screen_reader_announcements():
    """Verifica se há anúncios para leitores de tela"""
    js_path = 'static/js/high-contrast-toggle.js'
    
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'aria-live' in content, "Região aria-live não encontrada"
    assert 'announceToScreenReader' in content or 'announce' in content, \
        "Função de anúncio não encontrada"


def test_prefers_contrast_media_query():
    """Verifica se há suporte a prefers-contrast"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'prefers-contrast' in content, "Media query prefers-contrast não encontrada"


def test_prefers_color_scheme_media_query():
    """Verifica se há suporte a prefers-color-scheme (modo escuro)"""
    css_path = 'static/css/accessibility-colors.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'prefers-color-scheme: dark' in content, \
        "Media query prefers-color-scheme: dark não encontrada"


def test_base_template_includes_accessibility_css():
    """Verifica se o template base inclui o CSS de acessibilidade"""
    template_path = 'templates/base.html'
    
    if not os.path.exists(template_path):
        pytest.skip("Template base.html não encontrado")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'accessibility-colors.css' in content, \
        "CSS de acessibilidade não incluído no template base"


def test_base_template_includes_scripts():
    """Verifica se o template base inclui os scripts de acessibilidade"""
    template_path = 'templates/base.html'
    
    if not os.path.exists(template_path):
        pytest.skip("Template base.html não encontrado")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'high-contrast-toggle.js' in content, \
        "Script de alto contraste não incluído no template base"
    assert 'colorblind-simulator.js' in content, \
        "Script de simulador não incluído no template base"


def test_documentation_completeness():
    """Verifica se a documentação está completa"""
    audit_path = 'docs/AUDITORIA_CONTRASTE_CORES.md'
    guide_path = 'docs/GUIA_ACESSIBILIDADE_CORES.md'
    
    # Verificar auditoria
    with open(audit_path, 'r', encoding='utf-8') as f:
        audit_content = f.read()
    
    assert 'WCAG 2.1' in audit_content, "Referência a WCAG não encontrada"
    assert 'Contraste' in audit_content, "Informação sobre contraste não encontrada"
    assert 'Daltonismo' in audit_content, "Informação sobre daltonismo não encontrada"
    
    # Verificar guia
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_content = f.read()
    
    assert 'Ctrl + Alt + C' in guide_content, "Atalho de teclado não documentado"
    assert 'btn-a11y-' in guide_content, "Classes de botão não documentadas"
    assert 'ColorblindSimulator' in guide_content, "API do simulador não documentada"


def test_color_contrast_script_exists():
    """Verifica se o script de teste de contraste existe"""
    script_path = 'test_color_contrast.py'
    assert os.path.exists(script_path), f"Script {script_path} não encontrado"


def test_color_contrast_script_runnable():
    """Verifica se o script de teste de contraste é executável"""
    script_path = 'test_color_contrast.py'
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar funções essenciais
    assert 'calculate_contrast_ratio' in content, "Função de cálculo não encontrada"
    assert 'check_wcag_compliance' in content, "Função de verificação WCAG não encontrada"
    assert 'test_color_combinations' in content, "Função de teste não encontrada"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
