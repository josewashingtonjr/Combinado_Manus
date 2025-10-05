#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.auth_service import login_required, cliente_required, AuthService
from services.cliente_service import ClienteService

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')

# ==============================================================================
#  DASHBOARD DO CLIENTE
# ==============================================================================

@cliente_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal do cliente"""
    user = AuthService.get_current_user()
    
    # Verificar se o usuário tem papel de cliente
    if 'cliente' not in user.roles:
        flash('Você não tem permissão para acessar a área do cliente.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Obter dados do dashboard
    dashboard_data = ClienteService.get_dashboard_data(user.id)
    
    return render_template('cliente/dashboard.html', 
                         user=user, 
                         data=dashboard_data)

# ==============================================================================
#  CARTEIRA E SALDO
# ==============================================================================

@cliente_bp.route('/carteira')
@login_required
def carteira():
    """Visualizar carteira e saldo"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    wallet_data = ClienteService.get_wallet_data(user.id)
    
    return render_template('cliente/carteira.html', 
                         user=user, 
                         wallet=wallet_data)

# ==============================================================================
#  HISTÓRICO DE TRANSAÇÕES
# ==============================================================================

@cliente_bp.route('/transacoes')
@login_required
def transacoes():
    """Histórico de transações do cliente"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    page = request.args.get('page', 1, type=int)
    transactions = ClienteService.get_transactions_history(user.id, page)
    
    return render_template('cliente/transacoes.html', 
                         user=user, 
                         transactions=transactions)

# ==============================================================================
#  ORDENS DE SERVIÇO
# ==============================================================================

@cliente_bp.route('/ordens')
@login_required
def ordens():
    """Ordens de serviço do cliente"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    page = request.args.get('page', 1, type=int)
    orders = ClienteService.get_client_orders(user.id, page)
    
    return render_template('cliente/ordens.html', 
                         user=user, 
                         orders=orders)

# ==============================================================================
#  PERFIL DO CLIENTE
# ==============================================================================

@cliente_bp.route('/perfil')
@login_required
def perfil():
    """Perfil do cliente"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    return render_template('cliente/perfil.html', user=user)

# ==============================================================================
#  TROCA DE PAPEL (CLIENTE <-> PRESTADOR)
# ==============================================================================

@cliente_bp.route('/trocar-para-prestador')
@login_required
def trocar_para_prestador():
    """Trocar para a área do prestador"""
    user = AuthService.get_current_user()
    
    # Verificar se o usuário também é prestador
    if 'prestador' not in user.roles:
        flash('Você não tem permissão para acessar a área do prestador. Entre em contato com o administrador.', 'warning')
        return redirect(url_for('cliente.dashboard'))
    
    # Redirecionar para o dashboard do prestador
    flash('Bem-vindo à área do prestador!', 'info')
    return redirect(url_for('prestador.dashboard'))

# ==============================================================================
#  COMPRA DE TOKENS (SOLICITAÇÃO)
# ==============================================================================

@cliente_bp.route('/solicitar-tokens')
@login_required
def solicitar_tokens():
    """Solicitar compra de tokens (controlada pelo admin)"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    return render_template('cliente/solicitar_tokens.html', user=user)

@cliente_bp.route('/solicitar-tokens', methods=['POST'])
@login_required
def processar_solicitacao_tokens():
    """Processar solicitação de tokens"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        
        if amount <= 0:
            flash('Quantidade deve ser maior que zero.', 'error')
            return redirect(url_for('cliente.solicitar_tokens'))
        
        # Registrar solicitação (será processada pelo admin)
        ClienteService.create_token_request(user.id, amount, description)
        flash('Solicitação de tokens enviada com sucesso! Aguarde aprovação do administrador.', 'success')
        
    except ValueError:
        flash('Quantidade inválida.', 'error')
    except Exception as e:
        flash(f'Erro ao processar solicitação: {str(e)}', 'error')
    
    return redirect(url_for('cliente.dashboard'))
