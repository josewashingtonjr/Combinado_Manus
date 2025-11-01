#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, url_for, flash, session, current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import os
import logging
import traceback
from datetime import datetime

# ==============================================================================
#  CONFIGURAÇÃO DA APLICAÇÃO
# ==============================================================================

def create_app(config_class=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object('config.Config')
    
    return app


app = create_app()

# Configurar CORS
CORS(app, supports_credentials=True)

# ==============================================================================
#  CONFIGURAÇÃO DE LOGGING
# ==============================================================================

# Criar diretório de logs se não existir
os.makedirs('logs', exist_ok=True)

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema_combinado.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Logger específico para erros do sistema
error_logger = logging.getLogger('sistema_combinado.errors')
error_logger.setLevel(logging.ERROR)

# Handler específico para erros críticos
error_handler = logging.FileHandler('logs/erros_criticos.log', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - Contexto: %(pathname)s:%(lineno)d'
)
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

from models import db
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)  # Proteção CSRF habilitada

# ==============================================================================
#  IMPORTAÇÃO DE MODELOS (necessário para migrations)
# ==============================================================================

from models import User, AdminUser, Wallet, Transaction, Order

# ==============================================================================
#  REGISTRO DE BLUEPRINTS
# ==============================================================================

from routes.home_routes import home_bp
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.cliente_routes import cliente_bp
from routes.prestador_routes import prestador_bp
from routes.app_routes import app_bp
from routes.role_routes import role_bp

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(prestador_bp)
app.register_blueprint(app_bp)
app.register_blueprint(role_bp)



# ==============================================================================
#  ROTAS PRINCIPAIS
# ==============================================================================

# Rota principal agora é gerenciada pelo home_bp

# ==============================================================================
#  CONTEXTO GLOBAL DE TEMPLATES
# ==============================================================================

@app.context_processor
def inject_version_info():
    """Injeta informações de versão em todos os templates"""
    from version import get_version_info
    return get_version_info()

# ==============================================================================
#  FILTROS JINJA2
# ==============================================================================

@app.template_filter('format_currency')
def format_currency(value):
    """Formatar valores monetários para usuários finais (sempre R$)"""
    if value is None:
        return "R$ 0,00"
    try:
        if hasattr(value, '__float__'):
            value = float(value)
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

@app.template_filter('format_tokens')
def format_tokens(value):
    """Formatar valores como tokens para administradores (terminologia técnica)"""
    if value is None:
        return "0 tokens"
    try:
        if hasattr(value, '__float__'):
            value = float(value)
        # Formatação brasileira (ponto para milhares)
        formatted = f"{value:,.0f}".replace(',', '.')
        if value == 1:
            return f"{formatted} token"
        else:
            return f"{formatted} tokens"
    except (ValueError, TypeError):
        return "0 tokens"

@app.template_filter('format_value_by_user_type')
def format_value_by_user_type(value, user_type=None):
    """Formatar valores baseado no tipo de usuário (admin vê tokens, usuários veem R$)"""
    if user_type == 'admin':
        return format_tokens(value)
    else:
        return format_currency(value)

# ==============================================================================
#  MIDDLEWARE PARA TRATAMENTO DE ERROS DE VALIDAÇÃO
# ==============================================================================

@app.before_request
def validate_database_connection():
    """Middleware para verificar conexão com banco antes de cada requisição"""
    # Pular verificação para rotas estáticas e de erro
    if request.endpoint and (
        request.endpoint.startswith('static') or 
        request.endpoint.startswith('error') or
        request.path.startswith('/static/')
    ):
        return
    
    try:
        # Tentar uma query simples para verificar conexão
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        app.logger.error(f"Erro de conexão com banco de dados: {e}")
        
        # Se for uma requisição AJAX, retornar JSON
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            from flask import jsonify
            return jsonify({
                'error': 'database_connection',
                'message': 'Sistema temporariamente indisponível. Tente novamente em alguns minutos.'
            }), 503
        
        # Caso contrário, renderizar página de erro
        return render_template('errors/500.html', is_database_error=True), 503

@app.errorhandler(Exception)
def handle_validation_errors(error):
    """Handler global para capturar erros de validação e outros"""
    # Se for um erro de validação do WTForms
    if hasattr(error, 'errors') and hasattr(error, 'form'):
        from services.validation_service import ValidationService
        
        user_type = ValidationService.get_user_type()
        formatted_errors = ValidationService.get_form_errors_formatted(error.form, user_type)
        
        # Log do erro de validação
        ValidationService.log_validation_error('form_validation', str(formatted_errors))
        
        # Se for requisição AJAX, retornar JSON
        if request.is_json:
            from flask import jsonify
            return jsonify({
                'error': 'validation_error',
                'errors': formatted_errors
            }), 400
        
        # Caso contrário, flash das mensagens e redirecionar
        for field, messages in formatted_errors.items():
            for message in messages:
                flash(f"{field}: {message}", 'error')
        
        return redirect(request.referrer or url_for('home.index'))
    
    # Para outros tipos de erro, deixar o Flask lidar normalmente
    raise error

# ==============================================================================
#  FUNÇÕES UTILITÁRIAS PARA TRATAMENTO DE ERROS
# ==============================================================================

def get_safe_redirect_url():
    """Obter URL segura para redirecionamento baseada no contexto do usuário"""
    # Verificar se é administrador
    if session.get('admin_id'):
        return url_for('admin.dashboard')
    
    # Verificar se é usuário logado
    if session.get('user_id'):
        # Importar aqui para evitar import circular
        from services.role_service import RoleService
        try:
            user_roles = RoleService.get_user_roles(session.get('user_id'))
            
            # Priorizar cliente se tiver ambos os papéis
            if 'cliente' in user_roles:
                return url_for('cliente.dashboard')
            elif 'prestador' in user_roles:
                return url_for('prestador.dashboard')
        except Exception:
            # Em caso de erro, redirecionar para home
            pass
    
    # Fallback para página inicial
    return url_for('home.index')

