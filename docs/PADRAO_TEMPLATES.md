# Padrão de Templates - Sistema Combinado

## Visão Geral

Este documento define os padrões e diretrizes para criação e manutenção de templates no Sistema Combinado, garantindo consistência visual, funcional e de experiência do usuário em toda a aplicação.

## Estrutura Hierárquica de Templates

### 1. Template Base (`templates/base.html`)

**Responsabilidades:**
- Estrutura HTML5 básica
- Meta tags essenciais (charset, viewport)
- Inclusão de Bootstrap 5.1.3 e Font Awesome 6.0.0
- Sistema de mensagens flash padronizado
- Blocos principais: `title`, `navbar`, `content`, `footer`, `extra_css`, `extra_js`

**Padrão de Blocos:**
```html
{% block title %}Sistema Combinado{% endblock %}
{% block navbar %}{% endblock %}
{% block content %}{% endblock %}
{% block footer %}{% endblock %}
{% block extra_css %}{% endblock %}
{% block extra_js %}{% endblock %}
```

### 2. Templates Base por Papel

#### 2.1 Admin (`templates/admin/base_admin.html`)
- **Herda:** `base.html`
- **Cor Principal:** Azul (`bg-primary`)
- **Ícone:** `fas fa-cog` (Engrenagem)
- **Terminologia:** "Tokens" (técnica)
- **Layout:** Sidebar expansível com subcategorias + conteúdo principal
- **Bloco Principal:** `admin_content`

#### 2.2 Cliente (`templates/cliente/base_cliente.html`)
- **Herda:** `base.html`
- **Cor Principal:** Verde (`bg-success`)
- **Ícone:** `fas fa-user-tie` (Cliente)
- **Terminologia:** "Saldo em R$" (amigável)
- **Layout:** Sidebar simples + cards de informação rápida
- **Bloco Principal:** `cliente_content`

#### 2.3 Prestador (`templates/prestador/base_prestador.html`)
- **Herda:** `base.html`
- **Cor Principal:** Amarelo (`bg-warning`)
- **Ícone:** `fas fa-user-cog` (Prestador)
- **Terminologia:** "Saldo em R$" (amigável)
- **Layout:** Sidebar + cards de oportunidades e saldo
- **Bloco Principal:** `prestador_content`

## Padrões de Design

### 1. Cores Semânticas

| Contexto | Cor | Classe Bootstrap | Uso |
|----------|-----|------------------|-----|
| Admin | Azul | `bg-primary` | Navegação, cards informativos |
| Cliente | Verde | `bg-success` | Navegação, status positivo |
| Prestador | Amarelo | `bg-warning` | Navegação, alertas |
| Erro/Urgente | Vermelho | `bg-danger` | Contestações, erros |
| Informação | Azul claro | `bg-info` | Dados complementares |
| Neutro | Cinza | `bg-secondary` | Configurações, logs |

### 2. Ícones Padronizados (Font Awesome)

| Funcionalidade | Ícone | Contexto |
|----------------|-------|----------|
| Dashboard | `fas fa-tachometer-alt` | Todos os papéis |
| Usuários | `fas fa-users` | Admin, listagens |
| Carteira/Saldo | `fas fa-wallet` | Cliente, Prestador |
| Tokens | `fas fa-coins` | Admin (técnico) |
| Ordens | `fas fa-clipboard-list` | Cliente, Prestador |
| Contestações | `fas fa-exclamation-triangle` | Admin |
| Configurações | `fas fa-cogs` | Admin |
| Relatórios | `fas fa-chart-bar` | Admin |
| Logs | `fas fa-list-alt` | Admin |
| Sair | `fas fa-sign-out-alt` | Todos |
| Perfil | `fas fa-user-edit` | Cliente, Prestador |
| Troca de Papel | `fas fa-exchange-alt` | Usuários dual |

### 3. Layout Responsivo

**Desktop (≥768px):**
- Sidebar visível (2/12 colunas)
- Conteúdo principal (10/12 colunas)
- Menu lateral expansível (admin)

**Mobile (<768px):**
- Sidebar oculta
- Navbar superior com menu hambúrguer
- Conteúdo em largura total
- Cards empilhados verticalmente

## Padrões de Componentes

### 1. Cards de Métricas

**Estrutura Padrão:**
```html
<div class="col-md-3 mb-4">
    <div class="card border-0 shadow-sm">
        <div class="card-body text-center">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="card-title text-muted mb-1">TÍTULO</h6>
                    <h3 class="mb-0 text-CONTEXTO">VALOR</h3>
                </div>
                <div class="text-CONTEXTO">
                    <i class="fas fa-ICONE fa-2x"></i>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 2. Sidebar Expansível (Admin)

**Estrutura:**
- Header azul com título "Acesso Rápido"
- Categorias principais com ícones coloridos
- Subcategorias com indentação (ps-4)
- Animação Bootstrap Collapse

### 3. Mensagens Flash

**Classes Padronizadas:**
- `alert-success`: Sucesso
- `alert-danger`: Erro
- `alert-warning`: Aviso
- `alert-info`: Informação

### 4. Formulários

**Padrão de Campos:**
```html
<div class="mb-3">
    <label for="campo" class="form-label">Label</label>
    <input type="text" class="form-control" id="campo" name="campo" required>
    <div class="form-text">Texto de ajuda (opcional)</div>
