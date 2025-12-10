# Implementation Plan

## Fase 1: Fundação - Modelos e Estrutura de Dados

- [ ] 1. Criar modelos de dados para pré-ordens
  - Criar enum `PreOrderStatus` em models.py com estados: em_negociacao, aguardando_resposta, pronto_conversao, convertida, cancelada, expirada
  - Criar modelo `PreOrder` com todos os campos necessários (id, invite_id, client_id, provider_id, title, description, current_value, original_value, delivery_date, service_category, status, client_accepted_terms, provider_accepted_terms, timestamps, etc.)
  - Adicionar relacionamentos com Invite, User, Order, PreOrderProposal, PreOrderHistory
  - Adicionar propriedades calculadas: is_expired, can_be_converted, days_until_expiration
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 5.1, 8.4, 15.1, 15.3_

- [x] 1.1 Testes de propriedade para PreOrder
  - Property 1: Criação de pré-ordem a partir de convite (Req 1.1, 1.2)
  - Property 2: Convite marcado como convertido (Req 1.3)
  - Property 3: Pré-ordem não bloqueia valores (Req 1.5, 6.1)
  - Property 47: Prazo de negociação (Req 15.1)

- [x] 2. Criar modelos para propostas e histórico
  - Criar enum `ProposalStatus` com: pendente, aceita, rejeitada, cancelada
  - Criar modelo `PreOrderProposal` com campos: id, pre_order_id, proposed_by, proposed_value, proposed_delivery_date, proposed_description, justification, status, timestamps
  - Criar modelo `PreOrderHistory` com campos: id, pre_order_id, event_type, actor_id, description, event_data (JSON), created_at
  - Adicionar relacionamentos apropriados
  - _Requirements: 2.4, 3.5, 10.1, 10.2, 17.1, 17.2_

- [x] 2.1 Testes de propriedade para propostas
  - Property 6: Proposta requer justificativa (Req 2.4)
  - Property 10: Registro de histórico (Req 3.5, 17.1, 17.2)

- [x] 3. Criar migrations SQL
  - Criar arquivo migrations/add_pre_order_system.sql
  - Adicionar CREATE TABLE para pre_orders com todos os campos e constraints
  - Adicionar CREATE TABLE para pre_order_proposals
  - Adicionar CREATE TABLE para pre_order_history
  - Adicionar índices: idx_pre_orders_status, idx_pre_orders_client, idx_pre_orders_provider, idx_pre_orders_expires
  - Adicionar constraints: check_current_value_positive, check_expires_after_creation
  - Criar script Python apply_pre_order_migration.py para aplicar migration
  - _Requirements: Performance e Data Integrity_

## Fase 2: Lógica de Negócio - Serviços Core

- [x] 4. Implementar PreOrderStateManager
  - Criar services/pre_order_state_manager.py
  - Implementar método transition_to(pre_order_id, new_status, actor_id, reason) com validação de transições válidas
  - Implementar método check_mutual_acceptance(pre_order_id) retornando bool
  - Implementar método reset_acceptances(pre_order_id) para limpar flags quando há nova proposta
  - Adicionar mapeamento de transições válidas por estado
  - Adicionar logging de todas as transições
  - _Requirements: 2.5, 4.5, 5.1, 8.4, 14.1, 15.3_

- [x] 4.1 Testes de propriedade para state manager
  - Property 7: Transição ao submeter proposta (Req 2.5)
  - Property 15: Retorno à negociação após rejeição (Req 4.5)
  - Property 16: Detecção de aceitação mútua (Req 5.1)
  - Property 27: Transição para cancelada (Req 8.4)

- [x] 5. Implementar PreOrderService
  - Criar services/pre_order_service.py
  - Implementar create_from_invite(invite_id) para criar pré-ordem a partir de convite aceito
  - Implementar get_pre_order_details(pre_order_id, user_id) retornando dados completos com validação de permissão
  - Implementar accept_terms(pre_order_id, user_id) para marcar aceitação de termos com validação de saldo
  - Implementar cancel_pre_order(pre_order_id, user_id, reason) com validação de motivo obrigatório
  - Integrar com NotificationService para todas as ações
  - Integrar com PreOrderStateManager para transições
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 7.1, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 5.1 Testes de propriedade para PreOrderService
  - Property 4: Notificação de criação (Req 1.4, 11.1)
  - Property 20: Validação de saldo ao aceitar termos (Req 7.1)
  - Property 23: Marcação de aceitação (Req 7.5)
  - Property 24-28: Cancelamento (Req 8.1-8.5)

