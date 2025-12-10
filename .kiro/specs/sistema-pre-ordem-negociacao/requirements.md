# Requirements Document

## Introduction

Este documento especifica a implementação de um sistema de pré-ordem para resolver conflitos lógicos no fluxo atual de convites e ordens. Atualmente, quando um convite é aceito, uma ordem de serviço é criada imediatamente, mas a aba "Convites" ainda permite modificações, criando conflito entre duas abas controlando o mesmo processo. A solução proposta introduz uma pré-ordem como estágio intermediário de negociação, onde ambas as partes podem ajustar condições antes da conversão em ordem definitiva.

## Glossary

- **Sistema**: A plataforma de gestão de ordens de serviço
- **Cliente**: Usuário que cria convites e solicita serviços
- **Prestador**: Usuário que aceita convites e executa serviços
- **Convite**: Proposta inicial de serviço enviada por um usuário a outro
- **Pre_Ordem**: Estágio intermediário de negociação após aceitação do convite
- **Ordem**: Contrato de serviço definitivo com valores bloqueados em escrow
- **Escrow**: Sistema de bloqueio de fundos até conclusão do serviço
- **Aceitacao_Mutua**: Quando ambas as partes concordam com os termos da pré-ordem
- **Proposta_Alteracao**: Modificação de valor ou condições sugerida durante a pré-ordem
- **Saldo_Disponivel**: Quantidade de tokens disponível na carteira do usuário
- **Valor_Acordado**: Valor final negociado e aceito por ambas as partes

## Requirements

### Requirement 1: Criação de Pré-Ordem após Aceitação de Convite

**User Story:** Como usuário (cliente ou prestador), quando eu aceitar um convite, quero que seja criada uma pré-ordem em vez de uma ordem definitiva, para que eu possa negociar os detalhes antes do compromisso final.

#### Acceptance Criteria

1. WHEN um usuário aceita um convite, THE Sistema SHALL criar uma Pre_Ordem com status 'em_negociacao'
2. WHEN uma Pre_Ordem é criada, THE Sistema SHALL copiar todos os dados do convite (título, descrição, valor, prazo)
3. WHEN uma Pre_Ordem é criada, THE Sistema SHALL marcar o convite como 'convertido_pre_ordem'
4. WHEN uma Pre_Ordem é criada, THE Sistema SHALL notificar ambas as partes sobre a criação
5. WHEN uma Pre_Ordem é criada, THE Sistema SHALL NOT bloquear valores em escrow

### Requirement 2: Negociação de Valor na Pré-Ordem

**User Story:** Como cliente ou prestador, quero poder propor alterações de valor durante a pré-ordem, para que possamos chegar a um acordo justo antes de criar a ordem definitiva.

#### Acceptance Criteria

1. WHILE uma Pre_Ordem está em negociação, THE Sistema SHALL permitir que qualquer parte proponha novo valor
2. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL notificar a outra parte imediatamente
3. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL exibir valor original e valor proposto lado a lado
4. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL incluir campo obrigatório de justificativa
5. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL atualizar o status da Pre_Ordem para 'aguardando_resposta'

### Requirement 3: Modificação de Condições na Pré-Ordem

**User Story:** Como cliente ou prestador, quero poder modificar descrição, prazo e outros detalhes durante a pré-ordem, para que todos os aspectos do serviço sejam acordados mutuamente.

#### Acceptance Criteria

1. WHILE uma Pre_Ordem está em negociação, THE Sistema SHALL permitir edição de descrição do serviço
2. WHILE uma Pre_Ordem está em negociação, THE Sistema SHALL permitir edição de prazo de entrega
3. WHEN uma modificação é proposta, THE Sistema SHALL exibir comparação entre valores originais e propostos
4. WHEN uma modificação é proposta, THE Sistema SHALL requerer aprovação da outra parte
5. WHEN uma modificação é proposta, THE Sistema SHALL registrar histórico completo de alterações

### Requirement 4: Aceitação de Propostas na Pré-Ordem

**User Story:** Como usuário que recebe uma proposta de alteração, quero poder aceitar ou rejeitar claramente, para que a negociação avance ou retorne ao estado anterior.

#### Acceptance Criteria

1. WHEN um usuário recebe uma Proposta_Alteracao, THE Sistema SHALL exibir botões "Aceitar" e "Rejeitar" claramente
2. WHEN um usuário aceita uma proposta, THE Sistema SHALL atualizar a Pre_Ordem com os novos valores
3. WHEN um usuário aceita uma proposta, THE Sistema SHALL marcar a proposta como 'aceita' no histórico
4. WHEN um usuário rejeita uma proposta, THE Sistema SHALL manter os valores anteriores da Pre_Ordem
5. WHEN um usuário rejeita uma proposta, THE Sistema SHALL permitir nova rodada de negociação

