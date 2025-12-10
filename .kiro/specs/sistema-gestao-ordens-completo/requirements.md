# Requirements Document

## Introduction

Este documento especifica os requisitos para um sistema completo de gestão de ordens de serviço com dashboard centralizado, controle de status, prazos automáticos, sistema de cancelamento com multas e arbitragem de contestações. O sistema gerencia todo o ciclo de vida de uma ordem desde sua criação até a conclusão, incluindo fluxos alternativos de cancelamento e disputas.

## Glossary

- **Sistema**: O sistema de gestão de ordens de serviço
- **Cliente**: Usuário que solicita e paga pelo serviço
- **Prestador**: Usuário que executa o serviço
- **Admin**: Administrador da plataforma com poderes de arbitragem
- **Ordem**: Registro de um serviço a ser executado, criado a partir de um convite aceito
- **Dashboard**: Interface centralizada para visualização e gestão de ordens
- **Escrow**: Sistema de bloqueio de valores até a conclusão do serviço
- **Taxa de Contestação**: Valor fixo bloqueado como garantia, configurável pelo admin
- **Taxa de Cancelamento**: Multa percentual aplicada em cancelamentos, configurável pelo admin
- **Taxa da Plataforma**: Percentual cobrado sobre o valor do serviço, configurável pelo admin
- **Prazo de Confirmação**: Período de 36 horas para o cliente responder após conclusão
- **Confirmação Automática**: Processo que confirma a ordem após 36 horas sem resposta
- **Contestação**: Disputa aberta pelo cliente quando não concorda com a execução
- **Arbitragem**: Processo de decisão do admin sobre uma contestação

## Requirements

### Requirement 1: Dashboard Centralizado de Ordens

**User Story:** Como usuário (cliente ou prestador), quero visualizar todas as minhas ordens em um dashboard centralizado, para que eu possa acompanhar rapidamente o status de cada serviço.

#### Acceptance Criteria

1. WHEN o usuário acessa a rota de ordens, THE Sistema SHALL exibir um dashboard com todas as ordens do usuário
2. THE Sistema SHALL exibir estatísticas resumidas em cards incluindo total de ordens, ordens aguardando execução, ordens para confirmar, ordens concluídas, ordens canceladas e ordens contestadas
3. THE Sistema SHALL permitir filtrar ordens por status através de botões ou dropdown
4. THE Sistema SHALL exibir cada ordem em um card contendo título do serviço, nome da outra parte, valor, status visual com cor e ícone, data de criação e botões de ação contextual
5. THE Sistema SHALL atualizar automaticamente as estatísticas e lista de ordens a cada 30 segundos

### Requirement 2: Criação e Inicialização de Ordem

**User Story:** Como sistema, quero criar automaticamente uma ordem quando um convite for aceito, para que o serviço possa ser gerenciado através do fluxo de ordens.

#### Acceptance Criteria

1. WHEN um convite é aceito, THE Sistema SHALL criar uma ordem com status "aguardando_execucao"
2. THE Sistema SHALL bloquear o valor do serviço mais a taxa de contestação da carteira do cliente
3. THE Sistema SHALL bloquear a taxa de contestação da carteira do prestador como garantia
4. THE Sistema SHALL registrar a data de criação e a data limite para execução do serviço
5. THE Sistema SHALL notificar ambas as partes sobre a criação da ordem

### Requirement 3: Marcação de Serviço Concluído

**User Story:** Como prestador, quero marcar o serviço como concluído após executá-lo, para que o cliente possa confirmar e eu receba o pagamento.

#### Acceptance Criteria

1. WHEN o prestador clica em "Marcar como Concluído", THE Sistema SHALL mudar o status da ordem para "servico_executado"
2. THE Sistema SHALL registrar a data e hora de conclusão (completed_at)
3. THE Sistema SHALL calcular e registrar o prazo de confirmação como 36 horas após a conclusão (confirmation_deadline)
4. THE Sistema SHALL exibir um contador regressivo de 36 horas na interface do cliente
5. THE Sistema SHALL notificar o cliente informando que ele tem 36 horas para confirmar ou contestar
6. THE Sistema SHALL bloquear a opção de cancelamento para ambas as partes após a marcação de conclusão

### Requirement 4: Confirmação Manual pelo Cliente

**User Story:** Como cliente, quero confirmar manualmente que o serviço foi bem executado, para que o prestador receba o pagamento imediatamente.

#### Acceptance Criteria

1. WHEN o cliente clica em "Confirmar Serviço" dentro de 36 horas, THE Sistema SHALL mudar o status para "concluida"
2. THE Sistema SHALL transferir o valor do serviço menos a taxa da plataforma para a carteira do prestador
3. THE Sistema SHALL devolver a taxa de contestação para a carteira do cliente
4. THE Sistema SHALL devolver a taxa de contestação para a carteira do prestador
5. THE Sistema SHALL transferir a taxa da plataforma para a carteira do admin
6. THE Sistema SHALL registrar a data de confirmação e notificar ambas as partes

