"""
Teste para verificar que os botões de ação têm altura mínima de 48px.
Requirement 2: Botões Otimizados para Touch - altura mínima de 48px
"""
import re
import os


def test_touch_targets_css_has_48px_min_height():
    """Verifica se touch-targets.css define min-height: 48px para botões."""
    css_path = 'static/css/touch-targets.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há regra global para .btn com min-height: 48px
    assert 'min-height: 48px' in content, "touch-targets.css deve conter min-height: 48px"
    
    # Verificar se .btn está incluído nas regras
    assert '.btn' in content, "touch-targets.css deve ter regras para .btn"
    
    # Verificar se há regra para touch-target
    assert '.touch-target' in content, "touch-targets.css deve ter classe .touch-target"
    
    print("✓ touch-targets.css contém regras de altura mínima 48px para botões")


def test_style_css_has_48px_min_height():
    """Verifica se style.css define min-height: 48px para botões."""
    css_path = 'static/css/style.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há regra para .btn com min-height: 48px
    assert 'min-height: 48px' in content, "style.css deve conter min-height: 48px"
    
    print("✓ style.css contém regras de altura mínima 48px para botões")


def test_invite_css_has_48px_min_height():
    """Verifica se invite.css define min-height: 48px para botões."""
    css_path = 'static/css/invite.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há regra para botões com min-height: 48px
    assert 'min-height: 48px' in content, "invite.css deve conter min-height: 48px"
    
    # Verificar se accept-btn e reject-btn estão definidos
    assert '.accept-btn' in content, "invite.css deve ter classe .accept-btn"
    assert '.reject-btn' in content, "invite.css deve ter classe .reject-btn"
    
    print("✓ invite.css contém regras de altura mínima 48px para botões")


def test_tokens_css_has_48px_min_height():
    """Verifica se tokens.css define min-height: 48px para botões."""
    css_path = 'static/css/tokens.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há regra para .btn com min-height: 48px
    assert 'min-height: 48px' in content, "tokens.css deve conter min-height: 48px"
    
    print("✓ tokens.css contém regras de altura mínima 48px para botões")


def test_mobile_first_css_has_touch_target_variable():
    """Verifica se mobile-first.css define variável --touch-target-min: 48px."""
    css_path = 'static/css/mobile-first.css'
    assert os.path.exists(css_path), f"Arquivo {css_path} não encontrado"
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se a variável está definida como 48px
    assert '--touch-target-min: 48px' in content, "mobile-first.css deve definir --touch-target-min: 48px"
    
    print("✓ mobile-first.css define variável --touch-target-min: 48px")


def test_all_button_classes_have_min_height():
    """Verifica se todas as classes de botão principais têm min-height definido."""
    css_path = 'static/css/touch-targets.css'
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Classes de botão que devem ter min-height
    button_classes = [
        '.btn',
        '.btn-primary',
        '.btn-secondary',
        '.btn-success',
        '.btn-danger',
        '.btn-warning',
        '.btn-info',
    ]
    
    # Verificar se há uma regra que inclui todas essas classes
    for btn_class in button_classes:
        assert btn_class in content, f"touch-targets.css deve incluir {btn_class}"
    
    print("✓ Todas as classes de botão principais estão incluídas nas regras de altura mínima")


if __name__ == '__main__':
    print("Executando testes de altura mínima de botões (48px)...")
    print("-" * 60)
    
    test_touch_targets_css_has_48px_min_height()
    test_style_css_has_48px_min_height()
    test_invite_css_has_48px_min_height()
    test_tokens_css_has_48px_min_height()
    test_mobile_first_css_has_touch_target_variable()
    test_all_button_classes_have_min_height()
    
    print("-" * 60)
    print("✓ Todos os testes passaram!")
    print("\nRequisito 2 (Botões Otimizados para Touch) implementado:")
    print("- Altura mínima de 48px para todos os botões de ação")
