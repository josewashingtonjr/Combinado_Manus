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
    users = User.query.filter_by(active=True).all()
    return render_template('admin/tokens.html', users=users)

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

# ==============================================================================
#  CONFIGURAÇÕES DO SISTEMA
# ==============================================================================

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@admin_required
def configuracoes():
    """Configurações do sistema"""
    form = SystemConfigForm()
    
    if form.validate_on_submit():
        try:
            AdminService.update_system_config(form.data)
            flash('Configurações atualizadas com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao atualizar configurações: {str(e)}', 'error')
    else:
        # Carregar configurações atuais
        config = AdminService.get_system_config()
        if config:
            form.taxa_sistema.data = config.get('taxa_sistema', 5.0)
            form.valor_token.data = config.get('valor_token', 1.0)
            form.sistema_ativo.data = config.get('sistema_ativo', True)
            form.manutencao.data = config.get('manutencao', False)
            form.observacoes.data = config.get('observacoes', '')
    
    return render_template('admin/configuracoes.html', form=form)

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
