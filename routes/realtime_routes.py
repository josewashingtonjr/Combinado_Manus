# -*- coding: utf-8 -*-
"""
Rotas para Atualizações em Tempo Real
Implementa endpoints SSE para dashboards
"""

from flask import Blueprint, jsonify
from services.auth_service import AuthService
from services.realtime_service import RealtimeService
from services.role_service import RoleService
import logging

logger = logging.getLogger(__name__)

realtime_bp = Blueprint('realtime', __name__, url_prefix='/realtime')


@realtime_bp.route('/dashboard/stream')
def dashboard_stream():
    """
    Endpoint SSE para atualizações da dashboard
    
    Returns:
        Stream SSE com atualizações em tempo real
    """
    try:
        # Verificar autenticação
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'Não autenticado'}), 401
        
        # Obter papel ativo do usuário
        active_role = RoleService.get_active_role()
        if not active_role:
            return jsonify({'error': 'Papel não definido'}), 400
        
        # Criar stream SSE
        return RealtimeService.create_sse_stream(user.id, active_role)
        
    except Exception as e:
        logger.error(f"Erro ao criar stream SSE: {e}")
        return jsonify({'error': 'Erro ao estabelecer conexão'}), 500


@realtime_bp.route('/dashboard/check-updates')
def check_updates():
    """
    Endpoint de fallback para verificar atualizações via polling
    
    Returns:
        JSON com atualizações disponíveis
    """
    try:
        # Verificar autenticação
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'Não autenticado'}), 401
        
        # Obter papel ativo do usuário
        active_role = RoleService.get_active_role()
        if not active_role:
            return jsonify({'error': 'Papel não definido'}), 400
        
        # Verificar atualizações
        updates = RealtimeService.check_for_updates(user.id, active_role)
        
        return jsonify({
            'success': True,
            'has_updates': len(updates) > 0,
            'updates': updates
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar atualizações: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar atualizações'
        }), 500


@realtime_bp.route('/dashboard/refresh')
def refresh_dashboard():
    """
    Endpoint para forçar atualização manual da dashboard
    
    Returns:
        JSON indicando sucesso
    """
    try:
        # Verificar autenticação
        user = AuthService.get_current_user()
        if not user:
            return jsonify({'error': 'Não autenticado'}), 401
        
        # Invalidar cache do usuário
        RealtimeService.notify_balance_changed(user.id)
        
        return jsonify({
            'success': True,
            'message': 'Dashboard atualizada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro ao atualizar dashboard'
        }), 500