### Requirement 5: Confirmação Automática após 36 Horas

**User Story:** Como prestador, quero que a ordem seja automaticamente confirmada se o cliente não responder em 36 horas, para que eu não fique indefinidamente aguardando pagamento.

#### Acceptance Criteria

1. WHEN o prazo de confirmação (36 horas) expira sem resposta do cliente, THE Sistema SHALL automaticamente mudar o status para "concluida"
2. THE Sistema SHALL processar os pagamentos da mesma forma que uma confirmação manual
3. THE Sistema SHALL executar a verificação de ordens expiradas a cada hora através de um job automático
4. THE Sistema SHALL registrar no histórico que a confirmação foi automática
5. THE Sistema SHALL notificar ambas as partes sobre a confirmação automática
6. WHEN faltam 12 horas para a confirmação automática, THE Sistema SHALL enviar um lembrete ao cliente

### Requirement 6: Cancelamento de Ordem com Multa

**User Story:** Como usuário (cliente ou prestador), quero poder cancelar uma ordem antes da execução em caso de imprevistos, aceitando pagar uma multa pela parte prejudicada.

#### Acceptance Criteria

1. WHEN um usuário cancela uma ordem com status "aguardando_execucao", THE Sistema SHALL mudar o status para "cancelada"
2. THE Sistema SHALL calcular a multa como 10% do valor do serviço
3. THE Sistema SHALL transferir 50% da multa para a carteira da plataforma
4. THE Sistema SHALL transferir 50% da multa para a carteira da parte prejudicada
5. THE Sistema SHALL devolver o valor do serviço menos a multa para quem cancelou
6. THE Sistema SHALL devolver as taxas de contestação para ambas as partes
7. THE Sistema SHALL exigir que o usuário forneça um motivo para o cancelamento
8. THE Sistema SHALL bloquear o cancelamento se o status for diferente de "aguardando_execucao"

### Requirement 7: Abertura de Contestação

**User Story:** Como cliente, quero poder contestar um serviço que não foi executado adequadamente, para que um admin possa arbitrar e proteger meus direitos.

#### Acceptance Criteria

1. WHEN o cliente clica em "Contestar Serviço" dentro de 36 horas após conclusão, THE Sistema SHALL mudar o status para "contestada"
2. THE Sistema SHALL exigir que o cliente forneça uma descrição detalhada do motivo com mínimo de 20 caracteres
3. THE Sistema SHALL permitir que o cliente anexe provas em formato de imagem, vídeo ou documento
4. THE Sistema SHALL armazenar as URLs das provas no campo dispute_evidence
5. THE Sistema SHALL notificar o admin e o prestador sobre a contestação
6. THE Sistema SHALL bloquear a confirmação automática quando uma contestação for aberta
7. THE Sistema SHALL manter os valores em escrow até a resolução da contestação

### Requirement 8: Arbitragem de Contestação pelo Admin

**User Story:** Como admin, quero analisar contestações e tomar decisões baseadas nas provas apresentadas, para que disputas sejam resolvidas de forma justa.

#### Acceptance Criteria

1. WHEN o admin acessa uma contestação, THE Sistema SHALL exibir todas as provas e declarações de ambas as partes
2. WHEN o admin decide a favor do cliente, THE Sistema SHALL devolver o valor do serviço para o cliente, transferir a taxa de contestação do cliente para a plataforma, e não liberar pagamento para o prestador
3. WHEN o admin decide a favor do prestador, THE Sistema SHALL transferir o valor do serviço menos taxa da plataforma para o prestador, devolver a taxa de contestação do prestador, e transferir a taxa de contestação do cliente para a plataforma
4. THE Sistema SHALL mudar o status para "resolvida" após a decisão
5. THE Sistema SHALL registrar a decisão, o vencedor e as notas do admin
6. THE Sistema SHALL notificar ambas as partes sobre a decisão final

### Requirement 9: Visualização Detalhada de Ordem

**User Story:** Como usuário, quero visualizar todos os detalhes de uma ordem específica, para que eu possa acompanhar seu progresso e tomar ações necessárias.

#### Acceptance Criteria

1. WHEN o usuário clica em uma ordem, THE Sistema SHALL exibir uma página com todos os detalhes incluindo título, descrição, valor, status, datas relevantes e histórico
2. THE Sistema SHALL exibir o contador regressivo de 36 horas quando o status for "servico_executado"
3. THE Sistema SHALL exibir alertas visuais quando faltarem menos de 12 horas para confirmação automática
4. THE Sistema SHALL exibir botões de ação contextual baseados no status atual e no papel do usuário
5. THE Sistema SHALL exibir o cálculo detalhado de valores incluindo taxa da plataforma, taxa de contestação e valor líquido

