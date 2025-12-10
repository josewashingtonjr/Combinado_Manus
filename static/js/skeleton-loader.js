/**
 * Skeleton Loader System
 * Sistema de skeleton loading para melhorar percepção de velocidade
 * 
 * Funcionalidades:
 * - Gerenciamento de skeleton loading
 * - Integração com loading states
 * - Transições suaves
 * - Suporte a diferentes tipos de conteúdo
 * 
 * Requirements: 8.2
 */

class SkeletonLoader {
    constructor(options = {}) {
        this.options = {
            minDisplayTime: options.minDisplayTime || 500, // Tempo mínimo para mostrar skeleton
            fadeOutDuration: options.fadeOutDuration || 300, // Duração do fade out
            autoHide: options.autoHide !== false, // Auto-esconder quando conteúdo carregar
            ...options
        };

        this.activeSkeletons = new Map();
        this.init();
    }

    init() {
        console.log('Skeleton Loader System inicializado');
        
        // Observa mudanças no DOM
        this.observeDOMChanges();
        
        // Integra com loading states existente
        this.integrateWithLoadingStates();
    }

    /**
     * Mostra skeleton loading em um container
     * @param {HTMLElement|string} target - Elemento ou seletor CSS
     * @param {string} type - Tipo de skeleton (convite-card, ordem-card, convite-list, etc)
     * @param {object} options - Opções adicionais
     */
    show(target, type = 'convite-card', options = {}) {
        const container = typeof target === 'string' ? document.querySelector(target) : target;
        
        if (!container) {
            console.warn('Container não encontrado:', target);
            return;
        }

        // Se já está mostrando skeleton, ignora
        if (this.activeSkeletons.has(container)) {
            return;
        }

        // Salva conteúdo original
        const originalContent = container.innerHTML;
        const startTime = Date.now();

        this.activeSkeletons.set(container, {
            originalContent,
            startTime,
            type,
            options
        });

        // Adiciona classe de container
        container.classList.add('skeleton-loading-container');
        container.setAttribute('aria-busy', 'true');

        // Carrega e insere skeleton
        this.loadSkeleton(container, type, options);
    }

    /**
     * Esconde skeleton loading e restaura conteúdo
     * @param {HTMLElement|string} target - Elemento ou seletor CSS
     * @param {string} newContent - Novo conteúdo opcional
     */
    hide(target, newContent = null) {
        const container = typeof target === 'string' ? document.querySelector(target) : target;
        
        if (!container || !this.activeSkeletons.has(container)) {
            return;
        }

        const skeletonData = this.activeSkeletons.get(container);
        const elapsedTime = Date.now() - skeletonData.startTime;
        const remainingTime = Math.max(0, this.options.minDisplayTime - elapsedTime);

        // Aguarda tempo mínimo
        setTimeout(() => {
            this.performHide(container, newContent || skeletonData.originalContent);
        }, remainingTime);
    }

    /**
     * Executa o hide com transição
     */
    performHide(container, content) {
        // Adiciona classe de fade out
        container.classList.add('skeleton-fade-out');

        setTimeout(() => {
            // Restaura conteúdo
            container.innerHTML = content;
            
            // Remove classes
            container.classList.remove('skeleton-loading-container', 'skeleton-fade-out');
            container.removeAttribute('aria-busy');
            
            // Adiciona classe de fade in
            container.classList.add('skeleton-fade-in');
            
            setTimeout(() => {
                container.classList.remove('skeleton-fade-in');
            }, this.options.fadeOutDuration);

            // Remove do mapa
            this.activeSkeletons.delete(container);

            // Dispara evento customizado
            container.dispatchEvent(new CustomEvent('skeleton-hidden', {
                bubbles: true,
                detail: { container }
            }));
        }, this.options.fadeOutDuration);
    }

    /**
     * Carrega template de skeleton
     */
    loadSkeleton(container, type, options = {}) {
        const count = options.count || 3;
        let skeletonHTML = '';

        switch (type) {
            case 'convite-card':
                skeletonHTML = this.getConviteCardSkeleton();
                break;
            
            case 'ordem-card':
                skeletonHTML = this.getOrdemCardSkeleton();
                break;
            
            case 'convite-list':
                skeletonHTML = this.getConviteListSkeleton(count);
                break;
            
            case 'ordem-list':
                skeletonHTML = this.getOrdemListSkeleton(count);
                break;
            
            case 'convite-detail':
                skeletonHTML = this.getConviteDetailSkeleton();
                break;
            
            case 'ordem-detail':
                skeletonHTML = this.getOrdemDetailSkeleton();
                break;
            
            case 'dashboard':
                skeletonHTML = this.getDashboardSkeleton();
                break;
            
            default:
                skeletonHTML = this.getGenericSkeleton(count);
        }

        container.innerHTML = skeletonHTML;

        // Dispara evento customizado
        container.dispatchEvent(new CustomEvent('skeleton-shown', {
            bubbles: true,
            detail: { container, type }
        }));
    }

