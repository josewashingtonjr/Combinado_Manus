/**
 * JavaScript para interações dinâmicas do sistema de pré-ordens
 * Implementa validações, feedback visual, confirmações e máscaras de input
 */

class PreOrdemInteractions {
    constructor() {
        this.currentPreOrderId = null;
        this.originalValue = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidations();
        this.setupLoadingStates();
        this.setupConfirmations();
        this.setupVisualFeedback();
        this.setupMasks();
        this.initializePreOrderData();
    }

    /**
     * Configura os event listeners principais
     */
    setupEventListeners() {
        // Formulário de proposta de alteração
        const proposeForm = document.getElementById('proposeAlteracaoForm');
        if (proposeForm) {
            proposeForm.addEventListener('submit', (e) => this.handleProposeAlteracao(e));
        }

        // Botão de aceitar termos
        const acceptTermsBtn = document.getElementById('btn-aceitar-termos');
        if (acceptTermsBtn) {
            acceptTermsBtn.addEventListener('click', (e) => this.handleAcceptTerms(e));
        }

        // Formulário de cancelamento
        const cancelForm = document.getElementById('cancelPreOrderForm');
        if (cancelForm) {
            cancelForm.addEventListener('submit', (e) => this.handleCancelPreOrder(e));
        }

        // Campo de valor proposto - cálculo de diferença
        const proposedValueInput = document.getElementById('proposed_value');
        if (proposedValueInput) {
            proposedValueInput.addEventListener('input', (e) => this.calculateValueDifference(e));
            proposedValueInput.addEventListener('blur', (e) => this.validateProposedValue(e));
        }

        // Campo de data de entrega proposta
        const proposedDateInput = document.getElementById('proposed_delivery_date');
        if (proposedDateInput) {
            proposedDateInput.addEventListener('blur', (e) => this.validateProposedDate(e));
        }

        // Campo de justificativa
        const justificationInput = document.getElementById('justification');
        if (justificationInput) {
            justificationInput.addEventListener('input', (e) => this.updateCharacterCount(e));
            justificationInput.addEventListener('blur', (e) => this.validateJustification(e));
        }

        // Botões de aceitar/rejeitar proposta
        const acceptProposalBtn = document.getElementById('btn-aceitar-proposta');
        if (acceptProposalBtn) {
            acceptProposalBtn.addEventListener('click', (e) => this.handleAcceptProposal(e));
        }

        const rejectProposalBtn = document.getElementById('btn-rejeitar-proposta');
        if (rejectProposalBtn) {
            rejectProposalBtn.addEventListener('click', (e) => this.handleRejectProposal(e));
        }
    }

    /**
     * Configura validações do lado cliente
     */
    setupFormValidations() {
        // Validação de valor proposto
        const proposedValueInput = document.getElementById('proposed_value');
        if (proposedValueInput) {
            proposedValueInput.addEventListener('input', (e) => {
                // Permitir apenas números e ponto decimal
                let value = e.target.value.replace(/[^\d.,]/g, '');
                value = value.replace(',', '.');
                e.target.value = value;
            });
        }

        // Validação de data
        const proposedDateInput = document.getElementById('proposed_delivery_date');
        if (proposedDateInput) {
            // Definir data mínima como hoje
            const today = new Date().toISOString().split('T')[0];
            proposedDateInput.setAttribute('min', today);
        }
    }

    /**
     * Configura estados de loading nos botões
     */
    setupLoadingStates() {
        const submitButtons = document.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(button => {
            const form = button.closest('form');
            if (form) {
                form.addEventListener('submit', () => {
                    this.setButtonLoading(button, true);
                });
            }
        });
    }

    /**
     * Configura confirmações para ações críticas
     */
    setupConfirmations() {
        // Confirmação para aceitar termos
        const acceptTermsBtn = document.getElementById('btn-aceitar-termos');
        if (acceptTermsBtn) {
            acceptTermsBtn.addEventListener('click', (e) => {
                if (!this.confirmAcceptTerms()) {
                    e.preventDefault();
                    return false;
                }
            });
        }

        // Confirmação para cancelar pré-ordem
        const cancelBtn = document.querySelector('.btn-cancel-pre-order');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                if (!this.confirmCancelPreOrder()) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    }

