#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, session
from services.auth_service import login_required

# Criar blueprint para área do app (cliente logado)
app_bp = Blueprint('app', __name__, url_prefix='/app')

@app_bp.route('/home')
@login_required
def home():
    """Página inicial do cliente logado"""
    # Verificar se usuário tem papel de cliente
    user_roles = session.get('user_role', '').split(',')
    if 'cliente' not in user_roles:
        return redirect(url_for('prestador.dashboard'))
    
    return render_template('cliente/dashboard.html')

@app_bp.route('/carteira')
@login_required
def carteira():
    """Página da carteira do cliente"""
    return render_template('cliente/carteira.html')

@app_bp.route('/historico')
@login_required
def historico():
    """Página de histórico do cliente"""
    return render_template('cliente/historico.html')

@app_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil do cliente"""
    return render_template('cliente/perfil.html')
