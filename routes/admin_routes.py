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
            user = AdminService.create_user(
                nome=form.nome.data,
                email=form.email.data,
                cpf=form.cpf.data,
                phone=form.phone.data,
                password=form.password.data,
                roles=form.roles.data
            )
            flash(f'Usuário {user.nome} criado com sucesso!', 'success')
            return redirect(url_for('admin.usuarios'))
        except Exception as e:
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
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
                flash('Quantidade deve ser maior que zero', 'error')
                return redirect(url_for('admin.criar_tokens'))
            
            result = AdminService.create_tokens(amount, description)
            flash(f'Criados {amount:,.0f} tokens com sucesso! Novo saldo admin: {result["new_admin_balance"]:,.0f} tokens', 'success')
            return redirect(url_for('admin.tokens'))
        except Exception as e:
            flash(f'Erro ao criar tokens: {str(e)}', 'error')
    
    return render_template('admin/criar_tokens.html')

@admin_bp.route('/tokens/integridade')
@admin_required
def verificar_integridade():
    """Verificar integridade do sistema de tokens"""
    try:
        integrity_check = AdminService.validate_system_integrity()
        return render_template('admin/integridade_tokens.html', integrity_check=integrity_check)
    except Exception as e:
        flash(f'Erro ao verificar integridade: {str(e)}', 'error')
        return redirect(url_for('admin.tokens'))

@admin_bp.route('/tokens/alertas')
@admin_required
def alertas_tokens():
    """Ver alertas de atividade suspeita"""
    try:
        alerts = AdminService.get_suspicious_activity_alerts()
        return render_template('admin/alertas_tokens.html', alerts=alerts)
    except Exception as e:
        flash(f'Erro ao carregar alertas: {str(e)}', 'error')
        return redirect(url_for('admin.tokens'))

@admin_bp.route('/tokens/transferir-para-admin', methods=['GET', 'POST'])
@admin_required
def transferir_para_admin():
    """Transferir tokens para o admin principal (ID 0)"""
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', 'Transferência para admin principal')
            
            if amount <= 0:
                flash('Quantidade deve ser maior que zero', 'error')
                return render_template('admin/transferir_para_admin.html')
            
            # Obter admin atual da sessão
            from services.auth_service import AuthService
            current_admin = AuthService.get_current_admin()
            
            if not current_admin:
                flash('Erro: Administrador não encontrado.', 'error')
                return redirect(url_for('auth.admin_login'))
            
            # Verificar se não é o próprio admin principal tentando transferir para si mesmo
            if current_admin.id == 0:
                flash('Admin principal não pode transferir tokens para si mesmo.', 'error')
                return render_template('admin/transferir_para_admin.html')
            
            # Verificar se admin atual tem carteira e saldo suficiente
            from services.wallet_service import WalletService
            current_admin_wallet = WalletService.get_wallet_info(current_admin.id)
            
            if not current_admin_wallet or current_admin_wallet['balance'] < amount:
                flash(f'Saldo insuficiente. Saldo atual: {current_admin_wallet["balance"] if current_admin_wallet else 0:,.0f} tokens', 'error')
                return render_template('admin/transferir_para_admin.html')
            
            # Realizar transferência: admin atual -> admin principal (ID 0)
            result = WalletService.transfer_tokens_between_users(
                from_user_id=current_admin.id,
                to_user_id=0,  # Admin principal
                amount=amount,
                description=description
            )
            
            flash(f'Transferidos {amount:,.0f} tokens para o admin principal com sucesso!', 'success')
            return redirect(url_for('admin.tokens'))
            
        except Exception as e:
            flash(f'Erro ao transferir tokens: {str(e)}', 'error')
    
    # GET - mostrar formulário
    try:
        from services.auth_service import AuthService
        from services.wallet_service import WalletService
        
        current_admin = AuthService.get_current_admin()
        if current_admin and current_admin.id != 0:
            current_admin_wallet = WalletService.get_wallet_info(current_admin.id)
            admin_principal_wallet = WalletService.get_admin_wallet_info()
            
            return render_template('admin/transferir_para_admin.html', 
                                 current_admin=current_admin,
                                 current_admin_wallet=current_admin_wallet,
                                 admin_principal_wallet=admin_principal_wallet)
        else:
            flash('Admin principal não precisa transferir tokens para si mesmo.', 'info')
            return redirect(url_for('admin.tokens'))
    except Exception as e:
        flash(f'Erro ao carregar dados: {str(e)}', 'error')
        return redirect(url_for('admin.tokens'))