    /**
     * Configura feedback visual para ações do usuário
     */
    setupVisualFeedback() {
        // Feedback visual para campos de formulário
        const formInputs = document.querySelectorAll('input, textarea, select');
        formInputs.forEach(input => {
            input.addEventListener('focus', (e) => this.addFocusEffect(e.target));
            input.addEventListener('blur', (e) => this.removeFocusEffect(e.target));
            input.addEventListener('input', (e) => this.updateFieldStatus(e.target));
        });

        // Animações para botões
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', (e) => this.addHoverEffect(e.target));
            button.addEventListener('mouseleave', (e) => this.removeHoverEffect(e.target));
        });
    }

    /**
     * Configura máscaras de input
     */
    setupMasks() {
        // Máscara para valores monetários
        const moneyInputs = document.querySelectorAll('input[data-mask="money"]');
        moneyInputs.forEach(input => {
            input.addEventListener('input', (e) => this.applyMoneyMask(e));
            input.addEventListener('blur', (e) => this.formatMoneyValue(e));
        });

        // Máscara para datas já é nativa do input type="date"
    }

    /**
     * Inicializa dados da pré-ordem
     */
    initializePreOrderData() {
        // Obter ID da pré-ordem
        const preOrderElement = document.querySelector('[data-pre-order-id]');
        if (preOrderElement) {
            this.currentPreOrderId = preOrderElement.getAttribute('data-pre-order-id');
        }

        // Obter valor original
        const originalValueElement = document.querySelector('[data-original-value]');
        if (originalValueElement) {
            this.originalValue = parseFloat(originalValueElement.getAttribute('data-original-value'));
        }

        // Inicializar contador de caracteres
        const justificationInput = document.getElementById('justification');
        if (justificationInput) {
            this.updateCharacterCount({ target: justificationInput });
        }
    }

    /**
     * Manipula submissão do formulário de proposta de alteração
     */
    async handleProposeAlteracao(e) {
        const form = e.target;
        
        // Validar formulário
        if (!this.validateProposeForm(form)) {
            e.preventDefault();
            return false;
        }

        // Confirmação final
        if (!this.confirmProposeAlteracao(form)) {
            e.preventDefault();
            return false;
        }

        // Aplicar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            this.setButtonLoading(submitBtn, true, 'Enviar Proposta', 'Enviando...');
        }

        // Mostrar feedback
        this.showNotification('📤 Enviando proposta de alteração...', 'info');
        
        return true;
    }

    /**
     * Manipula clique no botão de aceitar termos
     */
    async handleAcceptTerms(e) {
        e.preventDefault();
        
        const button = e.target.closest('button');
        const preOrderId = this.currentPreOrderId;
        
        if (!preOrderId) {
            this.showNotification('❌ Erro: ID da pré-ordem não encontrado', 'error');
            return;
        }

        this.setButtonLoading(button, true, 'Aceitar Termos', 'Processando...');

        try {
            const response = await fetch(`/pre-ordem/${preOrderId}/aceitar-termos`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ ' + data.message, 'success');
                
                // Atualizar saldo disponível na interface
                if (data.new_balance !== undefined) {
                    this.updateBalanceDisplay(data.new_balance);
                }
                
                // Recarregar página após breve delay
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error(data.message || 'Erro ao aceitar termos');
            }
        } catch (error) {
            console.error('Erro ao aceitar termos:', error);
            this.showNotification('❌ ' + error.message, 'error');
            this.setButtonLoading(button, false, 'Aceitar Termos');
        }
    }

    /**
     * Manipula submissão do formulário de cancelamento
     */
    async handleCancelPreOrder(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.setButtonLoading(submitBtn, true, 'Confirmar Cancelamento', 'Cancelando...');
        this.showNotification('🔄 Cancelando pré-ordem...', 'info');
        
        return true;
    }

    /**
     * Manipula aceitação de proposta
     */
    async handleAcceptProposal(e) {
        e.preventDefault();
        
        const button = e.target.closest('button');
        const proposalId = button.getAttribute('data-proposal-id');
        
        if (!proposalId) {
            this.showNotification('❌ Erro: ID da proposta não encontrado', 'error');
            return;
        }

        if (!confirm('Tem certeza que deseja aceitar esta proposta?\n\nOs novos termos serão aplicados à pré-ordem.')) {
            return;
        }

        this.setButtonLoading(button, true, 'Aceitar Proposta', 'Processando...');

        try {
            const response = await fetch(`/pre-ordem/${this.currentPreOrderId}/aceitar-proposta/${proposalId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ ' + data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error(data.message || 'Erro ao aceitar proposta');
            }
        } catch (error) {
            console.error('Erro ao aceitar proposta:', error);
            this.showNotification('❌ ' + error.message, 'error');
            this.setButtonLoading(button, false, 'Aceitar Proposta');
        }
    }

    /**
     * Manipula rejeição de proposta
     */
    async handleRejectProposal(e) {
        e.preventDefault();
        
        const button = e.target.closest('button');
        const proposalId = button.getAttribute('data-proposal-id');
        
        if (!proposalId) {
            this.showNotification('❌ Erro: ID da proposta não encontrado', 'error');
            return;
        }

        if (!confirm('Tem certeza que deseja rejeitar esta proposta?\n\nA pré-ordem retornará aos termos anteriores.')) {
            return;
        }

        this.setButtonLoading(button, true, 'Rejeitar Proposta', 'Processando...');

        try {
            const response = await fetch(`/pre-ordem/${this.currentPreOrderId}/rejeitar-proposta/${proposalId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ ' + data.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error(data.message || 'Erro ao rejeitar proposta');
            }
        } catch (error) {
            console.error('Erro ao rejeitar proposta:', error);
            this.showNotification('❌ ' + error.message, 'error');
            this.setButtonLoading(button, false, 'Rejeitar Proposta');
        }
    }

    /**
     * Calcula e exibe diferença percentual ao alterar valor
     */
    calculateValueDifference(e) {
        const input = e.target;
        const proposedValue = parseFloat(input.value) || 0;
        const originalValue = this.originalValue || parseFloat(input.getAttribute('data-original-value')) || 0;
        
        const differenceDiv = document.getElementById('value-difference');
        const differenceText = document.getElementById('difference-text');
        const differencePercentage = document.getElementById('difference-percentage');

        if (proposedValue > 0 && originalValue > 0 && proposedValue !== originalValue) {
            const difference = proposedValue - originalValue;
            const percentage = ((difference / originalValue) * 100).toFixed(2);
            
            differenceDiv.style.display = 'block';
            
            if (difference > 0) {
                // Aumento
                differenceDiv.className = 'alert alert-warning mt-2';
                differenceText.innerHTML = `<i class="fas fa-arrow-up me-1"></i>Aumento de ${this.formatCurrency(difference)}`;
                differencePercentage.textContent = `(+${percentage}%)`;
                
                // Alerta para aumentos extremos
                if (percentage > 100) {
                    this.showWarning('⚠️ Aumento muito alto! Forneça uma justificativa detalhada.');
                }
            } else {
                // Redução
                differenceDiv.className = 'alert alert-info mt-2';
                differenceText.innerHTML = `<i class="fas fa-arrow-down me-1"></i>Redução de ${this.formatCurrency(Math.abs(difference))}`;
                differencePercentage.textContent = `(${percentage}%)`;
                
                // Alerta para reduções extremas
                if (Math.abs(percentage) > 50) {
                    this.showWarning('⚠️ Redução muito alta! Forneça uma justificativa detalhada.');
                }
            }
        } else {
            differenceDiv.style.display = 'none';
        }
    }

    /**
     * Atualiza contador de caracteres da justificativa
     */
    updateCharacterCount(e) {
        const input = e.target;
        const currentLength = input.value.length;
        const maxLength = parseInt(input.getAttribute('maxlength')) || 500;
        const minLength = 50;
        
        const counterElement = document.getElementById('character-count');
        if (counterElement) {
            counterElement.textContent = `${currentLength}/${maxLength} caracteres`;
            
            if (currentLength < minLength) {
                counterElement.className = 'form-text text-danger';
                counterElement.textContent += ` (mínimo ${minLength})`;
            } else {
                counterElement.className = 'form-text text-muted';
            }
        }
    }

    /**
     * Atualiza exibição do saldo disponível
     */
    updateBalanceDisplay(newBalance) {
        const balanceElements = document.querySelectorAll('[data-balance-display]');
        balanceElements.forEach(element => {
            element.textContent = this.formatCurrency(newBalance);
            
            // Adicionar animação de atualização
            element.classList.add('balance-updated');
            setTimeout(() => {
                element.classList.remove('balance-updated');
            }, 1000);
        });
    }

    /**
     * Validações de formulário
     */
    validateProposeForm(form) {
        const proposedValue = parseFloat(document.getElementById('proposed_value')?.value);
        const proposedDate = document.getElementById('proposed_delivery_date')?.value;
        const proposedDescription = document.getElementById('proposed_description')?.value?.trim();
        const justification = document.getElementById('justification')?.value?.trim();
        
        // Verificar se pelo menos um campo foi alterado
        const hasChanges = proposedValue || proposedDate || proposedDescription;
        if (!hasChanges) {
            this.showNotification('❌ Você deve alterar pelo menos um campo (valor, prazo ou descrição)', 'error');
            return false;
        }

        // Validar valor se fornecido
        if (proposedValue !== undefined && proposedValue !== null && proposedValue !== '') {
            if (proposedValue <= 0) {
                this.showNotification('❌ O valor proposto deve ser maior que zero', 'error');
                return false;
            }
            
            if (proposedValue > 50000) {
                this.showNotification('❌ O valor proposto é muito alto (máximo R$ 50.000)', 'error');
                return false;
            }
            
            if (this.originalValue && proposedValue === this.originalValue) {
                this.showNotification('❌ O valor proposto deve ser diferente do valor atual', 'error');
                return false;
            }
        }

        // Validar data se fornecida
        if (proposedDate) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selectedDate = new Date(proposedDate);
            
            if (selectedDate < today) {
                this.showNotification('❌ A data de entrega deve ser futura', 'error');
                return false;
            }
        }

        // Validar justificativa
        if (!justification || justification.length < 50) {
            this.showNotification('❌ A justificativa deve ter pelo menos 50 caracteres', 'error');
            document.getElementById('justification')?.focus();
            return false;
        }

        if (justification.length > 500) {
            this.showNotification('❌ A justificativa deve ter no máximo 500 caracteres', 'error');
            return false;
        }

        return true;
    }

    validateProposedValue(e) {
        const input = e.target;
        const value = parseFloat(input.value);
        
        if (input.value && value <= 0) {
            this.addFieldError(input, 'Valor deve ser maior que zero');
            return false;
        }
        
        if (value > 50000) {
            this.addFieldError(input, 'Valor muito alto (máximo R$ 50.000)');
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    validateProposedDate(e) {
        const input = e.target;
        const selectedDate = new Date(input.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (input.value && selectedDate < today) {
            this.addFieldError(input, 'A data deve ser futura');
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    validateJustification(e) {
        const input = e.target;
        const value = input.value.trim();
        
        if (value.length > 0 && value.length < 50) {
            this.addFieldError(input, 'Justificativa muito curta (mínimo 50 caracteres)');
            return false;
        }
        
        if (value.length > 500) {
            this.addFieldError(input, 'Justificativa muito longa (máximo 500 caracteres)');
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    /**
     * Confirmações para ações críticas
     */
    confirmProposeAlteracao(form) {
        const proposedValue = parseFloat(document.getElementById('proposed_value')?.value);
        const originalValue = this.originalValue;
        
        let message = 'Tem certeza que deseja enviar esta proposta de alteração?\n\n';
        
        if (proposedValue && originalValue) {
            const difference = proposedValue - originalValue;
            if (difference > 0) {
                message += `Você está propondo um AUMENTO de ${this.formatCurrency(difference)}.\n\n`;
            } else if (difference < 0) {
                message += `Você está propondo uma REDUÇÃO de ${this.formatCurrency(Math.abs(difference))}.\n\n`;
            }
        }
        
        message += 'A outra parte será notificada e poderá aceitar ou rejeitar sua proposta.';
        
        return confirm(message);
    }

    confirmAcceptTerms() {
        return confirm(
            'Tem certeza que deseja aceitar os termos atuais?\n\n' +
            'Ao aceitar, você confirma que concorda com o valor, prazo e descrição da pré-ordem.\n\n' +
            'Quando ambas as partes aceitarem, a pré-ordem será convertida em uma ordem definitiva e os valores serão bloqueados.'
        );
    }

    confirmCancelPreOrder() {
        const reason = document.getElementById('cancellation_reason')?.value?.trim();
        
        let message = 'Tem certeza que deseja cancelar esta pré-ordem?\n\n';
        message += 'Esta ação não pode ser desfeita e a outra parte será notificada.';
        
        if (reason) {
            message += '\n\nMotivo informado: ' + reason;
        }
        
        return confirm(message);
    }

    /**
     * Máscaras de input
     */
    applyMoneyMask(e) {
        let value = e.target.value;
        
        // Remover tudo exceto números e ponto
        value = value.replace(/[^\d.]/g, '');
        
        // Permitir apenas um ponto decimal
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        
        // Limitar casas decimais a 2
        if (parts.length === 2 && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        
        e.target.value = value;
    }

    formatMoneyValue(e) {
        const input = e.target;
        const value = parseFloat(input.value);
        
        if (!isNaN(value) && value > 0) {
            input.value = value.toFixed(2);
        }
    }

    /**
     * Estados de loading e feedback visual
     */
    setButtonLoading(button, isLoading, originalText = '', loadingText = 'Carregando...') {
        if (!button) return;

        const icon = button.querySelector('i');
        const textSpan = button.querySelector('.btn-text') || button;

        if (isLoading) {
            button.disabled = true;
            button.classList.add('loading');
            button.setAttribute('data-original-html', button.innerHTML);
            
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin me-2';
            }
            
            if (loadingText) {
                if (icon) {
                    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
                } else {
                    button.textContent = loadingText;
                }
            }
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            
            const originalHtml = button.getAttribute('data-original-html');
            if (originalHtml) {
                button.innerHTML = originalHtml;
                button.removeAttribute('data-original-html');
            } else if (originalText) {
                button.textContent = originalText;
            }
        }
    }

    addFocusEffect(element) {
        element.classList.add('focused');
        const parent = element.closest('.form-group, .mb-3');
        if (parent) {
            parent.classList.add('focused');
        }
    }

    removeFocusEffect(element) {
        element.classList.remove('focused');
        const parent = element.closest('.form-group, .mb-3');
        if (parent) {
            parent.classList.remove('focused');
        }
    }

    updateFieldStatus(element) {
        if (element.value.trim()) {
            element.classList.add('has-value');
        } else {
            element.classList.remove('has-value');
        }
    }

    addHoverEffect(element) {
        if (!element.disabled) {
            element.classList.add('hover-effect');
        }
    }

    removeHoverEffect(element) {
        element.classList.remove('hover-effect');
    }

    addFieldError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        this.removeFieldFeedback(field);
        
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    }

    addFieldSuccess(field) {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        this.removeFieldFeedback(field);
    }

    removeFieldError(field) {
        field.classList.remove('is-invalid');
        this.removeFieldFeedback(field);
    }

    removeFieldFeedback(field) {
        const feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    /**
     * Sistema de notificações
     */
    showNotification(message, type = 'info') {
        // Criar container de notificações se não existir
        let notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            notificationContainer.className = 'notification-container position-fixed top-0 end-0 p-3';
            notificationContainer.style.zIndex = '9999';
            document.body.appendChild(notificationContainer);
        }

        // Criar notificação
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${this.getBootstrapColor(type)} alert-dismissible fade show`;
        notification.setAttribute('role', 'alert');
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas ${this.getNotificationIcon(type)} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            </div>
        `;

        notificationContainer.appendChild(notification);

        // Auto-remover após delay
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }
        }, type === 'error' ? 8000 : 5000);
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showInfo(message) {
        this.showNotification(message, 'info');
    }

    getBootstrapColor(type) {
        const colors = {
            'success': 'success',
            'error': 'danger',
            'info': 'info',
            'warning': 'warning'
        };
        return colors[type] || 'info';
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle'
        };
        return icons[type] || 'fa-info-circle';
    }

    /**
     * Utilitários
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Fallback: tentar obter de cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return value;
            }
        }
        
        return '';
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.preOrdemInteractions = new PreOrdemInteractions();
});
