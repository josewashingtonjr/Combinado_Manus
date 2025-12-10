"""
Teste de Validação do Form Helpers System
Verifica se o sistema de validação de formulários está funcionando corretamente
"""

import os
from pathlib import Path

def test_form_helpers_file_exists():
    """Verifica se o arquivo form-helpers.js foi criado"""
    file_path = Path('static/js/form-helpers.js')
    assert file_path.exists(), "Arquivo form-helpers.js não encontrado"
    print("✅ Arquivo form-helpers.js existe")

def test_form_helpers_content():
    """Verifica se o conteúdo do arquivo está correto"""
    file_path = Path('static/js/form-helpers.js')
    content = file_path.read_text(encoding='utf-8')
    
    # Verifica classe principal
    assert 'class FormHelpers' in content, "Classe FormHelpers não encontrada"
    print("✅ Classe FormHelpers encontrada")
    
    # Verifica validadores
    validadores_esperados = [
        'email',
        'telefone',
        'cpf',
        'cnpj',
        'valor',
        'required',
        'senha-forte',
        'confirmar-senha'
    ]
    
    for validador in validadores_esperados:
        assert f"'{validador}'" in content or f'"{validador}"' in content, \
            f"Validador '{validador}' não encontrado"
    print(f"✅ Todos os {len(validadores_esperados)} validadores encontrados")
    
    # Verifica máscaras
    mascaras_esperadas = [
        'telefone',
        'cpf',
        'cnpj',
        'cep',
        'valor',
        'data',
        'hora'
    ]
    
    for mascara in mascaras_esperadas:
        assert f"'{mascara}'" in content or f'"{mascara}"' in content, \
            f"Máscara '{mascara}' não encontrada"
    print(f"✅ Todas as {len(mascaras_esperadas)} máscaras encontradas")
    
    # Verifica métodos principais
    metodos_esperados = [
        'validateField',
        'validateForm',
        'applyMask',
        'updateFieldUI',
        'validateCPF',
        'validateCNPJ',
        'getCleanValue',
        'setMaskedValue'
    ]
    
    for metodo in metodos_esperados:
        assert metodo in content, f"Método '{metodo}' não encontrado"
    print(f"✅ Todos os {len(metodos_esperados)} métodos principais encontrados")
    
    # Verifica textos em português
    textos_ptbr = [
        'Digite um e-mail válido',
        'Este campo é obrigatório',
        'Digite um telefone válido',
        'CPF inválido',
        'CNPJ inválido',
        'As senhas não coincidem',
        'Por favor, corrija os erros no formulário'
    ]
    
    for texto in textos_ptbr:
        assert texto in content, f"Texto em português '{texto}' não encontrado"
    print(f"✅ Todos os {len(textos_ptbr)} textos em português encontrados")

def test_form_helpers_integration():
    """Verifica integração com outros sistemas"""
    file_path = Path('static/js/form-helpers.js')
    content = file_path.read_text(encoding='utf-8')
    
    # Verifica integração com toast
    assert 'window.toast' in content, "Integração com toast não encontrada"
    print("✅ Integração com toast feedback encontrada")
    
    # Verifica exportação global
    assert 'window.FormHelpers' in content, "Exportação global não encontrada"
    assert 'window.formHelpers' in content, "Instância global não encontrada"
    print("✅ Exportações globais encontradas")
    
    # Verifica inicialização automática
    assert 'DOMContentLoaded' in content, "Inicialização automática não encontrada"
    print("✅ Inicialização automática configurada")

def test_form_helpers_examples_file():
    """Verifica se o arquivo de exemplos foi criado"""
    file_path = Path('static/js/form-helpers-examples.html')
    assert file_path.exists(), "Arquivo de exemplos não encontrado"
    print("✅ Arquivo de exemplos existe")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Verifica exemplos de uso
    exemplos_esperados = [
        'data-validate',
        'data-mask',
        'telefone',
        'cpf',
        'valor',
        'senha-forte',
        'confirmar-senha',
        'required'
    ]
    
    for exemplo in exemplos_esperados:
        assert exemplo in content, f"Exemplo '{exemplo}' não encontrado"
    print(f"✅ Todos os {len(exemplos_esperados)} exemplos de uso encontrados")