### Requirement 5: Conversão de Pré-Ordem em Ordem Definitiva

**User Story:** Como cliente ou prestador, quando ambos concordarmos com todos os termos da pré-ordem, quero que ela seja convertida automaticamente em ordem definitiva, para que o serviço possa começar oficialmente.

#### Acceptance Criteria

1. WHEN ambas as partes aceitam os termos da Pre_Ordem, THE Sistema SHALL verificar Aceitacao_Mutua
2. WHEN Aceitacao_Mutua é confirmada, THE Sistema SHALL validar que o Cliente possui Saldo_Disponivel suficiente
3. WHEN Aceitacao_Mutua é confirmada, THE Sistema SHALL validar que o Prestador possui saldo para taxa de contestação
4. WHEN validações são bem-sucedidas, THE Sistema SHALL criar Ordem com status 'aceita'
5. WHEN a Ordem é criada, THE Sistema SHALL bloquear valores em escrow automaticamente

### Requirement 6: Bloqueio de Valores Apenas na Conversão

**User Story:** Como cliente ou prestador, quero que meus tokens sejam bloqueados apenas quando a ordem definitiva for criada, para que eu mantenha liquidez durante a negociação.

#### Acceptance Criteria

1. WHILE uma Pre_Ordem está em negociação, THE Sistema SHALL NOT bloquear valores em escrow
2. WHEN a Pre_Ordem é convertida em Ordem, THE Sistema SHALL bloquear o Valor_Acordado do Cliente em escrow
3. WHEN a Pre_Ordem é convertida em Ordem, THE Sistema SHALL bloquear a taxa de contestação do Prestador em escrow
4. IF o Cliente não possui saldo suficiente no momento da conversão, THE Sistema SHALL impedir a criação da Ordem
5. IF o Prestador não possui saldo suficiente no momento da conversão, THE Sistema SHALL impedir a criação da Ordem

### Requirement 7: Validação de Saldo Antes da Aceitação Mútua

**User Story:** Como cliente, quero ser avisado se não tenho saldo suficiente antes de aceitar os termos finais, para que eu possa adicionar saldo antes de confirmar.

#### Acceptance Criteria

1. WHEN o Cliente tenta aceitar os termos finais da Pre_Ordem, THE Sistema SHALL validar Saldo_Disponivel
2. IF o saldo é insuficiente, THE Sistema SHALL exibir mensagem clara com valor necessário e saldo atual
3. IF o saldo é insuficiente, THE Sistema SHALL exibir botão "Adicionar Saldo" com valor sugerido
4. WHEN o Cliente adiciona saldo suficiente, THE Sistema SHALL permitir aceitar os termos finais
5. WHEN o Cliente aceita os termos finais, THE Sistema SHALL marcar sua aceitação na Pre_Ordem

### Requirement 8: Cancelamento de Pré-Ordem

**User Story:** Como cliente ou prestador, quero poder cancelar a pré-ordem se não chegarmos a um acordo, para que o processo seja encerrado sem criar ordem definitiva.

#### Acceptance Criteria

1. WHILE uma Pre_Ordem está em negociação, THE Sistema SHALL permitir que qualquer parte cancele
2. WHEN uma Pre_Ordem é cancelada, THE Sistema SHALL solicitar motivo do cancelamento
3. WHEN uma Pre_Ordem é cancelada, THE Sistema SHALL notificar a outra parte imediatamente
4. WHEN uma Pre_Ordem é cancelada, THE Sistema SHALL atualizar status para 'cancelada'
5. WHEN uma Pre_Ordem é cancelada, THE Sistema SHALL NOT criar Ordem definitiva

### Requirement 9: Visualização de Pré-Ordens na Dashboard

**User Story:** Como cliente ou prestador, quero ver todas as minhas pré-ordens em negociação na dashboard, para que eu possa acompanhar e responder às propostas pendentes.

#### Acceptance Criteria

1. WHEN um usuário acessa sua dashboard, THE Sistema SHALL exibir seção "Pré-Ordens em Negociação"
2. WHEN um usuário visualiza pré-ordens, THE Sistema SHALL exibir título, valor atual, outra parte e status
3. WHEN uma Pre_Ordem tem proposta pendente, THE Sistema SHALL exibir indicador visual destacado
4. WHEN um usuário clica em uma Pre_Ordem, THE Sistema SHALL navegar para página de detalhes e negociação
5. WHEN não há pré-ordens ativas, THE Sistema SHALL exibir mensagem informativa

