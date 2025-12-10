#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, flash, redirect, url_for, session
from services.auth_service import login_required, AuthService
from services.proposal_service import ProposalService
from services.invite_service import InviteService
from services.balance_validator import BalanceValidator
from services.security_validator import SecurityValidator
from decimal import Decimal
import logging

proposal_bp = Blueprint('proposal', __name__)

# ==============================================================================
#  CRIAR PROPOSTA DE ALTERAÇÃO
# ==============================================================================

@proposal_bp.route('/convite/<int:invite_id>/propor-alteracao', methods=['POST'])
@login_required
def propor_alteracao(invite_id):
    """
    DEPRECATED: Esta rota foi descontinuada.
    
    Negociações de valor agora são feitas na tela de pré-ordem após aceitar o convite.
    Esta rota é mantida apenas para compatibilidade e redireciona com mensagem informativa.
    
    O fluxo correto agora é:
    1. Prestador aceita o convite
    2. Sistema cria pré-ordem automaticamente
    3. Negociações são feitas na tela de pré-ordem
    """
    user = AuthService.get_current_user()
    
    # Determinar para onde redirecionar
    is_client = 'cliente' in user.roles
    
    if request.is_json:
        return jsonify({
            'success': False,
            'error': 'deprecated',
            'message': 'Esta funcionalidade foi movida para a pré-ordem. Aceite o convite primeiro para negociar valores.'
        }), 410  # 410 Gone - recurso não mais disponível
    
    flash('Para negociar valores, primeiro aceite o convite. A negociação será feita na tela de pré-ordem.', 'info')
    
    if is_client:
        return redirect(url_for('cliente.convites'))
    else:
        return redirect(url_for('prestador.convites'))

# ==============================================================================
#  APROVAR PROPOSTA
# ==============================================================================

