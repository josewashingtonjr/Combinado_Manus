/**
 * HIGH CONTRAST TOGGLE
 * Sistema de alternância de modo de alto contraste
 * Persiste preferência no localStorage
 */

(function() {
    'use strict';
    
    // Constantes
    const STORAGE_KEY = 'high-contrast-mode';
    const HIGH_CONTRAST_CLASS = 'high-contrast';
    
    /**
     * Inicializa o sistema de alto contraste
     */
    function initHighContrast() {
        // Verificar preferência salva
        const savedPreference = localStorage.getItem(STORAGE_KEY);
        
        if (savedPreference === 'enabled') {
            enableHighContrast();
        }
        
        // Criar botão de toggle se não existir
        createToggleButton();
        
        // Adicionar listener para atalho de teclado (Ctrl+Alt+C)
        document.addEventListener('keydown', handleKeyboardShortcut);
    }
    
    /**
     * Cria o botão de toggle de alto contraste
     */
    function createToggleButton() {
        // Verificar se já existe
        if (document.getElementById('high-contrast-toggle')) {
            return;
        }
        
        const button = document.createElement('button');
        button.id = 'high-contrast-toggle';
        button.className = 'high-contrast-toggle';
        button.setAttribute('aria-label', 'Alternar modo de alto contraste');
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('title', 'Ativar/Desativar Alto Contraste (Ctrl+Alt+C)');
        
        button.innerHTML = `
            <span class="high-contrast-toggle-icon" aria-hidden="true">◐</span>
            <span class="high-contrast-toggle-text">Alto Contraste</span>
        `;
        
        button.addEventListener('click', toggleHighContrast);
        
        document.body.appendChild(button);
        
        // Atualizar estado do botão
        updateButtonState();
    }
    
    /**
     * Alterna o modo de alto contraste
     */
    function toggleHighContrast() {
        const isEnabled = document.documentElement.classList.contains(HIGH_CONTRAST_CLASS);
        
        if (isEnabled) {
            disableHighContrast();
        } else {
            enableHighContrast();
        }
    }
    
    /**
     * Ativa o modo de alto contraste
     */
    function enableHighContrast() {
        document.documentElement.classList.add(HIGH_CONTRAST_CLASS);
        document.body.classList.add(HIGH_CONTRAST_CLASS);
        localStorage.setItem(STORAGE_KEY, 'enabled');
        updateButtonState();
        
        // Anunciar mudança para leitores de tela
        announceToScreenReader('Modo de alto contraste ativado');
    }
    
    /**
     * Desativa o modo de alto contraste
     */
    function disableHighContrast() {
        document.documentElement.classList.remove(HIGH_CONTRAST_CLASS);
        document.body.classList.remove(HIGH_CONTRAST_CLASS);
        localStorage.setItem(STORAGE_KEY, 'disabled');
        updateButtonState();
        
        // Anunciar mudança para leitores de tela
        announceToScreenReader('Modo de alto contraste desativado');
    }
    
    /**
     * Atualiza o estado visual do botão
     */
    function updateButtonState() {
        const button = document.getElementById('high-contrast-toggle');
        if (!button) return;
        
        const isEnabled = document.documentElement.classList.contains(HIGH_CONTRAST_CLASS);
        button.setAttribute('aria-pressed', isEnabled ? 'true' : 'false');
        
        const text = button.querySelector('.high-contrast-toggle-text');
        if (text) {
            text.textContent = isEnabled ? 'Contraste Normal' : 'Alto Contraste';
        }
    }
    
    /**
     * Manipula atalho de teclado (Ctrl+Alt+C)
     */
    function handleKeyboardShortcut(event) {
        if (event.ctrlKey && event.altKey && event.key === 'c') {
            event.preventDefault();
            toggleHighContrast();
        }
    }
    
    /**
     * Anuncia mensagem para leitores de tela
     */
    function announceToScreenReader(message) {
        // Criar ou obter região de anúncio
        let announcer = document.getElementById('a11y-announcer');
        
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'a11y-announcer';
            announcer.setAttribute('role', 'status');
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.style.position = 'absolute';
            announcer.style.left = '-10000px';
            announcer.style.width = '1px';
            announcer.style.height = '1px';
            announcer.style.overflow = 'hidden';
            document.body.appendChild(announcer);
        }
        
        // Limpar e adicionar nova mensagem
        announcer.textContent = '';
        setTimeout(() => {
            announcer.textContent = message;
        }, 100);
    }
    
    /**
     * Verifica se o navegador suporta preferências de contraste
     */
    function checkSystemPreferences() {
        // Verificar preferência de alto contraste do sistema
        if (window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches) {
            console.log('Sistema configurado para alto contraste');
            // Não ativar automaticamente, apenas informar
        }
    }
    
    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHighContrast);
    } else {
        initHighContrast();
    }
    
    // Verificar preferências do sistema
    checkSystemPreferences();
    
    // Expor API pública
    window.HighContrastMode = {
        enable: enableHighContrast,
        disable: disableHighContrast,
        toggle: toggleHighContrast,
        isEnabled: function() {
            return document.documentElement.classList.contains(HIGH_CONTRAST_CLASS);
        }
    };
    
})();
