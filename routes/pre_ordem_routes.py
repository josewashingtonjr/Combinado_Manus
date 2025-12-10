#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rotas para gerenciamento de pré-ordens

Este módulo gerencia todas as rotas relacionadas a pré-ordens, incluindo:
- Visualização de detalhes
- Criação de propostas
- Aceitação/rejeição de propostas
- Aceitação de termos finais
- Cancelamento
- Consulta de histórico

Requirements: 2.1, 3.1, 3.2, 4.1, 4.2, 4.4, 5.1, 7.1, 8.1, 17.3
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, PreOrder, PreOrderProposal, PreOrderHistory, User
from services.auth_service import login_required, AuthService
from services.pre_order_service import PreOrderService
from services.pre_order_proposal_service import PreOrderProposalService
from services.security_validator import SecurityValidator
from services.rate_limiter_service import (
    limiter,
    limit_pre_order_proposals,
    limit_pre_order_cancellations,
    limit_general_requests,
    log_rate_limit_exceeded
)
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

pre_ordem_bp = Blueprint('pre_ordem', __name__, url_prefix='/pre-ordem')


# ==============================================================================
#  DECORADOR DE VALIDAÇÃO DE PERMISSÃO
# ==============================================================================

def require_pre_order_participant():
    """
    Decorador para validar que o usuário é participante da pré-ordem
    (cliente ou prestador)
    """
    def decorator(f):
        def wrapper(pre_order_id, *args, **kwargs):
            user = AuthService.get_current_user()
            
            # Buscar pré-ordem
            pre_order = PreOrder.query.get_or_404(pre_order_id)
            
            # Validar que usuário é cliente ou prestador
            if user.id not in [pre_order.client_id, pre_order.provider_id]:
                # Logging detalhado de tentativa de acesso não autorizado
                logger.warning(
                    f"ACESSO NÃO AUTORIZADO - Usuário {user.id} ({user.nome}) "
                    f"tentou acessar pré-ordem {pre_order_id} sem permissão. "
                    f"IP: {request.remote_addr}, "
                    f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}, "
                    f"Rota: {request.endpoint}"
                )
                
                # Registrar tentativa de acesso não autorizado
                log_rate_limit_exceeded(
                    user_id=user.id,
                    action=f"acesso_nao_autorizado_pre_ordem_{pre_order_id}",
                    ip=request.remote_addr
                )
                
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'unauthorized',
                        'message': 'Você não tem permissão para acessar esta pré-ordem'
                    }), 403
                
                flash('Você não tem permissão para acessar esta pré-ordem.', 'error')
                return redirect(url_for('home.index'))
            
            # Passar pré-ordem para a função
            return f(pre_order_id, pre_order=pre_order, *args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# ==============================================================================
#  VISUALIZAÇÃO DE DETALHES
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>')
@login_required
@limiter.limit("60 per minute")  # Limite de visualizações
@require_pre_order_participant()
def ver_detalhes(pre_order_id, pre_order=None):
    """
    Visualiza detalhes completos de uma pré-ordem
    
    GET /pre-ordem/<id>
    
    Exibe:
    - Informações principais (título, descrição, valor, prazo)
    - Status atual com indicadores visuais
    - Histórico de alterações em timeline
    - Proposta ativa se existir
    - Botões de ação disponíveis
    
    Validações:
    - Usuário deve ser cliente ou prestador da pré-ordem
    
    Requirements: 9.2, 9.3, 10.1-10.4, 13.1-13.4, 18.1
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter detalhes completos da pré-ordem
        details = PreOrderService.get_pre_order_details(
            pre_order_id=pre_order_id,
            user_id=user.id
        )
        
        # Determinar se é cliente ou prestador
        is_client = (user.id == pre_order.client_id)
        user_role = 'cliente' if is_client else 'prestador'
        
        # Determinar ações disponíveis
        can_propose = pre_order.status in ['em_negociacao', 'aguardando_resposta']
        can_accept_terms = (
            pre_order.status in ['em_negociacao', 'aguardando_resposta'] and
            not pre_order.has_active_proposal
        )
        can_cancel = pre_order.status not in ['convertida', 'cancelada', 'expirada']
        
        # Verificar se há proposta pendente que o usuário pode responder
        active_proposal = details.get('active_proposal')
        can_respond_proposal = False
        if active_proposal and active_proposal['status'] == 'pendente':
            # Usuário pode responder se não foi ele quem propôs
            can_respond_proposal = (active_proposal['proposed_by'] != user.id)
        
        # Usar template genérico de pré-ordem
        template = 'pre_ordem/detalhes.html'
        
        logger.info(
            f"Usuário {user.id} ({user.nome}) visualizando pré-ordem {pre_order_id}. "
            f"Papel: {user_role}, Status: {pre_order.status}"
        )
        
        # Buscar objetos originais para o template (com métodos datetime)
        client = User.query.get(pre_order.client_id)
        provider = User.query.get(pre_order.provider_id)
        
        # Buscar histórico com objetos completos
        history_items = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order_id
        ).order_by(PreOrderHistory.created_at.desc()).all()
        
        # Adicionar actor a cada item do histórico
        for item in history_items:
            item.actor = User.query.get(item.actor_id) if item.actor_id else None
        
        return render_template(
            template,
            user=user,
            pre_order=pre_order,  # Passar objeto original, não dicionário
            client=client,
            provider=provider,
            active_proposal=pre_order.get_active_proposal(),
            history_items=history_items,
            state_description=details['state_description'],
            user_role=user_role,
            is_client=is_client,
            can_propose=can_propose,
            can_propose_changes=can_propose,  # Alias para o template
            can_accept_terms=can_accept_terms,
            can_cancel=can_cancel,
            can_respond_proposal=can_respond_proposal
        )
        
    except PermissionError as e:
        logger.warning(f"Erro de permissão ao visualizar pré-ordem {pre_order_id}: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('home.index'))
    except Exception as e:
        logger.error(f"Erro ao visualizar pré-ordem {pre_order_id}: {str(e)}")
        flash('Erro ao carregar detalhes da pré-ordem.', 'error')
        return redirect(url_for('home.index'))


# ==============================================================================
#  CRIAÇÃO DE PROPOSTAS
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/propor-alteracao', methods=['POST'])
@login_required
@limit_pre_order_proposals()  # Máximo 10 propostas por hora
@require_pre_order_participant()
def propor_alteracao(pre_order_id, pre_order=None):
    """
    Cria uma proposta de alteração para a pré-ordem
    
    POST /pre-ordem/<id>/propor-alteracao
    
    Parâmetros:
    - proposed_value: Novo valor proposto (opcional)
    - proposed_delivery_date: Nova data de entrega (opcional)
    - proposed_description: Nova descrição (opcional)
    - justification: Justificativa da proposta (obrigatório, mín. 50 caracteres)
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    - Pré-ordem deve estar em estado válido (em_negociacao ou aguardando_resposta)
    - Pelo menos um campo deve ser alterado
    - Justificativa é obrigatória
    - Propostas extremas exigem justificativa detalhada
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 19.1-19.3, 19.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter dados do formulário
        proposed_value_str = request.form.get('proposed_value', '').strip()
        proposed_delivery_date_str = request.form.get('proposed_delivery_date', '').strip()
        proposed_description = request.form.get('proposed_description', '').strip()
        justification = request.form.get('justification', '').strip()
        
        # Sanitizar inputs
        justification = SecurityValidator.sanitize_input(justification, max_length=2000)
        proposed_description = SecurityValidator.sanitize_input(proposed_description, max_length=5000) if proposed_description else None
        
        # Converter e validar valor se fornecido
        proposed_value = None
        if proposed_value_str:
            try:
                proposed_value = SecurityValidator.validate_monetary_value(
                    proposed_value_str,
                    field_name="Valor proposto"
                )
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
        # Converter e validar data se fornecida
        proposed_delivery_date = None
        if proposed_delivery_date_str:
            try:
                proposed_delivery_date = SecurityValidator.validate_date_future(
                    proposed_delivery_date_str,
                    field_name="Data de entrega proposta"
                )
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
        # Criar proposta
        result = PreOrderProposalService.create_proposal(
            pre_order_id=pre_order_id,
            user_id=user.id,
            proposed_value=proposed_value,
            proposed_delivery_date=proposed_delivery_date,
            proposed_description=proposed_description,
            justification=justification
        )
        
        if result['success']:
            flash(result['message'], 'success')
            
            # Avisar se proposta é extrema
            if result.get('is_extreme'):
                flash(
                    f"⚠️ Proposta extrema detectada: {result['extreme_reason']}. "
                    f"A outra parte será notificada sobre esta alteração significativa.",
                    'warning'
                )
        else:
            flash(result.get('error', 'Erro ao criar proposta'), 'error')
        
        return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao criar proposta para pré-ordem {pre_order_id}: {str(e)}")
        flash('Erro ao criar proposta. Tente novamente.', 'error')
    
    return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))


