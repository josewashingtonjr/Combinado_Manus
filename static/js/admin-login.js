/* =============================================================================
   ADMIN LOGIN JAVASCRIPT - COMBINADO
   ============================================================================= */

document.addEventListener('DOMContentLoaded', function() {
    setupAdminLoginForm();
});

/**
 * Configura o formulário de login administrativo
 */
function setupAdminLoginForm() {
    const form = document.getElementById('adminLoginForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleAdminLogin(form);
    });
    
    // Validação em tempo real
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(input);
        });
        
        input.addEventListener('input', function() {
            clearFieldError(input);
        });
    });
}

/**
 * Processa login administrativo
 */
function handleAdminLogin(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    console.log('Tentativa de login admin:', data);
    
    // Validar campos
    if (!validateForm(form)) {
        console.log('Validação falhou');
        return;
    }
    
    // Desabilitar botão de submit
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Entrando...';
    
    // Enviar dados via AJAX
    fetch('/auth/admin-login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('Status da resposta:', response.status);
        return response.json();
    })
    .then(result => {
        console.log('Resposta do servidor:', result);
        if (result.ok) {
            // Salvar token no localStorage
            localStorage.setItem('admin_token', result.token);
            localStorage.setItem('admin_data', JSON.stringify(result.user));
            
            // Mostrar sucesso e redirecionar
            showSuccessMessage(form, 'Login realizado! Redirecionando...');
            setTimeout(() => {
                window.location.href = '/admin/dashboard';
            }, 1000);
        } else {
            // Mostrar erro
            showFormError(form, result.error);
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        showFormError(form, 'Erro de conexão');
        
        // Log detalhado para debug
        console.log('Detalhes do erro:', {
            message: error.message,
            stack: error.stack
        });
    })
    .finally(() => {
        // Reabilitar botão
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

/**
 * Valida um formulário completo
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Valida um campo específico
 */
function validateField(field) {
    const value = field.value.trim();
    const errorElement = field.parentElement.querySelector('.form__error');
    
    // Limpar erro anterior
    clearFieldError(field);
    
    // Validações
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, errorElement, 'Este campo é obrigatório');
        return false;
    }
    
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, errorElement, 'Digite um e-mail válido');
        return false;
    }
    
    if (field.type === 'password' && value && value.length < 3) {
        showFieldError(field, errorElement, 'Senha muito curta');
        return false;
    }
    
    return true;
}

/**
 * Mostra erro em um campo
 */
function showFieldError(field, errorElement, message) {
    field.classList.add('error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('active');
    }
}

/**
 * Limpa erro de um campo
 */
function clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentElement.querySelector('.form__error');
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.classList.remove('active');
    }
}

/**
 * Valida formato de e-mail
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Mostra mensagem de sucesso
 */
function showSuccessMessage(form, message = '✓ Sucesso!') {
    const submitButton = form.querySelector('button[type="submit"]');
    
    submitButton.textContent = message;
    submitButton.style.backgroundColor = 'var(--semantic-success)';
}

/**
 * Mostra mensagem de erro no formulário
 */
function showFormError(form, message) {
    // Criar ou atualizar div de erro
    let errorDiv = form.querySelector('.alert-error');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'alert-error';
        errorDiv.style.cssText = `
            padding: 12px 16px;
            margin-bottom: 16px;
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #ef4444;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        `;
        form.insertBefore(errorDiv, form.firstChild);
    }
    
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message || 'E-mail ou senha incorretos'}`;
    errorDiv.style.display = 'flex';
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}