### Requirement 10: Histórico de Negociação na Pré-Ordem

**User Story:** Como cliente ou prestador, quero ver o histórico completo de propostas e alterações na pré-ordem, para que eu entenda como chegamos aos termos atuais.

#### Acceptance Criteria

1. WHEN um usuário visualiza uma Pre_Ordem, THE Sistema SHALL exibir timeline de todas as alterações
2. THE Sistema SHALL exibir cada proposta com timestamp, autor, valores e justificativa
3. THE Sistema SHALL exibir status de cada proposta (aceita, rejeitada, pendente)
4. THE Sistema SHALL destacar visualmente o valor atual acordado
5. THE Sistema SHALL permitir expandir/colapsar detalhes de cada proposta no histórico

### Requirement 11: Notificações de Eventos da Pré-Ordem

**User Story:** Como cliente ou prestador, quero receber notificações sobre eventos importantes na pré-ordem, para que eu possa responder rapidamente às propostas.

#### Acceptance Criteria

1. WHEN uma Pre_Ordem é criada, THE Sistema SHALL notificar ambas as partes
2. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL notificar a outra parte imediatamente
3. WHEN uma proposta é aceita ou rejeitada, THE Sistema SHALL notificar o autor da proposta
4. WHEN Aceitacao_Mutua é alcançada, THE Sistema SHALL notificar ambas as partes sobre criação da Ordem
5. WHEN uma Pre_Ordem é cancelada, THE Sistema SHALL notificar a outra parte com o motivo

### Requirement 12: Separação de Responsabilidades entre Convites e Pré-Ordens

**User Story:** Como usuário do sistema, quero que a aba "Convites" seja apenas para aceitar/rejeitar convites iniciais, e toda negociação aconteça na aba "Pré-Ordens", para evitar confusão.

#### Acceptance Criteria

1. WHEN um convite é convertido em Pre_Ordem, THE Sistema SHALL remover opções de modificação da aba "Convites"
2. THE Sistema SHALL exibir convites convertidos com status "Convertido em Pré-Ordem" e link para a pré-ordem
3. THE Sistema SHALL permitir apenas visualização de convites convertidos na aba "Convites"
4. THE Sistema SHALL centralizar todas as funcionalidades de negociação na aba "Pré-Ordens"
5. THE Sistema SHALL manter convites não aceitos na aba "Convites" com funcionalidades de aceitar/rejeitar

### Requirement 13: Indicadores de Status na Pré-Ordem

**User Story:** Como cliente ou prestador, quero ver claramente o status atual da pré-ordem e quem precisa agir, para que eu saiba se devo fazer algo.

#### Acceptance Criteria

1. WHEN uma Pre_Ordem está aguardando minha ação, THE Sistema SHALL exibir badge "Ação Necessária"
2. WHEN uma Pre_Ordem está aguardando a outra parte, THE Sistema SHALL exibir "Aguardando [Nome]"
3. WHEN ambas as partes aceitaram, THE Sistema SHALL exibir "Pronto para Conversão"
4. WHEN há proposta pendente, THE Sistema SHALL exibir "Proposta Pendente de [Nome]"
5. THE Sistema SHALL usar cores distintas para cada status (vermelho=ação necessária, amarelo=aguardando, verde=pronto)

### Requirement 14: Tratamento de Erros na Conversão de Pré-Ordem

**User Story:** Como administrador do sistema, quero que erros na conversão de pré-ordem para ordem sejam tratados adequadamente, para evitar estados inconsistentes.

#### Acceptance Criteria

1. IF a criação da Ordem falha após Aceitacao_Mutua, THE Sistema SHALL reverter a Pre_Ordem para status 'em_negociacao'
2. IF o bloqueio de valores falha, THE Sistema SHALL cancelar a criação da Ordem e manter a Pre_Ordem ativa
3. WHEN ocorre erro na conversão, THE Sistema SHALL registrar erro em log com detalhes completos
4. WHEN ocorre erro na conversão, THE Sistema SHALL notificar ambas as partes com mensagem clara
5. WHEN uma transação de escrow falha, THE Sistema SHALL garantir rollback completo sem valores inconsistentes

### Requirement 15: Limite de Tempo para Negociação

