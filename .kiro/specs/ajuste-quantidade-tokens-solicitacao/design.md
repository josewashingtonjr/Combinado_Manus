# Design Document

## Overview

Este documento descreve o design da funcionalidade de ajuste de quantidade de tokens em solicitações de compra. A solução permitirá que administradores corrijam discrepâncias entre o valor solicitado e o valor efetivamente pago antes de aprovar uma solicitação, mantendo um histórico completo de auditoria.

## Architecture

### Componentes Afetados

1. **Backend (Flask)**
   - Nova rota: `POST /admin/tokens/solicitacoes/<request_id>/ajustar`
   - Modificação na rota existente: `POST /admin/tokens/solicitacoes/<request_id>/processar`
   - Service layer: Lógica de ajuste e validação

2. **Frontend (HTML/JavaScript)**
   - Template: `templates/admin/solicitacoes_tokens.html`
   - Modal de ajuste de quantidade
   - JavaScript para interação com o modal

3. **Database**
   - Modelo existente: `TokenRequest` (sem alterações estruturais)
   - Campo utilizado: `admin_notes` para histórico de ajustes

### Fluxo de Dados

```
Admin visualiza solicitação pendente
    ↓
Admin clica em "Ajustar Quantidade"
    ↓
Modal exibe valor atual e campo editável
    ↓
Admin insere novo valor e justificativa (opcional)
    ↓
Sistema valida o novo valor (> 0)
    ↓
Sistema atualiza TokenRequest.amount
    ↓
Sistema adiciona registro em admin_notes
    ↓
Sistema retorna sucesso e atualiza interface
    ↓
Admin pode aprovar/rejeitar com valor ajustado
```

## Components and Interfaces

### 1. Nova Rota de Ajuste

**Endpoint:** `POST /admin/tokens/solicitacoes/<request_id>/ajustar`

**Parâmetros:**
- `request_id` (int): ID da solicitação a ser ajustada
- `new_amount` (Decimal): Nova quantidade de tokens
- `adjustment_reason` (string, opcional): Justificativa do ajuste

**Resposta de Sucesso (200):**
```json
{
  "success": true,
  "message": "Quantidade ajustada com sucesso",
  "old_amount": 100.00,
  "new_amount": 50.00,
  "request_id": 123
}
```

**Resposta de Erro (400):**
```json
{
  "success": false,
  "error": "Mensagem de erro específica"
}
```

**Validações:**
- Solicitação deve existir
- Solicitação deve estar com status 'pending'
- new_amount deve ser > 0
- new_amount deve ser diferente do amount atual
- Admin deve estar autenticado

### 2. Service Layer

**Função:** `AdminService.adjust_token_request_amount()`

```python
@staticmethod
def adjust_token_request_amount(request_id, new_amount, admin_id, reason=None):
    """
    Ajusta a quantidade de tokens de uma solicitação pendente
    
    Args:
        request_id (int): ID da solicitação
        new_amount (Decimal): Nova quantidade
        admin_id (int): ID do admin que está fazendo o ajuste
        reason (str, optional): Justificativa do ajuste
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'old_amount': Decimal,
            'new_amount': Decimal,
            'error': str (se success=False)
        }
    """
```

**Lógica:**
1. Buscar TokenRequest por ID
2. Validar que status == 'pending'
3. Validar que new_amount > 0
4. Validar que new_amount != amount atual
5. Armazenar old_amount
6. Atualizar amount com new_amount
7. Construir nota de ajuste com timestamp, admin_id, valores antigo/novo e reason
8. Adicionar nota ao admin_notes (preservando notas anteriores)
9. Commit da transação
10. Retornar resultado

### 3. Frontend - Modal de Ajuste

**Estrutura HTML:**
```html
<div class="modal fade" id="ajustarQuantidadeModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Ajustar Quantidade de Tokens</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form id="ajustarQuantidadeForm">
                <div class="modal-body">
                    <input type="hidden" id="adjust_request_id" name="request_id">
                    
                    <div class="alert alert-info">
                        <strong>Valor Solicitado Original:</strong> 
                        R$ <span id="original_amount">0.00</span>
                    </div>
                    
                    <div class="mb-3">
                        <label for="new_amount" class="form-label">
                            Nova Quantidade (R$) <span class="text-danger">*</span>
                        </label>
                        <input type="number" 
                               class="form-control" 
                               id="new_amount" 
                               name="new_amount" 
                               step="0.01" 
                               min="0.01" 
                               required>
                        <div class="form-text">
                            Insira o valor que corresponde ao pagamento efetivamente realizado
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="adjustment_reason" class="form-label">
                            Justificativa (Opcional)
                        </label>
                        <textarea class="form-control" 
                                  id="adjustment_reason" 
                                  name="adjustment_reason" 
                                  rows="3" 
                                  maxlength="500"
                                  placeholder="Ex: Comprovante mostra pagamento de apenas R$ 50,00"></textarea>
                        <div class="form-text">
                            <span id="char_count">0</span>/500 caracteres
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        Cancelar
                    </button>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-1"></i> Salvar Ajuste
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
```

