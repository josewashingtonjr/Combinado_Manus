# Plano de Implementação

**IMPORTANTE:** Sempre consultar a Planta Arquitetônica (docs/PLANTA_ARQUITETONICA.md) e os documentos de Requirements/Design antes de implementar qualquer funcionalidade. O sistema segue arquitetura específica com admin como fonte central de tokens.

- [x] 1. Validar e testar a base existente do sistema
  - Testar sistema de autenticação completo com todos os tipos de usuário
  - Validar renderização de todos os templates sem erros
  - Verificar navegação entre todas as páginas e rotas
  - Confirmar funcionamento do banco de dados e migrações
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Implementar sistema de carteiras funcionais conforme arquitetura de tokenomics
  - [x] 2.1 Criar lógica de criação automática de carteiras
    - ✅ Implementar função para criar carteira automaticamente ao registrar usuário
    - ✅ Adicionar validação para garantir que todo usuário tenha carteira
    - ✅ Criar testes unitários para criação de carteiras (33 testes aprovados)
    - ✅ Implementar carteira do admin (ID 0) como fonte central de tokens
    - _Requisitos: 3.1, 10.2_

  - [x] 2.2 Implementar operações básicas de carteira seguindo fluxo admin→usuário
    - ✅ Desenvolver funções de débito e crédito com validação de saldo
    - ✅ Implementar verificação de saldo suficiente antes de transações
    - ✅ Criar sistema de bloqueio de saldo para escrow
    - ✅ Implementar admin como único criador de tokens (admin_create_tokens)
    - ✅ Implementar venda de tokens admin→usuário (admin_sell_tokens_to_user)
    - ✅ Implementar compra de tokens usuário→admin (user_sell_tokens_to_admin)
    - ✅ Adicionar testes para operações de carteira
    - _Requisitos: 3.2, 3.4, 10.3_

  - [x] 2.3 Desenvolver sistema de transações com rastreabilidade total
    - ✅ Implementar registro de todas as transações com IDs únicos
    - ✅ Criar tipos de transação expandidos (criacao_tokens, venda_tokens, recompra_tokens, etc.)
    - ✅ Adicionar timestamps e logs imutáveis para auditoria
    - ✅ Implementar validação de integridade matemática das transações
    - ✅ Desenvolver sistema de resumo de tokens no sistema
    - ✅ Desenvolver testes para rastreabilidade de transações
    - _Requisitos: 10.1, 10.2, 10.4_

  - [x] 2.4 Implementar arquitetura de tokenomics conforme planta do projeto
    - ✅ Admin (ID 0) possui primeira carteira com 1.000.000 tokens iniciais
    - ✅ Admin é único que pode criar tokens do zero via admin_create_tokens()
    - ✅ Tokens dos usuários são adquiridos da carteira do admin via deposit()
    - ✅ Saques retornam tokens para carteira do admin via withdraw()
    - ✅ Sistema de rastreabilidade completa de origem/destino de todos os tokens
    - ✅ Validação de integridade: admin_balance + tokens_in_circulation = total_created
    - _Requisitos: Planta Arquitetônica, Tokenomics, 10.1, 10.2, 10.3, 10.4_

