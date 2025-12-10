#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rotas para gerenciamento de timeout de sessão
Endpoints para verificação de status, extensão e avisos de expiração
"""

from flask import Blueprint, jsonify, session, request, current_app
from services.session_timeout_manager import SessionTimeoutManager

# Criar blueprint para timeout de sessão
session_timeout_bp = Blueprint('session_timeout', __name__, url_prefix='/session')

@session_timeout_bp.route('/check-status')
def check_status():
    """
    Verificar status atual da sessão
    Retorna informações sobre expiração e tempo restante
    """
    try:
        # Verificar se há sessão ativa
        if not (session.get('user_id') or session.get('admin_id')):
            return jsonify({
                'authenticated': False,
                'message': 'Nenhuma sessão ativa'
            }), 401
        
        # Verificar status da sessão
        timeout_status = SessionTimeoutManager.check_session_timeout()
        
        if timeout_status['expired']:
            # Sessão expirada
            SessionTimeoutManager.invalidate_session()
            return jsonify({
                'authenticated': False,
                'expired': True,
                'reason': timeout_status.get('reason'),
                'message': timeout_status.get('message', 'Sessão expirada')
            }), 401
        
        # Sessão válida
        return jsonify({
            'authenticated': True,
            'expired': False,
            'should_warn': timeout_status.get('should_warn', False),
            'minutes_remaining': timeout_status.get('minutes_remaining', 0),
            'expires_at': timeout_status.get('expires_at'),
            'last_activity': timeout_status.get('last_activity')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status da sessão: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': 'Erro interno ao verificar sessão'
        }), 500

@session_timeout_bp.route('/extend', methods=['POST'])
def extend_session():
    """
    Estender sessão atual
    Atualiza o tempo de expiração
    """
    try:
        # Verificar se há sessão ativa
        if not (session.get('user_id') or session.get('admin_id')):
            return jsonify({
                'success': False,
                'message': 'Nenhuma sessão ativa para estender'
            }), 401
        
        # Tentar estender a sessão
        result = SessionTimeoutManager.extend_session()
        
        if result['success']:
            current_app.logger.info(
                f"Sessão estendida via endpoint - User: {session.get('user_id')}, "
                f"Admin: {session.get('admin_id')}"
            )
            return jsonify({
                'success': True,
                'message': 'Sessão estendida com sucesso',
                'new_expires_at': result.get('new_expires_at')
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Falha ao estender sessão')
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erro ao estender sessão: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno ao estender sessão'
        }), 500

@session_timeout_bp.route('/warning-info')
def warning_info():
    """
    Obter informações para exibir aviso de expiração
    """
    try:
        # Verificar se há sessão ativa
        if not (session.get('user_id') or session.get('admin_id')):
            return jsonify({
                'show_warning': False,
                'message': 'Nenhuma sessão ativa'
            }), 401
        
        # Verificar status da sessão
        timeout_status = SessionTimeoutManager.check_session_timeout()
        
        if timeout_status['expired']:
            return jsonify({
                'show_warning': False,
                'expired': True,
                'message': 'Sessão já expirada'
            })
        
        should_warn = timeout_status.get('should_warn', False)
        minutes_remaining = timeout_status.get('minutes_remaining', 0)
        
        return jsonify({
            'show_warning': should_warn,
            'minutes_remaining': minutes_remaining,
            'expires_at': timeout_status.get('expires_at'),
            'warning_message': f'Sua sessão expirará em {minutes_remaining} minuto(s). Deseja estender?'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter informações de aviso: {str(e)}")
        return jsonify({
            'show_warning': False,
            'error': 'Erro interno'
        }), 500

@session_timeout_bp.route('/cleanup', methods=['POST'])
def cleanup_expired():
    """
    Endpoint administrativo para limpeza de sessões expiradas
    Apenas administradores podem usar
    """
    try:
        # Verificar se é administrador
        if not session.get('admin_id'):
            return jsonify({
                'success': False,
                'message': 'Acesso negado - apenas administradores'
            }), 403
        
        # Executar limpeza
        count = SessionTimeoutManager.cleanup_expired_sessions()
        
        current_app.logger.info(
            f"Limpeza manual de sessões executada por admin {session.get('admin_id')} - "
            f"{count} sessões removidas"
        )
        
        return jsonify({
            'success': True,
            'message': f'{count} sessões expiradas foram removidas',
            'sessions_cleaned': count
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na limpeza de sessões: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno na limpeza'
        }), 500

@session_timeout_bp.route('/active-sessions')
def active_sessions():
    """
    Listar sessões ativas (apenas para administradores)
    """
    try:
        # Verificar se é administrador
        if not session.get('admin_id'):
            return jsonify({
                'success': False,
                'message': 'Acesso negado - apenas administradores'
            }), 403
        
        # Obter contagem de sessões ativas
        active_count = SessionTimeoutManager.get_active_sessions_count()
        
        return jsonify({
            'success': True,
            'active_sessions_count': active_count,
            'message': f'{active_count} sessões ativas no sistema'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar sessões ativas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno'
        }), 500

@session_timeout_bp.route('/user-sessions')
def user_sessions():
    """
    Listar sessões do usuário atual
    """
    try:
        user_id = session.get('user_id')
        admin_id = session.get('admin_id')
        
        if not (user_id or admin_id):
            return jsonify({
                'success': False,
                'message': 'Nenhuma sessão ativa'
            }), 401
        
        # Obter sessões do usuário
        user_sessions = SessionTimeoutManager.get_user_active_sessions(
            user_id=user_id,
            admin_id=admin_id
        )
        
        return jsonify({
            'success': True,
            'sessions': user_sessions,
            'count': len(user_sessions)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar sessões do usuário: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno'
        }), 500

@session_timeout_bp.route('/force-logout-user', methods=['POST'])
def force_logout_user():
    """
    Forçar logout de todas as sessões de um usuário (apenas admin)
    """
    try:
        # Verificar se é administrador
        if not session.get('admin_id'):
            return jsonify({
                'success': False,
                'message': 'Acesso negado - apenas administradores'
            }), 403
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        target_admin_id = data.get('admin_id')
        
        if not (target_user_id or target_admin_id):
            return jsonify({
                'success': False,
                'message': 'ID do usuário ou admin é obrigatório'
            }), 400
        
        # Forçar logout
        count = SessionTimeoutManager.force_logout_user(
            user_id=target_user_id,
            admin_id=target_admin_id
        )
        
        current_app.logger.info(
            f"Logout forçado executado por admin {session.get('admin_id')} - "
            f"Target: {'User' if target_user_id else 'Admin'} {target_user_id or target_admin_id}, "
            f"{count} sessões removidas"
        )
        
        return jsonify({
            'success': True,
            'message': f'{count} sessões foram encerradas',
            'sessions_removed': count
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao forçar logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno'
        }), 500