#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, make_response, jsonify
from forms import CreateUserForm, EditUserForm, SystemConfigForm, AddTokensForm
from models import User, AdminUser, Order, Transaction, db, Invite
from services.admin_service import AdminService
from services.auth_service import admin_required
from services.report_service import ReportService
from services.security_validator import SecurityValidator, rate_limit
from sqlalchemy import desc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ==============================================================================
#  DASHBOARD ADMINISTRATIVO
# ==============================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard principal do administrador"""
    stats = AdminService.get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

# ==============================================================================
#  GESTÃO DE PERFIL ADMIN
# ==============================================================================

@admin_bp.route('/alterar-senha', methods=['GET', 'POST'])
@admin_required
def alterar_senha():
    """Alterar senha do administrador com tratamento robusto de erros"""
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            senha_atual = request.form.get('senha_atual', '').strip()
            nova_senha = request.form.get('nova_senha', '').strip()
            confirmar_senha = request.form.get('confirmar_senha', '').strip()
            
            # Validações básicas de entrada
            if not senha_atual or not nova_senha or not confirmar_senha:
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template('admin/alterar_senha.html')
            
            if nova_senha != confirmar_senha:
                flash('A nova senha e a confirmação não coincidem.', 'error')
                return render_template('admin/alterar_senha.html')
            
            # Verificar sessão admin
            admin_id = session.get('admin_id')
            if not admin_id:
                flash('Sessão expirada. Faça login novamente.', 'error')
                return redirect(url_for('auth.admin_login'))
            
            # Usar AdminService para trocar senha com tratamento robusto
            from services.admin_service import AdminService
            result = AdminService.change_admin_password(admin_id, senha_atual, nova_senha)
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(result['error'], 'error')
                return render_template('admin/alterar_senha.html')
            
        except Exception as e:
            # Log do erro crítico
            import logging
            logger = logging.getLogger('app')
            logger.error(f"Erro crítico na troca de senha admin: {str(e)}")
            
            # Mensagem genérica para o usuário
            flash('Erro interno do servidor. O erro foi registrado automaticamente nos logs para análise técnica. Verifique os logs do sistema ou tente novamente em alguns minutos.', 'error')
            return render_template('admin/alterar_senha.html')
    
    return render_template('admin/alterar_senha.html')

# ==============================================================================
#  GESTÃO DE USUÁRIOS
# ==============================================================================

