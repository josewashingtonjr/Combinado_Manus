#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rotas para gerenciamento de papéis de usuário
Implementa alternância entre cliente e prestador para usuários dual
"""

from flask import Blueprint, redirect, url_for, flash, session, request, jsonify
from services.auth_service import login_required, AuthService
from services.role_service import RoleService

role_bp = Blueprint('role', __name__, url_prefix='/role')

# ==============================================================================
#  ALTERNÂNCIA DE PAPÉIS
# ==============================================================================

@role_bp.route('/switch')
@login_required
def switch_role():
    """Alternar entre papéis disponíveis"""
    user = AuthService.get_current_user()
    
    if not RoleService.is_dual_role_user(user.id):
        flash('Você não possui múltiplos papéis para alternar.', 'warning')
        return redirect(request.referrer or url_for('home.index'))
    
    # Alternar papel
    if RoleService.switch_role():
        new_role = RoleService.get_active_role()
        role_labels = {'cliente': 'Cliente', 'prestador': 'Prestador'}
        flash(f'Papel alterado para {role_labels.get(new_role, new_role)}!', 'success')
        
        # Redirecionar para o dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(new_role)
        return redirect(url_for(dashboard_url))
    else:
        flash('Erro ao alternar papel.', 'error')
        return redirect(request.referrer or url_for('home.index'))

@role_bp.route('/set/<role>')
@login_required
def set_role(role):
    """Definir papel específico"""
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem o papel solicitado
    if not RoleService.has_role(user.id, role):
        flash(f'Você não tem permissão para acessar o papel {role}.', 'error')
        return redirect(request.referrer or url_for('home.index'))
    
    # Definir papel ativo
    if RoleService.set_active_role(role):
        role_labels = {'cliente': 'Cliente', 'prestador': 'Prestador'}
        flash(f'Papel alterado para {role_labels.get(role, role)}!', 'success')
        
        # Redirecionar para o dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(role)
        return redirect(url_for(dashboard_url))
    else:
        flash('Erro ao definir papel.', 'error')
        return redirect(request.referrer or url_for('home.index'))

@role_bp.route('/current')
@login_required
def current_role():
    """Obter papel atual (API JSON)"""
    user = AuthService.get_current_user()
    
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    
    context = RoleService.get_context_for_templates()
    
    return jsonify({
        'active_role': context['active_role'],
        'available_roles': context['available_roles'],
        'is_dual_role': context['is_dual_role'],
        'can_switch_roles': context['can_switch_roles']
    })

@role_bp.route('/info')
@login_required
def role_info():
    """Obter informações detalhadas sobre papéis do usuário"""
    user = AuthService.get_current_user()
    
    if not user:
        flash('Usuário não autenticado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    context = RoleService.get_context_for_templates()
    
    return jsonify({
        'user_id': user.id,
        'user_name': user.nome,
        'user_email': user.email,
        'all_roles': user.roles.split(','),
        'active_role': context['active_role'],
        'available_roles': context['available_roles'],
        'is_dual_role': context['is_dual_role'],
        'can_switch_roles': context['can_switch_roles'],
        'role_color': context['role_color'],
        'role_icon': context['role_icon']
    })

# ==============================================================================
#  ROTAS DE CONVENIÊNCIA PARA DASHBOARDS
# ==============================================================================

@role_bp.route('/cliente')
@login_required
def go_to_cliente():
    """Ir para área do cliente"""
    user = AuthService.get_current_user()
    
    if not RoleService.has_role(user.id, 'cliente'):
        flash('Você não tem permissão para acessar a área do cliente.', 'error')
        return redirect(request.referrer or url_for('home.index'))
    
    RoleService.set_active_role('cliente')
    return redirect(url_for('cliente.dashboard'))

@role_bp.route('/prestador')
@login_required
def go_to_prestador():
    """Ir para área do prestador"""
    user = AuthService.get_current_user()
    
    if not RoleService.has_role(user.id, 'prestador'):
        flash('Você não tem permissão para acessar a área do prestador.', 'error')
        return redirect(request.referrer or url_for('home.index'))
    
    RoleService.set_active_role('prestador')
    return redirect(url_for('prestador.dashboard'))

# ==============================================================================
#  MIDDLEWARE PARA INICIALIZAÇÃO DE SESSÃO
# ==============================================================================

@role_bp.before_app_request
def initialize_user_role():
    """Inicializar papel do usuário na sessão se necessário"""
    user_id = session.get('user_id')
    
    # Só inicializar para usuários regulares (não admin)
    if user_id and not session.get('admin_id'):
        # Verificar se papel ativo está definido
        if not session.get('active_role'):
            RoleService.initialize_user_session(user_id)