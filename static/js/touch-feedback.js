/**
 * Touch Feedback System
 * Fornece feedback visual para interações touch em dispositivos móveis
 * 
 * Funcionalidades:
 * - Ripple effect em botões
 * - Prevenção de duplo clique
 * - Feedback visual imediato
 * - Integração automática com botões existentes
 */

class TouchFeedback {
    constructor(options = {}) {
        this.options = {
            rippleDuration: options.rippleDuration || 600,
            debounceTime: options.debounceTime || 300,
            rippleColor: options.rippleColor || 'rgba(255, 255, 255, 0.5)',
            ...options
        };
        
        this.processingButtons = new Set();
        this.init();
    }

    init() {
        // Adiciona ripple effect a todos os botões
        this.attachRippleEffect();
        
        // Previne duplo clique em botões de ação
        this.preventDoubleClick();
        
        // Adiciona feedback visual em elementos touch
        this.addTouchFeedback();
        
        console.log('Touch Feedback System inicializado');
    }

    /**
     * Adiciona efeito ripple a botões
     */
    attachRippleEffect() {
        const buttons = document.querySelectorAll('button, .btn, .touch-target, a.btn');
        
        buttons.forEach(button => {
            // Evita adicionar múltiplas vezes
            if (button.dataset.rippleAttached) return;
            
            button.dataset.rippleAttached = 'true';
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            
            button.addEventListener('click', (e) => {
                this.createRipple(e, button);
            });
        });
    }

    /**
     * Cria o efeito ripple
     */
    createRipple(event, element) {
        // Remove ripples antigos
        const oldRipples = element.querySelectorAll('.ripple');
        oldRipples.forEach(ripple => ripple.remove());
        
        const ripple = document.createElement('span');
        ripple.classList.add('ripple');
        
        // Calcula posição do clique
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.background = this.options.rippleColor;
        
        element.appendChild(ripple);
        
        // Remove ripple após animação
        setTimeout(() => {
            ripple.remove();
        }, this.options.rippleDuration);
    }

    /**
     * Previne duplo clique em botões de ação
     */
    preventDoubleClick() {
        const actionButtons = document.querySelectorAll(
            'button[type="submit"], .btn-primary, .btn-action, .btn-accept, .btn-reject'
        );
        
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Se já está processando, previne o clique
                if (this.processingButtons.has(button)) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
                
                // Marca como processando
                this.processingButtons.add(button);
                button.disabled = true;
                button.classList.add('processing');
                
                // Adiciona spinner se não tiver
                if (!button.querySelector('.spinner')) {
                    this.addSpinner(button);
                }
                
                // Remove após debounce time
                setTimeout(() => {
                    this.processingButtons.delete(button);
                    button.disabled = false;
                    button.classList.remove('processing');
                    this.removeSpinner(button);
                }, this.options.debounceTime);
            });
        });
    }

    /**
     * Adiciona spinner ao botão
     */
    addSpinner(button) {
        const spinner = document.createElement('span');
        spinner.classList.add('spinner', 'spinner-sm');
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const originalContent = button.innerHTML;
        button.dataset.originalContent = originalContent;
        button.innerHTML = '';
        button.appendChild(spinner);
    }

    /**
     * Remove spinner do botão
     */
    removeSpinner(button) {
        const spinner = button.querySelector('.spinner');
        if (spinner) {
            spinner.remove();
        }
        
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            delete button.dataset.originalContent;
        }
    }

    /**
     * Adiciona feedback visual em elementos touch
     */
    addTouchFeedback() {
        const touchElements = document.querySelectorAll(
            '.touch-target, .card, .list-item, a:not(.btn)'
        );
        
        touchElements.forEach(element => {
            // Evita adicionar múltiplas vezes
            if (element.dataset.touchFeedbackAttached) return;
            
            element.dataset.touchFeedbackAttached = 'true';
            
            element.addEventListener('touchstart', () => {
                element.classList.add('touch-active');
            });
            
            element.addEventListener('touchend', () => {
                setTimeout(() => {
                    element.classList.remove('touch-active');
                }, 150);
            });
            
            element.addEventListener('touchcancel', () => {
                element.classList.remove('touch-active');
            });
        });
    }

    /**
     * Reinicializa o sistema (útil para conteúdo dinâmico)
     */
    refresh() {
        this.attachRippleEffect();
        this.preventDoubleClick();
        this.addTouchFeedback();
    }

    /**
     * Reseta um botão específico (remove estado de processamento)
     */
    resetButton(button) {
        this.processingButtons.delete(button);
        button.disabled = false;
        button.classList.remove('processing');
        this.removeSpinner(button);
    }

    /**
     * Reseta todos os botões
     */
    resetAllButtons() {
        this.processingButtons.forEach(button => {
            this.resetButton(button);
        });
        this.processingButtons.clear();
    }
}

// CSS necessário para ripple effect
const rippleStyles = `
.ripple {
    position: absolute;
    border-radius: 50%;
    transform: scale(0);
    animation: ripple-animation 0.6s ease-out;
    pointer-events: none;
    z-index: 1;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.touch-active {
    opacity: 0.7;
    transform: scale(0.98);
    transition: all 0.15s ease;
}

button.processing,
.btn.processing {
    opacity: 0.6;
    cursor: not-allowed;
}

.spinner-sm {
    display: inline-block;
    width: 16px;
    height: 16px;
}
`;

// Injeta estilos no documento
function injectRippleStyles() {
    const styleId = 'touch-feedback-styles';
    
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = rippleStyles;
        document.head.appendChild(style);
    }
}

// Inicialização automática
let touchFeedbackInstance = null;

function initTouchFeedback(options = {}) {
    injectRippleStyles();
    touchFeedbackInstance = new TouchFeedback(options);
    return touchFeedbackInstance;
}

// Inicializa quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initTouchFeedback());
} else {
    initTouchFeedback();
}

// Exporta para uso global
window.TouchFeedback = TouchFeedback;
window.touchFeedback = touchFeedbackInstance;
window.initTouchFeedback = initTouchFeedback;
