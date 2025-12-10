# Exemplos Práticos - Acessibilidade ARIA

## Guia Rápido para Desenvolvedores

Este documento fornece exemplos práticos de como usar os recursos de acessibilidade implementados.

## 1. Formulários Acessíveis

### ✅ Bom Exemplo - Campo com Label
```html
<div class="mb-3">
    <label for="nome" class="form-label">
        <i class="fas fa-user" aria-hidden="true"></i>
        Nome Completo *
    </label>
    <input type="text" 
           class="form-control" 
           id="nome" 
           name="nome" 
           placeholder="Digite seu nome" 
           required>
    <small class="form-text text-muted">
        Este campo é obrigatório
    </small>
</div>
```

**O que acontece:**
- O script detecta o label associado via `for="nome"`
- Adiciona `aria-required="true"` automaticamente
- Leitor de tela anuncia: "Nome Completo, campo de texto, obrigatório"

### ❌ Evitar - Campo sem Label
```html
<!-- NÃO FAZER ISSO -->
<input type="text" name="nome" placeholder="Nome">
```

**Problema:** Leitores de tela não sabem o propósito do campo

**Solução automática:** O script adiciona `aria-label="Nome"` baseado no placeholder

### ✅ Campo com Erro
```html
<div class="mb-3">
    <label for="email" class="form-label">E-mail *</label>
    <input type="email" 
           class="form-control is-invalid" 
           id="email" 
           name="email" 
           value="email-invalido">
    <div class="invalid-feedback" id="email-error">
        Por favor, insira um e-mail válido
    </div>
</div>
```

**O que acontece:**
- Script detecta classe `is-invalid`
- Adiciona `aria-invalid="true"`
- Adiciona `aria-describedby="email-error"`
- Leitor de tela anuncia o erro ao focar no campo

## 2. Botões e Ícones

### ✅ Botão com Ícone e Texto
```html
<button class="btn btn-primary">
    <i class="fas fa-save"></i>
    Salvar
</button>
```

**O que acontece:**
- Script adiciona `aria-hidden="true"` ao ícone
- Leitor de tela anuncia apenas: "Salvar, botão"

### ✅ Botão Apenas com Ícone
```html
<button class="btn btn-outline-primary" title="Buscar">
    <i class="fas fa-search"></i>
</button>
```

**O que acontece:**
- Script adiciona `aria-label="Buscar"` ao ícone
- Adiciona `role="img"` ao ícone
- Leitor de tela anuncia: "Buscar, botão"

### ✅ Link com Ícone
```html
<a href="/perfil" class="nav-link">
    <i class="fas fa-user-circle"></i>
    Meu Perfil
</a>
```

**O que acontece:**
- Script adiciona `aria-hidden="true"` ao ícone
- Leitor de tela anuncia: "Meu Perfil, link"

## 3. Mensagens e Alertas

### ✅ Alerta de Sucesso
```html
<div class="alert alert-success" role="alert">
    <i class="fas fa-check-circle" aria-hidden="true"></i>
    <strong>Sucesso!</strong> Operação realizada com sucesso.
</div>
```

**O que acontece:**
- Script adiciona `aria-live="polite"`
- Script adiciona `aria-atomic="true"`
- Leitor de tela anuncia a mensagem quando ela aparece

### ✅ Alerta de Erro (Urgente)
```html
<div class="alert alert-danger" role="alert">
    <i class="fas fa-times-circle" aria-hidden="true"></i>
    <strong>Erro!</strong> Não foi possível completar a operação.
</div>
```

**O que acontece:**
- Script adiciona `aria-live="assertive"` (mais urgente)
- Interrompe leitura atual para anunciar o erro
- Leitor de tela anuncia imediatamente

### ✅ Toast Dinâmico
```javascript
// Criar toast programaticamente
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // O script adiciona aria-live automaticamente
}
```

## 4. Navegação

### ✅ Navegação Mobile
```html
<nav class="mobile-nav" role="navigation" aria-label="Navegação principal mobile">
    <ul class="mobile-nav-list">
        <li class="mobile-nav-item">
            <a href="/dashboard" 
               class="mobile-nav-link active"
               aria-label="Página inicial"
               aria-current="page">
                <span class="mobile-nav-icon">
                    <i class="fas fa-home" aria-hidden="true"></i>
                </span>
                <span class="mobile-nav-label">Início</span>
            </a>
        </li>
        <li class="mobile-nav-item">
            <a href="/convites" 
               class="mobile-nav-link"
               aria-label="Convites (3 pendentes)">
                <span class="mobile-nav-icon">
                    <i class="fas fa-envelope" aria-hidden="true"></i>
                    <span class="mobile-nav-badge" aria-label="3 convites pendentes">
                        3
                    </span>
                </span>
                <span class="mobile-nav-label">Convites</span>
            </a>
        </li>
    </ul>
</nav>
```

