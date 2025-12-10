/**
 * JavaScript para interações da página de convite
 * Implementa confirmações, estados de loading, validações e feedback visual
 */

class InviteInteractions {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidations();
        this.setupLoadingStates();
        this.setupConfirmations();
        this.setupVisualFeedback();
    }

    /**
     * Configura os event listeners principais
     */
    setupEventListeners() {
        // Botão de aceitar convite - REMOVIDO para evitar interferência
        // O formulário será processado nativamente pelo navegador
        // const acceptBtn = document.querySelector('.accept-btn');
        // if (acceptBtn) {
        //     acceptBtn.addEventListener('click', (e) => this.handleAcceptClick(e));
        // }

        // Botão de rejeitar convite
        const rejectBtn = document.querySelector('.reject-btn');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', (e) => this.handleRejectClick(e));
        }

        // Formulário de rejeição
        const rejectForm = document.getElementById('rejectForm');
        if (rejectForm) {
            rejectForm.addEventListener('submit', (e) => this.handleRejectSubmit(e));
        }

        // Botões de motivos rápidos
        const quickReasonButtons = document.querySelectorAll('.quick-reason');
        quickReasonButtons.forEach(button => {
            button.addEventListener('click', (e) => this.handleQuickReason(e));
        });

        // Formulários de login/cadastro
        const cadastroForm = document.getElementById('cadastroForm');
        const loginForm = document.getElementById('loginForm');
        
        if (cadastroForm) {
            cadastroForm.addEventListener('submit', (e) => this.handleCadastroSubmit(e));
        }
        
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLoginSubmit(e));
        }
    }

    /**
     * Configura validações do lado cliente
     */
    setupFormValidations() {
        // Validação de senhas
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm_password');
        
        if (passwordInput && confirmPasswordInput) {
            passwordInput.addEventListener('input', () => this.validatePasswords());
            confirmPasswordInput.addEventListener('input', () => this.validatePasswords());
        }

        // Máscara para CPF
        const cpfInput = document.getElementById('cpf');
        if (cpfInput) {
            cpfInput.addEventListener('input', (e) => this.applyCpfMask(e));
        }

        // Máscara para telefone
        const phoneInput = document.getElementById('phone');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => this.applyPhoneMask(e));
        }

        // Validação de email em tempo real
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', (e) => this.validateEmail(e));
        });
    }

    /**
     * Configura estados de loading nos botões
     */
    setupLoadingStates() {
        // Configurar todos os botões de submit para mostrar loading
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
        // Confirmação adicional para rejeição no modal
        const confirmRejectBtn = document.querySelector('.confirm-reject-btn');
        if (confirmRejectBtn) {
            confirmRejectBtn.addEventListener('click', (e) => {
                if (!this.confirmRejectAction()) {
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
     * Manipula clique no botão de aceitar
     */
    handleAcceptClick(e) {
        const button = e.target.closest('button');
        
        // Confirmação antes de aceitar
        if (!confirm('Tem certeza que deseja aceitar este convite?\n\nVocê será direcionado para fazer login ou criar sua conta.')) {
            e.preventDefault();
            return false;
        }

        // Aplicar estado de loading (sem interferir no submit)
        setTimeout(() => {
            this.setButtonLoading(button, true, 'Aceitar Convite', 'Processando...');
        }, 10);
        
        // Mostrar feedback visual
        this.showSuccessMessage('Convite aceito! Redirecionando...');
        
        // IMPORTANTE: Não interferir com o comportamento padrão do formulário
        // Deixar o navegador processar o submit normalmente
        return true;
    }

    /**
     * Manipula clique no botão de rejeitar
     */
    handleRejectClick(e) {
        const button = e.target.closest('button');
        
        // Aplicar estado de loading temporário
        this.setButtonLoading(button, true, 'Rejeitar Convite', 'Abrindo...');
        
        // Reabilitar após breve delay
        setTimeout(() => {
            this.setButtonLoading(button, false, 'Rejeitar Convite');
        }, 300);
    }

    /**
     * Manipula submissão do formulário de rejeição
     */
    handleRejectSubmit(e) {
        const form = e.target;
        const submitBtn = form.querySelector('.confirm-reject-btn');
        
        // Aplicar loading no botão
        if (submitBtn) {
            this.setButtonLoading(submitBtn, true, 'Confirmar Rejeição', 'Rejeitando...');
        }
        
        // Mostrar feedback
        this.showInfoMessage('Processando rejeição do convite...');
        
        return true;
    }

    /**
     * Manipula clique nos botões de motivo rápido
     */
    handleQuickReason(e) {
        const button = e.target.closest('button');
        const reason = button.getAttribute('data-reason');
        const textarea = document.getElementById('reject_reason');
        
        if (textarea && reason) {
            textarea.value = reason;
            textarea.focus();
            
            // Destacar visualmente o botão selecionado
            document.querySelectorAll('.quick-reason').forEach(btn => {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-secondary');
            });
            
            button.classList.remove('btn-outline-secondary');
            button.classList.add('btn-primary');
            
            // Feedback visual
            this.showSuccessMessage('Motivo selecionado!');
        }
    }

    /**
     * Manipula submissão do formulário de cadastro
     */
    handleCadastroSubmit(e) {
        const form = e.target;
        
        // Validações específicas do cadastro
        if (!this.validateCadastroForm(form)) {
            e.preventDefault();
            return false;
        }
        
        // Confirmação final
        if (!confirm('Deseja criar sua conta e visualizar o convite?')) {
            e.preventDefault();
            return false;
        }
        
        // Aplicar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            this.setButtonLoading(submitBtn, true, 'Criar Conta e Ver Convite', 'Criando conta...');
        }
        
        return true;
    }

    /**
     * Manipula submissão do formulário de login
     */
    handleLoginSubmit(e) {
        const form = e.target;
        
        // Validações básicas
        const password = form.querySelector('#login_password');
        if (!password || !password.value.trim()) {
            e.preventDefault();
            this.showErrorMessage('Digite sua senha para fazer login!');
            if (password) password.focus();
            return false;
        }
        
        // Aplicar loading
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            this.setButtonLoading(submitBtn, true, 'Entrar e Ver Convite', 'Fazendo login...');
        }
        
        return true;
    }

    /**
     * Valida formulário de cadastro
     */
    validateCadastroForm(form) {
        const password = form.querySelector('#password');
        const confirmPassword = form.querySelector('#confirm_password');
        const terms = form.querySelector('#terms');
        const nome = form.querySelector('#nome');
        const email = form.querySelector('#email');
        const cpf = form.querySelector('#cpf');
        
        // Validar nome
        if (!nome || !nome.value.trim()) {
            this.showErrorMessage('Nome completo é obrigatório!');
            if (nome) nome.focus();
            return false;
        }
        
        // Validar email
        if (!email || !this.isValidEmail(email.value)) {
            this.showErrorMessage('Digite um email válido!');
            if (email) email.focus();
            return false;
        }
        
        // Validar CPF
        if (!cpf || !this.isValidCPF(cpf.value)) {
            this.showErrorMessage('Digite um CPF válido!');
            if (cpf) cpf.focus();
            return false;
        }
        
        // Validar senhas
        if (!password || password.value.length < 6) {
            this.showErrorMessage('A senha deve ter pelo menos 6 caracteres!');
            if (password) password.focus();
            return false;
        }
        
        if (!confirmPassword || password.value !== confirmPassword.value) {
            this.showErrorMessage('As senhas não coincidem!');
            if (confirmPassword) confirmPassword.focus();
            return false;
        }
        
        // Validar termos
        if (!terms || !terms.checked) {
            this.showErrorMessage('Você deve aceitar os termos de uso!');
            if (terms) terms.focus();
            return false;
        }
        
        return true;
    }

    /**
     * Valida senhas em tempo real
     */
    validatePasswords() {
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (password && confirmPassword) {
            if (password.value !== confirmPassword.value) {
                confirmPassword.setCustomValidity('As senhas não coincidem');
                this.addFieldError(confirmPassword, 'As senhas não coincidem');
            } else {
                confirmPassword.setCustomValidity('');
                this.removeFieldError(confirmPassword);
            }
        }
    }

    /**
     * Aplica máscara de CPF
     */
    applyCpfMask(e) {
        let value = e.target.value.replace(/\D/g, '');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        e.target.value = value;
        
        // Validar CPF em tempo real
        if (value.length === 14) {
            if (this.isValidCPF(value)) {
                this.addFieldSuccess(e.target);
            } else {
                this.addFieldError(e.target, 'CPF inválido');
            }
        }
    }

    /**
     * Aplica máscara de telefone
     */
    applyPhoneMask(e) {
        let value = e.target.value.replace(/\D/g, '');
        value = value.replace(/(\d{2})(\d)/, '($1) $2');
        value = value.replace(/(\d{5})(\d)/, '$1-$2');
        e.target.value = value;
    }

    /**
     * Valida email
     */
    validateEmail(e) {
        const email = e.target.value;
        if (email && !this.isValidEmail(email)) {
            this.addFieldError(e.target, 'Email inválido');
        } else if (email) {
            this.addFieldSuccess(e.target);
        }
    }

    /**
     * Confirma ação de rejeição
     */
    confirmRejectAction() {
        const reason = document.getElementById('reject_reason');
        const reasonText = reason ? reason.value.trim() : '';
        
        let message = 'Tem certeza que deseja rejeitar este convite?\n\n';
        message += 'Esta ação não pode ser desfeita e o cliente será notificado.';
        
        if (reasonText) {
            message += '\n\nMotivo informado: ' + reasonText;
        }
        
        return confirm(message);
    }

    /**
     * Define estado de loading em botão
     */
    setButtonLoading(button, isLoading, originalText = '', loadingText = 'Carregando...') {
        if (!button) return;
        
        const icon = button.querySelector('i');
        const textSpan = button.querySelector('.btn-text') || button;
        
        if (isLoading) {
            button.disabled = true;
            button.classList.add('loading');
            
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin me-2';
            }
            
            if (textSpan && loadingText) {
                textSpan.textContent = loadingText;
            }
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            
            if (icon) {
                // Restaurar ícone original baseado no tipo de botão
                if (button.classList.contains('accept-btn')) {
                    icon.className = 'fas fa-check me-2';
                } else if (button.classList.contains('reject-btn')) {
                    icon.className = 'fas fa-times me-2';
                } else {
                    icon.className = 'fas fa-check me-2';
                }
            }
            
            if (textSpan && originalText) {
                textSpan.textContent = originalText;
            }
        }
    }

    /**
     * Adiciona efeito de foco
     */
    addFocusEffect(element) {
        element.classList.add('focused');
        const parent = element.closest('.form-group, .mb-3');
        if (parent) {
            parent.classList.add('focused');
        }
    }

    /**
     * Remove efeito de foco
     */
    removeFocusEffect(element) {
        element.classList.remove('focused');
        const parent = element.closest('.form-group, .mb-3');
        if (parent) {
            parent.classList.remove('focused');
        }
    }

    /**
     * Atualiza status do campo
     */
    updateFieldStatus(element) {
        if (element.value.trim()) {
            element.classList.add('has-value');
        } else {
            element.classList.remove('has-value');
        }
    }

    /**
     * Adiciona efeito hover
     */
    addHoverEffect(element) {
        if (!element.disabled) {
            element.classList.add('hover-effect');
        }
    }

    /**
     * Remove efeito hover
     */
    removeHoverEffect(element) {
        element.classList.remove('hover-effect');
    }

    /**
     * Adiciona erro ao campo
     */
    addFieldError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        // Remover mensagem de erro anterior
        this.removeFieldFeedback(field);
        
        // Adicionar nova mensagem de erro
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    }

    /**
     * Adiciona sucesso ao campo
     */
    addFieldSuccess(field) {
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        this.removeFieldFeedback(field);
    }

    /**
     * Remove erro do campo
     */
    removeFieldError(field) {
        field.classList.remove('is-invalid');
        this.removeFieldFeedback(field);
    }

    /**
     * Remove feedback do campo
     */
    removeFieldFeedback(field) {
        const feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    /**
     * Mostra mensagem de sucesso
     */
    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    /**
     * Mostra mensagem de erro
     */
    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    /**
     * Mostra mensagem de informação
     */
    showInfoMessage(message) {
        this.showToast(message, 'info');
    }

    /**
     * Mostra toast notification
     */
    showToast(message, type = 'info') {
        // Criar container de toasts se não existir
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Criar toast
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${this.getBootstrapColor(type)} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${this.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Mostrar toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: type === 'error' ? 5000 : 3000
        });
        bsToast.show();

        // Remover toast após esconder
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    /**
     * Obtém cor do Bootstrap para tipo de mensagem
     */
    getBootstrapColor(type) {
        const colors = {
            'success': 'success',
            'error': 'danger',
            'info': 'info',
            'warning': 'warning'
        };
        return colors[type] || 'info';
    }

    /**
     * Obtém ícone para tipo de toast
     */
    getToastIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle'
        };
        return icons[type] || 'fa-info-circle';
    }

    /**
     * Valida formato de email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Valida CPF
     */
    isValidCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        
        if (cpf.length !== 11) return false;
        if (/^(\d)\1{10}$/.test(cpf)) return false;
        
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(cpf.charAt(i)) * (10 - i);
        }
        let remainder = (sum * 10) % 11;
        if (remainder === 10 || remainder === 11) remainder = 0;
        if (remainder !== parseInt(cpf.charAt(9))) return false;
        
        sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += parseInt(cpf.charAt(i)) * (11 - i);
        }
        remainder = (sum * 10) % 11;
        if (remainder === 10 || remainder === 11) remainder = 0;
        if (remainder !== parseInt(cpf.charAt(10))) return false;
        
        return true;
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.inviteInteractions = new InviteInteractions();
});