/**
 * Script para funcionalidade dos menus do painel admin
 * Gerencia colapso/expansão e persistência de estado
 */

(function() {
    'use strict';
    
    // Chave para armazenar estado dos menus no localStorage
    const STORAGE_KEY = 'admin_menu_state';
    
    /**
     * Salva o estado de um menu no localStorage
     */
    function saveMenuState(menuId, isExpanded) {
        try {
            const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            state[menuId] = isExpanded;
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
            console.warn('Não foi possível salvar estado do menu:', e);
        }
    }
    
    /**
     * Recupera o estado de um menu do localStorage
     */
    function getMenuState(menuId) {
        try {
            const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
            return state[menuId];
        } catch (e) {
            console.warn('Não foi possível recuperar estado do menu:', e);
            return null;
        }
    }
    
    /**
     * Restaura o estado dos menus ao carregar a página
     */
    function restoreMenuStates() {
        const menus = document.querySelectorAll('[data-bs-toggle="collapse"]');
        
        menus.forEach(function(menuHeader) {
            const targetId = menuHeader.getAttribute('href').substring(1);
            const isExpanded = getMenuState(targetId);
            
            if (isExpanded === true) {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    // Usar Bootstrap Collapse API
                    const bsCollapse = new bootstrap.Collapse(targetElement, {
                        toggle: false
                    });
                    bsCollapse.show();
                }
            }
        });
    }
    
    /**
     * Adiciona listeners para salvar estado quando menu é expandido/colapsado
     */
    function setupMenuListeners() {
        const menus = document.querySelectorAll('[data-bs-toggle="collapse"]');
        
        menus.forEach(function(menuHeader) {
            const targetId = menuHeader.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Evento quando menu é mostrado
                targetElement.addEventListener('shown.bs.collapse', function() {
                    saveMenuState(targetId, true);
                });
                
                // Evento quando menu é ocultado
                targetElement.addEventListener('hidden.bs.collapse', function() {
                    saveMenuState(targetId, false);
                });
            }
        });
    }
    
    /**
     * Destaca o item de menu ativo baseado na URL atual
     */
    function highlightActiveMenuItem() {
        const currentPath = window.location.pathname;
        const currentSearch = window.location.search;
        const currentUrl = currentPath + currentSearch;
        
        // Remover classe active de todos os itens
        document.querySelectorAll('.sidebar-submenu-item').forEach(function(item) {
            item.classList.remove('active');
        });
        
        // Encontrar e destacar o item ativo
        document.querySelectorAll('.sidebar-submenu-item').forEach(function(item) {
            const itemHref = item.getAttribute('href');
            
            // Comparação exata para URLs com query strings
            if (itemHref === currentUrl) {
                item.classList.add('active');
                
                // Expandir o menu pai
                const parentCollapse = item.closest('.collapse');
                if (parentCollapse) {
                    const bsCollapse = new bootstrap.Collapse(parentCollapse, {
                        toggle: false
                    });
                    bsCollapse.show();
                }
            }
            // Comparação apenas do path para URLs sem query string
            else if (currentSearch === '' && itemHref === currentPath) {
                item.classList.add('active');
                
                // Expandir o menu pai
                const parentCollapse = item.closest('.collapse');
                if (parentCollapse) {
                    const bsCollapse = new bootstrap.Collapse(parentCollapse, {
                        toggle: false
                    });
                    bsCollapse.show();
                }
            }
        });
    }
    
    /**
     * Adiciona suporte para navegação por teclado
     */
    function setupKeyboardNavigation() {
        const menuItems = document.querySelectorAll('.sidebar-menu-header, .sidebar-submenu-item');
        
        menuItems.forEach(function(item, index) {
            item.addEventListener('keydown', function(e) {
                let targetIndex;
                
                switch(e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        targetIndex = (index + 1) % menuItems.length;
                        menuItems[targetIndex].focus();
                        break;
                        
                    case 'ArrowUp':
                        e.preventDefault();
                        targetIndex = (index - 1 + menuItems.length) % menuItems.length;
                        menuItems[targetIndex].focus();
                        break;
                        
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        item.click();
                        break;
                }
            });
        });
    }
    
    /**
     * Fallback para navegadores sem JavaScript
     */
    function removeNoJsClass() {
        document.documentElement.classList.remove('no-js');
    }
    
    /**
     * Inicialização quando DOM estiver pronto
     */
    function init() {
        removeNoJsClass();
        setupMenuListeners();
        restoreMenuStates();
        highlightActiveMenuItem();
        setupKeyboardNavigation();
        
        console.log('✓ Menu admin inicializado com sucesso');
    }
    
    // Executar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
