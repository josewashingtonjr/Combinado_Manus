#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from models import AdminUser, User

class AuthService:
    """Serviço de autenticação e autorização"""
    
    @staticmethod
    def is_admin_logged_in():
        """Verifica se há um administrador logado"""
        return 'admin_id' in session
    
    @staticmethod
    def is_user_logged_in():
        """Verifica se há um usuário logado"""
        return 'user_id' in session
    
    @staticmethod
    def get_current_admin():
        """Retorna o administrador atual"""
        if AuthService.is_admin_logged_in():
            return AdminUser.query.get(session['admin_id'])
        return None
    
    @staticmethod
    def get_current_user():
        """Retorna o usuário atual"""
        if AuthService.is_user_logged_in():
            return User.query.get(session['user_id'])
        return None
    
    @staticmethod
    def admin_login(admin, remember=False):
        """Realiza login do administrador"""
        session['admin_id'] = admin.id
        session['admin_email'] = admin.email
        session['admin_papel'] = admin.papel
        # TODO: Implementar "lembrar-me" se necessário
    
    @staticmethod
    def user_login(user, remember=False):
        """Realiza login do usuário com inicialização de papéis duais"""
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_roles'] = user.roles
        
        # Inicializar contexto de papéis para usuários duais
        from services.role_service import RoleService
        RoleService.initialize_user_session(user.id)
        
        # TODO: Implementar "lembrar-me" se necessário
    
    @staticmethod
    def logout():
        """Realiza logout (admin ou usuário)"""
        session.clear()
    
    @staticmethod
    def authenticate_admin(email, password):
        """Autentica um administrador"""
        admin = AdminUser.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            return admin
        return None
    
    @staticmethod
    def authenticate_user(email, password):
        """Autentica um usuário"""
        user = User.query.filter_by(email=email, active=True).first()
        if user and user.check_password(password):
            return user
        return None

# ==============================================================================
#  DECORADORES DE AUTORIZAÇÃO
# ==============================================================================

def admin_required(f):
    """Decorador que exige login de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_admin_logged_in():
            flash('Acesso negado. Login administrativo necessário.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorador que exige login de usuário"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_user_logged_in():
            flash('Acesso negado. Login necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        return f(*args, **kwargs)
    return decorated_function

def user_loader_required(f):
    """Decorador que exige login de usuário e carrega o objeto User"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_user_logged_in():
            flash('Acesso negado. Login necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        user = AuthService.get_current_user()
        if not user:
            flash('Sessão de usuário inválida. Faça login novamente.', 'error')
            return redirect(url_for('auth.user_login'))
        return f(user=user, *args, **kwargs)
    return decorated_function

def cliente_required(f):
    """Decorador que exige usuário com papel de cliente"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_user_logged_in():
            flash('Acesso negado. Login necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        
        user = AuthService.get_current_user()
        if not user or 'cliente' not in user.roles:
            flash('Acesso negado. Papel de cliente necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        
        return f(*args, **kwargs)
    return decorated_function

def prestador_required(f):
    """Decorador que exige usuário com papel de prestador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_user_logged_in():
            flash('Acesso negado. Login necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        
        user = AuthService.get_current_user()
        if not user or 'prestador' not in user.roles:
            flash('Acesso negado. Papel de prestador necessário.', 'error')
            return redirect(url_for('auth.user_login'))
        
        return f(*args, **kwargs)
    return decorated_function
