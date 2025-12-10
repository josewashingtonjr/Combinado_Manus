/**
 * Sistema de Atualizações em Tempo Real para Dashboards
 * Implementa SSE (Server-Sent Events) para atualizar ordens e saldo automaticamente
 */

class DashboardRealtime {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        this.pollingInterval = null;
        this.pollingFallbackActive = false;
        
        this.init();
    }

    /**
     * Inicializa o sistema de tempo real
     */
    init() {
        // Verificar se estamos em uma página de dashboard
        if (!this.isDashboardPage()) {
            return;
        }

        // Tentar conectar via SSE
        this.connectSSE();
        
        // Configurar manipuladores de visibilidade
        this.setupVisibilityHandling();
        
        // Configurar manipuladores de rede
        this.setupNetworkHandling();
    }

    /**
     * Verifica se estamos em uma página de dashboard
     */
    isDashboardPage() {
        const path = window.location.pathname;
        return path.includes('/cliente/dashboard') || 
               path.includes('/prestador/dashboard') ||
               document.querySelector('[data-dashboard-realtime]');
    }

    /**
     * Conecta ao stream SSE
     */
    connectSSE() {
        // Fechar conexão existente se houver
        if (this.eventSource) {
            this.eventSource.close();
        }

        try {
            // Criar nova conexão SSE
            this.eventSource = new EventSource('/realtime/dashboard/stream');
            
            // Manipulador de conexão aberta
            this.eventSource.addEventListener('open', () => {
                console.log('✅ Conexão SSE estabelecida');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.setConnectionStatus(true);
                
                // Parar polling se estava ativo
                if (this.pollingFallbackActive) {
                    this.stopPolling();
                }
            });
            
            // Manipulador de mensagens
            this.eventSource.addEventListener('message', (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleUpdate(data);
                } catch (error) {
                    console.error('Erro ao processar mensagem SSE:', error);
                }
            });
            
            // Manipulador de heartbeat
            this.eventSource.addEventListener('heartbeat', (event) => {
                // Apenas manter conexão viva
                console.debug('💓 Heartbeat recebido');
            });
            
            // Manipulador de erros
            this.eventSource.addEventListener('error', (event) => {
                console.error('❌ Erro na conexão SSE:', event);
                this.handleConnectionError();
            });
            
        } catch (error) {
            console.error('Erro ao criar conexão SSE:', error);
            this.handleConnectionError();
        }
    }

    /**
     * Manipula atualizações recebidas
     */
    handleUpdate(data) {
        console.log('📨 Atualização recebida:', data);
        
        switch (data.type) {
            case 'connected':
                this.showNotification('Conectado ao sistema de atualizações', 'success');
                break;
                
            case 'balance_updated':
                this.handleBalanceUpdate(data.data);
                break;
                
            case 'orders_updated':
                this.handleOrdersUpdate(data.data);
                break;
                
            case 'order_created':
                this.handleOrderCreated(data.data, data.message);
                break;
                
            case 'order_status_changed':
                this.handleOrderStatusChanged(data.data, data.message);
                break;
                
            case 'error':
                console.error('Erro do servidor:', data.message);
                if (data.retry) {
                    this.handleConnectionError();
                }
                break;
                
            case 'disconnected':
                console.log('Desconectado do servidor');
                this.handleConnectionError();
                break;
                
            default:
                console.log('Tipo de atualização desconhecido:', data.type);
        }
    }

    /**
     * Manipula atualização de saldo
     */
    handleBalanceUpdate(data) {
        console.log('💰 Atualizando saldo:', data);
        
        // Atualizar saldo disponível
        const availableElements = document.querySelectorAll('[data-balance-available]');
        availableElements.forEach(element => {
            element.textContent = this.formatCurrency(data.available);
            element.setAttribute('data-balance-available', data.available);
        });
        
        // Atualizar saldo bloqueado
        const blockedElements = document.querySelectorAll('[data-balance-blocked]');
        blockedElements.forEach(element => {
            element.textContent = this.formatCurrency(data.blocked);
            element.setAttribute('data-balance-blocked', data.blocked);
        });
        
        // Atualizar saldo total
        const totalElements = document.querySelectorAll('[data-balance-total]');
        totalElements.forEach(element => {
            element.textContent = this.formatCurrency(data.total);
            element.setAttribute('data-balance-total', data.total);
        });
        
        // Adicionar animação de atualização
        this.animateUpdate(availableElements);
        this.animateUpdate(blockedElements);
        
        // Mostrar notificação
        this.showNotification('💰 Saldo atualizado', 'info');
    }

    /**
     * Manipula atualização de ordens
     */
    handleOrdersUpdate(data) {
        console.log('📋 Atualizando ordens:', data);
        
        // Atualizar contador de ordens
        const countElements = document.querySelectorAll('[data-orders-count]');
        countElements.forEach(element => {
            element.textContent = data.count;
            element.setAttribute('data-orders-count', data.count);
        });
        
        // Recarregar lista de ordens
        this.reloadOrdersList();
    }

    /**
     * Manipula criação de nova ordem
     */
    handleOrderCreated(data, message) {
        console.log('✨ Nova ordem criada:', data);
        
        // Mostrar notificação destacada
        this.showNotification(message || `Nova ordem #${data.id} criada!`, 'success', 5000);
        
        // Recarregar lista de ordens
        this.reloadOrdersList();
        
        // Atualizar contadores
        this.updateOrdersCount();
    }

    /**
     * Manipula mudança de status de ordem
     */
    handleOrderStatusChanged(data, message) {
        console.log('🔄 Status de ordem mudou:', data);
        
        // Mostrar notificação
        this.showNotification(message || `Ordem #${data.order_id} atualizada`, 'info');
        
        // Atualizar elemento específico da ordem se existir
        const orderElement = document.querySelector(`[data-order-id="${data.order_id}"]`);
        if (orderElement) {
            // Atualizar badge de status
            const statusBadge = orderElement.querySelector('.order-status-badge');
            if (statusBadge) {
                statusBadge.textContent = this.formatStatus(data.new_status);
                statusBadge.className = `order-status-badge badge ${this.getStatusClass(data.new_status)}`;
            }
            
            // Adicionar animação
            this.animateUpdate([orderElement]);
        } else {
            // Se não encontrou o elemento, recarregar lista
            this.reloadOrdersList();
        }
    }

    /**
     * Recarrega lista de ordens via AJAX
     */
    reloadOrdersList() {
        const ordersContainer = document.querySelector('[data-orders-list]');
        if (!ordersContainer) {
            return;
        }

        // Adicionar indicador de carregamento
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'text-center py-3';
        loadingIndicator.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';
        
        // Mostrar loading
        ordersContainer.style.opacity = '0.6';
        
        // Fazer requisição para recarregar
        const currentPath = window.location.pathname;
        fetch(currentPath, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Extrair apenas a seção de ordens do HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newOrdersList = doc.querySelector('[data-orders-list]');
            
            if (newOrdersList) {
                ordersContainer.innerHTML = newOrdersList.innerHTML;
                this.animateUpdate([ordersContainer]);
            }
            
            ordersContainer.style.opacity = '1';
        })
        .catch(error => {
            console.error('Erro ao recarregar ordens:', error);
            ordersContainer.style.opacity = '1';
        });
    }

    /**
     * Atualiza contador de ordens
     */
    updateOrdersCount() {
        // Contar ordens visíveis na página
        const orderElements = document.querySelectorAll('[data-order-id]');
        const count = orderElements.length;
        
        const countElements = document.querySelectorAll('[data-orders-count]');
        countElements.forEach(element => {
            element.textContent = count;
            element.setAttribute('data-orders-count', count);
        });
    }

    /**
     * Adiciona animação de atualização
     */
    animateUpdate(elements) {
        elements.forEach(element => {
            element.classList.add('updated-flash');
            setTimeout(() => {
                element.classList.remove('updated-flash');
            }, 1000);
        });
    }

    /**
     * Manipula erro de conexão
     */
    handleConnectionError() {
        this.isConnected = false;
        this.setConnectionStatus(false);
        
        // Fechar conexão SSE se existir
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            // Tentar reconectar
            const delay = this.reconnectDelay * this.reconnectAttempts;
            console.log(`🔄 Tentando reconectar em ${delay}ms (tentativa ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectSSE();
            }, delay);
        } else {
            // Ativar fallback de polling
            console.log('⚠️ Máximo de tentativas de reconexão atingido. Ativando polling...');
            this.showNotification('Modo offline: atualizações manuais disponíveis', 'warning');
            this.startPolling();
        }
    }

    /**
     * Inicia polling como fallback
     */
    startPolling() {
        if (this.pollingInterval) {
            return;
        }

        this.pollingFallbackActive = true;
        
        this.pollingInterval = setInterval(() => {
            if (!document.hidden) {
                this.checkUpdatesViaPolling();
            }
        }, 30000); // Verificar a cada 30 segundos
        
        console.log('📡 Polling iniciado como fallback');
    }

    /**
     * Para polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            this.pollingFallbackActive = false;
            console.log('📡 Polling parado');
        }
    }

    /**
     * Verifica atualizações via polling
     */
    async checkUpdatesViaPolling() {
        try {
            const response = await fetch('/realtime/dashboard/check-updates', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.has_updates) {
                // Processar cada atualização
                data.updates.forEach(update => {
                    this.handleUpdate(update);
                });
            }
            
        } catch (error) {
            console.error('Erro ao verificar atualizações via polling:', error);
        }
    }

    /**
     * Define status de conexão
     */
    setConnectionStatus(isOnline) {
        const statusElement = document.getElementById('realtime-status');
        
        if (statusElement) {
            if (isOnline) {
                statusElement.className = 'realtime-status online';
                statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> Online';
                statusElement.title = 'Atualizações em tempo real ativas';
            } else {
                statusElement.className = 'realtime-status offline';
                statusElement.innerHTML = '<i class="fas fa-circle text-warning"></i> Offline';
                statusElement.title = 'Atualizações em tempo real desconectadas';
            }
        }
    }

    /**
     * Configura manipulação de visibilidade da página
     */
    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('📱 Página oculta - pausando atualizações');
            } else {
                console.log('📱 Página visível - retomando atualizações');
                
                // Se estava usando SSE, verificar conexão
                if (!this.pollingFallbackActive && !this.isConnected) {
                    this.connectSSE();
                }
                
                // Verificar atualizações imediatamente
                if (this.pollingFallbackActive) {
                    this.checkUpdatesViaPolling();
                }
            }
        });
    }

    /**
     * Configura manipulação de rede
     */
    setupNetworkHandling() {
        window.addEventListener('online', () => {
            console.log('🌐 Conexão restaurada');
            this.showNotification('Conexão restaurada', 'success');
            this.reconnectAttempts = 0;
            
            if (this.pollingFallbackActive) {
                this.stopPolling();
            }
            
            this.connectSSE();
        });

        window.addEventListener('offline', () => {
            console.log('📡 Sem conexão com a internet');
            this.showNotification('Sem conexão com a internet', 'warning');
            
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            this.setConnectionStatus(false);
        });
    }

    /**
     * Mostra notificação
     */
    showNotification(message, type = 'info', duration = 3000) {
        // Criar elemento de notificação
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapColor(type)} alert-dismissible fade show dashboard-notification`;
        notification.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; max-width: 350px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remover
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }
        }, duration);
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
     * Formata status para exibição
     */
    formatStatus(status) {
        const statusMap = {
            'aceita': 'Aceita',
            'em_andamento': 'Em Andamento',
            'aguardando_confirmacao': 'Aguardando Confirmação',
            'concluida': 'Concluída',
            'cancelada': 'Cancelada',
            'em_contestacao': 'Em Contestação'
        };
        return statusMap[status] || status;
    }

    /**
     * Obtém classe CSS para status
     */
    getStatusClass(status) {
        const classMap = {
            'aceita': 'bg-info',
            'em_andamento': 'bg-primary',
            'aguardando_confirmacao': 'bg-warning',
            'concluida': 'bg-success',
            'cancelada': 'bg-secondary',
            'em_contestacao': 'bg-danger'
        };
        return classMap[status] || 'bg-secondary';
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
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.stopPolling();
        
        console.log('🧹 Recursos de tempo real limpos');
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Só inicializar em páginas de dashboard
    if (window.location.pathname.includes('/dashboard') || 
        document.querySelector('[data-dashboard-realtime]')) {
        window.dashboardRealtime = new DashboardRealtime();
    }
});

// Limpar recursos quando a página for descarregada
window.addEventListener('beforeunload', function() {
    if (window.dashboardRealtime) {
        window.dashboardRealtime.destroy();
    }
});

// Adicionar botão de atualização manual
document.addEventListener('DOMContentLoaded', function() {
    const dashboardContainer = document.querySelector('[data-dashboard-realtime]');
    if (dashboardContainer) {
        // Criar botão de atualização manual
        const refreshButton = document.createElement('button');
        refreshButton.className = 'btn btn-sm btn-outline-primary position-fixed';
        refreshButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;';
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.title = 'Atualizar dashboard manualmente';
        refreshButton.onclick = function() {
            refreshButton.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
            
            fetch('/realtime/dashboard/refresh', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(() => {
                location.reload();
            })
            .catch(error => {
                console.error('Erro ao atualizar:', error);
                refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
            });
        };
        
        document.body.appendChild(refreshButton);
    }
});