# ==============================================================================
#  ACEITAÇÃO DE PROPOSTAS
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/aceitar-proposta/<int:proposal_id>', methods=['POST'])
@login_required
@limiter.limit("30 per hour")  # Limite de aceitações
@require_pre_order_participant()
def aceitar_proposta(pre_order_id, proposal_id, pre_order=None):
    """
    Aceita uma proposta de alteração
    
    POST /pre-ordem/<id>/aceitar-proposta/<proposal_id>
    
    Quando aceita:
    - Valores da pré-ordem são atualizados
    - Aceitações são resetadas (ambas as partes precisam aceitar novos termos)
    - Estado volta para em_negociacao
    - Notificações são enviadas
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    - Usuário não pode aceitar sua própria proposta
    - Proposta deve estar pendente
    
    Requirements: 3.4, 4.1, 4.2, 4.3, 4.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Aceitar proposta
        result = PreOrderProposalService.accept_proposal(
            proposal_id=proposal_id,
            user_id=user.id
        )
        
        if result['success']:
            flash(result['message'], 'success')
            
            # Informar sobre alterações aplicadas
            if result.get('changes_applied'):
                flash(
                    f"Alterações aplicadas: {', '.join(result['changes_applied'])}",
                    'info'
                )
        else:
            flash(result.get('error', 'Erro ao aceitar proposta'), 'error')
        
        return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao aceitar proposta {proposal_id}: {str(e)}")
        flash('Erro ao aceitar proposta. Tente novamente.', 'error')
    
    return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))


# ==============================================================================
#  REJEIÇÃO DE PROPOSTAS
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/rejeitar-proposta/<int:proposal_id>', methods=['POST'])
@login_required
@limiter.limit("30 per hour")  # Limite de rejeições
@require_pre_order_participant()
def rejeitar_proposta(pre_order_id, proposal_id, pre_order=None):
    """
    Rejeita uma proposta de alteração
    
    POST /pre-ordem/<id>/rejeitar-proposta/<proposal_id>
    
    Parâmetros:
    - rejection_reason: Motivo da rejeição (opcional)
    
    Quando rejeitada:
    - Valores da pré-ordem NÃO são alterados
    - Estado volta para em_negociacao
    - Notificações são enviadas
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    - Usuário não pode rejeitar sua própria proposta
    - Proposta deve estar pendente
    
    Requirements: 4.1, 4.4, 4.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter motivo da rejeição (opcional)
        rejection_reason = request.form.get('rejection_reason', '').strip()
        if rejection_reason:
            rejection_reason = SecurityValidator.sanitize_input(rejection_reason, max_length=500)
        
        # Rejeitar proposta
        result = PreOrderProposalService.reject_proposal(
            proposal_id=proposal_id,
            user_id=user.id,
            rejection_reason=rejection_reason if rejection_reason else None
        )
        
        if result['success']:
            flash(result['message'], 'info')
        else:
            flash(result.get('error', 'Erro ao rejeitar proposta'), 'error')
        
        return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao rejeitar proposta {proposal_id}: {str(e)}")
        flash('Erro ao rejeitar proposta. Tente novamente.', 'error')
    
    return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))


