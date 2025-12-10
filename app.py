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
#  CONFIGURAÇÃO DE LOGGING COM ROTATION
# ==============================================================================

# Criar diretório de logs se não existir
os.makedirs('logs', exist_ok=True)

from logging.handlers import RotatingFileHandler

# Configurar logging estruturado com rotation
# Handler principal do sistema com rotation (10MB por arquivo, mantém 5 backups)
main_handler = RotatingFileHandler(
    'logs/sistema_combinado.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
main_handler.setLevel(logging.INFO)
main_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
main_handler.setFormatter(main_formatter)

# Handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(main_formatter)

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    handlers=[main_handler, console_handler]
)

# Logger específico para erros do sistema com rotation
error_logger = logging.getLogger('sistema_combinado.errors')
error_logger.setLevel(logging.ERROR)

error_handler = RotatingFileHandler(
    'logs/erros_criticos.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - Contexto: %(pathname)s:%(lineno)d'
)
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# Logger específico para operações de ordem com rotation
order_operations_logger = logging.getLogger('sistema_combinado.order_operations')
order_operations_logger.setLevel(logging.INFO)

order_handler = RotatingFileHandler(
    'logs/order_operations.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,  # Mantém mais backups para operações de ordem
    encoding='utf-8'
)
order_handler.setLevel(logging.INFO)
order_formatter = logging.Formatter('%(asctime)s - ORDER_OPS - %(message)s')
order_handler.setFormatter(order_formatter)
order_operations_logger.addHandler(order_handler)

# Logger de auditoria com rotation (configurado em audit_service.py)
audit_logger = logging.getLogger('sistema_combinado.audit')
audit_logger.setLevel(logging.INFO)

audit_handler = RotatingFileHandler(
    'logs/audit.log',
    maxBytes=20*1024*1024,  # 20MB (maior porque auditoria é crítica)
    backupCount=20,  # Mantém mais backups para auditoria
    encoding='utf-8'
)
audit_handler.setLevel(logging.INFO)
audit_formatter = logging.Formatter('%(asctime)s - AUDIT - %(message)s')
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)

from models import db
db.init_app(app)
migrate = Migrate(app, db)

# Configurar Flask-Login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Configurar proteção CSRF
csrf = CSRFProtect(app)

# Configurar Rate Limiter
from services.rate_limiter_service import limiter, rate_limit_error_handler
limiter.init_app(app)

# Registrar handler de erro para rate limiting
@app.errorhandler(429)
def handle_rate_limit_error(e):
    return rate_limit_error_handler(e)

# Configurar Middleware de Performance
from services.performance_middleware import PerformanceMiddleware
performance = PerformanceMiddleware(app)

# Registrar Template Helpers
from template_helpers import register_template_helpers
register_template_helpers(app)

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
from routes.session_timeout_routes import session_timeout_bp
from routes.proposal_routes import proposal_bp
from routes.admin_proposal_monitoring_routes import admin_proposal_monitoring
from routes.order_routes import order_bp
from routes.realtime_routes import realtime_bp
from routes.pre_ordem_routes import pre_ordem_bp

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(prestador_bp)
app.register_blueprint(app_bp)
app.register_blueprint(role_bp)
app.register_blueprint(session_timeout_bp)
app.register_blueprint(proposal_bp)
app.register_blueprint(admin_proposal_monitoring)
app.register_blueprint(order_bp)
app.register_blueprint(realtime_bp)
app.register_blueprint(pre_ordem_bp)

# Configurar exceções de CSRF para rotas de autenticação
csrf.exempt(auth_bp)



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

