/* =============================================================================
   HOME PAGE JAVASCRIPT - COMBINADO
   ============================================================================= */

// Constantes
const APP_VERSION = '0.1.0';

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    setupFormValidation();
    setupFAQ();
});

/**
 * Inicializa a aplicação
 */
function initializeApp() {
    // Definir versão do sistema
    const versionElement = document.getElementById('appVersion');
    if (versionElement) {
        versionElement.textContent = APP_VERSION;
    }
    
    // Configurar acessibilidade
    setupAccessibility();
}

/**
 * Configura event listeners
 */
function setupEventListeners() {
    // Menu mobile
    const navToggle = document.querySelector('.nav__toggle');
    const navMenu = document.querySelector('.nav__menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', !isExpanded);
            navMenu.classList.toggle('active');
        });
    }
    
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Fechar modal ao clicar fora
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal__overlay')) {
            const modal = e.target.closest('.modal');
            if (modal) {
                closeModal(modal.id);
            }
        }
    });
    
    // Fechar modal com ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                closeModal(activeModal.id);
            }
        }
    });
}

/**
 * Configura validação de formulários
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            validateForm(form);
        });
        
        // Validação em tempo real
        const inputs = form.querySelectorAll('.form__input');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(input);
            });
        });
        
        // Validação de checkbox
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                validateField(checkbox);
            });
        });
    });
}

/**
 * Valida um formulário completo
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('.form__input, input[type="checkbox"]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    if (isValid) {
        handleFormSubmit(form);
    }
}

/**
 * Valida um campo específico
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    const errorElement = document.getElementById(field.getAttribute('aria-describedby')?.split(' ')[0]);
    
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
    
    if (field.type === 'password' && value && value.length < 8) {
        showFieldError(field, errorElement, 'A senha deve ter pelo menos 8 caracteres');
        return false;
    }
    
    if (field.type === 'checkbox' && field.hasAttribute('required') && !field.checked) {
        showFieldError(field, errorElement, 'Você deve aceitar os termos');
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
    const errorElement = document.getElementById(field.getAttribute('aria-describedby')?.split(' ')[0]);
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
 * Processa envio do formulário
 */
function handleFormSubmit(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const formId = form.id;
    
    // Determinar endpoint baseado no formulário
    let endpoint = '';
    if (formId === 'loginForm') {
        endpoint = '/auth/login';
    } else if (formId === 'registerForm') {
        endpoint = '/auth/register';
    } else {
        console.error('Formulário não reconhecido:', formId);
        return;
    }
    
    // Desabilitar botão de submit
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Processando...';
    
    // Enviar dados via AJAX
    console.log('Enviando para:', endpoint);
    console.log('Dados:', data);
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('Status da resposta:', response.status);
        console.log('Response OK:', response.ok);
        return response.json();
    })
    .then(result => {
        console.log('Resultado:', result);
        if (result.ok) {
            if (formId === 'loginForm') {
                // Salvar token no localStorage
                localStorage.setItem('auth_token', result.token);
                localStorage.setItem('user_data', JSON.stringify(result.user));
                
                // Redirecionar baseado no papel
                const userRole = result.user.role;
                let redirectUrl = '';
                
                if (userRole === 'admin') {
                    redirectUrl = '/admin/dashboard';
                } else if (userRole === 'cliente') {
                    redirectUrl = '/app/home';
                } else if (userRole === 'prestador') {
                    redirectUrl = '/prestador/dashboard';
                } else {
                    redirectUrl = '/app/home'; // fallback
                }
                
                // Mostrar sucesso e redirecionar
                showSuccessMessage(form, 'Login realizado! Redirecionando...');
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000);
                
            } else if (formId === 'registerForm') {
                // Mostrar sucesso para registro
                showSuccessMessage(form, result.message || 'Conta criada com sucesso!');
                
                // Fechar modal e redirecionar para login
                setTimeout(() => {
                    closeModal('registerModal');
                    // Mostrar alerta de sucesso
                    alert('✅ ' + (result.message || 'Conta criada com sucesso! Faça login para continuar.'));
                    // Redirecionar para página de login
                    window.location.href = '/auth/login';
                }, 1500);
            }
        } else {
            // Mostrar erro
            showFormError(form, result.error);
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        showFormError(form, 'Erro de conexão. Tente novamente.');
    })
    .finally(() => {
        // Reabilitar botão
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    });
}

/**
 * Mostra mensagem de sucesso
 */
function showSuccessMessage(form, message = '✓ Sucesso!') {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    submitButton.textContent = message;
    submitButton.style.backgroundColor = 'var(--semantic-success)';
    
    setTimeout(() => {
        submitButton.textContent = originalText;
        submitButton.style.backgroundColor = '';
    }, 2000);
}

/**
 * Mostra mensagem de erro no formulário
 */
function showFormError(form, message) {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    submitButton.textContent = '✗ ' + message;
    submitButton.style.backgroundColor = 'var(--semantic-error)';
    
    setTimeout(() => {
        submitButton.textContent = originalText;
        submitButton.style.backgroundColor = '';
    }, 3000);
}

/**
 * Configura FAQ
 */
function setupFAQ() {
    const faqQuestions = document.querySelectorAll('.faq__question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            const answer = this.nextElementSibling;
            
            // Fechar todas as outras perguntas
            faqQuestions.forEach(otherQuestion => {
                if (otherQuestion !== this) {
                    otherQuestion.setAttribute('aria-expanded', 'false');
                    otherQuestion.nextElementSibling.classList.remove('active');
                }
            });
            
            // Toggle da pergunta atual
            this.setAttribute('aria-expanded', !isExpanded);
            answer.classList.toggle('active');
        });
    });
}

/**
 * Configura acessibilidade
 */
function setupAccessibility() {
    // Adicionar foco visível para navegação por teclado
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
    
    // Anunciar mudanças de estado para leitores de tela
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    announcer.id = 'announcer';
    document.body.appendChild(announcer);
}

/**
 * Anuncia mensagem para leitores de tela
 */
function announce(message) {
    const announcer = document.getElementById('announcer');
    if (announcer) {
        announcer.textContent = message;
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
}

/**
 * Abre modal
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focar no primeiro campo do formulário
        const firstInput = modal.querySelector('.form__input');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Prevenir scroll do body
        document.body.style.overflow = 'hidden';
        
        announce('Modal aberto');
    }
}

/**
 * Fecha modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
        
        // Restaurar scroll do body
        document.body.style.overflow = '';
        
        // Limpar formulário
        const form = modal.querySelector('.form');
        if (form) {
            form.reset();
            clearFormErrors(form);
        }
        
        announce('Modal fechado');
    }
}

/**
 * Troca entre modais
 */
function switchModal(currentModalId, targetModalId) {
    closeModal(currentModalId);
    setTimeout(() => {
        openModal(targetModalId);
    }, 300);
}

/**
 * Limpa todos os erros de um formulário
 */
function clearFormErrors(form) {
    const errorElements = form.querySelectorAll('.form__error.active');
    const errorFields = form.querySelectorAll('.form__input.error');
    
    errorElements.forEach(error => {
        error.classList.remove('active');
        error.textContent = '';
    });
    
    errorFields.forEach(field => {
        field.classList.remove('error');
    });
}

// Expor funções globais necessárias
window.openModal = openModal;
window.closeModal = closeModal;
window.switchModal = switchModal;