# ==============================================================================
#  CONFIGURAÇÕES DO SISTEMA
# ==============================================================================

@admin_bp.route('/configuracoes', methods=['GET'])
@admin_required
def configuracoes():
    """Configurações do sistema"""
    try:
        # Carregar configurações atuais
        config = AdminService.get_system_config()
        return render_template('admin/configuracoes.html', config=config)
    except Exception as e:
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return render_template('admin/configuracoes.html', config={})

# ==============================================================================
#  RELATÓRIOS E AUDITORIA
# ==============================================================================

@admin_bp.route('/relatorios')
@admin_required
def relatorios():
    """Relatórios e auditoria do sistema"""
    try:
        # Obter estatísticas para os cards
        stats = AdminService.get_dashboard_stats()
        return render_template('admin/relatorios.html', stats=stats)
    except Exception as e:
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
        return render_template('admin/relatorios.html', stats=None)

@admin_bp.route('/logs')
@admin_required
def logs():
    """Logs de auditoria do sistema"""
    page = request.args.get('page', 1, type=int)
    # Implementar quando tivermos o modelo de logs
    return render_template('admin/logs.html')

# ==============================================================================
#  GESTÃO DE CONTESTAÇÕES
# ==============================================================================

@admin_bp.route('/contestacoes')
@admin_required
def contestacoes():
    """Lista todas as contestações de contratos com dados reais"""
    try:
        status_filter = request.args.get('status', '')
        
        # Buscar contestações reais do sistema
        from services.admin_service import AdminService
        contestacoes = AdminService.get_contestacoes(status=status_filter)
        
        # Calcular estatísticas
        contestacoes_pendentes = len(contestacoes)  # Todas são pendentes (status 'disputada')
        
        stats = {
            'pendentes': contestacoes_pendentes,
            'em_analise': 0,
            'resolvidas': 0,
            'rejeitadas': 0
        }
        
        return render_template('admin/contestacoes.html', 
                             contestacoes=contestacoes,
                             contestacoes_pendentes=contestacoes_pendentes,
                             stats=stats)
                             
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger('app')
        logger.error(f"Erro ao carregar contestações: {str(e)}")
        
        # Retornar página com erro tratado
        flash('Erro ao carregar contestações. Verifique os logs do sistema.', 'error')
        return render_template('admin/contestacoes.html', 
                             contestacoes=[],
                             contestacoes_pendentes=0,
                             stats={'pendentes': 0, 'em_analise': 0, 'resolvidas': 0, 'rejeitadas': 0})

@admin_bp.route('/contestacoes/<int:contestacao_id>')
@admin_required
def analisar_contestacao(contestacao_id):
    """Analisar uma contestação específica com dados reais"""
    try:
        # Buscar detalhes reais da contestação
        from services.admin_service import AdminService
        contestacao_details = AdminService.get_contestacao_details(contestacao_id)
        
        if not contestacao_details:
            flash('Contestação não encontrada ou não está em disputa.', 'error')
            return redirect(url_for('admin.contestacoes'))
        
        return render_template('admin/analisar_contestacao.html', 
                             contestacao=contestacao_details)
                             
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger('app')
        logger.error(f"Erro ao analisar contestação {contestacao_id}: {str(e)}")
        
        # Mensagem de erro para o usuário
        flash('Erro interno do servidor ao carregar contestação. O erro foi registrado automaticamente nos logs para análise técnica.', 'error')
        return redirect(url_for('admin.contestacoes'))

@admin_bp.route('/contestacoes/<int:contestacao_id>/decidir', methods=['POST'])
@admin_required
def decidir_contestacao(contestacao_id):
    """Tomar decisão sobre uma contestação com processamento real"""
    try:
        # Obter dados do formulário
        decisao = request.form.get('decisao')
        justificativa = request.form.get('justificativa', '').strip()
        
        # Validações básicas
        if not decisao or decisao not in ['favor_cliente', 'favor_prestador']:
            flash('Decisão inválida. Selecione uma opção válida.', 'error')
            return redirect(url_for('admin.analisar_contestacao', contestacao_id=contestacao_id))
        
        if not justificativa:
            flash('Justificativa é obrigatória para resolver a contestação.', 'error')
            return redirect(url_for('admin.analisar_contestacao', contestacao_id=contestacao_id))
        
        # Obter admin atual
        admin_id = session.get('admin_id')
        if not admin_id:
            flash('Sessão expirada. Faça login novamente.', 'error')
            return redirect(url_for('auth.admin_login'))
        
        # Resolver contestação usando AdminService
        from services.admin_service import AdminService
        result = AdminService.resolve_contestacao(
            admin_id=admin_id,
            order_id=contestacao_id,
            decision=decisao,
            admin_notes=justificativa
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('admin.contestacoes'))
        else:
            flash(result['error'], 'error')
            return redirect(url_for('admin.analisar_contestacao', contestacao_id=contestacao_id))
            
    except Exception as e:
        # Log do erro
        import logging
        logger = logging.getLogger('app')
        logger.error(f"Erro ao decidir contestação {contestacao_id}: {str(e)}")
        
        # Mensagem de erro para o usuário
        flash('Erro interno do servidor ao processar decisão. O erro foi registrado automaticamente nos logs para análise técnica.', 'error')
        return redirect(url_for('admin.analisar_contestacao', contestacao_id=contestacao_id))

