"""
Testes para Skeleton Loading System
Valida a implementação dos componentes de skeleton loading

Requirements: 8.2
"""

import os
import re
from pathlib import Path


def test_skeleton_css_exists():
    """Verifica se o arquivo CSS de skeleton existe"""
    css_path = Path('static/css/skeleton-loading.css')
    assert css_path.exists(), "Arquivo skeleton-loading.css não encontrado"
    print("✓ Arquivo CSS de skeleton existe")


def test_skeleton_js_exists():
    """Verifica se o arquivo JS de skeleton existe"""
    js_path = Path('static/js/skeleton-loader.js')
    assert js_path.exists(), "Arquivo skeleton-loader.js não encontrado"
    print("✓ Arquivo JS de skeleton existe")


def test_skeleton_components_exist():
    """Verifica se os componentes HTML de skeleton existem"""
    components = [
        'templates/components/skeleton-convite-card.html',
        'templates/components/skeleton-ordem-card.html',
        'templates/components/skeleton-convite-list.html',
        'templates/components/skeleton-ordem-list.html',
        'templates/components/skeleton-convite-detail.html',
        'templates/components/skeleton-ordem-detail.html',
        'templates/components/skeleton-dashboard.html'
    ]
    
    for component in components:
        path = Path(component)
        assert path.exists(), f"Componente {component} não encontrado"
        print(f"✓ Componente {component} existe")


def test_skeleton_css_has_animations():
    """Verifica se o CSS tem as animações necessárias"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    # Verifica animações
    assert '@keyframes skeleton-shimmer' in content, "Animação skeleton-shimmer não encontrada"
    assert '@keyframes skeleton-pulse' in content, "Animação skeleton-pulse não encontrada"
    print("✓ Animações CSS estão definidas")
    
    # Verifica classes base
    assert '.skeleton {' in content, "Classe .skeleton não encontrada"
    assert '.skeleton-text' in content, "Classe .skeleton-text não encontrada"
    assert '.skeleton-button' in content, "Classe .skeleton-button não encontrada"
    print("✓ Classes base CSS estão definidas")


def test_skeleton_css_has_card_styles():
    """Verifica se o CSS tem estilos para cards"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    required_classes = [
        '.skeleton-convite-card',
        '.skeleton-ordem-card',
        '.skeleton-convite-header',
        '.skeleton-ordem-header',
        '.skeleton-convite-actions',
        '.skeleton-ordem-actions'
    ]
    
    for class_name in required_classes:
        assert class_name in content, f"Classe {class_name} não encontrada no CSS"
    
    print("✓ Estilos de cards estão definidos")


def test_skeleton_css_has_list_styles():
    """Verifica se o CSS tem estilos para listas"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    required_classes = [
        '.skeleton-convites-list',
        '.skeleton-ordens-list',
        '.skeleton-convite-list-item',
        '.skeleton-ordem-list-item'
    ]
    
    for class_name in required_classes:
        assert class_name in content, f"Classe {class_name} não encontrada no CSS"
    
    print("✓ Estilos de listas estão definidos")


def test_skeleton_css_has_detail_styles():
    """Verifica se o CSS tem estilos para detalhes"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    required_classes = [
        '.skeleton-convite-detail',
        '.skeleton-ordem-detail',
        '.skeleton-convite-detail-header',
        '.skeleton-ordem-detail-header',
        '.skeleton-convite-detail-section'
    ]
    
    for class_name in required_classes:
        assert class_name in content, f"Classe {class_name} não encontrada no CSS"
    
    print("✓ Estilos de detalhes estão definidos")


def test_skeleton_css_is_responsive():
    """Verifica se o CSS tem media queries para responsividade"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    assert '@media (max-width: 768px)' in content, "Media query para mobile não encontrada"
    print("✓ CSS é responsivo (media queries presentes)")


def test_skeleton_css_has_accessibility():
    """Verifica se o CSS tem suporte a acessibilidade"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    # Verifica suporte a movimento reduzido
    assert '@media (prefers-reduced-motion: reduce)' in content, \
        "Suporte a prefers-reduced-motion não encontrado"
    
    # Verifica aria attributes
    assert 'aria-busy' in content or '[aria-busy' in content, \
        "Suporte a aria-busy não encontrado"
    
    print("✓ CSS tem suporte a acessibilidade")