    /**
     * Templates de skeleton inline (para não depender de arquivos externos)
     */
    
    getConviteCardSkeleton() {
        return `
            <div class="skeleton-convite-card" role="status" aria-label="Carregando convite...">
                <div class="skeleton-convite-header">
                    <div class="skeleton-convite-title-group">
                        <div class="skeleton skeleton-text-title"></div>
                        <div class="skeleton skeleton-text-subtitle"></div>
                    </div>
                    <div class="skeleton skeleton-badge"></div>
                </div>
                <div class="skeleton-convite-body">
                    <div class="skeleton-convite-info-row">
                        <div class="skeleton-convite-info-item">
                            <div class="skeleton skeleton-text" style="width: 60px; height: 12px;"></div>
                            <div class="skeleton skeleton-text" style="width: 100px; height: 20px;"></div>
                        </div>
                        <div class="skeleton-convite-info-item">
                            <div class="skeleton skeleton-text" style="width: 60px; height: 12px;"></div>
                            <div class="skeleton skeleton-text" style="width: 100px; height: 20px;"></div>
                        </div>
                    </div>
                    <div class="skeleton skeleton-text-medium"></div>
                    <div class="skeleton skeleton-text-short"></div>
                </div>
                <div class="skeleton-convite-actions">
                    <div class="skeleton skeleton-button"></div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            </div>
        `;
    }

    getOrdemCardSkeleton() {
        return `
            <div class="skeleton-ordem-card" role="status" aria-label="Carregando ordem...">
                <div class="skeleton-ordem-header">
                    <div class="skeleton skeleton-ordem-id"></div>
                    <div class="skeleton skeleton-badge"></div>
                </div>
                <div class="skeleton-ordem-body">
                    <div class="skeleton skeleton-ordem-value"></div>
                    <div class="skeleton-ordem-details">
                        <div class="skeleton-ordem-detail-item">
                            <div class="skeleton skeleton-text" style="width: 70px; height: 12px;"></div>
                            <div class="skeleton skeleton-text" style="width: 100px; height: 18px;"></div>
                        </div>
                        <div class="skeleton-ordem-detail-item">
                            <div class="skeleton skeleton-text" style="width: 60px; height: 12px;"></div>
                            <div class="skeleton skeleton-text" style="width: 90px; height: 18px;"></div>
                        </div>
                    </div>
                    <div class="skeleton skeleton-text-long"></div>
                </div>
                <div class="skeleton-ordem-actions">
                    <div class="skeleton skeleton-button"></div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            </div>
        `;
    }

    getConviteListSkeleton(count = 3) {
        let items = '';
        for (let i = 0; i < count; i++) {
            items += `
                <div class="skeleton-convite-list-item">
                    <div class="skeleton skeleton-convite-list-icon"></div>
                    <div class="skeleton-convite-list-content">
                        <div class="skeleton skeleton-text-title"></div>
                        <div class="skeleton skeleton-text-subtitle"></div>
                        <div class="skeleton skeleton-text-short"></div>
                    </div>
                    <div class="skeleton-convite-list-actions">
                        <div class="skeleton skeleton-button-small"></div>
                    </div>
                </div>
            `;
        }
        return `<div class="skeleton-convites-list" role="status" aria-label="Carregando lista de convites...">${items}</div>`;
    }

    getOrdemListSkeleton(count = 3) {
        let items = '';
        for (let i = 0; i < count; i++) {
            items += `
                <div class="skeleton-ordem-list-item">
                    <div class="skeleton-ordem-list-left">
                        <div class="skeleton skeleton-text-title"></div>
                        <div class="skeleton skeleton-text-subtitle"></div>
                        <div class="skeleton skeleton-text-short"></div>
                    </div>
                    <div class="skeleton-ordem-list-right">
                        <div class="skeleton skeleton-badge"></div>
                        <div class="skeleton skeleton-text" style="width: 100px; height: 24px;"></div>
                        <div class="skeleton skeleton-button-small"></div>
                    </div>
                </div>
            `;
        }
        return `<div class="skeleton-ordens-list" role="status" aria-label="Carregando lista de ordens...">${items}</div>`;
    }

    getConviteDetailSkeleton() {
        return `
            <div class="skeleton-convite-detail" role="status" aria-label="Carregando detalhes do convite...">
                <div class="skeleton-convite-detail-header">
                    <div class="skeleton skeleton-text-title" style="width: 70%;"></div>
                    <div class="skeleton skeleton-badge" style="margin-top: 12px;"></div>
                </div>
                <div class="skeleton-convite-detail-section">
                    <div class="skeleton skeleton-convite-detail-section-title"></div>
                    <div class="skeleton-convite-detail-grid">
                        ${this.getDetailGridItems(4)}
                    </div>
                </div>
                <div class="skeleton-convite-detail-actions">
                    <div class="skeleton skeleton-button"></div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            </div>
        `;
    }

