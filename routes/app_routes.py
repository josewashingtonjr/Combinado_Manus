#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, redirect, url_for, session
from services.auth_service import login_required, user_loader_required
from models import User

# Criar blueprint para área do app (cliente logado)
app_bp = Blueprint("app", __name__, url_prefix="/app")

@app_bp.route("/home")
@user_loader_required
def home(user):
    """Página inicial do cliente logado"""
    # Verificar se usuário tem papel de cliente
    # Verificar se usuário tem papel de cliente
    user_roles = user.roles.split(",") # user object already loaded by decorator
    if "cliente" not in user_roles:
        return redirect(url_for("prestador.dashboard"))
    
    from services.cliente_service import ClienteService # Importar ClienteService
    data = ClienteService.get_dashboard_data(user.id) # Obter dados do dashboard
    return render_template("cliente/dashboard.html", user=user, data=data)

@app_bp.route("/carteira")
@user_loader_required
def carteira(user):
    """Página da carteira do cliente"""

    return render_template("cliente/carteira.html", user=user)

@app_bp.route("/historico")
@user_loader_required
def historico(user):
    """Página de histórico do cliente"""

    return render_template("cliente/historico.html", user=user)

@app_bp.route("/perfil")
@user_loader_required
def perfil(user):
    """Página de perfil do cliente"""

    return render_template("cliente/perfil.html", user=user)

@app_bp.route("/switch-role/<role>")
@user_loader_required
def switch_role(user, role):
    """Alternar entre papéis disponíveis para usuários duais"""
    from flask import flash
    from services.role_service import RoleService
    
    # Verificar se usuário pode alternar para o papel solicitado
    if RoleService.set_active_role(role):
        flash(f"Papel alterado para {role.title()}", "success")
        
        # Redirecionar para dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(role)
        return redirect(url_for(dashboard_url))
    else:
        flash("Papel não disponível para seu usuário", "error")
        return redirect(url_for("home.index"))

@app_bp.route("/toggle-role")
@user_loader_required
def toggle_role(user):
    """Alternar automaticamente entre papéis disponíveis"""
    from flask import flash
    from services.role_service import RoleService
    
    if RoleService.switch_role():
        active_role = RoleService.get_active_role()
        flash(f"Papel alterado para {active_role.title()}", "success")
        
        # Redirecionar para dashboard apropriado
        dashboard_url = RoleService.get_role_dashboard_url(active_role)
        return redirect(url_for(dashboard_url))
    else:
        flash("Não há outros papéis disponíveis para alternar", "info")
        return redirect(url_for("home.index"))