**O que acontece:**
- `role="navigation"` identifica como navegação
- `aria-label` descreve o propósito da navegação
- `aria-current="page"` marca a página atual
- Badges têm descrição clara para leitores de tela

### ✅ Breadcrumb
```html
<nav aria-label="Breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item">
            <a href="/">Início</a>
        </li>
        <li class="breadcrumb-item">
            <a href="/convites">Convites</a>
        </li>
        <li class="breadcrumb-item active" aria-current="page">
            Criar Convite
        </li>
    </ol>
</nav>
```

## 5. Elementos Interativos Customizados

### ✅ Div como Botão
```html
<div class="card-clickable" 
     tabindex="0" 
     role="button"
     onclick="abrirDetalhes()">
    <h3>Título do Card</h3>
    <p>Descrição do card</p>
</div>
```

**O que acontece:**
- `tabindex="0"` torna o elemento focável
- `role="button"` indica que é um botão
- Script adiciona suporte para Enter e Space
- Leitor de tela anuncia: "Título do Card, botão"

### ✅ Accordion Acessível
```html
<div class="accordion">
    <button class="accordion-button" 
            aria-expanded="false" 
            aria-controls="panel1">
        Seção 1
    </button>
    <div id="panel1" 
         class="accordion-panel" 
         role="region" 
         aria-labelledby="accordion-button-1" 
         hidden>
        Conteúdo da seção 1
    </div>
</div>
```

## 6. Tabelas

### ✅ Tabela Acessível
```html
<table class="table" role="table">
    <caption>Lista de Convites Pendentes</caption>
    <thead>
        <tr>
            <th scope="col">Título</th>
            <th scope="col">Valor</th>
            <th scope="col">Data</th>
            <th scope="col">Ações</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Limpeza Residencial</td>
            <td>R$ 150,00</td>
            <td>25/12/2025</td>
            <td>
                <button class="btn btn-sm btn-success" aria-label="Aceitar convite Limpeza Residencial">
                    <i class="fas fa-check" aria-hidden="true"></i>
                </button>
                <button class="btn btn-sm btn-danger" aria-label="Recusar convite Limpeza Residencial">
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
            </td>
        </tr>
    </tbody>
</table>
```

**Pontos importantes:**
- `<caption>` descreve o propósito da tabela
- `scope="col"` identifica cabeçalhos de coluna
- Botões de ação têm `aria-label` descritivo

## 7. Modais

### ✅ Modal Acessível
```html
<div class="modal" 
     id="confirmModal" 
     tabindex="-1" 
     role="dialog" 
     aria-labelledby="confirmModalLabel" 
     aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="confirmModalLabel">
                    Confirmar Ação
                </h5>
                <button type="button" 
                        class="btn-close" 
                        data-bs-dismiss="modal" 
                        aria-label="Fechar modal">
                </button>
            </div>
            <div class="modal-body">
                <p>Tem certeza que deseja continuar?</p>
            </div>
            <div class="modal-footer">
                <button type="button" 
                        class="btn btn-secondary" 
                        data-bs-dismiss="modal">
                    Cancelar
                </button>
                <button type="button" 
                        class="btn btn-primary">
                    Confirmar
                </button>
            </div>
        </div>
    </div>
</div>
```

**Pontos importantes:**
- `role="dialog"` identifica como diálogo
- `aria-labelledby` aponta para o título
- `aria-hidden="true"` quando fechado
- Botão de fechar tem `aria-label`

## 8. Loading States

### ✅ Spinner com Feedback
```html
<button class="btn btn-primary" disabled>
    <span class="spinner-border spinner-border-sm" 
          role="status" 
          aria-hidden="true">
    </span>
    <span class="visually-hidden">Carregando...</span>
    Processando...
</button>
```

**O que acontece:**
- Spinner é decorativo (`aria-hidden="true"`)
- Texto "Carregando..." é anunciado por leitores de tela
- Botão desabilitado não é focável

