/**
 * Exemplos de Integração do Toast Feedback
 * Demonstra como usar o sistema de toast em cenários reais
 */

// ============================================
// EXEMPLO 1: Formulário de Convite
// ============================================

function handleConviteSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Mostra loading
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toast.success('Convite enviado com sucesso!');
            form.reset();
            // Redireciona após 2 segundos
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 2000);
        } else {
            toast.error(data.message || 'Erro ao enviar convite');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        toast.error('Erro de conexão. Tente novamente.');
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar Convite';
    });
}

// ============================================
// EXEMPLO 2: Aceitar/Recusar Convite
// ============================================

function aceitarConvite(conviteId) {
    // Confirmação
    if (!confirm('Deseja realmente aceitar este convite?')) {
        return;
    }
    
    // Mostra toast de processamento
    const toastId = toast.info('Processando...', 0); // Permanente
    
    fetch(`/prestador/aceitar-convite/${conviteId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        // Esconde toast de processamento
        toast.hide(toastId);
        
        if (data.success) {
            toast.success('Convite aceito! Redirecionando para pré-ordem...');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1500);
        } else {
            toast.error(data.message || 'Erro ao aceitar convite');
        }
    })
    .catch(error => {
        toast.hide(toastId);
        console.error('Erro:', error);
        toast.error('Erro de conexão. Tente novamente.');
    });
}

function recusarConvite(conviteId) {
    const motivo = prompt('Motivo da recusa (opcional):');
    
    const toastId = toast.info('Processando...', 0);
    
    fetch(`/prestador/recusar-convite/${conviteId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ motivo: motivo })
    })
    .then(response => response.json())
    .then(data => {
        toast.hide(toastId);
        
        if (data.success) {
            toast.success('Convite recusado');
            // Remove o card do convite da tela
            document.querySelector(`[data-convite-id="${conviteId}"]`)?.remove();
        } else {
            toast.error(data.message || 'Erro ao recusar convite');
        }
    })
    .catch(error => {
        toast.hide(toastId);
        console.error('Erro:', error);
        toast.error('Erro de conexão. Tente novamente.');
    });
}

// ============================================
// EXEMPLO 3: Validação de Formulário
// ============================================

function validateForm(form) {
    const errors = [];
    
    // Valida campos obrigatórios
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            errors.push(`O campo "${field.labels[0]?.textContent || field.name}" é obrigatório`);
        }
    });
    
    // Valida email
    const emailField = form.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailField.value)) {
            errors.push('Email inválido');
        }
    }
    
    // Valida telefone
    const phoneField = form.querySelector('input[type="tel"]');
    if (phoneField && phoneField.value) {
        const phoneRegex = /^\(\d{2}\)\s?\d{4,5}-?\d{4}$/;
        if (!phoneRegex.test(phoneField.value)) {
            errors.push('Telefone inválido. Use o formato (XX) XXXXX-XXXX');
        }
    }
    
    // Mostra erros
    if (errors.length > 0) {
        errors.forEach(error => {
            toast.error(error, 3000);
        });
        return false;
    }
    
    return true;
}

// ============================================
// EXEMPLO 4: Upload de Arquivo
// ============================================

function handleFileUpload(input) {
    const file = input.files[0];
    
    if (!file) {
        return;
    }
    
    // Valida tamanho (5MB)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
        toast.error('Arquivo muito grande. Tamanho máximo: 5MB');
        input.value = '';
        return;
    }
    
    // Valida tipo
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        toast.error('Tipo de arquivo não permitido. Use JPG, PNG, GIF ou PDF');
        input.value = '';
        return;
    }
    
    toast.success(`Arquivo "${file.name}" selecionado`);
    
    // Upload
    const formData = new FormData();
    formData.append('file', file);
    
    const toastId = toast.info('Enviando arquivo...', 0);
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        toast.hide(toastId);
        
        if (data.success) {
            toast.success('Arquivo enviado com sucesso!');
        } else {
            toast.error(data.message || 'Erro ao enviar arquivo');
        }
    })
    .catch(error => {
        toast.hide(toastId);
        console.error('Erro:', error);
        toast.error('Erro ao enviar arquivo');
    });
}

// ============================================
// EXEMPLO 5: Operações de Carteira
// ============================================

function solicitarSaque(valor) {
    if (valor <= 0) {
        toast.error('Valor inválido');
        return;
    }
    
    const toastId = toast.info('Processando solicitação...', 0);
    
    fetch('/prestador/solicitar-saque', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ valor: valor })
    })
    .then(response => response.json())
    .then(data => {
        toast.hide(toastId);
        
        if (data.success) {
            toast.success(`Saque de R$ ${valor.toFixed(2)} solicitado com sucesso!`);
            // Atualiza saldo na tela
            updateSaldoDisplay(data.novo_saldo);
        } else {
            toast.error(data.message || 'Erro ao solicitar saque');
        }
    })
    .catch(error => {
        toast.hide(toastId);
        console.error('Erro:', error);
        toast.error('Erro de conexão. Tente novamente.');
    });
}

