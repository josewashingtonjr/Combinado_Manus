/**
 * Sistema de Atualizações em Tempo Real para Pré-Ordens
 * 
 * Implementa:
 * - Server-Sent Events (SSE) para atualizações em tempo real
 * - Fallback para polling a cada 30 segundos
 * - Indicador de presença (outra parte visualizando)
 * - Notificações toast para eventos importantes
 * - Atualização automática ao submeter/aceitar/rejeitar propostas
 * 
 * Requirements: 20.1-20.5
 * 
 * **Feature: sistema-pre-ordem-negociacao, Property 59-62: Atualizações em tempo real**
 * **Validates: Requirements 20.1-20.5**
 */

class PreOrdemRealtime {
    constructor(preOrderId, userId, userRole) {
        this.preOrderId = preOrderId;
        this.userId = userId;
        this.userRole = userRole;
        this.eventSource = null;
        this.pollingInterval = null;
        this.lastUpdateTimestamp = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.pollingIntervalMs = 30000; // 30 segundos
        this.presenceCheckIntervalMs = 60000; // 1 minuto
        this.presenceInterval = null;
        this.otherPartyPresent = false;
        
        // Callbacks para eventos
        this.onStatusChange = null;
        this.onProposalReceived = null;
        this.onProposalAccepted = null;
        this.onProposalRejected = null;
        this.onMutualAcceptance = null;
        this.onPresenceChange = null;
        this.onError = null;
        
        this.init();
    }

    /**
     * Inicializa o sistema de tempo real
     */
    init() {
        console.log(`[PreOrdemRealtime] Inicializando para pré-ordem ${this.preOrderId}`);
        
        // Tentar conectar via SSE primeiro
        if (this.supportsSSE()) {
            this.connectSSE();
        } else {
            console.log('[PreOrdemRealtime] SSE não suportado, usando polling');
            this.startPolling();
        }
        
        // Iniciar verificação de presença
        this.startPresenceCheck();
        
        // Registrar presença inicial
        this.registerPresence();
        
        // Configurar listeners para eventos de página
        this.setupPageListeners();
        
        // Criar container de notificações se não existir
        this.createNotificationContainer();
    }

    /**
     * Verifica se o navegador suporta SSE
     */
    supportsSSE() {
        return typeof EventSource !== 'undefined';
    }