- [x] 3. Completar sistema de ordens de serviço seguindo arquitetura de escrow
  - [x] 3.1 Implementar criação de ordens com bloqueio de tokens
    - Consultar Planta Arquitetônica para fluxo correto de estados de ordem
    - Desenvolver formulário e validação para criação de ordens
    - Implementar verificação de saldo suficiente antes de criar ordem
    - Adicionar bloqueio automático de saldo em escrow ao criar ordem (transfer_to_escrow)
    - Garantir que tokens bloqueados não saem do sistema, apenas mudam de saldo→escrow
    - Criar testes para criação de ordens com validação de escrow
    - _Requisitos: 8.1, 3.2, Planta Arquitetônica seção 5.1_

  - [x] 3.2 Desenvolver fluxo de aceitação de ordens conforme design
    - Consultar documento de Design para fluxo de estados: disponivel→aceita→em_andamento
    - Implementar função para prestadores aceitarem ordens disponíveis
    - Atualizar status da ordem e registrar prestador responsável
    - Adicionar validações de disponibilidade e conflitos de horário
    - Implementar notificações para cliente sobre aceitação
    - Criar testes para aceitação de ordens
    - _Requisitos: 8.2, Design seção 3_

  - [x] 3.3 Implementar conclusão e pagamento seguindo tokenomics
    - Consultar Planta Arquitetônica para sistema de taxas e pagamentos
    - Desenvolver função para marcar ordens como concluídas
    - Implementar liberação de escrow: tokens→prestador, taxa→admin (release_from_escrow)
    - Adicionar sistema de confirmação do cliente antes da liberação
    - Garantir que admin recebe taxa configurável (ex: 5%) de cada transação
    - Implementar logs de auditoria para todos os pagamentos
    - Criar testes para conclusão de ordens e distribuição de tokens
    - _Requisitos: 8.3, Planta Arquitetônica seção 7.5_

  - [x] 3.4 Desenvolver sistema de cancelamento e disputas com reembolso
    - Consultar Planta Arquitetônica para sistema de contestações
    - Implementar cancelamento de ordens com devolução de escrow (refund_from_escrow)
    - Criar sistema de disputas com bloqueio de tokens até resolução admin
    - Adicionar validações para cancelamentos (prazos, motivos válidos)
    - Implementar interface admin para resolver disputas conforme design
    - Garantir que tokens sempre retornam ao estado correto (saldo ou admin)
    - Desenvolver testes para cancelamentos e disputas
    - _Requisitos: 8.4, Planta Arquitetônica seção 7.4_

- [x] 4. Implementar sistema de convites completo conforme Planta Arquitetônica
  - [x] 4.1 Criar modelo e estrutura de dados para convites
    - Consultar Planta Arquitetônica seção 8.3 e Requirements 17 para especificação completa
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface
    - Implementar modelo Invite com campos essenciais: client_id, invited_email, service_title, service_description
    - Adicionar campos de valor: original_value, final_value (para negociação)
    - Implementar campos de controle: status, token único, timestamps
    - Criar relacionamentos com User e Order conforme Design
    - Desenvolver migração para tabela de convites
    - _Requisitos: 17, Planta Arquitetônica seção 8.3, Design seção 6_

  - [x] 4.2 Desenvolver InviteService com lógica de negócio
    - Consultar Requirements 18 para operações de negócio completas
    - Consultar Planta Arquitetônica para validações de saldo e fluxos
    - Implementar create_invite() com validação de saldo conforme tokenomics
    - Desenvolver accept_invite() e reject_invite() seguindo design
    - Adicionar update_invite_terms() para negociação de valor/data
    - Criar convert_invite_to_order() para conversão automática
    - Implementar sistema de expiração automática
    - _Requisitos: 18, Planta Arquitetônica, Design seção 6_

  - [x] 4.3 Criar interfaces para gerenciamento de convites
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de design
    - Consultar Requirements 13-14 para funcionalidades de interface
    - Implementar formulário de criação no dashboard cliente seguindo padrões
    - Criar página de listagem de convites enviados/recebidos
    - Adicionar interface para prestador responder convites
    - Desenvolver sistema de notificações conforme Requirements 19
    - Garantir terminologia "R$" para usuários conforme Planta seção 6.1
    - _Requisitos: 13, 14, 19, docs/PADRAO_TEMPLATES.md, Planta seção 6.1_

  - [x] 4.4 Implementar fluxo de cadastro via convite
    - Consultar Requirements 16 para fluxo de cadastro via convite
    - Consultar Planta Arquitetônica para segurança e validações
    - Criar página de acesso via token único seguindo padrões de templates
    - Implementar detecção automática usuário/cadastro
    - Desenvolver redirecionamento pós-cadastro
    - Adicionar validações de segurança conforme Requirements 6
    - _Requisitos: 16, Planta Arquitetônica, docs/PADRAO_TEMPLATES.md_

