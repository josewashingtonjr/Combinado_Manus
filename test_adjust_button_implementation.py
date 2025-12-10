"""
Teste para verificar a implementação do botão de ajuste na tabela de solicitações
"""
import re
from pathlib import Path


def test_adjust_button_in_template():
    """Verifica se o botão de ajuste foi adicionado ao template"""
    template_path = Path('templates/admin/solicitacoes_tokens.html')
    
    assert template_path.exists(), "Template não encontrado"
    
    content = template_path.read_text(encoding='utf-8')
    
    # Verificar se o botão de ajuste existe
    assert 'btn-warning' in content, "Botão de ajuste não encontrado (classe btn-warning)"
    assert 'abrirModalAjuste' in content, "Função abrirModalAjuste não encontrada"
    assert 'fa-edit' in content, "Ícone de edição não encontrado"
    assert 'Ajustar Quantidade' in content, "Título do botão não encontrado"
    
    # Verificar se está dentro da condicional de status pending
    pending_section = re.search(
        r"{% if solicitacao\.status == 'pending' %}.*?{% else %}",
        content,
        re.DOTALL
    )
    
    assert pending_section, "Seção de solicitações pendentes não encontrada"
    
    pending_content = pending_section.group(0)
    
    # Verificar se o botão está na seção de pendentes
    assert 'abrirModalAjuste' in pending_content, "Botão de ajuste não está na seção de pendentes"
    assert 'btn-warning' in pending_content, "Botão warning não está na seção de pendentes"
    
    # Verificar se o onclick chama a função com os parâmetros corretos
    onclick_pattern = r'onclick="abrirModalAjuste\(\{\{ solicitacao\.id \}\}, \{\{ solicitacao\.amount \}\}\)"'
    assert re.search(onclick_pattern, content), "Onclick não está chamando abrirModalAjuste com os parâmetros corretos"
    
    print("✓ Botão de ajuste implementado corretamente")
    print("✓ Botão está na seção de solicitações pendentes")
    print("✓ Onclick chama abrirModalAjuste com request_id e amount")
    print("✓ Botão tem ícone de edição (fa-edit)")
    print("✓ Botão tem classe btn-warning")
    

def test_button_order():
    """Verifica se o botão de ajuste está na ordem correta (antes dos botões de aprovar/rejeitar)"""
    template_path = Path('templates/admin/solicitacoes_tokens.html')
    content = template_path.read_text(encoding='utf-8')
    
    # Encontrar a posição do botão de ajuste
    adjust_pos = content.find('abrirModalAjuste')
    approve_pos = content.find('action" value="approve')
    
    assert adjust_pos > 0, "Botão de ajuste não encontrado"
    assert approve_pos > 0, "Botão de aprovar não encontrado"
    assert adjust_pos < approve_pos, "Botão de ajuste deve vir antes do botão de aprovar"
    
    print("✓ Botão de ajuste está posicionado antes dos botões de aprovar/rejeitar")


def test_modal_exists():
    """Verifica se o modal de ajuste existe no template"""
    template_path = Path('templates/admin/solicitacoes_tokens.html')
    content = template_path.read_text(encoding='utf-8')
    
    assert 'ajustarQuantidadeModal' in content, "Modal de ajuste não encontrado"
    assert 'ajustarQuantidadeForm' in content, "Formulário de ajuste não encontrado"
    assert 'adjust_request_id' in content, "Campo request_id não encontrado"
    assert 'new_amount' in content, "Campo new_amount não encontrado"
    assert 'adjustment_reason' in content, "Campo adjustment_reason não encontrado"
    
    print("✓ Modal de ajuste existe no template")
    print("✓ Formulário de ajuste existe")
    print("✓ Todos os campos necessários estão presentes")


if __name__ == '__main__':
    print("Testando implementação do botão de ajuste...\n")
    
    try:
        test_adjust_button_in_template()
        print()
        test_button_order()
        print()
        test_modal_exists()
        print("\n✅ Todos os testes passaram!")
    except AssertionError as e:
        print(f"\n❌ Teste falhou: {e}")
        exit(1)
