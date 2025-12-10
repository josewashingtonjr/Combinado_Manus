# Exemplos Práticos de Integração - Skeleton Loading

## 🎯 Como Integrar nas Páginas Existentes

Este documento mostra exemplos práticos de como integrar o skeleton loading nas páginas do sistema.

---

## 1. Dashboard do Cliente

### Arquivo: `templates/cliente/dashboard.html`

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <h2>Meu Dashboard</h2>
    
    <!-- Container para estatísticas -->
    <div id="stats-container">
        <!-- Skeleton inicial -->
        {% include 'components/skeleton-dashboard.html' %}
    </div>
    
    <!-- Container para convites pendentes -->
    <div class="mt-4">
        <h3>Convites Pendentes</h3>
        <div id="convites-pendentes">
            <!-- Skeleton inicial -->
            {% include 'components/skeleton-convite-list.html' with count=3 %}
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Carrega estatísticas
    carregarEstatisticas();
    
    // Carrega convites pendentes
    carregarConvitesPendentes();
});

async function carregarEstatisticas() {
    const container = document.getElementById('stats-container');
    
    try {
        const response = await fetch('/api/cliente/estatisticas');
        const data = await response.json();
        
        // Renderiza estatísticas
        const html = `
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-card">
                        <h6>Convites Pendentes</h6>
                        <h2>${data.convites_pendentes}</h2>
                    </div>
                </div>
                <!-- Mais cards... -->
            </div>
        `;
        
        window.skeletonLoader.hide(container, html);
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
        window.toast.error('Erro ao carregar estatísticas');
    }
}

async function carregarConvitesPendentes() {
    const container = document.getElementById('convites-pendentes');
    
    try {
        const response = await fetch('/api/cliente/convites/pendentes');
        const convites = await response.json();
        
        const html = convites.map(c => `
            <div class="convite-item">
                <h5>${c.titulo}</h5>
                <p>R$ ${c.valor} - ${c.prazo} dias</p>
                <a href="/cliente/convite/${c.id}" class="btn btn-primary">Ver Detalhes</a>
            </div>
        `).join('');
        
        window.skeletonLoader.hide(container, html);
    } catch (error) {
        console.error('Erro ao carregar convites:', error);
        window.toast.error('Erro ao carregar convites');
    }
}
</script>
{% endblock %}
```

---

## 2. Lista de Convites com Filtros

### Arquivo: `templates/cliente/convites.html`

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>Meus Convites</h2>
        
        <!-- Filtros -->
        <div class="filters">
            <select id="status-filter" class="form-select" onchange="filtrarConvites()">
                <option value="">Todos</option>
                <option value="pendente">Pendentes</option>
                <option value="aceito">Aceitos</option>
                <option value="recusado">Recusados</option>
            </select>
        </div>
    </div>
    
    <!-- Lista de convites -->
    <div id="convites-lista">
        <!-- Skeleton inicial -->
        {% include 'components/skeleton-convite-list.html' with count=5 %}
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    carregarConvites();
});

async function carregarConvites(status = '') {
    const container = document.getElementById('convites-lista');
    
    // Mostra skeleton
    window.skeletonLoader.show(container, 'convite-list', { count: 5 });
    
    try {
        const url = status ? `/api/convites?status=${status}` : '/api/convites';
        const response = await fetch(url);
        const convites = await response.json();
        
        if (convites.length === 0) {
            const html = `
                <div class="empty-state">
                    <i class="fas fa-inbox fa-3x text-muted"></i>
                    <p class="mt-3">Nenhum convite encontrado</p>
                </div>
            `;
            window.skeletonLoader.hide(container, html);
            return;
        }
        
        const html = convites.map(convite => `
            <div class="convite-card">
                <div class="convite-header">
                    <h4>${convite.titulo}</h4>
                    <span class="badge bg-${getBadgeColor(convite.status)}">${convite.status}</span>
                </div>
                <div class="convite-body">
                    <p><strong>Valor:</strong> R$ ${convite.valor}</p>
                    <p><strong>Prazo:</strong> ${convite.prazo} dias</p>
                    <p>${convite.descricao}</p>
                </div>
                <div class="convite-actions">
                    <a href="/cliente/convite/${convite.id}" class="btn btn-primary">Ver Detalhes</a>
                </div>
            </div>
        `).join('');
        
        window.skeletonLoader.hide(container, html);
    } catch (error) {
        console.error('Erro ao carregar convites:', error);
        window.toast.error('Erro ao carregar convites');
        window.skeletonLoader.hide(container, '<p class="text-danger">Erro ao carregar convites</p>');
    }
}

function filtrarConvites() {
    const status = document.getElementById('status-filter').value;
    carregarConvites(status);
}

function getBadgeColor(status) {
    const colors = {
        'pendente': 'warning',
        'aceito': 'success',
        'recusado': 'danger'
    };
    return colors[status] || 'secondary';
}
</script>
{% endblock %}
```

