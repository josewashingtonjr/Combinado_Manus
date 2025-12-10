#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.auth_service import login_required, prestador_required, AuthService, user_loader_required
from services.prestador_service import PrestadorService
from services.invite_service import InviteService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
    
    # Buscar estatísticas para o dashboard
    from services.order_management_service import OrderManagementService
    statistics = OrderManagementService.get_order_statistics(user.id, 'prestador')
    
    return render_template('prestador/ordens.html', 
                         user=user, 
                         orders=orders,
                         status_filter=status_filter,
                         statistics=statistics)

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
    received_invites = InviteService.get_invites_for_phone(user.phone) if user.phone else []
    
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
        
        # Verificar se o convite é para este prestador OU se ele tem o token na sessão (fluxo de aceitação)
        has_session_token = session.get('invite_token') == token
        is_invited_phone = invite.invited_phone == user.phone
        
        # Verificar se o usuário é o cliente do convite
        # Se for, redirecionar para a view do cliente
        if 'cliente' in user.roles and invite.client_id == user.id:
            flash('Este convite deve ser visualizado na área do cliente.', 'info')
            return redirect(url_for('cliente.ver_convite', invite_id=invite.id))
        
        if not (is_invited_phone or has_session_token):
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
    """Aceitar um convite como prestador"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Obter o convite pelo token
        invite = InviteService.get_invite_by_token(token)
        
        # Usar o novo método de aceitação do InviteService
        result = InviteService.accept_invite_as_provider(invite.id, user.id)
        
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
            return redirect(url_for('prestador.ordens'))
        else:
            # Aguardando aceitação do cliente
            flash('Convite aceito com sucesso! Aguardando aceitação do cliente para criar a pré-ordem.', 'info')
            return redirect(url_for('prestador.convites'))
    
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
            return redirect(url_for('prestador.ver_convite', token=token))
            
        elif isinstance(e, OrderCreationError):
            # Erro na criação da ordem - convite permanece aceito
            # Requirements: 7.1, 7.2, 7.3, 7.4
            flash(f'{e.message}', 'error')
            flash('Seu convite permanece aceito. Você pode tentar novamente em alguns instantes.', 'info')
            return redirect(url_for('prestador.convites'))
            
        elif isinstance(e, EscrowBlockError):
            # Erro no bloqueio de escrow - operação cancelada
            # Requirements: 7.2, 7.5
            flash(f'{e.message}', 'error')
            flash('Seu convite permanece aceito. Nenhum valor foi debitado.', 'info')
            return redirect(url_for('prestador.convites'))
            
        elif isinstance(e, InviteValidationError):
            # Erro de validação do convite
            # Requirements: 7.4
            flash(f'Não foi possível aceitar o convite: {e.message}', 'error')
            return redirect(url_for('prestador.ver_convite', token=token))
            
        else:
            # Erro genérico
            # Requirements: 7.4
            error_message = str(e)
            flash(f'Erro ao aceitar convite: {error_message}. Por favor, tente novamente.', 'error')
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
        reason = request.form.get('reason', '') or request.form.get('rejection_reason', '')
        
        # Buscar convite pelo token
        invite = InviteService.get_invite_by_token(token)
        
        # Recusar o convite
        result = InviteService.reject_invite(
            invite=invite,
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
    """
    DEPRECATED: Esta rota foi descontinuada.
    Negociações de valor agora são feitas na tela de pré-ordem.
    
    Mantida apenas para compatibilidade - redireciona para o convite com mensagem informativa.
    """
    flash('Para negociar valores, primeiro aceite o convite. A negociação será feita na pré-ordem.', 'info')
    return redirect(url_for('prestador.ver_convite', token=token))

@prestador_bp.route('/convites/<int:invite_id>/excluir', methods=['POST'])
@login_required
def excluir_convite(invite_id):
    """Excluir um convite (apenas se já foi finalizado)"""
    user = AuthService.get_current_user()
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        from models import Invite, db
        invite = Invite.query.get_or_404(invite_id)
        
        # Verificar se o convite foi enviado para este prestador
        if invite.invited_phone != user.phone:
            flash('Convite não encontrado.', 'error')
            return redirect(url_for('prestador.convites'))
        
        # Verificar se o convite pode ser excluído
        # Prestador pode excluir apenas convites finalizados (para limpar a lista)
        if invite.status == 'convertido':
            flash('Convites já convertidos em ordens não podem ser excluídos.', 'error')
            return redirect(url_for('prestador.convites'))
        
        if invite.status == 'pendente':
            flash('Convites pendentes não podem ser excluídos. Responda o convite primeiro.', 'warning')
            return redirect(url_for('prestador.convites'))
        
        if invite.status == 'proposta_enviada':
            flash('Convites com proposta pendente não podem ser excluídos. Aguarde resposta do cliente.', 'warning')
            return redirect(url_for('prestador.convites'))
        
        # Salvar informações para mensagem
        service_title = invite.service_title
        
        # Excluir o convite
        db.session.delete(invite)
        db.session.commit()
        
        flash(f'Convite "{service_title}" excluído com sucesso.', 'success')
        return redirect(url_for('prestador.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao excluir convite: {str(e)}', 'error')
    
    return redirect(url_for('prestador.convites'))

# ==============================================================================
#  SOLICITAÇÃO DE TOKENS (ADICIONAR SALDO)
# ==============================================================================

@prestador_bp.route('/solicitar-tokens')
@user_loader_required
def solicitar_tokens(user):
    """Solicitar compra de tokens (controlada pelo admin)"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    # Usar o mesmo serviço do cliente para obter solicitações
    from services.cliente_service import ClienteService
    token_requests = ClienteService.get_user_token_requests(user.id)
    
    return render_template('prestador/solicitar_tokens.html', 
                         user=user, 
                         token_requests=token_requests)

