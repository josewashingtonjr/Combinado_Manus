"""
Teste simples para verificar melhorias visuais de comprovantes no template
"""
import os

def test_template_visual_improvements():
    """Testa se as melhorias visuais estão presentes no template"""
    
    template_path = 'templates/admin/solicitacoes_tokens.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template não encontrado: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar elementos visuais para comprovante anexado
    checks = [
        ('badge bg-success', 'Badge de comprovante anexado'),
        ('fa-paperclip', 'Ícone de anexo (paperclip)'),
        ('Ver Comprovante', 'Texto do botão'),
        ('btn-primary', 'Classe do botão primário'),
        ('target="_blank"', 'Abertura em nova aba'),
        ('rel="noopener noreferrer"', 'Atributo de segurança'),
        ('Comprovante anexado', 'Tooltip de comprovante'),
        ('fa-eye', 'Ícone de visualização'),
    ]
    
    print("Verificando elementos visuais para comprovante anexado:")
    for check, description in checks:
        if check in html:
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} - NÃO ENCONTRADO: '{check}'")
            return False
    
    # Verificar elementos para solicitação sem comprovante
    checks_no_receipt = [
        ('Sem comprovante', 'Texto para sem comprovante'),
        ('fa-times-circle', 'Ícone de sem comprovante'),
    ]
    
    print("\nVerificando elementos para sem comprovante:")
    for check, description in checks_no_receipt:
        if check in html:
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} - NÃO ENCONTRADO: '{check}'")
            return False
    
    # Verificar CSS customizado
    css_checks = [
        ('@keyframes pulse', 'Animação pulse'),
        ('animation: pulse 2s infinite', 'Aplicação da animação'),
        ('z-index: 1050', 'Z-index do modal'),
        ('z-index: 1040', 'Z-index do backdrop'),
        ('.badge.bg-success', 'Estilo do badge'),
        ('.alert-floating', 'Estilo de alertas flutuantes'),
        ('@keyframes slideInRight', 'Animação de slide'),
    ]
    
    print("\nVerificando CSS customizado:")
    for check, description in css_checks:
        if check in html:
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} - NÃO ENCONTRADO: '{check}'")
            return False
    
    # Verificar estrutura melhorada
    structure_checks = [
        ('d-flex align-items-center', 'Layout flexbox para comprovante'),
        ('receipt_original_name', 'Exibição do nome do arquivo'),
        ('fa-file', 'Ícone de arquivo'),
    ]
    
    print("\nVerificando estrutura melhorada:")
    for check, description in structure_checks:
        if check in html:
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} - NÃO ENCONTRADO: '{check}'")
            return False
    
    print("\n✅ TODOS OS ELEMENTOS VISUAIS ESTÃO PRESENTES NO TEMPLATE!")
    return True

if __name__ == '__main__':
    try:
        success = test_template_visual_improvements()
        if not success:
            exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