**User Story:** Como administrador do sistema, quero que pré-ordens não fiquem abertas indefinidamente, para evitar processos abandonados.

#### Acceptance Criteria

1. WHEN uma Pre_Ordem é criada, THE Sistema SHALL definir prazo de 7 dias para negociação
2. WHEN uma Pre_Ordem está próxima do prazo (24h), THE Sistema SHALL notificar ambas as partes
3. WHEN o prazo expira sem Aceitacao_Mutua, THE Sistema SHALL marcar a Pre_Ordem como 'expirada'
4. WHEN uma Pre_Ordem expira, THE Sistema SHALL notificar ambas as partes
5. THE Sistema SHALL permitir que administradores configurem o prazo padrão de negociação

### Requirement 16: Migração de Convites Existentes

**User Story:** Como administrador do sistema, quero migrar convites aceitos existentes para o novo modelo de pré-ordem, para manter consistência no sistema.

#### Acceptance Criteria

1. THE Sistema SHALL identificar todos os convites com status 'aceito' que ainda não geraram ordem
2. THE Sistema SHALL converter esses convites em Pre_Ordem com status 'em_negociacao'
3. THE Sistema SHALL preservar todos os dados originais do convite na Pre_Ordem
4. THE Sistema SHALL notificar usuários afetados sobre a mudança
5. THE Sistema SHALL fornecer relatório de migração com estatísticas e eventuais erros

### Requirement 17: Auditoria de Negociações

**User Story:** Como administrador do sistema, quero rastrear todas as negociações em pré-ordens, para análise e resolução de disputas.

#### Acceptance Criteria

1. THE Sistema SHALL registrar todas as ações em Pre_Ordem em log de auditoria
2. THE Sistema SHALL armazenar timestamp, usuário, ação e valores para cada evento
3. THE Sistema SHALL permitir consulta de histórico completo de qualquer Pre_Ordem
4. THE Sistema SHALL gerar relatórios de tempo médio de negociação
5. THE Sistema SHALL alertar sobre pré-ordens com muitas rodadas de negociação (possível disputa)

### Requirement 18: Interface de Negociação Intuitiva

**User Story:** Como cliente ou prestador, quero uma interface clara e intuitiva para negociar na pré-ordem, para que o processo seja simples e eficiente.

#### Acceptance Criteria

1. THE Sistema SHALL exibir card com informações principais da Pre_Ordem (título, valor, prazo)
2. THE Sistema SHALL exibir seção de histórico de negociação em timeline vertical
3. THE Sistema SHALL exibir formulário de proposta com campos de valor, prazo e justificativa
4. THE Sistema SHALL exibir botões de ação principais destacados (Aceitar Termos, Propor Alteração, Cancelar)
5. THE Sistema SHALL usar indicadores visuais para mostrar diferenças entre valores (setas, cores)

### Requirement 19: Validação de Propostas Razoáveis

**User Story:** Como administrador do sistema, quero que o sistema valide propostas extremas, para evitar abusos e negociações de má-fé.

#### Acceptance Criteria

1. WHEN uma Proposta_Alteracao aumenta o valor em mais de 100%, THE Sistema SHALL exibir aviso de alteração significativa
2. WHEN uma Proposta_Alteracao reduz o valor em mais de 50%, THE Sistema SHALL exibir aviso de alteração significativa
3. WHEN uma proposta extrema é submetida, THE Sistema SHALL requerer justificativa detalhada (mínimo 50 caracteres)
4. THE Sistema SHALL permitir que administradores configurem limites de variação aceitável
5. THE Sistema SHALL registrar propostas extremas para análise de padrões suspeitos

### Requirement 20: Atualização em Tempo Real da Pré-Ordem

**User Story:** Como cliente ou prestador, quero que a interface da pré-ordem seja atualizada automaticamente quando a outra parte fizer alterações, para acompanhar a negociação em tempo real.

#### Acceptance Criteria

1. WHEN uma Proposta_Alteracao é submetida, THE Sistema SHALL atualizar a interface da outra parte em tempo real
2. WHEN uma proposta é aceita ou rejeitada, THE Sistema SHALL atualizar ambas as interfaces imediatamente
3. WHEN Aceitacao_Mutua é alcançada, THE Sistema SHALL atualizar ambas as interfaces mostrando conversão em andamento
4. WHEN a conexão em tempo real falha, THE Sistema SHALL fornecer botão de atualização manual
5. THE Sistema SHALL exibir indicador quando a outra parte está visualizando a Pre_Ordem
