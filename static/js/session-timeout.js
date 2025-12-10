/**
 * Gerenciador de Timeout de Sessão
 * Monitora o status da sessão e exibe avisos de expiração
 */

class SessionTimeoutManager {
    constructor() {
        this.checkInterval = 60000; // Verificar a cada 1 minuto
        this.warningShown = false;
        this.intervalId = null;
        this.warningModal = null;
        
        this.init();
    }
    
    init() {
        // Iniciar monitoramento apenas se houver sessão ativa
        if (this.hasActiveSession()) {
            this.startMonitoring();
            this.createWarningModal();
        }
    }
    
    hasActiveSession() {
        // Verificar se há indicadores de sessão ativa na página
        return document.body.dataset.userLoggedIn === 'true' || 
               document.body.dataset.adminLoggedIn === 'true' ||
               window.location.pathname.includes('/admin/') ||
               window.location.pathname.includes('/cliente/') ||
               window.location.pathname.includes('/prestador/');
    }
    
    startMonitoring() {
        // Verificar imediatamente
        this.checkSessionStatus();
        
        // Configurar verificação periódica
        this.intervalId = setInterval(() => {
            this.checkSessionStatus();
        }, this.checkInterval);
        
        console.log('🕐 Monitoramento de sessão iniciado');
    }
    
    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('🛑 Monitoramento de sessão parado');
        }
    }
    
    async checkSessionStatus() {
        try {
            const response = await fetch('/session/check-status', {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.authenticated) {
                // Sessão expirada ou inválida
                this.handleSessionExpired(data);
                return;
            }
            
            // Verificar se deve mostrar aviso
            if (data.should_warn && !this.warningShown) {
                this.showWarning(data.minutes_remaining);
            } else if (!data.should_warn && this.warningShown) {
                // Sessão foi estendida, esconder aviso
                this.hideWarning();
            }
            
        } catch (error) {
            console.error('Erro ao verificar status da sessão:', error);
            // Em caso de erro de rede, não fazer nada drástico
        }
    }
    
    handleSessionExpired(data) {
        console.log('⚠️ Sessão expirada:', data.message);
        
        // Parar monitoramento
        this.stopMonitoring();
        
        // Mostrar mensagem e redirecionar
        this.showExpirationMessage(data.message || 'Sua sessão expirou');
        
        // Redirecionar após um breve delay
        setTimeout(() => {
            // Determinar URL de redirecionamento baseado na página atual
            let redirectUrl = '/auth/login';
            if (window.location.pathname.includes('/admin/')) {
                redirectUrl = '/auth/admin-login';
            }
            
            window.location.href = redirectUrl;
        }, 3000);
    }
    
    showWarning(minutesRemaining) {
        this.warningShown = true;
        
        const modal = this.getWarningModal();
        const messageEl = modal.querySelector('.timeout-message');
        const countdownEl = modal.querySelector('.timeout-countdown');
        
        messageEl.textContent = `Sua sessão expirará em ${minutesRemaining} minuto(s) por inatividade.`;
        countdownEl.textContent = `${minutesRemaining} minuto(s)`;
        
        // Mostrar modal
        modal.style.display = 'block';
        modal.classList.add('show');
        
        console.log(`⚠️ Aviso de expiração mostrado: ${minutesRemaining} minutos restantes`);
    }
    
    hideWarning() {
        this.warningShown = false;
        
        const modal = this.getWarningModal();
        modal.style.display = 'none';
        modal.classList.remove('show');
        
        console.log('✅ Aviso de expiração escondido');
    }
    
    async extendSession() {
        try {
            const response = await fetch('/session/extend', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                console.log('✅ Sessão estendida com sucesso');
                this.hideWarning();
                
                // Mostrar feedback positivo
                this.showNotification('Sessão estendida com sucesso!', 'success');
                
                return true;
            } else {
                console.error('Erro ao estender sessão:', data.message);
                this.showNotification('Erro ao estender sessão', 'error');
                return false;
            }
            
        } catch (error) {
            console.error('Erro na requisição de extensão:', error);
            this.showNotification('Erro de conexão', 'error');
            return false;
        }
    }
    
    createWarningModal() {
        // Verificar se modal já existe
        if (document.getElementById('session-timeout-modal')) {
            return;
        }
        
        const modalHtml = `
            <div id="session-timeout-modal" class="session-timeout-modal" style="display: none;">
                <div class="session-timeout-overlay"></div>
                <div class="session-timeout-content">
                    <div class="session-timeout-header">
                        <h3>⚠️ Aviso de Sessão</h3>
                    </div>
                    <div class="session-timeout-body">
                        <p class="timeout-message">Sua sessão expirará em breve por inatividade.</p>
                        <p class="timeout-countdown-label">Tempo restante: <strong class="timeout-countdown">5 minutos</strong></p>
                        <p class="timeout-question">Deseja estender sua sessão?</p>
                    </div>
                    <div class="session-timeout-actions">
                        <button id="extend-session-btn" class="btn btn-primary">
                            Sim, estender sessão
                        </button>
                        <button id="logout-session-btn" class="btn btn-secondary">
                            Não, fazer logout
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Adicionar modal ao body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Adicionar event listeners
        this.setupModalEvents();
        
        // Adicionar estilos CSS
        this.addModalStyles();
    }
    
    setupModalEvents() {
        const extendBtn = document.getElementById('extend-session-btn');
        const logoutBtn = document.getElementById('logout-session-btn');
        
        if (extendBtn) {
            extendBtn.addEventListener('click', async () => {
                const originalText = extendBtn.textContent;
                extendBtn.disabled = true;
                extendBtn.textContent = 'Estendendo...';
                
                const success = await this.extendSession();
                
                // Sempre reabilitar o botão após a tentativa
                extendBtn.disabled = false;
                
                if (success) {
                    extendBtn.textContent = originalText;
                } else {
                    extendBtn.textContent = 'Tentar novamente';
                    // Restaurar texto original após 2 segundos
                    setTimeout(() => {
                        extendBtn.textContent = originalText;
                    }, 2000);
                }
            });
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                // Redirecionar para logout
                let logoutUrl = '/auth/logout';
                if (window.location.pathname.includes('/admin/')) {
                    logoutUrl = '/auth/admin-logout';
                }
                
                window.location.href = logoutUrl;
            });
        }
    }
    
    getWarningModal() {
        return document.getElementById('session-timeout-modal');
    }
    
    showExpirationMessage(message) {
        // Criar notificação de expiração
        const notification = document.createElement('div');
        notification.className = 'session-expired-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <strong>⚠️ Sessão Expirada</strong>
                <p>${message}</p>
                <p>Redirecionando para login...</p>
            </div>
        `;
        
        // Adicionar estilos inline
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `session-notification session-notification-${type}`;
        notification.textContent = message;
        
        // Estilos baseados no tipo
        const colors = {
            success: { bg: '#d4edda', color: '#155724', border: '#c3e6cb' },
            error: { bg: '#f8d7da', color: '#721c24', border: '#f5c6cb' },
            info: { bg: '#d1ecf1', color: '#0c5460', border: '#bee5eb' }
        };
        
        const style = colors[type] || colors.info;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${style.bg};
            color: ${style.color};
            border: 1px solid ${style.border};
            border-radius: 4px;
            padding: 10px 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 9999;
            max-width: 300px;
        `;
        
        document.body.appendChild(notification);
        
        // Remover após 3 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    addModalStyles() {
        // Verificar se estilos já foram adicionados
        if (document.getElementById('session-timeout-styles')) {
            return;
        }
        
        const styles = `
            <style id="session-timeout-styles">
                .session-timeout-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                }
                
                .session-timeout-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                }
                
                .session-timeout-content {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                    max-width: 500px;
                    width: 90%;
                }
                
                .session-timeout-header {
                    padding: 20px 20px 10px;
                    border-bottom: 1px solid #eee;
                }
                
                .session-timeout-header h3 {
                    margin: 0;
                    color: #856404;
                }
                
                .session-timeout-body {
                    padding: 20px;
                }
                
                .session-timeout-body p {
                    margin: 10px 0;
                }
                
                .timeout-countdown {
                    color: #dc3545;
                    font-weight: bold;
                }
                
                .session-timeout-actions {
                    padding: 10px 20px 20px;
                    text-align: right;
                }
                
                .session-timeout-actions .btn {
                    margin-left: 10px;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }
                
                .session-timeout-actions .btn-primary {
                    background: #007bff;
                    color: white;
                }
                
                .session-timeout-actions .btn-primary:hover {
                    background: #0056b3;
                }
                
                .session-timeout-actions .btn-secondary {
                    background: #6c757d;
                    color: white;
                }
                
                .session-timeout-actions .btn-secondary:hover {
                    background: #545b62;
                }
                
                .session-timeout-actions .btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Aguardar um pouco para garantir que a página carregou completamente
    setTimeout(() => {
        window.sessionTimeoutManager = new SessionTimeoutManager();
    }, 1000);
});

// Exportar para uso global
window.SessionTimeoutManager = SessionTimeoutManager;