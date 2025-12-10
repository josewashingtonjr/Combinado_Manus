# Requirements Document

## Introduction

Este documento especifica os requisitos para corrigir o fluxo de aceitação de convites e criação automática de ordens de serviço. Atualmente, quando ambas as partes (cliente e prestador) aceitam um convite, o sistema não está criando automaticamente a ordem de serviço nem bloqueando os valores para pagamento. Além disso, as dashboards não estão exibindo corretamente as ordens em aberto e os fundos bloqueados.

## Glossary

- **Sistema**: A plataforma de gestão de ordens de serviço
- **Cliente**: Usuário que cria convites e solicita serviços
- **Prestador**: Usuário que aceita convites e executa serviços
- **Convite**: Proposta de serviço enviada pelo cliente ao prestador
- **Ordem**: Contrato de serviço ativo com valores bloqueados em escrow
- **Escrow**: Sistema de bloqueio de fundos até conclusão do serviço
- **Dashboard**: Painel principal de visualização do usuário
- **Fundos Bloqueados**: Valores retidos em escrow durante execução da ordem

## Requirements

### Requirement 1: Criação Automática de Ordem após Aceitação Mútua

**User Story:** Como cliente ou prestador, eu quero que o sistema crie automaticamente uma ordem de serviço quando ambas as partes aceitarem o convite, para que o trabalho possa começar imediatamente.

#### Acceptance Criteria

1. WHEN o cliente aceita um convite que já foi aceito pelo prestador, THEN THE Sistema SHALL criar automaticamente uma ordem de serviço com status 'aceita'
2. WHEN o prestador aceita um convite que já foi aceito pelo cliente, THEN THE Sistema SHALL criar automaticamente uma ordem de serviço com status 'aceita'
3. WHEN uma ordem é criada automaticamente, THEN THE Sistema SHALL bloquear o valor do serviço no escrow do cliente
4. WHEN uma ordem é criada automaticamente, THEN THE Sistema SHALL bloquear a taxa de contestação no escrow do prestador
5. WHEN uma ordem é criada automaticamente, THEN THE Sistema SHALL atualizar o status do convite para 'convertido'

### Requirement 2: Bloqueio Automático de Valores

**User Story:** Como administrador do sistema, eu quero que os valores sejam bloqueados automaticamente em escrow quando a ordem for criada, para garantir a segurança financeira da transação.

#### Acceptance Criteria

1. WHEN uma ordem é criada a partir de um convite aceito, THEN THE Sistema SHALL transferir o valor efetivo do serviço do saldo do cliente para o escrow
2. WHEN uma ordem é criada a partir de um convite aceito, THEN THE Sistema SHALL transferir a taxa de contestação do saldo do prestador para o escrow
3. IF o cliente não possui saldo suficiente, THEN THE Sistema SHALL impedir a criação da ordem e exibir mensagem de erro clara
4. IF o prestador não possui saldo suficiente para a taxa, THEN THE Sistema SHALL impedir a criação da ordem e exibir mensagem de erro clara
5. WHEN valores são bloqueados, THEN THE Sistema SHALL registrar transações de escrow com IDs únicos rastreáveis

### Requirement 3: Visualização de Ordens em Aberto na Dashboard do Cliente

**User Story:** Como cliente, eu quero ver todas as minhas ordens em aberto na dashboard principal, para acompanhar o progresso dos serviços contratados.

#### Acceptance Criteria

1. WHEN o cliente acessa sua dashboard, THEN THE Sistema SHALL exibir todas as ordens com status 'aceita', 'em_andamento' ou 'aguardando_confirmacao'
2. WHEN o cliente visualiza uma ordem em aberto, THEN THE Sistema SHALL exibir o título, valor, prestador, status e data de entrega
3. WHEN o cliente visualiza uma ordem em aberto, THEN THE Sistema SHALL exibir o valor bloqueado em escrow para aquela ordem
4. WHEN o cliente visualiza ordens em aberto, THEN THE Sistema SHALL ordenar por data de criação (mais recentes primeiro)
5. WHEN não há ordens em aberto, THEN THE Sistema SHALL exibir mensagem informativa clara

### Requirement 4: Visualização de Ordens em Aberto na Dashboard do Prestador

**User Story:** Como prestador, eu quero ver todas as minhas ordens em aberto na dashboard principal, para gerenciar os serviços que preciso executar.

#### Acceptance Criteria

1. WHEN o prestador acessa sua dashboard, THEN THE Sistema SHALL exibir todas as ordens onde ele é o prestador com status 'aceita', 'em_andamento' ou 'aguardando_confirmacao'
2. WHEN o prestador visualiza uma ordem em aberto, THEN THE Sistema SHALL exibir o título, valor, cliente, status e data de entrega
3. WHEN o prestador visualiza uma ordem em aberto, THEN THE Sistema SHALL exibir ações disponíveis (marcar como concluído, cancelar, etc.)
4. WHEN o prestador visualiza ordens em aberto, THEN THE Sistema SHALL ordenar por data de entrega (mais urgentes primeiro)
5. WHEN não há ordens em aberto, THEN THE Sistema SHALL exibir mensagem informativa clara

### Requirement 5: Visualização de Fundos Bloqueados

