"""
Teste do Componente Toast Feedback
Valida a implementação do sistema de notificações toast
"""

import os
import re


def test_toast_files_exist():
    """Verifica se todos os arquivos do componente toast foram criados"""
    files = [
        'static/css/toast-feedback.css',
        'static/js/toast-feedback.js',
        'templates/components/toast-feedback.html'
    ]
    
    for file_path in files:
        assert os.path.exists(file_path), f"Arquivo {file_path} não encontrado"
        print(f"✓ {file_path} existe")


def test_toast_css_structure():
    """Verifica a estrutura do CSS do toast"""
    with open('static/css/toast-feedback.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verifica classes essenciais
    required_classes = [
        '.toast-container',
        '.toast-feedback',
        '.toast-content',
        '.toast-icon',
        '.toast-message',
        '.toast-close',
        '.toast-progress',
        '.toast-success',
        '.toast-error',
        '.toast-warning',
        '.toast-info'
    ]
    
    for css_class in required_classes:
        assert css_class in css_content, f"Classe {css_class} não encontrada no CSS"
        print(f"✓ Classe {css_class} presente")
    
    # Verifica propriedades importantes
    assert 'min-height: 48px' in css_content, "Touch target mínimo não definido"
    print("✓ Touch target mínimo (48px) definido")
    
    assert 'position: fixed' in css_content, "Container não está fixo"
    print("✓ Container fixo no topo")
    
    assert 'z-index: 9999' in css_content, "Z-index não está alto o suficiente"
    print("✓ Z-index adequado")
    
    # Verifica animações
    assert '@keyframes slideInDown' in css_content, "Animação de entrada não definida"
    assert '@keyframes slideOutUp' in css_content, "Animação de saída não definida"
    print("✓ Animações de entrada/saída definidas")
    
    # Verifica responsividade
    assert '@media (max-width: 576px)' in css_content, "Media query mobile não encontrada"
    print("✓ Media query para mobile presente")
    
    # Verifica acessibilidade
    assert '@media (prefers-reduced-motion: reduce)' in css_content, "Suporte a movimento reduzido não encontrado"
    assert '@media (prefers-contrast: high)' in css_content, "Suporte a alto contraste não encontrado"
    print("✓ Suporte a preferências de acessibilidade")


def test_toast_javascript_structure():
    """Verifica a estrutura do JavaScript do toast"""
    with open('static/js/toast-feedback.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Verifica classe principal
    assert 'class ToastManager' in js_content, "Classe ToastManager não encontrada"
    print("✓ Classe ToastManager presente")
    
    # Verifica métodos essenciais
    required_methods = [
        'init()',
        'setup()',
        'show(',
        'hide(',
        'success(',
        'error(',
        'warning(',
        'info(',
        'hideAll()',
        'convertFlashMessages()'
    ]
    
    for method in required_methods:
        assert method in js_content, f"Método {method} não encontrado"
        print(f"✓ Método {method} presente")
    
    # Verifica API global
    assert 'window.showToast' in js_content, "API global showToast não exposta"
    assert 'window.toast' in js_content, "API global toast não exposta"
    print("✓ API global exposta")
    
    # Verifica duração padrão de 5 segundos
    assert 'duration = 5000' in js_content, "Duração padrão não é 5 segundos"
    print("✓ Duração padrão de 5 segundos")


def test_toast_html_structure():
    """Verifica a estrutura do HTML do toast"""
    with open('templates/components/toast-feedback.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Verifica container
    assert 'id="toast-container"' in html_content, "Container não tem ID correto"
    assert 'aria-live="polite"' in html_content, "Container não tem aria-live"
    print("✓ Container com atributos ARIA corretos")
    
    # Verifica template
    assert '<template id="toast-template">' in html_content, "Template não encontrado"
    print("✓ Template presente")
    
    # Verifica estrutura do toast
    assert 'class="toast-feedback"' in html_content, "Classe toast-feedback não encontrada"
    assert 'class="toast-content"' in html_content, "Classe toast-content não encontrada"
    assert 'class="toast-icon"' in html_content, "Classe toast-icon não encontrada"
    assert 'class="toast-message"' in html_content, "Classe toast-message não encontrada"
    assert 'class="toast-close"' in html_content, "Classe toast-close não encontrada"
    assert 'class="toast-progress"' in html_content, "Classe toast-progress não encontrada"
    print("✓ Estrutura do toast completa")
    
    # Verifica acessibilidade
    assert 'role="alert"' in html_content, "Role alert não encontrado"
    assert 'aria-label="Fechar"' in html_content, "Aria-label do botão fechar não encontrado"
    print("✓ Atributos de acessibilidade presentes")
    
    # Verifica ícones Font Awesome
    assert 'fas fa-' in html_content, "Ícones Font Awesome não encontrados"
    print("✓ Ícones Font Awesome presentes")


def test_toast_integration_in_base():
    """Verifica se o toast foi integrado no template base"""
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    # Verifica inclusão do CSS
    assert 'toast-feedback.css' in base_content, "CSS do toast não incluído no base.html"
    print("✓ CSS do toast incluído no base.html")
    
    # Verifica inclusão do JS
    assert 'toast-feedback.js' in base_content, "JS do toast não incluído no base.html"
    print("✓ JS do toast incluído no base.html")
    
    # Verifica inclusão do componente
    assert "include 'components/toast-feedback.html'" in base_content, "Componente toast não incluído no base.html"
    print("✓ Componente toast incluído no base.html")


def test_toast_colors_semantic():
    """Verifica se as cores semânticas estão corretas"""
    with open('static/css/toast-feedback.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Cores esperadas (Bootstrap padrão)
    colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    }
    
    for toast_type, color in colors.items():
        assert color in css_content, f"Cor {color} para {toast_type} não encontrada"
        print(f"✓ Cor semântica para {toast_type}: {color}")


def test_toast_touch_targets():
    """Verifica se os touch targets são adequados para mobile"""
    with open('static/css/toast-feedback.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verifica altura mínima de 48px (recomendação Apple/Google)
    assert 'min-height: 48px' in css_content, "Touch target mínimo não atende recomendações"
    print("✓ Touch target mínimo de 48px (Apple/Google guidelines)")
    
    # Verifica botão de fechar
    assert re.search(r'\.toast-close\s*{[^}]*width:\s*32px', css_content), "Botão fechar não tem largura adequada"
    assert re.search(r'\.toast-close\s*{[^}]*height:\s*32px', css_content), "Botão fechar não tem altura adequada"
    print("✓ Botão de fechar com dimensões adequadas")


def test_toast_animations():
    """Verifica se as animações estão implementadas"""
    with open('static/css/toast-feedback.css', 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Verifica animações
    animations = [
        'slideInDown',
        'slideOutUp',
        'progressBar'
    ]
    
    for animation in animations:
        assert f'@keyframes {animation}' in css_content, f"Animação {animation} não encontrada"
        print(f"✓ Animação {animation} implementada")
    
    # Verifica duração da animação
    assert '0.3s' in css_content, "Duração de animação não encontrada"
    print("✓ Duração de animação definida")


def test_toast_auto_dismiss():
    """Verifica se o auto-dismiss está configurado corretamente"""
    with open('static/js/toast-feedback.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Verifica timeout de 5 segundos
    assert 'duration = 5000' in js_content, "Duração padrão não é 5000ms"
    print("✓ Auto-dismiss padrão de 5 segundos")
    
    # Verifica implementação do timeout
    assert 'setTimeout' in js_content, "setTimeout não implementado"
    assert 'clearTimeout' in js_content, "clearTimeout não implementado"
    print("✓ Timeout implementado corretamente")


def run_all_tests():
    """Executa todos os testes"""
    tests = [
        ("Arquivos do Componente", test_toast_files_exist),
        ("Estrutura CSS", test_toast_css_structure),
        ("Estrutura JavaScript", test_toast_javascript_structure),
        ("Estrutura HTML", test_toast_html_structure),
        ("Integração no Base", test_toast_integration_in_base),
        ("Cores Semânticas", test_toast_colors_semantic),
        ("Touch Targets", test_toast_touch_targets),
        ("Animações", test_toast_animations),
        ("Auto-dismiss", test_toast_auto_dismiss)
    ]
    
    print("=" * 60)
    print("TESTE DO COMPONENTE TOAST FEEDBACK")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 60)
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name}: PASSOU")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name}: FALHOU")
            print(f"   Erro: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERRO")
            print(f"   Erro: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTADO: {passed} passaram, {failed} falharam")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
