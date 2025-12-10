"""
Teste para verificar a funcionalidade JavaScript do modal de ajuste
"""
import pytest


def test_modal_ajuste_presente_no_template():
    """Verifica se o modal de ajuste está presente no template"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar se o modal está presente
    assert 'id="ajustarQuantidadeModal"' in html
    assert 'id="ajustarQuantidadeForm"' in html
    assert 'id="adjust_request_id"' in html
    assert 'id="original_amount"' in html
    assert 'id="new_amount"' in html
    assert 'id="adjustment_reason"' in html
    assert 'id="char_count"' in html


def test_funcoes_javascript_presentes_no_template():
    """Verifica se as funções JavaScript estão presentes no template"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar se as funções JavaScript estão presentes
    assert 'function abrirModalAjuste(' in html
    assert 'function updateTableAmount(' in html
    assert 'function showAlert(' in html
    assert 'function getCsrfToken(' in html
    
    # Verificar event listeners
    assert 'addEventListener(\'input\'' in html
    assert 'addEventListener(\'submit\'' in html


def test_estrutura_modal_ajuste():
    """Verifica a estrutura HTML do modal de ajuste"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar elementos do modal
    assert 'Ajustar Quantidade de Tokens' in html
    assert 'Valor Solicitado Original:' in html
    assert 'Nova Quantidade (R$)' in html
    assert 'Justificativa (Opcional)' in html
    assert 'maxlength="500"' in html
    assert '/500 caracteres' in html
    assert 'Salvar Ajuste' in html


def test_validacoes_html5_no_campo_new_amount():
    """Verifica se as validações HTML5 estão presentes no campo new_amount"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar atributos de validação no campo new_amount
    assert 'type="number"' in html
    assert 'step="0.01"' in html
    assert 'min="0.01"' in html
    assert 'required' in html


def test_contador_caracteres_justificativa():
    """Verifica se o contador de caracteres está configurado corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar contador de caracteres
    assert 'id="char_count"' in html
    assert '/500 caracteres' in html
    assert 'maxlength="500"' in html
    
    # Verificar event listener para atualizar contador
    assert 'adjustment_reason' in html
    assert 'addEventListener(\'input\'' in html


def test_fetch_api_configurado_corretamente():
    """Verifica se a chamada fetch API está configurada corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar configuração do fetch
    assert 'fetch(' in html
    assert 'method: \'POST\'' in html
    assert '\'Content-Type\': \'application/json\'' in html
    assert '\'X-CSRFToken\': getCsrfToken()' in html
    assert 'JSON.stringify(' in html
    assert 'new_amount:' in html
    assert 'adjustment_reason:' in html


def test_tratamento_resposta_sucesso():
    """Verifica se o tratamento de resposta de sucesso está implementado"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar tratamento de sucesso
    assert 'if (data.success)' in html
    assert 'modal.hide()' in html
    assert 'showAlert(\'success\'' in html
    assert 'updateTableAmount(' in html


def test_tratamento_resposta_erro():
    """Verifica se o tratamento de erro está implementado"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar tratamento de erro
    assert 'catch (error)' in html
    assert 'showAlert(\'error\'' in html


def test_funcao_show_alert_implementada():
    """Verifica se a função showAlert está implementada corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar implementação da função showAlert
    assert 'function showAlert(type, message)' in html
    assert 'alert-floating' in html
    assert "alertDiv.style.position = 'fixed'" in html
    assert "type === 'success' ? 'success' : 'danger'" in html
    assert 'fa-check-circle' in html
    assert 'fa-exclamation-circle' in html
    assert 'document.body.appendChild(alertDiv)' in html
    assert 'setTimeout' in html


def test_funcao_update_table_amount_implementada():
    """Verifica se a função updateTableAmount está implementada corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar implementação da função updateTableAmount
    assert 'function updateTableAmount(requestId, newAmount)' in html
    assert 'data-request-id' in html
    assert 'badge bg-warning' in html
    assert 'Ajustado' in html


def test_funcao_get_csrf_token_implementada():
    """Verifica se a função getCsrfToken está implementada corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar implementação da função getCsrfToken
    assert 'function getCsrfToken()' in html
    assert 'input[name="csrf_token"]' in html


def test_funcao_abrir_modal_ajuste_implementada():
    """Verifica se a função abrirModalAjuste está implementada corretamente"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar implementação da função abrirModalAjuste
    assert 'function abrirModalAjuste(requestId, currentAmount)' in html
    assert 'document.getElementById(\'adjust_request_id\').value = requestId' in html
    assert 'document.getElementById(\'original_amount\').textContent' in html
    assert 'document.getElementById(\'new_amount\').value = \'\'' in html
    assert 'document.getElementById(\'adjustment_reason\').value = \'\'' in html
    assert 'new bootstrap.Modal(' in html
    assert 'modal.show()' in html


def test_event_listener_contador_caracteres():
    """Verifica se o event listener do contador de caracteres está configurado"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar event listener
    assert 'adjustmentReasonField.addEventListener(\'input\'' in html
    assert 'charCount.textContent = this.value.length' in html


def test_handler_submit_formulario():
    """Verifica se o handler de submit do formulário está configurado"""
    with open('templates/admin/solicitacoes_tokens.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Verificar handler de submit
    assert 'ajustarForm.addEventListener(\'submit\'' in html
    assert 'e.preventDefault()' in html
    assert 'const requestId = document.getElementById(\'adjust_request_id\').value' in html
    assert 'const newAmount = document.getElementById(\'new_amount\').value' in html
    assert 'const reason = document.getElementById(\'adjustment_reason\').value' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
