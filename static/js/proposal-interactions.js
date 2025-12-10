/**
 * JavaScript para interações dinâmicas do sistema de propostas
 * Implementa atualizações em tempo real, validações, feedback visual e confirmações
 */

class ProposalInteractions {
    constructor() {
        this.currentProposalId = null;
        this.balanceCheckData = null;
        this.updateInterval = null;
        this.isUpdating = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupRealTimeUpdates();
        this.setupFormValidations();
        this.setupLoadingStates();
        this.setupConfirmations();
        this.setupVisualFeedback();
        this.initializeProposalData();
    }

    /**
     * Configura os event listeners principais
     */
    setupEventListeners() {
        // Botão de aceitar proposta
        const acceptButton = document.getElementById('btn-aceitar-proposta');
        if (acceptButton) {
            this.currentProposalId = acceptButton.getAttribute('data-proposal-id');
            acceptButton.addEventListener('click', (e) => this.handleAcceptProposal(e));
        }

        // Formulário de rejeição de proposta
        const rejectForm = document.getElementById('reject-proposal-form');
        if (rejectForm) {
            rejectForm.addEventListener('submit', (e) => this.handleRejectProposal(e));
        }

        // Formulário de criação de proposta (prestador)
        const proposeForm = document.querySelector('#proposeModal form');
        if (proposeForm) {
            proposeForm.addEventListener('submit', (e) => this.handleCreateProposal(e));
        }

        // Formulário de cancelamento de proposta
        const cancelForm = document.querySelector('#cancelProposalModal form');
        if (cancelForm) {
            cancelForm.addEventListener('submit', (e) => this.handleCancelProposal(e));
        }

        // Formulário de adição de saldo integrado
        const addBalanceForm = document.getElementById('addBalanceForm');
        if (addBalanceForm) {
            addBalanceForm.addEventListener('submit', (e) => this.handleAddBalanceAndApprove(e));
        }

        // Campo de valor proposto (prestador)
        const proposedValueInput = document.getElementById('proposed_value');
        if (proposedValueInput) {
            proposedValueInput.addEventListener('input', (e) => this.calculateValueDifference(e));
        }

        // Campo de valor a adicionar (cliente)
        const amountInput = document.getElementById('amount_to_add');
        if (amountInput) {
            amountInput.addEventListener('input', (e) => this.handleAmountChange(e));
        }

        // Botões de valores pré-definidos
        document.addEventListener('click', (e) => {
            if (e.target.closest('#predefined-amounts .btn')) {
                this.handlePredefinedAmount(e);
            }
        });
    }

