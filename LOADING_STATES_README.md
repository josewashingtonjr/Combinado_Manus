# Sistema de Loading States

Sistema completo de estados de carregamento para melhorar o feedback visual durante operações assíncronas.

## 📋 Funcionalidades

- ✅ Spinner em botões durante ação
- ✅ Desabilitar botão durante processamento
- ✅ Skeleton loading para conteúdo
- ✅ Integração automática com formulários
- ✅ Wrapper para requisições AJAX
- ✅ Prevenção de duplo clique
- ✅ Tempo mínimo de loading (evita flash)
- ✅ Textos em português brasileiro

## 🚀 Instalação

O sistema é carregado automaticamente no `base.html`:

```html
<script src="{{ url_for('static', filename='js/loading-states.js') }}"></script>
```

## 📖 Uso Básico

### 1. Loading Automático em Botões

Adicione o atributo `data-loading` ao botão:

```html
<button class="btn btn-primary" data-loading data-loading-text="Salvando...">
    Salvar
</button>
```

**Atributos opcionais:**
- `data-loading-text`: Texto durante loading (padrão: "Carregando...")
- `data-loading-duration`: Duração em ms para remover automaticamente

### 2. Loading Manual em Botões

```javascript
const button = document.getElementById('meu-botao');

// Mostrar loading
window.loadingStates.showButtonLoading(button, 'Processando...');

// Esconder loading
window.loadingStates.hideButtonLoading(button);
```

### 3. Loading em Formulários

O sistema detecta automaticamente o submit de formulários:

```html
<form id="meu-form">
    <input type="text" name="nome" required>
    <button type="submit">Enviar</button>
</form>
```

Para formulários AJAX, remova o loading manualmente:

```javascript
const form = document.getElementById('meu-form');

// Após sucesso da requisição
window.loadingStates.hideFormLoading(form);
```

### 4. Skeleton Loading

Mostre skeleton enquanto carrega conteúdo:

```javascript
const container = document.getElementById('lista-convites');

// Mostrar skeleton
window.loadingStates.showSkeleton(container, 'card', 3);

// Após carregar dados
window.loadingStates.hideSkeleton(container);
```

**Tipos de skeleton disponíveis:**
- `'card'` - Cards com header, body e footer
- `'list'` - Lista com avatar e conteúdo
- `'table'` - Tabela com header e linhas
- `'generic'` - Linhas genéricas

### 5. Requisições AJAX com Loading

Use o wrapper completo que gerencia tudo automaticamente:

```javascript
await window.loadingStates.ajaxWithLoading({
    url: '/api/convites',
    method: 'GET',
    button: document.getElementById('carregar-btn'),
    container: document.getElementById('lista'),
    skeletonType: 'card',
    onSuccess: (data) => {
        // Atualiza interface com dados
        console.log('Dados carregados:', data);
    },
    onError: (error) => {
        console.error('Erro:', error);
    }
});
```

### 6. Fetch com Loading

Wrapper simples para fetch:

```javascript
const button = document.getElementById('download-btn');

const response = await window.loadingStates.fetchWithLoading(
    '/api/download',
    { method: 'GET' },
    button
);

const data = await response.json();
```

## 🎨 Exemplos Práticos

### Aceitar Convite

```javascript
document.getElementById('aceitar-convite').addEventListener('click', async () => {
    const button = event.target;
    
    await window.loadingStates.ajaxWithLoading({
        url: `/convite/${conviteId}/aceitar`,
        method: 'POST',
        button: button,
        onSuccess: (data) => {
            window.toast.success('Convite aceito com sucesso!');
            window.location.href = data.redirect_url;
        },
        onError: (error) => {
            window.toast.error('Erro ao aceitar convite');
        }
    });
});
```

### Carregar Lista de Ordens

```javascript
async function carregarOrdens() {
    const container = document.getElementById('lista-ordens');
    
    // Mostra skeleton
    window.loadingStates.showSkeleton(container, 'card', 5);
    
    try {
        const response = await fetch('/api/ordens');
        const ordens = await response.json();
        
        // Renderiza ordens
        container.innerHTML = renderOrdens(ordens);
    } catch (error) {
        window.toast.error('Erro ao carregar ordens');
    }
}
```