- [x] 6. Implementar PreOrderProposalService
  - Criar services/pre_order_proposal_service.py
  - Implementar create_proposal(pre_order_id, user_id, proposed_value, proposed_delivery_date, proposed_description, justification) com validações
  - Validar justificativa mínima de 50 caracteres
  - Validar que pelo menos um campo foi alterado
  - Detectar propostas extremas (>100% aumento ou >50% redução) e exigir justificativa detalhada
  - Implementar accept_proposal(proposal_id, user_id) atualizando valores da pré-ordem
  - Implementar reject_proposal(proposal_id, user_id) mantendo valores anteriores
  - Integrar com PreOrderStateManager para transições
  - Integrar com NotificationService
  - Registrar todas as ações em PreOrderHistory
  - _Requirements: 2.1-2.5, 3.1-3.5, 4.1-4.5, 19.1-19.3, 19.5_

- [x] 6.1 Testes de propriedade para propostas
  - Property 5: Permissão para propor (Req 2.1, 3.1, 3.2)
  - Property 8-9: Notificação e apresentação (Req 2.2, 2.3, 11.2)
  - Property 11-14: Aprovação e rejeição (Req 3.4, 4.1-4.5)
  - Property 55-58: Propostas extremas (Req 19.1-19.3, 19.5)

- [x] 7. Checkpoint - Testes de serviços básicos
  - Executar todos os testes unitários dos serviços
  - Verificar que transições de estado funcionam corretamente
  - Verificar que validações estão funcionando
  - Verificar que histórico está sendo registrado
  - _Ensure all tests pass, ask the user if questions arise_

## Fase 3: Conversão e Integração com Sistema Existente

- [x] 8. Implementar PreOrderConversionService
  - Criar services/pre_order_conversion_service.py
  - Implementar validate_balances(pre_order_id) verificando saldo do cliente e prestador
  - Implementar convert_to_order(pre_order_id) com transação atômica
  - No convert_to_order: validar aceitação mútua, validar saldos, criar Order, bloquear valores em escrow, atualizar pré-ordem, notificar
  - Implementar tratamento de erros com rollback completo
  - Implementar reversão de estado em caso de falha
  - Adicionar logging detalhado de erros
  - Integrar com WalletService para bloqueio de valores
  - Integrar com OrderService para criar ordem
  - _Requirements: 5.1-5.5, 6.2-6.5, 14.1-14.5_

- [x] 8.1 Testes de propriedade para conversão
  - Property 17-19: Validação e bloqueio (Req 5.2-5.5, 6.2-6.5)
  - Property 42-46: Tratamento de erros (Req 14.1-14.5)

- [x] 9. Modificar InviteService para criar pré-ordem
  - Modificar método accept_invite_as_client em services/invite_service.py
  - Modificar método accept_invite_as_provider em services/invite_service.py
  - Ao invés de criar Order, chamar PreOrderService.create_from_invite
  - Remover bloqueio imediato de valores
  - Atualizar status do convite para 'convertido_pre_ordem'
  - Manter compatibilidade com testes existentes
  - _Requirements: 1.1-1.5, 12.1-12.3, 12.5_

- [x] 9.1 Testes de propriedade para integração com convites
  - Property 37-40: Convites convertidos (Req 12.1-12.3, 12.5)

- [x] 10. Checkpoint - Testes de integração
  - Executar testes de integração do fluxo completo: convite → pré-ordem → ordem
  - Verificar que valores são bloqueados apenas na conversão
  - Verificar que convites convertidos não permitem modificações
  - _Ensure all tests pass, ask the user if questions arise_

## Fase 4: Interface e Experiência do Usuário