@admin_bp.route('/contestacoes/<int:contestacao_id>/marcar-em-analise', methods=['POST'])
@admin_required
def marcar_em_analise(contestacao_id):
    """Marcar contestação como em análise"""
    # TODO: Implementar
    # AdminService.marcar_contestacao_em_analise(contestacao_id)
    return {'ok': True}

# ==============================================================================
#  GESTÃO DE CONTRATOS/ORDENS
# ==============================================================================

@admin_bp.route('/contratos')
@admin_required
def contratos():
    """Lista todos os contratos/ordens do sistema"""
    try:
        # Obter filtros da URL
        status_filter = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        
        # Query base para ordens (que são os "contratos" do sistema)
        query = Order.query
        
        # Aplicar filtros se especificados
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(desc(Order.created_at))
        
        # Paginação
        orders = query.paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Estatísticas para cards
        stats = {
            'total': Order.query.count(),
            'disponivel': Order.query.filter_by(status='disponivel').count(),
            'aceita': Order.query.filter_by(status='aceita').count(),
            'em_andamento': Order.query.filter_by(status='em_andamento').count(),
            'concluida': Order.query.filter_by(status='concluida').count(),
            'cancelada': Order.query.filter_by(status='cancelada').count(),
            'disputada': Order.query.filter_by(status='disputada').count()
        }
        
        return render_template('admin/contratos.html', 
                             orders=orders, 
                             stats=stats,
                             status_filter=status_filter)
    except Exception as e:
        flash(f'Erro ao carregar contratos: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/contratos/ativos')
@admin_required
def contratos_ativos():
    """Lista contratos ativos (disponível, aceita, em_andamento)"""
    return redirect(url_for('admin.contratos', status='aceita,em_andamento'))

@admin_bp.route('/contratos/finalizados')
@admin_required
def contratos_finalizados():
    """Lista contratos finalizados"""
    return redirect(url_for('admin.contratos', status='concluida'))

@admin_bp.route('/contratos/<int:contrato_id>')
@admin_required
def ver_contrato(contrato_id):
    """Ver detalhes de um contrato"""
    try:
        order = Order.query.get_or_404(contrato_id)
        
        # Obter transações relacionadas a esta ordem
        transactions = Transaction.query.filter_by(order_id=contrato_id).order_by(desc(Transaction.created_at)).all()
        
        return render_template('admin/ver_contrato.html', 
                             order=order, 
                             transactions=transactions)
    except Exception as e:
        flash(f'Erro ao carregar contrato: {str(e)}', 'error')
        return redirect(url_for('admin.contratos'))

# ==============================================================================
#  SALVAR CONFIGURAÇÕES
# ==============================================================================

