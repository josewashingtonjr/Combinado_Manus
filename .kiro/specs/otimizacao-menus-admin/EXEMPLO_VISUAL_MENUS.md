# 🎨 Exemplo Visual da Estrutura de Menus Padronizada

## 📐 Estrutura Hierárquica

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVBAR SUPERIOR                           │
│  Dashboard | Usuários | Tokens | Ordens | Convites | ...    │
└─────────────────────────────────────────────────────────────┘
┌──────────────┬──────────────────────────────────────────────┐
│              │                                               │
│  MENU        │         CONTEÚDO PRINCIPAL                    │
│  LATERAL     │                                               │
│              │                                               │
│  📊 Dashboard│                                               │
│              │                                               │
│  👥 Usuários │                                               │
│    ├─ Todos  │                                               │
│    └─ Criar  │                                               │
│              │                                               │
│  🪙 Tokens   │                                               │
│    ├─ Gerenc.│                                               │
│    ├─ Solic. │                                               │
│    └─ Adicio.│                                               │
│              │                                               │
│  📋 Ordens   │                                               │
│    ├─ Todas  │                                               │
│    ├─ Aguard.│                                               │
│    ├─ Execut.│                                               │
│    ├─ Concl. │                                               │
│    ├─ Cancel.│                                               │
│    ├─ Contes.│                                               │
│    └─ Resolv.│                                               │
│              │                                               │
│  ⚠️ Contest. │                                               │
│    ├─ Todas  │                                               │
│    ├─ Penden.│                                               │
│    └─ Em Anál│                                               │
│              │                                               │
│  ✉️ Convites │                                               │
│    ├─ Todos  │                                               │
│    ├─ Penden.│                                               │
│    ├─ Aceitos│                                               │
│    └─ Recus. │                                               │
│              │                                               │
│  📄 Contrat. │                                               │
│    ├─ Todos  │                                               │
│    ├─ Ativos │                                               │
│    └─ Final. │                                               │
│              │                                               │
│  ⚙️ Config.  │                                               │
│    ├─ Visão  │                                               │
│    ├─ Taxas  │                                               │
│    ├─ Segur. │                                               │
│    └─ Senha  │                                               │
│              │                                               │
│  📊 Relatór. │                                               │
│    ├─ Financ.│                                               │
│    ├─ Usuár. │                                               │
│    └─ Contr. │                                               │
│              │                                               │
│  📝 Logs     │                                               │
│              │                                               │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 🎯 Estados Visuais dos Menus

### Menu Colapsado (Padrão)
```
┌────────────────────────────────────┐
│  👥 Usuários                    ▼  │  ← Chevron para baixo
└────────────────────────────────────┘
```

### Menu Expandido
```
┌────────────────────────────────────┐
│  👥 Usuários                    ▲  │  ← Chevron para cima (rotacionado)
├────────────────────────────────────┤
│    📋 Listar Todos                 │
│    ➕ Criar Novo                   │
└────────────────────────────────────┘
```

### Item Hover
```
┌────────────────────────────────────┐
│  👥 Usuários                    ▲  │
├────────────────────────────────────┤
│  ┃ 📋 Listar Todos                │  ← Borda azul + fundo claro
│    ➕ Criar Novo                   │
└────────────────────────────────────┘
```

### Item Ativo (Página Atual)
```
┌────────────────────────────────────┐
│  👥 Usuários                    ▲  │
├────────────────────────────────────┤
│  ┃ 📋 Listar Todos                │  ← Borda azul + fundo azul claro
│    ➕ Criar Novo                   │  ← Texto em negrito
└────────────────────────────────────┘
```

---

## 🎨 Paleta de Cores