- [x] 5. Conectar dashboards com dados reais seguindo terminologia diferenciada
  - [x] 5.1 Implementar métricas reais no dashboard administrativo com terminologia técnica
    - Consultar Planta Arquitetônica seção 7.2 para cards e métricas do dashboard
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de design e cores
    - Conectar cards de estatísticas com dados reais do banco (get_system_token_summary)
    - Implementar contadores usando terminologia "tokens" para administradores
    - Adicionar métricas de tokenomics: tokens criados, em circulação, saldo admin
    - Implementar cards coloridos conforme design: usuários (azul), contestações (vermelho)
    - Conectar sistema de contestações com dados reais do banco
    - Criar testes para métricas administrativas
    - _Requisitos: 5.1, 12.1, Planta Arquitetônica seção 7.2, docs/PADRAO_TEMPLATES.md_

  - [x] 5.2 Completar dashboard do cliente com terminologia em R$ (saldo)
    - Consultar Planta Arquitetônica seção 6.1 para terminologia diferenciada
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface cliente
    - Conectar saldo da carteira usando get_wallet_info() mas exibindo como "R$"
    - Implementar histórico de transações usando get_transaction_history()
    - Adicionar lista de ordens criadas pelo cliente (status, valores em R$)
    - Desenvolver sistema de alertas para saldo baixo (sem mencionar "tokens")
    - Garantir que usuários vejam apenas "saldo em R$", nunca "tokens"
    - Implementar filtro format_currency para conversão automática
    - _Requisitos: 2.2, 3.1, 3.3, 9.2, Planta Arquitetônica seção 6, docs/PADRAO_TEMPLATES.md_

  - [x] 5.3 Finalizar dashboard do prestador com funcionalidades e terminologia R$
    - Consultar Requirements para funcionalidades específicas do prestador
    - Consultar Planta Arquitetônica seção 6.1 para terminologia diferenciada
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface prestador
    - Conectar saldo e ganhos usando get_wallet_info() exibindo como "R$"
    - Implementar lista de ordens disponíveis para aceitar (valores em R$)
    - Adicionar histórico de ordens aceitas e concluídas com get_transactions_by_order()
    - Criar sistema de alertas para novas oportunidades (sem terminologia técnica)
    - Implementar métricas de performance: taxa de conclusão, ganhos médios
    - Garantir terminologia consistente "saldo em R$" para prestadores
    - _Requisitos: 2.3, 4.1, 4.2, 4.3, 9.2, Planta Arquitetônica seção 6.1, docs/PADRAO_TEMPLATES.md_

- [x] 6. Implementar sistema de terminologia diferenciada conforme Planta Arquitetônica
  - [x] 6.1 Configurar filtros e contextos para terminologia seguindo seção 6 da Planta
    - Consultar Planta Arquitetônica seção 6.1 para diferenciação de terminologia
    - Consultar Requirements 9.1, 9.2, 9.3 para especificações de terminologia
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface por papel
    - Atualizar filtro format_currency para mostrar "R$" para usuários finais
    - Implementar contexto diferenciado para administradores (terminologia "tokens")
    - Adicionar validação rigorosa para não vazar terminologia técnica para usuários
    - Garantir que admin vê "1000 tokens" e usuários veem "R$ 1.000,00"
    - Implementar detecção automática de tipo de usuário (AdminUser vs User)
    - Criar testes para terminologia por tipo de usuário
    - _Requisitos: 9.1, 9.2, 9.3, Planta Arquitetônica seção 6, docs/PADRAO_TEMPLATES.md_

  - [x] 6.2 Implementar alternância de papéis para usuários dual mantendo terminologia
    - Consultar Requirements 9.4 para usuários dual (cliente+prestador)
    - Consultar Planta Arquitetônica seção 6.3 para alternância de papéis
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de navegação dual
    - Desenvolver sistema para usuários alternarem entre cliente/prestador
    - Manter terminologia correta "R$" em ambos os papéis (nunca "tokens")
    - Adicionar interface para seleção de papel ativo no dashboard
    - Implementar contexto de sessão para papel ativo atual
    - Garantir que funcionalidades mudam conforme papel mas terminologia permanece "R$"
    - Criar testes para usuários com múltiplos papéis
    - _Requisitos: 9.4, Planta Arquitetônica seção 6.3, docs/PADRAO_TEMPLATES.md_