### ✅ Skeleton Loading
```html
<div class="skeleton-loader" 
     role="status" 
     aria-label="Carregando conteúdo">
    <div class="skeleton-line"></div>
    <div class="skeleton-line"></div>
    <div class="skeleton-line"></div>
    <span class="visually-hidden">Carregando...</span>
</div>
```

## 9. Dicas Rápidas

### Classes Utilitárias

```html
<!-- Esconder visualmente mas manter acessível -->
<span class="visually-hidden">
    Texto apenas para leitores de tela
</span>

<!-- Mostrar apenas quando focado -->
<a href="#main-content" class="visually-hidden-focusable">
    Pular para conteúdo principal
</a>
```

### Atalhos de Teclado

```javascript
// Adicionar atalho de teclado acessível
document.addEventListener('keydown', function(e) {
    // Ctrl+S para salvar
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        salvarFormulario();
        
        // Anunciar ação para leitores de tela
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.textContent = 'Formulário salvo com sucesso';
        document.body.appendChild(announcement);
        
        setTimeout(() => announcement.remove(), 3000);
    }
});
```

## 10. Checklist Rápido

Antes de fazer commit, verifique:

- [ ] Todos os campos de formulário têm `<label>` ou `aria-label`
- [ ] Ícones decorativos têm `aria-hidden="true"`
- [ ] Ícones funcionais têm `aria-label`
- [ ] Botões têm texto ou `aria-label` descritivo
- [ ] Links têm texto descritivo (evite "clique aqui")
- [ ] Imagens têm `alt` text
- [ ] Navegação tem `role="navigation"` e `aria-label`
- [ ] Página atual tem `aria-current="page"`
- [ ] Modais têm `role="dialog"` e `aria-labelledby`
- [ ] Alertas têm `role="alert"` ou `aria-live`
- [ ] Elementos customizados têm `role` apropriado
- [ ] Elementos interativos são focáveis (Tab)
- [ ] Foco é visível e claro

## 11. Ferramentas de Desenvolvimento

### Console do Navegador
```javascript
// Verificar elementos sem label
document.querySelectorAll('input:not([type="hidden"])').forEach(input => {
    const hasLabel = document.querySelector(`label[for="${input.id}"]`);
    const hasAriaLabel = input.hasAttribute('aria-label');
    if (!hasLabel && !hasAriaLabel) {
        console.warn('Campo sem label:', input);
    }
});

// Verificar ícones sem ARIA
document.querySelectorAll('i[class*="fa-"]').forEach(icon => {
    const hasAriaHidden = icon.hasAttribute('aria-hidden');
    const hasAriaLabel = icon.hasAttribute('aria-label');
    if (!hasAriaHidden && !hasAriaLabel) {
        console.warn('Ícone sem ARIA:', icon);
    }
});
```

### Bookmarklet para Teste Rápido
```javascript
javascript:(function(){
    // Destacar elementos sem label
    document.querySelectorAll('input:not([type="hidden"])').forEach(input => {
        const hasLabel = document.querySelector(`label[for="${input.id}"]`);
        const hasAriaLabel = input.hasAttribute('aria-label');
        if (!hasLabel && !hasAriaLabel) {
            input.style.outline = '3px solid red';
        }
    });
    alert('Elementos sem label destacados em vermelho');
})();
```

## 12. Recursos Adicionais

- **Documentação ARIA:** https://www.w3.org/WAI/ARIA/apg/
- **WCAG Quick Reference:** https://www.w3.org/WAI/WCAG21/quickref/
- **WebAIM:** https://webaim.org/
- **A11y Project:** https://www.a11yproject.com/
- **MDN Accessibility:** https://developer.mozilla.org/en-US/docs/Web/Accessibility

## Conclusão

Com estes exemplos, você pode criar componentes acessíveis desde o início. Lembre-se:

1. **Semântica primeiro:** Use HTML semântico sempre que possível
2. **ARIA quando necessário:** Use ARIA para complementar, não substituir HTML
3. **Teste com teclado:** Navegue com Tab para verificar acessibilidade
4. **Teste com leitor de tela:** Use NVDA ou VoiceOver para validar
5. **Automatize:** Use ferramentas como Lighthouse e axe DevTools

O script `accessibility-aria.js` ajuda automaticamente, mas seguir boas práticas desde o início é sempre melhor! 🎯