    /**
     * Conecta via Server-Sent Events
     */
    connectSSE() {
        try {
            const url = `/pre-ordem/${this.preOrderId}/stream?user_id=${this.userId}&role=${this.userRole}`;
            this.eventSource = new EventSource(url);
            
            this.eventSource.onopen = () => {
                console.log('[PreOrdemRealtime] Conexão SSE estabelecida');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.stopPolling();
                this.showConnectionStatus(true);
            };
            
            this.eventSource.onmessage = (event) => {
                this.handleSSEMessage(event);
            };
            
            // Eventos específicos
            this.eventSource.addEventListener('status_change', (event) => {
                this.handleStatusChange(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('proposal_received', (event) => {
                this.handleProposalReceived(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('proposal_accepted', (event) => {
                this.handleProposalAccepted(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('proposal_rejected', (event) => {
                this.handleProposalRejected(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('mutual_acceptance', (event) => {
                this.handleMutualAcceptance(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('presence', (event) => {
                this.handlePresenceUpdate(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('heartbeat', (event) => {
                console.log('[PreOrdemRealtime] Heartbeat recebido');
            });
            
            this.eventSource.onerror = (error) => {
                console.error('[PreOrdemRealtime] Erro SSE:', error);
                this.handleSSEError(error);
            };
            
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro ao conectar SSE:', error);
            this.startPolling();
        }
    }

    /**
     * Trata mensagens SSE genéricas
     */
    handleSSEMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('[PreOrdemRealtime] Mensagem recebida:', data);
            
            if (data.type) {
                switch (data.type) {
                    case 'status_change':
                        this.handleStatusChange(data);
                        break;
                    case 'proposal_received':
                        this.handleProposalReceived(data);
                        break;
                    case 'proposal_accepted':
                        this.handleProposalAccepted(data);
                        break;
                    case 'proposal_rejected':
                        this.handleProposalRejected(data);
                        break;
                    case 'mutual_acceptance':
                        this.handleMutualAcceptance(data);
                        break;
                    case 'presence':
                        this.handlePresenceUpdate(data);
                        break;
                    case 'connected':
                        console.log('[PreOrdemRealtime] Conexão confirmada');
                        break;
                }
            }
            
            this.lastUpdateTimestamp = new Date();
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro ao processar mensagem:', error);
        }
    }

    /**
     * Trata erros de conexão SSE
     */
    handleSSEError(error) {
        this.isConnected = false;
        this.showConnectionStatus(false);
        
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`[PreOrdemRealtime] Tentando reconectar em ${delay}ms...`);
            
            setTimeout(() => {
                this.connectSSE();
            }, delay);
        } else {
            console.log('[PreOrdemRealtime] Máximo de tentativas atingido, usando polling');
            this.startPolling();
        }
    }

    /**
     * Inicia polling como fallback
     */
    startPolling() {
        if (this.pollingInterval) {
            return; // Já está em polling
        }
        
        console.log(`[PreOrdemRealtime] Iniciando polling a cada ${this.pollingIntervalMs/1000}s`);
        
        // Fazer primeira verificação imediatamente
        this.pollForUpdates();
        
        // Configurar intervalo
        this.pollingInterval = setInterval(() => {
            this.pollForUpdates();
        }, this.pollingIntervalMs);
        
        this.showPollingIndicator(true);
    }

    /**
     * Para o polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            this.showPollingIndicator(false);
        }
    }

    /**
     * Faz polling para verificar atualizações
     */
    async pollForUpdates() {
        try {
            const response = await fetch(`/pre-ordem/${this.preOrderId}/status`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.processStatusUpdate(data);
            }
            
            this.lastUpdateTimestamp = new Date();
            
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro no polling:', error);
            if (this.onError) {
                this.onError(error);
            }
        }
    }

    /**
     * Processa atualização de status recebida via polling
     */
    processStatusUpdate(data) {
        // Verificar se houve mudança de status
        const statusElement = document.querySelector('[data-pre-order-status]');
        const currentStatus = statusElement ? statusElement.dataset.preOrderStatus : null;
        
        if (currentStatus && currentStatus !== data.status) {
            this.handleStatusChange({
                old_status: currentStatus,
                new_status: data.status,
                status_display: data.status_display
            });
        }
        
        // Verificar aceitação mútua
        if (data.has_mutual_acceptance) {
            this.handleMutualAcceptance(data);
        }
        
        // Atualizar indicadores de aceitação
        this.updateAcceptanceIndicators(data);
        
        // Verificar proposta ativa
        if (data.has_active_proposal) {
            this.updateProposalIndicator(true);
        }
    }

    /**
     * Inicia verificação de presença
     */
    startPresenceCheck() {
        this.presenceInterval = setInterval(() => {
            this.checkPresence();
        }, this.presenceCheckIntervalMs);
    }

    /**
     * Registra presença do usuário
     */
    async registerPresence() {
        try {
            await fetch(`/pre-ordem/${this.preOrderId}/presenca`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    action: 'enter'
                })
            });
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro ao registrar presença:', error);
        }
    }

    /**
     * Verifica presença da outra parte
     */
    async checkPresence() {
        try {
            const response = await fetch(`/pre-ordem/${this.preOrderId}/presenca?user_id=${this.userId}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handlePresenceUpdate(data);
            }
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro ao verificar presença:', error);
        }
    }

    // =========================================================================
    // HANDLERS DE EVENTOS
    // =========================================================================

    /**
     * Trata mudança de status
     */
    handleStatusChange(data) {
        console.log('[PreOrdemRealtime] Status alterado:', data);
        
        // Atualizar badge de status na página
        this.updateStatusBadge(data.new_status, data.status_display);
        
        // Mostrar notificação
        this.showToast(
            `Status atualizado para: ${data.status_display}`,
            'info',
            'fa-sync-alt'
        );
        
        // Callback personalizado
        if (this.onStatusChange) {
            this.onStatusChange(data);
        }
        
        // Recarregar página se status for terminal
        if (['convertida', 'cancelada', 'expirada'].includes(data.new_status)) {
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    }

    /**
     * Trata recebimento de nova proposta
     */
    handleProposalReceived(data) {
        console.log('[PreOrdemRealtime] Nova proposta recebida:', data);
        
        // Mostrar notificação destacada
        this.showToast(
            `📝 Nova proposta recebida de ${data.proposer_name || 'outra parte'}!`,
            'warning',
            'fa-file-alt'
        );
        
        // Atualizar indicador de proposta
        this.updateProposalIndicator(true);
        
        // Callback personalizado
        if (this.onProposalReceived) {
            this.onProposalReceived(data);
        }
        
        // Recarregar página para mostrar proposta
        setTimeout(() => {
            location.reload();
        }, 1500);
    }

    /**
     * Trata aceitação de proposta
     */
    handleProposalAccepted(data) {
        console.log('[PreOrdemRealtime] Proposta aceita:', data);
        
        this.showToast(
            '✅ Sua proposta foi aceita! Os novos termos foram aplicados.',
            'success',
            'fa-check-circle'
        );
        
        // Callback personalizado
        if (this.onProposalAccepted) {
            this.onProposalAccepted(data);
        }
        
        // Recarregar página
        setTimeout(() => {
            location.reload();
        }, 1500);
    }

    /**
     * Trata rejeição de proposta
     */
    handleProposalRejected(data) {
        console.log('[PreOrdemRealtime] Proposta rejeitada:', data);
        
        this.showToast(
            '❌ Sua proposta foi rejeitada. Você pode fazer uma nova proposta.',
            'danger',
            'fa-times-circle'
        );
        
        // Callback personalizado
        if (this.onProposalRejected) {
            this.onProposalRejected(data);
        }
        
        // Recarregar página
        setTimeout(() => {
            location.reload();
        }, 1500);
    }

    /**
     * Trata aceitação mútua alcançada
     */
    handleMutualAcceptance(data) {
        console.log('[PreOrdemRealtime] Aceitação mútua alcançada:', data);
        
        // Mostrar notificação especial
        this.showToast(
            '🎉 Ambas as partes aceitaram os termos! A pré-ordem será convertida em ordem.',
            'success',
            'fa-handshake',
            10000 // Duração maior
        );
        
        // Callback personalizado
        if (this.onMutualAcceptance) {
            this.onMutualAcceptance(data);
        }
        
        // Recarregar página após delay
        setTimeout(() => {
            location.reload();
        }, 3000);
    }

    /**
     * Trata atualização de presença
     */
    handlePresenceUpdate(data) {
        const wasPresent = this.otherPartyPresent;
        this.otherPartyPresent = data.other_party_present || false;
        
        // Atualizar indicador visual
        this.updatePresenceIndicator(this.otherPartyPresent);
        
        // Notificar apenas se mudou
        if (wasPresent !== this.otherPartyPresent) {
            if (this.otherPartyPresent) {
                this.showToast(
                    `👁️ ${data.other_party_name || 'A outra parte'} está visualizando esta pré-ordem`,
                    'info',
                    'fa-eye',
                    3000
                );
            }
            
            if (this.onPresenceChange) {
                this.onPresenceChange(this.otherPartyPresent, data);
            }
        }
    }

    // =========================================================================
    // ATUALIZAÇÕES DE UI
    // =========================================================================

    /**
     * Atualiza badge de status na página
     */
    updateStatusBadge(status, statusDisplay) {
        const badges = document.querySelectorAll('.status-badge-large, [data-pre-order-status]');
        
        badges.forEach(badge => {
            // Remover classes de cor antigas
            badge.classList.remove(
                'bg-primary', 'bg-secondary', 'bg-success', 
                'bg-danger', 'bg-warning', 'bg-info'
            );
            
            // Adicionar nova classe de cor
            const colorClass = this.getStatusColorClass(status);
            badge.classList.add(colorClass);
            
            // Atualizar texto
            badge.textContent = statusDisplay;
            
            // Atualizar data attribute
            badge.dataset.preOrderStatus = status;
        });
        
        // Adicionar animação de destaque
        badges.forEach(badge => {
            badge.classList.add('status-updated');
            setTimeout(() => {
                badge.classList.remove('status-updated');
            }, 1000);
        });
    }

    /**
     * Retorna classe de cor para status
     */
    getStatusColorClass(status) {
        const colorMap = {
            'em_negociacao': 'bg-primary',
            'aguardando_resposta': 'bg-warning',
            'pronto_conversao': 'bg-info',
            'convertida': 'bg-success',
            'cancelada': 'bg-danger',
            'expirada': 'bg-secondary'
        };
        return colorMap[status] || 'bg-secondary';
    }

    /**
     * Atualiza indicadores de aceitação
     */
    updateAcceptanceIndicators(data) {
        // Atualizar badge do cliente
        const clientBadge = document.querySelector('[data-acceptance="client"]');
        if (clientBadge) {
            if (data.client_accepted_terms) {
                clientBadge.className = 'badge bg-success';
                clientBadge.innerHTML = '<i class="fas fa-check"></i> Aceitou';
            } else {
                clientBadge.className = 'badge bg-warning';
                clientBadge.innerHTML = '<i class="fas fa-clock"></i> Pendente';
            }
        }
        
        // Atualizar badge do prestador
        const providerBadge = document.querySelector('[data-acceptance="provider"]');
        if (providerBadge) {
            if (data.provider_accepted_terms) {
                providerBadge.className = 'badge bg-success';
                providerBadge.innerHTML = '<i class="fas fa-check"></i> Aceitou';
            } else {
                providerBadge.className = 'badge bg-warning';
                providerBadge.innerHTML = '<i class="fas fa-clock"></i> Pendente';
            }
        }
    }

    /**
     * Atualiza indicador de proposta ativa
     */
    updateProposalIndicator(hasProposal) {
        const indicator = document.querySelector('.proposal-indicator, [data-proposal-indicator]');
        
        if (indicator) {
            if (hasProposal) {
                indicator.style.display = 'block';
                indicator.classList.add('pulse-animation');
            } else {
                indicator.style.display = 'none';
                indicator.classList.remove('pulse-animation');
            }
        }
    }

    /**
     * Atualiza indicador de presença
     */
    updatePresenceIndicator(isPresent) {
        let indicator = document.getElementById('presence-indicator');
        
        if (!indicator) {
            // Criar indicador se não existir
            indicator = document.createElement('div');
            indicator.id = 'presence-indicator';
            indicator.className = 'presence-indicator';
            document.body.appendChild(indicator);
        }
        
        if (isPresent) {
            indicator.innerHTML = `
                <i class="fas fa-eye me-2"></i>
                <span>Outra parte visualizando</span>
            `;
            indicator.classList.add('visible');
        } else {
            indicator.classList.remove('visible');
        }
    }

    /**
     * Mostra status de conexão
     */
    showConnectionStatus(connected) {
        let statusEl = document.getElementById('realtime-connection-status');
        
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'realtime-connection-status';
            statusEl.className = 'realtime-status';
            document.body.appendChild(statusEl);
        }
        
        if (connected) {
            statusEl.innerHTML = '<i class="fas fa-wifi me-1"></i> Tempo real';
            statusEl.className = 'realtime-status connected';
        } else {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Reconectando...';
            statusEl.className = 'realtime-status disconnected';
        }
    }

    /**
     * Mostra indicador de polling
     */
    showPollingIndicator(active) {
        let indicator = document.getElementById('polling-indicator');
        
        if (!indicator && active) {
            indicator = document.createElement('div');
            indicator.id = 'polling-indicator';
            indicator.className = 'polling-indicator';
            indicator.innerHTML = `
                <i class="fas fa-sync-alt me-1"></i>
                <span>Atualização automática</span>
                <button type="button" class="btn btn-sm btn-outline-light ms-2" 
                        onclick="window.preOrdemRealtime.forceRefresh()" 
                        title="Atualizar agora">
                    <i class="fas fa-redo"></i>
                </button>
            `;
            document.body.appendChild(indicator);
        }
        
        if (indicator) {
            indicator.style.display = active ? 'flex' : 'none';
        }
    }

    // =========================================================================
    // SISTEMA DE NOTIFICAÇÕES TOAST
    // =========================================================================

    /**
     * Cria container de notificações
     */
    createNotificationContainer() {
        if (!document.getElementById('realtime-toast-container')) {
            const container = document.createElement('div');
            container.id = 'realtime-toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
    }

    /**
     * Mostra notificação toast
     */
    showToast(message, type = 'info', icon = 'fa-info-circle', duration = 5000) {
        const container = document.getElementById('realtime-toast-container');
        if (!container) return;
        
        const toastId = `toast-${Date.now()}`;
        const colorClass = this.getToastColorClass(type);
        
        const toastHtml = `
            <div id="${toastId}" class="toast show ${colorClass}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header ${colorClass}">
                    <i class="fas ${icon} me-2"></i>
                    <strong class="me-auto">Pré-Ordem</strong>
                    <small>Agora</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fechar"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        
        // Adicionar animação de entrada
        toastElement.classList.add('toast-enter');
        
        // Configurar botão de fechar
        const closeBtn = toastElement.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.removeToast(toastElement);
            });
        }
        
        // Auto-remover após duração
        setTimeout(() => {
            this.removeToast(toastElement);
        }, duration);
        
        // Tocar som de notificação (se permitido)
        this.playNotificationSound(type);
    }

    /**
     * Remove toast com animação
     */
    removeToast(toastElement) {
        if (!toastElement) return;
        
        toastElement.classList.add('toast-exit');
        
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.parentNode.removeChild(toastElement);
            }
        }, 300);
    }

    /**
     * Retorna classe de cor para toast
     */
    getToastColorClass(type) {
        const colorMap = {
            'success': 'bg-success text-white',
            'danger': 'bg-danger text-white',
            'warning': 'bg-warning text-dark',
            'info': 'bg-info text-white',
            'primary': 'bg-primary text-white'
        };
        return colorMap[type] || 'bg-info text-white';
    }

    /**
     * Toca som de notificação
     */
    playNotificationSound(type) {
        // Verificar se notificações de som estão habilitadas
        if (localStorage.getItem('preOrdemSoundEnabled') === 'false') {
            return;
        }
        
        try {
            // Criar contexto de áudio
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Configurar frequência baseada no tipo
            const frequencies = {
                'success': 880,
                'danger': 440,
                'warning': 660,
                'info': 550
            };
            
            oscillator.frequency.value = frequencies[type] || 550;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
            
        } catch (error) {
            // Ignorar erros de áudio silenciosamente
        }
    }

    // =========================================================================
    // MÉTODOS PÚBLICOS
    // =========================================================================

    /**
     * Força atualização manual
     */
    forceRefresh() {
        console.log('[PreOrdemRealtime] Atualização manual solicitada');
        
        this.showToast('🔄 Atualizando...', 'info', 'fa-sync-alt', 2000);
        
        this.pollForUpdates().then(() => {
            // Recarregar página para garantir dados atualizados
            location.reload();
        });
    }

    /**
     * Notifica envio de proposta (para atualização imediata)
     */
    notifyProposalSubmitted() {
        console.log('[PreOrdemRealtime] Proposta enviada, aguardando confirmação...');
        
        // Forçar polling imediato após envio
        setTimeout(() => {
            this.pollForUpdates();
        }, 1000);
    }

    /**
     * Notifica aceitação de proposta
     */
    notifyProposalAccepted() {
        console.log('[PreOrdemRealtime] Proposta aceita, atualizando...');
        
        setTimeout(() => {
            this.pollForUpdates();
        }, 1000);
    }

    /**
     * Notifica rejeição de proposta
     */
    notifyProposalRejected() {
        console.log('[PreOrdemRealtime] Proposta rejeitada, atualizando...');
        
        setTimeout(() => {
            this.pollForUpdates();
        }, 1000);
    }

    /**
     * Notifica aceitação de termos
     */
    notifyTermsAccepted() {
        console.log('[PreOrdemRealtime] Termos aceitos, verificando aceitação mútua...');
        
        setTimeout(() => {
            this.pollForUpdates();
        }, 1000);
    }

    /**
     * Habilita/desabilita som de notificações
     */
    toggleSound(enabled) {
        localStorage.setItem('preOrdemSoundEnabled', enabled ? 'true' : 'false');
    }

    /**
     * Verifica se som está habilitado
     */
    isSoundEnabled() {
        return localStorage.getItem('preOrdemSoundEnabled') !== 'false';
    }

    // =========================================================================
    // UTILITÁRIOS
    // =========================================================================

    /**
     * Obtém token CSRF
     */
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

    /**
     * Configura listeners de página
     */
    setupPageListeners() {
        // Registrar saída ao fechar página
        window.addEventListener('beforeunload', () => {
            this.unregisterPresence();
        });
        
        // Pausar quando página não está visível
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    /**
     * Pausa atualizações
     */
    pauseUpdates() {
        console.log('[PreOrdemRealtime] Pausando atualizações (página oculta)');
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        if (this.presenceInterval) {
            clearInterval(this.presenceInterval);
            this.presenceInterval = null;
        }
    }

    /**
     * Retoma atualizações
     */
    resumeUpdates() {
        console.log('[PreOrdemRealtime] Retomando atualizações');
        
        // Fazer polling imediato
        this.pollForUpdates();
        
        // Reiniciar intervalos se necessário
        if (!this.isConnected && !this.pollingInterval) {
            this.startPolling();
        }
        
        if (!this.presenceInterval) {
            this.startPresenceCheck();
        }
        
        // Registrar presença novamente
        this.registerPresence();
    }

    /**
     * Remove registro de presença
     */
    async unregisterPresence() {
        try {
            // Usar sendBeacon para garantir envio mesmo ao fechar página
            const data = JSON.stringify({
                user_id: this.userId,
                action: 'leave'
            });
            
            navigator.sendBeacon(
                `/pre-ordem/${this.preOrderId}/presenca`,
                new Blob([data], { type: 'application/json' })
            );
        } catch (error) {
            console.error('[PreOrdemRealtime] Erro ao remover presença:', error);
        }
    }

    /**
     * Desconecta e limpa recursos
     */
    disconnect() {
        console.log('[PreOrdemRealtime] Desconectando...');
        
        // Fechar SSE
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        // Parar polling
        this.stopPolling();
        
        // Parar verificação de presença
        if (this.presenceInterval) {
            clearInterval(this.presenceInterval);
            this.presenceInterval = null;
        }
        
        // Remover presença
        this.unregisterPresence();
        
        this.isConnected = false;
    }
}


// =============================================================================
// INICIALIZAÇÃO AUTOMÁTICA
// =============================================================================

/**
 * Inicializa o sistema de tempo real quando a página carrega
 */
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos em uma página de pré-ordem
    const preOrderElement = document.querySelector('[data-pre-order-id]');
    
    if (preOrderElement) {
        const preOrderId = preOrderElement.dataset.preOrderId;
        const userId = preOrderElement.dataset.userId;
        const userRole = preOrderElement.dataset.userRole;
        
        if (preOrderId && userId) {
            // Criar instância global
            window.preOrdemRealtime = new PreOrdemRealtime(preOrderId, userId, userRole);
            
            console.log(`[PreOrdemRealtime] Sistema inicializado para pré-ordem ${preOrderId}`);
        }
    }
});

// =============================================================================
// ESTILOS CSS DINÂMICOS
// =============================================================================

/**
 * Adiciona estilos CSS necessários para o sistema de tempo real
 */
(function() {
    const styles = `
        /* Indicador de status de conexão */
        .realtime-status {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            z-index: 9998;
            transition: all 0.3s ease;
        }
        
        .realtime-status.connected {
            background: #28a745;
            color: white;
        }
        
        .realtime-status.disconnected {
            background: #ffc107;
            color: #212529;
        }
        
        /* Indicador de presença */
        .presence-indicator {
            position: fixed;
            bottom: 60px;
            left: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            background: #17a2b8;
            color: white;
            font-size: 12px;
            font-weight: 500;
            z-index: 9998;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s ease;
        }
        
        .presence-indicator.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        /* Indicador de polling */
        .polling-indicator {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 8px 16px;
            border-radius: 20px;
            background: #6c757d;
            color: white;
            font-size: 12px;
            font-weight: 500;
            z-index: 9998;
            display: flex;
            align-items: center;
        }
        
        .polling-indicator i {
            animation: spin 2s linear infinite;
        }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        /* Animação de atualização de status */
        .status-updated {
            animation: statusPulse 1s ease;
        }
        
        @keyframes statusPulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        /* Animação de proposta pendente */
        .pulse-animation {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
        }
        
        /* Animações de toast */
        .toast-enter {
            animation: toastEnter 0.3s ease;
        }
        
        .toast-exit {
            animation: toastExit 0.3s ease forwards;
        }
        
        @keyframes toastEnter {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes toastExit {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        /* Estilo do toast */
        #realtime-toast-container .toast {
            min-width: 300px;
            margin-bottom: 10px;
        }
        
        #realtime-toast-container .toast-header {
            border-bottom: none;
        }
        
        /* Responsividade */
        @media (max-width: 768px) {
            .realtime-status,
            .presence-indicator,
            .polling-indicator {
                bottom: 10px;
                left: 10px;
                font-size: 11px;
                padding: 6px 12px;
            }
            
            #realtime-toast-container {
                left: 10px;
                right: 10px;
            }
            
            #realtime-toast-container .toast {
                min-width: auto;
                width: 100%;
            }
        }
    `;
    
    const styleSheet = document.createElement('style');
    styleSheet.type = 'text/css';
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);
})();