- [x] 7. Desenvolver sistema de tratamento de erros robusto respeitando terminologia
  - [x] 7.1 Implementar páginas de erro personalizadas com design consistente
    - Consultar Planta Arquitetônica seção 7.6 para padrões de cores e design
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de templates de erro
    - Consultar Requirements 7.1, 7.2 para especificações de tratamento de erros
    - Atualizar templates 404.html e 500.html com design do sistema
    - Adicionar logging estruturado para erros 500 com contexto de usuário
    - Implementar redirecionamentos apropriados mantendo contexto de sessão
    - Garantir que páginas de erro respeitam terminologia por tipo de usuário
    - Criar testes para páginas de erro
    - _Requisitos: 7.1, 7.2, Planta Arquitetônica seção 7.6, docs/PADRAO_TEMPLATES.md_

  - [x] 7.2 Adicionar validações e mensagens de erro claras por tipo de usuário
    - Consultar Requirements seção 6 para segurança e proteção de dados
    - Consultar Planta Arquitetônica seção 6.1 para terminologia por usuário
    - Consultar Requirements 7.3, 7.4, 6.4, 9.2 para validações específicas
    - Implementar validações de formulário no frontend e backend
    - Criar mensagens de erro específicas: admin vê "tokens", usuários veem "R$"
    - Adicionar tratamento gracioso de falhas de conexão com banco
    - Implementar validações específicas para operações de tokenomics
    - Garantir que erros de saldo usam terminologia correta por usuário
    - Desenvolver testes para validações e tratamento de erros
    - _Requisitos: 7.3, 7.4, 6.4, 9.2, Planta Arquitetônica seção 6.1_

- [-] 8. Expandir suite de testes automatizados para cobrir arquitetura de tokenomics
  - [x] 8.1 Desenvolver testes unitários expandidos para modelos e serviços
    - Consultar Requirements 11.3 para cobertura de testes obrigatória
    - ✅ Expandir testes existentes do WalletService (33 testes já aprovados)
    - Criar testes específicos para arquitetura de tokenomics (admin como fonte)
    - Implementar testes para AdminUser e relacionamento com carteira ID 0
    - Adicionar testes para validação de integridade matemática do sistema
    - Testar fluxos admin→usuário e usuário→admin com diferentes cenários
    - Implementar testes para OrderService quando implementado
    - Configurar cobertura de testes para atingir mínimo de 90%
    - _Requisitos: 11.3, Arquitetura de Tokenomics_

  - [x] 8.2 Implementar testes de integração para fluxos completos de tokenomics
    - Consultar Planta Arquitetônica para fluxos críticos do sistema
    - Consultar Requirements 11.1, 11.2, 11.4 para especificações de testes
    - Criar testes para fluxo completo: login admin → criação tokens → venda usuário
    - Implementar testes para fluxo usuário: login → compra tokens → criação ordem → saque
    - Adicionar testes para fluxo prestador: login → aceitação ordem → recebimento → saque
    - Testar fluxo de disputas: ordem → disputa → resolução admin → distribuição tokens
    - Desenvolver testes para diferentes tipos de usuário respeitando terminologia
    - Implementar testes de integridade: verificar que tokens nunca "desaparecem"
    - Testar cenários de erro: saldo insuficiente, ordens inexistentes, etc.
    - _Requisitos: 11.1, 11.2, 11.4, Planta Arquitetônica_

- [ ] 9. Corrigir problemas críticos identificados no sistema
  - [x] 9.1 Implementar funcionalidade de troca de senha para admin
    - Consultar Planta Arquitetônica (docs/PLANTA_ARQUITETONICA.md) para padrões de segurança
    - Consultar Requirements e Design para validações de segurança necessárias
    - Criar interface no painel admin para alterar senha
    - Implementar validação de senha atual antes da alteração
    - Adicionar hash da nova senha usando werkzeug.security
    - Criar logs de auditoria para mudanças de senha admin
    - Testar funcionalidade de troca de senha
    - Atualizar Planta Arquitetônica se necessário com novos fluxos de segurança
    - _Requisitos: 6.1, 6.2_

  - [x] 9.2 Corrigir erro 500 na criação de usuários
    - Consultar Planta Arquitetônica para fluxo correto de criação de usuários
    - Consultar Requirements e Design para validações necessárias
    - Investigar logs de erro para identificar causa do erro 500
    - Corrigir problemas na validação de dados de usuário
    - Verificar criação automática de carteira para novos usuários
    - Implementar tratamento de erros mais robusto na criação
    - Testar criação de usuários admin e usuários comuns
    - Atualizar documentação se necessário com correções implementadas
    - _Requisitos: 7.2, 7.4_

  - [x] 9.3 Adicionar copyright e informações de versão
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface
    - Consultar Planta Arquitetônica para estrutura de templates
    - Adicionar copyright "W-jr (89) 98137-5841" em todos os templates base
    - Implementar sistema de versionamento do sistema
    - Adicionar informações de versão no footer das páginas
    - Criar página "Sobre" com informações do desenvolvedor
    - Atualizar Planta Arquitetônica com informações de versionamento
    - _Requisitos: Sistema de informações_

  - [x] 9.4 Corrigir funcionalidade do menu de contratos
    - Consultar Planta Arquitetônica seção de navegação e menus
    - Consultar Requirements 8.1, 8.2 para funcionalidades de ordens/contratos
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de menu
    - Investigar problemas no menu de contratos/ordens
    - Corrigir rotas e templates relacionados a contratos
    - Implementar listagem correta de ordens/contratos
    - Testar navegação completa do menu de contratos
    - Atualizar documentação com correções de navegação
    - _Requisitos: 2.5, 8.1, 8.2_

  - [x] 9.5 Implementar relatórios funcionais de contratos e usuários
    - Consultar Planta Arquitetônica seção 7.2 para dashboard e relatórios
    - Consultar Requirements 5.1, 12.1 para especificações de relatórios
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface de relatórios
    - Criar relatório de contratos com dados reais do banco
    - Implementar relatório de usuários com estatísticas
    - Adicionar filtros por data, status, tipo de usuário
    - Criar exportação de relatórios em PDF/Excel
    - Testar geração de relatórios com dados reais
    - Atualizar Planta Arquitetônica com funcionalidades de relatórios
    - _Requisitos: 5.1, 12.1_

  - [x] 9.6 Corrigir visibilidade do admin para recebimento de tokens
    - Consultar Planta Arquitetônica seção de tokenomics e admin como fonte central
    - Consultar Requirements 5.3, 10.1 para gestão de tokens admin
    - Verificar por que admin não aparece na lista de usuários
    - Corrigir filtros de usuários para incluir AdminUser
    - Implementar interface para admin receber tokens de outros admins
    - Testar transferência de tokens para conta admin
    - Atualizar Planta Arquitetônica se necessário com fluxos de tokens admin
    - _Requisitos: 5.3, 10.1_