@admin_bp.route('/configuracoes/salvar', methods=['POST'])
@admin_required
def salvar_configuracoes():
    """Salvar configurações de taxas, multas, segurança, backup e monitoramento"""
    tipo = request.form.get('tipo')
    
    try:
        if tipo == 'taxas':
            config_data = {
                'taxa_transacao': request.form.get('taxa_transacao', type=float),
                'taxa_saque': request.form.get('taxa_saque', type=float),
                'taxa_deposito': request.form.get('taxa_deposito', type=float),
                'valor_minimo_saque': request.form.get('valor_minimo_saque', type=float),
                'valor_maximo_saque': request.form.get('valor_maximo_saque', type=float, default=50000.0)
            }
            AdminService.update_system_config(config_data)
            flash('Taxas atualizadas com sucesso!', 'success')
            
        elif tipo == 'multas':
            config_data = {
                'multa_cancelamento': request.form.get('multa_cancelamento', type=float),
                'multa_atraso': request.form.get('multa_atraso', type=float),
                'multa_atraso_maxima': request.form.get('multa_atraso_maxima', type=float),
                'multa_contestacao_indevida': request.form.get('multa_contestacao_indevida', type=float),
                'prazo_contestacao': request.form.get('prazo_contestacao', type=int)
            }
            AdminService.update_system_config(config_data)
            flash('Multas e penalidades atualizadas com sucesso!', 'success')
            
        elif tipo == 'seguranca':
            config_data = {
                'senha_tamanho_minimo': request.form.get('senha_tamanho_minimo', type=int),
                'max_tentativas_login': request.form.get('max_tentativas_login', type=int),
                'timeout_bloqueio_login': request.form.get('timeout_bloqueio_login', type=int),
                'timeout_sessao': request.form.get('timeout_sessao', type=int),
                'require_2fa': 'true' if request.form.get('require_2fa') else 'false'
            }
            AdminService.update_system_config(config_data)
            flash('Configurações de segurança atualizadas com sucesso!', 'success')
            
        elif tipo == 'backup':
            config_data = {
                'backup_automatico': 'true' if request.form.get('backup_automatico') else 'false',
                'backup_intervalo_horas': request.form.get('backup_intervalo_horas', type=int),
                'backup_retencao_dias': request.form.get('backup_retencao_dias', type=int),
                'backup_path': request.form.get('backup_path', type=str)
            }
            AdminService.update_system_config(config_data)
            flash('Configurações de backup atualizadas com sucesso!', 'success')
            
        elif tipo == 'monitoramento':
            config_data = {
                'monitoramento_integridade': 'true' if request.form.get('monitoramento_integridade') else 'false',
                'intervalo_verificacao_integridade': request.form.get('intervalo_verificacao_integridade', type=int),
                'alerta_saldo_baixo': request.form.get('alerta_saldo_baixo', type=float),
                'alerta_transacao_alto_valor': request.form.get('alerta_transacao_alto_valor', type=float)
            }
            AdminService.update_system_config(config_data)
            flash('Configurações de monitoramento atualizadas com sucesso!', 'success')
            
        else:
            flash('Tipo de configuração inválido!', 'error')
            
    except Exception as e:
        flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return redirect(url_for('admin.configuracoes'))

# ==============================================================================
#  NOVAS ROTAS PARA FUNCIONALIDADES AVANÇADAS
# ==============================================================================

@admin_bp.route('/backup/criar', methods=['POST'])
@admin_required
def criar_backup():
    """Criar backup manual do sistema"""
    try:
        backup_type = request.json.get('type', 'full')
        backup = AdminService.create_backup(backup_type)
        
        if backup and backup.status == 'completed':
            return {
                'success': True,
                'message': f'Backup {backup_type} criado com sucesso!',
                'backup_id': backup.id,
                'file_size': backup.file_size
            }
        elif backup and backup.status == 'failed':
            return {
                'success': False,
                'message': f'Falha ao criar backup: {backup.error_message}'
            }
        else:
            return {
                'success': False,
                'message': 'Erro desconhecido ao criar backup'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao criar backup: {str(e)}'
        }

@admin_bp.route('/sistema/verificar-integridade-manual', methods=['POST'])
@admin_required
def verificar_integridade_manual():
    """Verificar integridade do sistema manualmente"""
    try:
        integrity_check = AdminService.validate_system_integrity()
        
        return {
            'success': True,
            'integrity_check': integrity_check
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao verificar integridade: {str(e)}'
        }

@admin_bp.route('/sistema/saude', methods=['GET'])
@admin_required
def verificar_saude_sistema():
    """Verificar saúde geral do sistema"""
    try:
        health_status = AdminService.get_system_health()
        
        return {
            'success': True,
            'health': health_status
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao verificar saúde do sistema: {str(e)}'
        }

@admin_bp.route('/alertas')
@admin_required
def alertas_sistema():
    """Visualizar alertas do sistema"""
    try:
        alertas_nao_resolvidos = AdminService.get_system_alerts(resolved=False)
        alertas_resolvidos = AdminService.get_system_alerts(resolved=True)
        
        return render_template('admin/alertas_sistema.html', 
                             alertas_nao_resolvidos=alertas_nao_resolvidos,
                             alertas_resolvidos=alertas_resolvidos)
    except Exception as e:
        flash(f'Erro ao carregar alertas: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/alertas/<int:alert_id>/resolver', methods=['POST'])
