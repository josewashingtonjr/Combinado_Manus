/**
 * Toast Feedback System
 * Sistema de notificações toast não-bloqueantes
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.template = null;
        this.toasts = new Map();
        this.init();
    }

    /**
     * Inicializa o sistema de toast
     */
    init() {
        // Aguarda o DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    /**
     * Configura o container e template
     */
    setup() {
        this.container = document.getElementById('toast-container');
        this.template = document.getElementById('toast-template');

        if (!this.container || !this.template) {
            console.warn('Toast container ou template não encontrado');
            return;
        }

        // Converte mensagens flash do Flask em toasts
        this.convertFlashMessages();
    }

    /**
     * Converte mensagens flash do Flask em toasts
     */
    convertFlashMessages() {
        const flashAlerts = document.querySelectorAll('.alert:not(.toast-converted)');
        
        flashAlerts.forEach(alert => {
            // Extrai a mensagem
            const message = alert.textContent.trim();
            
            // Determina o tipo baseado na classe
            let type = 'info';
            if (alert.classList.contains('alert-success')) type = 'success';
            else if (alert.classList.contains('alert-danger') || alert.classList.contains('alert-error')) type = 'error';
            else if (alert.classList.contains('alert-warning')) type = 'warning';
            
            // Cria o toast
            this.show(message, type);
            
            // Remove o alert original
            alert.classList.add('toast-converted');
            alert.style.display = 'none';
        });
    }

    /**
     * Mostra um toast
     * @param {string} message - Mensagem a exibir
     * @param {string} type - Tipo do toast (success, error, warning, info)
     * @param {number} duration - Duração em ms (padrão: 5000)
     * @returns {string} ID do toast criado
     */
    show(message, type = 'info', duration = 5000) {
        if (!this.container || !this.template) {
            console.warn('Toast system não inicializado');
            return null;
        }

        // Cria um ID único para o toast
        const toastId = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        // Clona o template
        const toastElement = this.template.content.cloneNode(true).querySelector('.toast-feedback');
        toastElement.id = toastId;
        toastElement.classList.add(`toast-${type}`);

        // Define a mensagem
        const messageElement = toastElement.querySelector('.toast-text');
        messageElement.textContent = message;

        // Configura o botão de fechar
        const closeButton = toastElement.querySelector('.toast-close');
        closeButton.addEventListener('click', () => this.hide(toastId));

        // Adiciona ao container
        this.container.appendChild(toastElement);

        // Armazena referência
        this.toasts.set(toastId, {
            element: toastElement,
            timeout: null
        });

        // Configura auto-dismiss
        if (duration > 0) {
            const timeout = setTimeout(() => this.hide(toastId), duration);
            this.toasts.get(toastId).timeout = timeout;
        }

        // Adiciona listener para pausar no hover
        toastElement.addEventListener('mouseenter', () => this.pauseAutoDismiss(toastId));
        toastElement.addEventListener('mouseleave', () => this.resumeAutoDismiss(toastId, duration));

        return toastId;
    }

    /**
     * Esconde um toast
     * @param {string} toastId - ID do toast a esconder
     */
    hide(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        // Cancela o timeout se existir
        if (toast.timeout) {
            clearTimeout(toast.timeout);
        }

        // Adiciona classe de saída
        toast.element.classList.add('toast-exit');

        // Remove após a animação
        setTimeout(() => {
            if (toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            this.toasts.delete(toastId);
        }, 300); // Duração da animação
    }

    /**
     * Pausa o auto-dismiss de um toast
     * @param {string} toastId - ID do toast
     */
    pauseAutoDismiss(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast || !toast.timeout) return;

        clearTimeout(toast.timeout);
        toast.timeout = null;

        // Pausa a animação da barra de progresso
        const progressBar = toast.element.querySelector('.toast-progress::after');
        if (progressBar) {
            progressBar.style.animationPlayState = 'paused';
        }
    }

    /**
     * Resume o auto-dismiss de um toast
     * @param {string} toastId - ID do toast
     * @param {number} duration - Duração restante
     */
    resumeAutoDismiss(toastId, duration) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        // Resume com duração reduzida (2 segundos)
        const timeout = setTimeout(() => this.hide(toastId), 2000);
        toast.timeout = timeout;
    }

    /**
     * Esconde todos os toasts
     */
    hideAll() {
        this.toasts.forEach((_, toastId) => this.hide(toastId));
    }

    /**
     * Métodos de conveniência
     */
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// Cria instância global
const toastManager = new ToastManager();

// Expõe API global simplificada
window.showToast = (message, type, duration) => toastManager.show(message, type, duration);
window.toast = {
    success: (msg, duration) => toastManager.success(msg, duration),
    error: (msg, duration) => toastManager.error(msg, duration),
    warning: (msg, duration) => toastManager.warning(msg, duration),
    info: (msg, duration) => toastManager.info(msg, duration),
    hide: (id) => toastManager.hide(id),
    hideAll: () => toastManager.hideAll()
};

// Exporta para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastManager;
}