- [x] 10. Implementar dashboard financeiro avançado
  - [x] 10.1 Criar cards de taxas recebidas na dashboard admin
    - Consultar Planta Arquitetônica seção 7.2 para dashboard e métricas
    - Consultar Requirements 12.1 para especificações de cards
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de design de cards
    - Implementar cálculo de taxas totais recebidas pelo sistema
    - Criar card colorido mostrando receita de taxas em tempo real
    - Adicionar gráfico de evolução das taxas por período
    - Implementar métricas de taxa média por transação
    - Atualizar Planta Arquitetônica com novas métricas financeiras
    - _Requisitos: 12.1, Planta Arquitetônica seção 7.2_

  - [x] 10.2 Desenvolver aba financeira completa para admin
    - Consultar Planta Arquitetônica seção 7.5 para configurações financeiras
    - Consultar Requirements para sistema financeiro e configurações
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de interface financeira
    - Criar nova seção "Financeiro" no menu lateral admin
    - Implementar dashboard financeiro com receitas e custos
    - Adicionar relatórios financeiros detalhados
    - Criar interface para configurar taxas do sistema
    - Implementar previsões e análises financeiras
    - Preparar estrutura para futuros pagamentos de clientes
    - Atualizar Planta Arquitetônica com nova seção financeira
    - _Requisitos: Sistema financeiro, 12.1_

  - [x] 10.3 Implementar card de valores totais em circulação
    - Consultar Planta Arquitetônica seção de tokenomics para arquitetura de tokens
    - Consultar Requirements 10.1, 10.3 para arquitetura de tokenomics
    - Consultar docs/PADRAO_TEMPLATES.md para padrões de cards de métricas
    - Criar card mostrando total de tokens em circulação
    - Adicionar breakdown por tipo: saldo usuários, escrow, admin
    - Implementar alertas para inconsistências nos totais
    - Criar gráfico de distribuição de tokens no sistema
    - Adicionar histórico de evolução da circulação
    - Atualizar Planta Arquitetônica com métricas de circulação
    - _Requisitos: 10.1, 10.3, Arquitetura de Tokenomics_