@prestador_bp.route('/solicitar-tokens', methods=['POST'])
@user_loader_required
def processar_solicitacao_tokens(user):
    """Processar solicitação de tokens com upload de comprovante"""
    
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        payment_method = request.form.get('payment_method', 'pix')
        
        if amount <= 0:
            flash('Quantidade deve ser maior que zero.', 'error')
            return redirect(url_for('prestador.solicitar_tokens'))
        
        # Verificar se foi enviado um arquivo
        receipt_file = request.files.get('receipt')
        if not receipt_file or receipt_file.filename == '':
            flash('Comprovante de depósito é obrigatório.', 'error')
            return redirect(url_for('prestador.solicitar_tokens'))
        
        # Validar tipo de arquivo
        allowed_extensions = {'jpg', 'jpeg', 'png', 'pdf'}
        file_extension = receipt_file.filename.rsplit('.', 1)[1].lower() if '.' in receipt_file.filename else ''
        
        if file_extension not in allowed_extensions:
            flash('Formato de arquivo não permitido. Use JPG, PNG ou PDF.', 'error')
            return redirect(url_for('prestador.solicitar_tokens'))
        
        # Usar o mesmo serviço do cliente para criar solicitação
        from services.cliente_service import ClienteService
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
    
    return redirect(url_for('prestador.dashboard'))

@prestador_bp.route('/convites/criar')
@user_loader_required
def criar_convite(user):
    """Formulário para criar convite (prestador propondo serviço)"""
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    return render_template('prestador/criar_convite.html', user=user)

@prestador_bp.route('/convites/criar', methods=['POST'])
@user_loader_required
def processar_criar_convite(user):
    """Processar criação de convite pelo prestador"""
    if 'prestador' not in user.roles:
        flash('Acesso negado.', 'error')
        return redirect(url_for('auth.user_login'))
    
    try:
        # Obter dados do formulário
        client_email = request.form.get('client_email', '').strip()
        service_title = request.form.get('service_title', '').strip()
        service_description = request.form.get('service_description', '').strip()
        service_category = request.form.get('service_category', '').strip()
        # Manter como string para converter para Decimal no serviço
        proposed_value = request.form.get('proposed_value', '0')
        delivery_date_str = request.form.get('delivery_date', '')
        
        # Validações básicas
        if not client_email:
            flash('Email do cliente é obrigatório.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        if not service_title:
            flash('Título do serviço é obrigatório.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        if not service_description:
            flash('Descrição do serviço é obrigatória.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        # Validar e converter valor
        try:
            proposed_value_float = float(proposed_value)
            if proposed_value_float <= 0:
                flash('Valor do serviço deve ser maior que zero.', 'error')
                return redirect(url_for('prestador.criar_convite'))
        except (ValueError, TypeError):
            flash('Valor do serviço inválido.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        # Converter data de entrega
        try:
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d')
            if delivery_date <= datetime.now():
                flash('Data de entrega deve ser futura.', 'error')
                return redirect(url_for('prestador.criar_convite'))
        except ValueError:
            flash('Data de entrega inválida.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        # Verificar se o cliente existe no sistema
        from models import User
        client = User.query.filter_by(email=client_email).first()
        
        if not client:
            flash(f'Cliente com email {client_email} não encontrado no sistema. '
                  f'Convide-o a se cadastrar primeiro.', 'warning')
            return redirect(url_for('prestador.criar_convite'))
        
        if 'cliente' not in client.roles:
            flash(f'O usuário {client_email} não tem papel de cliente no sistema.', 'error')
            return redirect(url_for('prestador.criar_convite'))
        
        # Criar o convite (prestador propondo serviço para cliente)
        # Usamos o InviteService mas invertendo a lógica
        result = InviteService.create_invite(
            client_id=client.id,  # Cliente que vai receber
            invited_phone=user.phone,  # Prestador que está propondo (para rastreamento)
            service_title=service_title,
            service_description=service_description,
            original_value=proposed_value,
            delivery_date=delivery_date,
            service_category=service_category
        )
        
        # Marcar que o prestador já aceitou (pois ele é o criador da proposta)
        # Assim, quando o cliente aceitar, a pré-ordem será criada automaticamente
        from models import Invite, db
        invite = Invite.query.get(result['invite_id'])
        if invite:
            invite.provider_accepted = True
            invite.provider_accepted_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(
                f"Convite {invite.id} criado pelo prestador {user.id} ({user.nome}). "
                f"provider_accepted marcado como True automaticamente."
            )
        
        flash(f'Proposta de serviço enviada com sucesso para {client_email}!', 'success')
        return redirect(url_for('prestador.convites'))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Erro ao criar proposta: {str(e)}', 'error')
    
    return redirect(url_for('prestador.criar_convite'))
