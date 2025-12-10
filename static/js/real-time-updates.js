/**
 * Sistema de atualizações em tempo real para propostas
 * Implementa WebSocket ou polling para atualizações instantâneas
 */

class RealTimeUpdates {
    constructor() {
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.updateInterval = null;
        this.lastUpdateTime = Date.now();
        
        this.init();
    }

    init() {
        this.setupConnectionStatus();
        this.startPolling();
        this.setupVisibilityHandling();
        this.setupNetworkHandling();
    }

    /**
     * Configura indicador de status de conexão
     */
    setupConnectionStatus() {
        // Criar indicador de status se não existir
        if (!document.getElementById('connection-status')) {
            const statusIndicator = document.createElement('div');
            statusIndicator.id = 'connection-status';
            statusIndicator.className = 'connection-status online';
            statusIndicator.innerHTML = '<i class="fas fa-wifi me-1"></i>Online';
            document.body.appendChild(statusIndicator);
        }
    }

    /**
     * Inicia polling para atualizações
     */
    startPolling() {
        if (this.updateInterval) return;

        // Verificar se há elementos que precisam de atualizações
        const proposalElements = document.querySelectorAll('[data-proposal-status]');
        if (proposalElements.length === 0) return;

        this.updateInterval = setInterval(() => {
            if (!document.hidden && this.shouldCheckForUpdates()) {
                this.checkForUpdates();
            }
        }, 10000); // Verificar a cada 10 segundos

        this.setConnectionStatus(true);
    }

