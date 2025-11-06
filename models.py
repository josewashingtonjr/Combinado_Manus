#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum
import secrets
import string

class UserRole(enum.Enum):
    CLIENTE = "cliente"
    PRESTADOR = "prestador"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    roles = db.Column(db.String(50), nullable=False, default=UserRole.CLIENTE.value)
    
    # Campos para soft delete
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    deletion_reason = db.Column(db.Text, nullable=True)

    # Relacionamento para quem deletou o usuário
    deleted_by_admin = db.relationship('AdminUser', foreign_keys=[deleted_by], backref='deleted_users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_deleted(self):
        """Verifica se o usuário foi deletado (soft delete)"""
        return self.deleted_at is not None

    def soft_delete(self, deleted_by_admin_id, reason=None):
        """Marca o usuário como deletado sem remover do banco"""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_admin_id
        self.deletion_reason = reason
        self.active = False

    def restore(self):
        """Restaura um usuário deletado"""
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None
        self.active = True

    def __repr__(self):
        return f'<User {self.email}>'

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    papel = db.Column(db.String(50), nullable=False, default='admin') # ex: admin, super_admin
    
    # Campos para soft delete
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    deletion_reason = db.Column(db.Text, nullable=True)

    # Relacionamento para quem deletou o admin (auto-referência)
    deleted_by_admin = db.relationship('AdminUser', remote_side=[id], backref='deleted_admins')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_deleted(self):
        """Verifica se o admin foi deletado (soft delete)"""
        return self.deleted_at is not None

    def soft_delete(self, deleted_by_admin_id, reason=None):
        """Marca o admin como deletado sem remover do banco"""
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_admin_id
        self.deletion_reason = reason

    def restore(self):
        """Restaura um admin deletado"""
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None

    def __repr__(self):
        return f'<AdminUser {self.email}>'


# ==============================================================================
#  MODELOS DE DADOS FINANCEIROS
# ==============================================================================

class Wallet(db.Model):
    """Modelo de carteira para cada usuário"""
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    balance = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    escrow_balance = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('wallet', uselist=False, cascade="all, delete-orphan"))
    
    __table_args__ = (
        db.CheckConstraint('balance >= 0', name='check_balance_non_negative'),
        db.CheckConstraint('escrow_balance >= 0', name='check_escrow_balance_non_negative'),
    )

class Transaction(db.Model):
    """Modelo para registrar todas as transações"""
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # ex: 'deposito', 'saque', 'pagamento', 'recebimento', 'taxa'
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    def __init__(self, **kwargs):
        # Gerar transaction_id automaticamente se não fornecido
        if 'transaction_id' not in kwargs or not kwargs['transaction_id']:
            from services.transaction_id_generator import TransactionIdGenerator
            kwargs['transaction_id'] = TransactionIdGenerator.generate_unique_id()
        super(Transaction, self).__init__(**kwargs)
    
    __table_args__ = (
        db.CheckConstraint('amount != 0', name='check_transaction_amount_not_zero'),
    )