### Formulário de Proposta

```html
<form id="form-proposta" data-ajax="true">
    <input type="number" name="valor" required>
    <textarea name="descricao" required></textarea>
    <button type="submit" class="btn btn-primary">
        Enviar Proposta
    </button>
</form>

<script>
document.getElementById('form-proposta').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    await window.loadingStates.ajaxWithLoading({
        url: '/api/proposta',
        method: 'POST',
        data: data,
        form: form,
        onSuccess: (result) => {
            window.toast.success('Proposta enviada!');
            form.reset();
        }
    });
});
</script>
```

## 🔧 API Completa

### Métodos de Botão

```javascript
// Mostrar loading
loadingStates.showButtonLoading(button, text?)

// Esconder loading
loadingStates.hideButtonLoading(button)
```

### Métodos de Formulário

```javascript
// Mostrar loading
loadingStates.showFormLoading(form)

// Esconder loading
loadingStates.hideFormLoading(form)
```

### Métodos de Skeleton

```javascript
// Mostrar skeleton
loadingStates.showSkeleton(container, type, count)

// Esconder skeleton
loadingStates.hideSkeleton(container)
```

### Métodos de Requisição

```javascript
// Fetch com loading
loadingStates.fetchWithLoading(url, options, button?)

// AJAX completo
loadingStates.ajaxWithLoading({
    url: string,
    method: string,
    data: object,
    button: HTMLElement,
    form: HTMLFormElement,
    container: HTMLElement,
    skeletonType: string,
    onSuccess: function,
    onError: function
})
```

### Métodos Utilitários

```javascript
// Reseta todos os estados
loadingStates.resetAll()
```

## 🎯 Configuração

Personalize o comportamento ao inicializar:

```javascript
window.initLoadingStates({
    spinnerHTML: '<i class="fas fa-spinner fa-spin"></i>',
    spinnerText: 'Aguarde...',
    minLoadingTime: 300 // ms
});
```

## 📱 Responsividade

O sistema é totalmente responsivo e otimizado para mobile:

- Skeleton adapta layout em telas pequenas
- Botões mantêm tamanho adequado
- Animações suaves e performáticas

## ♿ Acessibilidade

- Botões desabilitados durante loading
- Feedback visual claro
- Textos descritivos
- Compatível com leitores de tela

## 🔗 Integração com Outros Sistemas

### Com Toast Feedback

```javascript
await loadingStates.ajaxWithLoading({
    url: '/api/acao',
    method: 'POST',
    button: button,
    onSuccess: (data) => {
        window.toast.success(data.message);
    },
    onError: (error) => {
        window.toast.error(error.message);
    }
});
```

### Com Touch Feedback

O sistema funciona em conjunto com o touch feedback:
- Ripple effect continua funcionando
- Prevenção de duplo clique é coordenada
- Estados visuais são complementares

## 📊 Performance

- Tempo mínimo de loading evita flash visual
- Animações CSS otimizadas
- Reutilização de elementos DOM
- Limpeza automática de memória

## 🐛 Troubleshooting

### Loading não aparece

Verifique se o script está carregado:
```javascript
console.log(window.loadingStates); // Deve retornar objeto
```

### Loading não desaparece

Use o método de reset:
```javascript
window.loadingStates.resetAll();
```

### Skeleton não aparece

Verifique se o container existe:
```javascript
const container = document.getElementById('meu-container');
console.log(container); // Não deve ser null
```

## 📝 Requisitos Atendidos

- ✅ **Requirement 5.1**: Exibir loading spinner durante operações
- ✅ **Requirement 8.2**: Mostrar skeleton loading enquanto carrega dados

## 🎓 Exemplos Interativos

Abra o arquivo `static/js/loading-states-examples.html` no navegador para ver exemplos interativos de todos os recursos.

## 📄 Licença

Parte do Sistema Combinado - Todos os direitos reservados.