- [x] 11. Criar rotas para pré-ordens
  - Criar routes/pre_ordem_routes.py
  - Implementar GET /pre-ordem/<id> para visualizar detalhes (apenas partes envolvidas)
  - Implementar POST /pre-ordem/<id>/propor-alteracao para criar proposta
  - Implementar POST /pre-ordem/<id>/aceitar-proposta/<proposal_id> para aceitar
  - Implementar POST /pre-ordem/<id>/rejeitar-proposta/<proposal_id> para rejeitar
  - Implementar POST /pre-ordem/<id>/aceitar-termos para aceitar termos finais
  - Implementar POST /pre-ordem/<id>/cancelar para cancelar pré-ordem
  - Implementar GET /pre-ordem/<id>/historico para consultar histórico
  - Adicionar validações de autorização em todas as rotas
  - Adicionar tratamento de erros com mensagens claras
  - Registrar rotas no app.py
  - _Requirements: 2.1, 3.1, 3.2, 4.1, 4.2, 4.4, 5.1, 7.1, 8.1, 17.3_

- [x] 12. Criar template de detalhes da pré-ordem
  - Criar templates/pre_ordem/detalhes.html
  - Adicionar card com informações principais: título, descrição, valor atual, valor original, prazo
  - Adicionar seção de status com indicadores visuais (cores e badges)
  - Adicionar seção de histórico em timeline vertical com todas as alterações
  - Adicionar formulário de proposta com campos: valor, prazo, descrição, justificativa
  - Adicionar botões de ação: Aceitar Termos, Propor Alteração, Cancelar
  - Adicionar indicadores de diferença entre valores (setas, percentuais, cores)
  - Adicionar modal de confirmação para ações críticas
  - Implementar responsividade para mobile
  - _Requirements: 9.2, 9.3, 10.1-10.4, 13.1-13.4, 18.1_

- [x] 12.1 Testes de propriedade para apresentação
  - Property 29-34: Apresentação de dados (Req 9.2, 9.3, 10.1-10.4)
  - Property 41: Indicadores de status (Req 13.1-13.4)
  - Property 54: Informações principais (Req 18.1)

- [x] 13. Adicionar seção de pré-ordens nas dashboards
  - Modificar templates/cliente/dashboard.html
  - Modificar templates/prestador/dashboard.html
  - Adicionar seção "Pré-Ordens em Negociação" com lista de pré-ordens ativas
  - Exibir para cada pré-ordem: título, valor atual, outra parte, status, indicador de proposta pendente
  - Adicionar filtros: todas, aguardando minha ação, aguardando outra parte
  - Adicionar links para detalhes de cada pré-ordem
  - Exibir mensagem quando não há pré-ordens ativas
  - Adicionar contador de pré-ordens pendentes no menu lateral
  - _Requirements: 9.1-9.5_

- [x] 14. Implementar JavaScript para interações
  - Criar static/js/pre-ordem-interactions.js
  - Implementar validação de formulário de proposta no frontend
  - Implementar cálculo automático de diferença percentual ao alterar valor
  - Implementar confirmação antes de ações críticas (cancelar, aceitar termos)
  - Adicionar feedback visual ao submeter ações (loading, success, error)
  - Implementar atualização de saldo disponível ao aceitar termos
  - Adicionar máscaras de input para valores monetários e datas
  - _Requirements: Interface interativa_

- [-] 15. Implementar atualizações em tempo real
  - Criar static/js/pre-ordem-realtime.js
  - Implementar WebSocket para atualizações em tempo real usando SocketIO
  - Implementar fallback para polling a cada 30 segundos
  - Adicionar atualização automática ao submeter proposta
  - Adicionar atualização automática ao aceitar/rejeitar proposta
  - Adicionar atualização automática ao alcançar aceitação mútua
  - Adicionar indicador de presença (outra parte visualizando)
  - Adicionar botão de atualização manual para fallback
  - Adicionar notificações toast para eventos importantes
  - _Requirements: 20.1-20.5_

- [x] 15.1 Testes de propriedade para tempo real
  - Property 59-62: Atualizações em tempo real (Req 20.1-20.5)

- [x] 16. Checkpoint - Interface funcional
  - Testar navegação completa do fluxo de negociação
  - Verificar responsividade em diferentes dispositivos
  - Verificar atualizações em tempo real
  - Verificar validações de formulário
  - _Ensure all tests pass, ask the user if questions arise_

## Fase 5: Funcionalidades Complementares