**JavaScript:**
```javascript
function abrirModalAjuste(requestId, currentAmount) {
    // Preencher campos do modal
    document.getElementById('adjust_request_id').value = requestId;
    document.getElementById('original_amount').textContent = currentAmount.toFixed(2);
    document.getElementById('new_amount').value = '';
    document.getElementById('adjustment_reason').value = '';
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('ajustarQuantidadeModal'));
    modal.show();
}

// Handler do formulário
document.getElementById('ajustarQuantidadeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const requestId = document.getElementById('adjust_request_id').value;
    const newAmount = document.getElementById('new_amount').value;
    const reason = document.getElementById('adjustment_reason').value;
    
    try {
        const response = await fetch(`/admin/tokens/solicitacoes/${requestId}/ajustar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                new_amount: parseFloat(newAmount),
                adjustment_reason: reason
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Fechar modal
            bootstrap.Modal.getInstance(document.getElementById('ajustarQuantidadeModal')).hide();
            
            // Mostrar mensagem de sucesso
            showAlert('success', data.message);
            
            // Atualizar valor na tabela
            updateTableAmount(requestId, data.new_amount);
        } else {
            showAlert('error', data.error);
        }
    } catch (error) {
        showAlert('error', 'Erro ao ajustar quantidade: ' + error.message);
    }
});

// Contador de caracteres
document.getElementById('adjustment_reason').addEventListener('input', function() {
    document.getElementById('char_count').textContent = this.value.length;
});
```

### 4. Modificações na Tabela de Solicitações

**Adicionar coluna de ações:**
```html
<td>
    {% if solicitacao.status == 'pending' %}
    <div class="btn-group btn-group-sm" role="group">
        <!-- Botão de ajustar -->
        <button type="button" 
                class="btn btn-warning btn-sm" 
                onclick="abrirModalAjuste({{ solicitacao.id }}, {{ solicitacao.amount }})"
                title="Ajustar Quantidade">
            <i class="fas fa-edit"></i>
        </button>
        
        <!-- Botões existentes de aprovar/rejeitar -->
        <form method="POST" action="{{ url_for('admin.processar_solicitacao_token', request_id=solicitacao.id) }}" style="display: inline;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="hidden" name="action" value="approve">
            <button type="submit" class="btn btn-success btn-sm" 
                    onclick="return confirm('Aprovar esta solicitação?')"
                    title="Aprovar">
                <i class="fas fa-check"></i>
            </button>
        </form>
        
        <form method="POST" action="{{ url_for('admin.processar_solicitacao_token', request_id=solicitacao.id) }}" style="display: inline;">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <input type="hidden" name="action" value="reject">
            <button type="submit" class="btn btn-danger btn-sm" 
                    onclick="return confirm('Rejeitar esta solicitação?')"
                    title="Rejeitar">
                <i class="fas fa-times"></i>
            </button>
        </form>
        
        <button type="button" class="btn btn-info btn-sm" 
                onclick="verDetalhes({{ solicitacao.id }})"
                title="Ver Detalhes">
            <i class="fas fa-eye"></i>
        </button>
    </div>
    {% else %}
    <!-- Solicitação já processada -->
    <div class="text-muted">
        <small>
            Processada em {{ solicitacao.processed_at.strftime('%d/%m/%Y %H:%M') if solicitacao.processed_at else 'N/A' }}
        </small>
    </div>
    {% endif %}
</td>
```

**Indicador visual de ajuste:**
```html
<td>
    <strong class="text-success">R$ {{ "%.2f"|format(solicitacao.amount) }}</strong>
    {% if solicitacao.admin_notes and 'Quantidade ajustada' in solicitacao.admin_notes %}
    <span class="badge bg-warning text-dark ms-1" title="Quantidade foi ajustada">
        <i class="fas fa-edit"></i> Ajustado
    </span>
    {% endif %}
</td>
```

## Data Models

### TokenRequest (Existente - Sem Alterações)

O modelo `TokenRequest` já possui todos os campos necessários:

```python
class TokenRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(18, 2), nullable=False)  # ← Campo a ser ajustado
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)  # ← Campo para histórico de ajustes
    
    # Campos de comprovante
    payment_method = db.Column(db.String(50), nullable=True, default='pix')
    receipt_filename = db.Column(db.String(255), nullable=True)
    receipt_original_name = db.Column(db.String(255), nullable=True)
    receipt_uploaded_at = db.Column(db.DateTime, nullable=True)
```

**Formato das Notas de Ajuste:**
```
[AJUSTE] Quantidade ajustada de R$ 100.00 para R$ 50.00 em 20/11/2025 15:30 por Admin #1
Justificativa: Comprovante mostra pagamento de apenas R$ 50,00