function adicionarSaldo(valor) {
    if (valor <= 0) {
        toast.error('Valor inválido');
        return;
    }
    
    toast.info('Redirecionando para pagamento...', 2000);
    
    // Redireciona para gateway de pagamento
    setTimeout(() => {
        window.location.href = `/pagamento/adicionar-saldo?valor=${valor}`;
    }, 2000);
}

// ============================================
// EXEMPLO 6: Notificações em Tempo Real
// ============================================

function setupRealtimeNotifications() {
    // Simula WebSocket ou polling
    setInterval(() => {
        fetch('/api/notificacoes/novas')
            .then(response => response.json())
            .then(data => {
                if (data.notificacoes && data.notificacoes.length > 0) {
                    data.notificacoes.forEach(notif => {
                        const type = notif.tipo || 'info';
                        toast[type](notif.mensagem, 7000);
                    });
                }
            })
            .catch(error => {
                console.error('Erro ao buscar notificações:', error);
            });
    }, 30000); // A cada 30 segundos
}

// ============================================
// EXEMPLO 7: Copiar para Área de Transferência
// ============================================

function copyToClipboard(text, label = 'Texto') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                toast.success(`${label} copiado para área de transferência!`, 2000);
            })
            .catch(err => {
                console.error('Erro ao copiar:', err);
                toast.error('Erro ao copiar');
            });
    } else {
        // Fallback para navegadores antigos
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            toast.success(`${label} copiado!`, 2000);
        } catch (err) {
            console.error('Erro ao copiar:', err);
            toast.error('Erro ao copiar');
        }
        
        document.body.removeChild(textarea);
    }
}

// ============================================
// EXEMPLO 8: Confirmação de Ações Destrutivas
// ============================================

function deleteItem(itemId, itemName) {
    // Mostra toast de confirmação customizado
    const confirmToastId = toast.warning(
        `Tem certeza que deseja excluir "${itemName}"? Esta ação não pode ser desfeita.`,
        0 // Permanente
    );
    
    // Adiciona botões de confirmação ao toast
    const toastElement = document.getElementById(confirmToastId);
    if (toastElement) {
        const messageDiv = toastElement.querySelector('.toast-message');
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.style.marginTop = '10px';
        buttonsDiv.style.display = 'flex';
        buttonsDiv.style.gap = '8px';
        
        const confirmBtn = document.createElement('button');
        confirmBtn.textContent = 'Confirmar';
        confirmBtn.className = 'btn btn-sm btn-danger';
        confirmBtn.onclick = () => {
            toast.hide(confirmToastId);
            performDelete(itemId, itemName);
        };
        
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancelar';
        cancelBtn.className = 'btn btn-sm btn-secondary';
        cancelBtn.onclick = () => {
            toast.hide(confirmToastId);
            toast.info('Ação cancelada');
        };
        
        buttonsDiv.appendChild(confirmBtn);
        buttonsDiv.appendChild(cancelBtn);
        messageDiv.appendChild(buttonsDiv);
    }
}

function performDelete(itemId, itemName) {
    const toastId = toast.info('Excluindo...', 0);
    
    fetch(`/api/items/${itemId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        }
    })
    .then(response => response.json())
    .then(data => {
        toast.hide(toastId);
        
        if (data.success) {
            toast.success(`"${itemName}" excluído com sucesso`);
            // Remove elemento da tela
            document.querySelector(`[data-item-id="${itemId}"]`)?.remove();
        } else {
            toast.error(data.message || 'Erro ao excluir');
        }
    })
    .catch(error => {
        toast.hide(toastId);
        console.error('Erro:', error);
        toast.error('Erro de conexão');
    });
}

// ============================================
// EXEMPLO 9: Feedback de Salvamento Automático
// ============================================

let autoSaveTimeout;

function setupAutoSave(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(autoSaveTimeout);
            
            autoSaveTimeout = setTimeout(() => {
                autoSave(form);
            }, 2000); // Salva após 2 segundos de inatividade
        });
    });
}

function autoSave(form) {
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toast.success('Rascunho salvo automaticamente', 2000);
        }
    })
    .catch(error => {
        console.error('Erro no auto-save:', error);
        // Não mostra erro para não incomodar o usuário
    });
}

// ============================================
// INICIALIZAÇÃO
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Toast Integration Examples carregado');
    
    // Exemplo: Setup de notificações em tempo real
    // setupRealtimeNotifications();
    
    // Exemplo: Setup de auto-save em formulários
    // const forms = document.querySelectorAll('form[data-auto-save]');
    // forms.forEach(form => setupAutoSave(form));
});