    getOrdemDetailSkeleton() {
        return `
            <div class="skeleton-ordem-detail" role="status" aria-label="Carregando detalhes da ordem...">
                <div class="skeleton-ordem-detail-header">
                    <div>
                        <div class="skeleton skeleton-text-title" style="width: 200px;"></div>
                        <div class="skeleton skeleton-text-subtitle" style="margin-top: 8px;"></div>
                    </div>
                    <div class="skeleton skeleton-badge"></div>
                </div>
                <div class="skeleton-convite-detail-section">
                    <div class="skeleton skeleton-convite-detail-section-title"></div>
                    <div class="skeleton-convite-detail-grid">
                        ${this.getDetailGridItems(4)}
                    </div>
                </div>
                <div class="skeleton-convite-detail-actions">
                    <div class="skeleton skeleton-button"></div>
                    <div class="skeleton skeleton-button"></div>
                </div>
            </div>
        `;
    }

    getDashboardSkeleton() {
        return `
            <div class="skeleton-dashboard" role="status" aria-label="Carregando dashboard...">
                <div class="skeleton-dashboard-stats">
                    ${this.getStatCards(4)}
                </div>
                ${this.getConviteListSkeleton(3)}
            </div>
        `;
    }

    getGenericSkeleton(count = 3) {
        let lines = '';
        for (let i = 0; i < count; i++) {
            lines += '<div class="skeleton skeleton-text"></div>';
        }
        return `<div class="skeleton-generic" role="status" aria-label="Carregando...">${lines}</div>`;
    }

    getDetailGridItems(count) {
        let items = '';
        for (let i = 0; i < count; i++) {
            items += `
                <div class="skeleton-convite-detail-item">
                    <div class="skeleton skeleton-convite-detail-label"></div>
                    <div class="skeleton skeleton-convite-detail-value"></div>
                </div>
            `;
        }
        return items;
    }

    getStatCards(count) {
        let cards = '';
        for (let i = 0; i < count; i++) {
            cards += `
                <div class="skeleton-stat-card">
                    <div class="skeleton skeleton-stat-label"></div>
                    <div class="skeleton skeleton-stat-value"></div>
                </div>
            `;
        }
        return cards;
    }

    /**
     * Integra com sistema de loading states existente
     */
    integrateWithLoadingStates() {
        // Se existir LoadingStates, estende funcionalidade
        if (window.LoadingStates) {
            const originalShowSkeleton = window.LoadingStates.prototype.showSkeleton;
            
            window.LoadingStates.prototype.showSkeleton = (container, type, count) => {
                if (window.skeletonLoader) {
                    window.skeletonLoader.show(container, type, { count });
                } else {
                    originalShowSkeleton.call(this, container, type, count);
                }
            };
        }
    }

    /**
     * Observa mudanças no DOM
     */
    observeDOMChanges() {
        // Detecta quando conteúdo é carregado via AJAX
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.hasAttribute('data-skeleton-target')) {
                        const type = node.getAttribute('data-skeleton-type') || 'convite-card';
                        this.show(node, type);
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
     * Wrapper para fetch com skeleton loading
     */
    async fetchWithSkeleton(url, options = {}) {
        const {
            container,
            skeletonType = 'convite-card',
            skeletonOptions = {},
            ...fetchOptions
        } = options;

        if (container) {
            this.show(container, skeletonType, skeletonOptions);
        }

        try {
            const response = await fetch(url, fetchOptions);
            const data = await response.json();

            if (container && data.html) {
                this.hide(container, data.html);
            }

            return data;
        } catch (error) {
            console.error('Erro no fetch:', error);
            
            if (container) {
                this.hide(container, '<p class="error-message">Erro ao carregar conteúdo</p>');
            }
            
            throw error;
        }
    }

    /**
     * Reseta todos os skeletons ativos
     */
    resetAll() {
        this.activeSkeletons.forEach((data, container) => {
            this.hide(container);
        });
    }
}

// CSS para transições
const skeletonTransitionStyles = `
.skeleton-loading-container {
    min-height: 200px;
    position: relative;
}

.skeleton-fade-out {
    animation: skeletonFadeOut 0.3s ease-out forwards;
}

.skeleton-fade-in {
    animation: skeletonFadeIn 0.3s ease-in forwards;
}

@keyframes skeletonFadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

@keyframes skeletonFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Acessibilidade */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
`;

// Injeta estilos
function injectSkeletonTransitionStyles() {
    const styleId = 'skeleton-transition-styles';
    
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = skeletonTransitionStyles;
        document.head.appendChild(style);
    }
}

// Inicialização
let skeletonLoaderInstance = null;

function initSkeletonLoader(options = {}) {
    injectSkeletonTransitionStyles();
    skeletonLoaderInstance = new SkeletonLoader(options);
    return skeletonLoaderInstance;
}

// Inicializa quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initSkeletonLoader());
} else {
    initSkeletonLoader();
}

// Exporta para uso global
window.SkeletonLoader = SkeletonLoader;
window.skeletonLoader = skeletonLoaderInstance;
window.initSkeletonLoader = initSkeletonLoader;