@admin_required
def resolver_alerta(alert_id):
    """Marcar alerta como resolvido"""
    try:
        from services.config_service import MonitoringService
        admin_id = session.get('admin_id', 1)  # TODO: Obter ID do admin da sessão
        
        success = MonitoringService.resolve_alert(alert_id, admin_id)
        
        if success:
            flash('Alerta marcado como resolvido!', 'success')
        else:
            flash('Erro ao resolver alerta!', 'error')
            
    except Exception as e:
        flash(f'Erro ao resolver alerta: {str(e)}', 'error')
    
    return redirect(url_for('admin.alertas_sistema'))

@admin_bp.route('/backup/status')
@admin_required
def status_backup():
    """Obter status dos backups"""
    try:
        from services.config_service import BackupService
        status = BackupService.get_backup_status()
        return status
    except Exception as e:
        return {
            'error': str(e),
            'total_backups': 0,
            'backup_enabled': False
        }

@admin_bp.route('/seguranca/estatisticas')
@admin_required
def estatisticas_seguranca():
    """Obter estatísticas de segurança"""
    try:
        from services.config_service import SecurityService
        stats = SecurityService.get_security_stats()
        return stats
    except Exception as e:
        return {
            'error': str(e),
            'total_attempts_24h': 0,
            'failed_attempts_24h': 0
        }

# ==============================================================================
#  RELATÓRIOS FUNCIONAIS
# ==============================================================================

@admin_bp.route('/relatorios/contratos')
@admin_required
def relatorios_contratos():
    """Relatório de contratos com filtros"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status_filter = request.args.get('status', 'todos')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar relatório
        data = ReportService.get_contracts_report_data(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )
        
        return render_template('admin/relatorio_contratos.html', data=data)
    except Exception as e:
        flash(f'Erro ao gerar relatório de contratos: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/relatorios/usuarios')
@admin_required
def relatorios_usuarios():
    """Relatório de usuários com filtros"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        user_type = request.args.get('user_type', 'todos')
        status_filter = request.args.get('status', 'todos')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar relatório
        data = ReportService.get_users_report_data(
            start_date=start_date,
            end_date=end_date,
            user_type=user_type,
            status_filter=status_filter
        )
        
        return render_template('admin/relatorio_usuarios.html', data=data)
    except Exception as e:
        flash(f'Erro ao gerar relatório de usuários: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/relatorios/financeiro')