---

## 3. Detalhes do Convite

### Arquivo: `templates/cliente/ver_convite.html`

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <div id="convite-detalhes">
        <!-- Skeleton inicial -->
        {% include 'components/skeleton-convite-detail.html' %}
    </div>
</div>

<script>
const conviteId = {{ convite_id }};

document.addEventListener('DOMContentLoaded', function() {
    carregarDetalhesConvite();
});

async function carregarDetalhesConvite() {
    const container = document.getElementById('convite-detalhes');
    
    try {
        const response = await fetch(`/api/convites/${conviteId}`);
        const convite = await response.json();
        
        const html = `
            <div class="convite-detail-page">
                <div class="convite-detail-header">
                    <h2>${convite.titulo}</h2>
                    <span class="badge bg-${getBadgeColor(convite.status)}">${convite.status}</span>
                </div>
                
                <div class="convite-detail-section">
                    <h4>Informações Principais</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Valor:</strong> R$ ${convite.valor}</p>
                            <p><strong>Prazo:</strong> ${convite.prazo} dias</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Cliente:</strong> ${convite.cliente_nome}</p>
                            <p><strong>Data:</strong> ${formatarData(convite.data_criacao)}</p>
                        </div>
                    </div>
                </div>
                
                <div class="convite-detail-section">
                    <h4>Descrição</h4>
                    <p>${convite.descricao}</p>
                </div>
                
                ${convite.status === 'pendente' ? `
                    <div class="convite-detail-actions">
                        <button class="btn btn-success btn-lg" onclick="aceitarConvite()">
                            <i class="fas fa-check"></i> Aceitar Convite
                        </button>
                        <button class="btn btn-outline-danger btn-lg" onclick="recusarConvite()">
                            <i class="fas fa-times"></i> Recusar
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
        
        window.skeletonLoader.hide(container, html);
    } catch (error) {
        console.error('Erro ao carregar detalhes:', error);
        window.toast.error('Erro ao carregar detalhes do convite');
    }
}

async function aceitarConvite() {
    const button = event.target.closest('button');
    const container = document.getElementById('convite-detalhes');
    
    // Mostra loading no botão
    window.loadingStates.showButtonLoading(button, 'Aceitando...');
    
    try {
        const response = await fetch(`/api/convites/${conviteId}/aceitar`, {
            method: 'POST'
        });
        
        if (response.ok) {
            window.toast.success('Convite aceito com sucesso!');
            
            // Mostra skeleton enquanto recarrega
            window.skeletonLoader.show(container, 'convite-detail');
            
            // Recarrega detalhes
            await carregarDetalhesConvite();
        } else {
            const error = await response.json();
            window.toast.error(error.message || 'Erro ao aceitar convite');
        }
    } catch (error) {
        console.error('Erro:', error);
        window.toast.error('Erro ao aceitar convite');
    } finally {
        window.loadingStates.hideButtonLoading(button);
    }
}

function formatarData(data) {
    return new Date(data).toLocaleDateString('pt-BR');
}

