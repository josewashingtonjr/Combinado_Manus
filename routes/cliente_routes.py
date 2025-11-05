#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.auth_service import login_required, cliente_required, AuthService
from services.cliente_service import ClienteService
from services.order_service import OrderService
from services.invite_service import InviteService
from forms import CreateOrderForm, SafeCreateOrderForm
from services.validation_service import ValidationService
from datetime import datetime, timedelta

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
    orders = OrderService.get_client_orders(user.id, page)
    
    return render_template('cliente/ordens.html', 
                         user=user, 
                         orders=orders)

@cliente_bp.route('/ordens/criar')
@login_required
def criar_ordem():
    """Formulário para criar nova ordem de serviço"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    form = CreateOrderForm()
    
    # Obter informações da carteira para mostrar saldo disponível
    try:
        from services.wallet_service import WalletService
        wallet_info = WalletService.get_wallet_info(user.id)
    except Exception as e:
        wallet_info = {'balance': 0.0}
        flash(f'Erro ao carregar informações da carteira: {str(e)}', 'warning')
    
    return render_template('cliente/criar_ordem.html', 
                         user=user, 
                         form=form,
                         wallet=wallet_info)

@cliente_bp.route('/ordens/criar', methods=['POST'])
@login_required
def processar_criar_ordem():
    """Processar criação de nova ordem de serviço com validações personalizadas"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Usar formulário com validações de banco de dados
    form = SafeCreateOrderForm()
    
    # Verificar conexão com banco de dados primeiro
    db_valid, db_message = ValidationService.validate_database_connection()
    if not db_valid:
        flash(db_message, 'error')
        ValidationService.log_validation_error('database_connection', db_message, {'user_id': user.id})
        return redirect(url_for('cliente.criar_ordem'))
    
    if form.validate_on_submit():
        try:
            # Obter tipo de usuário para mensagens personalizadas
            user_type = ValidationService.get_user_type()
            
            # Validações específicas de tokenomics
            value = float(form.value.data)
            
            # Verificar saldo do usuário
            from services.wallet_service import WalletService
            wallet_info = WalletService.get_wallet_info(user.id)
            
            if not wallet_info:
                error_msg = ValidationService.format_error_message(
                    "Erro ao acessar informações da carteira.", user_type
                )
                flash(error_msg, 'error')
                ValidationService.log_validation_error('wallet_access', error_msg, {'user_id': user.id})
                return redirect(url_for('cliente.criar_ordem'))
            
            # Validar saldo suficiente para ordem + taxa de escrow (exemplo: 5%)
            escrow_fee = value * 0.05  # 5% de taxa de escrow
            total_needed = value + escrow_fee
            
            balance_valid, balance_message = ValidationService.validate_balance(
                total_needed, wallet_info['balance'], user_type
            )
            
            if not balance_valid:
                flash(balance_message, 'error')
                ValidationService.log_validation_error('insufficient_balance', balance_message, {
                    'user_id': user.id,
                    'requested_amount': total_needed,
                    'available_balance': wallet_info['balance']
                })
                return redirect(url_for('cliente.criar_ordem'))
            
            # Validar operação de escrow
            escrow_valid, escrow_message = ValidationService.validate_tokenomics_operation(
                'escrow', value, wallet_info['balance']
            )
            
            if not escrow_valid:
                flash(escrow_message, 'error')
                ValidationService.log_validation_error('escrow_validation', escrow_message, {
                    'user_id': user.id,
                    'order_value': value
                })
                return redirect(url_for('cliente.criar_ordem'))
            
            # Criar a ordem com bloqueio automático de tokens
            result = OrderService.create_order(
                client_id=user.id,
                title=form.title.data,
                description=form.description.data,
                value=value
            )
            
            # Mensagem de sucesso personalizada por tipo de usuário
            if user_type == 'admin':
                success_msg = f'Ordem criada com sucesso! {value} tokens foram bloqueados em escrow.'
            else:
                success_msg = f'Ordem criada com sucesso! Valor de R$ {value:,.2f} foi bloqueado em garantia.'
            
            flash(success_msg, 'success')
            return redirect(url_for('cliente.ordens'))
            
        except ValueError as e:
            error_msg = ValidationService.format_error_message(str(e), user_type)
            flash(error_msg, 'error')
            ValidationService.log_validation_error('value_error', str(e), {'user_id': user.id})
        except Exception as e:
            error_msg = ValidationService.format_error_message(f'Erro ao criar ordem: {str(e)}', user_type)
            flash(error_msg, 'error')
            ValidationService.log_validation_error('order_creation_error', str(e), {'user_id': user.id})
    else:
        # Mostrar erros de validação do formulário com formatação personalizada
        user_type = ValidationService.get_user_type()
        formatted_errors = ValidationService.get_form_errors_formatted(form, user_type)
        
        for field, errors in formatted_errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
        
        ValidationService.log_validation_error('form_validation', 'Erros de validação do formulário', {
            'user_id': user.id,
            'errors': formatted_errors
        })
    
    return redirect(url_for('cliente.criar_ordem'))

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
    
    # Template perfil.html não existe, redirecionando para dashboard
    flash('Página de perfil em desenvolvimento. Redirecionado para dashboard.', 'info')
    return redirect(url_for('cliente.dashboard'))

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