@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    """Lista todos os usuários do sistema"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/usuarios.html', users=users)

@admin_bp.route('/usuarios/criar', methods=['GET', 'POST'])
@admin_required
def criar_usuario():
    """Criar novo usuário"""
    form = CreateUserForm()
    if form.validate_on_submit():
        try:
            nome = form.nome.data
            email = form.email.data
            cpf = form.cpf.data
            phone = form.phone.data
            password = form.password.data
            roles = form.roles.data
            
            # Criar usuário
            user = AdminService.create_user(
                nome=nome,
                email=email,
                cpf=cpf,
                phone=phone,
                password=password,
                roles=roles
            )
            flash(f'Usuário {user.nome} criado com sucesso!', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
        
        # Se o formulário não for validado, as mensagens de erro do WTForms serão exibidas
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Campo {getattr(form, field).label.text}: {error}", 'error')
    
    return render_template('admin/criar_usuario.html', form=form)

@admin_bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_usuario(user_id):
    """Editar usuário existente"""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        try:
            AdminService.update_user(user, form.data)
            flash(f'Usuário {user.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return render_template('admin/editar_usuario.html', form=form, user=user)

@admin_bp.route('/usuarios/<int:user_id>/deletar', methods=['POST'])
@admin_required
def deletar_usuario(user_id):
    """Deletar usuário usando soft delete"""
    from flask import request
    from services.auth_service import AuthService
    
    # Obter admin atual
    current_admin = AuthService.get_current_admin()
    if not current_admin:
        flash('Erro: Admin não encontrado na sessão', 'error')
        return redirect(url_for('admin.usuarios'))
    
    # Obter motivo da exclusão (opcional)
    reason = request.form.get('reason', '').strip()
    if not reason:
        reason = 'Exclusão via painel administrativo'
    
    # Executar soft delete
    result = AdminService.delete_user(user_id, current_admin.id, reason)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Erro ao deletar usuário: {result['error']}", 'error')
    
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/<int:user_id>/restaurar', methods=['POST'])
@admin_required
def restaurar_usuario(user_id):
    """Restaurar usuário deletado"""
    from services.auth_service import AuthService
    
    # Obter admin atual
    current_admin = AuthService.get_current_admin()
    if not current_admin:
        flash('Erro: Admin não encontrado na sessão', 'error')
        return redirect(url_for('admin.usuarios_deletados'))
    
    # Executar restauração
    result = AdminService.restore_user(user_id, current_admin.id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f"Erro ao restaurar usuário: {result['error']}", 'error')
    
    return redirect(url_for('admin.usuarios_deletados'))

@admin_bp.route('/usuarios/deletados')
@admin_required
def usuarios_deletados():
    """Listar usuários deletados"""
    result = AdminService.get_deleted_users()
    
    if result['success']:
        users = result['users']
    else:
        users = []
        flash(f"Erro ao carregar usuários deletados: {result['error']}", 'error')
    
    return render_template('admin/usuarios_deletados.html', users=users)

# ==============================================================================
#  GESTÃO DE CONVITES
# ==============================================================================

@admin_bp.route('/convites')
@admin_required
def convites():
    """Dashboard de convites do sistema"""
    from models import Invite
    from sqlalchemy import func
    
    # Filtros
    status_filter = request.args.get('status', 'todos')
    page = request.args.get('page', 1, type=int)
    
    # Validar valores de status permitidos
    valid_statuses = ['todos', 'pendente', 'aceito', 'recusado', 'expirado', 'convertido']
    if status_filter not in valid_statuses:
        flash(f'Status inválido: {status_filter}. Mostrando todos os convites.', 'warning')
        status_filter = 'todos'
    
    # Query base
    query = Invite.query
    
    # Aplicar filtro de status
    if status_filter != 'todos':
        query = query.filter(Invite.status == status_filter)
    
    # Paginação
    convites = query.order_by(desc(Invite.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    stats = {
        'total': Invite.query.count(),
        'pendentes': Invite.query.filter_by(status='pendente').count(),
        'aceitos': Invite.query.filter_by(status='aceito').count(),
        'recusados': Invite.query.filter_by(status='recusado').count(),
        'expirados': Invite.query.filter_by(status='expirado').count(),
        'convertidos': Invite.query.filter_by(status='convertido').count(),
        'com_propostas': Invite.query.filter_by(has_active_proposal=True).count()
    }
    
    return render_template('admin/convites.html', 
                         convites=convites, 
                         stats=stats,
                         status_filter=status_filter)

@admin_bp.route('/convites/<int:invite_id>')
@admin_required
def ver_convite(invite_id):
    """Ver detalhes de um convite específico"""
    from models import Invite
    convite = Invite.query.get_or_404(invite_id)
    return render_template('admin/ver_convite.html', convite=convite)

# ==============================================================================
#  GESTÃO DE ORDENS
# ==============================================================================

@admin_bp.route('/ordens')
@admin_required
def ordens():
    """Lista todas as ordens do sistema com filtros"""
    from datetime import datetime, timedelta
    
    # Obter parâmetros de filtro
    status_filter = request.args.get('status', '')
    user_id_filter = request.args.get('user_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    
    # Validar valores de status permitidos
    valid_statuses = ['aguardando_execucao', 'servico_executado', 'concluida', 'cancelada', 'contestada', 'resolvida']
    if status_filter and status_filter not in valid_statuses:
        flash(f'Status inválido: {status_filter}. Mostrando todas as ordens.', 'warning')
        status_filter = ''
    
    # Query base
    query = Order.query
    
    # Aplicar filtro de status
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    # Aplicar filtro de usuário (cliente ou prestador)
    if user_id_filter:
        query = query.filter(
            db.or_(
                Order.client_id == user_id_filter,
                Order.provider_id == user_id_filter
            )
        )
    
    # Aplicar filtro de data (date_from)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= date_from_obj)
        except ValueError:
            flash('Formato de data inválido para "Data Inicial"', 'error')
    
    # Aplicar filtro de data (date_to)
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Adicionar 1 dia para incluir todo o dia selecionado
            date_to_obj = date_to_obj + timedelta(days=1)
            query = query.filter(Order.created_at < date_to_obj)
        except ValueError:
            flash('Formato de data inválido para "Data Final"', 'error')
    
    # Eager loading de relacionamentos para otimização
    query = query.options(
        db.joinedload(Order.client),
        db.joinedload(Order.provider)
    )
    
    # Ordenar por data de criação (mais recentes primeiro) e paginar
    ordens = query.order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas gerais
    stats = {
        'total': Order.query.count(),
        'aguardando_execucao': Order.query.filter_by(status='aguardando_execucao').count(),
        'servico_executado': Order.query.filter_by(status='servico_executado').count(),
        'concluida': Order.query.filter_by(status='concluida').count(),
        'cancelada': Order.query.filter_by(status='cancelada').count(),
        'contestada': Order.query.filter_by(status='contestada').count(),
        'resolvida': Order.query.filter_by(status='resolvida').count()
    }
    
    # Lista de usuários para o filtro (top 50 usuários com mais ordens)
    from sqlalchemy import func
    top_users = db.session.query(
        User.id, 
        User.nome, 
        User.email,
        func.count(Order.id).label('order_count')
    ).join(
        Order, 
        db.or_(Order.client_id == User.id, Order.provider_id == User.id)
    ).group_by(
        User.id, User.nome, User.email
    ).order_by(
        desc('order_count')
    ).limit(50).all()
    
    return render_template('admin/ordens.html', 
                         ordens=ordens,
                         stats=stats,
                         status_filter=status_filter,
                         user_id_filter=user_id_filter,
                         date_from=date_from,
                         date_to=date_to,
                         top_users=top_users)

@admin_bp.route('/ordens/<int:order_id>')
@admin_required
def ver_ordem(order_id):
    """Exibe detalhes completos de uma ordem específica"""
    # Buscar ordem com eager loading de relacionamentos
    order = Order.query.options(
        db.joinedload(Order.client),
        db.joinedload(Order.provider),
        db.joinedload(Order.cancelled_by_user),
        db.joinedload(Order.dispute_opener)
    ).get_or_404(order_id)
    
    # Buscar transações relacionadas à ordem
    transactions = Transaction.query.filter_by(order_id=order_id).order_by(
        Transaction.created_at.desc()
    ).all()
    
    # Buscar convite relacionado se existir
    invite = None
    if order.invite_id:
        invite = Invite.query.get(order.invite_id)
    
    # Calcular informações adicionais
    hours_remaining = None
    if order.status == 'servico_executado' and order.confirmation_deadline:
        time_remaining = order.confirmation_deadline - datetime.utcnow()
        hours_remaining = max(0, time_remaining.total_seconds() / 3600)
    
    return render_template('admin/ver_ordem.html',
                         order=order,
                         transactions=transactions,
                         invite=invite,
                         hours_remaining=hours_remaining)

# ==============================================================================
#  GESTÃO DE CONTRATOS
# ==============================================================================

@admin_bp.route('/contratos')
@admin_required
def contratos():
    """Lista todos os contratos do sistema com filtros opcionais"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'todos')
    
    # Construir query base
    query = Order.query
    
    # Aplicar filtro de status se especificado
    if status_filter == 'ativo':
        # Contratos ativos (não finalizados/cancelados)
        query = query.filter(Order.status.in_(['aguardando_execucao', 'servico_executado', 'contestada']))
    elif status_filter == 'finalizado':
        # Contratos finalizados (concluídos ou cancelados)
        query = query.filter(Order.status.in_(['concluida', 'cancelada', 'resolvida']))
    # Se 'todos', não aplica filtro
    
    # Paginar resultados
    contratos = query.order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/contratos.html', 
                         contratos=contratos,
                         status_filter=status_filter)

