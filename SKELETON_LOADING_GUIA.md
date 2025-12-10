# Guia de Uso - Skeleton Loading

## 📋 Visão Geral

O sistema de Skeleton Loading melhora a percepção de velocidade do sistema mostrando placeholders animados enquanto o conteúdo real está sendo carregado.

## 🎯 Benefícios

- ✅ Melhora a percepção de velocidade
- ✅ Reduz a sensação de espera
- ✅ Fornece feedback visual imediato
- ✅ Melhora a experiência do usuário
- ✅ Totalmente acessível (ARIA labels)

## 📦 Componentes Disponíveis

### 1. Card de Convite
```javascript
window.skeletonLoader.show('#container', 'convite-card');
```

### 2. Card de Ordem
```javascript
window.skeletonLoader.show('#container', 'ordem-card');
```

### 3. Lista de Convites
```javascript
window.skeletonLoader.show('#container', 'convite-list', { count: 3 });
```

### 4. Lista de Ordens
```javascript
window.skeletonLoader.show('#container', 'ordem-list', { count: 5 });
```

### 5. Detalhes do Convite
```javascript
window.skeletonLoader.show('#container', 'convite-detail');
```

### 6. Detalhes da Ordem
```javascript
window.skeletonLoader.show('#container', 'ordem-detail');
```

### 7. Dashboard
```javascript
window.skeletonLoader.show('#container', 'dashboard');
```

## 🚀 Uso Básico

### JavaScript

```javascript
// Mostrar skeleton
window.skeletonLoader.show('#meu-container', 'convite-card');

// Esconder skeleton e mostrar conteúdo
window.skeletonLoader.hide('#meu-container', '<div>Conteúdo carregado</div>');

// Ou simplesmente esconder (restaura conteúdo original)
window.skeletonLoader.hide('#meu-container');
```

### Com Fetch/AJAX

```javascript
// Método 1: Manual
const container = document.getElementById('convites-list');
window.skeletonLoader.show(container, 'convite-list', { count: 5 });

fetch('/api/convites')
    .then(response => response.json())
    .then(data => {
        const html = renderConvites(data);
        window.skeletonLoader.hide(container, html);
    });

// Método 2: Usando wrapper
window.skeletonLoader.fetchWithSkeleton('/api/convites', {
    container: '#convites-list',
    skeletonType: 'convite-list',
    skeletonOptions: { count: 5 }
}).then(data => {
    // Skeleton é automaticamente escondido
    console.log('Dados carregados:', data);
});
```

## 🎨 Templates HTML (Jinja2)

### Incluir Skeleton em Template

```jinja2
{# Em uma página de lista de convites #}
<div id="convites-container">
    {% if loading %}
        {% include 'components/skeleton-convite-list.html' with count=5 %}
    {% else %}
        {% for convite in convites %}
            {# Renderizar convites reais #}
        {% endfor %}
    {% endif %}
</div>
```

### Componentes Disponíveis

```jinja2
{# Card de Convite #}
{% include 'components/skeleton-convite-card.html' %}

{# Card de Ordem #}
{% include 'components/skeleton-ordem-card.html' %}

{# Lista de Convites (com contagem) #}
{% include 'components/skeleton-convite-list.html' with count=3 %}

{# Lista de Ordens (com contagem) #}
{% include 'components/skeleton-ordem-list.html' with count=5 %}

{# Detalhes do Convite #}
{% include 'components/skeleton-convite-detail.html' %}

{# Detalhes da Ordem #}
{% include 'components/skeleton-ordem-detail.html' %}

{# Dashboard #}
{% include 'components/skeleton-dashboard.html' %}
```

## 🔧 Configuração Avançada

### Opções do SkeletonLoader

```javascript
const skeletonLoader = new SkeletonLoader({
    minDisplayTime: 500,      // Tempo mínimo para mostrar skeleton (ms)
    fadeOutDuration: 300,     // Duração do fade out (ms)
    autoHide: true            // Auto-esconder quando conteúdo carregar
});
```

### Eventos Customizados

```javascript
// Quando skeleton é mostrado
document.addEventListener('skeleton-shown', (e) => {
    console.log('Skeleton mostrado:', e.detail.type);
});

// Quando skeleton é escondido
document.addEventListener('skeleton-hidden', (e) => {
    console.log('Skeleton escondido');
});
```

## 📱 Responsividade

Todos os skeletons são totalmente responsivos e se adaptam automaticamente a diferentes tamanhos de tela:

- **Desktop**: Layout completo com múltiplas colunas
- **Tablet**: Layout adaptado com menos colunas
- **Mobile**: Layout de coluna única

## ♿ Acessibilidade

Todos os skeletons incluem:

- `role="status"` - Indica que é um status de carregamento
- `aria-busy="true"` - Indica que o conteúdo está carregando
- `aria-label` - Descrição do que está carregando
- `.sr-only` - Texto para leitores de tela

## 🎯 Exemplos Práticos

### Exemplo 1: Dashboard do Cliente

