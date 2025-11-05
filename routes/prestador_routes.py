#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.auth_service import login_required, prestador_required, AuthService, user_loader_required
from services.prestador_service import PrestadorService
from services.invite_service import InviteService
from datetime import datetime

prestador_bp = Blueprint('prestador', __name__, url_prefix='/prestador')

# ==============================================================================
#  DASHBOARD DO PRESTADOR
# ==============================================================================

@prestador_bp.route('/dashboard')
@user_loader_required
def dashboard(user):
    """Dashboard principal do prestador"""
    
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
@user_loader_required
def carteira(user):
    """Visualizar carteira e ganhos"""
    
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
@user_loader_required
def ordens(user):
    """Ordens de serviço disponíveis e do prestador"""
    
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
@user_loader_required
def ordens_disponiveis(user):
    """Ordens disponíveis para aceitar"""
    
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
@user_loader_required
def ganhos(user):
    """Histórico de ganhos do prestador"""
    
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
@user_loader_required
def perfil(user):
    """Perfil do prestador"""
    
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
@user_loader_required
def trocar_para_cliente(user):
    """Trocar para a área do cliente"""
    
    # Verificar se o usuário também é cliente
    if 'cliente' not in user.roles:
        flash('Você não tem permissão para acessar a área do cliente. Entre em contato com o administrador.', 'warning')
        return redirect(url_for('prestador.dashboard'))
    
    # Redirecionar para o dashboard do cliente
    flash('Bem-vindo à área do cliente!', 'info')
    return redirect(url_for('app.home'))

# ==============================================================================
#  AÇÕES EM ORDENS
# ==============================================================================

@prestador_bp.route('/ordens/<int:order_id>/aceitar', methods=['POST'])
@user_loader_required
def aceitar_ordem(user, order_id):
    """Aceitar uma ordem de serviço"""
    
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
@user_loader_required
def concluir_ordem(user, order_id):
    """Marcar ordem como concluída"""
    
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
@user_loader_required
def saque(user):
    """Solicitar saque de saldo"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    return render_template('prestador/saque.html', user=user)

@prestador_bp.route('/saque', methods=['POST'])
@user_loader_required
def processar_saque(user):
    """Processar solicitação de saque"""
    
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

# ==============================================================================
#  SISTEMA DE CONVITES
# ==============================================================================

@prestador_bp.route('/convites')
@user_loader_required
def convites(user):
    """Listar convites recebidos pelo prestador"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Obter convites recebidos
    received_invites = InviteService.get_invites_for_email(user.email)
    
    return render_template('prestador/convites.html', 
                         user=user, 
                         invites=received_invites)

@prestador_bp.route('/convites/<token>')
@user_loader_required
def ver_convite(user, token):
    """Ver detalhes de um convite específico"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se o convite é para este prestador
        if invite.invited_email != user.email:
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('prestador.convites'))
        
        return render_template('prestador/ver_convite.html', 
                             user=user, 
                             invite=invite,
                             contestation_fee=InviteService.CONTESTATION_FEE)
        
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('prestador.convites'))
    except Exception as e:
        flash(f'Erro ao carregar convite: {str(e)}', 'error')
        return redirect(url_for('prestador.convites'))

@prestador_bp.route('/convites/<token>/aceitar', methods=['POST'])
@user_loader_required
def aceitar_convite(user, token):
    """Aceitar um convite com possibilidade de alteração de termos"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Obter dados do formulário
        final_value = request.form.get('final_value')
        new_delivery_date_str = request.form.get('new_delivery_date')
        
        # Converter valores se fornecidos
        final_value = float(final_value) if final_value else None
        new_delivery_date = None
        
        if new_delivery_date_str:
            try:
                new_delivery_date = datetime.strptime(new_delivery_date_str, '%Y-%m-%d')
                if new_delivery_date <= datetime.now():
                    flash('Nova data de entrega deve ser futura.', 'error')
                    return redirect(url_for('prestador.ver_convite', token=token))
            except ValueError:
                flash('Data de entrega inválida.', 'error')
                return redirect(url_for('prestador.ver_convite', token=token))
        
        # Aceitar o convite
        result = InviteService.accept_invite(
            token=token,
            provider_id=user.id,
            final_value=final_value,
            new_delivery_date=new_delivery_date
        )
        
        flash('Convite aceito com sucesso! O cliente será notificado.', 'success')
        return redirect(url_for('prestador.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao aceitar convite: {str(e)}', 'error')
    
    return redirect(url_for('prestador.ver_convite', token=token))

@prestador_bp.route('/convites/<token>/recusar', methods=['POST'])
@login_required
def recusar_convite(token):
    """Recusar um convite"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        reason = request.form.get('reason', '')
        
        # Recusar o convite
        result = InviteService.reject_invite(
            token=token,
            provider_id=user.id,
            reason=reason
        )
        
        flash('Convite recusado. O cliente será notificado automaticamente.', 'info')
        return redirect(url_for('prestador.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao recusar convite: {str(e)}', 'error')
    
    return redirect(url_for('prestador.ver_convite', token=token))

@prestador_bp.route('/convites/<token>/alterar-termos', methods=['POST'])
@login_required
def alterar_termos_convite(token):
    """Propor alterações nos termos do convite"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Obter dados do formulário
        new_value = request.form.get('new_value')
        new_delivery_date_str = request.form.get('new_delivery_date')
        
        # Converter valores
        new_value = float(new_value) if new_value else None
        new_delivery_date = None
        
        if new_delivery_date_str:
            try:
                new_delivery_date = datetime.strptime(new_delivery_date_str, '%Y-%m-%d')
                if new_delivery_date <= datetime.now():
                    flash('Nova data de entrega deve ser futura.', 'error')
                    return redirect(url_for('prestador.ver_convite', token=token))
            except ValueError:
                flash('Data de entrega inválida.', 'error')
                return redirect(url_for('prestador.ver_convite', token=token))
        
        # Validar se pelo menos um campo foi alterado
        if new_value is None and new_delivery_date is None:
            flash('Você deve alterar pelo menos o valor ou a data de entrega.', 'error')
            return redirect(url_for('prestador.ver_convite', token=token))
        
        # Alterar termos
        result = InviteService.update_invite_terms(
            token=token,
            provider_id=user.id,
            new_value=new_value,
            new_delivery_date=new_delivery_date
        )
        
        flash('Termos alterados com sucesso! O cliente será notificado das mudanças.', 'success')
        return redirect(url_for('prestador.ver_convite', token=token))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao alterar termos: {str(e)}', 'error')
    
    return redirect(url_for('prestador.ver_convite', token=token))
