"""
Teste de Consistência dos Menus do Painel Admin
Valida estrutura HTML, classes CSS e funcionalidade dos menus colapsáveis
"""

import re
from pathlib import Path


def test_menu_structure():
    """Testa se todos os menus colapsáveis têm estrutura consistente"""
    
    # Ler o template base_admin.html
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão esperado para menus colapsáveis
    menu_pattern = r'<a class="d-flex justify-content-between align-items-center p-3 text-decoration-none text-dark sidebar-menu-header"'
    
    # Encontrar todos os menus colapsáveis
    menus = re.findall(menu_pattern, content)
    
    print(f"✓ Encontrados {len(menus)} menus colapsáveis com estrutura padronizada")
    
    # Verificar se todos têm aria-expanded e aria-controls
    aria_expanded_count = content.count('aria-expanded="false"')
    aria_controls_count = content.count('aria-controls=')
    
    print(f"✓ {aria_expanded_count} menus com aria-expanded")
    print(f"✓ {aria_controls_count} menus com aria-controls")
    
    # Verificar ícone de transição
    transition_icon_count = content.count('transition-icon')
    print(f"✓ {transition_icon_count} ícones com classe transition-icon")
    
    # Verificar submenus
    submenu_pattern = r'sidebar-submenu-item'
    submenus = re.findall(submenu_pattern, content)
    print(f"✓ {len(submenus)} itens de submenu com classe padronizada")
    
    assert len(menus) >= 8, "Deve haver pelo menos 8 menus colapsáveis"
    assert aria_expanded_count >= 8, "Todos os menus devem ter aria-expanded"
    assert transition_icon_count >= 8, "Todos os menus devem ter ícone com transição"
    
    print("\n✅ Estrutura dos menus está consistente!")


def test_css_classes():
    """Testa se as classes CSS estão aplicadas corretamente"""
    
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Classes obrigatórias
    required_classes = [
        'sidebar-menu-header',
        'sidebar-submenu-item',
        'transition-icon',
        'list-group-item-action',
        'ps-4',
        'py-2'
    ]
    
    for css_class in required_classes:
        count = content.count(css_class)
        print(f"✓ Classe '{css_class}' encontrada {count} vezes")
        assert count > 0, f"Classe {css_class} não encontrada"
    
    print("\n✅ Todas as classes CSS estão aplicadas!")


def test_css_file_exists():
    """Testa se o arquivo CSS específico existe"""
    
    css_path = Path('static/css/admin-menu.css')
    assert css_path.exists(), "Arquivo admin-menu.css não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verificar estilos importantes
    important_styles = [
        '.sidebar-menu-header',
        '.sidebar-submenu-item',
        '.transition-icon',
        'hover',
        'transition',
        'aria-expanded'
    ]
    
    for style in important_styles:
        assert style in css_content, f"Estilo {style} não encontrado no CSS"
        print(f"✓ Estilo '{style}' presente no CSS")
    
    print("\n✅ Arquivo CSS está completo!")


def test_navbar_consistency():
    """Testa consistência da navbar superior"""
    
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar elementos da navbar
    navbar_elements = [
        'navbar-brand',
        'navbar-toggler',
        'navbar-collapse',
        'nav-link',
        'dropdown-toggle',
        'dropdown-menu'
    ]
    
    for element in navbar_elements:
        count = content.count(element)
        print(f"✓ Elemento '{element}' encontrado {count} vezes")
        assert count > 0, f"Elemento {element} não encontrado na navbar"
    
    # Verificar badges de notificação
    badge_count = content.count('badge bg-warning')
    print(f"✓ {badge_count} badges de notificação encontrados")
    
    print("\n✅ Navbar está consistente!")


def test_menu_ids():
    """Testa se todos os menus têm IDs únicos"""
    
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar todos os IDs de menu
    menu_ids = re.findall(r'id="(menu[A-Za-z]+)"', content)
    
    print(f"✓ Encontrados {len(menu_ids)} IDs de menu")
    
    # Verificar se não há duplicatas
    unique_ids = set(menu_ids)
    assert len(menu_ids) == len(unique_ids), "Existem IDs duplicados!"
    
    # IDs esperados
    expected_ids = [
        'menuUsuarios',
        'menuTokens',
        'menuOrdens',
        'menuContestacoes',
        'menuConvites',
        'menuContratos',
        'menuConfig',
        'menuRelatorios'
    ]
    
    for expected_id in expected_ids:
        assert expected_id in menu_ids, f"ID {expected_id} não encontrado"
        print(f"✓ ID '{expected_id}' presente")
    
    print("\n✅ Todos os IDs de menu são únicos e corretos!")


def test_accessibility():
    """Testa atributos de acessibilidade"""
    
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar atributos ARIA
    aria_attributes = [
        'aria-expanded',
        'aria-controls',
        'role="button"'
    ]
    
    for attr in aria_attributes:
        count = content.count(attr)
        print(f"✓ Atributo '{attr}' encontrado {count} vezes")
        assert count > 0, f"Atributo {attr} não encontrado"
    
    print("\n✅ Atributos de acessibilidade estão presentes!")


def test_css_link():
    """Testa se o link para o CSS está no template"""
    
    template_path = Path('templates/admin/base_admin.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'admin-menu.css' in content, "Link para admin-menu.css não encontrado"
    print("✓ Link para admin-menu.css presente no template")
    
    print("\n✅ CSS está linkado corretamente!")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTE DE CONSISTÊNCIA DOS MENUS DO PAINEL ADMIN")
    print("=" * 60)
    print()
    
    try:
        print("1. Testando estrutura dos menus...")
        print("-" * 60)
        test_menu_structure()
        print()
        
        print("2. Testando classes CSS...")
        print("-" * 60)
        test_css_classes()
        print()
        
        print("3. Testando arquivo CSS...")
        print("-" * 60)
        test_css_file_exists()
        print()
        
        print("4. Testando consistência da navbar...")
        print("-" * 60)
        test_navbar_consistency()
        print()
        
        print("5. Testando IDs dos menus...")
        print("-" * 60)
        test_menu_ids()
        print()
        
        print("6. Testando acessibilidade...")
        print("-" * 60)
        test_accessibility()
        print()
        
        print("7. Testando link do CSS...")
        print("-" * 60)
        test_css_link()
        print()
        
        print("=" * 60)
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 60)
        print()
        print("Resumo:")
        print("- Estrutura dos menus: ✓ Padronizada")
        print("- Classes CSS: ✓ Aplicadas corretamente")
        print("- Arquivo CSS: ✓ Completo")
        print("- Navbar: ✓ Consistente")
        print("- IDs: ✓ Únicos e corretos")
        print("- Acessibilidade: ✓ Implementada")
        print("- Link CSS: ✓ Presente")
        
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        exit(1)
