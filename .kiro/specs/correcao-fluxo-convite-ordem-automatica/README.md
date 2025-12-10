# Correção do Fluxo de Convite para Ordem Automática

## Descrição

Esta spec corrige o problema crítico onde convites aceitos por ambas as partes (cliente e prestador) não estão gerando automaticamente ordens de serviço nem bloqueando os valores necessários em escrow.

## Problema Atual

1. **Fluxo Quebrado**: Quando cliente e prestador aceitam um convite, nada acontece automaticamente
2. **Bloqueio Manual**: Valores não são bloqueados em escrow
3. **Dashboards Incompletas**: Ordens em aberto e fundos bloqueados não aparecem
4. **Falta de Notificações**: Usuários não sabem quando ordens são criadas

## Solução

Implementar sistema de aceitação mútua que:
- Detecta quando ambas as partes aceitaram
- Cria ordem automaticamente
- Bloqueia valores em escrow atomicamente
- Atualiza dashboards em tempo real
- Envia notificações apropriadas

## Arquivos da Spec

- **requirements.md**: 10 requisitos detalhados com critérios de aceitação
- **design.md**: Arquitetura completa, componentes, fluxos e diagramas
- **tasks.md**: 16 tarefas de implementação organizadas em fases

## Componentes Principais

1. **InviteAcceptanceCoordinator** (Novo)
   - Coordena aceitação mútua
   - Cria ordem quando ambos aceitam
   - Bloqueia valores atomicamente

2. **DashboardDataService** (Novo)
   - Agrega dados de ordens em aberto
   - Calcula fundos bloqueados
   - Fornece métricas para dashboards

3. **InviteService** (Atualização)
   - Métodos separados para aceitação de cliente e prestador
   - Validação de saldos antes da aceitação
   - Integração com coordenador

4. **NotificationService** (Atualização)
   - Notificações de criação de ordem
   - Alertas de saldo insuficiente

## Fases de Implementação

1. **Fase 1**: Modelo e Migração (Tarefa 1)
2. **Fase 2**: Serviços Core (Tarefas 2-4)
3. **Fase 3**: Rotas e Controllers (Tarefas 5-7)
4. **Fase 4**: Templates e UI (Tarefas 8-9)
5. **Fase 5**: Notificações e Logging (Tarefas 10-11)
6. **Fase 6**: Tratamento de Erros (Tarefa 12)
7. **Fase 7**: Tempo Real (Tarefa 13)
8. **Fase 8**: Testes (Tarefas 14-16)

## Como Executar

Para começar a implementação, abra o arquivo `tasks.md` e clique em "Start task" na primeira tarefa.

## Requisitos Técnicos

- Python 3.11+
- Flask
- SQLAlchemy
- PostgreSQL ou SQLite
- WebSocket (para tempo real)

## Impacto

Esta correção é **crítica** pois:
- Resolve fluxo principal do sistema
- Garante segurança financeira (escrow)
- Melhora experiência do usuário
- Previne estados inconsistentes

## Status

- [x] Requirements - Aprovado
- [x] Design - Aprovado
- [x] Tasks - Aprovado
- [ ] Implementation - Pendente
