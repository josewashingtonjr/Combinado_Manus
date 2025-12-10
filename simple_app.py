#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versão simplificada do app.py para teste
"""

from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

# Criar aplicação
app = Flask(__name__)

# Configuração básica
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-forte'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/test_combinado.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar banco
from models import db
db.init_app(app)

# Rota básica
@app.route('/')
def index():
    return "<h1>Sistema Combinado - Funcionando!</h1><p>Controle de criação de tokens implementado com sucesso!</p>"

@app.route('/test-token-control')
def test_token_control():
    """Teste básico do controle de tokens"""
    try:
        from services.token_creation_control_service import TokenCreationControlService
        from models import AdminUser
        
        # Buscar um admin
        admin = AdminUser.query.first()
        if not admin:
            return "<h2>❌ Nenhum admin encontrado</h2>"
        
        # Testar o serviço
        info = TokenCreationControlService.get_admin_limits_info(admin.id)
        
        html = f"""
        <h1>✅ Teste do Controle de Tokens</h1>
        <h2>Admin: {info['admin_email']}</h2>
        <ul>
            <li><strong>Limite Diário:</strong> R$ {info['daily_limit']:.2f}</li>
            <li><strong>Usado Diário:</strong> R$ {info['daily_used']:.2f} ({info['daily_percentage_used']:.1f}%)</li>
            <li><strong>Restante Diário:</strong> R$ {info['daily_remaining']:.2f}</li>
            <li><strong>Limite Mensal:</strong> R$ {info['monthly_limit']:.2f}</li>
            <li><strong>Usado Mensal:</strong> R$ {info['monthly_used']:.2f} ({info['monthly_percentage_used']:.1f}%)</li>
            <li><strong>Restante Mensal:</strong> R$ {info['monthly_remaining']:.2f}</li>
        </ul>
        <p><a href="/">← Voltar</a></p>
        """
        return html
        
    except Exception as e:
        return f"<h2>❌ Erro no teste: {e}</h2><p><a href='/'>← Voltar</a></p>"

if __name__ == '__main__':
    with app.app_context():
        # Criar tabelas se necessário
        db.create_all()
        
        # Criar admin de teste se não existir
        from models import AdminUser
        admin = AdminUser.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = AdminUser(email='admin@test.com', papel='admin')
            admin.set_password('senha123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin de teste criado: admin@test.com / senha123")
    
    print("🚀 Iniciando servidor simplificado...")
    print("📍 Acesse: http://localhost:5001")
    print("🧪 Teste o controle de tokens: http://localhost:5001/test-token-control")
    
    app.run(debug=True, host='0.0.0.0', port=5001)