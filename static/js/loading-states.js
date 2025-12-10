/**
 * Loading States System
 * Sistema de estados de carregamento para melhorar feedback visual
 * 
 * Funcionalidades:
 * - Spinner em botões durante ação
 * - Desabilitar botão durante processamento
 * - Skeleton loading para conteúdo
 * - Integração com formulários e ações AJAX
 * 
 * Requirements: 5.1, 8.2
 */

class LoadingStates {
    constructor(options = {}) {
        this.options = {
            spinnerHTML: options.spinnerHTML || '<i class="fas fa-spinner fa-spin"></i>',
            spinnerText: options.spinnerText || 'Carregando...',
            minLoadingTime: options.minLoadingTime || 300, // Tempo mínimo para evitar flash
            ...options
        };
        
        this.loadingButtons = new Map();
        this.loadingForms = new Set();
        this.init();
    }

    init() {
        console.log('Loading States System inicializado');
        
        // Integra com formulários automaticamente
        this.attachFormHandlers();
        
        // Integra com botões de ação
        this.attachButtonHandlers();
        
        // Observa mudanças no DOM para novos elementos
        this.observeDOMChanges();
    }

    /**
     * Adiciona spinner a um botão
     * @param {HTMLElement} button - Elemento do botão
     * @param {string} text - Texto opcional durante loading
     */
    showButtonLoading(button, text = null) {
        if (!button || this.loadingButtons.has(button)) {
            return; // Já está em loading
        }

        // Salva estado original
        const originalState = {
            html: button.innerHTML,
            disabled: button.disabled,
            classList: Array.from(button.classList),
            startTime: Date.now()
        };
        
        this.loadingButtons.set(button, originalState);

        // Desabilita o botão
        button.disabled = true;
        button.classList.add('btn-loading');

        // Cria conteúdo de loading
        const loadingText = text || this.options.spinnerText;
        const spinnerHTML = `
            <span class="btn-loading-content">
                <span class="btn-spinner">${this.options.spinnerHTML}</span>
                <span class="btn-loading-text">${loadingText}</span>
            </span>
        `;

        button.innerHTML = spinnerHTML;
    }

    /**
     * Remove spinner de um botão
     * @param {HTMLElement} button - Elemento do botão
     */
    hideButtonLoading(button) {
        if (!button || !this.loadingButtons.has(button)) {
            return;
        }

        const originalState = this.loadingButtons.get(button);
        const elapsedTime = Date.now() - originalState.startTime;
        const remainingTime = Math.max(0, this.options.minLoadingTime - elapsedTime);

        // Aguarda tempo mínimo para evitar flash
        setTimeout(() => {
            // Restaura estado original
            button.innerHTML = originalState.html;
            button.disabled = originalState.disabled;
            button.classList.remove('btn-loading');

            this.loadingButtons.delete(button);
        }, remainingTime);
    }

    /**
     * Adiciona loading a um formulário
     * @param {HTMLFormElement} form - Elemento do formulário
     */
    showFormLoading(form) {
        if (!form || this.loadingForms.has(form)) {
            return;
        }

        this.loadingForms.add(form);
        form.classList.add('form-loading');

        // Desabilita todos os inputs e botões
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => {
            input.dataset.wasDisabled = input.disabled;
            input.disabled = true;
        });

