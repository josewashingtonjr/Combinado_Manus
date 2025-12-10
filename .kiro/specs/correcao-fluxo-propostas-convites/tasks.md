# Implementation Plan

- [x] 1. Corrigir InviteStateManager para gerenciar campos de proposta corretamente
  - Modificar método transition_to_state() para limpar campos baseado no estado alvo
  - Adicionar lógica para PENDENTE: limpar has_active_proposal, current_proposal_id e effective_value
  - Adicionar lógica para PROPOSTA_ACEITA: limpar has_active_proposal mas manter current_proposal_id
  - Adicionar lógica para PROPOSTA_REJEITADA: limpar todos os campos de proposta
  - Corrigir método can_be_accepted() para bloquear aceitação quando has_active_proposal é True
  - _Requirements: 1.1, 1.4, 2.1, 2.2, 2.3, 9.1, 9.2, 10.1, 10.2, 10.3_

- [x] 2. Remover limpeza duplicada dos métodos do modelo Proposal
  - Modificar método accept() para apenas setar effective_value no convite
  - Modificar método reject() para não limpar campos (será feito pelo StateManager)
  - Modificar método cancel() para não limpar campos (será feito pelo StateManager)
  - Garantir que apenas status e responded_at são atualizados nos métodos
  - _Requirements: 9.3, 10.4_

- [x] 3. Corrigir sequência de operações no ProposalService.approve_proposal()
  - Modificar para chamar proposal.accept() primeiro (seta effective_value)
  - Adicionar db.session.flush() após accept()
  - Modificar para chamar transition_to(PROPOSTA_ACEITA) depois (limpa has_active_proposal)
  - Garantir que effective_value está setado antes da transição
  - Validar que resultado retorna effective_value correto
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.4_

- [x] 4. Corrigir sequência de operações no ProposalService.reject_proposal()
  - Modificar para chamar proposal.reject() primeiro
  - Adicionar db.session.flush() após reject()
  - Modificar para transicionar para PROPOSTA_REJEITADA (limpa campos)
  - Adicionar segunda transição para PENDENTE (estado final)
  - Garantir que todos os campos de proposta são limpos
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.1, 5.2, 5.3_

- [x] 5. Corrigir sequência de operações no ProposalService.cancel_proposal()
  - Modificar para chamar proposal.cancel() primeiro
  - Adicionar db.session.flush() após cancel()
  - Modificar para transicionar diretamente para PENDENTE (limpa campos)
  - Garantir que convite volta ao estado original
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 6. Atualizar template do prestador para exibir botão de aceitar corretamente
  - Modificar lógica de desabilitação do botão baseado em invite.has_active_proposal
  - Adicionar mensagem "Aguardando Cliente" quando proposta está pendente
  - Modificar texto do botão para mostrar valor efetivo quando proposta aceita
  - Adicionar tooltip explicativo quando botão está desabilitado
  - Garantir que botão é habilitado após cliente responder
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.3, 5.1_

- [x] 7. Atualizar template do prestador para exibir valor correto
  - Modificar para mostrar effective_value quando existe
  - Modificar para mostrar proposed_value quando proposta está pendente
  - Modificar para mostrar original_value quando não há proposta
  - Adicionar indicação visual do estado (cor, ícone)
  - Mostrar valor original riscado quando há effective_value
  - _Requirements: 4.2, 5.2_

- [x] 8. Atualizar template do cliente para exibir valor correto
  - Modificar para mostrar effective_value como valor principal quando existe
  - Adicionar comparação com original_value quando há effective_value
  - Calcular e exibir diferença (aumento/redução)
  - Usar cores apropriadas (verde para redução, vermelho para aumento)
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 9. Atualizar template do cliente para exibir card de proposta pendente
  - Criar card destacado quando has_active_proposal é True
  - Mostrar comparação visual entre valores original e proposto
  - Exibir justificativa do prestador
  - Adicionar botões "Aceitar Proposta" e "Rejeitar Proposta"
  - Integrar verificação de saldo para aumentos
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 10. Atualizar JavaScript para feedback correto após rejeição
  - Modificar handleRejectProposal() para mostrar mensagem de sucesso apropriada
  - Adicionar indicação que convite voltou ao valor original
  - Garantir que página recarrega para mostrar estado atualizado
  - Adicionar loading state durante processamento
  - _Requirements: 2.3, 5.4_

- [x] 11. Atualizar JavaScript para feedback correto após aprovação
  - Modificar handleAcceptProposal() para mostrar mensagem de sucesso apropriada
  - Adicionar indicação que prestador pode aceitar o convite
  - Garantir que página recarrega para mostrar novo valor
  - Adicionar loading state durante processamento
  - _Requirements: 3.5, 4.5_

- [x] 12. Adicionar validação de estado antes de aceitar convite
  - Modificar InviteService.accept_invite() para chamar can_be_accepted()
  - Lançar erro se has_active_proposal é True
  - Retornar mensagem clara sobre aguardar aprovação
  - Adicionar log de tentativa bloqueada
  - _Requirements: 1.4, 1.5_

- [x] 13. Garantir que ordem de serviço usa valor efetivo correto
  - Modificar criação de ordem para usar invite.current_value
  - Validar que current_value retorna effective_value quando existe
  - Validar que current_value retorna original_value quando não há proposta
  - Adicionar referência à proposta na ordem se houver
  - Validar saldo do cliente com valor correto
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 14. Adicionar validação de integridade após transições
  - Criar método validate_proposal_fields() no InviteStateManager
  - Validar que campos estão corretos para cada estado
  - Lançar erro se inconsistência for detectada
  - Adicionar log de validação
  - _Requirements: 9.4, 9.5, 10.5_

- [ ]* 15. Criar testes para transições de estado
  - Testar transição PENDENTE -> PROPOSTA_ENVIADA (seta campos)
  - Testar transição PROPOSTA_ENVIADA -> PROPOSTA_ACEITA (limpa has_active_proposal)
  - Testar transição PROPOSTA_ENVIADA -> PROPOSTA_REJEITADA -> PENDENTE (limpa tudo)
  - Testar transição PROPOSTA_ENVIADA -> PENDENTE via cancelamento (limpa tudo)
  - Validar campos após cada transição
  - _Requirements: 9.1, 9.2, 10.1, 10.2, 10.3_

- [ ]* 16. Criar testes para bloqueio de aceitação
  - Testar que can_be_accepted() retorna False quando has_active_proposal é True
  - Testar que can_be_accepted() retorna True após aprovação
  - Testar que can_be_accepted() retorna True após rejeição
  - Testar que accept_invite() lança erro quando proposta está pendente
  - _Requirements: 1.1, 1.4, 1.5_

- [ ]* 17. Criar testes para valor efetivo
  - Testar que effective_value é setado após aprovação
  - Testar que effective_value é limpo após rejeição
  - Testar que effective_value é limpo após cancelamento
  - Testar que current_value retorna valor correto em cada estado
  - Testar que ordem de serviço usa valor correto
  - _Requirements: 3.1, 3.2, 6.1, 6.2_

- [ ]* 18. Criar testes de integração para fluxo completo
  - Testar fluxo: criar proposta -> aprovar -> aceitar convite -> criar ordem
  - Testar fluxo: criar proposta -> rejeitar -> aceitar com valor original
  - Testar fluxo: criar proposta -> cancelar -> aceitar com valor original
  - Validar que valores estão corretos em cada etapa
  - Validar que botões estão habilitados/desabilitados corretamente
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_