- [x] 17. Implementar sistema de expiração
  - Criar jobs/expire_pre_orders.py para job agendado
  - Implementar verificação de pré-ordens próximas da expiração (24h)
  - Implementar notificação 24h antes da expiração
  - Implementar marcação automática como 'expirada' ao atingir prazo
  - Implementar notificação de expiração
  - Configurar cron job ou scheduler (APScheduler) para executar a cada hora
  - Adicionar configuração de prazo padrão em config.py (7 dias)
  - _Requirements: 15.1-15.5_

- [x] 17.1 Testes de propriedade para expiração
  - Property 48-50: Notificações e expiração (Req 15.2-15.4)

- [x] 18. Implementar sistema de auditoria e alertas
  - Garantir que PreOrderHistory registra todas as ações
  - Criar services/pre_order_audit_service.py
  - Implementar get_full_history(pre_order_id) retornando histórico completo
  - Implementar check_excessive_negotiations(pre_order_id) alertando se >5 propostas
  - Implementar generate_negotiation_report() com tempo médio, taxa de conversão, etc.
  - Implementar generate_extreme_proposals_report() listando propostas suspeitas
  - Adicionar logs de auditoria com IP e user agent
  - _Requirements: 17.1-17.5_

- [x] 18.1 Testes de propriedade para auditoria
  - Property 52-53: Histórico e alertas (Req 17.3, 17.5)

- [x] 19. Implementar validação de saldo com UX melhorada
  - Modificar PreOrderService.accept_terms para validar saldo antes de aceitar
  - Adicionar endpoint POST /pre-ordem/<id>/verificar-saldo retornando status
  - Modificar template para exibir mensagem clara quando saldo insuficiente
  - Adicionar botão "Adicionar Saldo" com valor sugerido calculado automaticamente
  - Implementar modal de adição de saldo integrado
  - Permitir aceitar termos imediatamente após adicionar saldo
  - _Requirements: 7.1-7.4_

- [x] 19.1 Testes de propriedade para validação de saldo
  - Property 21-22: Mensagens e fluxo de saldo (Req 7.2-7.4)

- [x] 20. Implementar notificações específicas
  - Criar templates de notificação em templates/notifications/
  - Template: pre_ordem_criada.html (para ambas as partes)
  - Template: proposta_recebida.html (para destinatário)
  - Template: proposta_aceita.html (para autor)
  - Template: proposta_rejeitada.html (para autor)
  - Template: pre_ordem_convertida.html (para ambas as partes)
  - Template: pre_ordem_cancelada.html (para outra parte)
  - Template: pre_ordem_expirando.html (24h antes)
  - Template: pre_ordem_expirada.html (após expiração)
  - Template: erro_conversao.html (em caso de erro)
  - Integrar templates com NotificationService
  - _Requirements: 1.4, 2.2, 8.3, 11.1-11.5, 14.4, 15.2, 15.4_

- [x] 20.1 Testes de propriedade para notificações
  - Property 35-36: Notificações de resposta e conversão (Req 11.3, 11.4)

## Fase 6: Migração e Otimização

- [x] 21. Criar script de migração de dados
  - Criar migrate_invites_to_pre_orders.py
  - Identificar convites com status 'aceito' sem order_id associado
  - Para cada convite: criar PreOrder preservando todos os dados (título, descrição, valor, prazo)
  - Atualizar status do convite para 'convertido_pre_ordem'
  - Criar registro em PreOrderHistory para migração
  - Notificar usuários afetados sobre a mudança
  - Gerar relatório JSON com estatísticas: total migrado, erros, tempo de execução
  - Implementar modo dry-run para testar antes de executar
  - Implementar rollback em caso de erro
  - _Requirements: 16.1-16.5_

- [x] 21.1 Testes de propriedade para migração
  - Property 51: Preservação de dados (Req 16.3)