</div>
```

## Terminologia por Papel

### 1. Administrador
- **Linguagem:** Técnica
- **Valores:** "1000 tokens", "Tokenomics"
- **Interface:** Completa com métricas técnicas
- **Filtros:** Sem conversão de terminologia

### 2. Cliente/Prestador
- **Linguagem:** Amigável
- **Valores:** "R$ 1.000,00", "Saldo"
- **Interface:** Simplificada
- **Filtros:** `|format_currency` obrigatório

### 3. Implementação
```html
<!-- Admin -->
<span>{{ valor }} tokens</span>

<!-- Cliente/Prestador -->
<span>{{ valor|format_currency }}</span>
```

## Padrões de Navegação

### 1. Breadcrumbs (quando aplicável)
```html
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="#">Home</a></li>
        <li class="breadcrumb-item active">Página Atual</li>
    </ol>
</nav>
```

### 2. Paginação
```html
<nav aria-label="Navegação de páginas">
    <ul class="pagination justify-content-center">
        <!-- Itens de paginação -->
    </ul>
</nav>
```

### 3. Troca de Papéis (Usuários Dual)
- Botão destacado na navbar
- Ícone `fas fa-exchange-alt`
- Classe `btn-outline-light`

## Padrões de Acessibilidade

### 1. Obrigatórios
- `alt` em todas as imagens
- `aria-label` em botões sem texto
- `role` em elementos interativos
- Contraste adequado (WCAG 2.1)

### 2. Navegação por Teclado
- `tabindex` apropriado
- Foco visível
- Atalhos de teclado (quando aplicável)

### 3. Leitores de Tela
- Estrutura semântica (h1, h2, etc.)
- Labels descritivos
- Texto alternativo informativo

## Padrões de Performance

### 1. CSS/JS
- Bootstrap e Font Awesome via CDN
- CSS customizado em arquivo separado
- JS customizado no final do body

### 2. Imagens
- Formatos otimizados (WebP quando possível)
- Lazy loading para imagens não críticas
- Dimensões apropriadas

## Validação e Testes

### 1. Checklist de Template
- [ ] Herda do template base correto
- [ ] Usa terminologia apropriada ao papel
- [ ] Implementa responsividade
- [ ] Segue padrões de cores
- [ ] Inclui ícones padronizados
- [ ] Atende critérios de acessibilidade
- [ ] Funciona em diferentes navegadores

### 2. Testes Obrigatórios
- Renderização em Chrome, Firefox, Safari
- Responsividade em diferentes resoluções
- Navegação por teclado
- Validação HTML5

## Estrutura de Arquivos

```
templates/
├── base.html                    # Template base principal
├── admin/
│   ├── base_admin.html         # Base para admin
│   ├── dashboard.html          # Dashboard admin
│   └── ...                     # Outras páginas admin
├── cliente/
│   ├── base_cliente.html       # Base para cliente
│   ├── dashboard.html          # Dashboard cliente
│   └── ...                     # Outras páginas cliente
├── prestador/
│   ├── base_prestador.html     # Base para prestador
│   ├── dashboard.html          # Dashboard prestador
│   └── ...                     # Outras páginas prestador
├── auth/
│   ├── admin_login.html        # Login admin
│   ├── user_login.html         # Login usuário
│   └── ...                     # Outras páginas auth
├── errors/
│   ├── 404.html               # Página não encontrada
│   ├── 500.html               # Erro interno
│   └── ...                    # Outros erros
└── home/
    └── index.html             # Página inicial
```

## Convenções de Nomenclatura

### 1. Arquivos
- Snake_case: `base_admin.html`
- Descritivo: `criar_ordem.html`
- Agrupado por funcionalidade

### 2. Classes CSS
- Bootstrap padrão quando possível
- Prefixo `sc-` para classes customizadas
- BEM methodology para componentes complexos

### 3. IDs e Names
- Camel_case: `formCriarOrdem`
- Descritivos e únicos
- Sem caracteres especiais

## Manutenção e Evolução

### 1. Versionamento
- Documentar mudanças significativas
- Manter compatibilidade com versões anteriores
- Testar impacto em todos os templates

### 2. Refatoração
- Revisar padrões a cada 6 meses
- Atualizar dependências (Bootstrap, Font Awesome)
- Otimizar performance continuamente

---

**Última Atualização:** 06 de Outubro de 2025  
**Versão:** 1.0.0  
**Responsável:** Equipe de Desenvolvimento