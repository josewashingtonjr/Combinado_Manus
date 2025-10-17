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

@app_bp.route('/switch-role/<role>')
@login_required
def switch_role(role):
    """Alternar entre papéis disponíveis para usuários duais"""
    from flask import flash
    from services.role_service import RoleService
    
    # Verificar se usuário pode alternar para o papel solicitado
    if RoleService.set_active_role(role):
        flash(f'Papel alterado para {role.title()}', 'success')
        
        # Redirecionar para dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(role)
        return redirect(url_for(dashboard_url))
    else:
        flash('Papel não disponível para seu usuário', 'error')
        return redirect(url_for('home.index'))

@app_bp.route('/toggle-role')
@login_required
def toggle_role():
    """Alternar automaticamente entre papéis disponíveis"""
    from flask import flash
    from services.role_service import RoleService
    
    if RoleService.switch_role():
        active_role = RoleService.get_active_role()
        flash(f'Papel alterado para {active_role.title()}', 'success')
        
        # Redirecionar para dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(active_role)
        return redirect(url_for(dashboard_url))
    else:
        flash('Não há outros papéis disponíveis para alternar', 'info')
        return redirect(url_for('home.index'))