class Order(db.Model):
    """Modelo para ordens de serviço"""
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    value = db.Column(db.Numeric(18, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='disponivel') # disponivel, aceita, em_andamento, concluida, cancelada, disputada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=True)  # Relacionamento com convite
    
    # Campos para sistema de disputas/contestações
    dispute_reason = db.Column(db.Text, nullable=True)  # Motivo da disputa
    dispute_opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Quem abriu a disputa
    dispute_opened_at = db.Column(db.DateTime, nullable=True)  # Quando a disputa foi aberta
    dispute_resolved_at = db.Column(db.DateTime, nullable=True)  # Quando a disputa foi resolvida
    dispute_resolution = db.Column(db.Text, nullable=True)  # Decisão/resolução da disputa
    
    client = db.relationship('User', foreign_keys=[client_id], backref='created_orders')
    provider = db.relationship('User', foreign_keys=[provider_id], backref='accepted_orders')
    transactions = db.relationship('Transaction', backref='order')
    
    __table_args__ = (
        db.CheckConstraint('value > 0', name='check_order_value_positive'),
    )

class Invite(db.Model):
    """Modelo para convites de serviço"""
    __tablename__ = 'invites'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_email = db.Column(db.String(120), nullable=True)  # Mantido por compatibilidade
    invited_phone = db.Column(db.String(20), nullable=False)  # Campo principal para WhatsApp/Telegram
    service_title = db.Column(db.String(200), nullable=False)
    service_description = db.Column(db.Text, nullable=False)
    service_category = db.Column(db.String(100), nullable=True)  # Ex: pedreiro, encanador, eletricista
    original_value = db.Column(db.Numeric(10, 2), nullable=False)
    final_value = db.Column(db.Numeric(10, 2), nullable=True)
    delivery_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, aceito, recusado, expirado, convertido
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Relacionamentos
    client = db.relationship('User', foreign_keys=[client_id], backref='sent_invites')
    order = db.relationship('Order', backref=db.backref('invite', uselist=False), foreign_keys='Order.invite_id')
    
    def __init__(self, **kwargs):
        super(Invite, self).__init__(**kwargs)
        if not self.token:
            self.token = self.generate_token()
        if not self.status:
            self.status = 'pendente'
        # Definir expiração baseada na data do serviço se não foi especificada
        if not self.expires_at and self.delivery_date:
            self.expires_at = self.delivery_date
    
    @staticmethod
    def generate_token():
        """Gera um token único para o convite"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    @property
    def is_expired(self):
        """Verifica se o convite está expirado - expira na data do serviço"""
        return datetime.utcnow() > self.delivery_date
    
    @property
    def can_be_accepted(self):
        """Verifica se o convite pode ser aceito"""
        return self.status == 'pendente' and not self.is_expired
    
    @property
    def invite_link(self):
        """Gera o link do convite para ser enviado ao prestador"""
        from flask import url_for, request
        try:
            return url_for('auth.convite_acesso', token=self.token, _external=True)
        except:
            # Fallback se não estiver em contexto de request
            return f"/convite/{self.token}"
    
    def __repr__(self):
        return f'<Invite {self.id}: {self.service_title} para {self.invited_phone}>'


# ==============================================================================
#  MODELOS DE CONFIGURAÇÃO DO SISTEMA
# ==============================================================================

class SystemConfig(db.Model):
    """Modelo para configurações do sistema"""
    __tablename__ = 'system_configs'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='general')  # taxas, multas, seguranca, backup
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemConfig {self.key}: {self.value}>'

class SystemBackup(db.Model):
    """Modelo para controle de backups do sistema"""
    __tablename__ = 'system_backups'
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(50), nullable=False)  # full, incremental, wallets, transactions
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='completed')  # running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<SystemBackup {self.backup_type} - {self.status}>'

class LoginAttempt(db.Model):
    """Modelo para controle de tentativas de login"""
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 support
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=False)
    attempt_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_type = db.Column(db.String(20), nullable=False, default='user')  # user, admin
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} - {"Success" if self.success else "Failed"}>'

class SystemAlert(db.Model):
    """Modelo para alertas do sistema"""
    __tablename__ = 'system_alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # integrity_check, backup_failed, suspicious_activity
    severity = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text, nullable=True)  # JSON data for additional context
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    
    resolver = db.relationship('AdminUser', backref='resolved_alerts')
    
    def __repr__(self):
        return f'<SystemAlert {self.alert_type} - {self.severity}>'

class TokenRequest(db.Model):
    """Modelo para solicitações de tokens"""
    __tablename__ = 'token_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Campos para comprovante de depósito
    payment_method = db.Column(db.String(50), nullable=True, default='pix')  # pix, ted, doc, cartao
    receipt_filename = db.Column(db.String(255), nullable=True)  # Nome do arquivo do comprovante
    receipt_original_name = db.Column(db.String(255), nullable=True)  # Nome original do arquivo
    receipt_uploaded_at = db.Column(db.DateTime, nullable=True)  # Quando foi enviado
    
    # Relacionamentos
    user = db.relationship('User', backref='token_requests')
    processor = db.relationship('AdminUser', backref='processed_token_requests')
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_token_request_amount_positive'),
    )
    
    def __repr__(self):
        return f'<TokenRequest {self.user_id} - R${self.amount} - {self.status}>'

class SessionTimeout(db.Model):
    """Modelo para controle de timeout de sessões"""
    __tablename__ = 'session_timeouts'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Relacionamentos
    user = db.relationship('User', backref='session_timeouts')
    admin = db.relationship('AdminUser', backref='session_timeouts')
    
    def __repr__(self):
        return f'<SessionTimeout {self.session_id} - Expires: {self.expires_at}>'

class OrderStatusHistory(db.Model):
    """Modelo para histórico de mudanças de status de ordens"""
    __tablename__ = 'order_status_history'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    previous_status = db.Column(db.String(50), nullable=False)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_by_admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Relacionamentos
    order = db.relationship('Order', backref='status_history')
    changed_by_user = db.relationship('User', foreign_keys=[changed_by_user_id])
    changed_by_admin = db.relationship('AdminUser', foreign_keys=[changed_by_admin_id])
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.order_id}: {self.previous_status} -> {self.new_status}>'

class TokenCreationLimit(db.Model):
    """Modelo para controle de limites de criação de tokens por administrador"""
    __tablename__ = 'token_creation_limits'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False, unique=True)
    daily_limit = db.Column(db.Numeric(18, 2), nullable=False, default=10000.00)
    monthly_limit = db.Column(db.Numeric(18, 2), nullable=False, default=100000.00)
    current_daily_used = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    current_monthly_used = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    last_daily_reset = db.Column(db.Date, default=datetime.utcnow().date)
    last_monthly_reset = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com AdminUser
    admin = db.relationship('AdminUser', backref=db.backref('token_creation_limit', uselist=False))
    
    __table_args__ = (
        db.CheckConstraint('daily_limit > 0', name='check_daily_limit_positive'),
        db.CheckConstraint('monthly_limit > 0', name='check_monthly_limit_positive'),
        db.CheckConstraint('current_daily_used >= 0', name='check_daily_used_non_negative'),
        db.CheckConstraint('current_monthly_used >= 0', name='check_monthly_used_non_negative'),
    )
    
    @property
    def daily_remaining(self):
        """Retorna o valor restante do limite diário"""
        return max(0, self.daily_limit - self.current_daily_used)
    
    @property
    def monthly_remaining(self):
        """Retorna o valor restante do limite mensal"""
        return max(0, self.monthly_limit - self.current_monthly_used)
    
    @property
    def is_daily_limit_exceeded(self):
        """Verifica se o limite diário foi excedido"""
        return self.current_daily_used >= self.daily_limit
    
    @property
    def is_monthly_limit_exceeded(self):
        """Verifica se o limite mensal foi excedido"""
        return self.current_monthly_used >= self.monthly_limit
    
    def can_create_tokens(self, amount):
        """Verifica se é possível criar a quantidade de tokens solicitada"""
        return (self.current_daily_used + amount <= self.daily_limit and 
                self.current_monthly_used + amount <= self.monthly_limit)
    
    def reset_daily_if_needed(self):
        """Reseta o contador diário se necessário"""
        today = datetime.utcnow().date()
        if self.last_daily_reset < today:
            self.current_daily_used = 0.00
            self.last_daily_reset = today
    
    def reset_monthly_if_needed(self):
        """Reseta o contador mensal se necessário"""
        today = datetime.utcnow().date()
        # Verifica se mudou o mês
        if (self.last_monthly_reset.year != today.year or 
            self.last_monthly_reset.month != today.month):
            self.current_monthly_used = 0.00
            self.last_monthly_reset = today
    
    def add_usage(self, amount):
        """Adiciona uso aos contadores diário e mensal"""
        self.reset_daily_if_needed()
        self.reset_monthly_if_needed()
        self.current_daily_used += amount
        self.current_monthly_used += amount
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<TokenCreationLimit Admin:{self.admin_id} Daily:{self.daily_limit} Monthly:{self.monthly_limit}>'