function getBadgeColor(status) {
    const colors = {
        'pendente': 'warning',
        'aceito': 'success',
        'recusado': 'danger'
    };
    return colors[status] || 'secondary';
}
</script>
{% endblock %}
```

---

## 4. Lista de Ordens do Prestador

### Arquivo: `templates/prestador/ordens.html`

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <h2>Minhas Ordens</h2>
    
    <!-- Tabs de filtro -->
    <ul class="nav nav-tabs mb-4" role="tablist">
        <li class="nav-item">
            <a class="nav-link active" data-status="" onclick="filtrarOrdens('')">Todas</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-status="em_andamento" onclick="filtrarOrdens('em_andamento')">Em Andamento</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" data-status="concluida" onclick="filtrarOrdens('concluida')">Concluídas</a>
        </li>
    </ul>
    
    <!-- Lista de ordens -->
    <div id="ordens-lista">
        <!-- Skeleton inicial -->
        {% include 'components/skeleton-ordem-list.html' with count=5 %}
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    carregarOrdens();
});

async function carregarOrdens(status = '') {
    const container = document.getElementById('ordens-lista');
    
    // Mostra skeleton
    window.skeletonLoader.show(container, 'ordem-list', { count: 5 });
    
    try {
        const url = status ? `/api/ordens?status=${status}` : '/api/ordens';
        const response = await fetch(url);
        const ordens = await response.json();
        
        if (ordens.length === 0) {
            const html = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list fa-3x text-muted"></i>
                    <p class="mt-3">Nenhuma ordem encontrada</p>
                </div>
            `;
            window.skeletonLoader.hide(container, html);
            return;
        }
        
        const html = ordens.map(ordem => `
            <div class="ordem-card">
                <div class="ordem-header">
                    <span class="ordem-id">Ordem #${ordem.id}</span>
                    <span class="badge bg-${getStatusColor(ordem.status)}">${ordem.status_display}</span>
                </div>
                <div class="ordem-body">
                    <h4>R$ ${ordem.valor}</h4>
                    <p><strong>Cliente:</strong> ${ordem.cliente_nome}</p>
                    <p><strong>Prazo:</strong> ${ordem.prazo_dias} dias</p>
                    <p>${ordem.descricao_curta}</p>
                </div>
                <div class="ordem-actions">
                    <a href="/prestador/ordem/${ordem.id}" class="btn btn-primary">Ver Detalhes</a>
                    ${getActionButton(ordem)}
                </div>
            </div>
        `).join('');
        
        window.skeletonLoader.hide(container, html);
    } catch (error) {
        console.error('Erro ao carregar ordens:', error);
        window.toast.error('Erro ao carregar ordens');
    }
}

function filtrarOrdens(status) {
    // Atualiza tab ativa
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.status === status) {
            link.classList.add('active');
        }
    });
    
    carregarOrdens(status);
}

function getStatusColor(status) {
    const colors = {
        'pendente': 'warning',
        'em_andamento': 'info',
        'concluida': 'success',
        'cancelada': 'danger'
    };
    return colors[status] || 'secondary';
}

function getActionButton(ordem) {
    if (ordem.status === 'em_andamento') {
        return `<button class="btn btn-success" onclick="marcarConcluida(${ordem.id})">Marcar como Concluída</button>`;
    }
    return '';
}

async function marcarConcluida(ordemId) {
    const button = event.target;
    window.loadingStates.showButtonLoading(button, 'Processando...');
    
    try {
        const response = await fetch(`/api/ordens/${ordemId}/concluir`, {
            method: 'POST'
        });
        
        if (response.ok) {
            window.toast.success('Ordem marcada como concluída!');
            carregarOrdens(); // Recarrega lista
        } else {
            const error = await response.json();
            window.toast.error(error.message || 'Erro ao marcar ordem');
        }
    } catch (error) {
        console.error('Erro:', error);
        window.toast.error('Erro ao processar requisição');
    } finally {
        window.loadingStates.hideButtonLoading(button);
    }
}
</script>
{% endblock %}
```

---

## 5. Busca com Skeleton

### Exemplo de busca com debounce

```javascript
let searchTimeout;

function buscarConvites() {
    const query = document.getElementById('search-input').value;
    const container = document.getElementById('resultados');
    
    // Limpa timeout anterior
    clearTimeout(searchTimeout);
    
    // Aguarda 500ms após parar de digitar
    searchTimeout = setTimeout(async () => {
        if (query.length < 3) {
            container.innerHTML = '<p class="text-muted">Digite pelo menos 3 caracteres</p>';
            return;
        }
        
        // Mostra skeleton
        window.skeletonLoader.show(container, 'convite-list', { count: 3 });
        
        try {
            const response = await fetch(`/api/convites/buscar?q=${encodeURIComponent(query)}`);
            const resultados = await response.json();
            
            if (resultados.length === 0) {
                window.skeletonLoader.hide(container, '<p class="text-muted">Nenhum resultado encontrado</p>');
                return;
            }
            
            const html = resultados.map(r => renderConvite(r)).join('');
            window.skeletonLoader.hide(container, html);
        } catch (error) {
            console.error('Erro na busca:', error);
            window.toast.error('Erro ao buscar');
        }
    }, 500);
}
```

---

## 6. Paginação com Skeleton

```javascript
let paginaAtual = 1;
const itensPorPagina = 10;