- [x] 22. Adicionar índices e otimizações
  - Criar migrations/add_pre_order_indexes.sql
  - Adicionar índice: CREATE INDEX idx_pre_orders_status ON pre_orders(status)
  - Adicionar índice: CREATE INDEX idx_pre_orders_client ON pre_orders(client_id)
  - Adicionar índice: CREATE INDEX idx_pre_orders_provider ON pre_orders(provider_id)
  - Adicionar índice: CREATE INDEX idx_pre_orders_expires ON pre_orders(expires_at)
  - Adicionar índice: CREATE INDEX idx_pre_order_proposals_status ON pre_order_proposals(status)
  - Adicionar índice: CREATE INDEX idx_pre_order_history_pre_order ON pre_order_history(pre_order_id, created_at)
  - Implementar caching de pré-ordens ativas por usuário (TTL: 5 min) usando Flask-Caching
  - Implementar caching de histórico (TTL: 10 min)
  - Implementar paginação: 20 pré-ordens por página, 50 eventos de histórico
  - _Requirements: Performance considerations_

- [x] 23. Implementar rate limiting e segurança
  - Instalar Flask-Limiter
  - Adicionar rate limiting: máximo 10 propostas por pré-ordem por hora
  - Adicionar rate limiting: máximo 5 cancelamentos por usuário por dia
  - Adicionar rate limiting: máximo 20 requisições por minuto por usuário
  - Implementar validação de autorização em todas as rotas (apenas partes envolvidas)
  - Adicionar sanitização de campos de texto usando bleach
  - Adicionar validação rigorosa de valores numéricos (positivos, limites razoáveis)
  - Adicionar validação de datas (futuras, dentro de limites)
  - Implementar proteção CSRF em todos os formulários
  - Adicionar logging de tentativas de acesso não autorizado
  - _Requirements: Security considerations_

- [ ] 24. Checkpoint Final - Testes completos
  - Executar suite completa de testes unitários
  - Executar testes de integração do fluxo completo
  - Executar testes de carga (simular 100 usuários simultâneos)
  - Verificar performance de queries (todas <100ms)
  - Verificar que rate limiting funciona
  - Verificar que caching funciona
  - _Ensure all tests pass, ask the user if questions arise_

## Fase 7: Documentação e Deploy

- [ ] 25. Criar documentação técnica
  - Criar docs/pre_ordem_api.md documentando todos os endpoints
  - Documentar parâmetros, respostas, códigos de erro
  - Criar docs/pre_ordem_fluxo_estados.md com diagrama de estados
  - Documentar transições válidas e inválidas
  - Criar docs/pre_ordem_integracao.md explicando integração com sistema existente
  - Documentar como convites se tornam pré-ordens e depois ordens
  - Criar docs/pre_ordem_troubleshooting.md com erros comuns e soluções
  - _Requirements: Documentation_

- [ ] 26. Criar guia do usuário
  - Criar docs/guia_usuario_pre_ordem.md
  - Explicar o que é uma pré-ordem e como funciona
  - Documentar como negociar (propor alterações, aceitar, rejeitar)
  - Documentar como aceitar termos finais
  - Documentar como cancelar pré-ordem
  - Adicionar screenshots e exemplos práticos
  - Traduzir para português
  - _Requirements: User documentation_

- [x] 27. Configurar monitoramento e alertas
  - Configurar métricas no Prometheus/Grafana ou similar
  - Métrica: pre_ordens_criadas_total (contador)
  - Métrica: pre_ordens_convertidas_total (contador)
  - Métrica: pre_ordens_canceladas_total (contador)
  - Métrica: tempo_medio_negociacao (gauge)
  - Métrica: propostas_por_pre_ordem (histogram)
  - Configurar alerta: taxa_falha_conversao > 5%
  - Configurar alerta: tempo_medio_negociacao > 5 dias
  - Configurar alerta: taxa_expiracao > 20%
  - Criar dashboard de monitoramento com visão geral
  - _Requirements: Monitoring and Observability_

- [x] 28. Executar migração em produção
  - Fazer backup completo do banco de dados
  - Executar migrate_invites_to_pre_orders.py em modo dry-run
  - Revisar relatório de migração
  - Executar migração real em horário de baixo tráfego
  - Verificar que todos os convites foram migrados corretamente
  - Monitorar logs por 24h após migração
  - _Requirements: Migration strategy_

## Resumo de Propriedades Testáveis

Total de propriedades de correção: 62
- Propriedades obrigatórias (implementação core): 28
- Propriedades opcionais (testes adicionais): 34

As propriedades opcionais podem ser implementadas incrementalmente após o MVP estar funcionando.
