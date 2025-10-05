#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect, url_for, flash, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import os

# ==============================================================================
#  CONFIGURAÇÃO DA APLICAÇÃO
# ==============================================================================

app = Flask(__name__)
app.config.from_object('config.Config')

# Configurar CORS
CORS(app, supports_credentials=True)

from models import db
db.init_app(app)
migrate = Migrate(app, db)
# csrf = CSRFProtect(app)  # Desabilitado para APIs AJAX

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

app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(prestador_bp)
app.register_blueprint(app_bp)

# ==============================================================================
#  ROTAS PRINCIPAIS
# ==============================================================================

# Rota principal agora é gerenciada pelo home_bp

# ==============================================================================
#  FILTROS JINJA2
# ==============================================================================

@app.template_filter('format_currency')
def format_currency(value):
    """Formatar valores monetários"""
    if value is None:
        return "R$ 0,00"
    try:
        if hasattr(value, '__float__'):
            value = float(value)
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

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
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ==============================================================================
#  INICIALIZAÇÃO
# ==============================================================================

if __name__ == '__main__':
    # Inicializar banco de dados
    init_db()
    
    # Iniciar servidor
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