        // Adiciona spinner ao botão de submit
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            this.showButtonLoading(submitButton);
        }
    }

    /**
     * Remove loading de um formulário
     * @param {HTMLFormElement} form - Elemento do formulário
     */
    hideFormLoading(form) {
        if (!form || !this.loadingForms.has(form)) {
            return;
        }

        this.loadingForms.delete(form);
        form.classList.remove('form-loading');

        // Reabilita inputs que não estavam desabilitados
        const inputs = form.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => {
            if (input.dataset.wasDisabled === 'false') {
                input.disabled = false;
            }
            delete input.dataset.wasDisabled;
        });

        // Remove spinner do botão de submit
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            this.hideButtonLoading(submitButton);
        }
    }

    /**
     * Cria skeleton loading para um container
     * @param {HTMLElement} container - Container onde criar skeleton
     * @param {string} type - Tipo de skeleton (card, list, table)
     * @param {number} count - Quantidade de itens skeleton
     */
    showSkeleton(container, type = 'card', count = 3) {
        if (!container) return;

        container.classList.add('skeleton-container');
        container.dataset.originalContent = container.innerHTML;

        let skeletonHTML = '';

        switch (type) {
            case 'card':
                skeletonHTML = this.createCardSkeleton(count);
                break;
            case 'list':
                skeletonHTML = this.createListSkeleton(count);
                break;
            case 'table':
                skeletonHTML = this.createTableSkeleton(count);
                break;
            default:
                skeletonHTML = this.createGenericSkeleton(count);
        }

        container.innerHTML = skeletonHTML;
    }

    /**
     * Remove skeleton loading
     * @param {HTMLElement} container - Container com skeleton
     */
    hideSkeleton(container) {
        if (!container || !container.dataset.originalContent) {
            return;
        }

        container.classList.remove('skeleton-container');
        container.innerHTML = container.dataset.originalContent;
        delete container.dataset.originalContent;
    }

    /**
     * Cria skeleton de card
     */
    createCardSkeleton(count) {
        let html = '<div class="skeleton-cards">';
        for (let i = 0; i < count; i++) {
            html += `
                <div class="skeleton-card">
                    <div class="skeleton-header">
                        <div class="skeleton-line skeleton-title"></div>
                        <div class="skeleton-line skeleton-subtitle"></div>
                    </div>
                    <div class="skeleton-body">
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line"></div>
                        <div class="skeleton-line skeleton-short"></div>
                    </div>
                    <div class="skeleton-footer">
                        <div class="skeleton-button"></div>
                        <div class="skeleton-button"></div>
                    </div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }

    /**
     * Cria skeleton de lista
     */
    createListSkeleton(count) {
        let html = '<div class="skeleton-list">';
        for (let i = 0; i < count; i++) {
            html += `
                <div class="skeleton-list-item">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-content">
                        <div class="skeleton-line skeleton-title"></div>
                        <div class="skeleton-line skeleton-subtitle"></div>
                    </div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }

    /**
     * Cria skeleton de tabela
     */
    createTableSkeleton(count) {
        let html = '<div class="skeleton-table">';
        html += '<div class="skeleton-table-header">';
        for (let i = 0; i < 4; i++) {
            html += '<div class="skeleton-line"></div>';
        }
        html += '</div>';
        
        for (let i = 0; i < count; i++) {
            html += '<div class="skeleton-table-row">';
            for (let j = 0; j < 4; j++) {
                html += '<div class="skeleton-line"></div>';
            }
            html += '</div>';
        }
        html += '</div>';
        return html;
    }

    /**
     * Cria skeleton genérico
     */
    createGenericSkeleton(count) {
        let html = '<div class="skeleton-generic">';
        for (let i = 0; i < count; i++) {
            html += '<div class="skeleton-line"></div>';
        }
        html += '</div>';
        return html;
    }

    /**
     * Integra com formulários automaticamente
     */
    attachFormHandlers() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            
            // Ignora se já está em loading
            if (this.loadingForms.has(form)) {
                e.preventDefault();
                return false;
            }

            // Adiciona loading ao formulário
            this.showFormLoading(form);

            // Se for AJAX, não faz nada mais
            if (form.dataset.ajax === 'true') {
                return;
            }

            // Para formulários normais, o loading será removido no redirect
        });
    }

    /**
     * Integra com botões de ação
     */
    attachButtonHandlers() {
        // Botões com data-loading
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-loading]');
            if (!button) return;

            const loadingText = button.dataset.loadingText || null;
            this.showButtonLoading(button, loadingText);

            // Se tiver data-loading-duration, remove automaticamente
            const duration = parseInt(button.dataset.loadingDuration);
            if (duration) {
                setTimeout(() => {
                    this.hideButtonLoading(button);
                }, duration);
            }
        });
    }

    /**
     * Observa mudanças no DOM para novos elementos
     */
    observeDOMChanges() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        // Reanexa handlers em novos formulários
                        if (node.tagName === 'FORM') {
                            // Já está coberto pelo event delegation
                        }
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Wrapper para fetch com loading automático
     * @param {string} url - URL da requisição
     * @param {object} options - Opções do fetch
     * @param {HTMLElement} button - Botão opcional para mostrar loading
     * @returns {Promise}
     */
    async fetchWithLoading(url, options = {}, button = null) {
        if (button) {
            this.showButtonLoading(button);
        }

        try {
            const response = await fetch(url, options);
            return response;
        } finally {
            if (button) {
                this.hideButtonLoading(button);
            }
        }
    }

    /**
     * Wrapper para AJAX com loading automático
     * @param {object} config - Configuração da requisição
     * @returns {Promise}
     */
    async ajaxWithLoading(config) {
        const {
            url,
            method = 'GET',
            data = null,
            button = null,
            form = null,
            container = null,
            skeletonType = 'card',
            onSuccess = null,
            onError = null
        } = config;

        // Mostra loading
        if (button) this.showButtonLoading(button);
        if (form) this.showFormLoading(form);
        if (container) this.showSkeleton(container, skeletonType);

        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            const result = await response.json();

            if (response.ok) {
                if (onSuccess) onSuccess(result);
                
                // Mostra toast de sucesso se houver mensagem
                if (result.message && window.toast) {
                    window.toast.success(result.message);
                }
            } else {
                throw new Error(result.message || 'Erro na requisição');
            }

            return result;

        } catch (error) {
            console.error('Erro na requisição:', error);
            
            if (onError) {
                onError(error);
            }
            
            // Mostra toast de erro
            if (window.toast) {
                window.toast.error(error.message || 'Erro ao processar requisição');
            }
            
            throw error;

        } finally {
            // Remove loading
            if (button) this.hideButtonLoading(button);
            if (form) this.hideFormLoading(form);
            if (container) this.hideSkeleton(container);
        }
    }

    /**
     * Reseta todos os estados de loading
     */
    resetAll() {
        // Reseta botões
        this.loadingButtons.forEach((state, button) => {
            this.hideButtonLoading(button);
        });

        // Reseta formulários
        this.loadingForms.forEach(form => {
            this.hideFormLoading(form);
        });
    }
}

