# Implementation Plan

- [x] 1. Criar migração de banco de dados para campos de aceitação mútua
  - Adicionar campos client_accepted, client_accepted_at, provider_accepted, provider_accepted_at ao modelo Invite
  - Criar índice composto para performance em (client_accepted, provider_accepted, status)
  - Testar migração em ambiente de desenvolvimento
  - _Requirements: 1.1, 1.2, 9.1, 9.2_

- [x] 2. Implementar InviteAcceptanceCoordinator
  - [x] 2.1 Criar arquivo services/invite_acceptance_coordinator.py
    - Implementar método process_acceptance para processar aceitação de convite
    - Implementar método check_mutual_acceptance para verificar se ambas as partes aceitaram
    - Implementar método create_order_from_mutual_acceptance para criar ordem quando há aceitação mútua
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.2 Implementar validação de saldos antes da criação da ordem
    - Validar saldo do cliente para valor do serviço + taxa de contestação
    - Validar saldo do prestador para taxa de contestação
    - Retornar mensagens de erro claras quando saldo insuficiente
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4_

  - [x] 2.3 Implementar criação atômica de ordem com bloqueio de valores
    - Usar transação de banco de dados para garantir atomicidade
    - Criar ordem de serviço com status 'aceita'
    - Bloquear valor do serviço no escrow do cliente
    - Bloquear taxa de contestação no escrow do prestador
    - Atualizar status do convite para 'convertido'
    - Implementar rollback completo em caso de erro
    - _Requirements: 1.3, 1.4, 2.1, 2.2, 2.5, 7.1, 7.2, 7.5_

- [x] 3. Atualizar InviteService com métodos de aceitação separados
  - [x] 3.1 Implementar método accept_invite_as_client
    - Validar que usuário é o cliente do convite
    - Validar saldo suficiente antes de aceitar
    - Marcar client_accepted como True e registrar timestamp
    - Chamar InviteAcceptanceCoordinator.process_acceptance
    - _Requirements: 1.1, 8.1, 8.3, 8.5_

  - [x] 3.2 Implementar método accept_invite_as_provider
    - Validar que usuário é o prestador do convite (via telefone)
    - Validar saldo suficiente para taxa antes de aceitar
    - Marcar provider_accepted como True e registrar timestamp
    - Chamar InviteAcceptanceCoordinator.process_acceptance
    - _Requirements: 1.2, 8.2, 8.3, 8.5_

  - [x] 3.3 Adicionar propriedades ao modelo Invite
    - Propriedade is_mutually_accepted para verificar aceitação mútua
    - Propriedade pending_acceptance_from para identificar quem falta aceitar
    - _Requirements: 9.3_

- [x] 4. Criar DashboardDataService para agregar dados das dashboards
  - [x] 4.1 Implementar método get_open_orders
    - Retornar ordens com status 'aceita', 'em_andamento' ou 'aguardando_confirmacao'
    - Filtrar por role (cliente ou prestador)
    - Ordenar por data de criação (cliente) ou data de entrega (prestador)
    - Incluir informações de valor, status, e parte relacionada
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Implementar método get_blocked_funds_summary
    - Calcular total de fundos bloqueados em escrow por usuário
    - Detalhar valores bloqueados por ordem
    - Incluir título e ID da ordem para cada bloqueio
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 4.3 Implementar método get_dashboard_metrics
    - Agregar saldo disponível e bloqueado
    - Contar ordens em aberto por status
    - Calcular estatísticas do mês
    - Gerar alertas baseados em saldo e ordens
    - _Requirements: 3.5, 4.5, 5.1, 5.2_

- [x] 5. Atualizar rotas de aceitação de convites
  - [x] 5.1 Atualizar rota cliente_bp.aceitar_convite
    - Usar InviteService.accept_invite_as_client
    - Exibir mensagem apropriada se ordem foi criada ou aguardando prestador
    - Tratar erros de saldo insuficiente com mensagem clara
    - Redirecionar para página apropriada após aceitação
    - _Requirements: 1.1, 6.1, 6.3, 6.4, 8.3, 8.4_

  - [x] 5.2 Atualizar rota prestador_bp.aceitar_convite
    - Usar InviteService.accept_invite_as_provider
    - Exibir mensagem apropriada se ordem foi criada ou aguardando cliente
    - Tratar erros de saldo insuficiente com mensagem clara
    - Redirecionar para página apropriada após aceitação
    - _Requirements: 1.2, 6.2, 6.3, 6.4, 8.3, 8.4_

