# Requirements Document

## Introduction

Esta especificação define as correções necessárias no fluxo de propostas de alteração de convites. O sistema atual apresenta problemas críticos onde:
1. Quando o prestador propõe alteração, o convite não fica bloqueado para aceitação até aprovação do cliente
2. Quando o cliente rejeita a proposta, o convite não retorna corretamente ao estado original para ambas as partes
3. Quando o cliente aceita a proposta, o valor não é atualizado corretamente nas interfaces do cliente e prestador
4. O prestador consegue aceitar o convite mesmo com proposta pendente de aprovação

## Glossary

- **Sistema_Convite**: O sistema responsável por gerenciar convites entre clientes e prestadores
- **Proposta_Alteracao**: Modificação de valor sugerida pelo prestador
- **Cliente**: Usuário que cria convites e contrata serviços
- **Prestador**: Usuário que recebe convites e executa serviços
- **Valor_Original**: Valor inicial definido pelo cliente no convite
- **Valor_Proposto**: Novo valor sugerido pelo prestador
- **Valor_Efetivo**: Valor atual do convite após proposta aceita
- **Estado_Convite**: Status atual do convite no fluxo de propostas
- **Botao_Aceitar**: Botão que permite ao prestador aceitar o convite
- **Interface_Cliente**: Tela onde o cliente visualiza e gerencia seus convites
- **Interface_Prestador**: Tela onde o prestador visualiza e gerencia convites recebidos

## Requirements

### Requirement 1

**User Story:** Como um prestador, quando eu propor alteração de valor, o botão de aceitar convite deve ser bloqueado até o cliente responder, para que eu não aceite com o valor errado

#### Acceptance Criteria

1. WHEN um prestador submete uma Proposta_Alteracao, THE Sistema_Convite SHALL desabilitar o Botao_Aceitar imediatamente
2. THE Sistema_Convite SHALL exibir mensagem "Aguardando aprovação do cliente" no lugar do Botao_Aceitar
3. THE Sistema_Convite SHALL mostrar o Valor_Proposto claramente na Interface_Prestador
4. THE Sistema_Convite SHALL impedir qualquer tentativa de aceitar o convite via API enquanto proposta está pendente
5. THE Sistema_Convite SHALL manter o botão desabilitado até que o cliente aprove ou rejeite a proposta

### Requirement 2

**User Story:** Como um cliente, quando eu rejeitar uma proposta, o convite deve retornar ao estado original para mim e para o prestador, para que possamos continuar com o valor inicial

#### Acceptance Criteria

1. WHEN um cliente rejeita uma Proposta_Alteracao, THE Sistema_Convite SHALL limpar o campo has_active_proposal do convite
2. THE Sistema_Convite SHALL limpar o campo current_proposal_id do convite
3. THE Sistema_Convite SHALL limpar o campo effective_value do convite
4. THE Sistema_Convite SHALL transicionar o convite para estado PENDENTE
5. THE Sistema_Convite SHALL habilitar o Botao_Aceitar na Interface_Prestador com o Valor_Original

### Requirement 3

**User Story:** Como um cliente, quando eu aceitar uma proposta, o novo valor deve aparecer corretamente na minha interface, para que eu saiba quanto será cobrado

#### Acceptance Criteria

1. WHEN um cliente aceita uma Proposta_Alteracao, THE Sistema_Convite SHALL atualizar o campo effective_value com o Valor_Proposto
2. THE Sistema_Convite SHALL exibir o Valor_Efetivo como valor principal na Interface_Cliente
3. THE Sistema_Convite SHALL mostrar o Valor_Original como referência histórica
4. THE Sistema_Convite SHALL calcular e exibir a diferença entre valores
5. THE Sistema_Convite SHALL atualizar todos os cálculos de saldo com o Valor_Efetivo

### Requirement 4

**User Story:** Como um prestador, quando o cliente aceitar minha proposta, o novo valor deve aparecer na minha interface e o botão de aceitar deve ser habilitado, para que eu possa aceitar o convite com o valor correto

#### Acceptance Criteria

1. WHEN um cliente aceita uma Proposta_Alteracao, THE Sistema_Convite SHALL habilitar o Botao_Aceitar na Interface_Prestador
2. THE Sistema_Convite SHALL exibir o Valor_Efetivo como valor principal na Interface_Prestador
3. THE Sistema_Convite SHALL mostrar mensagem "Proposta aceita! Você pode aceitar o convite"
4. THE Sistema_Convite SHALL atualizar o estado do convite para PROPOSTA_ACEITA
5. THE Sistema_Convite SHALL notificar o prestador sobre a aceitação da proposta

