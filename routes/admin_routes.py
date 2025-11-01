#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request, make_response
from forms import CreateUserForm, EditUserForm, SystemConfigForm, AddTokensForm
from models import User, AdminUser, Order, Transaction, db
from services.admin_service import AdminService
from services.auth_service import admin_required
from services.report_service import ReportService
from sqlalchemy import desc
from datetime import datetime

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
    """Deletar usuário"""
    user = User.query.get_or_404(user_id)
    try:
        AdminService.delete_user(user)
        flash(f'Usuário {user.nome} deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar usuário: {str(e)}', 'error')
    
    return redirect(url_for('admin.usuarios'))

# ==============================================================================
#  GESTÃO DE CONTRATOS
# ==============================================================================

@admin_bp.route('/contratos')
@admin_required
def contratos():
    """Lista todos os contratos do sistema"""
    page = request.args.get('page', 1, type=int)
    # Assumindo que 'Order' representa um contrato para fins de listagem
    contratos = Order.query.order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/contratos.html', contratos=contratos)

@admin_bp.route('/contratos/ativos')
@admin_required
def contratos_ativos():
    """Lista todos os contratos ativos (não finalizados/cancelados)"""
    page = request.args.get('page', 1, type=int)
    # Assumindo status 'ativo' para contratos em andamento
    contratos = Order.query.filter(Order.status.in_(['pendente', 'em_andamento', 'em_negociacao'])).order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/contratos.html', contratos=contratos)

@admin_bp.route('/contratos/finalizados')
@admin_required
def contratos_finalizados():
    """Lista todos os contratos finalizados (concluídos/cancelados)"""
    page = request.args.get('page', 1, type=int)
    # Assumindo status 'finalizado' para contratos concluídos ou cancelados
    contratos = Order.query.filter(Order.status.in_(['concluido', 'cancelado'])).order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/contratos.html', contratos=contratos)

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
            from services.token_service import TokenService
            TokenService.create_system_tokens(amount, description)
            
            flash(f'{amount} tokens criados com sucesso!', 'success')
            return redirect(url_for('admin.tokens'))
        except Exception as e:
            flash(f'Erro ao criar tokens: {str(e)}', 'error')
    
    return render_template('admin/criar_tokens.html')

# ==============================================================================
#  GESTÃO DE CONFIGURAÇÕES
# ==============================================================================

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@admin_required
def configuracoes():
    """Gerenciar configurações do sistema"""
    config = AdminService.get_system_config()
    form = SystemConfigForm(obj=config)
    
    if form.validate_on_submit():
        try:
            AdminService.update_system_config(form.data)
            flash('Configurações atualizadas com sucesso!', 'success')
            return redirect(url_for('admin.configuracoes'))
        except Exception as e:
            flash(f'Erro ao atualizar configurações: {str(e)}', 'error')
    
    return render_template('admin/configuracoes.html', form=form)

# ==============================================================================
#  GESTÃO DE CONTESTACÕES
# ==============================================================================

@admin_bp.route('/contestacoes')
@admin_required
def contestacoes():
    """Lista todas as contestações em aberto"""
    page = request.args.get('page', 1, type=int)
    disputes = Order.query.filter(Order.dispute_reason != None).order_by(desc(Order.dispute_opened_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/contestacoes.html', disputes=disputes)

@admin_bp.route('/contestacoes/<int:order_id>/analisar', methods=['GET', 'POST'])
@admin_required
def analisar_contestacao(order_id):
    """Analisar e resolver uma contestação"""
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        resolution = request.form.get('resolution', '').strip()
        
        if not resolution:
            flash('A resolução da contestação não pode ser vazia.', 'error')
            return render_template('admin/analisar_contestacao.html', order=order)
        
        try:
            from services.order_service import OrderService
            OrderService.resolve_dispute(order_id, resolution)
            flash('Contestação resolvida com sucesso!', 'success')
            return redirect(url_for('admin.contestacoes'))
        except Exception as e:
            flash(f'Erro ao resolver contestação: {str(e)}', 'error')
            
    return render_template('admin/analisar_contestacao.html', order=order)

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
    report_data = ReportService.generate_user_activity_report()
    
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



# Rota de contestações já definida na linha 319