- [x] 6. Atualizar ClienteService para usar DashboardDataService
  - [x] 6.1 Modificar método get_dashboard_data
    - Usar DashboardDataService.get_dashboard_metrics
    - Incluir ordens em aberto na resposta
    - Incluir fundos bloqueados detalhados
    - Adicionar alertas de saldo baixo se aplicável
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2_

  - [x] 6.2 Adicionar método get_open_orders_for_client
    - Usar DashboardDataService.get_open_orders com role='cliente'
    - Retornar lista formatada para template
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 7. Atualizar PrestadorService para usar DashboardDataService
  - [x] 7.1 Modificar método get_dashboard_data
    - Usar DashboardDataService.get_dashboard_metrics
    - Incluir ordens em aberto na resposta
    - Incluir fundos bloqueados detalhados
    - Adicionar alertas de saldo baixo se aplicável
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2_

  - [x] 7.2 Adicionar método get_open_orders_for_provider
    - Usar DashboardDataService.get_open_orders com role='prestador'
    - Retornar lista formatada para template
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 8. Atualizar template da dashboard do cliente
  - [x] 8.1 Adicionar seção de ordens em aberto
    - Exibir lista de ordens com status, valor, prestador e data
    - Incluir link para ver detalhes de cada ordem
    - Mostrar mensagem quando não há ordens em aberto
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 8.2 Adicionar visualização de fundos bloqueados
    - Exibir saldo disponível e bloqueado separadamente
    - Mostrar detalhamento de valores bloqueados por ordem
    - Adicionar links clicáveis para ordens
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.3 Atualizar cards de estatísticas
    - Incluir informação de fundos bloqueados no card de saldo
    - Atualizar contadores de ordens ativas
    - _Requirements: 3.1, 5.1, 5.2_

- [x] 9. Atualizar template da dashboard do prestador
  - [x] 9.1 Adicionar seção de ordens em aberto
    - Exibir lista de ordens com status, valor, cliente e data
    - Incluir ações disponíveis (marcar como concluído, etc.)
    - Ordenar por urgência (data de entrega)
    - Mostrar mensagem quando não há ordens em aberto
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 9.2 Adicionar visualização de fundos bloqueados
    - Exibir saldo disponível e bloqueado separadamente
    - Mostrar detalhamento de valores bloqueados por ordem
    - Adicionar links clicáveis para ordens
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 9.3 Atualizar cards de estatísticas
    - Incluir informação de fundos bloqueados no card de saldo
    - Atualizar contadores de ordens ativas
    - _Requirements: 4.1, 5.1, 5.2_

- [x] 10. Implementar sistema de notificações para criação de ordem
  - [x] 10.1 Adicionar método notify_order_created ao NotificationService
    - Enviar notificação ao cliente informando criação da ordem
    - Enviar notificação ao prestador informando criação da ordem
    - Incluir número da ordem, valor e data de entrega
    - Incluir link direto para visualizar a ordem
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 10.2 Adicionar método notify_insufficient_balance
    - Notificar usuário quando tentativa de aceitação falha por saldo insuficiente
    - Incluir valor necessário e saldo atual
    - Sugerir adicionar saldo
    - _Requirements: 6.5, 8.3, 8.4_

  - [x] 10.3 Integrar notificações no InviteAcceptanceCoordinator
    - Chamar notify_order_created após criação bem-sucedida
    - Chamar notify_insufficient_balance em caso de erro de saldo
    - _Requirements: 6.1, 6.2, 6.5_

- [x] 11. Implementar logging e auditoria
  - [x] 11.1 Adicionar logs de aceitação de convites
    - Registrar quando cliente aceita convite
    - Registrar quando prestador aceita convite
    - Incluir timestamps e IDs de usuário
    - _Requirements: 9.1, 9.2_

  - [x] 11.2 Adicionar logs de criação de ordem
    - Registrar criação de ordem a partir de convite
    - Incluir valores bloqueados e IDs de transação
    - Registrar qual usuário completou a aceitação mútua
    - _Requirements: 9.1, 9.2, 9.4_

  - [x] 11.3 Adicionar logs de erros
    - Registrar falhas na criação de ordem com detalhes completos
    - Registrar falhas no bloqueio de valores
    - Incluir stack trace para debugging
    - _Requirements: 7.3, 7.4_