[Notas anteriores preservadas aqui...]
```

## Error Handling

### Validações e Erros

1. **Solicitação não encontrada (404)**
   - Mensagem: "Solicitação não encontrada"
   - Ação: Redirecionar para lista de solicitações

2. **Solicitação não está pendente (400)**
   - Mensagem: "Apenas solicitações pendentes podem ser ajustadas"
   - Ação: Retornar erro JSON

3. **Valor inválido (400)**
   - Mensagem: "O novo valor deve ser maior que zero"
   - Ação: Retornar erro JSON

4. **Valor igual ao atual (400)**
   - Mensagem: "O novo valor deve ser diferente do valor atual"
   - Ação: Retornar erro JSON

5. **Admin não autenticado (401)**
   - Mensagem: "Autenticação necessária"
   - Ação: Redirecionar para login

6. **Erro de banco de dados (500)**
   - Mensagem: "Erro ao salvar ajuste. Tente novamente."
   - Ação: Rollback da transação e retornar erro JSON
   - Log: Registrar erro completo no log do sistema

### Tratamento de Exceções

```python
try:
    # Lógica de ajuste
    db.session.commit()
    return {'success': True, 'message': '...'}
except ValueError as e:
    db.session.rollback()
    logger.warning(f"Validação falhou ao ajustar solicitação {request_id}: {e}")
    return {'success': False, 'error': str(e)}
except Exception as e:
    db.session.rollback()
    logger.error(f"Erro ao ajustar solicitação {request_id}: {e}", exc_info=True)
    return {'success': False, 'error': 'Erro interno ao processar ajuste'}
```

## Testing Strategy

### Testes Unitários

1. **test_adjust_token_request_amount_success**
   - Cenário: Ajuste válido de quantidade
   - Verificar: amount atualizado, admin_notes contém registro, retorno de sucesso

2. **test_adjust_token_request_amount_invalid_status**
   - Cenário: Tentar ajustar solicitação aprovada/rejeitada
   - Verificar: Erro retornado, amount não alterado

3. **test_adjust_token_request_amount_invalid_value**
   - Cenário: Tentar ajustar com valor <= 0
   - Verificar: Erro de validação retornado

4. **test_adjust_token_request_amount_same_value**
   - Cenário: Tentar ajustar com valor igual ao atual
   - Verificar: Erro retornado

5. **test_adjust_token_request_amount_with_reason**
   - Cenário: Ajuste com justificativa
   - Verificar: Justificativa incluída nas admin_notes

6. **test_adjust_token_request_amount_preserves_notes**
   - Cenário: Ajustar solicitação que já tem admin_notes
   - Verificar: Notas anteriores preservadas

### Testes de Integração

1. **test_adjust_and_approve_flow**
   - Cenário: Ajustar quantidade e depois aprovar
   - Verificar: Tokens adicionados na quantidade ajustada

2. **test_adjust_route_authentication**
   - Cenário: Tentar ajustar sem autenticação
   - Verificar: Redirecionamento para login

3. **test_adjust_route_authorization**
   - Cenário: Usuário não-admin tenta ajustar
   - Verificar: Acesso negado

### Testes Manuais

1. **Interface do Modal**
   - Abrir modal de ajuste
   - Verificar exibição do valor original
   - Inserir novo valor e justificativa
   - Verificar contador de caracteres
   - Submeter formulário
   - Verificar atualização da tabela

2. **Validações Frontend**
   - Tentar submeter com valor vazio
   - Tentar submeter com valor negativo
   - Verificar mensagens de erro

3. **Fluxo Completo**
   - Criar solicitação como usuário
   - Fazer login como admin
   - Visualizar comprovante
   - Ajustar quantidade
   - Aprovar solicitação
   - Verificar saldo do usuário

## Security Considerations

1. **Autenticação e Autorização**
   - Apenas admins autenticados podem ajustar quantidades
   - Decorator `@admin_required` na rota

2. **Validação de Entrada**
   - Sanitização do campo `adjustment_reason`
   - Validação de tipo e range para `new_amount`
   - Proteção contra SQL injection (uso de ORM)

3. **CSRF Protection**
   - Token CSRF em todas as requisições POST
   - Validação no backend

4. **Auditoria**
   - Registro completo de quem fez o ajuste (admin_id)
   - Timestamp do ajuste
   - Valores antigo e novo preservados

5. **Rate Limiting**
   - Considerar limite de ajustes por minuto para evitar abuso
   - Implementar se necessário

## Performance Considerations

1. **Queries Otimizadas**
   - Busca de TokenRequest por ID (índice primário)
   - Sem joins complexos necessários

2. **Transações Atômicas**
   - Uso de transação para garantir consistência
   - Rollback em caso de erro

3. **Caching**
   - Não aplicável para esta funcionalidade (dados sempre atualizados)

4. **Frontend**
   - Modal carregado uma vez na página
   - Atualização dinâmica da tabela sem reload completo
   - Requisições AJAX para melhor UX

## Deployment Considerations

1. **Migração de Banco de Dados**
   - Não necessária (usa campos existentes)

2. **Compatibilidade**
   - Funcionalidade adicional, não quebra código existente
   - Solicitações antigas sem ajustes continuam funcionando normalmente

3. **Rollback**
   - Remover rota e código JavaScript
   - Dados existentes (admin_notes) permanecem íntegros

4. **Monitoramento**
   - Adicionar log de ajustes para análise
   - Monitorar frequência de ajustes para identificar padrões