def log_user_action(action, details=None):
    """Log de ações do usuário para auditoria"""
    user_context = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'admin_id': session.get('admin_id'),
        'user_id': session.get('user_id'),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'N/A'),
        'url': request.url,
        'method': request.method,
        'details': details or {}
    }
    
    app.logger.info(f"Ação do usuário: {action} | Contexto: {user_context}")

# ==============================================================================
#  FUNÇÕES DE CONTEXTO
# ==============================================================================

@app.context_processor
def inject_user():
    """Injetar informações do usuário em todos os templates"""
    return dict(
        current_admin_id=session.get('admin_id'),
        current_user_id=session.get('user_id')
    )

@app.context_processor
def inject_user_context():
    """Injetar contexto de terminologia baseado no tipo de usuário"""
    # Detectar se é administrador
    is_admin = session.get('admin_id') is not None
    
    # Detectar tipo de usuário atual
    user_type = 'admin' if is_admin else 'user'
    
    # Definir terminologia baseada no tipo
    if is_admin:
        terminology = {
            'balance_label': 'Tokens',
            'balance_unit': 'tokens',
            'currency_symbol': '',
            'value_format': 'tokens',
            'technical_view': True
        }
    else:
        terminology = {
            'balance_label': 'Saldo',
            'balance_unit': 'R$',
            'currency_symbol': 'R$',
            'value_format': 'currency',
            'technical_view': False
        }
    
    # Obter contexto de papéis para usuários regulares
    role_context = {}
    if not is_admin and session.get('user_id'):
        from services.role_service import RoleService
        role_context = RoleService.get_context_for_templates()
    
    return dict(
        user_type=user_type,
        is_admin_user=is_admin,
        terminology=terminology,
        **role_context
    )

# ==============================================================================
#  INICIALIZAÇÃO DO BANCO DE DADOS
# ==============================================================================

def init_db():
    """Inicializar banco de dados e criar usuário admin padrão"""
    with app.app_context():
        db.create_all()
        
        # Criar administrador padrão se não existir
        admin = AdminUser.query.filter_by(email='admin@combinado.com').first()
        if not admin:
            admin = AdminUser(email='admin@combinado.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Administrador padrão criado: admin@combinado.com / admin123")

# ==============================================================================
#  ROTA DE TESTE
# ==============================================================================

@app.route('/test-login')
def test_login():
    """Página de teste para debug do login"""
    return render_template('test_login.html')

# ==============================================================================
#  TRATAMENTO DE ERROS
# ==============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Tratamento de erro 404 - Página não encontrada"""
    # Log do erro 404 com contexto
    user_context = {
        'admin_id': session.get('admin_id'),
        'user_id': session.get('user_id'),
        'url': request.url,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'N/A')
    }
    
    app.logger.warning(f"Erro 404 - Página não encontrada: {request.url} | Contexto: {user_context}")
    
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Tratamento de erro 500 - Erro interno do servidor"""
    # Rollback da sessão do banco de dados
    try:
        db.session.rollback()
    except Exception as rollback_error:
        app.logger.error(f"Erro no rollback da sessão: {rollback_error}")
    
    # Detectar se é erro de conexão com banco de dados
    is_db_error = False
    db_error_messages = [
        'connection', 'database', 'postgresql', 'sqlite', 'mysql',
        'operational error', 'programming error', 'integrity error'
    ]
    
    error_str = str(error).lower()
    for db_msg in db_error_messages:
        if db_msg in error_str:
            is_db_error = True
            break
    
    # Capturar informações detalhadas do erro
    error_details = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'is_database_error': is_db_error,
        'traceback': traceback.format_exc(),
        'url': request.url,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'N/A'),
        'admin_id': session.get('admin_id'),
        'user_id': session.get('user_id'),
        'session_data': dict(session) if session else {},
        'form_data': dict(request.form) if request.form else {},
        'args': dict(request.args) if request.args else {}
    }
    
    # Log estruturado do erro crítico
    if is_db_error:
        error_logger.critical(
            f"ERRO CRÍTICO DE BANCO DE DADOS - {error_details['error_type']}: {error_details['error_message']} | "
            f"URL: {error_details['url']} | "
            f"Usuário: Admin={error_details['admin_id']}, User={error_details['user_id']} | "
            f"IP: {error_details['ip']} | "
            f"Timestamp: {error_details['timestamp']}",
            extra={'error_details': error_details}
        )
    else:
        error_logger.error(
            f"ERRO CRÍTICO 500 - {error_details['error_type']}: {error_details['error_message']} | "
            f"URL: {error_details['url']} | "
            f"Usuário: Admin={error_details['admin_id']}, User={error_details['user_id']} | "
            f"IP: {error_details['ip']} | "
            f"Timestamp: {error_details['timestamp']}",
            extra={'error_details': error_details}
        )
    
    # Log adicional com traceback completo
    app.logger.error(f"Traceback completo do erro 500:\n{error_details['traceback']}")
    
    return render_template('errors/500.html', is_database_error=is_db_error), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Tratamento de erro 403 - Acesso negado"""
    user_context = {
        'admin_id': session.get('admin_id'),
        'user_id': session.get('user_id'),
        'url': request.url,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'N/A')
    }
    
    app.logger.warning(f"Erro 403 - Acesso negado: {request.url} | Contexto: {user_context}")
    
    return render_template('errors/403.html'), 403

# ==============================================================================
#  INICIALIZAÇÃO
# ==============================================================================

if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    
    # Iniciar servidor
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)