# ==============================================================================
#  ACEITAÇÃO DE TERMOS FINAIS
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/aceitar-termos', methods=['POST'])
@login_required
@limiter.limit("20 per hour")  # Limite de aceitação de termos
@require_pre_order_participant()
def aceitar_termos(pre_order_id, pre_order=None):
    """
    Aceita os termos finais da pré-ordem
    
    POST /pre-ordem/<id>/aceitar-termos
    
    Quando aceita:
    - Marca aceitação do usuário
    - Valida saldo disponível
    - Se ambas as partes aceitaram, pré-ordem fica pronta para conversão
    - Notificações são enviadas
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    - Pré-ordem deve estar em estado válido
    - Não pode haver proposta pendente
    - Usuário deve ter saldo suficiente
    
    Requirements: 5.1, 7.1, 7.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Aceitar termos
        result = PreOrderService.accept_terms(
            pre_order_id=pre_order_id,
            user_id=user.id
        )
        
        if result['success']:
            flash(result['message'], 'success')
            
            # Se alcançou aceitação mútua, destacar
            if result.get('has_mutual_acceptance'):
                flash(
                    '🎉 Ambas as partes aceitaram os termos! '
                    'A pré-ordem será convertida em ordem automaticamente.',
                    'success'
                )
        else:
            error = result.get('error')
            
            # Tratamento especial para saldo insuficiente
            if error == 'Saldo insuficiente':
                flash(result.get('message'), 'warning')
                
                # Sugerir adição de saldo
                shortfall = result.get('shortfall', 0)
                flash(
                    f'💡 Adicione pelo menos R$ {shortfall:.2f} ao seu saldo para continuar.',
                    'info'
                )
            else:
                flash(result.get('message', 'Erro ao aceitar termos'), 'error')
        
        return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao aceitar termos da pré-ordem {pre_order_id}: {str(e)}")
        flash('Erro ao aceitar termos. Tente novamente.', 'error')
    
    return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))


# ==============================================================================
#  CANCELAMENTO
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/cancelar', methods=['POST'])
@login_required
@limit_pre_order_cancellations()  # Máximo 5 cancelamentos por dia
@require_pre_order_participant()
def cancelar(pre_order_id, pre_order=None):
    """
    Cancela uma pré-ordem
    
    POST /pre-ordem/<id>/cancelar
    
    Parâmetros:
    - reason: Motivo do cancelamento (obrigatório, mín. 10 caracteres)
    
    Quando cancelada:
    - Status muda para cancelada
    - Nenhuma ordem é criada
    - Notificações são enviadas
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    - Pré-ordem não pode estar convertida, cancelada ou expirada
    - Motivo é obrigatório
    
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter motivo do cancelamento
        reason = request.form.get('reason', '').strip()
        
        # Sanitizar motivo
        reason = SecurityValidator.sanitize_input(reason, max_length=1000)
        
        # Validar motivo
        if not reason or len(reason) < 10:
            flash('Motivo do cancelamento é obrigatório e deve ter pelo menos 10 caracteres.', 'error')
            return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
        # Cancelar pré-ordem
        result = PreOrderService.cancel_pre_order(
            pre_order_id=pre_order_id,
            user_id=user.id,
            reason=reason
        )
        
        if result['success']:
            flash(result['message'], 'warning')
        else:
            flash(result.get('error', 'Erro ao cancelar pré-ordem'), 'error')
        
        return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except PermissionError as e:
        flash(str(e), 'error')
    except Exception as e:
        logger.error(f"Erro ao cancelar pré-ordem {pre_order_id}: {str(e)}")
        flash('Erro ao cancelar pré-ordem. Tente novamente.', 'error')
    
    return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))