- [ ] 11. Corrigir problemas críticos identificados no sistema
  - [x] 11.1 Corrigir erro 500 na troca de senha do admin
    - Consultar Requirements 20 e Design seção "Correções Críticas" para especificações
    - Implementar AdminService.change_admin_password() com tratamento robusto de erros
    - Atualizar rota alterar_senha() com try-catch adequado e validações rigorosas
    - Adicionar logs de auditoria para mudanças de senha admin
    - Garantir que sessão permaneça ativa após troca de senha bem-sucedida
    - Testar cenários: senha atual incorreta, senhas não coincidem, erro de banco
    - _Requisitos: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 11.2 Corrigir erro 500 na análise de contestações/disputas
    - Consultar Requirements 21 e Design seção "Sistema de Contestações Real"
    - Implementar AdminService.get_contestacoes() conectando com dados reais do banco
    - Criar AdminService.get_contestacao_details() para buscar detalhes completos
    - Atualizar rota analisar_contestacao() para usar ordens com status 'disputada'
    - Implementar interface funcional para resolução de disputas
    - Integrar com OrderService para distribuição de tokens conforme decisão
    - Testar fluxo: listar contestações → analisar disputa → tomar decisão → resolver
    - _Requisitos: 21.1, 21.2, 21.3, 21.4, 21.5_

  - [-] 11.3 Implementar sistema de papéis duais funcionais
    - Consultar Requirements 22 e Design seção "Interface de Papéis Duais"
    - Implementar interface de alternância de papéis no dashboard de usuários
    - Criar middleware @app.context_processor para injetar contexto de papel
    - Adicionar rota /switch-role/<role> para alternância entre cliente/prestador
    - Atualizar navegação para refletir papel ativo atual do usuário
    - Garantir que convites funcionem independente do papel ativo
    - Testar usuário dual: alternar papel → criar convite → receber convite → aceitar
    - _Requisitos: 22.1, 22.2, 22.3, 22.4, 22.5_

  - [ ] 11.4 Adicionar campos necessários ao modelo Order para disputas
    - Consultar Design seção "Sistema de Contestações Real" para campos necessários
    - Adicionar campos dispute_reason, dispute_opened_by, dispute_opened_at ao modelo Order
    - Criar migração para adicionar novos campos de disputa
    - Atualizar OrderService.open_dispute() para usar novos campos
    - Implementar OrderService.resolve_dispute() com distribuição de tokens
    - Testar integridade: criar ordem → disputar → resolver → verificar tokens
    - _Requisitos: 21.3, 21.4, 21.5_

- [ ] 12. Finalizar e documentar o sistema completo seguindo PDR rigoroso
  - [ ] 12.1 Realizar testes de ponta a ponta validando todas as correções
    - Testar fluxo completo admin: login → troca senha → criação usuários → gestão tokens
    - Testar sistema de contestações: listar → analisar → resolver disputas
    - Validar papéis duais: alternar papel → usar funcionalidades → manter contexto
    - Verificar dashboard financeiro com dados reais
    - Confirmar copyright e versão em todas as páginas
    - Testar cenários de erro corrigidos (sem mais 500s)
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 20.1-20.5, 21.1-21.5, 22.1-22.5_

  - [ ] 12.2 Atualizar documentação completa com todas as correções
    - Documentar todas as correções críticas implementadas
    - Atualizar guia do admin com funcionalidades de contestação
    - Criar documentação do sistema de papéis duais
    - Atualizar STATUS_SISTEMA.md com problemas resolvidos
    - Documentar sistema de versionamento e copyright
    - Criar relatório final de correções implementadas
    - _Requisitos: 11.1, 11.2, 11.4, PDR Etapas 6-7_

- [-] 10. Implementar funcionalidades administrativas avançadas conforme Planta
  - [x] 10.1 Desenvolver interface de gestão de tokens para admin
    - Consultar Planta Arquitetônica seção 7.3 para menu de tokens
    - Implementar interface para admin criar novos tokens (admin_create_tokens)
    - Adicionar visualização de resumo do sistema (get_system_token_summary)
    - Criar interface para monitorar tokens em circulação vs saldo admin
    - Implementar alertas para admin sobre atividade suspeita ou inconsistências
    - Adicionar logs de auditoria para todas as ações administrativas
    - _Requisitos: 5.3, Planta Arquitetônica seção 7.3_

  - [x] 10.2 Implementar sistema de configurações avançadas
    - Consultar Planta Arquitetônica seção 7.5 para configurações do sistema
    - Implementar interface para configurar taxas (% que admin recebe por transação)
    - Adicionar configuração de limites: saque mínimo, máximo por usuário, etc.
    - Criar sistema de backup automático de dados críticos (saldos, transações)
    - Implementar monitoramento de integridade automático com alertas
    - Adicionar configurações de segurança: timeouts, tentativas de login, etc.
    - _Requisitos: Planta Arquitetônica seção 7.5, 6.4_