def test_skeleton_js_has_class():
    """Verifica se o JS define a classe SkeletonLoader"""
    js_path = Path('static/js/skeleton-loader.js')
    content = js_path.read_text()
    
    assert 'class SkeletonLoader' in content, "Classe SkeletonLoader não encontrada"
    print("✓ Classe SkeletonLoader está definida")


def test_skeleton_js_has_methods():
    """Verifica se o JS tem os métodos necessários"""
    js_path = Path('static/js/skeleton-loader.js')
    content = js_path.read_text()
    
    required_methods = [
        'show(',
        'hide(',
        'loadSkeleton(',
        'getConviteCardSkeleton(',
        'getOrdemCardSkeleton(',
        'getConviteListSkeleton(',
        'getOrdemListSkeleton(',
        'getConviteDetailSkeleton(',
        'getOrdemDetailSkeleton(',
        'getDashboardSkeleton('
    ]
    
    for method in required_methods:
        assert method in content, f"Método {method} não encontrado no JS"
    
    print("✓ Todos os métodos necessários estão definidos")


def test_skeleton_js_has_integration():
    """Verifica se o JS tem integração com loading states"""
    js_path = Path('static/js/skeleton-loader.js')
    content = js_path.read_text()
    
    assert 'integrateWithLoadingStates' in content, \
        "Método de integração com loading states não encontrado"
    assert 'window.LoadingStates' in content, \
        "Referência a LoadingStates não encontrada"
    
    print("✓ Integração com Loading States está implementada")


def test_skeleton_js_exports_global():
    """Verifica se o JS exporta para escopo global"""
    js_path = Path('static/js/skeleton-loader.js')
    content = js_path.read_text()
    
    assert 'window.SkeletonLoader' in content, "Export para window.SkeletonLoader não encontrado"
    assert 'window.skeletonLoader' in content, "Export para window.skeletonLoader não encontrado"
    
    print("✓ Exports globais estão definidos")


def test_skeleton_components_have_aria():
    """Verifica se os componentes HTML têm atributos ARIA"""
    components = [
        'templates/components/skeleton-convite-card.html',
        'templates/components/skeleton-ordem-card.html',
        'templates/components/skeleton-convite-list.html',
        'templates/components/skeleton-ordem-list.html'
    ]
    
    for component_path in components:
        path = Path(component_path)
        content = path.read_text()
        
        assert 'role="status"' in content, f"{component_path} não tem role='status'"
        assert 'aria-busy="true"' in content, f"{component_path} não tem aria-busy='true'"
        assert 'aria-label=' in content, f"{component_path} não tem aria-label"
        
        print(f"✓ {component_path} tem atributos ARIA corretos")


def test_skeleton_components_have_sr_only():
    """Verifica se os componentes têm texto para leitores de tela"""
    components = [
        'templates/components/skeleton-convite-card.html',
        'templates/components/skeleton-ordem-card.html',
        'templates/components/skeleton-convite-list.html',
        'templates/components/skeleton-ordem-list.html'
    ]
    
    for component_path in components:
        path = Path(component_path)
        content = path.read_text()
        
        assert 'sr-only' in content or 'Carregando' in content, \
            f"{component_path} não tem texto para leitores de tela"
        
        print(f"✓ {component_path} tem texto para leitores de tela")


def test_base_template_includes_skeleton_css():
    """Verifica se o base.html inclui o CSS de skeleton"""
    base_path = Path('templates/base.html')
    content = base_path.read_text()
    
    assert 'skeleton-loading.css' in content, \
        "skeleton-loading.css não está incluído no base.html"
    
    print("✓ CSS de skeleton está incluído no base.html")


def test_base_template_includes_skeleton_js():
    """Verifica se o base.html inclui o JS de skeleton"""
    base_path = Path('templates/base.html')
    content = base_path.read_text()
    
    assert 'skeleton-loader.js' in content, \
        "skeleton-loader.js não está incluído no base.html"
    
    print("✓ JS de skeleton está incluído no base.html")


def test_demo_page_exists():
    """Verifica se a página de demonstração existe"""
    demo_path = Path('static/skeleton-loading-demo.html')
    assert demo_path.exists(), "Página de demonstração não encontrada"
    print("✓ Página de demonstração existe")


