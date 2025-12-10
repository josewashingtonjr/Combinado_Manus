# Implementation Plan

- [x] 1. Implementar service layer para ajuste de quantidade
  - Criar método `AdminService.adjust_token_request_amount()` com validações completas
  - Implementar lógica de atualização do campo `amount`
  - Implementar construção e adição de notas de ajuste em `admin_notes`
  - Garantir preservação de notas administrativas anteriores
  - _Requirements: 1.4, 1.5, 2.1, 2.4, 3.2, 3.3, 5.5_

- [x] 2. Criar rota de ajuste de quantidade
  - Adicionar rota `POST /admin/tokens/solicitacoes/<request_id>/ajustar` em `routes/admin_routes.py`
  - Implementar decorator `@admin_required` para autenticação
  - Implementar validação de parâmetros (request_id, new_amount, adjustment_reason)
  - Implementar chamada ao `AdminService.adjust_token_request_amount()`
  - Implementar retorno JSON com sucesso/erro
  - Implementar tratamento de exceções com rollback
  - _Requirements: 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4_

- [x] 3. Implementar modal de ajuste no frontend
  - Adicionar estrutura HTML do modal em `templates/admin/solicitacoes_tokens.html`
  - Implementar campos: valor original (readonly), novo valor (input), justificativa (textarea)
  - Implementar contador de caracteres para justificativa (limite 500)
  - Implementar validação HTML5 (required, min, step para valores decimais)
  - _Requirements: 1.2, 3.1, 3.4_

- [x] 4. Implementar JavaScript para interação com modal
  - Criar função `abrirModalAjuste(requestId, currentAmount)` para abrir modal
  - Implementar handler de submit do formulário com fetch API
  - Implementar função `updateTableAmount(requestId, newAmount)` para atualizar tabela dinamicamente
  - Implementar função `showAlert(type, message)` para feedback visual
  - Implementar função `getCsrfToken()` para proteção CSRF
  - Adicionar event listener para contador de caracteres
  - _Requirements: 1.1, 1.2, 1.4, 3.4_

- [x] 5. Adicionar botão de ajuste na tabela de solicitações
  - Modificar coluna de ações em `templates/admin/solicitacoes_tokens.html`
  - Adicionar botão "Ajustar Quantidade" com ícone de edição
  - Implementar condicional para exibir apenas em solicitações pendentes
  - Adicionar atributo `onclick` chamando `abrirModalAjuste()`
  - _Requirements: 1.1, 5.1, 5.2, 5.3_

- [x] 6. Implementar indicadores visuais de ajuste
  - Adicionar badge "Ajustado" na coluna de valor quando houver ajuste
  - Implementar verificação de presença de "Quantidade ajustada" em `admin_notes`
  - Adicionar tooltip com informações do ajuste
  - Estilizar badge com cor de destaque (warning)
  - _Requirements: 2.2, 4.1_

- [x] 7. Implementar melhorias visuais para comprovantes
  - Adicionar ícone destacado quando há comprovante anexado
  - Melhorar botão de visualização de comprovante
  - Garantir que modal de ajuste permaneça acessível após visualizar comprovante
  - _Requirements: 4.2, 4.3_

- [x] 8. Criar testes unitários para service layer
  - Escrever `test_adjust_token_request_amount_success()`
  - Escrever `test_adjust_token_request_amount_invalid_status()`
  - Escrever `test_adjust_token_request_amount_invalid_value()`
  - Escrever `test_adjust_token_request_amount_same_value()`
  - Escrever `test_adjust_token_request_amount_with_reason()`
  - Escrever `test_adjust_token_request_amount_preserves_notes()`
  - _Requirements: 1.3, 1.4, 1.5, 2.4, 3.2, 3.3, 5.4, 5.5_

- [x] 9. Criar testes de integração
  - Escrever `test_adjust_and_approve_flow()` para fluxo completo
  - Escrever `test_adjust_route_authentication()` para verificar autenticação
  - Escrever `test_adjust_route_authorization()` para verificar autorização
  - Escrever `test_adjust_route_validation()` para validações de entrada
  - _Requirements: 2.3, 5.1, 5.2, 5.3, 5.4_

- [x] 10. Documentar funcionalidade
  - Adicionar comentários no código explicando lógica de ajuste
  - Documentar formato das notas de ajuste em admin_notes
  - Criar README.md na pasta da spec com resumo da funcionalidade
  - _Requirements: 2.1, 2.2_
