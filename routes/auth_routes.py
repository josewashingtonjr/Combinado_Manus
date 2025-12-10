#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import User, AdminUser
from services.auth_service import login_required
from services.invite_service import InviteService
from datetime import datetime
import secrets

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
        
        # Inicializar timeout de sessão
        from services.session_timeout_manager import SessionTimeoutManager
        SessionTimeoutManager.initialize_session_timeout()
        
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
    
    # Inicializar timeout de sessão
    from services.session_timeout_manager import SessionTimeoutManager
    SessionTimeoutManager.initialize_session_timeout()
    
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
        
        # Inicializar timeout de sessão
        from services.session_timeout_manager import SessionTimeoutManager
        SessionTimeoutManager.initialize_session_timeout()
        
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
    
    # Inicializar timeout de sessão
    from services.session_timeout_manager import SessionTimeoutManager
    SessionTimeoutManager.initialize_session_timeout()
    
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
    # Invalidar sessão no sistema de timeout
    from services.session_timeout_manager import SessionTimeoutManager
    SessionTimeoutManager.invalidate_session()
    
    session.clear()
    return redirect(url_for('home.index'))

@auth_bp.route('/admin-logout')
def admin_logout():
    """Logout de administradores"""
    # Invalidar sessão no sistema de timeout
    from services.session_timeout_manager import SessionTimeoutManager
    SessionTimeoutManager.invalidate_session()
    
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
        
        # Verificar se o convite já foi aceito e tem pré-ordem
        if invite.status == 'convertido_pre_ordem' and invite.pre_order:
            flash('Este convite já foi aceito! Faça login para acessar a pré-ordem.', 'info')
            return redirect(url_for('auth.user_login'))
        
        # Verificar se o convite já foi aceito (aguardando aceitação mútua)
        if invite.status == 'aceito':
            flash('Este convite já foi aceito! Faça login para continuar.', 'info')
            return redirect(url_for('auth.user_login'))
        
        # Verificar se o convite pode ser acessado
        if invite.status not in ['pendente'] or invite.is_expired:
            if invite.status == 'recusado':
                flash('Este convite foi recusado.', 'error')
            elif invite.status == 'expirado' or invite.is_expired:
                flash('Este convite expirou.', 'error')
            elif invite.status == 'convertido':
                flash('Este convite já foi convertido em ordem de serviço.', 'info')
            else:
                flash('Este convite não está mais disponível.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Sempre mostrar a página de convite com opções de cadastro e login
        # Qualquer prestador pode responder ao convite, não apenas o telefone específico
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
        
        # Verificar se o usuário aceitou o convite na sessão
        if session.get('invite_accepted') != token:
            flash('Você precisa aceitar o convite primeiro.', 'warning')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Obter dados do formulário
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        cpf = request.form.get('cpf', '').strip()
        phone = request.form.get('phone', '').strip()
        terms = request.form.get('terms') == 'on'
        
        # Validações
        if not nome or not email or not password or not cpf:
            flash('Nome, email, senha e CPF são obrigatórios.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        if not terms:
            flash('Você deve aceitar os termos de uso.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        # Verificar se já existe usuário com este email, telefone ou CPF
        existing_user = User.query.filter(
            (User.email == email) | (User.phone == phone) | (User.cpf == cpf)
        ).first()
        
        if existing_user:
            flash('Já existe uma conta com este email, telefone ou CPF.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        # Criar novo usuário
        from models import db
        user = User(
            nome=nome,
            email=email,  # Email fornecido no cadastro
            cpf=cpf,
            phone=phone,  # Telefone fornecido no cadastro (pode ser diferente do convite)
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
        session['active_role'] = 'prestador'  # Definir papel ativo como prestador
        
        # Inicializar timeout de sessão
        from services.session_timeout_manager import SessionTimeoutManager
        SessionTimeoutManager.initialize_session_timeout()
        
        # Armazenar token do convite na sessão para permitir acesso
        session['invite_token'] = token
        
        # Limpar dados de aceitação do convite da sessão
        session.pop('invite_accepted', None)
        session.pop('invite_acceptance_time', None)
        
        flash(f'Conta criada com sucesso! Bem-vindo, {nome}!', 'success')
        
        # Redirecionar para ver o convite
        return redirect(url_for('prestador.ver_convite', token=token))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao criar conta: {str(e)}', 'error')
        return redirect(url_for('auth.convite_login_cadastro', token=token))

@auth_bp.route('/convite/<token>/login', methods=['POST'])
def processar_login_convite(token):
    """Processar login de usuário existente via convite"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Verificar se o usuário aceitou o convite na sessão
        if session.get('invite_accepted') != token:
            flash('Você precisa aceitar o convite primeiro.', 'warning')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Obter dados do formulário
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validações
        if not email or not password:
            flash('Email e senha são obrigatórios.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        # Buscar usuário pelo email fornecido
        user = User.query.filter_by(email=email, active=True).first()
        
        # Verificar se o usuário existe e a senha está correta
        if not user or not user.check_password(password):
            flash('Email ou senha incorretos.', 'error')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        # Verificar se o usuário tem o papel de prestador
        user_roles = user.roles.split(',') if user.roles else []
        if 'prestador' not in user_roles:
            flash('Apenas prestadores podem responder a convites. Entre em contato com o suporte para ativar seu perfil de prestador.', 'warning')
            return redirect(url_for('auth.convite_login_cadastro', token=token))
        
        # Fazer login
        session['user_id'] = user.id
        session['user_role'] = user.roles
        session['active_role'] = 'prestador'  # Definir papel ativo como prestador
        
        # Inicializar timeout de sessão
        from services.session_timeout_manager import SessionTimeoutManager
        SessionTimeoutManager.initialize_session_timeout()
        
        # Armazenar token do convite na sessão para permitir acesso
        session['invite_token'] = token
        
        # Limpar dados de aceitação do convite da sessão
        session.pop('invite_accepted', None)
        session.pop('invite_acceptance_time', None)
        
        flash(f'Login realizado com sucesso! Bem-vindo, {user.nome}!', 'success')
        
        # Redirecionar para ver o convite
        return redirect(url_for('prestador.ver_convite', token=token))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao fazer login: {str(e)}', 'error')
        return redirect(url_for('auth.convite_login_cadastro', token=token))

@auth_bp.route('/convite/<token>/aceitar-inicial', methods=['POST'])
def aceitar_convite_inicial(token):
    """Aceitar convite inicialmente e redirecionar para login/cadastro"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Armazenar na sessão que o usuário aceitou o convite
        session['invite_accepted'] = token
        session['invite_acceptance_time'] = datetime.now().isoformat()
        
        flash('Convite aceito! Agora complete seu cadastro ou faça login para prosseguir.', 'success')
        
        # Redirecionar para página de login/cadastro com contexto do convite
        return redirect(url_for('auth.convite_login_cadastro', token=token))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao aceitar convite: {str(e)}', 'error')
        return redirect(url_for('auth.convite_acesso', token=token))

@auth_bp.route('/convite/<token>/login-cadastro')
def convite_login_cadastro(token):
    """Página de login/cadastro após aceitar o convite"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Verificar se o usuário aceitou o convite na sessão
        if session.get('invite_accepted') != token:
            flash('Você precisa aceitar o convite primeiro.', 'warning')
            return redirect(url_for('auth.convite_acesso', token=token))
        
        # Verificar se a aceitação não expirou (30 minutos)
        acceptance_time_str = session.get('invite_acceptance_time')
        if acceptance_time_str:
            from datetime import datetime, timedelta
            acceptance_time = datetime.fromisoformat(acceptance_time_str)
            if datetime.now() - acceptance_time > timedelta(minutes=30):
                session.pop('invite_accepted', None)
                session.pop('invite_acceptance_time', None)
                flash('Sua aceitação expirou. Aceite o convite novamente.', 'warning')
                return redirect(url_for('auth.convite_acesso', token=token))
        
        return render_template('auth/convite_login_cadastro.html', 
                             invite=invite, 
                             token=token)
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash('Erro ao processar convite. Tente novamente.', 'error')
        return redirect(url_for('auth.user_login'))

@auth_bp.route('/convite/<token>/rejeitar', methods=['POST'])
def rejeitar_convite(token):
    """Rejeitar um convite sem necessidade de login"""
    try:
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        if invite.status != 'pendente' or invite.is_expired:
            flash('Este convite não está mais disponível ou expirou.', 'error')
            return redirect(url_for('auth.user_login'))
        
        # Obter motivo da rejeição (opcional)
        reason = request.form.get('reason', '').strip()
        
        # Rejeitar o convite (sem provider_id para rejeição anônima)
        InviteService.reject_invite(invite, reason=reason)
        
        flash('Convite rejeitado com sucesso. O cliente foi notificado e poderá enviar para outro prestador.', 'info')
        
        # Redirecionar para página inicial
        return redirect(url_for('home.index'))
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash(f'Erro ao rejeitar convite: {str(e)}', 'error')
        return redirect(url_for('auth.convite_acesso', token=token))


@auth_bp.route('/convite/<token>/debug')
def debug_convite(token):
    """Página de debug para convites"""
    try:
        from services.invite_service import InviteService
        
        # Verificar se o convite existe e é válido
        invite = InviteService.get_invite_by_token(token)
        
        return render_template('debug_invite.html', 
                             invite=invite, 
                             token=token)
        
    except ValueError as e:
        flash('Convite não encontrado ou inválido.', 'error')
        return redirect(url_for('auth.user_login'))
    except Exception as e:
        flash('Erro ao processar convite. Tente novamente.', 'error')
        return redirect(url_for('auth.user_login'))


@auth_bp.route('/convite/<token>/propor-alteracao', methods=['POST'])
def propor_alteracao_convite(token):
    """
    DEPRECATED: Rota removida conforme otimização mobile.
    
    A negociação de termos agora acontece na pré-ordem após aceitação mútua.
    Esta rota agora apenas informa o usuário sobre o novo fluxo.
    
    Novo fluxo simplificado:
    1. Aceite o convite
    2. Uma pré-ordem será criada automaticamente
    3. Negocie os termos na tela de pré-ordem
    
    Requirements: Otimização Mobile - Requirement 1 (Simplificação da Interface de Convites)
    """
    flash(
        'A negociação de valores foi simplificada! '
        'Aceite o convite primeiro e depois você poderá negociar os termos na pré-ordem.',
        'info'
    )
    return redirect(url_for('auth.convite_acesso', token=token))
