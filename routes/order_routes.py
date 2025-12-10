#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rotas para gerenciamento de ordens de serviço
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Order, User
from services.auth_service import login_required, AuthService
from services.order_management_service import OrderManagementService
from services.config_service import ConfigService
from services.security_validator import SecurityValidator, require_order_ownership, rate_limit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__, url_prefix='/ordens')


# ==============================================================================
#  ROTAS COMUNS (Cliente e Prestador)
# ==============================================================================

@order_bp.route('/')
@login_required
def listar_ordens():
    """Lista ordens do usuário (como cliente ou prestador)"""
    user = AuthService.get_current_user()
    
    # Determinar papel ativo
    active_role = session.get('active_role', 'cliente')
    
    # Validar que o usuário tem o papel necessário
    if active_role == 'cliente' and 'cliente' not in user.roles:
        flash('Você não tem permissão para acessar a área do cliente.', 'error')
        return redirect(url_for('home.index'))
    
    if active_role == 'prestador' and 'prestador' not in user.roles:
        flash('Você não tem permissão para acessar a área do prestador.', 'error')
        return redirect(url_for('home.index'))
    
    # Filtro de status dos query params
    status_filter = request.args.get('status')
    
    try:
        # Buscar ordens baseado no papel
        orders = OrderManagementService.get_orders_by_user(user.id, active_role, status_filter)
        
        # Buscar estatísticas para o dashboard
        statistics = OrderManagementService.get_order_statistics(user.id, active_role)
        
        # Determinar template apropriado
        if active_role == 'cliente':
            template = 'cliente/ordens.html'
        else:
            template = 'prestador/ordens.html'
        
        return render_template(
            template, 
            user=user, 
            orders=orders, 
            statistics=statistics,
            status_filter=status_filter
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar ordens: {e}")
        flash('Erro ao carregar ordens.', 'error')
        return redirect(url_for('home.index'))


@order_bp.route('/<int:order_id>')
@login_required
@require_order_ownership()
def ver_ordem(order_id, order=None):
    """
    Visualiza detalhes de uma ordem
    
    Features:
        - Validar que usuário é cliente ou prestador da ordem
        - Buscar ordem com eager loading de relacionamentos
        - Calcular horas restantes para confirmação automática
        - Determinar botões de ação disponíveis baseado em status e role
        - Renderizar template apropriado (cliente/ver_ordem.html ou prestador/ver_ordem.html)
    """
    user = AuthService.get_current_user()
    
    try:
        # Se a ordem não foi passada pelo decorator, buscar com eager loading
        if not order:
            order = Order.query.options(
                db.joinedload(Order.client),
                db.joinedload(Order.provider),
                db.joinedload(Order.cancelled_by_user),
                db.joinedload(Order.dispute_opener)
            ).get_or_404(order_id)
        
        # Determinar papel do usuário nesta ordem
        is_client = (order.client_id == user.id)
        is_provider = (order.provider_id == user.id)
        
        # Calcular horas restantes para confirmação automática
        hours_remaining = order.hours_until_auto_confirmation
        is_near_deadline = order.is_near_auto_confirmation  # Menos de 12 horas
        
        # Determinar botões de ação disponíveis baseado em status e role
        available_actions = {
            'can_mark_completed': is_provider and order.can_be_marked_completed,
            'can_confirm': is_client and order.can_be_confirmed,
            'can_dispute': is_client and order.can_be_disputed,
            'can_cancel': (is_client or is_provider) and order.can_be_cancelled,
            'show_countdown': order.status == 'servico_executado' and hours_remaining is not None,
            'is_near_deadline': is_near_deadline
        }
        
        # Calcular valores detalhados para exibição
        from decimal import Decimal
        
        # Garantir que todos os valores sejam Decimal
        if order.platform_fee_percentage_at_creation is not None:
            platform_fee_percentage = Decimal(str(order.platform_fee_percentage_at_creation))
        else:
            config_value = ConfigService.get_platform_fee_percentage()
            platform_fee_percentage = Decimal(str(config_value)) if config_value is not None else Decimal('5.0')
        
        if order.contestation_fee_at_creation is not None:
            contestation_fee = Decimal(str(order.contestation_fee_at_creation))
        else:
            config_value = ConfigService.get_contestation_fee()
            contestation_fee = Decimal(str(config_value)) if config_value is not None else Decimal('10.0')
        
        if order.cancellation_fee_percentage_at_creation is not None:
            cancellation_fee_percentage = Decimal(str(order.cancellation_fee_percentage_at_creation))
        else:
            config_value = ConfigService.get_cancellation_fee_percentage()
            cancellation_fee_percentage = Decimal(str(config_value)) if config_value is not None else Decimal('10.0')
        
        # Calcular valores (garantir que tudo seja Decimal)
        service_value = Decimal(str(order.value))  # Garantir que é Decimal
        platform_fee = service_value * (platform_fee_percentage / Decimal('100'))
        provider_net_amount = service_value - platform_fee
        cancellation_fee = service_value * (cancellation_fee_percentage / Decimal('100'))
        
        value_breakdown = {
            'service_value': float(service_value),
            'platform_fee': float(platform_fee),
            'platform_fee_percentage': float(platform_fee_percentage),
            'provider_net_amount': float(provider_net_amount),
            'contestation_fee': float(contestation_fee),
            'cancellation_fee': float(cancellation_fee),
            'cancellation_fee_percentage': float(cancellation_fee_percentage)
        }
        
        # Escolher template baseado no papel
        if is_client:
            template = 'cliente/ver_ordem.html'
        else:
            template = 'prestador/ver_ordem.html'
        
        logger.info(
            f"Usuário {user.id} ({user.nome}) visualizando ordem {order_id}. "
            f"Papel: {'cliente' if is_client else 'prestador'}, "
            f"Status: {order.status}, "
            f"Horas restantes: {hours_remaining if hours_remaining else 'N/A'}"
        )
        
        return render_template(
            template,
            user=user,
            order=order,
            is_client=is_client,
            is_provider=is_provider,
            hours_remaining=hours_remaining,
            available_actions=available_actions,
            value_breakdown=value_breakdown
        )
        
    except Exception as e:
        logger.error(f"Erro ao visualizar ordem {order_id}: {e}")
        flash('Erro ao carregar ordem.', 'error')
        return redirect(url_for('order.listar_ordens'))


# ==============================================================================
#  ROTAS DO PRESTADOR
# ==============================================================================

@order_bp.route('/<int:order_id>/marcar-concluido', methods=['POST'])
@login_required
@require_order_ownership(required_role='provider')
@rate_limit('mark_completed', max_attempts=10, window_seconds=60)
def marcar_concluido(order_id, order=None):
    """Prestador marca o serviço como concluído"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('order.listar_ordens'))
    
    # Validar permissão para a ação específica
    is_allowed, error_msg = SecurityValidator.validate_order_action_permission(
        order, user.id, 'mark_completed'
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    try:
        result = OrderManagementService.mark_service_completed(order_id, user.id)
        
        flash(result['message'], 'success')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao marcar ordem {order_id} como concluída: {e}")
        flash('Erro ao marcar serviço como concluído.', 'error')
    
    return redirect(url_for('order.ver_ordem', order_id=order_id))


# ==============================================================================
#  ROTAS DO CLIENTE
# ==============================================================================

@order_bp.route('/<int:order_id>/confirmar', methods=['POST'])
@login_required
@require_order_ownership(required_role='client')
@rate_limit('confirm_service', max_attempts=10, window_seconds=60)
def confirmar_servico(order_id, order=None):
    """Cliente confirma que o serviço foi bem executado"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('order.listar_ordens'))
    
    # Validar permissão para a ação específica
    is_allowed, error_msg = SecurityValidator.validate_order_action_permission(
        order, user.id, 'confirm'
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    try:
        result = OrderManagementService.confirm_service(order_id, user.id)
        
        flash(result['message'], 'success')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao confirmar ordem {order_id}: {e}")
        flash('Erro ao confirmar serviço.', 'error')
    
    return redirect(url_for('order.ver_ordem', order_id=order_id))


@order_bp.route('/<int:order_id>/contestar', methods=['GET', 'POST'])
@login_required
@require_order_ownership(required_role='client')
def contestar_servico(order_id, order=None):
    """
    Cliente contesta o serviço
    
    GET: Exibe formulário de contestação
    POST: Processa contestação com upload de arquivos de prova
    """
    user = AuthService.get_current_user()
    
    # Validar que usuário é cliente
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('order.listar_ordens'))
    
    if request.method == 'GET':
        # Validar se pode contestar
        is_allowed, error_msg = SecurityValidator.validate_order_action_permission(
            order, user.id, 'dispute'
        )
        if not is_allowed:
            flash(error_msg, 'error')
            return redirect(url_for('order.ver_ordem', order_id=order_id))
        
        # Renderizar template cliente/contestar_ordem.html
        return render_template('cliente/contestar_ordem.html', user=user, order=order)
    
    # POST: Processar contestação com rate limiting
    is_allowed, error_msg = SecurityValidator.check_rate_limit(
        user.id, 'open_dispute', max_attempts=3, window_seconds=300
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    try:
        # Obter motivo do formulário e sanitizar
        reason = SecurityValidator.sanitize_input(
            request.form.get('reason', '').strip(),
            max_length=2000
        )
        
        # Validar motivo (mínimo 20 caracteres)
        if not reason or len(reason) < 20:
            flash('Motivo da contestação deve ter pelo menos 20 caracteres.', 'error')
            return redirect(url_for('order.contestar_servico', order_id=order_id))
        
        # Obter arquivos de prova do request.files
        evidence_files = []
        if 'evidence' in request.files:
            files = request.files.getlist('evidence')
            
            # Validar múltiplos arquivos
            is_valid, error_msg, valid_files = SecurityValidator.validate_multiple_files(files)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('order.contestar_servico', order_id=order_id))
            
            evidence_files = valid_files
        
        # Chamar OrderManagementService.open_dispute()
        result = OrderManagementService.open_dispute(
            order_id=order_id,
            client_id=user.id,
            reason=reason,
            evidence_files=evidence_files
        )
        
        # Exibir mensagem de sucesso
        flash(result['message'], 'success')
        
        # Informar sobre arquivos enviados
        if result.get('evidence_files_count', 0) > 0:
            flash(
                f"{result['evidence_files_count']} arquivo(s) de prova enviado(s) com sucesso.",
                'info'
            )
        
        # Redirecionar para detalhes da ordem
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except ValueError as e:
        # Exibir mensagem de erro de validação
        flash(str(e), 'error')
        logger.warning(f"Erro de validação ao contestar ordem {order_id}: {e}")
    except Exception as e:
        # Exibir mensagem de erro genérico
        logger.error(f"Erro ao contestar ordem {order_id}: {e}", exc_info=True)
        flash('Erro ao abrir contestação. Tente novamente.', 'error')
    
    # Redirecionar para detalhes da ordem em caso de erro
    return redirect(url_for('order.ver_ordem', order_id=order_id))


# ==============================================================================
#  ROTAS DE CONTESTAÇÃO
# ==============================================================================

@order_bp.route('/<int:order_id>/responder-contestacao', methods=['GET', 'POST'])
@login_required
@require_order_ownership(required_role='provider')
def responder_contestacao(order_id, order=None):
    """Prestador responde à contestação do cliente"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('order.listar_ordens'))
    
    if order.status != 'contestada':
        flash('Esta ordem não está contestada.', 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    if order.dispute_provider_response:
        flash('Você já respondeu a esta contestação.', 'info')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    if request.method == 'GET':
        return render_template('prestador/responder_contestacao.html', user=user, order=order)
    
    # POST: Processar resposta com rate limiting
    is_allowed, error_msg = SecurityValidator.check_rate_limit(
        user.id, 'respond_dispute', max_attempts=3, window_seconds=300
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    try:
        # Obter resposta do formulário e sanitizar
        response = SecurityValidator.sanitize_input(
            request.form.get('response', '').strip(),
            max_length=2000
        )
        
        # Validar resposta (mínimo 20 caracteres)
        if not response or len(response) < 20:
            flash('Resposta deve ter pelo menos 20 caracteres.', 'error')
            return redirect(url_for('order.responder_contestacao', order_id=order_id))
        
        # Upload de arquivos de prova
        evidence_files = []
        if 'evidence' in request.files:
            files = request.files.getlist('evidence')
            is_valid, error_msg, valid_files = SecurityValidator.validate_multiple_files(files)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('order.responder_contestacao', order_id=order_id))
            evidence_files = valid_files
        
        # Chamar OrderManagementService.provider_respond_to_dispute()
        result = OrderManagementService.provider_respond_to_dispute(
            order_id=order_id,
            provider_id=user.id,
            response=response,
            evidence_files=evidence_files
        )
        
        # Exibir mensagem de sucesso
        flash(result['message'], 'success')
        
        # Informar sobre arquivos enviados
        if result.get('evidence_files_count', 0) > 0:
            flash(
                f"{result['evidence_files_count']} arquivo(s) de prova enviado(s) com sucesso.",
                'info'
            )
        
        # Redirecionar para detalhes da ordem
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except ValueError as e:
        # Exibir mensagem de erro de validação
        flash(str(e), 'error')
        logger.warning(f"Erro de validação ao responder contestação {order_id}: {e}")
    except Exception as e:
        # Exibir mensagem de erro genérico
        logger.error(f"Erro ao responder contestação {order_id}: {e}", exc_info=True)
        flash('Erro ao enviar resposta. Tente novamente.', 'error')
    
    # Redirecionar para detalhes da ordem em caso de erro
    return redirect(url_for('order.ver_ordem', order_id=order_id))


# ==============================================================================
#  ROTAS DE CANCELAMENTO (Cliente e Prestador)
# ==============================================================================

@order_bp.route('/<int:order_id>/cancelar', methods=['POST'])
@login_required
@require_order_ownership()
@rate_limit('cancel_order', max_attempts=3, window_seconds=300)
def cancelar_ordem(order_id, order=None):
    """Cancela uma ordem (antes do serviço ser marcado como concluído)"""
    user = AuthService.get_current_user()
    
    # Validar permissão para a ação específica
    is_allowed, error_msg = SecurityValidator.validate_order_action_permission(
        order, user.id, 'cancel'
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
    
    try:
        # Sanitizar motivo do cancelamento
        reason = SecurityValidator.sanitize_input(
            request.form.get('reason', '').strip(),
            max_length=500
        )
        
        if not reason:
            flash('Motivo do cancelamento é obrigatório.', 'error')
            return redirect(url_for('order.ver_ordem', order_id=order_id))
        
        result = OrderManagementService.cancel_order(order_id, user.id, reason)
        
        flash(result['message'], 'warning')
        return redirect(url_for('order.ver_ordem', order_id=order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao cancelar ordem {order_id}: {e}")
        flash('Erro ao cancelar ordem.', 'error')
    
    return redirect(url_for('order.ver_ordem', order_id=order_id))


# ==============================================================================
#  API ENDPOINTS (AJAX)
# ==============================================================================

@order_bp.route('/<int:order_id>/status', methods=['GET'])
@login_required
@require_order_ownership()
def get_order_status(order_id, order=None):
    """
    API: Retorna status atual da ordem em JSON
    
    Returns:
        JSON com status, hours_remaining, can_confirm, can_dispute
    """
    user = AuthService.get_current_user()
    
    try:
        if not order:
            order = Order.query.get_or_404(order_id)
        
        # Retornar JSON com status, hours_remaining, can_confirm, can_dispute
        return jsonify({
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'hours_remaining': order.hours_until_auto_confirmation,
            'can_confirm': order.can_be_confirmed,
            'can_dispute': order.can_be_disputed,
            'can_cancel': order.can_be_cancelled,
            'can_mark_completed': order.can_be_marked_completed,
            'is_near_deadline': order.is_near_auto_confirmation
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar status da ordem {order_id}: {e}")
        return jsonify({'error': 'Erro ao buscar status'}), 500


@order_bp.route('/estatisticas', methods=['GET'])
@login_required
def get_estatisticas():
    """
    API: Retorna estatísticas do dashboard em JSON
    
    Returns:
        JSON com estatísticas das ordens do usuário
    """
    user = AuthService.get_current_user()
    active_role = session.get('active_role', 'cliente')
    
    try:
        # Obter estatísticas do dashboard usando o serviço
        statistics = OrderManagementService.get_order_statistics(user.id, active_role)
        
        return jsonify({
            'success': True,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': 'Erro ao buscar estatísticas'}), 500
