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
    
    # Calcular estatísticas
    from models import Order
    all_orders = Order.query.filter_by(client_id=user.id).all()
    statistics = {
        'total': len(all_orders),
        'aguardando': len([o for o in all_orders if o.status == 'aceita']),
        'para_confirmar': len([o for o in all_orders if o.status == 'concluida']),
        'concluidas': len([o for o in all_orders if o.status == 'confirmada']),
        'em_disputa': len([o for o in all_orders if o.status == 'em_disputa']),
        'canceladas': len([o for o in all_orders if o.status == 'cancelada'])
    }
    
    return render_template('cliente/ordens.html', 
                         user=user, 
                         orders=orders,
                         statistics=statistics)

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
    
    # Obter solicitações recentes do usuário
    token_requests = ClienteService.get_user_token_requests(user.id)
    
    return render_template('cliente/solicitar_tokens.html', 
                         user=user, 
                         token_requests=token_requests)

@cliente_bp.route('/solicitar-tokens', methods=['POST'])
@login_required
def processar_solicitacao_tokens():
    """Processar solicitação de tokens com upload de comprovante"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        payment_method = request.form.get('payment_method', 'pix')
        
        if amount <= 0:
            flash('Quantidade deve ser maior que zero.', 'error')
            return redirect(url_for('cliente.solicitar_tokens'))
        
        # Verificar se foi enviado um arquivo
        receipt_file = request.files.get('receipt')
        if not receipt_file or receipt_file.filename == '':
            flash('Comprovante de depósito é obrigatório.', 'error')
            return redirect(url_for('cliente.solicitar_tokens'))
        
        # Validar tipo de arquivo
        allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
        file_extension = receipt_file.filename.rsplit('.', 1)[1].lower() if '.' in receipt_file.filename else ''
        
        if file_extension not in allowed_extensions:
            flash('Formato de arquivo não permitido. Use JPG, PNG ou PDF.', 'error')
            return redirect(url_for('cliente.solicitar_tokens'))
        
        # Registrar solicitação com comprovante
        ClienteService.create_token_request_with_receipt(
            user_id=user.id,
            amount=amount,
            description=description,
            payment_method=payment_method,
            receipt_file=receipt_file
        )
        
        flash('Solicitação enviada com sucesso! Comprovante recebido. Processamento em até 2 horas.', 'success')
        
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
    
    # Verificar se está copiando dados de um convite rejeitado
    copy_from_id = request.args.get('copy_from')
    edit_mode = request.args.get('edit') == 'true'
    copied_invite = None
    
    if copy_from_id:
        try:
            copied_invite = Invite.query.get(copy_from_id)
            if copied_invite and copied_invite.client_id == user.id and copied_invite.status == 'recusado':
                # Mostrar mensagem informativa sobre a cópia
                if edit_mode:
                    flash(f'Dados copiados do convite rejeitado. Você pode modificar as informações baseado no feedback: "{copied_invite.rejection_reason or "Sem motivo específico"}"', 'info')
                else:
                    flash(f'Dados copiados do convite rejeitado. Revise as informações antes de enviar.', 'info')
            else:
                copied_invite = None
                flash('Convite não encontrado ou não pode ser copiado.', 'warning')
        except Exception as e:
            copied_invite = None
            flash('Erro ao copiar dados do convite.', 'error')
    
    return render_template('cliente/criar_convite.html', 
                         user=user,
                         wallet=wallet_info,
                         contestation_fee=InviteService.CONTESTATION_FEE,
                         copied_invite=copied_invite,
                         edit_mode=edit_mode)

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
        invited_phone = request.form.get('invited_phone', '').strip()
        service_title = request.form.get('service_title', '').strip()
        service_description = request.form.get('service_description', '').strip()
        service_category = request.form.get('service_category', '').strip()
        # Manter como string para converter para Decimal no serviço
        original_value = request.form.get('original_value', '0')
        delivery_date_str = request.form.get('delivery_date', '')
        
        # Validações básicas
        if not invited_phone or len(invited_phone) < 10:
            flash('Telefone do prestador é obrigatório e deve ser válido.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        if not service_title:
            flash('Título do serviço é obrigatório.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        if not service_description:
            flash('Descrição do serviço é obrigatória.', 'error')
            return redirect(url_for('cliente.criar_convite'))
        
        # Validar e converter valor
        try:
            original_value_float = float(original_value)
            if original_value_float <= 0:
                flash('Valor do serviço deve ser maior que zero.', 'error')
                return redirect(url_for('cliente.criar_convite'))
        except (ValueError, TypeError):
            flash('Valor do serviço inválido.', 'error')
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
            invited_phone=invited_phone,
            service_title=service_title,
            service_description=service_description,
            original_value=original_value,
            delivery_date=delivery_date,
            service_category=service_category
        )
        
        # Marcar que o cliente já aceitou (pois ele é o criador do convite)
        # Assim, quando o prestador aceitar, a pré-ordem será criada automaticamente
        from models import Invite, db
        invite = Invite.query.get(result['invite_id'])
        if invite:
            invite.client_accepted = True
            invite.client_accepted_at = datetime.now()
            db.session.commit()
        
        # Gerar link do convite
        invite_link = result.get('invite_link', f"/convite/{result['token']}")
        
        flash(f'Convite criado com sucesso! Link para enviar ao prestador: {invite_link}', 'success')
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
        from models import Invite, Proposal
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite pertence ao cliente
        # O cliente é sempre o client_id, independente de ser contraproposta ou não
        if invite.client_id != user.id:
            # Se o usuário não é o cliente, verificar se ele é o prestador
            # Nesse caso, redirecionar para a view do prestador
            if 'prestador' in user.roles and invite.invited_phone == user.phone:
                flash('Este convite deve ser visualizado na área do prestador.', 'info')
                return redirect(url_for('prestador.ver_convite', token=invite.token))
            
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('cliente.convites'))
        
        # Carregar proposta ativa se existir
        current_proposal = None
        if invite.has_active_proposal and invite.current_proposal_id:
            current_proposal = Proposal.query.get(invite.current_proposal_id)
        
        # Adicionar proposta ao objeto invite para uso no template
        invite.current_proposal = current_proposal
        
        return render_template('cliente/ver_convite.html', 
                             user=user, 
                             invite=invite)
        
    except Exception as e:
        flash(f'Erro ao carregar convite: {str(e)}', 'error')
        return redirect(url_for('cliente.convites'))

@cliente_bp.route('/convites/<int:invite_id>/aceitar', methods=['POST'])
@login_required
def aceitar_convite(invite_id):
    """Aceitar um convite como cliente"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Usar o novo método de aceitação do InviteService
        result = InviteService.accept_invite_as_client(invite_id, user.id)
        
        # Verificar se a pré-ordem foi criada automaticamente
        if result.get('pre_order_created'):
            pre_order_id = result.get('pre_order_id')
            flash(f'Convite aceito com sucesso! Pré-ordem #{pre_order_id} criada. '
                  f'Você pode negociar os termos antes de confirmar.', 'success')
            # Redirecionar para a página de detalhes da pré-ordem
            return redirect(url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id))
        elif result.get('order_created'):
            # Fallback para ordem direta (caso legado)
            order_id = result.get('order_id')
            flash(f'Convite aceito com sucesso! Ordem #{order_id} criada automaticamente. '
                  f'Os valores foram bloqueados em garantia.', 'success')
            return redirect(url_for('cliente.ordens'))
        else:
            # Aguardando aceitação do prestador
            flash('Convite aceito com sucesso! Aguardando aceitação do prestador para criar a pré-ordem.', 'info')
            return redirect(url_for('cliente.convites'))
    
    except Exception as e:
        # Importar exceções personalizadas
        from services.exceptions import (
            InsufficientBalanceError,
            OrderCreationError,
            EscrowBlockError,
            InviteValidationError
        )
        
        # Tratamento específico por tipo de erro
        # Requirements: 7.4, 8.3, 8.4
        if isinstance(e, InsufficientBalanceError):
            # Erro de saldo insuficiente - mensagem clara com valores
            # Requirements: 7.4, 8.3, 8.4
            flash(f'{e.message}', 'error')
            flash('Você pode adicionar saldo através do menu "Solicitar Tokens".', 'info')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
            
        elif isinstance(e, OrderCreationError):
            # Erro na criação da ordem - convite permanece aceito
            # Requirements: 7.1, 7.2, 7.3, 7.4
            flash(f'{e.message}', 'error')
            flash('Seu convite permanece aceito. Você pode tentar novamente em alguns instantes.', 'info')
            return redirect(url_for('cliente.convites'))
            
        elif isinstance(e, EscrowBlockError):
            # Erro no bloqueio de escrow - operação cancelada
            # Requirements: 7.2, 7.5
            flash(f'{e.message}', 'error')
            flash('Seu convite permanece aceito. Nenhum valor foi debitado.', 'info')
            return redirect(url_for('cliente.convites'))
            
        elif isinstance(e, InviteValidationError):
            # Erro de validação do convite
            # Requirements: 7.4
            flash(f'Não foi possível aceitar o convite: {e.message}', 'error')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
            
        else:
            # Erro genérico
            # Requirements: 7.4
            error_message = str(e)
            flash(f'Erro ao aceitar convite: {error_message}. Por favor, tente novamente.', 'error')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))