# ==============================================================================
#  GESTÃO DE TOKENS
# ==============================================================================

@admin_bp.route('/tokens')
@admin_required
def tokens():
    """Gestão de tokens do sistema"""
    try:
        # Obter dados completos para gestão de tokens
        token_data = AdminService.get_token_management_data()
        
        # Obter alertas de atividade suspeita
        alerts = AdminService.get_suspicious_activity_alerts()
        
        # Validar integridade do sistema
        integrity_check = AdminService.validate_system_integrity()
        
        return render_template('admin/tokens.html', 
                             token_data=token_data,
                             alerts=alerts,
                             integrity_check=integrity_check)
    except Exception as e:
        flash(f'Erro ao carregar dados de tokens: {str(e)}', 'error')
        return render_template('admin/tokens.html', 
                             token_data=None,
                             alerts=[],
                             integrity_check=None)

@admin_bp.route('/tokens/adicionar', methods=['GET', 'POST'])
@admin_required
def adicionar_tokens():
    """Adicionar tokens para usuário"""
    form = AddTokensForm()
    
    # Incluir usuários normais ativos
    user_choices = [(u.id, f'{u.nome} ({u.email})') for u in User.query.filter_by(active=True).all()]
    
    # Incluir AdminUsers (para transferências entre admins)
    admin_choices = [(a.id, f'[ADMIN] {a.email}') for a in AdminUser.query.all() if a.id != 0]  # Excluir admin principal
    
    # Combinar as listas
    form.user_id.choices = user_choices + admin_choices
    
    if form.validate_on_submit():
        try:
            user_id = form.user_id.data
            
            # Tentar buscar primeiro como User normal
            user = User.query.get(user_id)
            if user:
                AdminService.add_tokens_to_user(user, form.amount.data, form.description.data)
                flash(f'Tokens adicionados com sucesso para {user.nome}!', 'success')
            else:
                # Se não encontrou como User, buscar como AdminUser
                admin_user = AdminUser.query.get(user_id)
                if admin_user:
                    # Para AdminUsers, usar o WalletService diretamente
                    from services.wallet_service import WalletService
                    result = WalletService.admin_sell_tokens_to_user(
                        user_id=admin_user.id,
                        amount=form.amount.data,
                        description=form.description.data
                    )
                    flash(f'Tokens transferidos com sucesso para admin {admin_user.email}!', 'success')
                else:
                    flash('Usuário não encontrado!', 'error')
                    return render_template('admin/adicionar_tokens.html', form=form)
            
            return redirect(url_for('admin.tokens'))
        except Exception as e:
            flash(f'Erro ao adicionar tokens: {str(e)}', 'error')
    
    return render_template('admin/adicionar_tokens.html', form=form)

@admin_bp.route('/tokens/criar', methods=['GET', 'POST'])
@admin_required
def criar_tokens():
    """Criar novos tokens no sistema"""
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', 'Criação de tokens pelo admin')
            
            if amount <= 0:
                flash('Quantidade deve ser maior que zero.', 'error')
                return render_template('admin/criar_tokens.html')
            
            # Usar AdminService para criar tokens
            AdminService.create_tokens(amount, description)
            
            flash(f'{amount} tokens criados com sucesso!', 'success')
            return redirect(url_for('admin.tokens'))
        except Exception as e:
            flash(f'Erro ao criar tokens: {str(e)}', 'error')
    
    return render_template('admin/criar_tokens.html')

@admin_bp.route('/tokens/solicitacoes')
@admin_required
def solicitacoes_tokens():
    """Gerenciar solicitações de tokens dos usuários"""
    try:
        from models import TokenRequest, User
        
        # Obter todas as solicitações ordenadas por data
        solicitacoes = TokenRequest.query.order_by(TokenRequest.created_at.desc()).all()
        
        # Estatísticas
        stats = {
            'total': len(solicitacoes),
            'pendentes': len([s for s in solicitacoes if s.status == 'pending']),
            'aprovadas': len([s for s in solicitacoes if s.status == 'approved']),
            'rejeitadas': len([s for s in solicitacoes if s.status == 'rejected']),
            'valor_total_pendente': sum([s.amount for s in solicitacoes if s.status == 'pending'])
        }
        
        return render_template('admin/solicitacoes_tokens.html', 
                             solicitacoes=solicitacoes,
                             stats=stats)
    except Exception as e:
        import traceback
        logger.error(f'Erro detalhado ao carregar solicitações: {str(e)}')
        logger.error(f'Traceback: {traceback.format_exc()}')
        flash(f'Erro ao carregar solicitações: {str(e)}', 'error')
        return render_template('admin/solicitacoes_tokens.html', 
                             solicitacoes=[],
                             stats={})

