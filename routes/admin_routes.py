#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from forms import CreateUserForm, EditUserForm, SystemConfigForm, AddTokensForm
from models import User, AdminUser, db
from services.admin_service import AdminService
from services.auth_service import admin_required
from sqlalchemy import desc

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
    form.user_id.choices = [(u.id, f'{u.nome} ({u.email})') for u in User.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        try:
            user = User.query.get(form.user_id.data)
            AdminService.add_tokens_to_user(user, form.amount.data, form.description.data)
            flash(f'Tokens adicionados com sucesso para {user.nome}!', 'success')
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
    return render_template('admin/relatorios.html')

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
    """Lista todas as contestações de contratos"""
    status_filter = request.args.get('status', '')
    tipo_filter = request.args.get('tipo', '')
    contrato_id = request.args.get('contrato_id', '')
    
    # TODO: Implementar filtros quando tivermos o modelo de Contestacao
    contestacoes = []  # AdminService.get_contestacoes(status=status_filter, tipo=tipo_filter)
    contestacoes_pendentes = 0  # len([c for c in contestacoes if c.status == 'pendente'])
    
    stats = {
        'pendentes': 0,
        'em_analise': 0,
        'resolvidas': 0,
        'rejeitadas': 0
    }
    
    return render_template('admin/contestacoes.html', 
                         contestacoes=contestacoes,
                         contestacoes_pendentes=contestacoes_pendentes,
                         stats=stats)

@admin_bp.route('/contestacoes/<int:contestacao_id>')
@admin_required
def analisar_contestacao(contestacao_id):
    """Analisar uma contestação específica"""
    # TODO: Buscar contestação do banco
    contestacao = {
        'id': contestacao_id,
        'contrato_id': 1,
        'usuario_nome': 'Cliente Teste',
        'usuario_tipo': 'cliente',
        'tipo': 'Serviço não entregue',
        'status': 'pendente',
        'motivo': 'O prestador não entregou o serviço no prazo acordado.',
        'valor': 150.00,
        'valor_contrato': 150.00,
        'cliente_nome': 'Cliente Teste',
        'prestador_nome': 'Prestador Teste',
        'created_at': None,
        'contrato_data': None,
        'prioridade': 'alta',
        'evidencias': [],
        'historico': []
    }
    
    return render_template('admin/analisar_contestacao.html', contestacao=contestacao)

@admin_bp.route('/contestacoes/<int:contestacao_id>/decidir', methods=['POST'])
@admin_required
def decidir_contestacao(contestacao_id):
    """Tomar decisão sobre uma contestação"""
    decisao = request.form.get('decisao')
    justificativa = request.form.get('justificativa')
    percentual_cliente = request.form.get('percentual_cliente', type=float)
    
    # TODO: Implementar lógica de decisão
    # AdminService.decidir_contestacao(contestacao_id, decisao, justificativa, percentual_cliente)
    
    flash('Decisão registrada com sucesso!', 'success')
    return redirect(url_for('admin.contestacoes'))

@admin_bp.route('/contestacoes/<int:contestacao_id>/marcar-em-analise', methods=['POST'])
@admin_required
def marcar_em_analise(contestacao_id):
    """Marcar contestação como em análise"""
    # TODO: Implementar
    # AdminService.marcar_contestacao_em_analise(contestacao_id)
    return {'ok': True}

@admin_bp.route('/contratos/<int:contrato_id>')
@admin_required
def ver_contrato(contrato_id):
    """Ver detalhes de um contrato"""
    # TODO: Implementar quando tivermos o modelo de Contrato
    flash('Funcionalidade em desenvolvimento', 'info')
    return redirect(url_for('admin.dashboard'))

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
