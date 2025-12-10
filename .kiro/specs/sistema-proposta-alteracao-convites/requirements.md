# Requirements Document

## Introduction

Esta especificação define as correções necessárias no sistema de propostas de alteração de convites para resolver problemas lógicos críticos. O sistema atual permite que prestadores proponham alterações de valor sem considerar adequadamente o impacto no saldo do cliente e sem implementar um fluxo de aprovação apropriado.

## Glossary

- **Sistema_Convite**: O sistema responsável por gerenciar convites entre clientes e prestadores
- **Proposta_Alteracao**: Modificação de valor ou condições sugerida pelo prestador
- **Cliente**: Usuário que cria convites e contrata serviços
- **Prestador**: Usuário que recebe convites e executa serviços
- **Valor_Original**: Valor inicial definido pelo cliente no convite
- **Valor_Proposto**: Novo valor sugerido pelo prestador na proposta de alteração
- **Taxa_Contestacao**: Taxa adicional que o cliente deve ter disponível para contestações
- **Saldo_Cliente**: Quantidade de tokens disponível na carteira do cliente
- **Status_Proposta**: Estado da proposta (pendente, aceita, rejeitada)
- **Ordem_Servico**: Contrato formal gerado após aceitação final do convite

## Requirements

### Requirement 1

**User Story:** Como um cliente, eu quero ser notificado quando um prestador propor alteração de valor, para que eu possa decidir se aceito ou rejeito a nova proposta

#### Acceptance Criteria

1. WHEN um prestador submete uma Proposta_Alteracao, THE Sistema_Convite SHALL notificar o Cliente imediatamente
2. THE Sistema_Convite SHALL exibir claramente o Valor_Original e o Valor_Proposto lado a lado
3. THE Sistema_Convite SHALL calcular e exibir a diferença entre os valores (positiva ou negativa)
4. THE Sistema_Convite SHALL mostrar o Status_Proposta como "aguardando aprovação do cliente"
5. THE Sistema_Convite SHALL incluir justificativa do prestador para a alteração proposta

### Requirement 2

**User Story:** Como um cliente, eu quero poder aceitar ou rejeitar propostas de alteração, para que eu tenha controle sobre os custos do serviço

#### Acceptance Criteria

1. WHEN um cliente visualiza uma Proposta_Alteracao, THE Sistema_Convite SHALL exibir botões "Aceitar Proposta" e "Rejeitar Proposta"
2. WHEN um cliente clica em "Rejeitar Proposta", THE Sistema_Convite SHALL retornar o convite ao estado original
3. WHEN um cliente rejeita uma proposta, THE Sistema_Convite SHALL notificar o prestador sobre a rejeição
4. THE Sistema_Convite SHALL permitir que o cliente adicione comentários ao rejeitar uma proposta
5. THE Sistema_Convite SHALL registrar todas as ações de aprovação/rejeição com timestamp

### Requirement 3

**User Story:** Como um cliente, eu quero verificar se tenho saldo suficiente antes de aceitar uma proposta de aumento, para que eu não aceite algo que não posso pagar

#### Acceptance Criteria

1. WHEN o Valor_Proposto é maior que o Valor_Original, THE Sistema_Convite SHALL verificar se o Saldo_Cliente é suficiente
2. THE Sistema_Convite SHALL calcular o valor total necessário (Valor_Proposto + Taxa_Contestacao)
3. IF o Saldo_Cliente é insuficiente, THEN THE Sistema_Convite SHALL exibir mensagem de saldo insuficiente
4. WHEN o saldo é insuficiente, THE Sistema_Convite SHALL exibir botão "Adicionar Saldo" junto com o valor necessário
5. THE Sistema_Convite SHALL bloquear a aceitação da proposta até que o saldo seja suficiente

### Requirement 4

**User Story:** Como um cliente, eu quero poder adicionar saldo diretamente quando aceitar uma proposta de aumento, para que o processo seja mais fluido

#### Acceptance Criteria

