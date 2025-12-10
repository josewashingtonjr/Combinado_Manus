# Tarefas - Otimização Mobile e Usabilidade

## Fase 1: Simplificação dos Convites

- [x] 1. Remover Funcionalidades de Proposta dos Templates de Convite
  - Remover modal de "Propor Alteração" de `templates/prestador/ver_convite.html`
  - Remover modal de "Propor Alteração" de `templates/cliente/ver_convite.html`
  - Remover seção de contrapropostas dos templates
  - Manter apenas botões "Aceitar" e "Recusar"
  - Adicionar mensagem informativa sobre negociação na pré-ordem
  - _Requirements: 1.1, 1.2_

- [x] 2. Simplificar Rotas de Convite
  - Remover ou deprecar rota `alterar_termos_convite` em `routes/prestador_routes.py`
  - Atualizar `routes/proposal_routes.py` para redirecionar para pré-ordem
  - Garantir que aceitação de convite cria pré-ordem automaticamente
  - Adicionar redirecionamento para pré-ordem após aceitar convite
  - _Requirements: 1.3_

- [x] 3. Atualizar Serviço de Convites
  - Simplificar `InviteService` removendo métodos de proposta
  - Garantir que `accept_invite` cria pré-ordem
  - Manter apenas `accept_invite` e `reject_invite` como ações principais
  - _Requirements: 1.1, 1.2_

## Fase 2: CSS Mobile-First

- [x] 4. Criar CSS de Touch Targets
  - Criar arquivo `static/css/touch-targets.css`
  - Definir classe `.touch-target` com min-height: 48px
  - Definir classe `.btn-mobile` para botões otimizados
  - Adicionar espaçamento adequado entre elementos clicáveis
  - Implementar estados :active para feedback visual
  - _Requirements: 2.1, 2.2_

- [x] 5. Criar CSS Mobile-First Base
  - Criar arquivo `static/css/mobile-first.css`
  - Definir breakpoints consistentes (576px, 768px, 992px)
  - Implementar layout de coluna única para mobile
  - Garantir fonte mínima de 16px
  - Remover scroll horizontal em todos os containers
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 6. Atualizar Estilos de Botões
  - Aumentar tamanho de botões de ação para 48px altura
  - Usar cores mais contrastantes
  - Adicionar ícones aos botões principais
  - Implementar hierarquia visual clara (primário/secundário/destrutivo)
  - _Requirements: 2.3, 2.4_

## Fase 3: Templates Simplificados

- [x] 7. Criar Template de Convite Simplificado
  - Criar novo template `templates/components/convite-card-simple.html`
  - Exibir apenas: título, valor, prazo, status
  - Botões grandes de Aceitar/Recusar
  - Remover informações secundárias para acordeão
  - _Requirements: 1.4, 3.4_

- [x] 8. Criar Componente de Navegação Mobile
  - Criar `templates/components/mobile-nav.html`
  - Implementar barra fixa no rodapé
  - Usar ícones grandes e reconhecíveis
  - Destacar página atual
  - Adicionar badge para notificações
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 9. Criar Componente de Feedback Toast
  - Criar `templates/components/toast-feedback.html`
  - Criar `static/css/toast-feedback.css`
  - Criar `static/js/toast-feedback.js`
  - Implementar toast não-bloqueante
  - Cores semânticas (sucesso/erro/aviso/info)
  - Auto-dismiss após 5 segundos
  - Botão de fechar manual
  - Barra de progresso visual
  - Integrar no `templates/base.html`
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

## Fase 4: JavaScript Interativo

- [x] 10. Criar Script de Feedback Touch
  - Criar `static/js/touch-feedback.js`
  - Implementar ripple effect em botões
  - Adicionar feedback visual ao tocar
  - Prevenir duplo clique/tap
  - Integrar com botões existentes
  - _Requirements: 2.4, 2.5_

- [x] 11. Criar Script de Loading States
  - Criar `static/js/loading-states.js`
  - Implementar spinner em botões durante ação
  - Desabilitar botão durante processamento
  - Mostrar skeleton loading para conteúdo
  - Integrar com formulários e ações AJAX
  - _Requirements: 5.1, 8.2_

- [x] 12. Criar Script de Validação de Formulários
  - Criar `static/js/form-helpers.js`
  - Implementar validação em tempo real
  - Adicionar máscaras para telefone e valores
  - Mostrar mensagens de erro claras
  - Usar teclado apropriado para cada campo
  - Integrar com toast feedback
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

## Fase 5: Acessibilidade

- [x] 13. Melhorar Contraste e Cores
  - Auditar contraste de todas as cores
  - Garantir ratio mínimo de 4.5:1
  - Adicionar modo de alto contraste opcional
  - Testar com simulador de daltonismo
  - Documentar conformidade
  - _Requirements: 7.1_

- [x] 14. Adicionar Labels e ARIA
  - Garantir label em todos os campos de formulário
  - Adicionar aria-label em ícones
  - Implementar aria-live para mensagens dinâmicas
  - Testar navegação por teclado
  - Validar com leitores de tela
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 15. Otimizar para Zoom
  - Testar layout com zoom de 200%
  - Corrigir quebras de layout
  - Garantir que texto não seja cortado
  - Manter funcionalidade com zoom
  - Validar em diferentes dispositivos
  - _Requirements: 7.2_

## Fase 6: Performance

- [x] 16. Otimizar Carregamento
  - Minificar CSS e JS
  - Implementar lazy loading para imagens
  - Cachear assets estáticos
  - Comprimir respostas do servidor
  - Medir e documentar melhorias
  - _Requirements: 8.1, 8.3, 8.5_

- [x] 17. Implementar Skeleton Loading
  - Criar componentes de skeleton
  - Aplicar em listas de convites/ordens
  - Aplicar em cards de detalhes
  - Melhorar percepção de velocidade
  - Integrar com loading states
  - _Requirements: 8.2_

## Fase 7: Testes e Validação

- [ ] 18. Testar em Dispositivos Reais
  - Testar em Android (Chrome)
  - Testar em iOS (Safari)
  - Testar em tablets
  - Documentar problemas encontrados
  - Criar relatório de compatibilidade
  - _Requirements: Todos_

- [ ] 19. Testar com Usuários Leigos
  - Recrutar 5 usuários sem experiência técnica
  - Observar uso do sistema
  - Coletar feedback
  - Iterar baseado em problemas encontrados
  - Documentar melhorias sugeridas
  - _Requirements: 1.4, 9.1, 9.2_

- [ ] 20. Validar Acessibilidade
  - Rodar Lighthouse accessibility audit
  - Testar com leitor de tela (NVDA/VoiceOver)
  - Corrigir problemas encontrados
  - Documentar conformidade WCAG
  - Gerar relatório final
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