```javascript
// Ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = document.getElementById('dashboard-content');
    
    // Mostra skeleton
    window.skeletonLoader.show(dashboard, 'dashboard');
    
    // Carrega dados
    fetch('/api/dashboard')
        .then(response => response.json())
        .then(data => {
            const html = renderDashboard(data);
            window.skeletonLoader.hide(dashboard, html);
        });
});
```

### Exemplo 2: Lista de Convites com Filtro

```javascript
function filtrarConvites(status) {
    const lista = document.getElementById('convites-lista');
    
    // Mostra skeleton
    window.skeletonLoader.show(lista, 'convite-list', { count: 5 });
    
    // Busca convites filtrados
    fetch(`/api/convites?status=${status}`)
        .then(response => response.json())
        .then(convites => {
            const html = convites.map(c => renderConvite(c)).join('');
            window.skeletonLoader.hide(lista, html);
        });
}
```

### Exemplo 3: Detalhes do Convite

```javascript
function verConvite(id) {
    const detalhes = document.getElementById('convite-detalhes');
    
    // Mostra skeleton
    window.skeletonLoader.show(detalhes, 'convite-detail');
    
    // Carrega detalhes
    fetch(`/api/convites/${id}`)
        .then(response => response.json())
        .then(convite => {
            const html = renderConviteDetalhes(convite);
            window.skeletonLoader.hide(detalhes, html);
        });
}
```

### Exemplo 4: Integração com Loading States

```javascript
// Skeleton + Loading Button
async function aceitarConvite(id) {
    const button = document.getElementById('btn-aceitar');
    const detalhes = document.getElementById('convite-detalhes');
    
    // Mostra loading no botão
    window.loadingStates.showButtonLoading(button, 'Aceitando...');
    
    try {
        const response = await fetch(`/api/convites/${id}/aceitar`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Mostra skeleton enquanto recarrega
            window.skeletonLoader.show(detalhes, 'convite-detail');
            
            // Recarrega detalhes
            const convite = await fetch(`/api/convites/${id}`).then(r => r.json());
            const html = renderConviteDetalhes(convite);
            window.skeletonLoader.hide(detalhes, html);
            
            // Mostra toast de sucesso
            window.toast.success('Convite aceito com sucesso!');
        }
    } finally {
        window.loadingStates.hideButtonLoading(button);
    }
}
```

## 🧪 Teste

Abra o arquivo de demonstração para ver todos os skeletons em ação:

```
static/skeleton-loading-demo.html
```

## 📊 Performance

- **Animações otimizadas**: Usa `will-change` e `contain` para melhor performance
- **Movimento reduzido**: Respeita `prefers-reduced-motion`
- **Lazy rendering**: Skeletons são criados apenas quando necessário
- **Memória eficiente**: Limpa automaticamente skeletons não utilizados

## 🎨 Customização

### Modificar Cores

Edite `static/css/skeleton-loading.css`:

```css
.skeleton {
    background: linear-gradient(
        90deg,
        #f0f0f0 0px,    /* Cor base */
        #f8f8f8 40px,   /* Cor highlight */
        #f0f0f0 80px    /* Cor base */
    );
}
```

### Modificar Velocidade da Animação

```css
@keyframes skeleton-shimmer {
    /* Ajuste a duração em animation */
}

.skeleton {
    animation: skeleton-shimmer 1.2s ease-in-out infinite;
    /* Altere 1.2s para mais rápido (0.8s) ou mais lento (2s) */
}
```

## 🐛 Troubleshooting

### Skeleton não aparece

1. Verifique se os arquivos CSS e JS estão carregados
2. Verifique se o container existe no DOM
3. Verifique o console para erros

### Skeleton não desaparece

1. Certifique-se de chamar `hide()` após carregar o conteúdo
2. Verifique se o seletor está correto
3. Use `window.skeletonLoader.resetAll()` para limpar todos

### Animação não funciona

1. Verifique se o CSS está carregado corretamente
2. Verifique se há conflitos com outros estilos
3. Teste em diferentes navegadores

## 📚 Referências

- **Requirements**: 8.2 (Performance em Conexões Lentas)
- **Design**: Melhoria da percepção de velocidade
- **Acessibilidade**: WCAG 2.1 Level AA compliant

## 🔄 Integração com Sistema Existente

O Skeleton Loading está totalmente integrado com:

- ✅ Loading States System
- ✅ Toast Feedback
- ✅ Mobile Navigation
- ✅ Accessibility Features
- ✅ Performance Optimization

## 📝 Notas Importantes

1. **Sempre use skeleton para operações que levam mais de 300ms**
2. **Mantenha o tempo mínimo de exibição em 500ms** para evitar flash
3. **Use o tipo correto de skeleton** para cada contexto
4. **Teste em conexões lentas** (3G) para validar a experiência
5. **Combine com loading states** para feedback completo

## 🎓 Boas Práticas

1. **Mostre skeleton imediatamente** ao iniciar carregamento
2. **Use contagem realista** (não mostre 10 skeletons se normalmente há 3 itens)
3. **Mantenha consistência** com o layout real
4. **Não abuse** - use apenas quando necessário
5. **Teste a transição** - deve ser suave e natural

---

**Implementado em**: 02/12/2024  
**Versão**: 1.0  
**Status**: ✅ Completo e Testado
