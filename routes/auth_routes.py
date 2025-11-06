#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, AdminUser
from services.auth_service import login_required
from services.invite_service import InviteService
import secrets
# CSRF removido para APIs AJAX

# Criar blueprint para autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/')
def index():
    """Página inicial de autenticação"""
    return render_template('auth/index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    """Login de usuários (clientes/prestadores)"""
    if request.method == 'GET':
        return render_template('auth/user_login_simple.html')
    
    # Processar login via AJAX
    if request.is_json:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        print(f"🔍 LOGIN ATTEMPT - Email: {email}, Password: {'*' * len(password)}")
        
        if not email or not password:
            print("❌ Campos vazios")
            return jsonify({
                'ok': False,
                'error': 'E-mail e senha são obrigatórios'
            }), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=email, active=True).first()
        print(f"🔍 Usuário encontrado: {user is not None}")
        
        if user:
            password_valid = user.check_password(password)
            print(f"🔍 Senha válida: {password_valid}")
            
            if not password_valid:
                print("❌ Senha incorreta")
                return jsonify({
                    'ok': False,
                    'error': 'E-mail ou senha incorretos'
                }), 401
        else:
            print("❌ Usuário não encontrado")
            return jsonify({
                'ok': False,
                'error': 'E-mail ou senha incorretos'
            }), 401
        
        # Gerar token de sessão
        token = secrets.token_urlsafe(32)
        session['user_id'] = user.id
        session['user_token'] = token
        session['user_role'] = user.roles
        
        # Determinar papel principal para redirecionamento
        roles = user.roles.split(',') if user.roles else []
        primary_role = roles[0] if roles else 'cliente'
        session['active_role'] = primary_role
        
        return jsonify({
            'ok': True,
            'token': token,
            'user': {
                'id': user.id,
                'name': user.nome,
                'email': user.email,
                'role': primary_role,
                'roles': roles
            }
        })
    
    # Fallback para form tradicional
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('E-mail e senha são obrigatórios', 'error')
        return render_template('auth/user_login_simple.html')
    
    user = User.query.filter_by(email=email, active=True).first()
    
    if not user or not user.check_password(password):
        flash('E-mail ou senha incorretos', 'error')
        return render_template('auth/user_login_simple.html')
    
    session['user_id'] = user.id
    session['user_role'] = user.roles
    
    # Redirecionamento baseado no papel
    roles = user.roles.split(',') if user.roles else []
    
    # Definir papel ativo inicial
    if 'cliente' in roles:
        session['active_role'] = 'cliente'
        return redirect(url_for('cliente.dashboard'))
    elif 'prestador' in roles:
        session['active_role'] = 'prestador'
        return redirect(url_for('prestador.dashboard'))
    else:
        session['active_role'] = 'cliente'  # Default
        return redirect(url_for('home.index'))

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Login de administradores"""
    if request.method == 'GET':
        return render_template('auth/admin_login.html')
    
    # Processar login via AJAX
    if request.is_json:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'ok': False,
                'error': 'E-mail e senha são obrigatórios'
            }), 400
        
        # Buscar administrador
        admin = AdminUser.query.filter_by(email=email).first()
        
        if not admin or not admin.check_password(password):
            return jsonify({
                'ok': False,
                'error': 'E-mail ou senha incorretos'
            }), 401
        
        # Gerar token de sessão
        token = secrets.token_urlsafe(32)
        session['admin_id'] = admin.id
        session['admin_token'] = token
        session['admin_role'] = admin.papel
        
        return jsonify({
            'ok': True,
            'token': token,
            'user': {
                'id': admin.id,
                'email': admin.email,
                'role': 'admin',
                'papel': admin.papel
            }
        })
    
    # Fallback para form tradicional
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('E-mail e senha são obrigatórios', 'error')
        return render_template('auth/admin_login.html')
    
    admin = AdminUser.query.filter_by(email=email).first()
    
    if not admin or not admin.check_password(password):
        flash('E-mail ou senha incorretos', 'error')
        return render_template('auth/admin_login.html')
    
    session['admin_id'] = admin.id
    session['admin_role'] = admin.papel
    
    return redirect(url_for('admin.dashboard'))

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registro de novos usuários via AJAX"""
    if not request.is_json:
        return jsonify({
            'ok': False,
            'error': 'Content-Type deve ser application/json'
        }), 400
    
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    terms = data.get('terms', False)
    
    # Validações
    if not name or not email or not password:
        return jsonify({
            'ok': False,
            'error': 'Todos os campos são obrigatórios'
        }), 400
    
    if len(password) < 8:
        return jsonify({
            'ok': False,
            'error': 'A senha deve ter pelo menos 8 caracteres'
        }), 400
    
    if not terms:
        return jsonify({
            'ok': False,
            'error': 'Você deve aceitar os termos de uso'
        }), 400
    
    # Verificar se usuário já existe
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            'ok': False,
            'error': 'Este e-mail já está cadastrado'
        }), 409
    
    # Criar novo usuário
    try:
        from models import db
        user = User(
            nome=name,
            email=email,
            cpf='',  # Será preenchido posteriormente
            phone='',
            roles='cliente,prestador',  # Papéis duais por padrão
            active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira para o usuário
        from services.wallet_service import WalletService
        WalletService.create_wallet_for_user(user)
        
        return jsonify({
            'ok': True,
            'message': 'Conta criada com sucesso! Faça login para continuar.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'ok': False,
            'error': 'Erro interno do servidor'
        }), 500

@auth_bp.route('/logout')
def logout():
    """Logout de usuários (clientes/prestadores)"""
    session.clear()
    return redirect(url_for('home.index'))

@auth_bp.route('/admin-logout')
def admin_logout():
    """Logout de administradores"""
    session.clear()
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/check-auth')
def check_auth():
    """Verificar status de autenticação via AJAX"""
    if 'admin_id' in session:
        return jsonify({
            'authenticated': True,
            'type': 'admin',
            'redirect': '/admin/dashboard'
        })
    elif 'user_id' in session:
        user_role = session.get('user_role', 'cliente')
        roles = user_role.split(',') if user_role else ['cliente']
        primary_role = roles[0]
        
        redirect_url = '/app/home' if primary_role == 'cliente' else '/prestador/dashboard'
        
        return jsonify({
            'authenticated': True,
            'type': 'user',
            'role': primary_role,
            'redirect': redirect_url
        })
    else:
        return jsonify({
            'authenticated': False
        })

# ==============================================================================
#  FLUXO DE CADASTRO VIA CONVITE
# ==============================================================================

@auth_bp.route('/convite/<token>')
def convite_acesso(token):
    """Página de acesso via token de convite"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se o convite pode ser acessado
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Verificar se já existe um usuário com este telefone
        existing_user = User.query.filter_by(phone=invite.invited_phone).first()
        
        if existing_user:
            # Usuário já existe, redirecionar para login
            flash(f'Você já tem uma conta. Faça login para ver o convite.', 'info')
            session['invite_token'] = token  # Salvar token para após o login
            return redirect(url_for('auth.user_login'))
        else:
            # Usuário não existe, mostrar página de cadastro
            return render_template('auth/convite_cadastro.html', 
                                 invite=invite, 
                                 token=token)
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash('Erro ao processar convite. Tente novamente.', 'error')
        return redirect(url_for('auth.user_login'))

@auth_bp.route('/convite/<token>/cadastrar', methods=['POST'])
def processar_cadastro_convite(token):
    """Processar cadastro de usuário via convite"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Obter dados do formulário
        nome = request.form.get('nome', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        cpf = request.form.get('cpf', '').strip()
        phone = request.form.get('phone', '').strip()
        terms = request.form.get('terms') == 'on'
        
        # Validações
        if not nome or not password or not cpf:
            flash('Nome, senha e CPF são obrigatórios.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        if not terms:
            flash('Você deve aceitar os termos de uso.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Verificar se já existe usuário com este telefone ou CPF
        existing_user = User.query.filter(
            (User.phone == invite.invited_phone) | (User.cpf == cpf)
        ).first()
        
        if existing_user:
            flash('Já existe uma conta com este telefone ou CPF.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Criar novo usuário
        from models import db
        user = User(
            nome=nome,
            email=email,  # Email fornecido no cadastro
            cpf=cpf,
            phone=invite.invited_phone,  # Telefone do convite
            roles='cliente,prestador',  # Papéis duais por padrão
            active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira para o usuário
        from services.wallet_service import WalletService
        WalletService.create_wallet_for_user(user)
        
        # Fazer login automático
        session['user_id'] = user.id
        session['user_role'] = user.roles
        session['invite_token'] = token  # Manter token para redirecionamento
        
        flash(f'Conta criada com sucesso! Bem-vindo, {nome}!', 'success')
        
        # Redirecionar para ver o convite
        return redirect(url_for('prestador.ver_convite', token=token))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao criar conta: {str(e)}', 'error')
        return redirect(url_for('auth.convite_acesso', token=token))

@auth_bp.route('/convite/<token>/login', methods=['POST'])
def processar_login_convite(token):
    """Processar login de usuário existente via convite"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Obter dados do formulário
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validações
        if not email or not password:
            flash('Email e senha são obrigatórios.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Verificar se o email corresponde ao convite
        if email != invite.invited_email:
            flash('Este convite foi enviado para outro email.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Buscar usuário
        user = User.query.filter_by(email=email, active=True).first()
        
        if not user or not user.check_password(password):
            flash('Email ou senha incorretos.', 'error')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Fazer login
        session['user_id'] = user.id
        session['user_role'] = user.roles
        session['invite_token'] = token
        
        flash(f'Login realizado com sucesso! Bem-vindo, {user.nome}!', 'success')
        
        # Redirecionar para ver o convite
        return redirect(url_for('prestador.ver_convite', token=token))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao fazer login: {str(e)}', 'error')
        return redirect(url_for('auth.convite_acesso', token=token))