# ==============================================================================
#  CONSULTA DE HISTÓRICO
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/historico')
@login_required
@limiter.limit("30 per minute")  # Limite de consultas de histórico
@require_pre_order_participant()
def consultar_historico(pre_order_id, pre_order=None):
    """
    Consulta o histórico completo de uma pré-ordem
    
    GET /pre-ordem/<id>/historico
    
    Retorna JSON com:
    - Lista de eventos ordenados por data
    - Detalhes de cada evento (tipo, ator, descrição, data)
    - Dados adicionais do evento
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    
    Requirements: 10.1, 10.2, 17.1, 17.2, 17.3
    """
    user = AuthService.get_current_user()
    
    try:
        # Buscar histórico
        history_entries = PreOrderHistory.query.filter_by(
            pre_order_id=pre_order_id
        ).order_by(PreOrderHistory.created_at.desc()).all()
        
        # Formatar histórico
        history = []
        for entry in history_entries:
            actor = User.query.get(entry.actor_id) if entry.actor_id else None
            
            history.append({
                'id': entry.id,
                'event_type': entry.event_type,
                'event_type_display': entry.event_type_display,
                'actor_id': entry.actor_id,
                'actor_name': actor.nome if actor else 'Sistema',
                'description': entry.description,
                'event_data': entry.event_data,
                'created_at': entry.created_at.isoformat(),
                'created_at_formatted': entry.created_at.strftime('%d/%m/%Y %H:%M')
            })
        
        logger.info(
            f"Usuário {user.id} consultou histórico da pré-ordem {pre_order_id}. "
            f"Total de eventos: {len(history)}"
        )
        
        return jsonify({
            'success': True,
            'pre_order_id': pre_order_id,
            'history': history,
            'total_events': len(history)
        })
        
    except Exception as e:
        logger.error(f"Erro ao consultar histórico da pré-ordem {pre_order_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao consultar histórico'
        }), 500