// CSS necessário para loading states
const loadingStyles = `
/* Botão Loading */
.btn-loading {
    position: relative;
    pointer-events: none;
    opacity: 0.7;
}

.btn-loading-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn-spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.btn-loading-text {
    font-size: 0.9em;
}

/* Form Loading */
.form-loading {
    position: relative;
    opacity: 0.6;
    pointer-events: none;
}

/* Skeleton Loading */
.skeleton-container {
    animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.skeleton-line {
    height: 16px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: 4px;
    margin-bottom: 8px;
}

@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-title {
    height: 24px;
    width: 60%;
}

.skeleton-subtitle {
    height: 16px;
    width: 40%;
}

.skeleton-short {
    width: 70%;
}

.skeleton-button {
    height: 40px;
    width: 100px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: 8px;
    display: inline-block;
    margin-right: 8px;
}

/* Skeleton Card */
.skeleton-cards {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.skeleton-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    background: white;
}

.skeleton-header {
    margin-bottom: 16px;
}

.skeleton-body {
    margin-bottom: 16px;
}

.skeleton-footer {
    display: flex;
    gap: 8px;
}

/* Skeleton List */
.skeleton-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.skeleton-list-item {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 12px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

.skeleton-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    flex-shrink: 0;
}

.skeleton-content {
    flex: 1;
}

/* Skeleton Table */
.skeleton-table {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
}

.skeleton-table-header,
.skeleton-table-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 12px;
}

.skeleton-table-header {
    background: #f8f9fa;
    border-bottom: 2px solid #e0e0e0;
}

.skeleton-table-row {
    border-bottom: 1px solid #f0f0f0;
}

.skeleton-table-row:last-child {
    border-bottom: none;
}

/* Skeleton Generic */
.skeleton-generic {
    padding: 16px;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .skeleton-table-header,
    .skeleton-table-row {
        grid-template-columns: 1fr;
    }
    
    .skeleton-button {
        width: 100%;
        margin-bottom: 8px;
    }
}
`;

// Injeta estilos no documento
function injectLoadingStyles() {
    const styleId = 'loading-states-styles';
    
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = loadingStyles;
        document.head.appendChild(style);
    }
}

// Inicialização automática
let loadingStatesInstance = null;

function initLoadingStates(options = {}) {
    injectLoadingStyles();
    loadingStatesInstance = new LoadingStates(options);
    return loadingStatesInstance;
}

// Inicializa quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initLoadingStates());
} else {
    initLoadingStates();
}

// Exporta para uso global
window.LoadingStates = LoadingStates;
window.loadingStates = loadingStatesInstance;
window.initLoadingStates = initLoadingStates;
