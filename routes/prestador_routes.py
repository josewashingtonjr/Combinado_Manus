#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.auth_service import login_required, prestador_required, AuthService
from services.prestador_service import PrestadorService

prestador_bp = Blueprint('prestador', __name__, url_prefix='/prestador')

# ==============================================================================
#  DASHBOARD DO PRESTADOR
# ==============================================================================

@prestador_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal do prestador"""
    user = AuthService.get_current_user()
    
    # Verificar se o usuário tem papel de prestador
    if 'prestador' not in user.roles:
        flash('Você não tem permissão para acessar a área do prestador.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Obter dados do dashboard
    dashboard_data = PrestadorService.get_dashboard_data(user.id)
    
    return render_template('prestador/dashboard.html', 
                         user=user, 
                         data=dashboard_data)

# ==============================================================================
#  CARTEIRA E GANHOS
# ==============================================================================

@prestador_bp.route('/carteira')
@login_required
def carteira():
    """Visualizar carteira e ganhos"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    wallet_data = PrestadorService.get_wallet_data(user.id)
    
    return render_template('prestador/carteira.html', 
                         user=user, 
                         wallet=wallet_data)

# ==============================================================================
#  ORDENS DE SERVIÇO
# ==============================================================================

@prestador_bp.route('/ordens')
@login_required
def ordens():
    """Ordens de serviço disponíveis e do prestador"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'todas')
    
    orders = PrestadorService.get_provider_orders(user.id, page, status_filter)
    
    return render_template('prestador/ordens.html', 
                         user=user, 
                         orders=orders,
                         status_filter=status_filter)

@prestador_bp.route('/ordens/disponiveis')
@login_required
def ordens_disponiveis():
    """Ordens disponíveis para aceitar"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    page = request.args.get('page', 1, type=int)
    available_orders = PrestadorService.get_available_orders(page)
    
    return render_template('prestador/ordens_disponiveis.html', 
                         user=user, 
                         orders=available_orders)

# ==============================================================================
#  HISTÓRICO DE GANHOS
# ==============================================================================

@prestador_bp.route('/ganhos')
@login_required
def ganhos():
    """Histórico de ganhos do prestador"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    page = request.args.get('page', 1, type=int)
    periodo = request.args.get('periodo', 'mes')
    
    earnings = PrestadorService.get_earnings_history(user.id, page, periodo)
    
    return render_template('prestador/ganhos.html', 
                         user=user, 
                         earnings=earnings,
                         periodo=periodo)

# ==============================================================================
#  PERFIL DO PRESTADOR
# ==============================================================================

@prestador_bp.route('/perfil')
@login_required
def perfil():
    """Perfil do prestador"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    profile_data = PrestadorService.get_provider_profile(user.id)
    
    return render_template('prestador/perfil.html', 
                         user=user, 
                         profile=profile_data)

# ==============================================================================
#  TROCA DE PAPEL (PRESTADOR <-> CLIENTE)
# ==============================================================================

@prestador_bp.route('/trocar-para-cliente')
@login_required
def trocar_para_cliente():
    """Trocar para a área do cliente"""
    user = AuthService.get_current_user()
    
    # Verificar se o usuário também é cliente
    if 'cliente' not in user.roles:
        flash('Você não tem permissão para acessar a área do cliente. Entre em contato com o administrador.', 'warning')
        return redirect(url_for('prestador.dashboard'))
    
    # Redirecionar para o dashboard do cliente
    flash('Bem-vindo à área do cliente!', 'info')
    return redirect(url_for('cliente.dashboard'))

# ==============================================================================
#  AÇÕES EM ORDENS
# ==============================================================================

@prestador_bp.route('/ordens/<int:order_id>/aceitar', methods=['POST'])
@login_required
def aceitar_ordem(order_id):
    """Aceitar uma ordem de serviço"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        PrestadorService.accept_order(user.id, order_id)
        flash('Ordem aceita com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao aceitar ordem: {str(e)}', 'error')
    
    return redirect(url_for('prestador.ordens'))

@prestador_bp.route('/ordens/<int:order_id>/concluir', methods=['POST'])
@login_required
def concluir_ordem(order_id):
    """Marcar ordem como concluída"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        PrestadorService.complete_order(user.id, order_id)
        flash('Ordem marcada como concluída! Aguardando confirmação do cliente.', 'success')
    except Exception as e:
        flash(f'Erro ao concluir ordem: {str(e)}', 'error')
    
    return redirect(url_for('prestador.ordens'))

# ==============================================================================
#  SAQUE DE SALDO
# ==============================================================================

@prestador_bp.route('/saque')
@login_required
def saque():
    """Solicitar saque de saldo"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    return render_template('prestador/saque.html', user=user)

@prestador_bp.route('/saque', methods=['POST'])
@login_required
def processar_saque():
    """Processar solicitação de saque"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        amount = float(request.form.get('amount', 0))
        bank_info = request.form.get('bank_info', '')
        
        if amount <= 0:
            flash('Valor deve ser maior que zero.', 'error')
            return redirect(url_for('prestador.saque'))
        
        # Processar solicitação de saque
        PrestadorService.create_withdrawal_request(user.id, amount, bank_info)
        flash('Solicitação de saque enviada com sucesso! Será processada em até 2 dias úteis.', 'success')
        
    except ValueError:
        flash('Valor inválido.', 'error')
    except Exception as e:
        flash(f'Erro ao processar saque: {str(e)}', 'error')
    
    return redirect(url_for('prestador.dashboard'))