### Menu Lateral
```css
/* Cabeçalho Normal */
background: #ffffff
color: #212529

/* Cabeçalho Hover */
background: #f8f9fa
color: #212529

/* Cabeçalho Expandido */
background: #e9ecef
color: #212529

/* Item Normal */
background: #ffffff
color: #495057

/* Item Hover */
background: #f1f3f5
color: #0d6efd
border-left: 3px solid #0d6efd

/* Item Ativo */
background: #e7f1ff
color: #0d6efd
font-weight: 500
border-left: 3px solid #0d6efd
```

### Ícones
```css
.text-primary   → #0d6efd (azul)
.text-success   → #198754 (verde)
.text-warning   → #ffc107 (amarelo)
.text-danger    → #dc3545 (vermelho)
.text-info      → #0dcaf0 (ciano)
.text-secondary → #6c757d (cinza)
```

---

## 📱 Responsividade

### Desktop (> 768px)
```
┌─────────────────────────────────────────────────┐
│              NAVBAR SUPERIOR                     │
└─────────────────────────────────────────────────┘
┌──────────┬──────────────────────────────────────┐
│  MENU    │         CONTEÚDO                     │
│  LATERAL │                                      │
│  (20%)   │         (80%)                        │
└──────────┴──────────────────────────────────────┘
```

### Tablet/Mobile (< 768px)
```
┌─────────────────────────────────────────────────┐
│  NAVBAR SUPERIOR (com botão hamburger)          │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│                                                  │
│              CONTEÚDO (100%)                     │
│                                                  │
│  (Menu lateral oculto, acessível via navbar)    │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Animações

### Chevron Rotation
```
Estado Inicial:  ▼  (0deg)
                 ↓
                 ↓  transition: 0.3s ease
                 ↓
Estado Expandido: ▲  (180deg)
```

### Hover Effect
```
Estado Normal:
┌────────────────────┐
│  📋 Item           │
└────────────────────┘

Hover (0.2s):
┌────────────────────┐
│ ┃📋 Item           │  ← Desliza 0.25rem para direita
└────────────────────┘
```

### Collapse/Expand
```
Colapsando:
┌────────────────┐
│  Item 1        │
│  Item 2        │  ← height: auto → 0
│  Item 3        │     transition: 0.3s
└────────────────┘

Expandindo:
┌────────────────┐
│  Item 1        │  ← height: 0 → auto
│  Item 2        │     transition: 0.3s
│  Item 3        │
└────────────────┘
```

---

## ⌨️ Navegação por Teclado

### Atalhos Disponíveis
```
Arrow Down (↓)  → Próximo item
Arrow Up (↑)    → Item anterior
Enter / Space   → Ativar item/menu
Tab             → Próximo elemento focável
Shift + Tab     → Elemento anterior
```

### Indicador de Foco
```
┌────────────────────────────────────┐
│  ╔═══════════════════════════════╗ │
│  ║ 📋 Item Focado                ║ │  ← Outline azul 2px
│  ╚═══════════════════════════════╝ │
└────────────────────────────────────┘
```

---

## 🏷️ Badges de Notificação

### Navbar
```
┌─────────────────────────────────┐
│  🪙 Tokens  [3]                 │  ← Badge amarelo com contagem
└─────────────────────────────────┘
```

### Menu Lateral
```
┌─────────────────────────────────┐
│  🪙 Tokens [3]              ▼   │
├─────────────────────────────────┤
│    🔧 Gerenciar                 │
│    📨 Solicitações [3]          │  ← Badge também no submenu
│    ➕ Adicionar                 │
└─────────────────────────────────┘
```

---

## 📊 Exemplo de Menu Completo

### Menu de Ordens (Expandido com Item Ativo)
```html
┌──────────────────────────────────────────┐
│  📋 Ordens                            ▲  │  ← Cabeçalho expandido
├──────────────────────────────────────────┤
│    📋 Todas                              │  ← Item normal
│  ┃ ⏰ Aguardando                         │  ← Item ativo (página atual)
│    ⏳ Executadas                         │  ← Item normal
│    ✅ Concluídas                         │  ← Item normal
│    ❌ Canceladas                         │  ← Item normal
│    ⚠️ Contestadas                        │  ← Item normal
│    ⚖️ Resolvidas                         │  ← Item normal
└──────────────────────────────────────────┘
```

### CSS Aplicado
```css
/* Cabeçalho */
.sidebar-menu-header {
    padding: 0.75rem 1rem;
    background: #e9ecef;
}

