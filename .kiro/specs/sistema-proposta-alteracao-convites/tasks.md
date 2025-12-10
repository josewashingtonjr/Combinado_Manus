textos e chats em# Implementation Plan

- [x] 1. Criar estrutura de dados para propostas de alteração
  - Criar tabela invite_proposals com campos necessários
  - Adicionar campos has_active_proposal e current_proposal_id à tabela invites
  - Criar índices para otimização de consultas
  - Implementar migração de banco de dados
  - _Requirements: 8.2, 8.3_

- [x] 2. Implementar modelo Proposal no sistema
  - Criar classe Proposal no models.py
  - Definir relacionamentos com Invite e User
  - Implementar validações de dados (valores, status)
  - Adicionar métodos de conveniência para consultas
  - _Requirements: 1.4, 8.1_

- [x] 3. Desenvolver ProposalService para lógica de negócio
  - Implementar método create_proposal com validações
  - Criar approve_proposal com verificação de saldo
  - Desenvolver reject_proposal com histórico
  - Adicionar cancel_proposal para prestadores
  - Implementar check_client_balance_sufficiency
  - _Requirements: 1.1, 2.1, 2.2, 5.5_

- [x] 4. Criar BalanceValidator para verificação de saldo
  - Implementar calculate_required_balance (valor + taxa contestação)
  - Desenvolver check_sufficiency para validação de saldo
  - Criar suggest_top_up_amount para cálculo de recarga
  - Adicionar reserve_funds para reserva automática
  - _Requirements: 3.1, 3.2, 3.3, 4.2_

- [x] 5. Atualizar rotas para suportar propostas de alteração
  - Criar rota POST /convite/<id>/propor-alteracao
  - Implementar rota POST /proposta/<id>/aprovar
  - Adicionar rota POST /proposta/<id>/rejeitar
  - Criar rota DELETE /proposta/<id>/cancelar
  - Adicionar validações de autorização em todas as rotas
  - _Requirements: 1.1, 2.1, 2.2, 5.5_

- [x] 6. Implementar controle de estados do convite
  - Atualizar lógica de status do convite para incluir estados de proposta
  - Implementar bloqueio de aceitação durante proposta pendente
  - Criar validação de transições de estado válidas
  - Adicionar logs de auditoria para mudanças de estado
  - _Requirements: 5.1, 5.2, 6.1, 6.2, 8.1_

- [x] 7. Atualizar interface do prestador para propostas
  - Adicionar formulário "Propor Alteração" na página do convite
  - Implementar exibição de status "Aguardando aprovação do cliente"
  - Bloquear botão "Aceitar Convite" durante proposta pendente
  - Mostrar valor proposto em vez do original quando aplicável
  - Adicionar opção de cancelar proposta enviada
  - _Requirements: 5.1, 5.2, 5.3, 6.3, 6.4_

- [x] 8. Desenvolver interface do cliente para aprovação de propostas
  - Criar página de visualização de proposta com comparação de valores
  - Implementar botões "Aceitar Proposta" e "Rejeitar Proposta"
  - Adicionar verificação visual de saldo suficiente
  - Mostrar calculadora de valor necessário (proposta + taxa)
  - Implementar campo de comentários para rejeição
  - _Requirements: 1.2, 1.3, 2.1, 2.4, 3.2_

- [x] 9. Implementar fluxo de adição de saldo integrado
  - Detectar saldo insuficiente na aprovação de proposta
  - Exibir modal com valor necessário para adicionar
  - Integrar com sistema de adição de saldo existente
  - Permitir aprovação automática após adição de saldo suficiente
  - Confirmar transação antes de processar aprovação
  - _Requirements: 3.4, 4.1, 4.3, 4.4, 4.5_

- [x] 10. Desenvolver sistema de notificações para propostas
  - Criar notificação para cliente quando proposta é enviada
  - Implementar notificação para prestador sobre resposta do cliente
  - Adicionar notificação de saldo insuficiente
  - Incluir valores original e proposto nas notificações
  - Fornecer links diretos para ações necessárias
  - _Requirements: 1.1, 6.5, 9.1, 9.2, 9.3, 9.5_

- [x] 11. Atualizar geração de ordem de serviço
  - Modificar criação de ordem para usar valor efetivo (original ou proposto aceito)
  - Incluir histórico da proposta na ordem de serviço
  - Reservar valor correto do saldo do cliente
  - Adicionar referência à proposta aceita nos dados da ordem
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 12. Implementar validações de segurança e autorização
  - Validar que apenas prestador do convite pode criar propostas
  - Verificar que apenas cliente do convite pode aprovar/rejeitar
  - Implementar rate limiting para criação de propostas
  - Adicionar validação de valores propostos (limites razoáveis)
  - Sanitizar justificativas e comentários de entrada
  - _Requirements: 8.5, 2.4, 1.5_

- [x] 13. Criar sistema de auditoria e monitoramento
  - Implementar log completo de todas as ações de proposta
  - Armazenar histórico de propostas por convite
  - Criar métricas de propostas aceitas vs rejeitadas
  - Implementar alertas para padrões suspeitos
  - Adicionar dashboard administrativo para monitoramento
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 14. Desenvolver tratamento de erros e casos extremos
  - Implementar tratamento para ações simultâneas (concorrência)
  - Adicionar recovery para estados inconsistentes
  - Criar validação de integridade de dados
  - Implementar rollback automático em falhas de transação
  - Adicionar mensagens de erro claras para usuários
  - _Requirements: 3.3, 4.4, 7.4_

- [x] 15. Atualizar JavaScript para interações dinâmicas
  - Implementar atualização em tempo real de estados de proposta
  - Adicionar validação client-side para formulários
  - Criar feedback visual para ações de proposta
  - Implementar confirmações para ações críticas
  - Adicionar loading states para operações assíncronas
  - _Requirements: 9.4, 2.1, 6.5_

- [x] 16. Criar testes unitários para componentes de proposta
  - Testar ProposalService com diferentes cenários
  - Validar BalanceValidator com vários casos de saldo
  - Testar transições de estado do convite
  - Verificar validações de autorização
  - _Requirements: 1.1, 3.1, 5.1, 2.1_

- [ ]* 17. Implementar testes de integração para fluxo completo
  - Testar fluxo completo: proposta → aprovação → aceitação → ordem
  - Validar cenários de rejeição e cancelamento
  - Testar integração com sistema de saldo
  - Verificar notificações end-to-end
  - _Requirements: 7.3, 2.2, 4.3, 9.1_

- [ ]* 18. Desenvolver testes de UI para estados de proposta
  - Testar visibilidade correta de botões em cada estado
  - Validar mensagens explicativas
  - Verificar fluxo de adição de saldo integrado
  - Testar responsividade em dispositivos móveis
  - _Requirements: 5.2, 6.1, 4.1, 9.4_