### Requirement 10: Controle de Permissões por Papel

**User Story:** Como sistema, quero garantir que apenas usuários autorizados possam executar ações específicas, para que a segurança e integridade do processo sejam mantidas.

#### Acceptance Criteria

1. THE Sistema SHALL permitir que apenas o prestador marque a ordem como concluída
2. THE Sistema SHALL permitir que apenas o cliente confirme ou conteste o serviço
3. THE Sistema SHALL permitir que apenas o admin arbitre contestações
4. THE Sistema SHALL permitir que ambas as partes cancelem a ordem antes da conclusão
5. THE Sistema SHALL validar a propriedade da ordem antes de permitir qualquer ação
6. THE Sistema SHALL retornar erro 403 quando um usuário tentar executar ação não autorizada

### Requirement 11: Sistema de Notificações

**User Story:** Como usuário, quero receber notificações sobre eventos importantes nas minhas ordens, para que eu possa responder em tempo hábil.

#### Acceptance Criteria

1. WHEN uma ordem é criada, THE Sistema SHALL notificar ambas as partes
2. WHEN o prestador marca como concluído, THE Sistema SHALL notificar o cliente com destaque para o prazo de 36 horas
3. WHEN faltam 12 horas para confirmação automática, THE Sistema SHALL enviar lembrete ao cliente
4. WHEN uma ordem é confirmada automaticamente, THE Sistema SHALL notificar ambas as partes
5. WHEN uma ordem é cancelada, THE Sistema SHALL notificar a parte prejudicada
6. WHEN uma contestação é aberta, THE Sistema SHALL notificar o admin e o prestador
7. WHEN uma contestação é resolvida, THE Sistema SHALL notificar ambas as partes

### Requirement 12: Integridade Financeira

**User Story:** Como sistema, quero garantir que todas as transações financeiras sejam atômicas e rastreáveis, para que não haja perda ou duplicação de valores.

#### Acceptance Criteria

1. THE Sistema SHALL executar todas as transferências de valores dentro de uma transação atômica
2. WHEN uma transação falha, THE Sistema SHALL reverter todas as operações relacionadas
3. THE Sistema SHALL registrar cada transação com um ID único e rastreável
4. THE Sistema SHALL validar saldos antes de executar qualquer transferência
5. THE Sistema SHALL manter log detalhado de todas as operações financeiras
6. THE Sistema SHALL garantir que a soma de valores bloqueados mais valores disponíveis seja sempre consistente

### Requirement 13: Configuração Dinâmica de Taxas pelo Admin

**User Story:** Como admin, quero configurar e editar todas as taxas do sistema através de uma interface de configurações, para que eu possa ajustar os valores conforme necessário sem alterar código.

#### Acceptance Criteria

1. THE Sistema SHALL permitir que o admin configure a taxa da plataforma como percentual do valor do serviço
2. THE Sistema SHALL permitir que o admin configure a taxa de contestação como valor fixo
3. THE Sistema SHALL permitir que o admin configure a taxa de cancelamento como percentual do valor do serviço
4. WHEN o admin altera uma taxa, THE Sistema SHALL aplicar o novo valor apenas para ordens criadas após a alteração
5. WHEN o admin altera uma taxa, THE Sistema SHALL exibir o novo valor percentual em todos os avisos e cálculos do sistema
6. THE Sistema SHALL exibir para os usuários qual taxa será aplicada antes de criar uma ordem ou executar uma ação
7. THE Sistema SHALL armazenar as taxas vigentes no momento da criação de cada ordem para garantir consistência
8. THE Sistema SHALL validar que taxas percentuais estejam entre 0% e 100%
9. THE Sistema SHALL validar que taxas fixas sejam valores positivos

### Requirement 14: Responsividade e Atualização em Tempo Real

**User Story:** Como usuário, quero que o dashboard seja responsivo e atualize automaticamente, para que eu tenha informações sempre atualizadas sem precisar recarregar a página.

#### Acceptance Criteria

1. THE Sistema SHALL atualizar automaticamente o dashboard a cada 30 segundos
2. THE Sistema SHALL atualizar automaticamente a página de detalhes da ordem a cada 60 segundos quando o status for "servico_executado"
3. THE Sistema SHALL exibir o dashboard corretamente em dispositivos móveis com largura mínima de 320px
4. THE Sistema SHALL adaptar o layout de cards e botões para telas pequenas
5. THE Sistema SHALL manter a funcionalidade completa em todos os tamanhos de tela