### Requirement 5

**User Story:** Como um prestador, quando o cliente rejeitar minha proposta, o convite deve voltar ao estado original e eu devo poder aceitar com o valor inicial, para que eu possa decidir se aceito ou não

#### Acceptance Criteria

1. WHEN um cliente rejeita uma Proposta_Alteracao, THE Sistema_Convite SHALL habilitar o Botao_Aceitar na Interface_Prestador
2. THE Sistema_Convite SHALL exibir o Valor_Original como valor do convite
3. THE Sistema_Convite SHALL remover qualquer indicação de proposta pendente
4. THE Sistema_Convite SHALL notificar o prestador sobre a rejeição
5. THE Sistema_Convite SHALL permitir que o prestador aceite o convite com o Valor_Original

### Requirement 6

**User Story:** Como um prestador, quando eu aceitar um convite após proposta aprovada, a ordem de serviço deve ser criada com o valor correto, para que o pagamento seja pelo valor acordado

#### Acceptance Criteria

1. WHEN um prestador aceita um convite com proposta aprovada, THE Sistema_Convite SHALL criar ordem de serviço com o Valor_Efetivo
2. THE Sistema_Convite SHALL reservar o Valor_Efetivo do saldo do cliente
3. THE Sistema_Convite SHALL incluir referência à proposta aceita na ordem de serviço
4. THE Sistema_Convite SHALL registrar histórico completo da negociação
5. THE Sistema_Convite SHALL validar que o cliente tem saldo suficiente para o Valor_Efetivo

### Requirement 7

**User Story:** Como um cliente, quando uma proposta estiver pendente, eu devo ver claramente as opções de aceitar ou rejeitar, para que eu possa tomar uma decisão informada

#### Acceptance Criteria

1. WHEN uma Proposta_Alteracao está pendente, THE Sistema_Convite SHALL exibir card destacado com a proposta
2. THE Sistema_Convite SHALL mostrar comparação visual entre Valor_Original e Valor_Proposto
3. THE Sistema_Convite SHALL exibir botões "Aceitar Proposta" e "Rejeitar Proposta" claramente
4. THE Sistema_Convite SHALL mostrar justificativa do prestador
5. THE Sistema_Convite SHALL verificar saldo automaticamente para aumentos de valor

### Requirement 8

**User Story:** Como um prestador, quando eu cancelar minha proposta, o convite deve voltar ao estado original, para que eu possa aceitar com o valor inicial se desejar

#### Acceptance Criteria

1. WHEN um prestador cancela sua Proposta_Alteracao, THE Sistema_Convite SHALL limpar has_active_proposal
2. THE Sistema_Convite SHALL limpar current_proposal_id
3. THE Sistema_Convite SHALL limpar effective_value
4. THE Sistema_Convite SHALL habilitar o Botao_Aceitar com Valor_Original
5. THE Sistema_Convite SHALL notificar o cliente sobre o cancelamento

### Requirement 9

**User Story:** Como um usuário do sistema, eu quero que as transições de estado sejam consistentes, para que não haja estados inválidos ou inconsistentes

#### Acceptance Criteria

1. THE Sistema_Convite SHALL validar todas as transições de estado antes de executá-las
2. THE Sistema_Convite SHALL usar transações atômicas para mudanças de estado
3. THE Sistema_Convite SHALL reverter mudanças em caso de erro
4. THE Sistema_Convite SHALL registrar log de auditoria para todas as transições
5. THE Sistema_Convite SHALL garantir que apenas uma proposta ativa existe por convite

### Requirement 10

**User Story:** Como um desenvolvedor, eu quero que o gerenciador de estados limpe corretamente os campos de proposta, para que não haja dados órfãos no banco

#### Acceptance Criteria

1. WHEN o estado transiciona para PENDENTE após rejeição, THE Sistema_Convite SHALL executar clear_active_proposal()
2. WHEN o estado transiciona para PENDENTE após cancelamento, THE Sistema_Convite SHALL executar clear_active_proposal()
3. WHEN o estado transiciona para PROPOSTA_ACEITA, THE Sistema_Convite SHALL manter current_proposal_id mas limpar has_active_proposal
4. THE Sistema_Convite SHALL garantir que effective_value é atualizado corretamente
5. THE Sistema_Convite SHALL validar integridade dos dados após cada transição
