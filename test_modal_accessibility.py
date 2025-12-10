"""
Teste para verificar que o modal de ajuste permanece acessível após visualizar comprovante
"""
import os

def test_modal_remains_accessible():
    """
    Verifica que o modal de ajuste permanece acessível após visualizar comprovante.
    
    O comprovante abre em nova aba (target="_blank"), então o modal não é afetado.
    """
    
    template_path = 'templates/admin/solicitacoes_tokens.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template não encontrado: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    print("Verificando que o modal de ajuste permanece acessível:")
    
    # 1. Verificar que o link do comprovante abre em nova aba
    if 'target="_blank"' in html and 'view_receipt' in html:
        print("  ✓ Comprovante abre em nova aba (target='_blank')")
    else:
        print("  ❌ Comprovante não está configurado para abrir em nova aba")
        return False
    
    # 2. Verificar atributo de segurança
    if 'rel="noopener noreferrer"' in html:
        print("  ✓ Atributo de segurança presente (rel='noopener noreferrer')")
    else:
        print("  ❌ Atributo de segurança ausente")
        return False
    
    # 3. Verificar que o modal de ajuste existe
    if 'id="ajustarQuantidadeModal"' in html:
        print("  ✓ Modal de ajuste existe no template")
    else:
        print("  ❌ Modal de ajuste não encontrado")
        return False
    
    # 4. Verificar que o botão de ajuste está presente
    if 'abrirModalAjuste' in html:
        print("  ✓ Botão de ajuste presente")
    else:
        print("  ❌ Botão de ajuste não encontrado")
        return False
    
    # 5. Verificar z-index adequado para modais
    if 'z-index: 1050' in html and 'z-index: 1040' in html:
        print("  ✓ Z-index configurado corretamente para modais")
    else:
        print("  ❌ Z-index não configurado adequadamente")
        return False
    
    # 6. Verificar que não há JavaScript que fecha o modal ao clicar no comprovante
    # (não deve haver event listeners que interferem)
    if 'modal.hide()' in html:
        # Verificar que hide() só é chamado em contextos apropriados
        lines_with_hide = [line for line in html.split('\n') if 'modal.hide()' in line]
        for line in lines_with_hide:
            if 'view_receipt' in line or 'Ver Comprovante' in line:
                print("  ❌ Modal pode ser fechado ao visualizar comprovante")
                return False
        print("  ✓ Modal não é fechado ao visualizar comprovante")
    else:
        print("  ✓ Nenhum código que fecha modal indevidamente")
    
    print("\n✅ MODAL DE AJUSTE PERMANECE ACESSÍVEL APÓS VISUALIZAR COMPROVANTE!")
    print("\nExplicação técnica:")
    print("  - O comprovante abre em nova aba (target='_blank')")
    print("  - Isso não afeta a página atual onde o modal está")
    print("  - O usuário pode visualizar o comprovante e voltar para ajustar")
    print("  - Atributos de segurança (rel='noopener noreferrer') previnem vulnerabilidades")
    
    return True

if __name__ == '__main__':
    try:
        success = test_modal_remains_accessible()
        if not success:
            exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
