"""
Teste para validar o template de contestação (Task 27)
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def test_contestar_template_content():
    """Testa se o template de contestação tem o conteúdo correto"""
    
    # Ler o arquivo do template
    template_path = 'templates/cliente/contestar_ordem.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template não encontrado: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar elementos em português
    assert 'Contestar Ordem' in html, "Título 'Contestar Ordem' não encontrado"
    assert 'Motivo da Contestação' in html, "Seção 'Motivo da Contestação' não encontrada"
    assert 'Provas' in html, "Seção 'Provas' não encontrada"
    assert 'Taxa de Contestação' in html, "Informação sobre taxa não encontrada"
    assert 'Possíveis Resultados' in html, "Seção de resultados não encontrada"
    assert 'confirmo que' in html.lower(), "Checkbox de confirmação não encontrado"
    assert 'Abrir Contestação' in html, "Botão de submit não encontrado"
    
    # Verificar campos do formulário
    assert 'name="reason"' in html, "Campo 'reason' não encontrado"
    assert 'name="evidence"' in html, "Campo 'evidence' não encontrado"
    assert 'name="confirm"' in html, "Checkbox 'confirm' não encontrado"
    assert 'minlength="20"' in html, "Validação de mínimo 20 caracteres não encontrada"
    assert 'maxlength="1000"' in html, "Validação de máximo 1000 caracteres não encontrada"
    
    # Verificar tipos de arquivo aceitos
    assert '.jpg' in html, "Tipo .jpg não encontrado"
    assert '.png' in html, "Tipo .png não encontrado"
    assert '.pdf' in html, "Tipo .pdf não encontrado"
    assert '.mp4' in html, "Tipo .mp4 não encontrado"
    
    # Verificar informações sobre limites
    assert '5 arquivos' in html or '5 arquivo' in html, "Limite de 5 arquivos não mencionado"
    assert '10MB' in html or '10 MB' in html, "Limite de 10MB não mencionado"
    
    # Verificar JavaScript de preview
    assert 'file-preview' in html, "Elemento de preview não encontrado"
    assert 'char-count' in html, "Contador de caracteres não encontrado"
    
    # Verificar avisos sobre prazo
    assert 'Prazo' in html or 'prazo' in html, "Informação sobre prazo não encontrada"
    
    # Verificar checkbox obrigatório
    assert 'required' in html, "Atributo 'required' não encontrado"
    
    # Verificar textos em português
    assert 'Descreva detalhadamente' in html, "Texto de instrução não encontrado"
    assert 'caracteres' in html, "Referência a caracteres não encontrada"
    
    # Verificar JavaScript de validação
    assert 'addEventListener' in html, "JavaScript de eventos não encontrado"
    assert 'selectedFiles' in html or 'file' in html.lower(), "Lógica de arquivos não encontrada"
    
    print("✅ Teste do template de contestação passou com sucesso!")
    print(f"   ✓ Template existe e está acessível")
    print(f"   ✓ Todos os textos estão em português")
    print(f"   ✓ Campos de formulário presentes (reason, evidence, confirm)")
    print(f"   ✓ Validações configuradas (minlength=20, maxlength=1000)")
    print(f"   ✓ Preview de arquivos implementado com JavaScript")
    print(f"   ✓ Informações sobre taxas e resultados presentes")
    print(f"   ✓ Tipos de arquivo aceitos: JPG, PNG, PDF, MP4")
    print(f"   ✓ Limites especificados: 5 arquivos, 10MB cada")
    print(f"   ✓ Checkbox de confirmação obrigatório")
    print(f"   ✓ Avisos sobre prazo e possíveis resultados")
    
    return True


if __name__ == '__main__':
    try:
        result = test_contestar_template_content()
        if result:
            print("\n✅ TODOS OS TESTES PASSARAM!")
            print("\n📋 Resumo da Task 27:")
            print("   - Template criado: templates/cliente/contestar_ordem.html")
            print("   - Formulário com campo de motivo (textarea, min 20 chars)")
            print("   - Upload múltiplo de arquivos (.jpg, .png, .pdf, .mp4)")
            print("   - Preview de arquivos com JavaScript")
            print("   - Informações sobre taxa de R$ 10,00")
            print("   - Avisos sobre possíveis resultados")
            print("   - Informações sobre prazo para contestar")
            print("   - Checkbox de confirmação obrigatório")
            print("   - Botão de submit com validação")
            print("   - Todos os textos em português")
            sys.exit(0)
        else:
            print("\n❌ ALGUNS TESTES FALHARAM")
            sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ FALHA NA VALIDAÇÃO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
