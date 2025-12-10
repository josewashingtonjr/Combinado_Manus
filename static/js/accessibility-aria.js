/**
 * ACCESSIBILITY ARIA ENHANCEMENT
 * 
 * Adiciona automaticamente atributos ARIA e melhora a acessibilidade
 * para elementos que não têm labels adequados.
 * 
 * Requirements: 7.3, 7.4, 7.5
 * - Garantir label em todos os campos de formulário
 * - Adicionar aria-label em ícones
 * - Implementar aria-live para mensagens dinâmicas
 */

(function() {
    'use strict';
    
    /**
     * Adiciona aria-label a ícones que não têm texto descritivo
     */
    function enhanceIcons() {
        // Mapear ícones comuns para descrições
        const iconDescriptions = {
            'fa-home': 'Início',
            'fa-envelope': 'Convites',
            'fa-envelope-open-text': 'Criar convite',
            'fa-handshake': 'Negociação',
            'fa-clipboard-list': 'Ordens',
            'fa-user-circle': 'Perfil',
            'fa-wallet': 'Carteira',
            'fa-phone': 'Telefone',
            'fa-calendar': 'Data',
            'fa-tag': 'Título',
            'fa-tools': 'Categoria',
            'fa-align-left': 'Descrição',
            'fa-dollar-sign': 'Valor',
            'fa-calculator': 'Cálculo',
            'fa-info-circle': 'Informação',
            'fa-exclamation-triangle': 'Atenção',
            'fa-exclamation-circle': 'Aviso',
            'fa-check-circle': 'Sucesso',
            'fa-times-circle': 'Erro',
            'fa-trash': 'Excluir',
            'fa-edit': 'Editar',
            'fa-eye': 'Visualizar',
            'fa-arrow-left': 'Voltar',
            'fa-arrow-right': 'Avançar',
            'fa-plus': 'Adicionar',
            'fa-minus': 'Remover',
            'fa-search': 'Buscar',
            'fa-filter': 'Filtrar',
            'fa-download': 'Baixar',
            'fa-upload': 'Enviar',
            'fa-file-upload': 'Enviar arquivo',
            'fa-paperclip': 'Anexar',
            'fa-paper-plane': 'Enviar',
            'fa-times': 'Fechar',
            'fa-bars': 'Menu',
            'fa-cog': 'Configurações',
            'fa-sign-out-alt': 'Sair',
            'fa-bell': 'Notificações',
            'fa-question-circle': 'Ajuda',
            'fa-shield-alt': 'Proteção',
            'fa-lock': 'Bloqueado',
            'fa-unlock': 'Desbloqueado',
            'fa-check': 'Confirmar',
            'fa-ban': 'Cancelar',
            'fa-redo': 'Refazer',
            'fa-undo': 'Desfazer',
            'fa-copy': 'Copiar',
            'fa-paste': 'Colar',
            'fa-save': 'Salvar',
            'fa-print': 'Imprimir',
            'fa-share': 'Compartilhar',
            'fa-star': 'Favorito',
            'fa-heart': 'Curtir',
            'fa-comment': 'Comentar',
            'fa-reply': 'Responder',
            'fa-forward': 'Encaminhar',
            'fa-refresh': 'Atualizar',
            'fa-sync': 'Sincronizar',
            'fa-spinner': 'Carregando',
            'fa-circle-notch': 'Processando',
            'fa-hourglass': 'Aguardando',
            'fa-clock': 'Horário',
            'fa-history': 'Histórico',
            'fa-chart-line': 'Gráfico',
            'fa-chart-bar': 'Estatísticas',
            'fa-table': 'Tabela',
            'fa-list': 'Lista',
            'fa-th': 'Grade',
            'fa-th-list': 'Lista detalhada',
            'fa-sort': 'Ordenar',
            'fa-sort-up': 'Ordenar crescente',
            'fa-sort-down': 'Ordenar decrescente',
            'fa-code': 'Código',
            'fa-lightbulb': 'Dica',
            'fa-bolt': 'Ação rápida',
            'fa-fire': 'Urgente',
            'fa-flag': 'Marcar',
            'fa-bookmark': 'Salvar para depois',
            'fa-map-marker': 'Localização',
            'fa-map': 'Mapa',
            'fa-compass': 'Navegação',
            'fa-globe': 'Global',
            'fa-language': 'Idioma',
            'fa-image': 'Imagem',
            'fa-video': 'Vídeo',
            'fa-music': 'Áudio',
            'fa-file': 'Arquivo',
            'fa-folder': 'Pasta',
            'fa-database': 'Banco de dados',
            'fa-server': 'Servidor',
            'fa-cloud': 'Nuvem',
            'fa-link': 'Link',
            'fa-unlink': 'Remover link',
            'fa-external-link': 'Link externo',
            'fa-anchor': 'Âncora',
            'fa-bullseye': 'Objetivo',
            'fa-balance-scale': 'Equilíbrio',
            'fa-gavel': 'Decisão',
            'fa-briefcase': 'Trabalho',
            'fa-suitcase': 'Bagagem',
            'fa-graduation-cap': 'Educação',
            'fa-book': 'Livro',
            'fa-newspaper': 'Notícias',
            'fa-trophy': 'Conquista',
            'fa-gift': 'Presente',
            'fa-birthday-cake': 'Aniversário',
            'fa-certificate': 'Certificado',
            'fa-award': 'Prêmio',
            'fa-medal': 'Medalha',
            'fa-ribbon': 'Fita',
            'fa-wrench': 'Ferramenta',
            'fa-hammer': 'Construção',
            'fa-paint-brush': 'Pintura',
            'fa-palette': 'Cores',
            'fa-magic': 'Mágica',
            'fa-wand-magic': 'Varinha mágica'
        };
        
        // Selecionar todos os ícones
        const icons = document.querySelectorAll('i[class*="fa-"]');
        
        icons.forEach(function(icon) {
            // Verificar se o ícone já tem aria-label ou aria-hidden
            if (icon.hasAttribute('aria-label') || icon.hasAttribute('aria-hidden')) {
                return;
            }
            
            // Verificar se o ícone está dentro de um elemento com texto
            const parent = icon.parentElement;
            const hasText = parent && parent.textContent.trim().length > icon.textContent.trim().length;
            
            if (hasText) {
                // Se tem texto ao lado, marcar como decorativo
                icon.setAttribute('aria-hidden', 'true');
            } else {
                // Se não tem texto, tentar adicionar aria-label
                const classList = Array.from(icon.classList);
                let description = null;
                
                // Procurar descrição baseada nas classes
                for (let className of classList) {
                    if (iconDescriptions[className]) {
                        description = iconDescriptions[className];
                        break;
                    }
                }
                
                if (description) {
                    icon.setAttribute('aria-label', description);
                    icon.setAttribute('role', 'img');
                } else {
                    // Se não encontrou descrição, marcar como decorativo
                    icon.setAttribute('aria-hidden', 'true');
                }
            }
        });
    }
    
    /**
     * Garante que todos os campos de formulário têm labels
     */
    function enhanceFormFields() {
        // Selecionar todos os inputs, selects e textareas
        const fields = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
        
        fields.forEach(function(field) {
            // Verificar se já tem label associado
            const fieldId = field.id;
            const fieldName = field.name;
            
            if (!fieldId && !fieldName) {
                // Se não tem ID nem name, adicionar ID baseado no tipo
                const fieldType = field.type || field.tagName.toLowerCase();
                field.id = 'field-' + fieldType + '-' + Math.random().toString(36).substr(2, 9);
            }
            
            // Verificar se existe label associado
            const existingLabel = fieldId ? document.querySelector('label[for="' + fieldId + '"]') : null;
            
            if (!existingLabel && !field.hasAttribute('aria-label') && !field.hasAttribute('aria-labelledby')) {
                // Tentar encontrar label pelo contexto
                const placeholder = field.placeholder;
                const title = field.title;
                const ariaLabel = placeholder || title || field.name || 'Campo de formulário';
                
                field.setAttribute('aria-label', ariaLabel);
            }
            
            // Adicionar aria-required para campos obrigatórios
            if (field.hasAttribute('required') && !field.hasAttribute('aria-required')) {
                field.setAttribute('aria-required', 'true');
            }
            
            // Adicionar aria-invalid para campos com erro
            if (field.classList.contains('is-invalid') && !field.hasAttribute('aria-invalid')) {
                field.setAttribute('aria-invalid', 'true');
                
                // Procurar mensagem de erro associada
                const errorMessage = field.parentElement.querySelector('.invalid-feedback, .error-message');
                if (errorMessage && !errorMessage.id) {
                    errorMessage.id = 'error-' + (field.id || field.name);
                    field.setAttribute('aria-describedby', errorMessage.id);
                }
            }
        });
    }
    
    /**
     * Adiciona aria-live para mensagens dinâmicas
     */
    function enhanceDynamicMessages() {
        // Selecionar elementos de alerta e mensagens
        const alerts = document.querySelectorAll('.alert, .toast, .notification, .message, [role="alert"]');
        
        alerts.forEach(function(alert) {
            if (!alert.hasAttribute('aria-live')) {
                // Determinar o tipo de aria-live baseado na classe
                let ariaLive = 'polite';
                
                if (alert.classList.contains('alert-danger') || 
                    alert.classList.contains('alert-error') ||
                    alert.classList.contains('error')) {
                    ariaLive = 'assertive';
                }
                
                alert.setAttribute('aria-live', ariaLive);
                alert.setAttribute('aria-atomic', 'true');
            }
            
            // Garantir que tem role="alert" se for importante
            if (!alert.hasAttribute('role') && 
                (alert.classList.contains('alert-danger') || 
                 alert.classList.contains('alert-warning'))) {
                alert.setAttribute('role', 'alert');
            }
        });
        
        // Adicionar aria-live para contadores e badges
        const badges = document.querySelectorAll('.badge, .counter, [class*="badge"]');
        badges.forEach(function(badge) {
            if (!badge.hasAttribute('aria-live') && badge.textContent.trim().match(/^\d+$/)) {
                badge.setAttribute('aria-live', 'polite');
                badge.setAttribute('aria-atomic', 'true');
            }
        });
    }
    
    /**
     * Melhora a navegação por teclado
     */
    function enhanceKeyboardNavigation() {
        // Adicionar indicador visual de foco
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', function() {
            document.body.classList.remove('keyboard-navigation');
        });
        
        // Garantir que elementos interativos são focáveis
        const interactiveElements = document.querySelectorAll('[onclick], [data-toggle], [data-dismiss]');
        interactiveElements.forEach(function(element) {
            if (!element.hasAttribute('tabindex') && 
                element.tagName !== 'BUTTON' && 
                element.tagName !== 'A' &&
                element.tagName !== 'INPUT') {
                element.setAttribute('tabindex', '0');
                element.setAttribute('role', 'button');
                
                // Adicionar suporte para Enter e Space
                element.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.click();
                    }
                });
            }
        });
    }
    
    /**
     * Adiciona skip links para navegação rápida
     */
    function addSkipLinks() {
        // Verificar se já existe skip link
        if (document.querySelector('.skip-link')) {
            return;
        }
        
        // Criar skip link para conteúdo principal
        const mainContent = document.querySelector('main, [role="main"], #main-content, .main-content');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
        
        if (mainContent) {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link';
            skipLink.textContent = 'Pular para o conteúdo principal';
            skipLink.setAttribute('aria-label', 'Pular para o conteúdo principal');
            
            document.body.insertBefore(skipLink, document.body.firstChild);
        }
    }
    
    /**
     * Monitora mudanças no DOM para aplicar melhorias em conteúdo dinâmico
     */
    function observeDOMChanges() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    // Aplicar melhorias aos novos elementos
                    enhanceIcons();
                    enhanceFormFields();
                    enhanceDynamicMessages();
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Inicializa todas as melhorias de acessibilidade
     */
    function init() {
        // Aguardar DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        console.log('[Accessibility] Aplicando melhorias de acessibilidade...');
        
        enhanceIcons();
        enhanceFormFields();
        enhanceDynamicMessages();
        enhanceKeyboardNavigation();
        addSkipLinks();
        observeDOMChanges();
        
        console.log('[Accessibility] Melhorias de acessibilidade aplicadas com sucesso!');
    }
    
    // Inicializar
    init();
    
})();