@app.context_processor
def inject_csrf_token():
    """Injeta token CSRF em todos os templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

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

@app.before_request
def check_session_timeout():
    """Middleware para verificar timeout de sessão"""
    # Pular verificação para rotas que não precisam de autenticação
    skip_routes = [
        'static', 'auth.index', 'auth.user_login', 'auth.admin_login', 
        'auth.register', 'auth.convite_acesso', 'auth.processar_cadastro_convite',
        'auth.processar_login_convite', 'auth.aceitar_convite_inicial', 
        'auth.convite_login_cadastro', 'auth.rejeitar_convite', 'home.index', 'home.sobre',
        'session_timeout.check_status', 'session_timeout.extend_session'
    ]
    
    # Pular para rotas estáticas e específicas
    if (request.endpoint and any(request.endpoint.startswith(route) for route in ['static', 'error']) or
        request.path.startswith('/static/') or
        request.endpoint in skip_routes):
        return
    
    # Verificar se há sessão ativa (usuário ou admin)
    has_session = session.get('user_id') or session.get('admin_id')
    
    if has_session:
        from services.session_timeout_manager import SessionTimeoutManager
        
        # Verificar status da sessão
        timeout_status = SessionTimeoutManager.check_session_timeout()
        
        if timeout_status['expired']:
            # Sessão expirada - limpar e redirecionar
            SessionTimeoutManager.invalidate_session()
            
            # Log da expiração
            app.logger.info(
                f"Sessão expirada - User: {session.get('user_id')}, "
                f"Admin: {session.get('admin_id')}, Motivo: {timeout_status.get('reason')}"
            )
            
            # Se for requisição AJAX, retornar JSON
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': 'session_expired',
                    'message': timeout_status.get('message', 'Sua sessão expirou'),
                    'redirect': url_for('auth.user_login') if session.get('user_id') else url_for('auth.admin_login')
                }), 401
            
            # Limpar sessão e redirecionar
            session.clear()
            flash('Sua sessão expirou por inatividade. Faça login novamente.', 'warning')
            
            # Redirecionar baseado no tipo de usuário
            if session.get('admin_id'):
                return redirect(url_for('auth.admin_login'))
            else:
                return redirect(url_for('auth.user_login'))
        
        # Se não expirou, atualizar última atividade para requisições importantes
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            SessionTimeoutManager.extend_session()

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

@app.context_processor
def inject_admin_stats():
    """Injetar estatísticas do admin para mostrar notificações"""
    # Só injetar se for administrador
    if session.get('admin_id'):
        try:
            from services.admin_service import AdminService
            stats = AdminService.get_dashboard_stats()
            app.logger.info(f"Context processor - Stats injetadas: {list(stats.keys())}")
            return dict(stats=stats)
        except Exception as e:
            app.logger.error(f"Erro no context processor: {str(e)}")
            # Em caso de erro, retornar stats vazias
            return dict(stats={'solicitacoes_tokens_pendentes': 0})
    
    return dict()

@app.context_processor
def inject_mobile_notifications():
    """
    Injetar contagens de notificações para badges da navegação mobile
    
    Task 8: Adicionar badge para notificações
    Requirement 4: Navegação Simplificada - Badge para notificações pendentes
    """
    from flask_login import current_user
    from models import Invite, PreOrder, Order
    
    # Inicializar contadores
    pending_invites = 0
    pending_pre_orders = 0
    pending_orders = 0
    
    # Só calcular se houver usuário autenticado
    if current_user and current_user.is_authenticated:
        try:
            user_id = current_user.id
            
            # Contar convites pendentes (recebidos e não respondidos)
            if hasattr(current_user, 'roles'):
                if 'prestador' in current_user.roles:
                    # Prestador: convites recebidos aguardando resposta
                    pending_invites = Invite.query.filter_by(
                        prestador_id=user_id,
                        status='pendente'
                    ).count()
                    
                    # Prestador: pré-ordens aguardando ação (propostas do cliente)
                    pending_pre_orders = PreOrder.query.filter(
                        PreOrder.prestador_id == user_id,
                        PreOrder.status.in_(['aguardando_prestador', 'proposta_cliente'])
                    ).count()
                    
                    # Prestador: ordens aguardando ação
                    pending_orders = Order.query.filter(
                        Order.prestador_id == user_id,
                        Order.status.in_(['aceita', 'em_andamento'])
                    ).count()
                    
                elif 'cliente' in current_user.roles:
                    # Cliente: convites enviados aguardando resposta
                    pending_invites = Invite.query.filter_by(
                        cliente_id=user_id,
                        status='pendente'
                    ).count()
                    
                    # Cliente: pré-ordens aguardando ação (propostas do prestador)
                    pending_pre_orders = PreOrder.query.filter(
                        PreOrder.cliente_id == user_id,
                        PreOrder.status.in_(['aguardando_cliente', 'proposta_prestador'])
                    ).count()
                    
                    # Cliente: ordens aguardando confirmação ou em disputa
                    pending_orders = Order.query.filter(
                        Order.client_id == user_id,
                        Order.status.in_(['concluida_aguardando_confirmacao', 'em_disputa'])
                    ).count()
                    
        except Exception as e:
            app.logger.error(f"Erro ao calcular notificações mobile: {str(e)}")
            # Em caso de erro, retornar contadores zerados
            pass
    
    return dict(
        pending_invites=pending_invites,
        pending_pre_orders=pending_pre_orders,
        pending_orders=pending_orders
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
#  ROTAS DE SESSÃO
# ==============================================================================

@app.route('/session/check-status')
def check_session_status():
    """Verifica o status da sessão e retorna informações sobre expiração"""
    from datetime import datetime, timedelta
    
    # Verificar se há sessão ativa
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')
    session_expires = session.get('session_expires')
    
    if not (user_id or admin_id) or not session_expires:
        return jsonify({
            'authenticated': False,
            'message': 'Sessão não encontrada'
        }), 401
    
    # Converter string para datetime se necessário
    if isinstance(session_expires, str):
        session_expires = datetime.fromisoformat(session_expires)
    
    now = datetime.utcnow()
    time_remaining = session_expires - now
    minutes_remaining = int(time_remaining.total_seconds() / 60)
    
    # Mostrar aviso se faltarem 5 minutos ou menos
    should_warn = minutes_remaining <= 5 and minutes_remaining > 0
    
    return jsonify({
        'authenticated': True,
        'should_warn': should_warn,
        'minutes_remaining': minutes_remaining,
        'expires_at': session_expires.isoformat()
    })

@app.route('/session/extend', methods=['POST'])
def extend_session():
    """Estende a sessão do usuário"""
    from datetime import datetime, timedelta
    
    # Verificar se há sessão ativa
    user_id = session.get('user_id')
    admin_id = session.get('admin_id')
    session_id = session.get('session_id')
    
    if not (user_id or admin_id) or not session_id:
        return jsonify({
            'success': False,
            'message': 'Sessão não encontrada'
        }), 401
    
    try:
        # Estender sessão por mais 30 minutos
        new_expiration = datetime.utcnow() + timedelta(minutes=30)
        session['session_expires'] = new_expiration.isoformat()
        session.modified = True
        
        app.logger.info(f"Sessão estendida - Session: {session_id}, "
                       f"User: {user_id}, Admin: {admin_id}, "
                       f"Nova expiração: {new_expiration}")
        
        return jsonify({
            'success': True,
            'message': 'Sessão estendida com sucesso',
            'new_expiration': new_expiration.isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao estender sessão: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao estender sessão'
        }), 500

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

@app.errorhandler(400)
def csrf_error(error):
    """Tratamento específico para erros CSRF"""
    # Verificar se é erro CSRF
    if 'CSRF' in str(error) or 'csrf' in str(error).lower():
        user_context = {
            'admin_id': session.get('admin_id'),
            'user_id': session.get('user_id'),
            'url': request.url,
            'method': request.method,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'N/A')
        }
        
        app.logger.warning(f"Erro CSRF detectado: {request.url} | Contexto: {user_context}")
        
        # Se for requisição AJAX, retornar JSON
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from flask import jsonify
            return jsonify({
                'error': 'csrf_error',
                'message': 'Token de segurança inválido. Recarregue a página e tente novamente.'
            }), 400
        
        # Para requisições normais, mostrar mensagem e redirecionar
        flash('Token de segurança inválido. Tente novamente.', 'error')
        return redirect(request.referrer or get_safe_redirect_url())
    
    # Se não for erro CSRF, deixar o Flask lidar normalmente
    raise error

# ==============================================================================
#  INICIALIZAÇÃO
# ==============================================================================

if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    
    # Iniciar servidor
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)