async function carregarPagina(pagina) {
    const container = document.getElementById('lista-container');
    paginaAtual = pagina;
    
    // Mostra skeleton
    window.skeletonLoader.show(container, 'convite-list', { count: itensPorPagina });
    
    try {
        const response = await fetch(`/api/convites?page=${pagina}&per_page=${itensPorPagina}`);
        const data = await response.json();
        
        const html = `
            <div class="lista-items">
                ${data.items.map(item => renderItem(item)).join('')}
            </div>
            <div class="pagination-controls">
                ${renderPaginacao(data.total_pages, pagina)}
            </div>
        `;
        
        window.skeletonLoader.hide(container, html);
        
        // Scroll para o topo
        container.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Erro ao carregar página:', error);
        window.toast.error('Erro ao carregar página');
    }
}

function renderPaginacao(totalPaginas, paginaAtual) {
    let html = '<nav><ul class="pagination">';
    
    for (let i = 1; i <= totalPaginas; i++) {
        const active = i === paginaAtual ? 'active' : '';
        html += `
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="carregarPagina(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    html += '</ul></nav>';
    return html;
}
```

---

## 7. Infinite Scroll com Skeleton

```javascript
let carregando = false;
let paginaAtual = 1;
let temMaisPaginas = true;

function setupInfiniteScroll() {
    const container = document.getElementById('lista-container');
    
    window.addEventListener('scroll', () => {
        if (carregando || !temMaisPaginas) return;
        
        const scrollPosition = window.innerHeight + window.scrollY;
        const threshold = document.body.offsetHeight - 500;
        
        if (scrollPosition >= threshold) {
            carregarMaisItens();
        }
    });
}

async function carregarMaisItens() {
    carregando = true;
    paginaAtual++;
    
    const container = document.getElementById('lista-container');
    const loadingIndicator = document.createElement('div');
    loadingIndicator.id = 'loading-more';
    container.appendChild(loadingIndicator);
    
    // Mostra skeleton no final da lista
    window.skeletonLoader.show(loadingIndicator, 'convite-list', { count: 3 });
    
    try {
        const response = await fetch(`/api/convites?page=${paginaAtual}`);
        const data = await response.json();
        
        if (data.items.length === 0) {
            temMaisPaginas = false;
            loadingIndicator.remove();
            return;
        }
        
        const html = data.items.map(item => renderItem(item)).join('');
        
        // Remove skeleton e adiciona novos itens
        loadingIndicator.remove();
        container.insertAdjacentHTML('beforeend', html);
        
        temMaisPaginas = data.has_next;
    } catch (error) {
        console.error('Erro ao carregar mais itens:', error);
        window.toast.error('Erro ao carregar mais itens');
        loadingIndicator.remove();
    } finally {
        carregando = false;
    }
}

document.addEventListener('DOMContentLoaded', setupInfiniteScroll);
```

---

## 🎯 Dicas de Integração

### 1. Sempre use skeleton para operações > 300ms
```javascript
// ❌ Ruim - sem feedback
fetch('/api/data').then(data => render(data));

// ✅ Bom - com skeleton
window.skeletonLoader.show('#container', 'convite-list');
fetch('/api/data').then(data => {
    window.skeletonLoader.hide('#container', render(data));
});
```

### 2. Combine com loading states em botões
```javascript
async function salvar() {
    const button = event.target;
    const container = document.getElementById('form-container');
    
    // Loading no botão
    window.loadingStates.showButtonLoading(button, 'Salvando...');
    
    // Skeleton no container (se necessário)
    window.skeletonLoader.show(container, 'convite-detail');
    
    try {
        await fetch('/api/salvar', { method: 'POST' });
        window.toast.success('Salvo com sucesso!');
    } finally {
        window.loadingStates.hideButtonLoading(button);
        window.skeletonLoader.hide(container);
    }
}
```

### 3. Use contagem realista
```javascript
// ❌ Ruim - mostra 20 skeletons quando normalmente há 3 itens
window.skeletonLoader.show('#lista', 'convite-list', { count: 20 });

// ✅ Bom - mostra quantidade realista
window.skeletonLoader.show('#lista', 'convite-list', { count: 5 });
```

### 4. Trate erros adequadamente
```javascript
try {
    window.skeletonLoader.show('#container', 'convite-list');
    const data = await fetch('/api/data');
    window.skeletonLoader.hide('#container', render(data));
} catch (error) {
    // Mostra mensagem de erro em vez de deixar skeleton
    window.skeletonLoader.hide('#container', '<p class="error">Erro ao carregar</p>');
    window.toast.error('Erro ao carregar dados');
}
```

---

**Implementado em**: 02/12/2024  
**Versão**: 1.0  
**Status**: ✅ Pronto para Uso