# REMOVIDO: Conversão de convite agora é feita pelo prestador
# O prestador é quem ganha com o serviço e paga a taxa para a plataforma

@cliente_bp.route('/convites/<int:invite_id>/excluir', methods=['POST'])
@login_required
def excluir_convite(invite_id):
    """Excluir um convite (apenas se ainda não foi aceito/convertido)"""
    user = AuthService.get_current_user()
    
    if 'cliente' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        from models import Invite, db
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite pertence ao cliente
        if invite.client_id != user.id:
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('cliente.convites'))
        
        # Verificar se o convite pode ser excluído
        # Apenas convites finalizados podem ser excluídos (para limpar a lista)
        if invite.status == 'convertido':
            flash('Convites já convertidos em ordens não podem ser excluídos.', 'error')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
        
        if invite.status == 'pendente':
            flash('Convites pendentes não podem ser excluídos. Aguarde resposta do prestador.', 'warning')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
        
        if invite.status == 'proposta_enviada':
            flash('Convites com proposta pendente não podem ser excluídos. Responda a proposta primeiro.', 'warning')
            return redirect(url_for('cliente.ver_convite', invite_id=invite_id))
        
        # Salvar informações para mensagem
        service_title = invite.service_title
        
        # Excluir o convite
        db.session.delete(invite)
        db.session.commit()
        
        flash(f'Convite "{service_title}" excluído com sucesso.', 'success')
        return redirect(url_for('cliente.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao excluir convite: {str(e)}', 'error')
    
    return redirect(url_for('cliente.convites'))