# ==============================================================================
#  API: VERIFICAR SALDO PARA ACEITAÇÃO
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/verificar-saldo', methods=['GET'])
@login_required
@limiter.limit("30 per minute")  # Limite de verificações de saldo
@require_pre_order_participant()
def verificar_saldo(pre_order_id, pre_order=None):
    """
    Verifica se o usuário tem saldo suficiente para aceitar os termos
    
    GET /pre-ordem/<id>/verificar-saldo
    
    Retorna JSON com:
    - is_sufficient: Se o saldo é suficiente
    - current_balance: Saldo atual
    - required_amount: Valor necessário
    - shortfall: Quanto falta (se insuficiente)
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    
    Requirements: 7.1, 7.2, 7.3
    """
    user = AuthService.get_current_user()
    
    try:
        from services.wallet_service import WalletService
        from services.config_service import ConfigService
        
        # Determinar se é cliente ou prestador
        is_client = (user.id == pre_order.client_id)
        
        # Obter saldo atual
        wallet_info = WalletService.get_wallet_info(user.id)
        current_balance = Decimal(str(wallet_info['balance']))
        
        # Calcular valor necessário
        if is_client:
            # Cliente precisa de valor do serviço + taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            required_amount = pre_order.current_value + contestation_fee
        else:
            # Prestador precisa apenas da taxa de contestação
            contestation_fee = ConfigService.get_contestation_fee()
            required_amount = contestation_fee
        
        # Verificar suficiência
        is_sufficient = current_balance >= required_amount
        shortfall = max(Decimal('0'), required_amount - current_balance)
        
        return jsonify({
            'success': True,
            'pre_order_id': pre_order_id,
            'user_role': 'cliente' if is_client else 'prestador',
            'balance_check': {
                'is_sufficient': is_sufficient,
                'current_balance': float(current_balance),
                'required_amount': float(required_amount),
                'shortfall': float(shortfall),
                'service_value': float(pre_order.current_value),
                'contestation_fee': float(contestation_fee)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar saldo para pré-ordem {pre_order_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar saldo'
        }), 500


# ==============================================================================
#  API: STATUS DA PRÉ-ORDEM
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/status', methods=['GET'])
@login_required
@limiter.limit("60 per minute")  # Limite de consultas de status
@require_pre_order_participant()
def obter_status(pre_order_id, pre_order=None):
    """
    Retorna o status atual da pré-ordem em JSON
    
    GET /pre-ordem/<id>/status
    
    Útil para atualizações em tempo real via AJAX
    
    Retorna:
    - status: Estado atual
    - client_accepted_terms: Se cliente aceitou
    - provider_accepted_terms: Se prestador aceitou
    - has_active_proposal: Se há proposta pendente
    - can_be_converted: Se pode ser convertida
    - is_expired: Se expirou
    - days_until_expiration: Dias até expirar
    
    Requirements: 20.1-20.5
    """
    try:
        return jsonify({
            'success': True,
            'pre_order_id': pre_order_id,
            'status': pre_order.status,
            'status_display': pre_order.status_display,
            'client_accepted_terms': pre_order.client_accepted_terms,
            'provider_accepted_terms': pre_order.provider_accepted_terms,
            'has_mutual_acceptance': pre_order.has_mutual_acceptance,
            'has_active_proposal': pre_order.has_active_proposal,
            'can_be_converted': pre_order.can_be_converted,
            'is_expired': pre_order.is_expired,
            'days_until_expiration': pre_order.days_until_expiration,
            'is_near_expiration': pre_order.is_near_expiration,
            'updated_at': pre_order.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status da pré-ordem {pre_order_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao obter status'
        }), 500


# ==============================================================================
#  API: VERIFICAR SALDO PARA ACEITAÇÃO (POST)
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/verificar-saldo', methods=['POST'])
@login_required
@limiter.limit("30 per minute")  # Limite de verificações de saldo
@require_pre_order_participant()
def verificar_saldo_post(pre_order_id, pre_order=None):
    """
    Verifica se o usuário tem saldo suficiente para aceitar os termos (POST)
    
    POST /pre-ordem/<id>/verificar-saldo
    
    Retorna JSON com:
    - is_sufficient: Se o saldo é suficiente
    - current_balance: Saldo atual
    - required_amount: Valor necessário
    - shortfall: Quanto falta (se insuficiente)
    - suggested_amount: Valor sugerido para adicionar
    
    Validações:
    - Usuário deve ser participante da pré-ordem
    
    Requirements: 7.1, 7.2, 7.3
    """
    user = AuthService.get_current_user()
    
    try:
        from services.wallet_service import WalletService
        from services.config_service import ConfigService
        
        # Determinar se é cliente ou prestador
        is_client = (user.id == pre_order.client_id)
        user_role = 'cliente' if is_client else 'prestador'
        
        # Obter saldo atual
        wallet_info = WalletService.get_wallet_info(user.id)
        current_balance = Decimal(str(wallet_info['balance']))
        
        # Calcular valor necessário
        contestation_fee = ConfigService.get_contestation_fee()
        
        if is_client:
            # Cliente precisa de valor do serviço + taxa de contestação
            required_amount = pre_order.current_value + contestation_fee
            breakdown = {
                'service_value': float(pre_order.current_value),
                'contestation_fee': float(contestation_fee),
                'description': f'Valor do serviço (R$ {pre_order.current_value:.2f}) + Taxa de contestação (R$ {contestation_fee:.2f})'
            }
        else:
            # Prestador precisa apenas da taxa de contestação
            required_amount = contestation_fee
            breakdown = {
                'contestation_fee': float(contestation_fee),
                'description': f'Taxa de contestação (R$ {contestation_fee:.2f})'
            }
        
        # Verificar suficiência
        is_sufficient = current_balance >= required_amount
        shortfall = max(Decimal('0'), required_amount - current_balance)
        
        # Calcular valor sugerido para adicionar (shortfall + 10% de margem)
        if shortfall > 0:
            suggested_amount = shortfall * Decimal('1.1')  # 10% de margem
            suggested_amount = suggested_amount.quantize(Decimal('0.01'))  # Arredondar para 2 casas
        else:
            suggested_amount = Decimal('0')
        
        return jsonify({
            'success': True,
            'pre_order_id': pre_order_id,
            'user_role': user_role,
            'balance_check': {
                'is_sufficient': is_sufficient,
                'current_balance': float(current_balance),
                'required_amount': float(required_amount),
                'shortfall': float(shortfall),
                'suggested_amount': float(suggested_amount),
                'breakdown': breakdown
            },
            'message': (
                'Saldo suficiente para aceitar os termos.' if is_sufficient else
                f'Saldo insuficiente. Você precisa de R$ {required_amount:.2f}, mas tem apenas R$ {current_balance:.2f}. '
                f'Adicione pelo menos R$ {shortfall:.2f} para continuar.'
            )
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar saldo para pré-ordem {pre_order_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar saldo',
            'message': str(e)
        }), 500


# ==============================================================================
#  API: ADICIONAR SALDO E ACEITAR TERMOS
# ==============================================================================

@pre_ordem_bp.route('/<int:pre_order_id>/adicionar-saldo-e-aceitar', methods=['POST'])
@login_required
@limiter.limit("10 per hour")  # Limite de adições de saldo
@require_pre_order_participant()
def adicionar_saldo_e_aceitar(pre_order_id, pre_order=None):
    """
    Fluxo integrado: adicionar saldo e aceitar termos automaticamente
    
    POST /pre-ordem/<id>/adicionar-saldo-e-aceitar
    
    Parâmetros:
    - amount_to_add: Valor a adicionar ao saldo
    - payment_method: Método de pagamento (opcional, padrão: 'pix')
    
    Este endpoint permite que o usuário adicione saldo suficiente e aceite
    os termos em uma única operação.
    
    Requirements: 7.3, 7.4
    """
    user = AuthService.get_current_user()
    
    try:
        from services.wallet_service import WalletService
        from services.config_service import ConfigService
        
        # Obter dados do formulário ou JSON
        if request.is_json:
            data = request.get_json()
            amount_to_add = data.get('amount_to_add')
            payment_method = data.get('payment_method', 'pix')
        else:
            amount_to_add = request.form.get('amount_to_add')
            payment_method = request.form.get('payment_method', 'pix')
        
        # Validar valor
        if not amount_to_add:
            return jsonify({
                'success': False,
                'error': 'Valor a adicionar é obrigatório'
            }), 400
        
        try:
            amount_to_add = SecurityValidator.validate_monetary_value(
                amount_to_add,
                field_name="Valor a adicionar",
                min_value=Decimal('0.01'),
                max_value=Decimal('10000.00')
            )
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Determinar se é cliente ou prestador
        is_client = (user.id == pre_order.client_id)
        user_role = 'cliente' if is_client else 'prestador'
        
        # Calcular valor necessário
        contestation_fee = ConfigService.get_contestation_fee()
        
        if is_client:
            required_amount = pre_order.current_value + contestation_fee
        else:
            required_amount = contestation_fee
        
        # Obter saldo atual
        wallet_info = WalletService.get_wallet_info(user.id)
        current_balance = Decimal(str(wallet_info['balance']))
        
        # Calcular novo saldo após adição
        new_balance = current_balance + amount_to_add
        
        # Verificar se o novo saldo será suficiente
        if new_balance < required_amount:
            shortfall_after_addition = required_amount - new_balance
            return jsonify({
                'success': False,
                'error': 'Valor insuficiente',
                'message': f'Após adicionar R$ {amount_to_add:.2f}, ainda faltarão R$ {shortfall_after_addition:.2f}. '
                          f'Adicione pelo menos R$ {required_amount - current_balance:.2f}.'
            }), 400
        
        # Adicionar saldo (usando admin_sell_tokens_to_user para simular compra de tokens)
        description = f'Adição de saldo para aceitar termos da pré-ordem #{pre_order_id}'
        
        add_result = WalletService.admin_sell_tokens_to_user(
            user_id=user.id,
            amount=float(amount_to_add),
            description=description
        )
        
        if not add_result.get('success'):
            return jsonify({
                'success': False,
                'error': 'Erro ao adicionar saldo',
                'message': add_result.get('error', 'Erro desconhecido')
            }), 500
        
        # Agora aceitar os termos
        accept_result = PreOrderService.accept_terms(
            pre_order_id=pre_order_id,
            user_id=user.id
        )
        
        if accept_result['success']:
            logger.info(
                f"Usuário {user.id} ({user_role}) adicionou R$ {amount_to_add:.2f} e aceitou termos "
                f"da pré-ordem {pre_order_id}"
            )
            
            return jsonify({
                'success': True,
                'message': f'Saldo adicionado (R$ {amount_to_add:.2f}) e termos aceitos com sucesso!',
                'balance_added': float(amount_to_add),
                'new_balance': float(new_balance),
                'accept_result': accept_result
            })
        else:
            # Se falhou ao aceitar, o saldo já foi adicionado
            # Informar o usuário
            return jsonify({
                'success': False,
                'error': 'Saldo adicionado, mas erro ao aceitar termos',
                'message': f'O saldo de R$ {amount_to_add:.2f} foi adicionado, mas houve um erro ao aceitar os termos: '
                          f'{accept_result.get("error", "Erro desconhecido")}. Tente aceitar os termos novamente.',
                'balance_added': float(amount_to_add),
                'new_balance': float(new_balance)
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao adicionar saldo e aceitar termos da pré-ordem {pre_order_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar solicitação',
            'message': str(e)
        }), 500


# ==============================================================================
#  ROTAS DE TEMPO REAL (SSE E PRESENÇA)
# ==============================================================================

# Cache de presença em memória (em produção, usar Redis)
_presence_cache = {}

@pre_ordem_bp.route('/<int:pre_order_id>/stream')
@login_required
@require_pre_order_participant()
def stream_updates(pre_order_id, pre_order=None):
    """
    Stream de atualizações em tempo real via Server-Sent Events (SSE)
    
    GET /pre-ordem/<id>/stream
    
    Envia eventos:
    - status_change: Quando status da pré-ordem muda
    - proposal_received: Quando nova proposta é criada
    - proposal_accepted: Quando proposta é aceita
    - proposal_rejected: Quando proposta é rejeitada
    - mutual_acceptance: Quando ambas as partes aceitam
    - presence: Atualização de presença da outra parte
    - heartbeat: Sinal de conexão ativa
    
    Requirements: 20.1-20.5
    """
    import time
    import json
    from flask import Response, stream_with_context
    
    user = AuthService.get_current_user()
    
    def generate():
        """Gerador de eventos SSE"""
        # Buscar pré-ordem fresca do banco para evitar problemas de sessão
        current_pre_order = PreOrder.query.get(pre_order_id)
        if not current_pre_order:
            yield format_sse_event({
                'type': 'error',
                'message': 'Pré-ordem não encontrada'
            })
            return
        
        last_status = current_pre_order.status
        last_proposal_count = current_pre_order.proposals.count()
        last_client_accepted = current_pre_order.client_accepted_terms
        last_provider_accepted = current_pre_order.provider_accepted_terms
        
        # Enviar evento de conexão
        yield format_sse_event({
            'type': 'connected',
            'message': 'Conexão estabelecida',
            'pre_order_id': pre_order_id
        })
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # Buscar pré-ordem fresca do banco a cada iteração
                current_pre_order = PreOrder.query.get(pre_order_id)
                if not current_pre_order:
                    break
                
                # Verificar mudança de status
                if current_pre_order.status != last_status:
                    yield format_sse_event({
                        'type': 'status_change',
                        'old_status': last_status,
                        'new_status': current_pre_order.status,
                        'status_display': current_pre_order.status_display
                    }, event='status_change')
                    last_status = current_pre_order.status
                
                # Verificar nova proposta
                current_proposal_count = current_pre_order.proposals.count()
                if current_proposal_count > last_proposal_count:
                    # Buscar última proposta
                    latest_proposal = current_pre_order.proposals.order_by(
                        PreOrderProposal.created_at.desc()
                    ).first()
                    
                    if latest_proposal and latest_proposal.proposed_by != user.id:
                        proposer = User.query.get(latest_proposal.proposed_by)
                        yield format_sse_event({
                            'type': 'proposal_received',
                            'proposal_id': latest_proposal.id,
                            'proposer_name': proposer.nome if proposer else 'Outra parte',
                            'proposed_value': float(latest_proposal.proposed_value) if latest_proposal.proposed_value else None
                        }, event='proposal_received')
                    
                    last_proposal_count = current_proposal_count
                
                # Verificar aceitação mútua
                if (current_pre_order.client_accepted_terms and current_pre_order.provider_accepted_terms and
                    (not last_client_accepted or not last_provider_accepted)):
                    yield format_sse_event({
                        'type': 'mutual_acceptance',
                        'message': 'Ambas as partes aceitaram os termos!'
                    }, event='mutual_acceptance')
                
                last_client_accepted = current_pre_order.client_accepted_terms
                last_provider_accepted = current_pre_order.provider_accepted_terms
                
                # Verificar presença da outra parte
                other_party_id = current_pre_order.provider_id if user.id == current_pre_order.client_id else current_pre_order.client_id
                other_party_present = is_user_present(pre_order_id, other_party_id)
                
                if other_party_present:
                    other_party = User.query.get(other_party_id)
                    yield format_sse_event({
                        'type': 'presence',
                        'other_party_present': True,
                        'other_party_name': other_party.nome if other_party else 'Outra parte'
                    }, event='presence')
                
                # Heartbeat
                yield format_sse_event({
                    'type': 'heartbeat',
                    'timestamp': datetime.utcnow().isoformat()
                }, event='heartbeat')
                
                # Aguardar antes da próxima verificação
                time.sleep(5)
                retry_count = 0
                
            except GeneratorExit:
                logger.info(f"Cliente desconectou do stream - Pré-ordem: {pre_order_id}, User: {user.id}")
                break
            except Exception as e:
                logger.error(f"Erro no stream SSE: {e}")
                retry_count += 1
                time.sleep(2)
        
        yield format_sse_event({
            'type': 'disconnected',
            'message': 'Conexão encerrada'
        })
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


def format_sse_event(data, event='message'):
    """Formata dados no formato SSE"""
    import json
    message = f"event: {event}\n"
    message += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return message


def is_user_present(pre_order_id, user_id):
    """Verifica se usuário está presente na pré-ordem"""
    key = f"{pre_order_id}_{user_id}"
    if key in _presence_cache:
        # Verificar se presença ainda é válida (últimos 2 minutos)
        last_seen = _presence_cache[key]
        if (datetime.utcnow() - last_seen).total_seconds() < 120:
            return True
    return False


@pre_ordem_bp.route('/<int:pre_order_id>/presenca', methods=['GET', 'POST'])
@login_required
@require_pre_order_participant()
def gerenciar_presenca(pre_order_id, pre_order=None):
    """
    Gerencia presença de usuários na pré-ordem
    
    GET /pre-ordem/<id>/presenca - Verifica presença da outra parte
    POST /pre-ordem/<id>/presenca - Registra/remove presença
    
    Requirements: 20.3 (Indicador de presença)
    """
    user = AuthService.get_current_user()
    
    if request.method == 'POST':
        # Registrar ou remover presença
        data = request.get_json() or {}
        action = data.get('action', 'enter')
        
        key = f"{pre_order_id}_{user.id}"
        
        if action == 'enter':
            _presence_cache[key] = datetime.utcnow()
            logger.debug(f"Presença registrada - Pré-ordem: {pre_order_id}, User: {user.id}")
        elif action == 'leave':
            if key in _presence_cache:
                del _presence_cache[key]
            logger.debug(f"Presença removida - Pré-ordem: {pre_order_id}, User: {user.id}")
        
        return jsonify({'success': True})
    
    else:
        # Verificar presença da outra parte
        other_party_id = pre_order.provider_id if user.id == pre_order.client_id else pre_order.client_id
        other_party_present = is_user_present(pre_order_id, other_party_id)
        
        other_party = User.query.get(other_party_id)
        
        return jsonify({
            'success': True,
            'other_party_present': other_party_present,
            'other_party_name': other_party.nome if other_party else 'Outra parte'
        })