    /**
     * Para polling
     */
    stopPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        this.setConnectionStatus(false);
    }

    /**
     * Verifica se deve buscar atualizações
     */
    shouldCheckForUpdates() {
        // Não verificar se há modal aberto
        if (document.querySelector('.modal.show')) {
            return false;
        }

        // Não verificar se usuário está digitando
        if (document.activeElement && document.activeElement.tagName === 'INPUT') {
            return false;
        }

        // Verificar apenas se passou tempo suficiente desde a última atualização
        return (Date.now() - this.lastUpdateTime) > 8000;
    }

    /**
     * Verifica atualizações no servidor
     */
    async checkForUpdates() {
        try {
            const proposalElements = document.querySelectorAll('[data-proposal-status]');
            const inviteId = this.getInviteId();
            
            if (!inviteId) return;

            const response = await fetch(`/convite/${inviteId}/status-updates`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success && data.has_updates) {
                this.handleUpdates(data.updates);
            }

            this.lastUpdateTime = Date.now();
            this.setConnectionStatus(true);
            this.reconnectAttempts = 0;

        } catch (error) {
            console.error('Erro ao verificar atualizações:', error);
            this.handleConnectionError();
        }
    }

    /**
     * Manipula atualizações recebidas
     */
    handleUpdates(updates) {
        updates.forEach(update => {
            switch (update.type) {
                case 'proposal_status_changed':
                    this.handleProposalStatusUpdate(update);
                    break;
                case 'balance_updated':
                    this.handleBalanceUpdate(update);
                    break;
                case 'new_notification':
                    this.handleNewNotification(update);
                    break;
                case 'invite_expired':
                    this.handleInviteExpired(update);
                    break;
                default:
                    console.log('Tipo de atualização desconhecido:', update.type);
            }
        });
    }

    /**
     * Manipula mudança de status da proposta
     */
    handleProposalStatusUpdate(update) {
        // Mostrar notificação
        this.showRealTimeNotification(update.message, 'info');
        
        // Atualizar elementos na página
        this.updateProposalStatusElements(update.new_status);
        
        // Se for uma mudança crítica, recarregar após delay
        if (update.requires_reload) {
            setTimeout(() => {
                if (confirm('O status da proposta foi atualizado. Deseja recarregar a página para ver as mudanças?')) {
                    location.reload();
                }
            }, 2000);
        }
    }

    /**
     * Manipula atualização de saldo
     */
    handleBalanceUpdate(update) {
        // Atualizar elementos de saldo na página
        const balanceElements = document.querySelectorAll('[data-balance]');
        balanceElements.forEach(element => {
            element.textContent = this.formatCurrency(update.new_balance);
            element.setAttribute('data-balance', update.new_balance);
        });

        // Mostrar notificação se for um aumento significativo
        if (update.change > 0) {
            this.showRealTimeNotification(
                `💰 Saldo atualizado: +${this.formatCurrency(update.change)}`, 
                'success'
            );
        }

        // Re-verificar suficiência de saldo se há proposta pendente
        if (window.proposalInteractions && window.proposalInteractions.currentProposalId) {
            window.proposalInteractions.checkProposalBalance(
                window.proposalInteractions.currentProposalId
            );
        }
    }

    /**
     * Manipula nova notificação
     */
    handleNewNotification(update) {
        this.showRealTimeNotification(update.message, update.level || 'info');
        
        // Adicionar indicador visual se há notificações não lidas
        this.updateNotificationBadge(update.unread_count);
    }

    /**
     * Manipula expiração de convite
     */
    handleInviteExpired(update) {
        this.showRealTimeNotification(
            '⏰ Este convite expirou e não pode mais ser modificado.', 
            'warning'
        );
        
        // Desabilitar botões de ação
        this.disableActionButtons();
        
        // Recarregar após delay
        setTimeout(() => {
            location.reload();
        }, 5000);
    }

    /**
     * Atualiza elementos de status da proposta
     */
    updateProposalStatusElements(newStatus) {
        const statusElements = document.querySelectorAll('[data-proposal-status]');
        statusElements.forEach(element => {
            element.setAttribute('data-proposal-status', newStatus);
            
            // Atualizar classes CSS baseadas no status
            element.className = element.className.replace(
                /proposal-(pending|accepted|rejected)/g, 
                ''
            );
            
            if (newStatus === 'proposta_enviada') {
                element.classList.add('proposal-pending');
            } else if (newStatus === 'proposta_aceita') {
                element.classList.add('proposal-accepted');
            } else if (newStatus === 'proposta_rejeitada') {
                element.classList.add('proposal-rejected');
            }
        });
    }

    /**
     * Atualiza badge de notificações
     */
    updateNotificationBadge(count) {
        let badge = document.querySelector('.notification-badge');
        
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'notification-badge badge bg-danger position-absolute';
                badge.style.top = '-5px';
                badge.style.right = '-5px';
                
                const bellIcon = document.querySelector('.fa-bell');
                if (bellIcon && bellIcon.parentElement) {
                    bellIcon.parentElement.style.position = 'relative';
                    bellIcon.parentElement.appendChild(badge);
                }
            }
            
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        } else if (badge) {
            badge.style.display = 'none';
        }
    }

    /**
     * Desabilita botões de ação
     */
    disableActionButtons() {
        const actionButtons = document.querySelectorAll(
            '#btn-aceitar-proposta, .btn-reject-proposal, .btn-create-proposal, .btn-cancel-proposal'
        );
        
        actionButtons.forEach(button => {
            button.disabled = true;
            button.classList.add('disabled');
            button.title = 'Convite expirado';
        });
    }

    /**
     * Manipula erro de conexão
     */
    handleConnectionError() {
        this.setConnectionStatus(false);
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.startPolling();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.showRealTimeNotification(
                '⚠️ Conexão perdida. Algumas atualizações podem não aparecer automaticamente.', 
                'warning'
            );
        }
    }

    /**
     * Define status de conexão
     */
    setConnectionStatus(isOnline) {
        this.isConnected = isOnline;
        const statusElement = document.getElementById('connection-status');
        
        if (statusElement) {
            if (isOnline) {
                statusElement.className = 'connection-status online';
                statusElement.innerHTML = '<i class="fas fa-wifi me-1"></i>Online';
            } else {
                statusElement.className = 'connection-status offline';
                statusElement.innerHTML = '<i class="fas fa-wifi-slash me-1"></i>Offline';
            }
        }
    }

    /**
     * Configura manipulação de visibilidade da página
     */
    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Página não está visível - reduzir frequência ou parar
                this.stopPolling();
            } else {
                // Página voltou a ser visível - retomar atualizações
                this.startPolling();
                // Verificar imediatamente por atualizações perdidas
                setTimeout(() => this.checkForUpdates(), 1000);
            }
        });
    }

    /**
     * Configura manipulação de rede
     */
    setupNetworkHandling() {
        window.addEventListener('online', () => {
            this.showRealTimeNotification('🌐 Conexão restaurada', 'success');
            this.reconnectAttempts = 0;
            this.startPolling();
        });

        window.addEventListener('offline', () => {
            this.showRealTimeNotification('📡 Sem conexão com a internet', 'warning');
            this.stopPolling();
        });
    }

    /**
     * Mostra notificação em tempo real
     */
    showRealTimeNotification(message, type = 'info') {
        // Usar o sistema de notificações existente se disponível
        if (window.proposalInteractions) {
            window.proposalInteractions.showNotification(message, type);
            return;
        }

        // Fallback para notificação simples
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapColor(type)} alert-dismissible fade show position-fixed`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.maxWidth = '300px';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remover
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Obtém ID do convite da URL ou elementos da página
     */
    getInviteId() {
        // Tentar obter da URL
        const urlMatch = window.location.pathname.match(/\/convite\/(\d+)/);
        if (urlMatch) {
            return urlMatch[1];
        }

        // Tentar obter de elementos da página
        const inviteElement = document.querySelector('[data-invite-id]');
        if (inviteElement) {
            return inviteElement.getAttribute('data-invite-id');
        }

        return null;
    }

    /**
     * Obtém token CSRF
     */
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name=csrf-token]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    /**
     * Formata valor como moeda
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    /**
     * Obtém cor do Bootstrap para tipo de notificação
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
     * Limpa recursos
     */
    destroy() {
        this.stopPolling();
        
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.remove();
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Só inicializar em páginas de convite
    if (window.location.pathname.includes('/convite/') || 
        document.querySelector('[data-proposal-status]')) {
        window.realTimeUpdates = new RealTimeUpdates();
    }
});

// Limpar recursos quando a página for descarregada
window.addEventListener('beforeunload', function() {
    if (window.realTimeUpdates) {
        window.realTimeUpdates.destroy();
    }
});