- [x] 12. Implementar tratamento de erros robusto
  - [x] 12.1 Adicionar tratamento de erro de saldo insuficiente
    - Capturar exceção específica
    - Exibir mensagem clara com valores
    - Sugerir ação (adicionar saldo)
    - Não alterar estado do convite
    - _Requirements: 7.4, 8.3, 8.4_

  - [x] 12.2 Adicionar tratamento de erro de criação de ordem
    - Implementar rollback completo da transação
    - Reverter status do convite se necessário
    - Registrar erro em log
    - Exibir mensagem de erro ao usuário
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 12.3 Adicionar tratamento de erro de bloqueio de escrow
    - Cancelar criação da ordem
    - Garantir que nenhum valor fica inconsistente
    - Manter convite como aceito para retry
    - Notificar administrador se erro persistir
    - _Requirements: 7.2, 7.5_

- [x] 13. Implementar atualização em tempo real das dashboards
  - [x] 13.1 Adicionar WebSocket ou Server-Sent Events
    - Configurar conexão em tempo real
    - Enviar eventos quando ordem é criada
    - Enviar eventos quando status de ordem muda
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 13.2 Atualizar templates para receber eventos em tempo real
    - Adicionar JavaScript para escutar eventos
    - Atualizar lista de ordens sem recarregar página
    - Atualizar saldo bloqueado em tempo real
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 13.3 Adicionar fallback para atualização manual
    - Botão de atualização manual se conexão falhar
    - Polling automático como fallback
    - _Requirements: 10.5_

- [x] 14. Escrever testes unitários
  - [x] 14.1 Testes para InviteAcceptanceCoordinator
    - test_detect_mutual_acceptance
    - test_create_order_on_mutual_acceptance
    - test_insufficient_balance_client
    - test_insufficient_balance_provider
    - test_rollback_on_error
    - _Requirements: Todos_

  - [x] 14.2 Testes para DashboardDataService
    - test_get_open_orders_cliente
    - test_get_open_orders_prestador
    - test_get_blocked_funds_summary
    - test_dashboard_metrics_calculation
    - _Requirements: 3.1-3.5, 4.1-4.5, 5.1-5.5_

  - [x] 14.3 Testes para InviteService updates
    - test_accept_as_client
    - test_accept_as_provider
    - test_mutual_acceptance_triggers_order
    - test_validation_before_acceptance
    - _Requirements: 1.1-1.5, 8.1-8.5_

- [x] 15. Escrever testes de integração
  - [x] 15.1 Teste de fluxo completo de aceitação
    - Cliente cria convite
    - Prestador aceita
    - Cliente aceita
    - Verificar ordem criada
    - Verificar valores bloqueados
    - Verificar dashboards atualizadas
    - _Requirements: Todos_

  - [x] 15.2 Teste de fluxo com saldo insuficiente
    - Cliente com saldo baixo tenta aceitar
    - Verificar erro apropriado
    - Adicionar saldo
    - Aceitar com sucesso
    - _Requirements: 2.3, 2.4, 8.1-8.4_

  - [x] 15.3 Teste de fluxo de rollback
    - Simular falha no bloqueio de escrow
    - Verificar rollback da ordem
    - Verificar convite ainda aceito
    - Verificar possibilidade de retry
    - _Requirements: 7.1, 7.2, 7.5_

- [x] 16. Realizar testes manuais de UI
  - [ ] 16.1 Testar dashboard do cliente
    - Verificar exibição de ordens em aberto
    - Verificar exibição de fundos bloqueados
    - Verificar links clicáveis
    - Verificar mensagens quando vazio
    - _Requirements: 3.1-3.5, 5.1-5.5_

  - [x] 16.2 Testar dashboard do prestador
    - Verificar exibição de ordens em aberto
    - Verificar exibição de fundos bloqueados
    - Verificar ações disponíveis
    - Verificar ordenação por urgência
    - _Requirements: 4.1-4.5, 5.1-5.5_

  - [x] 16.3 Testar fluxo de aceitação
    - Testar aceitação pelo cliente
    - Testar aceitação pelo prestador
    - Verificar mensagens de feedback
    - Verificar redirecionamentos
    - Verificar notificações
    - _Requirements: 1.1-1.5, 6.1-6.5_