**User Story:** Como cliente ou prestador, eu quero ver claramente quanto dos meus fundos está bloqueado em escrow, para entender minha disponibilidade financeira.

#### Acceptance Criteria

1. WHEN o cliente acessa sua dashboard, THEN THE Sistema SHALL exibir o saldo disponível e o saldo bloqueado em escrow separadamente
2. WHEN o prestador acessa sua dashboard, THEN THE Sistema SHALL exibir o saldo disponível e o saldo bloqueado em escrow separadamente
3. WHEN o usuário visualiza fundos bloqueados, THEN THE Sistema SHALL exibir um detalhamento por ordem (valor bloqueado por cada ordem ativa)
4. WHEN o usuário clica em um valor bloqueado, THEN THE Sistema SHALL navegar para os detalhes da ordem correspondente
5. WHEN fundos são liberados do escrow, THEN THE Sistema SHALL atualizar a visualização em tempo real

### Requirement 6: Notificações de Criação de Ordem

**User Story:** Como cliente ou prestador, eu quero ser notificado quando uma ordem for criada automaticamente, para saber que o serviço está oficialmente iniciado.

#### Acceptance Criteria

1. WHEN uma ordem é criada automaticamente, THEN THE Sistema SHALL enviar notificação ao cliente informando a criação da ordem
2. WHEN uma ordem é criada automaticamente, THEN THE Sistema SHALL enviar notificação ao prestador informando a criação da ordem
3. WHEN uma notificação de ordem criada é enviada, THEN THE Sistema SHALL incluir número da ordem, valor e data de entrega
4. WHEN uma notificação de ordem criada é enviada, THEN THE Sistema SHALL incluir link direto para visualizar a ordem
5. WHEN o bloqueio de valores falha, THEN THE Sistema SHALL notificar ambas as partes sobre o erro e próximos passos

### Requirement 7: Tratamento de Erros no Fluxo de Conversão

**User Story:** Como administrador do sistema, eu quero que erros no processo de conversão de convite para ordem sejam tratados adequadamente, para evitar estados inconsistentes.

#### Acceptance Criteria

1. IF a criação da ordem falha após aceitação mútua, THEN THE Sistema SHALL reverter o status do convite para 'aceito'
2. IF o bloqueio de valores falha, THEN THE Sistema SHALL cancelar a criação da ordem e manter o convite como 'aceito'
3. WHEN ocorre um erro na conversão, THEN THE Sistema SHALL registrar o erro em log com detalhes completos
4. WHEN ocorre um erro na conversão, THEN THE Sistema SHALL exibir mensagem de erro clara ao usuário com ação sugerida
5. WHEN uma transação de escrow falha, THEN THE Sistema SHALL garantir rollback completo sem deixar valores inconsistentes

### Requirement 8: Validação de Saldo Antes da Aceitação

**User Story:** Como cliente ou prestador, eu quero ser avisado antes de aceitar um convite se não tenho saldo suficiente, para evitar erros após a aceitação.

#### Acceptance Criteria

1. WHEN o cliente tenta aceitar um convite, THEN THE Sistema SHALL validar se possui saldo suficiente para o valor do serviço
2. WHEN o prestador tenta aceitar um convite, THEN THE Sistema SHALL validar se possui saldo suficiente para a taxa de contestação
3. IF o saldo é insuficiente, THEN THE Sistema SHALL exibir mensagem clara indicando o valor necessário e o saldo atual
4. IF o saldo é insuficiente, THEN THE Sistema SHALL impedir a aceitação do convite
5. WHEN a validação de saldo é bem-sucedida, THEN THE Sistema SHALL permitir a aceitação do convite

### Requirement 9: Histórico de Conversão de Convite para Ordem

**User Story:** Como administrador do sistema, eu quero rastrear quando e como convites foram convertidos em ordens, para auditoria e resolução de problemas.

#### Acceptance Criteria

1. WHEN um convite é convertido em ordem, THEN THE Sistema SHALL registrar timestamp da conversão
2. WHEN um convite é convertido em ordem, THEN THE Sistema SHALL registrar qual usuário completou a aceitação mútua
3. WHEN um convite é convertido em ordem, THEN THE Sistema SHALL manter referência bidirecional entre convite e ordem
4. WHEN um convite é convertido em ordem, THEN THE Sistema SHALL preservar histórico de propostas se aplicável
5. WHEN um administrador consulta uma ordem, THEN THE Sistema SHALL exibir o convite original que a gerou

### Requirement 10: Atualização em Tempo Real das Dashboards

**User Story:** Como cliente ou prestador, eu quero que minha dashboard seja atualizada automaticamente quando uma ordem for criada, para ver as informações mais recentes sem recarregar a página.

#### Acceptance Criteria

1. WHEN uma ordem é criada, THEN THE Sistema SHALL atualizar a dashboard do cliente em tempo real
2. WHEN uma ordem é criada, THEN THE Sistema SHALL atualizar a dashboard do prestador em tempo real
3. WHEN fundos são bloqueados, THEN THE Sistema SHALL atualizar a visualização de saldo em tempo real
4. WHEN o status de uma ordem muda, THEN THE Sistema SHALL atualizar a lista de ordens em aberto em tempo real
5. WHEN a conexão em tempo real falha, THEN THE Sistema SHALL fornecer botão de atualização manual