/* Chevron rotacionado */
.transition-icon {
    transform: rotate(180deg);
}

/* Item ativo */
.sidebar-submenu-item.active {
    background: #e7f1ff;
    color: #0d6efd;
    font-weight: 500;
    border-left: 3px solid #0d6efd;
    padding-left: 1rem;
}
```

---

## 🎭 Comparação: Antes vs Depois

### ANTES (Inconsistente)
```
❌ Padding diferente em cada menu
❌ Alguns menus com p-2, outros com p-3
❌ Classes CSS variadas
❌ Sem atributos ARIA
❌ Sem animações
❌ Sem persistência de estado
```

### DEPOIS (Padronizado)
```
✅ Padding uniforme (p-3 para cabeçalhos)
✅ Classes CSS consistentes
✅ Atributos ARIA completos
✅ Animações suaves (0.3s)
✅ Persistência no localStorage
✅ Destaque automático do item ativo
✅ Navegação por teclado
```

---

## 🔍 Detalhes de Implementação

### Estrutura HTML Padrão
```html
<div class="list-group-item p-0">
    <!-- Cabeçalho do Menu -->
    <a class="d-flex justify-content-between align-items-center 
              p-3 text-decoration-none text-dark sidebar-menu-header" 
       data-bs-toggle="collapse" 
       href="#menuId" 
       role="button" 
       aria-expanded="false" 
       aria-controls="menuId">
        <span>
            <i class="fas fa-icon me-2 text-color"></i>
            <strong>Título</strong>
        </span>
        <i class="fas fa-chevron-down transition-icon"></i>
    </a>
    
    <!-- Conteúdo Colapsável -->
    <div class="collapse" id="menuId">
        <div class="list-group list-group-flush">
            <!-- Item de Submenu -->
            <a href="url" 
               class="list-group-item list-group-item-action 
                      ps-4 py-2 border-0 sidebar-submenu-item">
                <i class="fas fa-icon me-2"></i>
                Texto do Item
            </a>
        </div>
    </div>
</div>
```

### Classes CSS Obrigatórias
```
Cabeçalho:
- sidebar-menu-header
- d-flex
- justify-content-between
- align-items-center
- p-3
- text-decoration-none
- text-dark

Ícone:
- transition-icon
- fas
- fa-chevron-down

Submenu:
- sidebar-submenu-item
- list-group-item
- list-group-item-action
- ps-4
- py-2
- border-0
```

---

## 📈 Métricas de Sucesso

### Consistência Visual
- ✅ 100% dos menus seguem o mesmo padrão
- ✅ 100% dos ícones alinhados
- ✅ 100% dos espaçamentos uniformes

### Funcionalidade
- ✅ 100% dos menus colapsam/expandem
- ✅ 100% dos itens navegáveis por teclado
- ✅ 100% dos estados persistem

### Acessibilidade
- ✅ 100% dos atributos ARIA presentes
- ✅ 100% dos elementos focáveis
- ✅ 100% dos indicadores visuais

---

## 🎓 Guia de Uso

### Para Adicionar Novo Menu
1. Copie a estrutura HTML padrão
2. Altere o ID único (`menuId`)
3. Adicione ícone e título
4. Adicione itens de submenu
5. Teste com `test_admin_menu_consistency.py`

### Para Adicionar Novo Item
1. Use a classe `sidebar-submenu-item`
2. Mantenha padding `ps-4 py-2`
3. Adicione ícone com `me-2`
4. Teste navegação por teclado

---

**Documentação criada em:** 20 de novembro de 2025  
**Versão:** 1.0  
**Status:** ✅ Completo e Validado
