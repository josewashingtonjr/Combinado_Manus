# Design - Otimização Mobile e Usabilidade

## Visão Geral da Arquitetura

O sistema será otimizado seguindo a abordagem Mobile-First, com foco em simplicidade e acessibilidade para usuários leigos.

## Componentes Principais

### 1. Sistema de Design Mobile-First

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CSS       │  │  Templates  │  │    JavaScript       │  │
│  │   Mobile    │  │  Simplifi-  │  │    Interativo       │  │
│  │   First     │  │  cados      │  │    (Touch/Feedback) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Estrutura de Arquivos

```
static/
├── css/
│   ├── mobile-first.css      # Estilos base mobile
│   ├── touch-targets.css     # Botões e áreas clicáveis
│   └── accessibility.css     # Acessibilidade
├── js/
│   ├── touch-feedback.js     # Feedback visual touch
│   ├── form-helpers.js       # Máscaras e validação
│   └── loading-states.js     # Estados de carregamento
templates/
├── components/
│   ├── mobile-nav.html       # Navegação mobile
│   ├── action-buttons.html   # Botões padronizados
│   └── feedback-toast.html   # Mensagens de feedback
```

## Propriedades de Correção

### Property 1: Convites Simplificados
- **Descrição**: Interface de convites deve conter apenas aceitar/recusar
- **Validação**: Template de convite não deve conter formulários de proposta
- **Relacionado**: Requirement 1, Requirement 12 (spec pré-ordem)

### Property 2: Touch Targets Adequados
- **Descrição**: Todos os elementos interativos devem ter área mínima de 48x48px
- **Validação**: CSS deve definir min-height e min-width para botões
- **Relacionado**: Requirement 2

### Property 3: Responsividade Sem Scroll Horizontal
- **Descrição**: Layout não deve causar scroll horizontal em nenhum dispositivo
- **Validação**: max-width: 100% em containers e imagens
- **Relacionado**: Requirement 3

### Property 4: Feedback Visual Consistente
- **Descrição**: Toda ação deve ter feedback visual imediato
- **Validação**: Botões devem ter estados :active e :disabled
- **Relacionado**: Requirement 5

### Property 5: Formulários Acessíveis
- **Descrição**: Campos devem ter labels e validação clara
- **Validação**: Todos os inputs devem ter label associado
- **Relacionado**: Requirement 6, Requirement 7

## Decisões de Design

### D1: Remoção de Propostas dos Convites

**Contexto**: Atualmente os templates de convite contêm funcionalidades de proposta/contraproposta que deveriam estar apenas na pré-ordem.

**Decisão**: Remover modais e formulários de proposta dos templates de convite, mantendo apenas:
- Botão "Aceitar Convite"
- Botão "Recusar Convite"
- Informações do serviço (somente leitura)

**Consequências**:
- Simplifica a interface para o usuário
- Alinha com a spec de pré-ordem (Requirement 12)
- Reduz confusão sobre onde negociar

### D2: Navegação Mobile Fixa

**Contexto**: Usuários de celular precisam de navegação acessível sem scroll.

**Decisão**: Implementar barra de navegação fixa no rodapé com ícones grandes:
- 🏠 Home/Dashboard
- 📋 Convites/Pré-Ordens
- 📦 Ordens
- 👤 Perfil

**Consequências**:
- Navegação sempre acessível
- Padrão familiar (apps nativos)
- Área de conteúdo reduzida (compensada por scroll)

### D3: Botões de Ação Destacados

**Contexto**: Usuários leigos precisam identificar claramente o que fazer.

**Decisão**: Usar hierarquia visual clara:
- Ação principal: Botão grande, cor primária, 100% largura em mobile
- Ação secundária: Botão outline, menor destaque
- Ação destrutiva: Botão vermelho, com confirmação

**Consequências**:
- Reduz erros de clique
- Guia o usuário para ação correta
- Previne ações acidentais

### D4: Feedback Toast Não-Bloqueante

**Contexto**: Mensagens de feedback não devem interromper o fluxo.

**Decisão**: Usar toasts no topo da tela que:
- Aparecem automaticamente após ações
- Desaparecem após 5 segundos
- Podem ser fechados manualmente
- Não bloqueiam interação

**Consequências**:
- Usuário informado sem interrupção
- Experiência mais fluida
- Menos cliques necessários

## Fluxos Simplificados

### Fluxo de Aceitar Convite (Simplificado)

```
┌─────────────────┐
│  Ver Convite    │
│  (Informações)  │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Aceitar │ ◄── Botão grande, verde
    └────┬────┘
         │
┌────────▼────────┐
│   Confirmação   │
│   "Tem certeza?"│
└────────┬────────┘
         │
    ┌────▼────┐
    │ Sucesso │ ◄── Toast verde
    └────┬────┘
         │
┌────────▼────────┐
│  Redireciona    │
│  Pré-Ordem      │
└─────────────────┘
```

### Fluxo de Recusar Convite (Simplificado)

```
┌─────────────────┐
│  Ver Convite    │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Recusar │ ◄── Botão outline, vermelho
    └────┬────┘
         │
┌────────▼────────┐
│   Motivo        │
│   (Opcional)    │
└────────┬────────┘
         │
┌────────▼────────┐
│   Confirmação   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Sucesso │
    └────┬────┘
         │
┌────────▼────────┐
│  Volta Lista    │
└─────────────────┘
```

## Componentes Reutilizáveis

### Botão de Ação Principal

```html
<button class="btn-action-primary touch-target">
    <i class="icon"></i>
    <span class="btn-text">Texto da Ação</span>
</button>
```

```css
.btn-action-primary {
    min-height: 48px;
    width: 100%;
    font-size: 18px;
    font-weight: 600;
    border-radius: 12px;
    background: var(--primary-color);
    color: white;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn-action-primary:active {
    transform: scale(0.98);
    opacity: 0.9;
}
```

### Card de Convite Simplificado

```html
<div class="invite-card-simple">
    <div class="invite-header">
        <h3 class="invite-title">{{ titulo }}</h3>
        <span class="invite-status badge">{{ status }}</span>
    </div>
    <div class="invite-body">
        <p class="invite-value">R$ {{ valor }}</p>
        <p class="invite-date">Prazo: {{ data }}</p>
    </div>
    <div class="invite-actions">
        <button class="btn-accept">Aceitar</button>
        <button class="btn-reject">Recusar</button>
    </div>
</div>
```

## Métricas de Sucesso

1. **Tempo para completar ação**: < 3 cliques para aceitar/recusar convite
2. **Taxa de erro**: < 5% de cliques em botão errado
3. **Satisfação**: > 80% de usuários conseguem usar sem ajuda
4. **Performance**: < 3s para carregar em 3G