@admin_required
def relatorios_financeiro():
    """Relatório financeiro com filtros"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar relatório
        data = ReportService.get_financial_report_data(
            start_date=start_date,
            end_date=end_date
        )
        
        return render_template('admin/relatorio_financeiro.html', data=data)
    except Exception as e:
        flash(f'Erro ao gerar relatório financeiro: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/relatorios/convites')
@admin_required
def relatorios_convites():
    """Relatório de convites com filtros"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status_filter = request.args.get('status', 'todos')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar relatório
        data = ReportService.get_invites_report_data(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )
        
        return render_template('admin/relatorio_convites.html', data=data)
    except Exception as e:
        flash(f'Erro ao gerar relatório de convites: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

# ==============================================================================
#  EXPORTAÇÃO DE RELATÓRIOS
# ==============================================================================

@admin_bp.route('/export/contracts')
@admin_required
def export_contracts():
    """Exportar relatório de contratos"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status_filter = request.args.get('status', 'todos')
        format_type = request.args.get('format', 'excel')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar dados do relatório
        data = ReportService.get_contracts_report_data(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )
        
        # Exportar conforme formato solicitado
        if format_type == 'excel':
            file_data = ReportService.export_contracts_to_excel(data)
            response = make_response(file_data)
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename=relatorio_contratos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return response
        elif format_type == 'pdf':
            file_data = ReportService.export_contracts_to_pdf(data)
            response = make_response(file_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=relatorio_contratos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            return response
        else:
            flash('Formato de exportação inválido', 'error')
            return redirect(url_for('admin.relatorios'))
            
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/export/users')
@admin_required
def export_users():
    """Exportar relatório de usuários"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        user_type = request.args.get('user_type', 'todos')
        status_filter = request.args.get('status', 'todos')
        format_type = request.args.get('format', 'excel')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar dados do relatório
        data = ReportService.get_users_report_data(
            start_date=start_date,
            end_date=end_date,
            user_type=user_type,
            status_filter=status_filter
        )
        
        # Exportar conforme formato solicitado
        if format_type == 'excel':
            file_data = ReportService.export_users_to_excel(data)
            response = make_response(file_data)
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename=relatorio_usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            return response
        elif format_type == 'pdf':
            file_data = ReportService.export_users_to_pdf(data)
            response = make_response(file_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=relatorio_usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            return response
        else:
            flash('Formato de exportação inválido', 'error')
            return redirect(url_for('admin.relatorios'))
            
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/export/financial')
@admin_required
def export_financial():
    """Exportar relatório financeiro"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        format_type = request.args.get('format', 'excel')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar dados do relatório
        data = ReportService.get_financial_report_data(
            start_date=start_date,
            end_date=end_date
        )
        
        # Para relatório financeiro, vamos usar uma versão simplificada da exportação
        if format_type == 'excel':
            # Implementar exportação financeira para Excel (simplificada)
            flash('Exportação financeira para Excel em desenvolvimento', 'info')
            return redirect(url_for('admin.relatorios'))
        elif format_type == 'pdf':
            # Implementar exportação financeira para PDF (simplificada)
            flash('Exportação financeira para PDF em desenvolvimento', 'info')
            return redirect(url_for('admin.relatorios'))
        else:
            flash('Formato de exportação inválido', 'error')
            return redirect(url_for('admin.relatorios'))
            
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

@admin_bp.route('/export/invites')
@admin_required
def export_invites():
    """Exportar relatório de convites"""
    try:
        # Obter filtros da URL
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        status_filter = request.args.get('status', 'todos')
        format_type = request.args.get('format', 'excel')
        
        # Converter datas
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
        
        # Gerar dados do relatório
        data = ReportService.get_invites_report_data(
            start_date=start_date,
            end_date=end_date,
            status_filter=status_filter
        )
        
        # Para relatório de convites, vamos usar uma versão simplificada da exportação
        if format_type == 'excel':
            flash('Exportação de convites para Excel em desenvolvimento', 'info')
            return redirect(url_for('admin.relatorios'))
        elif format_type == 'pdf':
            flash('Exportação de convites para PDF em desenvolvimento', 'info')
            return redirect(url_for('admin.relatorios'))
        else:
            flash('Formato de exportação inválido', 'error')
            return redirect(url_for('admin.relatorios'))
            
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'error')
        return redirect(url_for('admin.relatorios'))

# ==============================================================================
#  SEÇÃO FINANCEIRA AVANÇADA (Nova Funcionalidade)
# ==============================================================================

@admin_bp.route('/financeiro/dashboard')
@admin_required
def financeiro_dashboard():
    """Dashboard financeiro completo"""
    try:
        # Obter estatísticas financeiras detalhadas
        stats = AdminService.get_dashboard_stats()
        
        # Dados específicos para dashboard financeiro
        from services.wallet_service import WalletService
        token_summary = WalletService.get_system_token_summary()
        
        # Receitas por período (últimos 6 meses)
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        receitas_mensais = []
        for i in range(6):
            mes_inicio = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            mes_fim = mes_inicio.replace(day=28) + timedelta(days=4)
            mes_fim = mes_fim - timedelta(days=mes_fim.day)
            
            receita_mes = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.type == 'taxa_sistema',
                Transaction.created_at >= mes_inicio,
                Transaction.created_at <= mes_fim
            ).scalar() or 0.0
            
            receitas_mensais.append({
                'mes': mes_inicio.strftime('%Y-%m'),
                'mes_nome': mes_inicio.strftime('%B %Y'),
                'receita': receita_mes
            })
        
        receitas_mensais.reverse()  # Ordem cronológica
        
        # Top usuários por volume de taxas geradas
        top_geradores_taxa = db.session.query(
            Transaction.related_user_id,
            User.nome,
            User.email,
            func.count(Transaction.id).label('transacoes_count'),
            func.sum(Transaction.amount).label('total_taxas')
        ).join(
            User, Transaction.related_user_id == User.id
        ).filter(
            Transaction.type == 'taxa_sistema'
        ).group_by(
            Transaction.related_user_id, User.nome, User.email
        ).order_by(
            desc('total_taxas')
        ).limit(10).all()
        
        # Previsão de receita (baseada na média dos últimos 3 meses)
        receita_3_meses = sum(r['receita'] for r in receitas_mensais[-3:])
        previsao_mensal = receita_3_meses / 3 if receita_3_meses > 0 else 0
        previsao_anual = previsao_mensal * 12
        
        financial_data = {
            'stats': stats,
            'token_summary': token_summary,
            'receitas_mensais': receitas_mensais,
            'top_geradores_taxa': top_geradores_taxa,
            'previsao_mensal': previsao_mensal,
            'previsao_anual': previsao_anual,
            'crescimento_mes': 0  # TODO: Calcular crescimento percentual
        }
        
        return render_template('admin/financeiro_dashboard.html', data=financial_data)
        
    except Exception as e:
        flash(f'Erro ao carregar dashboard financeiro: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/financeiro/receitas')
@admin_required
def financeiro_receitas():
    """Detalhamento de receitas e taxas"""
    try:
        # Filtros da URL
        periodo = request.args.get('periodo', '30')  # dias
        tipo_taxa = request.args.get('tipo', 'todas')
        
        # Calcular período
        from datetime import datetime, timedelta
        if periodo == '7':
            data_inicio = datetime.utcnow() - timedelta(days=7)
        elif periodo == '30':
            data_inicio = datetime.utcnow() - timedelta(days=30)
        elif periodo == '90':
            data_inicio = datetime.utcnow() - timedelta(days=90)
        else:
            data_inicio = datetime.utcnow() - timedelta(days=365)
        
        # Query base para transações de taxa
        query = Transaction.query.filter(
            Transaction.type == 'taxa_sistema',
            Transaction.created_at >= data_inicio
        )
        
        transacoes_taxa = query.order_by(desc(Transaction.created_at)).all()
        
        # Estatísticas do período
        total_receita = sum(t.amount for t in transacoes_taxa)
        total_transacoes = len(transacoes_taxa)
        taxa_media = total_receita / total_transacoes if total_transacoes > 0 else 0
        
        # Receita por dia
        receita_diaria = {}
        for transacao in transacoes_taxa:
            dia = transacao.created_at.strftime('%Y-%m-%d')
            if dia not in receita_diaria:
                receita_diaria[dia] = 0
            receita_diaria[dia] += transacao.amount
        
        receitas_data = {
            'transacoes': transacoes_taxa,
            'total_receita': total_receita,
            'total_transacoes': total_transacoes,
            'taxa_media': taxa_media,
            'receita_diaria': receita_diaria,
            'periodo': periodo,
            'data_inicio': data_inicio
        }
        
        return render_template('admin/financeiro_receitas.html', data=receitas_data)
        
    except Exception as e:
        flash(f'Erro ao carregar receitas: {str(e)}', 'error')
        return redirect(url_for('admin.financeiro_dashboard'))

@admin_bp.route('/financeiro/taxas', methods=['GET', 'POST'])
@admin_required
def financeiro_taxas():
    """Configuração de taxas do sistema"""
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            taxa_sistema = float(request.form.get('taxa_sistema', 5.0))
            taxa_saque = float(request.form.get('taxa_saque', 2.50))
            taxa_deposito = float(request.form.get('taxa_deposito', 0.0))
            valor_minimo_saque = float(request.form.get('valor_minimo_saque', 10.0))
            
            # Validações
            if not (0 <= taxa_sistema <= 50):
                flash('Taxa do sistema deve estar entre 0% e 50%', 'error')
                return redirect(url_for('admin.financeiro_taxas'))
            
            # Salvar configurações
            from services.config_service import ConfigService
            configs = {
                'taxa_sistema': taxa_sistema,
                'taxa_saque': taxa_saque,
                'taxa_deposito': taxa_deposito,
                'valor_minimo_saque': valor_minimo_saque
            }
            
            ConfigService.update_configs_batch(configs)
            flash('Configurações de taxas atualizadas com sucesso!', 'success')
            
        except Exception as e:
            flash(f'Erro ao salvar configurações: {str(e)}', 'error')
        
        return redirect(url_for('admin.financeiro_taxas'))
    
    # GET - Exibir formulário
    try:
        from services.config_service import ConfigService
        configs = {
            'taxa_sistema': ConfigService.get_config('taxa_sistema', 5.0),
            'taxa_saque': ConfigService.get_config('taxa_saque', 2.50),
            'taxa_deposito': ConfigService.get_config('taxa_deposito', 0.0),
            'valor_minimo_saque': ConfigService.get_config('valor_minimo_saque', 10.0)
        }
        
        return render_template('admin/financeiro_taxas.html', configs=configs)
        
    except Exception as e:
        flash(f'Erro ao carregar configurações: {str(e)}', 'error')
        return redirect(url_for('admin.financeiro_dashboard'))

@admin_bp.route('/financeiro/previsoes')
@admin_required
def financeiro_previsoes():
    """Previsões e análises financeiras"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Dados dos últimos 12 meses para análise
        meses_dados = []
        for i in range(12):
            mes_inicio = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            mes_fim = mes_inicio.replace(day=28) + timedelta(days=4)
            mes_fim = mes_fim - timedelta(days=mes_fim.day)
            
            # Receita do mês
            receita = db.session.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.type == 'taxa_sistema',
                Transaction.created_at >= mes_inicio,
                Transaction.created_at <= mes_fim
            ).scalar() or 0.0
            
            # Número de transações
            transacoes = Transaction.query.filter(
                Transaction.type == 'taxa_sistema',
                Transaction.created_at >= mes_inicio,
                Transaction.created_at <= mes_fim
            ).count()
            
            # Usuários ativos
            usuarios_ativos = db.session.query(
                func.count(func.distinct(Transaction.user_id))
            ).filter(
                Transaction.created_at >= mes_inicio,
                Transaction.created_at <= mes_fim
            ).scalar() or 0
            
            meses_dados.append({
                'mes': mes_inicio.strftime('%Y-%m'),
                'mes_nome': mes_inicio.strftime('%B %Y'),
                'receita': receita,
                'transacoes': transacoes,
                'usuarios_ativos': usuarios_ativos
            })
        
        meses_dados.reverse()  # Ordem cronológica
        
        # Cálculos de previsão
        receitas_recentes = [m['receita'] for m in meses_dados[-6:]]  # Últimos 6 meses
        media_mensal = sum(receitas_recentes) / len(receitas_recentes) if receitas_recentes else 0
        
        # Tendência (simples: comparar últimos 3 meses com 3 anteriores)
        ultimos_3 = sum(receitas_recentes[-3:]) / 3 if len(receitas_recentes) >= 3 else 0
        anteriores_3 = sum(receitas_recentes[-6:-3]) / 3 if len(receitas_recentes) >= 6 else 0
        crescimento = ((ultimos_3 - anteriores_3) / anteriores_3 * 100) if anteriores_3 > 0 else 0
        
        # Previsões
        previsao_proximo_mes = media_mensal * (1 + crescimento/100)
        previsao_trimestre = previsao_proximo_mes * 3
        previsao_ano = media_mensal * 12 * (1 + crescimento/100)
        
        previsoes_data = {
            'meses_dados': meses_dados,
            'media_mensal': media_mensal,
            'crescimento_percentual': crescimento,
            'previsao_proximo_mes': previsao_proximo_mes,
            'previsao_trimestre': previsao_trimestre,
            'previsao_ano': previsao_ano,
            'tendencia': 'crescimento' if crescimento > 0 else 'declinio' if crescimento < 0 else 'estavel'
        }
        
        return render_template('admin/financeiro_previsoes.html', data=previsoes_data)
        
    except Exception as e:
        flash(f'Erro ao gerar previsões: {str(e)}', 'error')
        return redirect(url_for('admin.financeiro_dashboard'))

@admin_bp.route('/financeiro/relatorios')
@admin_required
def financeiro_relatorios():
    """Relatórios financeiros detalhados"""
    try:
        # Relatório consolidado financeiro
        from datetime import datetime, timedelta
        
        # Período padrão: último mês
        data_inicio = datetime.utcnow().replace(day=1)
        data_fim = datetime.utcnow()
        
        # Filtros da URL
        if request.args.get('inicio'):
            data_inicio = datetime.strptime(request.args.get('inicio'), '%Y-%m-%d')
        if request.args.get('fim'):
            data_fim = datetime.strptime(request.args.get('fim'), '%Y-%m-%d')
        
        # Usar ReportService para dados financeiros
        financial_data = ReportService.get_financial_report_data(data_inicio, data_fim)
        
        # Dados adicionais específicos para admin
        from services.wallet_service import WalletService
        token_summary = WalletService.get_system_token_summary()
        
        # Análise de lucratividade
        receita_total = financial_data['receita_taxas']
        volume_total = financial_data['volume_total']
        margem_lucro = (receita_total / volume_total * 100) if volume_total > 0 else 0
        
        relatorio_data = {
            'financial_data': financial_data,
            'token_summary': token_summary,
            'margem_lucro': margem_lucro,
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim
            }
        }
        
        return render_template('admin/financeiro_relatorios.html', data=relatorio_data)
        
    except Exception as e:
        flash(f'Erro ao gerar relatórios: {str(e)}', 'error')
        return redirect(url_for('admin.financeiro_dashboard'))