@admin_bp.route('/tokens/solicitacoes/<int:request_id>/processar', methods=['POST'])
@admin_required
def processar_solicitacao_token(request_id):
    """Processar (aprovar/rejeitar) solicitação de token"""
    try:
        from models import TokenRequest, User
        from services.wallet_service import WalletService
        from datetime import datetime
        import logging
        
        logger = logging.getLogger('app')
        logger.info(f"Processando solicitação {request_id}")
        
        solicitacao = TokenRequest.query.get(request_id)
        if not solicitacao:
            logger.error(f"Solicitação {request_id} não encontrada")
            flash('Solicitação não encontrada.', 'error')
            return redirect(url_for('admin.solicitacoes_tokens'))
        
        # Refresh do objeto para garantir que temos os dados mais recentes do banco
        db.session.refresh(solicitacao)
        logger.info(f"Solicitação carregada - ID: {solicitacao.id}, Amount: {solicitacao.amount}, Status: {solicitacao.status}")
        
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes', '')
        
        logger.info(f"Action: {action}, Admin notes: {admin_notes}")
        
        if action == 'approve':
            logger.info(f"Aprovando solicitação {request_id}")
            logger.info(f"Valor da solicitação: R$ {solicitacao.amount}")
            logger.info(f"Admin notes: {solicitacao.admin_notes}")
            
            # Aprovar e adicionar tokens
            user = User.query.get(solicitacao.user_id)
            if user:
                logger.info(f"Usuário encontrado: {user.nome}")
                logger.info(f"Adicionando {solicitacao.amount} tokens para o usuário")
                
                # Usar WalletService para adicionar tokens
                result = WalletService.admin_sell_tokens_to_user(
                    user_id=user.id,
                    amount=solicitacao.amount,
                    description=f'Aprovação de solicitação #{solicitacao.id}'
                )
                logger.info(f"Tokens adicionados com sucesso: {result}")
                
                # Atualizar status da solicitação
                solicitacao.status = 'approved'
                solicitacao.processed_at = datetime.utcnow()
                solicitacao.processed_by = session.get('admin_id')
                solicitacao.admin_notes = admin_notes
                
                db.session.commit()
                logger.info(f"Status da solicitação atualizado")
                
                flash(f'Solicitação aprovada! {solicitacao.amount} tokens adicionados para {user.nome}.', 'success')
            else:
                logger.error(f"Usuário {solicitacao.user_id} não encontrado")
                flash('Usuário não encontrado.', 'error')
                
        elif action == 'reject':
            logger.info(f"Rejeitando solicitação {request_id}")
            # Rejeitar solicitação
            solicitacao.status = 'rejected'
            solicitacao.processed_at = datetime.utcnow()
            solicitacao.processed_by = session.get('admin_id')
            solicitacao.admin_notes = admin_notes
            
            db.session.commit()
            logger.info(f"Solicitação rejeitada com sucesso")
            
            flash('Solicitação rejeitada.', 'info')
        else:
            logger.warning(f"Action inválida: {action}")
            flash('Ação inválida.', 'error')
        
    except Exception as e:
        logger.error(f'Erro ao processar solicitação {request_id}: {str(e)}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
        flash(f'Erro ao processar solicitação: {str(e)}', 'error')
    
    return redirect(url_for('admin.solicitacoes_tokens'))

@admin_bp.route('/tokens/solicitacoes/<int:request_id>/comprovante')
@admin_required
def view_receipt(request_id):
    """Visualizar comprovante de depósito"""
    try:
        from models import TokenRequest
        import os
        from flask import send_file
        
        solicitacao = TokenRequest.query.get(request_id)
        if not solicitacao:
            flash('Solicitação não encontrada.', 'error')
            return redirect(url_for('admin.solicitacoes_tokens'))
        
        if not solicitacao.receipt_filename:
            flash('Comprovante não encontrado.', 'error')
            return redirect(url_for('admin.solicitacoes_tokens'))
        
        # Caminho do arquivo
        file_path = os.path.join('uploads/receipts', solicitacao.receipt_filename)
        
        if not os.path.exists(file_path):
            flash('Arquivo de comprovante não encontrado no servidor.', 'error')
            return redirect(url_for('admin.solicitacoes_tokens'))
        
        # Retornar arquivo para visualização
        return send_file(
            file_path,
            as_attachment=False,
            download_name=solicitacao.receipt_original_name or solicitacao.receipt_filename
        )
        
    except Exception as e:
        logger.error(f'Erro ao visualizar comprovante {request_id}: {str(e)}')
        flash(f'Erro ao visualizar comprovante: {str(e)}', 'error')
        return redirect(url_for('admin.solicitacoes_tokens'))

@admin_bp.route('/tokens/solicitacoes/<int:request_id>/ajustar', methods=['POST'])
@admin_required
def ajustar_quantidade_solicitacao(request_id):
    """
    Rota para ajustar a quantidade de tokens de uma solicitação pendente.
    
    Esta rota permite que administradores corrijam discrepâncias entre o valor
    solicitado e o valor efetivamente pago antes de aprovar a solicitação.
    
    Endpoint: POST /admin/tokens/solicitacoes/<request_id>/ajustar
    
    Parâmetros JSON esperados:
        - new_amount (float/Decimal): Nova quantidade de tokens (obrigatório)
        - adjustment_reason (str): Justificativa do ajuste (opcional, máx 500 caracteres)
    
    Validações realizadas:
        1. Autenticação do administrador
        2. Existência da solicitação
        3. Status da solicitação (deve ser 'pending')
        4. Formato e valor do new_amount (> 0 e diferente do atual)
        5. Tamanho da justificativa (máx 500 caracteres)
    
    Respostas:
        200: Ajuste realizado com sucesso
        400: Erro de validação (dados inválidos, status incorreto, etc)
        401: Admin não autenticado
        404: Solicitação não encontrada
        500: Erro interno do servidor
    
    Exemplo de requisição:
        POST /admin/tokens/solicitacoes/123/ajustar
        Content-Type: application/json
        {
            "new_amount": 50.00,
            "adjustment_reason": "Comprovante mostra pagamento de apenas R$ 50,00"
        }
    
    Exemplo de resposta de sucesso:
        {
            "success": true,
            "message": "Quantidade ajustada com sucesso",
            "old_amount": 100.0,
            "new_amount": 50.0,
            "request_id": 123
        }
    """
    try:
        from models import TokenRequest
        from decimal import Decimal, InvalidOperation
        from services.auth_service import AuthService
        
        # PASSO 1: Obter administrador atual da sessão
        # Necessário para registro de auditoria e validação de permissões
        current_admin = AuthService.get_current_admin()
        if not current_admin:
            return jsonify({'success': False, 'error': 'Admin não encontrado na sessão'}), 401
        
        # PASSO 2: Buscar solicitação no banco de dados
        # Verificamos se a solicitação existe antes de prosseguir
        solicitacao = TokenRequest.query.get(request_id)
        if not solicitacao:
            return jsonify({'success': False, 'error': 'Solicitação não encontrada'}), 404
        
        # PASSO 3: Validar que a solicitação está com status 'pending'
        # Apenas solicitações pendentes podem ser ajustadas
        # Solicitações aprovadas ou rejeitadas não devem ser modificadas
        if solicitacao.status != 'pending':
            return jsonify({'success': False, 'error': 'Apenas solicitações pendentes podem ser ajustadas'}), 400
        
        # PASSO 4: Obter dados do corpo da requisição JSON
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        # PASSO 5: Extrair parâmetros da requisição
        new_amount_str = data.get('new_amount')
        adjustment_reason = data.get('adjustment_reason', '').strip()
        
        # PASSO 6: Validar que new_amount foi fornecido
        if new_amount_str is None:
            return jsonify({'success': False, 'error': 'O campo new_amount é obrigatório'}), 400
        
        # PASSO 7: Converter new_amount para Decimal
        # Usamos Decimal para garantir precisão em valores monetários
        try:
            new_amount = Decimal(str(new_amount_str))
        except (InvalidOperation, ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Valor inválido para new_amount'}), 400
        
        # PASSO 8: Validar que o novo valor é maior que zero
        # Não permitimos valores negativos ou zero
        if new_amount <= 0:
            return jsonify({'success': False, 'error': 'O novo valor deve ser maior que zero'}), 400
        
        # PASSO 9: Validar que o novo valor é diferente do atual
        # Evita ajustes desnecessários que não alteram nada
        if new_amount == solicitacao.amount:
            return jsonify({'success': False, 'error': 'O novo valor deve ser diferente do valor atual'}), 400
        
        # PASSO 10: Validar tamanho da justificativa se fornecida
        # Limitamos a 500 caracteres para evitar textos muito longos
        if adjustment_reason and len(adjustment_reason) > 500:
            return jsonify({'success': False, 'error': 'A justificativa não pode exceder 500 caracteres'}), 400
        
        # PASSO 11: Chamar AdminService para realizar o ajuste
        # O service layer contém toda a lógica de negócio e validações adicionais
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=new_amount,
            admin_id=current_admin.id,
            reason=adjustment_reason if adjustment_reason else None
        )
        
        # PASSO 12: Processar resultado do service
        if result['success']:
            # Registrar log de auditoria para operação bem-sucedida
            logger.info(
                f"Admin {current_admin.id} ajustou solicitação {request_id} "
                f"de R$ {result['old_amount']} para R$ {result['new_amount']}"
            )
            # Retornar resposta de sucesso com dados do ajuste
            return jsonify({
                'success': True,
                'message': result['message'],
                'old_amount': float(result['old_amount']),
                'new_amount': float(result['new_amount']),
                'request_id': request_id
            }), 200
        else:
            # Retornar erro retornado pelo service
            return jsonify({'success': False, 'error': result.get('error', 'Erro desconhecido')}), 400
        
    except ValueError as e:
        # Erro de validação: registrar warning e retornar erro 400
        logger.warning(f"Erro de validação ao ajustar solicitação {request_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        # Erro inesperado: registrar erro completo, fazer rollback e retornar erro 500
        logger.error(f"Erro ao ajustar solicitação {request_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erro interno ao processar ajuste'}), 500

# ==============================================================================
#  GESTÃO DE CONFIGURAÇÕES
# ==============================================================================

@admin_bp.route('/configuracoes', methods=['GET'])
@admin_required
def configuracoes():
    """Página índice de configurações com links para diferentes seções"""
    return render_template('admin/configuracoes_index.html')

# ==============================================================================
#  GESTÃO DE CONFIGURAÇÕES DE TAXAS
# ==============================================================================

@admin_bp.route('/configuracoes/taxas', methods=['GET'])
@admin_required
def configuracoes_taxas():
    """Exibe formulário de configuração de taxas do sistema"""
    from services.config_service import ConfigService
    
    try:
        # Obter taxas atuais do ConfigService
        fees = ConfigService.get_all_fees()
        
        return render_template('admin/configuracoes_taxas.html', fees=fees)
    except Exception as e:
        logger.error(f"Erro ao carregar configurações de taxas: {str(e)}")
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/configuracoes/taxas', methods=['POST'])
@admin_required
def salvar_configuracoes_taxas():
    """Processa atualização das taxas do sistema"""
    from services.config_service import ConfigService
    from services.auth_service import AuthService
    from decimal import Decimal, InvalidOperation
    
    # Obter admin atual
    current_admin = AuthService.get_current_admin()
    if not current_admin:
        flash('Erro: Admin não encontrado na sessão', 'error')
        return redirect(url_for('admin.configuracoes_taxas'))
    
    try:
        # Obter valores do formulário
        platform_fee = request.form.get('platform_fee_percentage', '').strip()
        contestation_fee = request.form.get('contestation_fee', '').strip()
        cancellation_fee = request.form.get('cancellation_fee_percentage', '').strip()
        
        # Validações básicas
        if not platform_fee or not contestation_fee or not cancellation_fee:
            flash('Todos os campos são obrigatórios.', 'error')
            return redirect(url_for('admin.configuracoes_taxas'))
        
        # Converter para Decimal e validar
        try:
            platform_fee_decimal = Decimal(platform_fee)
            contestation_fee_decimal = Decimal(contestation_fee)
            cancellation_fee_decimal = Decimal(cancellation_fee)
        except InvalidOperation:
            flash('Valores inválidos. Use apenas números.', 'error')
            return redirect(url_for('admin.configuracoes_taxas'))
        
        # Validar taxa da plataforma (0-100%)
        if platform_fee_decimal < 0 or platform_fee_decimal > 100:
            flash('Taxa da plataforma deve estar entre 0% e 100%.', 'error')
            return redirect(url_for('admin.configuracoes_taxas'))
        
        # Validar taxa de contestação (valor positivo)
        if contestation_fee_decimal <= 0:
            flash('Taxa de contestação deve ser um valor positivo.', 'error')
            return redirect(url_for('admin.configuracoes_taxas'))
        
        # Validar taxa de cancelamento (0-100%)
        if cancellation_fee_decimal < 0 or cancellation_fee_decimal > 100:
            flash('Taxa de cancelamento deve estar entre 0% e 100%.', 'error')
            return redirect(url_for('admin.configuracoes_taxas'))
        
        # Atualizar taxas usando ConfigService
        success_count = 0
        errors = []
        
        # Atualizar taxa da plataforma
        success, message = ConfigService.set_platform_fee_percentage(
            platform_fee_decimal, 
            current_admin.id
        )
        if success:
            success_count += 1
        else:
            errors.append(f"Taxa da plataforma: {message}")
        
        # Atualizar taxa de contestação
        success, message = ConfigService.set_contestation_fee(
            contestation_fee_decimal, 
            current_admin.id
        )
        if success:
            success_count += 1
        else:
            errors.append(f"Taxa de contestação: {message}")
        
        # Atualizar taxa de cancelamento
        success, message = ConfigService.set_cancellation_fee_percentage(
            cancellation_fee_decimal, 
            current_admin.id
        )
        if success:
            success_count += 1
        else:
            errors.append(f"Taxa de cancelamento: {message}")
        
        # Exibir mensagens de resultado
        if success_count == 3:
            flash('Todas as taxas foram atualizadas com sucesso! As novas taxas serão aplicadas apenas para ordens criadas a partir de agora.', 'success')
            logger.info(
                f"Admin {current_admin.id} atualizou taxas: "
                f"plataforma={platform_fee_decimal}%, "
                f"contestação=R${contestation_fee_decimal}, "
                f"cancelamento={cancellation_fee_decimal}%"
            )
        elif success_count > 0:
            flash(f'{success_count} taxa(s) atualizada(s) com sucesso.', 'success')
            for error in errors:
                flash(error, 'error')
        else:
            flash('Erro ao atualizar taxas.', 'error')
            for error in errors:
                flash(error, 'error')
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de taxas: {str(e)}", exc_info=True)
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return redirect(url_for('admin.configuracoes_taxas'))

@admin_bp.route('/configuracoes/seguranca', methods=['GET'])
@admin_required
def configuracoes_seguranca():
    """Exibe formulário de configurações de segurança do sistema"""
    from services.config_service import ConfigService
    
    try:
        # Obter configurações de segurança atuais
        security_settings = {
            'session_timeout': ConfigService.get_config('session_timeout', 3600),
            'max_login_attempts': ConfigService.get_config('max_login_attempts', 5),
            'password_min_length': ConfigService.get_config('password_min_length', 8),
            'require_password_complexity': ConfigService.get_config('require_password_complexity', True),
            'enable_two_factor': ConfigService.get_config('enable_two_factor', False),
            'ip_whitelist_enabled': ConfigService.get_config('ip_whitelist_enabled', False),
            'ip_whitelist': ConfigService.get_config('ip_whitelist', ''),
        }
        
        return render_template('admin/configuracoes_seguranca.html', settings=security_settings)
    except Exception as e:
        logger.error(f"Erro ao carregar configurações de segurança: {str(e)}")
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/configuracoes/seguranca', methods=['POST'])
@admin_required
def salvar_configuracoes_seguranca():
    """Processa atualização das configurações de segurança"""
    from services.config_service import ConfigService
    from services.auth_service import AuthService
    
    # Obter admin atual
    current_admin = AuthService.get_current_admin()
    if not current_admin:
        flash('Erro: Admin não encontrado na sessão', 'error')
        return redirect(url_for('admin.configuracoes_seguranca'))
    
    try:
        # Obter valores do formulário
        session_timeout = request.form.get('session_timeout', '3600').strip()
        max_login_attempts = request.form.get('max_login_attempts', '5').strip()
        password_min_length = request.form.get('password_min_length', '8').strip()
        require_password_complexity = request.form.get('require_password_complexity') == 'on'
        enable_two_factor = request.form.get('enable_two_factor') == 'on'
        ip_whitelist_enabled = request.form.get('ip_whitelist_enabled') == 'on'
        ip_whitelist = request.form.get('ip_whitelist', '').strip()
        
        # Validações básicas
        try:
            session_timeout_int = int(session_timeout)
            max_login_attempts_int = int(max_login_attempts)
            password_min_length_int = int(password_min_length)
        except ValueError:
            flash('Valores numéricos inválidos.', 'error')
            return redirect(url_for('admin.configuracoes_seguranca'))
        
        # Validar limites
        if session_timeout_int < 300 or session_timeout_int > 86400:
            flash('Timeout de sessão deve estar entre 300 (5 min) e 86400 (24h) segundos.', 'error')
            return redirect(url_for('admin.configuracoes_seguranca'))
        
        if max_login_attempts_int < 3 or max_login_attempts_int > 20:
            flash('Tentativas máximas de login devem estar entre 3 e 20.', 'error')
            return redirect(url_for('admin.configuracoes_seguranca'))
        
        if password_min_length_int < 6 or password_min_length_int > 32:
            flash('Tamanho mínimo de senha deve estar entre 6 e 32 caracteres.', 'error')
            return redirect(url_for('admin.configuracoes_seguranca'))
        
        # Validar IP whitelist se habilitado
        if ip_whitelist_enabled and ip_whitelist:
            import re
            ips = [ip.strip() for ip in ip_whitelist.split(',')]
            ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
            for ip in ips:
                if not ip_pattern.match(ip):
                    flash(f'IP inválido na whitelist: {ip}', 'error')
                    return redirect(url_for('admin.configuracoes_seguranca'))
        
        # Atualizar configurações usando ConfigService
        success_count = 0
        errors = []
        
        configs = [
            ('session_timeout', session_timeout_int, 'seguranca'),
            ('max_login_attempts', max_login_attempts_int, 'seguranca'),
            ('password_min_length', password_min_length_int, 'seguranca'),
            ('require_password_complexity', require_password_complexity, 'seguranca'),
            ('enable_two_factor', enable_two_factor, 'seguranca'),
            ('ip_whitelist_enabled', ip_whitelist_enabled, 'seguranca'),
            ('ip_whitelist', ip_whitelist, 'seguranca'),
        ]
        
        for key, value, category in configs:
            success = ConfigService.set_config(key, value, category)
            if success:
                success_count += 1
            else:
                errors.append(f"Erro ao atualizar {key}")
        
        # Exibir mensagens de resultado
        if success_count == len(configs):
            flash('Configurações de segurança atualizadas com sucesso!', 'success')
            logger.info(f"Admin {current_admin.id} atualizou configurações de segurança")
        elif success_count > 0:
            flash(f'{success_count} configuração(ões) atualizada(s) com sucesso.', 'success')
            for error in errors:
                flash(error, 'error')
        else:
            flash('Erro ao atualizar configurações.', 'error')
            for error in errors:
                flash(error, 'error')
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de segurança: {str(e)}", exc_info=True)
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return redirect(url_for('admin.configuracoes_seguranca'))

# ==============================================================================
#  GESTÃO DE CONTESTAÇÕES - ARBITRAGEM
# ==============================================================================

@admin_bp.route('/contestacoes')
@admin_required
def contestacoes():
    """Lista todas as contestações com filtros por status"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'todas')
    
    # Validar valores de status permitidos
    valid_statuses = ['todas', 'pendente', 'em_analise']
    if status_filter not in valid_statuses:
        flash(f'Status inválido: {status_filter}. Mostrando todas as contestações.', 'warning')
        status_filter = 'todas'
    
    # Query base - ordens contestadas ou resolvidas
    query = Order.query.filter(
        db.or_(
            Order.status == 'contestada',
            Order.status == 'resolvida'
        )
    )
    
    # Aplicar filtro de status
    if status_filter == 'pendente':
        # Contestações pendentes = status 'contestada' sem análise iniciada
        query = query.filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes == None
        )
    elif status_filter == 'em_analise':
        # Contestações em análise = status 'contestada' com notas do admin (análise iniciada mas não resolvida)
        query = query.filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes != None
        )
    # Se 'todas', não aplica filtro adicional (mostra contestadas e resolvidas)
    
    # Eager loading e ordenação
    contestacoes = query.options(
        db.joinedload(Order.client),
        db.joinedload(Order.provider),
        db.joinedload(Order.dispute_opener)
    ).order_by(desc(Order.dispute_opened_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas
    stats = {
        'total_contestadas': Order.query.filter_by(status='contestada').count(),
        'total_pendentes': Order.query.filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes == None
        ).count(),
        'total_em_analise': Order.query.filter(
            Order.status == 'contestada',
            Order.dispute_admin_notes != None
        ).count(),
        'total_resolvidas': Order.query.filter_by(status='resolvida').count(),
        'resolvidas_cliente': Order.query.filter_by(status='resolvida', dispute_winner='client').count(),
        'resolvidas_prestador': Order.query.filter_by(status='resolvida', dispute_winner='provider').count()
    }
    
    return render_template('admin/contestacoes.html', 
                         contestacoes=contestacoes,
                         stats=stats,
                         status_filter=status_filter)

@admin_bp.route('/contestacoes/<int:order_id>')
@admin_required
def ver_contestacao(order_id):
    """Exibe detalhes completos de uma contestação para análise"""
    # Buscar ordem com eager loading de relacionamentos
    order = Order.query.options(
        db.joinedload(Order.client),
        db.joinedload(Order.provider),
        db.joinedload(Order.dispute_opener)
    ).get_or_404(order_id)
    
    # Verificar se a ordem está contestada
    if order.status != 'contestada':
        flash('Esta ordem não está contestada.', 'warning')
        return redirect(url_for('admin.ver_ordem', order_id=order_id))
    
    # Buscar transações relacionadas à ordem
    transactions = Transaction.query.filter_by(order_id=order_id).order_by(
        Transaction.created_at.desc()
    ).all()
    
    # Buscar convite relacionado se existir
    invite = None
    if order.invite_id:
        from models import Invite
        invite = Invite.query.get(order.invite_id)
    
    return render_template('admin/analisar_contestacao.html',
                         order=order,
                         transactions=transactions,
                         invite=invite)

@admin_bp.route('/contestacoes/<int:order_id>/resolver', methods=['POST'])
@admin_required
def resolver_contestacao(order_id):
    """Processa a resolução de uma contestação pelo admin"""
    from services.auth_service import AuthService
    from services.order_management_service import OrderManagementService
    
    # Obter admin atual
    current_admin = AuthService.get_current_admin()
    if not current_admin:
        flash('Erro: Admin não encontrado na sessão', 'error')
        return redirect(url_for('admin.contestacoes'))
    
    # Verificar rate limiting para evitar múltiplas resoluções acidentais
    is_allowed, error_msg = SecurityValidator.check_rate_limit(
        current_admin.id, 'resolve_dispute', max_attempts=10, window_seconds=60
    )
    if not is_allowed:
        flash(error_msg, 'error')
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    
    # Obter dados do formulário e sanitizar
    winner = request.form.get('winner', '').strip()
    admin_notes = SecurityValidator.sanitize_input(
        request.form.get('admin_notes', '').strip(),
        max_length=2000
    )
    
    # Validações básicas
    if not winner:
        flash('Você deve selecionar o vencedor da disputa.', 'error')
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    
    if winner not in ['client', 'provider']:
        flash('Vencedor inválido. Deve ser "client" ou "provider".', 'error')
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    
    if not admin_notes or len(admin_notes) < 10:
        flash('As notas do administrador são obrigatórias (mínimo 10 caracteres) para justificar a decisão.', 'error')
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    
    try:
        # Chamar OrderManagementService.resolve_dispute()
        result = OrderManagementService.resolve_dispute(
            order_id=order_id,
            admin_id=current_admin.id,
            winner=winner,
            admin_notes=admin_notes
        )
        
        if result['success']:
            winner_name = "cliente" if winner == 'client' else "prestador"
            flash(f'Contestação resolvida com sucesso a favor do {winner_name}!', 'success')
            logger.info(
                f"Admin {current_admin.id} resolveu contestação da ordem {order_id} "
                f"a favor do {winner_name}"
            )
        else:
            flash(f'Erro ao resolver contestação: {result.get("message", "Erro desconhecido")}', 'error')
        
    except ValueError as e:
        flash(f'Erro de validação: {str(e)}', 'error')
        logger.error(f"Erro de validação ao resolver contestação {order_id}: {e}")
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    except Exception as e:
        flash(f'Erro ao resolver contestação: {str(e)}', 'error')
        logger.error(f"Erro ao resolver contestação {order_id}: {e}", exc_info=True)
        return redirect(url_for('admin.ver_contestacao', order_id=order_id))
    
    # Redirecionar para lista de contestações
    return redirect(url_for('admin.contestacoes'))

# ==============================================================================
#  RELATÓRIOS
# ==============================================================================

@admin_bp.route('/relatorios')
@admin_required
def relatorios():
    """Página de relatórios administrativos"""
    # Exemplo de dados para relatórios
    total_users = User.query.count()
    total_orders = Order.query.count()
    total_disputes = Order.query.filter(Order.dispute_reason != None).count()
    
    # Gerar um relatório de exemplo (pode ser mais complexo)
    report_data = ReportService.get_users_report_data()
    
    return render_template('admin/relatorios.html', 
                           total_users=total_users, 
                           total_orders=total_orders, 
                           total_disputes=total_disputes,
                           report_data=report_data)

@admin_bp.route('/relatorios/gerar-pdf/<report_type>')
@admin_required
def gerar_pdf_relatorio(report_type):
    """Gerar PDF de relatórios"""
    try:
        pdf_buffer = ReportService.generate_pdf_report(report_type)
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.pdf'
        return response
    except Exception as e:
        flash(f'Erro ao gerar relatório PDF: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

# ==============================================================================
#  LOGS DO SISTEMA
# ==============================================================================

@admin_bp.route('/logs')
@admin_required
def logs():
    """Visualizar logs do sistema"""
    log_entries = AdminService.get_system_logs()
    return render_template('admin/logs.html', log_entries=log_entries)

# ==============================================================================
#  CONTROLES DO SISTEMA
# ==============================================================================

@admin_bp.route('/sistema/limpar-cache')
@admin_required
def limpar_cache():
    """Limpar cache do sistema"""
    try:
        AdminService.clear_cache()
        flash('Cache do sistema limpo com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao limpar cache: {str(e)}', 'error')
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/sistema/reiniciar')
@admin_required
def reiniciar_sistema():
    """Reiniciar serviços do sistema"""
    try:
        AdminService.restart_services()
        flash('Serviços do sistema reiniciados com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao reiniciar serviços: {str(e)}', 'error')
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/sistema/backup')
@admin_required
def fazer_backup():
    """Realizar backup do banco de dados"""
    try:
        backup_file = AdminService.perform_backup()
        flash(f'Backup realizado com sucesso: {backup_file}', 'success')
    except Exception as e:
        flash(f'Erro ao realizar backup: {str(e)}', 'error')
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/sistema/restaurar')
@admin_required
def restaurar_backup():
    """Restaurar banco de dados de um backup"""
    try:
        AdminService.restore_backup()
        flash('Banco de dados restaurado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao restaurar backup: {str(e)}', 'error')
    return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/sistema/auditoria')
@admin_required
def auditoria_sistema():
    """Executar auditoria completa do sistema"""
    try:
        audit_results = AdminService.run_system_audit()
        flash('Auditoria do sistema concluída. Verifique os logs para detalhes.', 'success')
        # Pode-se redirecionar para uma página de resultados de auditoria ou logs
    except Exception as e:
        flash(f'Erro ao executar auditoria: {str(e)}', 'error')
    return redirect(url_for('admin.configuracoes'))

# ==============================================================================
#  ROTAS DE ERRO PERSONALIZADAS
# ==============================================================================

@admin_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@admin_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# ==============================================================================
#  ROTA DE TESTE (APENAS PARA DESENVOLVIMENTO)
# ==============================================================================

@admin_bp.route('/test-error')
@admin_required
def test_error():
    """Rota para testar página de erro 500"""
    raise Exception("Este é um erro de teste intencional.")

@admin_bp.route('/test-404')
@admin_required
def test_404():
    """Rota para testar página de erro 404"""
    from werkzeug.exceptions import NotFound
    raise NotFound()