@proposal_bp.route('/proposta/<int:proposal_id>/aprovar', methods=['POST'])
@login_required
def aprovar_proposta(proposal_id):
    """
    Aprovar uma proposta de alteração
    
    Rota: POST /proposta/<id>/aprovar
    
    Validações:
    - Usuário deve estar logado
    - Usuário deve ter papel de cliente
    - Proposta deve existir e estar pendente
    - Cliente deve ser o dono do convite
    - Verificar saldo suficiente para aumentos de valor
    
    Requirements: 1.1, 2.1, 2.2, 5.5
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Apenas clientes podem aprovar propostas'
            }), 403
        
        flash('Apenas clientes podem aprovar propostas.', 'error')
        return redirect(url_for('cliente.convites'))
    
    try:
        # Obter comentário opcional do cliente
        client_response_reason = request.form.get('client_response_reason') or request.json.get('client_response_reason') if request.is_json else None
        
        # As validações de segurança (sanitização, limites) são feitas pelo SecurityValidator no ProposalService
        
        # Aprovar a proposta (validações de segurança são feitas internamente)
        result = ProposalService.approve_proposal(
            proposal_id=proposal_id,
            client_id=user.id,
            client_response_reason=client_response_reason  # Será sanitizado pelo SecurityValidator
        )
        
        # Log da ação
        logging.info(f"Proposta aprovada - Cliente {user.id}, Proposta {proposal_id}, "
                    f"Valor aprovado: {result['approved_value']}")
        
        # Resposta baseada no tipo de requisição
        if request.is_json:
            return jsonify(result), 200
        
        flash(result['message'], 'success')
        return redirect(url_for('cliente.ver_convite', invite_id=result['invite_id']))
        
    except ValueError as e:
        logging.warning(f"Erro de validação ao aprovar proposta - Cliente {user.id}, "
                       f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': str(e)
            }), 400
        
        flash(str(e), 'error')
        return redirect(request.referrer or url_for('cliente.convites'))
        
    except Exception as e:
        logging.error(f"Erro interno ao aprovar proposta - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor. Tente novamente.'
            }), 500
        
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(request.referrer or url_for('cliente.convites'))

# ==============================================================================
#  REJEITAR PROPOSTA
# ==============================================================================

@proposal_bp.route('/proposta/<int:proposal_id>/rejeitar', methods=['POST'])
@login_required
def rejeitar_proposta(proposal_id):
    """
    Rejeitar uma proposta de alteração
    
    Rota: POST /proposta/<id>/rejeitar
    
    Validações:
    - Usuário deve estar logado
    - Usuário deve ter papel de cliente
    - Proposta deve existir e estar pendente
    - Cliente deve ser o dono do convite
    - Registrar motivo da rejeição
    
    Requirements: 1.1, 2.1, 2.2, 5.5
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Apenas clientes podem rejeitar propostas'
            }), 403
        
        flash('Apenas clientes podem rejeitar propostas.', 'error')
        return redirect(url_for('cliente.convites'))
    
    try:
        # Obter motivo da rejeição
        client_response_reason = request.form.get('client_response_reason') or request.json.get('client_response_reason') if request.is_json else None
        
        # As validações de segurança (sanitização, limites) são feitas pelo SecurityValidator no ProposalService
        
        # Rejeitar a proposta (validações de segurança são feitas internamente)
        result = ProposalService.reject_proposal(
            proposal_id=proposal_id,
            client_id=user.id,
            client_response_reason=client_response_reason  # Será sanitizado pelo SecurityValidator
        )
        
        # Log da ação
        logging.info(f"Proposta rejeitada - Cliente {user.id}, Proposta {proposal_id}, "
                    f"Motivo: {client_response_reason or 'Não informado'}")
        
        # Resposta baseada no tipo de requisição
        if request.is_json:
            return jsonify(result), 200
        
        flash(result['message'], 'info')
        return redirect(url_for('cliente.ver_convite', invite_id=result['invite_id']))
        
    except ValueError as e:
        logging.warning(f"Erro de validação ao rejeitar proposta - Cliente {user.id}, "
                       f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': str(e)
            }), 400
        
        flash(str(e), 'error')
        return redirect(request.referrer or url_for('cliente.convites'))
        
    except Exception as e:
        logging.error(f"Erro interno ao rejeitar proposta - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor. Tente novamente.'
            }), 500
        
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(request.referrer or url_for('cliente.convites'))

# ==============================================================================
#  CANCELAR PROPOSTA
# ==============================================================================