1. WHEN um cliente tem saldo insuficiente para uma proposta, THE Sistema_Convite SHALL oferecer opção de adicionar saldo
2. THE Sistema_Convite SHALL calcular automaticamente o valor mínimo necessário para adicionar
3. WHEN um cliente adiciona saldo suficiente, THE Sistema_Convite SHALL permitir aceitar a proposta imediatamente
4. THE Sistema_Convite SHALL confirmar a transação de adição de saldo antes de processar a aceitação
5. THE Sistema_Convite SHALL registrar a adição de saldo como parte do processo de aceitação da proposta

### Requirement 5

**User Story:** Como um prestador, eu quero que o convite seja bloqueado para aceitação após propor alteração, para que o cliente primeiro aprove a mudança

#### Acceptance Criteria

1. WHEN um prestador submete uma Proposta_Alteracao, THE Sistema_Convite SHALL bloquear o botão "Aceitar Convite"
2. THE Sistema_Convite SHALL exibir mensagem "Aguardando aprovação da proposta pelo cliente"
3. THE Sistema_Convite SHALL mostrar o Valor_Proposto em vez do Valor_Original na interface do prestador
4. WHILE uma proposta está pendente, THE Sistema_Convite SHALL impedir a criação de novas propostas
5. THE Sistema_Convite SHALL permitir que o prestador cancele sua proposta e retorne ao estado original

### Requirement 6

**User Story:** Como um prestador, eu quero ver o status correto do convite após propor alteração, para que eu saiba se posso aceitar ou não

#### Acceptance Criteria

1. WHEN uma Proposta_Alteracao está pendente, THE Sistema_Convite SHALL exibir status "Proposta Enviada - Aguardando Cliente"
2. WHEN o cliente aceita a proposta, THE Sistema_Convite SHALL atualizar o status para "Proposta Aceita - Pode Aceitar Convite"
3. WHEN o cliente rejeita a proposta, THE Sistema_Convite SHALL retornar ao status "Convite Disponível"
4. THE Sistema_Convite SHALL exibir o valor correto (original ou proposto aceito) em todas as interfaces
5. THE Sistema_Convite SHALL notificar o prestador sobre mudanças de status da proposta

### Requirement 7

**User Story:** Como um prestador, eu quero poder aceitar o convite apenas após o cliente aprovar minha proposta, para que a Ordem_Servico seja gerada com o valor correto

#### Acceptance Criteria

1. WHILE uma proposta está pendente de aprovação, THE Sistema_Convite SHALL desabilitar o botão "Aceitar Convite"
2. WHEN o cliente aprova uma proposta, THE Sistema_Convite SHALL habilitar novamente o botão "Aceitar Convite"
3. WHEN o prestador aceita um convite com proposta aprovada, THE Sistema_Convite SHALL gerar a Ordem_Servico com o Valor_Proposto
4. THE Sistema_Convite SHALL reservar o valor correto (proposto e aprovado) do Saldo_Cliente
5. THE Sistema_Convite SHALL incluir histórico da proposta na Ordem_Servico gerada

### Requirement 8

**User Story:** Como um administrador do sistema, eu quero rastrear todas as propostas de alteração, para que eu possa monitorar o uso da funcionalidade

#### Acceptance Criteria

1. THE Sistema_Convite SHALL registrar todas as Proposta_Alteracao em log de auditoria
2. THE Sistema_Convite SHALL armazenar histórico completo de propostas por convite
3. THE Sistema_Convite SHALL incluir timestamps, valores originais, propostos e justificativas
4. THE Sistema_Convite SHALL permitir consulta de estatísticas de propostas (aceitas/rejeitadas)
5. THE Sistema_Convite SHALL alertar sobre padrões suspeitos de propostas (muitos aumentos, etc.)

### Requirement 9

**User Story:** Como um usuário do sistema, eu quero que as notificações sobre propostas sejam claras e acionáveis, para que eu entenda o que preciso fazer

#### Acceptance Criteria

1. THE Sistema_Convite SHALL enviar notificação imediata quando uma proposta é criada
2. THE Sistema_Convite SHALL incluir valores original e proposto na notificação
3. THE Sistema_Convite SHALL fornecer links diretos para visualizar e responder à proposta
4. THE Sistema_Convite SHALL usar linguagem clara sobre as ações disponíveis
5. THE Sistema_Convite SHALL notificar ambas as partes sobre mudanças de status da proposta