def test_form_helpers_requirements():
    """Verifica se os requisitos foram atendidos"""
    file_path = Path('static/js/form-helpers.js')
    content = file_path.read_text(encoding='utf-8')
    
    # Requirement 6.1: Campos grandes (verificado via CSS)
    assert 'min-height: 44px' in content, "Altura mínima de campos não encontrada"
    print("✅ Requirement 6.1: Campos com altura mínima")
    
    # Requirement 6.2: Teclado apropriado
    assert 'inputMode' in content, "Configuração de inputMode não encontrada"
    assert "type = 'tel'" in content or 'type = "tel"' in content, "Tipo tel não encontrado"
    print("✅ Requirement 6.2: Teclado apropriado configurado")
    
    # Requirement 6.3: Validação em tempo real
    assert 'validateOnInput' in content, "Validação em tempo real não encontrada"
    assert 'validateOnBlur' in content, "Validação ao sair do campo não encontrada"
    print("✅ Requirement 6.3: Validação em tempo real implementada")
    
    # Requirement 6.4: Máscaras
    assert 'applyMask' in content, "Aplicação de máscaras não encontrada"
    assert 'telefone' in content and 'cpf' in content, "Máscaras brasileiras não encontradas"
    print("✅ Requirement 6.4: Máscaras implementadas")

def test_form_helpers_css():
    """Verifica se os estilos CSS foram incluídos"""
    file_path = Path('static/js/form-helpers.js')
    content = file_path.read_text(encoding='utf-8')
    
    # Verifica estilos de validação
    estilos_esperados = [
        '.is-invalid',
        '.is-valid',
        '.has-error',
        '.has-success',
        '.error-message',
        'border-color: #dc3545',
        'border-color: #28a745'
    ]
    
    for estilo in estilos_esperados:
        assert estilo in content, f"Estilo '{estilo}' não encontrado"
    print(f"✅ Todos os {len(estilos_esperados)} estilos CSS encontrados")
    
    # Verifica responsividade mobile
    assert '@media (max-width: 768px)' in content, "Media query mobile não encontrada"
    assert 'font-size: 16px' in content, "Fonte mínima para mobile não encontrada"
    print("✅ Estilos responsivos para mobile encontrados")

def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 TESTES DO FORM HELPERS SYSTEM")
    print("="*60 + "\n")
    
    tests = [
        ("Existência do Arquivo", test_form_helpers_file_exists),
        ("Conteúdo do Arquivo", test_form_helpers_content),
        ("Integração com Sistemas", test_form_helpers_integration),
        ("Arquivo de Exemplos", test_form_helpers_examples_file),
        ("Requisitos Atendidos", test_form_helpers_requirements),
        ("Estilos CSS", test_form_helpers_css)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Teste: {test_name}")
            print("-" * 60)
            test_func()
            passed += 1
            print(f"✅ {test_name}: PASSOU\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name}: FALHOU")
            print(f"   Erro: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERRO")
            print(f"   Erro: {e}\n")
    
    print("="*60)
    print(f"📊 RESULTADO FINAL")
    print("="*60)
    print(f"✅ Testes Passados: {passed}/{len(tests)}")
    print(f"❌ Testes Falhados: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n📝 Próximos passos:")
        print("   1. Abra static/js/form-helpers-examples.html no navegador")
        print("   2. Teste as validações e máscaras")
        print("   3. Integre o form-helpers.js nos templates")
        print("   4. Adicione data-validate e data-mask nos campos")
    else:
        print(f"\n⚠️  {failed} teste(s) falharam. Verifique os erros acima.")
    
    print("="*60 + "\n")
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