# ==============================================================================
#  SISTEMA DE CONVITES
# ==============================================================================

@cliente_bp.route('/convites')
@login_required
def convites():
    """Listar convites enviados pelo cliente"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Obter convites enviados
    sent_invites = InviteService.get_invites_sent_by_client(user.id)
    
    # Obter estatísticas
    stats = InviteService.get_invite_statistics(user.id)
    
    return render_template('cliente/convites.html', 
                         user=user, 
                         invites=sent_invites,
                         stats=stats)

@cliente_bp.route('/convites/criar')
@login_required
def criar_convite():
    """Formulário para criar novo convite"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Obter informações da carteira para mostrar saldo disponível
    try:
        from services.wallet_service import WalletService
        wallet_info = WalletService.get_wallet_info(user.id)
    except Exception as e:
        wallet_info = {'balance': 0.0}
        flash(f'Erro ao carregar informações da carteira: {str(e)}', 'warning')
    
    return render_template('cliente/criar_convite.html', 
                         user=user,
                         wallet=wallet_info,
                         contestation_fee=InviteService.CONTESTATION_FEE)

@cliente_bp.route('/convites/criar', methods=['POST'])
@login_required
def processar_criar_convite():
    """Processar criação de novo convite"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Obter dados do formulário
        invited_email = request.form.get('invited_email', '').strip()
        service_title = request.form.get('service_title', '').strip()
        service_description = request.form.get('service_description', '').strip()
        original_value = float(request.form.get('original_value', 0))
        delivery_date_str = request.form.get('delivery_date', '')
        
        # Validações básicas
        if not invited_email or '@' not in invited_email:
            flash('Email do prestador é obrigatório e deve ser válido.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        if not service_title:
            flash('Título do serviço é obrigatório.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        if not service_description:
            flash('Descrição do serviço é obrigatória.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        if original_value <= 0:
            flash('Valor do serviço deve ser maior que zero.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        # Converter data de entrega
        try:
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d')
            if delivery_date <= datetime.now():
                flash('Data de entrega deve ser futura.', 'error')
                return redirect(url_for('cliente.criar_convite'))
        except ValueError:
            flash('Data de entrega inválida.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        # Criar o convite
        result = InviteService.create_invite(
            client_id=user.id,
            invited_email=invited_email,
            service_title=service_title,
            service_description=service_description,
            original_value=original_value,
            delivery_date=delivery_date
        )
        
        flash(f'Convite criado com sucesso! O prestador receberá uma notificação no email {invited_email}.', 'success')
        return redirect(url_for('cliente.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao criar convite: {str(e)}', 'error')
    
    return redirect(url_for('cliente.criar_convite'))

@cliente_bp.route('/convites/<int:invite_id>')
@login_required
def ver_convite(invite_id):
    """Ver detalhes de um convite específico"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        from models import Invite
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite pertence ao cliente
        if invite.client_id != user.id:
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('cliente.convites'))
        
        return render_template('cliente/ver_convite.html', 
                             user=user, 
                             invite=invite)
        
    except Exception as e:
        flash(f'Erro ao carregar convite: {str(e)}', 'error')
        return redirect(url_for('cliente.convites'))

@cliente_bp.route('/convites/<int:invite_id>/converter', methods=['POST'])
@login_required
def converter_convite(invite_id):
    """Converter convite aceito em ordem de serviço"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        from models import Invite
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite pertence ao cliente
        if invite.client_id != user.id:
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('cliente.convites'))
        
        # Verificar se o convite pode ser convertido
        if invite.status != 'aceito':
            flash('Apenas convites aceitos podem ser convertidos em ordens.', 'error')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
        
        # Converter para ordem
        result = InviteService.convert_invite_to_order(invite_id)
        
        flash(f'Convite convertido em ordem de serviço com sucesso! Ordem #{result["order_id"]} criada.', 'success')
        return redirect(url_for('cliente.ordens'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao converter convite: {str(e)}', 'error')
    
    return redirect(url_for('cliente.convites'))