    /**
     * Configura atualizações em tempo real
     */
    setupRealTimeUpdates() {
        // Verificar se há proposta pendente para monitorar
        const statusElement = document.querySelector('[data-proposal-status]');
        if (statusElement) {
            const status = statusElement.getAttribute('data-proposal-status');
            
            if (status === 'proposta_enviada' || status === 'proposta_aceita') {
                this.startRealTimeUpdates();
            }
        }

        // Parar atualizações quando a página não está visível
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopRealTimeUpdates();
            } else {
                this.resumeRealTimeUpdates();
            }
        });

        // Parar atualizações quando há modal aberto
        document.addEventListener('shown.bs.modal', () => {
            this.pauseUpdates();
        });

        document.addEventListener('hidden.bs.modal', () => {
            this.resumeUpdates();
        });
    }

    /**
     * Configura validações do lado cliente
     */
    setupFormValidations() {
        // Validação de valor proposto
        const proposedValueInput = document.getElementById('proposed_value');
        if (proposedValueInput) {
            proposedValueInput.addEventListener('blur', (e) => this.validateProposedValue(e));
        }

        // Validação de justificativa
        const justificationInput = document.getElementById('justification');
        if (justificationInput) {
            justificationInput.addEventListener('input', (e) => this.validateJustification(e));
        }

        // Validação de valor a adicionar
        const amountInput = document.getElementById('amount_to_add');
        if (amountInput) {
            amountInput.addEventListener('blur', (e) => this.validateAddAmount(e));
        }

        // Validação de motivo de rejeição
        const rejectionReasonInput = document.getElementById('rejection-reason');
        if (rejectionReasonInput) {
            rejectionReasonInput.addEventListener('input', (e) => this.validateRejectionReason(e));
        }
    }

    /**
     * Configura estados de loading
     */
    setupLoadingStates() {
        // Configurar todos os botões de ação para mostrar loading
        const actionButtons = document.querySelectorAll(
            '#btn-aceitar-proposta, .btn-reject-proposal, .btn-create-proposal, .btn-cancel-proposal'
        );
        
        actionButtons.forEach(button => {
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
        // Confirmação para aceitar proposta
        const acceptButton = document.getElementById('btn-aceitar-proposta');
        if (acceptButton) {
            acceptButton.addEventListener('click', (e) => {
                if (!this.confirmAcceptProposal()) {
                    e.preventDefault();
                    return false;
                }
            });
        }

        // Confirmação para rejeitar proposta
        const rejectButton = document.querySelector('.btn-reject-proposal');
        if (rejectButton) {
            rejectButton.addEventListener('click', (e) => {
                if (!this.confirmRejectProposal()) {
                    e.preventDefault();
                    return false;
                }
            });
        }
    }

    /**
     * Configura feedback visual
     */
    setupVisualFeedback() {
        // Feedback para campos de formulário
        const formInputs = document.querySelectorAll(
            '#proposed_value, #justification, #amount_to_add, #rejection-reason'
        );
        
        formInputs.forEach(input => {
            input.addEventListener('focus', (e) => this.addFocusEffect(e.target));
            input.addEventListener('blur', (e) => this.removeFocusEffect(e.target));
            input.addEventListener('input', (e) => this.updateFieldStatus(e.target));
        });

        // Animações para botões de ação
        const actionButtons = document.querySelectorAll('.btn-primary, .btn-success, .btn-warning, .btn-danger');
        actionButtons.forEach(button => {
            button.addEventListener('mouseenter', (e) => this.addHoverEffect(e.target));
            button.addEventListener('mouseleave', (e) => this.removeHoverEffect(e.target));
        });
    }

    /**
     * Inicializa dados da proposta
     */
    initializeProposalData() {
        // Verificar saldo se há proposta de aumento pendente
        const acceptButton = document.getElementById('btn-aceitar-proposta');
        if (acceptButton && acceptButton.disabled && this.currentProposalId) {
            this.checkProposalBalance(this.currentProposalId);
        }

        // Configurar formulário de rejeição
        const rejectForm = document.getElementById('reject-proposal-form');
        if (rejectForm && this.currentProposalId) {
            rejectForm.action = `/proposta/${this.currentProposalId}/rejeitar`;
        }
    }

    /**
     * Inicia atualizações em tempo real
     */
    startRealTimeUpdates() {
        if (this.updateInterval) return;
        
        this.updateInterval = setInterval(() => {
            if (!this.isUpdating && !document.hidden && !document.querySelector('.modal.show')) {
                this.checkForUpdates();
            }
        }, 15000); // Verificar a cada 15 segundos
    }

    /**
     * Para atualizações em tempo real
     */
    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Resume atualizações em tempo real
     */
    resumeRealTimeUpdates() {
        const statusElement = document.querySelector('[data-proposal-status]');
        if (statusElement) {
            const status = statusElement.getAttribute('data-proposal-status');
            if (status === 'proposta_enviada' || status === 'proposta_aceita') {
                this.startRealTimeUpdates();
            }
        }
    }

    /**
     * Pausa atualizações temporariamente
     */
    pauseUpdates() {
        this.isUpdating = true;
    }

    /**
     * Resume atualizações
     */
    resumeUpdates() {
        this.isUpdating = false;
    }

    /**
     * Verifica por atualizações no servidor
     */
    async checkForUpdates() {
        if (!this.currentProposalId) return;

        try {
            const response = await fetch(`/proposta/${this.currentProposalId}/status`);
            const data = await response.json();

            if (data.success && data.status_changed) {
                this.handleStatusUpdate(data);
            }
        } catch (error) {
            console.error('Erro ao verificar atualizações:', error);
        }
    }

    /**
     * Manipula atualização de status
     */
    handleStatusUpdate(data) {
        // Mostrar notificação de mudança
        this.showNotification(data.message, 'info');
        
        // Recarregar página após breve delay para mostrar a notificação
        setTimeout(() => {
            location.reload();
        }, 2000);
    }

    /**
     * Manipula aceitação de proposta
     */
    async handleAcceptProposal(e) {
        e.preventDefault();
        
        if (!this.currentProposalId) return;

        const button = e.target.closest('button');
        this.setButtonLoading(button, true, 'Aceitar Proposta', 'Processando...');

        try {
            const response = await fetch(`/proposta/${this.currentProposalId}/aprovar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                // Mensagem de sucesso apropriada indicando que o prestador pode aceitar o convite
                const effectiveValue = data.effective_value ? this.formatCurrency(data.effective_value) : '';
                const successMessage = effectiveValue 
                    ? `✅ Proposta aceita com sucesso! O novo valor é ${effectiveValue}. O prestador já pode aceitar o convite.`
                    : '✅ Proposta aceita com sucesso! O prestador já pode aceitar o convite.';
                
                this.showNotification(successMessage, 'success');
                
                // Recarregar página para mostrar o novo valor e estado atualizado
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

        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.setButtonLoading(submitBtn, true, 'Rejeitar Proposta', 'Rejeitando...');

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Mensagem de sucesso apropriada indicando que o convite voltou ao valor original
                this.showNotification('✅ Proposta rejeitada com sucesso! O convite retornou ao valor original.', 'success');
                
                // Recarregar página para mostrar estado atualizado
                setTimeout(() => location.reload(), 1500);
            } else {
                throw new Error(data.message || 'Erro ao rejeitar proposta');
            }
        } catch (error) {
            console.error('Erro ao rejeitar proposta:', error);
            this.showNotification('❌ ' + error.message, 'error');
            this.setButtonLoading(submitBtn, false, 'Rejeitar Proposta');
        }
    }

    /**
     * Manipula criação de proposta
     */
    async handleCreateProposal(e) {
        if (!this.validateCreateProposalForm(e.target)) {
            e.preventDefault();
            return false;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        this.setButtonLoading(submitBtn, true, 'Enviar Proposta', 'Enviando...');

        // Mostrar feedback visual
        this.showNotification('📤 Enviando proposta...', 'info');
    }

    /**
     * Manipula cancelamento de proposta
     */
    async handleCancelProposal(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.setButtonLoading(submitBtn, true, 'Cancelar Proposta', 'Cancelando...');
        this.showNotification('🔄 Cancelando proposta...', 'info');
    }

    /**
     * Manipula adição de saldo e aprovação
     */
    async handleAddBalanceAndApprove(e) {
        e.preventDefault();

        const form = e.target;
        const submitBtn = document.getElementById('confirm-addition-btn');
        const originalText = submitBtn.innerHTML;

        try {
            this.setButtonLoading(submitBtn, true, originalText, 'Processando...');

            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('✅ ' + data.message, 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                throw new Error(data.message || 'Erro ao processar adição de saldo');
            }
        } catch (error) {
            console.error('Erro ao adicionar saldo:', error);
            this.showNotification('❌ ' + error.message, 'error');
            this.setButtonLoading(submitBtn, false, originalText);
        }
    }

    /**
     * Calcula diferença de valor na proposta
     */
    calculateValueDifference(e) {
        const input = e.target;
        const originalValue = parseFloat(input.getAttribute('data-original-value')) || 0;
        const proposedValue = parseFloat(input.value) || 0;
        const difference = proposedValue - originalValue;

        const valueDifferenceDiv = document.getElementById('value-difference');
        const differenceText = document.getElementById('difference-text');

        if (difference !== 0 && proposedValue > 0) {
            valueDifferenceDiv.style.display = 'block';
            
            if (difference > 0) {
                valueDifferenceDiv.className = 'alert alert-warning';
                differenceText.innerHTML = `<i class="fas fa-arrow-up me-1"></i>Aumento de ${this.formatCurrency(difference)}`;
            } else {
                valueDifferenceDiv.className = 'alert alert-info';
                differenceText.innerHTML = `<i class="fas fa-arrow-down me-1"></i>Redução de ${this.formatCurrency(Math.abs(difference))}`;
            }
        } else {
            valueDifferenceDiv.style.display = 'none';
        }

        // Validar valor em tempo real
        this.validateProposedValue(e);
    }

    /**
     * Manipula mudança no valor a adicionar
     */
    handleAmountChange(e) {
        // Limpar seleção de botões pré-definidos
        document.querySelectorAll('#predefined-amounts .btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Simular se valor válido
        const amount = parseFloat(e.target.value) || 0;
        if (amount > 0) {
            this.simulateAddition();
        } else {
            document.getElementById('simulation-result').style.display = 'none';
            document.getElementById('confirm-addition-btn').disabled = true;
        }
    }

    /**
     * Manipula seleção de valor pré-definido
     */
    handlePredefinedAmount(e) {
        const button = e.target.closest('button');
        const amount = parseFloat(button.getAttribute('data-amount'));
        
        if (amount) {
            this.selectPredefinedAmount(amount, button);
        }
    }

    /**
     * Seleciona valor pré-definido
     */
    selectPredefinedAmount(amount, button) {
        // Atualizar campo de input
        document.getElementById('amount_to_add').value = amount.toFixed(2);

        // Atualizar botões ativos
        document.querySelectorAll('#predefined-amounts .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Simular automaticamente
        this.simulateAddition();
    }

    /**
     * Simula adição de saldo
     */
    async simulateAddition() {
        const amountInput = document.getElementById('amount_to_add');
        const amount = parseFloat(amountInput.value) || 0;

        if (amount <= 0) {
            document.getElementById('simulation-result').style.display = 'none';
            document.getElementById('confirm-addition-btn').disabled = true;
            return;
        }

        try {
            const response = await fetch(`/proposta/${this.currentProposalId}/simular-adicao`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ amount_to_add: amount })
            });

            const data = await response.json();

            if (data.success) {
                this.displaySimulationResult(data);
            } else {
                throw new Error(data.message || 'Erro na simulação');
            }
        } catch (error) {
            console.error('Erro na simulação:', error);
            document.getElementById('simulation-result').style.display = 'none';
            document.getElementById('confirm-addition-btn').disabled = true;
        }
    }

    /**
     * Exibe resultado da simulação
     */
    displaySimulationResult(data) {
        const resultDiv = document.getElementById('simulation-result');
        const statusP = document.getElementById('simulation-status');
        const simulatedBalanceSpan = document.getElementById('simulated-balance');

        simulatedBalanceSpan.textContent = this.formatCurrency(data.simulated_balance);

        if (data.will_be_sufficient) {
            statusP.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i>Saldo será suficiente para aprovar a proposta!';
            statusP.className = 'mb-0 text-success';
            document.getElementById('confirm-addition-btn').disabled = false;
        } else {
            statusP.innerHTML = `<i class="fas fa-exclamation-triangle text-warning me-2"></i>Ainda faltarão ${this.formatCurrency(data.remaining_shortfall)}. Adicione mais saldo.`;
            statusP.className = 'mb-0 text-warning';
            document.getElementById('confirm-addition-btn').disabled = true;
        }

        resultDiv.style.display = 'block';
    }

    /**
     * Verifica saldo para proposta
     */
    async checkProposalBalance(proposalId) {
        try {
            const response = await fetch(`/proposta/verificar-saldo/${proposalId}`);
            const data = await response.json();

            if (data.success) {
                this.displayBalanceStatus(data);
            } else {
                throw new Error(data.message || 'Erro ao verificar saldo');
            }
        } catch (error) {
            console.error('Erro ao verificar saldo:', error);
            document.getElementById('balance-check-container').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Erro ao verificar saldo. Tente recarregar a página.
                </div>
            `;
        }
    }

    /**
     * Exibe status do saldo
     */
    displayBalanceStatus(data) {
        const container = document.getElementById('balance-check-container');
        const acceptButton = document.getElementById('btn-aceitar-proposta');

        if (data.balance_check.is_sufficient) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Saldo Suficiente!</strong> Você pode aceitar esta proposta.
                    <br><small>Saldo atual: ${this.formatCurrency(data.balance_check.current_balance)} | 
                    Necessário: ${this.formatCurrency(data.balance_check.required_amount)}</small>
                </div>
            `;
            acceptButton.disabled = false;
            acceptButton.innerHTML = '<i class="fas fa-check me-2"></i>Aceitar Proposta';
        } else {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Saldo Insuficiente</strong>
                    <br>Saldo atual: ${this.formatCurrency(data.balance_check.current_balance)}
                    <br>Necessário: ${this.formatCurrency(data.balance_check.required_amount)}
                    <br>Faltam: ${this.formatCurrency(data.balance_check.shortfall)}
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-primary" onclick="proposalInteractions.showAddBalanceModal()">
                            <i class="fas fa-plus me-2"></i>Adicionar Saldo
                        </button>
                    </div>
                </div>
            `;
            acceptButton.disabled = true;
            acceptButton.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Saldo Insuficiente';
        }

        this.balanceCheckData = data;
    }

    /**
     * Mostra modal de adicionar saldo
     */
    async showAddBalanceModal() {
        if (!this.balanceCheckData || !this.currentProposalId) return;

        try {
            const response = await fetch(`/proposta/${this.currentProposalId}/calcular-saldo-necessario`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.message || 'Erro ao calcular saldo necessário');
            }

            this.populateAddBalanceModal(data);
            
            const modal = new bootstrap.Modal(document.getElementById('addBalanceModal'));
            modal.show();
        } catch (error) {
            console.error('Erro ao preparar modal:', error);
            this.showNotification('❌ Erro ao carregar informações de saldo: ' + error.message, 'error');
        }
    }

    /**
     * Popula modal de adicionar saldo
     */
    populateAddBalanceModal(data) {
        // Preencher dados básicos
        document.getElementById('current-balance').textContent = this.formatCurrency(data.balance_info.current_balance);
        document.getElementById('required-amount').textContent = this.formatCurrency(data.balance_info.required_amount);
        document.getElementById('shortfall-amount').textContent = this.formatCurrency(data.balance_info.shortfall);
        document.getElementById('proposal-value').textContent = this.formatCurrency(data.proposal_value);
        document.getElementById('contestation-fee').textContent = this.formatCurrency(data.balance_info.contestation_fee);
        document.getElementById('total-needed').textContent = this.formatCurrency(data.balance_info.required_amount);
        document.getElementById('minimum-addition').textContent = this.formatCurrency(data.balance_info.minimum_addition);

        // Criar opções pré-definidas
        const predefinedContainer = document.getElementById('predefined-amounts');
        predefinedContainer.innerHTML = '';

        data.predefined_options.forEach((amount, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `btn btn-outline-primary mb-1 ${index === 0 ? 'active' : ''}`;
            button.setAttribute('data-amount', amount);
            
            let label = this.formatCurrency(amount);
            if (index === 0) label += ' (Mínimo)';
            else if (index === 1) label += ' (Recomendado)';
            
            button.innerHTML = `<i class="fas fa-coins me-2"></i>${label}`;
            predefinedContainer.appendChild(button);
        });

        // Definir valor inicial
        if (data.predefined_options.length > 0) {
            document.getElementById('amount_to_add').value = data.predefined_options[0].toFixed(2);
            this.simulateAddition();
        }

        // Configurar formulário
        const form = document.getElementById('addBalanceForm');
        form.action = `/proposta/${this.currentProposalId}/adicionar-saldo-e-aprovar`;
    }

    /**
     * Validações de formulário
     */
    validateCreateProposalForm(form) {
        const proposedValue = parseFloat(document.getElementById('proposed_value').value);
        const justification = document.getElementById('justification').value.trim();
        const originalValue = parseFloat(document.getElementById('proposed_value').getAttribute('data-original-value')) || 0;

        if (!proposedValue || proposedValue <= 0) {
            this.showNotification('❌ Por favor, informe um valor válido para a proposta.', 'error');
            return false;
        }

        if (!justification) {
            this.showNotification('❌ Por favor, forneça uma justificativa para a alteração.', 'error');
            return false;
        }

        if (proposedValue === originalValue) {
            this.showNotification('❌ O valor proposto deve ser diferente do valor original.', 'error');
            return false;
        }

        const difference = proposedValue - originalValue;
        const action = difference > 0 ? 'aumento' : 'redução';
        const message = `Confirma a proposta de ${action} de ${this.formatCurrency(Math.abs(difference))}?\n\nO cliente será notificado e poderá aceitar ou rejeitar sua proposta.`;

        return confirm(message);
    }

    validateProposedValue(e) {
        const input = e.target;
        const value = parseFloat(input.value);
        
        if (value <= 0) {
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

    validateJustification(e) {
        const input = e.target;
        const value = input.value.trim();
        
        if (value.length < 10) {
            this.addFieldError(input, 'Justificativa muito curta (mínimo 10 caracteres)');
            return false;
        }
        
        if (value.length > 500) {
            this.addFieldError(input, 'Justificativa muito longa (máximo 500 caracteres)');
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    validateAddAmount(e) {
        const input = e.target;
        const value = parseFloat(input.value);
        const min = parseFloat(input.getAttribute('min')) || 1;
        const max = parseFloat(input.getAttribute('max')) || 10000;
        
        if (value < min) {
            this.addFieldError(input, `Valor mínimo: ${this.formatCurrency(min)}`);
            return false;
        }
        
        if (value > max) {
            this.addFieldError(input, `Valor máximo: ${this.formatCurrency(max)}`);
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    validateRejectionReason(e) {
        const input = e.target;
        const value = input.value.trim();
        const maxLength = parseInt(input.getAttribute('maxlength')) || 300;
        
        if (value.length > maxLength) {
            this.addFieldError(input, `Máximo ${maxLength} caracteres`);
            return false;
        }
        
        this.removeFieldError(input);
        return true;
    }

    /**
     * Confirmações
     */
    confirmAcceptProposal() {
        return confirm('Tem certeza que deseja aceitar esta proposta?\n\nEsta ação não pode ser desfeita.');
    }

    confirmRejectProposal() {
        const reason = document.getElementById('rejection-reason').value.trim();
        let message = 'Tem certeza que deseja rejeitar esta proposta?\n\nO convite retornará ao valor original e o prestador será notificado.';
        
        if (reason) {
            message += '\n\nMotivo informado: ' + reason;
        }
        
        return confirm(message);
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
                if (button.classList.contains('btn-success')) {
                    icon.className = 'fas fa-check me-2';
                } else if (button.classList.contains('btn-danger')) {
                    icon.className = 'fas fa-times me-2';
                } else if (button.classList.contains('btn-warning')) {
                    icon.className = 'fas fa-edit me-2';
                } else {
                    icon.className = 'fas fa-check me-2';
                }
            }
            
            if (textSpan && originalText) {
                textSpan.textContent = originalText;
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
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        notificationContainer.appendChild(notification);

        // Auto-remover após delay
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, type === 'error' ? 8000 : 5000);
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
        const metaTag = document.querySelector('meta[name=csrf-token]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.proposalInteractions = new ProposalInteractions();
});