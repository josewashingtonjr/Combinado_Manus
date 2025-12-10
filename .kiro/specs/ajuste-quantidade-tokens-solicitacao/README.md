# Funcionalidade de Ajuste de Quantidade em Solicitações de Tokens

## Visão Geral

Esta funcionalidade permite que administradores ajustem a quantidade de tokens em solicitações pendentes antes de aprová-las. Isso é útil quando há discrepância entre o valor solicitado pelo usuário e o valor efetivamente pago (verificado através do comprovante).

## Contexto do Problema

Anteriormente, quando um usuário solicitava a compra de tokens (por exemplo, 100 tokens) mas o comprovante de pagamento mostrava um valor diferente (por exemplo, apenas 50 tokens), o administrador não tinha como corrigir essa discrepância. A única opção era rejeitar a solicitação e pedir ao usuário que criasse uma nova, gerando retrabalho e má experiência.

## Solução Implementada

A solução adiciona um botão "Ajustar Quantidade" na interface de gerenciamento de solicitações de tokens, que permite ao administrador:

1. **Visualizar o valor original** solicitado pelo usuário
2. **Inserir o novo valor** que corresponde ao pagamento efetivo
3. **Adicionar uma justificativa** (opcional) explicando o motivo do ajuste
4. **Preservar o histórico** de todas as alterações nas notas administrativas

## Componentes Implementados

### 1. Backend - Service Layer

**Arquivo:** `services/admin_service.py`

**Método:** `adjust_token_request_amount(request_id, new_amount, admin_id, reason=None)`

**Funcionalidade:**
- Valida que a solicitação existe e está com status 'pending'
- Valida que o novo valor é maior que zero e diferente do atual
- Atualiza o campo `amount` da solicitação
- Adiciona registro detalhado nas `admin_notes` com:
  - Valores antigo e novo
  - Data e hora do ajuste
  - ID e email do administrador
  - Justificativa (se fornecida)
- Preserva notas administrativas anteriores
- Registra log de auditoria

**Formato das Notas de Ajuste:**
```
[AJUSTE] Quantidade ajustada de R$ 100.00 para R$ 50.00 em 20/11/2025 15:30 por Admin #1 (admin@example.com)
Justificativa: Comprovante mostra pagamento de apenas R$ 50,00

[Notas anteriores preservadas aqui...]
```

### 2. Backend - Rota de API

**Arquivo:** `routes/admin_routes.py`

**Endpoint:** `POST /admin/tokens/solicitacoes/<request_id>/ajustar`

**Parâmetros JSON:**
```json
{
  "new_amount": 50.00,
  "adjustment_reason": "Comprovante mostra pagamento de apenas R$ 50,00"
}
```

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

**Resposta de Erro (400/404/500):**
```json
{
  "success": false,
  "error": "Mensagem de erro específica"
}
```

**Validações Implementadas:**
- Autenticação do administrador
- Solicitação deve existir
- Solicitação deve estar com status 'pending'
- Novo valor deve ser maior que zero
- Novo valor deve ser diferente do atual
- Justificativa limitada a 500 caracteres (se fornecida)
- Proteção CSRF

### 3. Frontend - Modal de Ajuste

**Arquivo:** `templates/admin/solicitacoes_tokens.html`

**Componentes do Modal:**
- **Cabeçalho:** Título "Ajustar Quantidade de Tokens"
- **Corpo:**
  - Alert informativo mostrando o valor original
  - Campo numérico para o novo valor (validação HTML5: required, min=0.01, step=0.01)
  - Textarea para justificativa (opcional, maxlength=500)
  - Contador de caracteres em tempo real
- **Rodapé:**
  - Botão "Cancelar" (fecha o modal)
  - Botão "Salvar Ajuste" (submete o formulário)

**JavaScript Implementado:**
- `abrirModalAjuste(requestId, currentAmount)`: Abre o modal e preenche os campos
- Handler de submit do formulário com fetch API
- `updateTableAmount(requestId, newAmount)`: Atualiza a tabela dinamicamente após ajuste
- `showAlert(type, message)`: Exibe alertas flutuantes de sucesso/erro
- `getCsrfToken()`: Obtém token CSRF para proteção
- Contador de caracteres para a justificativa

### 4. Frontend - Indicadores Visuais

**Melhorias na Tabela de Solicitações:**

1. **Badge "Ajustado":** Aparece ao lado do valor quando a solicitação foi ajustada
   - Cor: warning (amarelo)
   - Ícone: fa-edit
   - Tooltip: Mostra informações do ajuste

2. **Botão de Ajuste:** Aparece apenas para solicitações pendentes
   - Cor: warning (amarelo)
   - Ícone: fa-edit
   - Posicionado antes dos botões de aprovar/rejeitar

3. **Ícone de Comprovante:** Destaque visual quando há comprovante anexado
   - Badge verde com ícone fa-paperclip
   - Animação de pulse para chamar atenção
   - Botão "Ver Comprovante" abre em nova aba

## Fluxo de Uso

1. **Admin visualiza solicitações pendentes** na página `/admin/tokens/solicitacoes`
2. **Admin clica no botão "Ajustar Quantidade"** (ícone de edição amarelo)
3. **Modal é aberto** mostrando:
   - Valor original solicitado
   - Campo para inserir novo valor
   - Campo opcional para justificativa
4. **Admin insere o novo valor** e opcionalmente uma justificativa
5. **Admin clica em "Salvar Ajuste"**
6. **Sistema valida** os dados e atualiza a solicitação
7. **Tabela é atualizada dinamicamente** mostrando o novo valor e badge "Ajustado"
8. **Admin pode então aprovar** a solicitação com o valor corrigido

