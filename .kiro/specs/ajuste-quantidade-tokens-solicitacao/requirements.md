# Requirements Document

## Introduction

Este documento especifica os requisitos para implementar a funcionalidade de ajuste de quantidade de tokens em solicitações de compra. Atualmente, quando um usuário solicita a compra de tokens (por exemplo, 100 tokens) mas o admin verifica que o pagamento foi feito por uma quantidade diferente (por exemplo, apenas 50 tokens), o sistema não permite ajustar o valor. O admin precisa poder corrigir a quantidade solicitada para corresponder ao valor efetivamente pago antes de aprovar a solicitação.

## Glossary

- **Sistema**: A plataforma web de gestão de tokens e ordens de serviço
- **Admin**: Usuário administrador com permissões para gerenciar solicitações de tokens
- **TokenRequest**: Modelo de dados que representa uma solicitação de compra de tokens
- **Solicitação**: Pedido de compra de tokens feito por um usuário
- **Quantidade Ajustada**: Valor corrigido de tokens que corresponde ao pagamento efetivamente realizado
- **Comprovante**: Arquivo de imagem ou PDF enviado pelo usuário como prova de pagamento

## Requirements

### Requirement 1

**User Story:** Como administrador, eu quero poder visualizar e editar a quantidade de tokens solicitada antes de aprovar, para que eu possa corrigir discrepâncias entre o valor solicitado e o valor efetivamente pago.

#### Acceptance Criteria

1. WHEN THE Admin visualiza uma solicitação pendente, THE Sistema SHALL exibir um botão ou link "Ajustar Quantidade" ao lado dos botões de aprovar e rejeitar
2. WHEN THE Admin clica em "Ajustar Quantidade", THE Sistema SHALL exibir um modal ou formulário com o valor atual e um campo editável para o novo valor
3. WHEN THE Admin insere um novo valor de quantidade, THE Sistema SHALL validar que o valor é maior que zero
4. WHEN THE Admin confirma o ajuste, THE Sistema SHALL atualizar o campo `amount` do TokenRequest com o novo valor
5. WHEN o ajuste é salvo com sucesso, THE Sistema SHALL registrar a alteração nas notas administrativas (`admin_notes`) incluindo o valor original e o valor ajustado

### Requirement 2

**User Story:** Como administrador, eu quero que o histórico de ajustes seja preservado, para que eu possa auditar todas as modificações feitas nas solicitações.

#### Acceptance Criteria

1. WHEN THE Admin ajusta a quantidade de uma solicitação, THE Sistema SHALL adicionar uma entrada nas `admin_notes` com formato "Quantidade ajustada de R$ X para R$ Y em [data/hora] por Admin [ID]"
2. WHEN THE Admin visualiza os detalhes de uma solicitação ajustada, THE Sistema SHALL exibir claramente o valor original e o valor ajustado
3. WHEN uma solicitação é aprovada após ajuste, THE Sistema SHALL adicionar tokens na quantidade ajustada (não na quantidade original)
4. WHEN THE Admin visualiza o histórico de uma solicitação, THE Sistema SHALL preservar todas as notas administrativas anteriores ao adicionar novas

### Requirement 3

**User Story:** Como administrador, eu quero poder adicionar uma justificativa ao ajustar a quantidade, para que fique documentado o motivo da alteração.

#### Acceptance Criteria

1. WHEN THE Admin ajusta a quantidade, THE Sistema SHALL exibir um campo opcional de texto para justificativa
2. WHEN THE Admin fornece uma justificativa, THE Sistema SHALL incluir essa justificativa nas `admin_notes` junto com o registro do ajuste
3. WHEN THE Admin não fornece justificativa, THE Sistema SHALL permitir o ajuste mesmo assim, registrando apenas os valores alterados
4. WHEN a justificativa é fornecida, THE Sistema SHALL limitar o texto a 500 caracteres

### Requirement 4

**User Story:** Como administrador, eu quero que o sistema me alerte sobre discrepâncias comuns, para que eu possa identificar rapidamente solicitações que precisam de ajuste.

#### Acceptance Criteria

1. WHEN THE Admin visualiza a lista de solicitações pendentes, THE Sistema SHALL destacar visualmente solicitações com valores comuns de discrepância (múltiplos de 10, 50, 100)
2. WHEN uma solicitação tem comprovante anexado, THE Sistema SHALL exibir um ícone indicando que há comprovante disponível para verificação
3. WHEN THE Admin visualiza o comprovante, THE Sistema SHALL manter o modal de ajuste acessível para facilitar a correção imediata
4. WHEN há múltiplas solicitações do mesmo usuário, THE Sistema SHALL agrupar visualmente essas solicitações na lista

### Requirement 5

**User Story:** Como administrador, eu quero que apenas solicitações pendentes possam ser ajustadas, para que não haja modificações em solicitações já processadas.

#### Acceptance Criteria

1. WHEN uma solicitação tem status 'approved', THE Sistema SHALL ocultar o botão "Ajustar Quantidade"
2. WHEN uma solicitação tem status 'rejected', THE Sistema SHALL ocultar o botão "Ajustar Quantidade"
3. WHEN uma solicitação tem status 'pending', THE Sistema SHALL exibir o botão "Ajustar Quantidade"
4. WHEN THE Admin tenta ajustar uma solicitação não-pendente via requisição direta, THE Sistema SHALL retornar erro 400 com mensagem "Apenas solicitações pendentes podem ser ajustadas"
5. WHEN o ajuste é bem-sucedido, THE Sistema SHALL manter o status como 'pending' para permitir aprovação ou rejeição posterior
