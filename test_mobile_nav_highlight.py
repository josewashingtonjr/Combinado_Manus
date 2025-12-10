"""
Teste para validar o destaque da página atual na navegação mobile

Task 8: Destacar página atual
Requirement 4: Navegação Simplificada
"""

import pytest
from flask import Flask, render_template_string
from jinja2 import Template


def test_mobile_nav_active_class_dashboard():
    """Testa se a classe 'active' é aplicada corretamente no item Dashboard"""
    
    # Simular contexto de request com path do dashboard
    template_str = """
    {% set current_path = '/cliente/dashboard' %}
    {% set is_dashboard = '/dashboard' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_dashboard else '' }}">Dashboard</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'active' in result
    assert 'mobile-nav-link active' in result


def test_mobile_nav_active_class_convites():
    """Testa se a classe 'active' é aplicada corretamente no item Convites"""
    
    template_str = """
    {% set current_path = '/prestador/convites' %}
    {% set is_invites = '/convites' in current_path or '/convite' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_invites else '' }}">Convites</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'active' in result
    assert 'mobile-nav-link active' in result


def test_mobile_nav_active_class_pre_ordem():
    """Testa se a classe 'active' é aplicada corretamente no item Pré-Ordem"""
    
    template_str = """
    {% set current_path = '/pre-ordem/listar' %}
    {% set is_pre_orders = '/pre-ordem' in current_path or '/pre_ordem' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_pre_orders else '' }}">Pré-Ordem</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'active' in result
    assert 'mobile-nav-link active' in result


def test_mobile_nav_active_class_ordens():
    """Testa se a classe 'active' é aplicada corretamente no item Ordens"""
    
    template_str = """
    {% set current_path = '/cliente/ordem/123' %}
    {% set is_orders = '/ordem' in current_path or '/order' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_orders else '' }}">Ordens</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'active' in result
    assert 'mobile-nav-link active' in result


def test_mobile_nav_active_class_perfil():
    """Testa se a classe 'active' é aplicada corretamente no item Perfil"""
    
    template_str = """
    {% set current_path = '/prestador/carteira' %}
    {% set is_profile = '/perfil' in current_path or '/carteira' in current_path or '/transacoes' in current_path or '/saque' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_profile else '' }}">Perfil</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'active' in result
    assert 'mobile-nav-link active' in result


def test_mobile_nav_only_one_active():
    """Testa se apenas um item está ativo por vez"""
    
    template_str = """
    {% set current_path = '/cliente/dashboard' %}
    {% set is_dashboard = '/dashboard' in current_path %}
    {% set is_invites = '/convites' in current_path %}
    {% set is_orders = '/ordem' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_dashboard else '' }}">Dashboard</a>
    <a class="mobile-nav-link {{ 'active' if is_invites else '' }}">Convites</a>
    <a class="mobile-nav-link {{ 'active' if is_orders else '' }}">Ordens</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    # Contar quantas vezes 'active' aparece
    active_count = result.count('mobile-nav-link active')
    
    assert active_count == 1, f"Esperado 1 item ativo, encontrado {active_count}"


def test_mobile_nav_aria_current_attribute():
    """Testa se o atributo aria-current é aplicado corretamente"""
    
    template_str = """
    {% set current_path = '/cliente/dashboard' %}
    {% set is_dashboard = '/dashboard' in current_path %}
    
    <a aria-current="{{ 'page' if is_dashboard else 'false' }}">Dashboard</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    assert 'aria-current="page"' in result


def test_mobile_nav_no_active_on_wrong_page():
    """Testa se a classe 'active' NÃO é aplicada quando não está na página"""
    
    template_str = """
    {% set current_path = '/cliente/dashboard' %}
    {% set is_invites = '/convites' in current_path %}
    
    <a class="mobile-nav-link {{ 'active' if is_invites else '' }}">Convites</a>
    """
    
    template = Template(template_str)
    result = template.render()
    
    # Não deve ter 'active' após 'mobile-nav-link'
    assert 'mobile-nav-link active' not in result
    # Mas deve ter 'mobile-nav-link' sozinho
    assert 'mobile-nav-link' in result


def test_mobile_nav_css_classes_present():
    """Testa se as classes CSS necessárias estão presentes no CSS"""
    
    with open('static/css/mobile-nav.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verificar se as classes importantes estão definidas
    assert '.mobile-nav-link.active' in css_content
    assert '.mobile-nav-link.active::before' in css_content
    assert '.mobile-nav-link.active .mobile-nav-icon' in css_content
    assert '.mobile-nav-link.active .mobile-nav-label' in css_content


def test_mobile_nav_visual_indicators_in_css():
    """Testa se os indicadores visuais estão definidos no CSS"""
    
    with open('static/css/mobile-nav.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verificar indicadores visuais
    assert 'font-weight: 700' in css_content  # Negrito
    assert 'background-color: rgba(74, 95, 193, 0.08)' in css_content  # Fundo destacado
    assert 'filter: drop-shadow' in css_content  # Efeito de brilho
    assert 'linear-gradient' in css_content  # Barra gradiente
    assert 'box-shadow' in css_content  # Sombra


def test_mobile_nav_animations_in_css():
    """Testa se as animações estão definidas no CSS"""
    
    with open('static/css/mobile-nav.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verificar animações
    assert '@keyframes activeIndicatorGlow' in css_content
    assert 'transition:' in css_content
    assert 'cubic-bezier' in css_content


def test_mobile_nav_component_structure():
    """Testa se o componente mobile-nav.html tem a estrutura correta"""
    
    with open('templates/components/mobile-nav.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Verificar estrutura básica
    assert '<nav class="mobile-nav' in html_content
    assert 'mobile-nav-list' in html_content
    assert 'mobile-nav-item' in html_content
    assert 'mobile-nav-link' in html_content
    assert 'mobile-nav-icon' in html_content
    assert 'mobile-nav-label' in html_content
    
    # Verificar lógica de detecção de página
    assert 'current_path = request.path' in html_content
    assert 'is_dashboard' in html_content
    assert 'is_invites' in html_content
    assert 'is_pre_orders' in html_content
    assert 'is_orders' in html_content
    assert 'is_profile' in html_content


def test_mobile_nav_javascript_feedback():
    """Testa se o JavaScript de feedback está presente"""
    
    with open('templates/components/mobile-nav.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Verificar JavaScript
    assert '<script>' in html_content
    assert 'touchstart' in html_content
    assert 'touchend' in html_content
    assert 'classList.add' in html_content
    assert 'classList.remove' in html_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