## Validações e Segurança

### Validações de Backend
- ✅ Solicitação deve existir
- ✅ Solicitação deve estar com status 'pending'
- ✅ Novo valor deve ser > 0
- ✅ Novo valor deve ser diferente do atual
- ✅ Justificativa limitada a 500 caracteres
- ✅ Admin deve estar autenticado
- ✅ Proteção CSRF

### Validações de Frontend
- ✅ Campo de valor é obrigatório (HTML5 required)
- ✅ Valor mínimo de 0.01 (HTML5 min)
- ✅ Incremento de 0.01 (HTML5 step)
- ✅ Contador de caracteres para justificativa
- ✅ Limite de 500 caracteres na justificativa

### Segurança
- ✅ Autenticação via decorator `@admin_required`
- ✅ Proteção CSRF em todas as requisições POST
- ✅ Sanitização de entrada (justificativa)
- ✅ Validação de tipos (Decimal para valores monetários)
- ✅ Tratamento de exceções com rollback de transação
- ✅ Logs de auditoria para todas as operações

## Auditoria e Rastreabilidade

Todas as operações de ajuste são registradas em múltiplos níveis:

1. **Notas Administrativas (`admin_notes`):**
   - Formato estruturado com tag [AJUSTE]
   - Valores antigo e novo
   - Data e hora precisa
   - ID e email do administrador
   - Justificativa (se fornecida)

2. **Logs do Sistema:**
   - Registro em `logs/sistema_combinado.log`
   - Nível INFO para operações bem-sucedidas
   - Nível WARNING para validações falhadas
   - Nível ERROR para erros inesperados

3. **Indicadores Visuais:**
   - Badge "Ajustado" na interface
   - Tooltip com informações do ajuste
   - Histórico preservado nas notas

## Testes Implementados

### Testes Unitários (`tests/test_admin_service_adjust_token_request.py`)
- ✅ `test_adjust_token_request_amount_success`: Ajuste válido
- ✅ `test_adjust_token_request_amount_invalid_status`: Tentar ajustar solicitação não-pendente
- ✅ `test_adjust_token_request_amount_invalid_value`: Valor <= 0
- ✅ `test_adjust_token_request_amount_same_value`: Valor igual ao atual
- ✅ `test_adjust_token_request_amount_with_reason`: Ajuste com justificativa
- ✅ `test_adjust_token_request_amount_preserves_notes`: Preservação de notas anteriores

### Testes de Integração (`tests/test_adjust_token_request_integration.py`)
- ✅ `test_adjust_and_approve_flow`: Fluxo completo de ajuste e aprovação
- ✅ `test_adjust_route_authentication`: Verificação de autenticação
- ✅ `test_adjust_route_authorization`: Verificação de autorização
- ✅ `test_adjust_route_validation`: Validações de entrada

### Testes de Interface (`tests/test_adjust_modal_javascript.py`)
- ✅ Verificação da estrutura HTML do modal
- ✅ Verificação dos campos do formulário
- ✅ Verificação das funções JavaScript

## Exemplos de Uso

### Exemplo 1: Ajuste Simples
```
Situação: Usuário solicitou 100 tokens mas pagou apenas 50
Ação: Admin ajusta para 50 tokens
Resultado: Solicitação atualizada, badge "Ajustado" aparece, admin pode aprovar
```

### Exemplo 2: Ajuste com Justificativa
```
Situação: Usuário solicitou 200 tokens mas comprovante mostra 150
Ação: Admin ajusta para 150 tokens com justificativa "Comprovante mostra PIX de R$ 150,00"
Resultado: Ajuste registrado com justificativa nas notas administrativas
```

### Exemplo 3: Múltiplos Ajustes
```
Situação: Admin ajusta valor duas vezes (primeiro erro de digitação)
Resultado: Ambos os ajustes são registrados nas notas, preservando histórico completo
```

## Manutenção e Evolução

### Possíveis Melhorias Futuras
- [ ] Notificação automática ao usuário quando valor é ajustado
- [ ] Histórico visual de ajustes na interface (timeline)
- [ ] Sugestão automática de valor baseado em padrões de pagamento
- [ ] Integração com sistema de pagamento para validação automática
- [ ] Relatório de ajustes realizados (estatísticas)

### Pontos de Atenção
- O ajuste só é permitido para solicitações com status 'pending'
- Após ajuste, o status permanece 'pending' para permitir aprovação/rejeição
- Notas administrativas crescem com cada ajuste (considerar limite no futuro)
- Valores são armazenados como Decimal para precisão monetária

## Requisitos Atendidos

Esta implementação atende completamente aos requisitos especificados em `requirements.md`:

- ✅ **Requirement 1:** Visualização e edição de quantidade antes de aprovar
- ✅ **Requirement 2:** Preservação de histórico de ajustes
- ✅ **Requirement 3:** Justificativa opcional para ajustes
- ✅ **Requirement 4:** Alertas visuais sobre discrepâncias
- ✅ **Requirement 5:** Restrição de ajustes apenas para solicitações pendentes

## Suporte e Documentação

Para mais informações, consulte:
- `requirements.md`: Requisitos detalhados
- `design.md`: Decisões de design e arquitetura
- `tasks.md`: Lista de tarefas de implementação
- Código-fonte comentado em `services/admin_service.py` e `routes/admin_routes.py`

## Contato

Para dúvidas ou sugestões sobre esta funcionalidade, consulte a equipe de desenvolvimento.