@proposal_bp.route('/proposta/<int:proposal_id>/cancelar', methods=['DELETE', 'POST'])
@login_required
def cancelar_proposta(proposal_id):
    """
    Cancelar uma proposta de alteração (ação do prestador)
    
    Rota: DELETE /proposta/<id>/cancelar (ou POST para compatibilidade com formulários)
    
    Validações:
    - Usuário deve estar logado
    - Usuário deve ter papel de prestador
    - Proposta deve existir e estar pendente
    - Prestador deve ser o criador da proposta
    
    Requirements: 1.1, 2.1, 2.2, 5.5
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de prestador
    if 'prestador' not in user.roles:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Apenas prestadores podem cancelar suas propostas'
            }), 403
        
        flash('Apenas prestadores podem cancelar suas propostas.', 'error')
        return redirect(url_for('prestador.convites'))
    
    try:
        # Cancelar a proposta
        result = ProposalService.cancel_proposal(
            proposal_id=proposal_id,
            prestador_id=user.id
        )
        
        # Log da ação
        logging.info(f"Proposta cancelada - Prestador {user.id}, Proposta {proposal_id}")
        
        # Resposta baseada no tipo de requisição
        if request.is_json:
            return jsonify(result), 200
        
        flash(result['message'], 'info')
        return redirect(url_for('prestador.convites'))
        
    except ValueError as e:
        logging.warning(f"Erro de validação ao cancelar proposta - Prestador {user.id}, "
                       f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': str(e)
            }), 400
        
        flash(str(e), 'error')
        return redirect(request.referrer or url_for('prestador.convites'))
        
    except Exception as e:
        logging.error(f"Erro interno ao cancelar proposta - Prestador {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor. Tente novamente.'
            }), 500
        
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(request.referrer or url_for('prestador.convites'))

# ==============================================================================
#  VERIFICAR SALDO PARA PROPOSTA (AJAX)
# ==============================================================================

@proposal_bp.route('/proposta/verificar-saldo/<int:proposal_id>', methods=['GET'])
@login_required
def verificar_saldo_proposta(proposal_id):
    """
    Verificar se cliente tem saldo suficiente para aprovar uma proposta
    
    Rota: GET /proposta/verificar-saldo/<id>
    
    Retorna informações de saldo em formato JSON para uso em AJAX
    
    Requirements: 3.1, 3.2, 3.3
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Apenas clientes podem verificar saldo para propostas'
        }), 403
    
    try:
        # Obter informações da proposta
        proposal_info = ProposalService.get_proposal_by_id(proposal_id)
        
        # Verificar se cliente é o dono do convite
        if proposal_info['invite_info']['client_name'] != user.nome:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Você não tem permissão para verificar esta proposta'
            }), 403
        
        # Verificar saldo
        balance_status = BalanceValidator.validate_proposal_balance(
            client_id=user.id,
            proposed_value=Decimal(str(proposal_info['proposed_value']))
        )
        
        # Obter resumo completo do saldo
        balance_summary = BalanceValidator.get_balance_summary(user.id)
        
        return jsonify({
            'success': True,
            'proposal_id': proposal_id,
            'proposed_value': proposal_info['proposed_value'],
            'original_value': proposal_info['original_value'],
            'value_difference': proposal_info['value_difference'],
            'is_increase': proposal_info['is_increase'],
            'balance_check': {
                'is_sufficient': balance_status.is_sufficient,
                'current_balance': float(balance_status.current_balance),
                'required_amount': float(balance_status.required_amount),
                'shortfall': float(balance_status.shortfall),
                'suggested_top_up': float(balance_status.suggested_top_up),
                'contestation_fee': float(balance_status.contestation_fee)
            },
            'balance_summary': {
                'balance': float(balance_summary['balance']),
                'escrow_balance': float(balance_summary['escrow_balance']),
                'total_balance': float(balance_summary['total_balance']),
                'available_for_proposals': float(balance_summary['available_for_proposals'])
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logging.error(f"Erro ao verificar saldo para proposta - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

# ==============================================================================
#  FLUXO INTEGRADO DE ADIÇÃO DE SALDO
# ==============================================================================

@proposal_bp.route('/proposta/<int:proposal_id>/adicionar-saldo-e-aprovar', methods=['POST'])
@login_required
def adicionar_saldo_e_aprovar(proposal_id):
    """
    Fluxo integrado: adicionar saldo e aprovar proposta automaticamente
    
    Rota: POST /proposta/<id>/adicionar-saldo-e-aprovar
    
    Este endpoint permite que o cliente adicione saldo suficiente e aprove
    a proposta em uma única operação atômica.
    
    Requirements: 3.4, 4.1, 4.3, 4.4, 4.5
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Apenas clientes podem usar este fluxo'
            }), 403
        
        flash('Apenas clientes podem usar este fluxo.', 'error')
        return redirect(url_for('cliente.convites'))
    
    try:
        # Obter dados do formulário
        amount_to_add = request.form.get('amount_to_add') or request.json.get('amount_to_add') if request.is_json else None
        payment_method = request.form.get('payment_method') or request.json.get('payment_method') if request.is_json else 'pix'
        description = request.form.get('description') or request.json.get('description') if request.is_json else None
        client_response_reason = request.form.get('client_response_reason') or request.json.get('client_response_reason') if request.is_json else None
        
        # Validar dados de entrada
        if not amount_to_add:
            raise ValueError("Valor a adicionar é obrigatório")
        
        try:
            amount_to_add = Decimal(str(amount_to_add))
        except (ValueError, TypeError):
            raise ValueError("Valor a adicionar deve ser um número válido")
        
        if amount_to_add <= 0:
            raise ValueError("Valor a adicionar deve ser maior que zero")
        
        if amount_to_add > 10000:
            raise ValueError("Valor máximo por adição: R$ 10.000,00")
        
        # Limitar descrição e comentário
        if description and len(description.strip()) > 200:
            raise ValueError("Descrição não pode exceder 200 caracteres")
        
        if client_response_reason and len(client_response_reason.strip()) > 300:
            raise ValueError("Comentário não pode exceder 300 caracteres")
        
        # Obter informações da proposta
        proposal_info = ProposalService.get_proposal_by_id(proposal_id)
        
        # Verificar se cliente é o dono do convite
        if proposal_info['invite_info']['client_name'] != user.nome:
            raise ValueError("Você não tem permissão para esta proposta")
        
        # Verificar se proposta está pendente
        if proposal_info['status'] != 'pending':
            raise ValueError("Proposta não está mais pendente")
        
        # Verificar saldo atual e calcular se será suficiente após adição
        balance_status = BalanceValidator.validate_proposal_balance(
            client_id=user.id,
            proposed_value=Decimal(str(proposal_info['proposed_value']))
        )
        
        # Calcular novo saldo após adição
        new_balance = balance_status.current_balance + amount_to_add
        
        # Verificar se o novo saldo será suficiente
        if new_balance < balance_status.required_amount:
            shortfall_after_addition = balance_status.required_amount - new_balance
            raise ValueError(f"Valor insuficiente. Após adicionar R$ {amount_to_add:.2f}, "
                           f"ainda faltarão R$ {shortfall_after_addition:.2f}. "
                           f"Adicione pelo menos R$ {balance_status.shortfall:.2f}")
        
        # Executar fluxo integrado usando ProposalService
        result = ProposalService.add_balance_and_approve_proposal(
            proposal_id=proposal_id,
            client_id=user.id,
            amount_to_add=amount_to_add,
            payment_method=payment_method,
            description=description.strip() if description else None,
            client_response_reason=client_response_reason.strip() if client_response_reason else None
        )
        
        # Log da ação
        logging.info(f"Saldo adicionado e proposta aprovada - Cliente {user.id}, "
                    f"Proposta {proposal_id}, Valor adicionado: {amount_to_add}, "
                    f"Valor aprovado: {result['approved_value']}")
        
        # Resposta baseada no tipo de requisição
        if request.is_json:
            return jsonify(result), 200
        
        flash(result['message'], 'success')
        return redirect(url_for('cliente.ver_convite', invite_id=result['invite_id']))
        
    except ValueError as e:
        logging.warning(f"Erro de validação no fluxo integrado - Cliente {user.id}, "
                       f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'validation_error',
                'message': str(e)
            }), 400
        
        flash(str(e), 'error')
        return redirect(request.referrer or url_for('cliente.convites'))
        
    except Exception as e:
        logging.error(f"Erro interno no fluxo integrado - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor. Tente novamente.'
            }), 500
        
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(request.referrer or url_for('cliente.convites'))

@proposal_bp.route('/proposta/<int:proposal_id>/simular-adicao', methods=['POST'])
@login_required
def simular_adicao_saldo(proposal_id):
    """
    Simular adição de saldo para verificar se será suficiente
    
    Rota: POST /proposta/<id>/simular-adicao
    
    Requirements: 4.2, 4.3
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Apenas clientes podem simular adição de saldo'
        }), 403
    
    try:
        # Obter valor a adicionar
        amount_to_add = request.json.get('amount_to_add') if request.is_json else None
        
        if not amount_to_add:
            raise ValueError("Valor a adicionar é obrigatório")
        
        try:
            amount_to_add = Decimal(str(amount_to_add))
        except (ValueError, TypeError):
            raise ValueError("Valor deve ser um número válido")
        
        if amount_to_add <= 0:
            raise ValueError("Valor deve ser maior que zero")
        
        # Executar simulação
        result = ProposalService.simulate_balance_addition(
            proposal_id=proposal_id,
            client_id=user.id,
            amount_to_add=amount_to_add
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logging.error(f"Erro ao simular adição de saldo - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

@proposal_bp.route('/proposta/<int:proposal_id>/calcular-saldo-necessario', methods=['GET'])
@login_required
def calcular_saldo_necessario(proposal_id):
    """
    Calcular valor exato necessário para aprovar uma proposta
    
    Rota: GET /proposta/<id>/calcular-saldo-necessario
    
    Retorna cálculo detalhado do saldo necessário para uso no modal
    
    Requirements: 3.1, 3.2, 4.2
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de cliente
    if 'cliente' not in user.roles:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Apenas clientes podem calcular saldo necessário'
        }), 403
    
    try:
        # Obter informações da proposta
        proposal_info = ProposalService.get_proposal_by_id(proposal_id)
        
        # Verificar se cliente é o dono do convite
        if proposal_info['invite_info']['client_name'] != user.nome:
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Você não tem permissão para esta proposta'
            }), 403
        
        # Verificar saldo e calcular valores necessários
        balance_status = BalanceValidator.validate_proposal_balance(
            client_id=user.id,
            proposed_value=Decimal(str(proposal_info['proposed_value']))
        )
        
        # Calcular diferentes opções de adição de saldo
        minimum_addition = balance_status.shortfall if balance_status.shortfall > 0 else Decimal('0')
        suggested_addition = balance_status.suggested_top_up if balance_status.shortfall > 0 else Decimal('0')
        
        # Opções pré-definidas para facilitar escolha do usuário
        predefined_options = []
        if minimum_addition > 0:
            predefined_options = [
                float(minimum_addition),  # Valor mínimo exato
                float(minimum_addition + Decimal('50')),  # Mínimo + R$ 50
                float(minimum_addition + Decimal('100')),  # Mínimo + R$ 100
                float(minimum_addition + Decimal('200'))   # Mínimo + R$ 200
            ]
        
        return jsonify({
            'success': True,
            'proposal_id': proposal_id,
            'proposal_value': float(proposal_info['proposed_value']),
            'original_value': float(proposal_info['original_value']),
            'balance_info': {
                'current_balance': float(balance_status.current_balance),
                'required_amount': float(balance_status.required_amount),
                'contestation_fee': float(balance_status.contestation_fee),
                'is_sufficient': balance_status.is_sufficient,
                'shortfall': float(balance_status.shortfall),
                'minimum_addition': float(minimum_addition),
                'suggested_addition': float(suggested_addition)
            },
            'predefined_options': predefined_options,
            'payment_methods': [
                {'value': 'pix', 'label': 'PIX (Instantâneo)', 'processing_time': '2 horas'},
                {'value': 'ted', 'label': 'TED (1-2 dias úteis)', 'processing_time': '1-2 dias'},
                {'value': 'doc', 'label': 'DOC (1-2 dias úteis)', 'processing_time': '1-2 dias'}
            ]
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logging.error(f"Erro ao calcular saldo necessário - Cliente {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

# ==============================================================================
#  OBTER DETALHES DA PROPOSTA (AJAX)
# ==============================================================================

@proposal_bp.route('/proposta/<int:proposal_id>/detalhes', methods=['GET'])
@login_required
def obter_detalhes_proposta(proposal_id):
    """
    Obter detalhes completos de uma proposta
    
    Rota: GET /proposta/<id>/detalhes
    
    Retorna informações detalhadas da proposta em formato JSON
    
    Requirements: 1.1, 2.1, 2.2, 5.5
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter informações da proposta
        proposal_info = ProposalService.get_proposal_by_id(proposal_id)
        
        # Verificar autorização (cliente do convite ou prestador da proposta)
        is_client = 'cliente' in user.roles and proposal_info['invite_info']['client_name'] == user.nome
        is_prestador = 'prestador' in user.roles and proposal_info['prestador_id'] == user.id
        
        if not (is_client or is_prestador):
            return jsonify({
                'success': False,
                'error': 'unauthorized',
                'message': 'Você não tem permissão para ver esta proposta'
            }), 403
        
        # Adicionar informações específicas baseadas no papel do usuário
        response_data = {
            'success': True,
            'proposal': proposal_info,
            'user_role': 'cliente' if is_client else 'prestador'
        }
        
        # Se for cliente, incluir verificação de saldo
        if is_client and proposal_info['status'] == 'pending':
            balance_status = BalanceValidator.validate_proposal_balance(
                client_id=user.id,
                proposed_value=Decimal(str(proposal_info['proposed_value']))
            )
            
            response_data['balance_check'] = {
                'is_sufficient': balance_status.is_sufficient,
                'current_balance': float(balance_status.current_balance),
                'required_amount': float(balance_status.required_amount),
                'shortfall': float(balance_status.shortfall),
                'suggested_top_up': float(balance_status.suggested_top_up),
                'contestation_fee': float(balance_status.contestation_fee)
            }
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logging.error(f"Erro ao obter detalhes da proposta - Usuário {user.id}, "
                     f"Proposta {proposal_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

# ==============================================================================
#  ESTATÍSTICAS DE SEGURANÇA E MONITORAMENTO
# ==============================================================================

@proposal_bp.route('/proposta/estatisticas-seguranca', methods=['GET'])
@login_required
def obter_estatisticas_seguranca():
    """
    Obter estatísticas de segurança para monitoramento
    
    Rota: GET /proposta/estatisticas-seguranca
    
    Retorna informações sobre rate limiting, padrões suspeitos e uso do sistema
    
    Requirements: 8.5 - Monitoramento de padrões suspeitos
    """
    user = AuthService.get_current_user()
    
    try:
        # Obter estatísticas específicas do usuário se for prestador
        if 'prestador' in user.roles:
            stats = SecurityValidator.get_security_statistics(prestador_id=user.id)
        else:
            # Para clientes, retornar estatísticas gerais (limitadas)
            stats = SecurityValidator.get_security_statistics()
            # Remover informações sensíveis para clientes
            if 'top_prestadores' in stats:
                del stats['top_prestadores']
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'user_role': 'prestador' if 'prestador' in user.roles else 'cliente'
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas de segurança - Usuário {user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500

@proposal_bp.route('/proposta/verificar-limites/<int:invite_id>', methods=['GET'])
@login_required
def verificar_limites_proposta(invite_id):
    """
    Verificar limites de rate limiting antes de criar proposta
    
    Rota: GET /proposta/verificar-limites/<invite_id>
    
    Permite que prestadores verifiquem se podem criar mais propostas
    
    Requirements: 8.5 - Rate limiting para criação de propostas
    """
    user = AuthService.get_current_user()
    
    # Verificar se usuário tem papel de prestador
    if 'prestador' not in user.roles:
        return jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Apenas prestadores podem verificar limites de propostas'
        }), 403
    
    try:
        # Verificar rate limiting
        rate_result = SecurityValidator.validate_rate_limiting(user.id, invite_id)
        
        # Obter estatísticas do prestador
        stats = SecurityValidator.get_security_statistics(prestador_id=user.id)
        
        return jsonify({
            'success': True,
            'can_create_proposal': rate_result.is_valid,
            'rate_limiting': {
                'is_valid': rate_result.is_valid,
                'error_code': rate_result.error_code,
                'error_message': rate_result.error_message,
                'details': rate_result.details
            },
            'statistics': stats,
            'limits': {
                'max_per_invite': SecurityValidator.MAX_PROPOSALS_PER_INVITE,
                'max_per_hour': SecurityValidator.MAX_PROPOSALS_PER_HOUR,
                'max_per_day': SecurityValidator.MAX_PROPOSALS_PER_DAY
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao verificar limites - Prestador {user.id}, "
                     f"Convite {invite_id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor. Tente novamente.'
        }), 500