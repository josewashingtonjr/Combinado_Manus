# Loading States - Guia Rápido

## 🚀 Início Rápido

### 1. Loading Automático em Botões

Adicione `data-loading` ao botão:

```html
<button class="btn btn-primary" data-loading data-loading-text="Salvando...">
    Salvar
</button>
```

### 2. Loading Manual

```javascript
// Mostrar
window.loadingStates.showButtonLoading(button, 'Processando...');

// Esconder
window.loadingStates.hideButtonLoading(button);
```

### 3. Skeleton Loading

```javascript
// Mostrar skeleton
window.loadingStates.showSkeleton(container, 'card', 3);

// Esconder skeleton
window.loadingStates.hideSkeleton(container);
```

### 4. AJAX Completo

```javascript
await window.loadingStates.ajaxWithLoading({
    url: '/api/dados',
    method: 'POST',
    data: { id: 123 },
    button: meuBotao,
    container: meuContainer,
    skeletonType: 'list',
    onSuccess: (data) => {
        console.log('Sucesso!', data);
    },
    onError: (error) => {
        console.error('Erro!', error);
    }
});
```

## 📝 Tipos de Skeleton

- `'card'` - Cards completos
- `'list'` - Listas com avatar
- `'table'` - Tabelas
- `'generic'` - Linhas simples

## 🎯 Exemplos Práticos

### Aceitar Convite

```javascript
document.getElementById('aceitar-btn').addEventListener('click', async () => {
    await window.loadingStates.ajaxWithLoading({
        url: `/convite/${id}/aceitar`,
        method: 'POST',
        button: event.target,
        onSuccess: () => {
            window.toast.success('Convite aceito!');
            location.reload();
        }
    });
});
```

### Carregar Lista

```javascript
async function carregarLista() {
    const container = document.getElementById('lista');
    window.loadingStates.showSkeleton(container, 'card', 5);
    
    const response = await fetch('/api/lista');
    const dados = await response.json();
    
    container.innerHTML = renderLista(dados);
}
```

### Formulário AJAX

```javascript
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    await window.loadingStates.ajaxWithLoading({
        url: '/api/salvar',
        method: 'POST',
        data: new FormData(form),
        form: form,
        onSuccess: () => {
            window.toast.success('Salvo!');
            form.reset();
        }
    });
});
```

## 🔧 API Essencial

```javascript
// Botões
loadingStates.showButtonLoading(button, text?)
loadingStates.hideButtonLoading(button)

// Formulários
loadingStates.showFormLoading(form)
loadingStates.hideFormLoading(form)

// Skeleton
loadingStates.showSkeleton(container, type, count)
loadingStates.hideSkeleton(container)

// AJAX
loadingStates.ajaxWithLoading(config)
loadingStates.fetchWithLoading(url, options, button?)

// Utilitários
loadingStates.resetAll()
```

## 📖 Documentação Completa

Veja `LOADING_STATES_README.md` para documentação completa.

## 🎨 Exemplos Interativos

Abra `static/js/loading-states-examples.html` no navegador.