def test_demo_page_has_all_examples():
    """Verifica se a página de demonstração tem todos os exemplos"""
    demo_path = Path('static/skeleton-loading-demo.html')
    content = demo_path.read_text()
    
    required_demos = [
        'Card de Convite',
        'Card de Ordem',
        'Lista de Convites',
        'Lista de Ordens',
        'Detalhes do Convite',
        'Dashboard'
    ]
    
    for demo in required_demos:
        assert demo in content, f"Demo '{demo}' não encontrado na página"
    
    print("✓ Página de demonstração tem todos os exemplos")


def test_guide_exists():
    """Verifica se o guia de uso existe"""
    guide_path = Path('SKELETON_LOADING_GUIA.md')
    assert guide_path.exists(), "Guia de uso não encontrado"
    print("✓ Guia de uso existe")


def test_guide_has_examples():
    """Verifica se o guia tem exemplos de uso"""
    guide_path = Path('SKELETON_LOADING_GUIA.md')
    content = guide_path.read_text()
    
    assert '```javascript' in content, "Guia não tem exemplos JavaScript"
    assert 'window.skeletonLoader.show' in content, "Guia não tem exemplo de show()"
    assert 'window.skeletonLoader.hide' in content, "Guia não tem exemplo de hide()"
    
    print("✓ Guia tem exemplos de uso")


def test_skeleton_css_performance():
    """Verifica se o CSS tem otimizações de performance"""
    css_path = Path('static/css/skeleton-loading.css')
    content = css_path.read_text()
    
    # Verifica otimizações
    assert 'will-change' in content, "Otimização will-change não encontrada"
    assert 'contain:' in content, "Otimização contain não encontrada"
    
    print("✓ CSS tem otimizações de performance")


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("TESTES - SKELETON LOADING SYSTEM")
    print("="*60 + "\n")
    
    tests = [
        ("Arquivos Existem", [
            test_skeleton_css_exists,
            test_skeleton_js_exists,
            test_skeleton_components_exist,
            test_demo_page_exists,
            test_guide_exists
        ]),
        ("CSS - Estrutura", [
            test_skeleton_css_has_animations,
            test_skeleton_css_has_card_styles,
            test_skeleton_css_has_list_styles,
            test_skeleton_css_has_detail_styles
        ]),
        ("CSS - Recursos", [
            test_skeleton_css_is_responsive,
            test_skeleton_css_has_accessibility,
            test_skeleton_css_performance
        ]),
        ("JavaScript - Estrutura", [
            test_skeleton_js_has_class,
            test_skeleton_js_has_methods,
            test_skeleton_js_has_integration,
            test_skeleton_js_exports_global
        ]),
        ("Componentes HTML", [
            test_skeleton_components_have_aria,
            test_skeleton_components_have_sr_only
        ]),
        ("Integração", [
            test_base_template_includes_skeleton_css,
            test_base_template_includes_skeleton_js
        ]),
        ("Documentação", [
            test_demo_page_has_all_examples,
            test_guide_has_examples
        ])
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category, category_tests in tests:
        print(f"\n📋 {category}")
        print("-" * 60)
        
        for test_func in category_tests:
            total_tests += 1
            try:
                test_func()
                passed_tests += 1
            except AssertionError as e:
                failed_tests.append((test_func.__name__, str(e)))
                print(f"✗ {test_func.__name__}: {e}")
            except Exception as e:
                failed_tests.append((test_func.__name__, str(e)))
                print(f"✗ {test_func.__name__}: Erro inesperado - {e}")
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    print(f"\nTotal de testes: {total_tests}")
    print(f"✓ Passou: {passed_tests}")
    print(f"✗ Falhou: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ TESTES FALHADOS:")
        for test_name, error in failed_tests:
            print(f"  - {test_name}: {error}")
        print("\n")
        return False
    else:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        print("\n🎉 Skeleton Loading System implementado com sucesso!")
        print("\n📚 Próximos passos:")
        print("  1. Abra static/skeleton-loading-demo.html para ver a demonstração")
        print("  2. Leia SKELETON_LOADING_GUIA.md para aprender a usar")
        print("  3. Integre skeleton loading nas páginas de convites e ordens")
        print("\n")
        return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
