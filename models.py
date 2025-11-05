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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    papel = db.Column(db.String(50), nullable=False, default='admin') # ex: admin, super_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    balance = db.Column(db.Float, nullable=False, default=0.0)
    escrow_balance = db.Column(db.Float, nullable=False, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('wallet', uselist=False, cascade="all, delete-orphan"))

class Transaction(db.Model):
    """Modelo para registrar todas as transações"""
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # ex: 'deposito', 'saque', 'pagamento', 'recebimento', 'taxa'
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    related_user = db.relationship('User', foreign_keys=[related_user_id])

class Order(db.Model):
    """Modelo para ordens de serviço"""
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    value = db.Column(db.Float, nullable=False)
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

class Invite(db.Model):
    """Modelo para convites de serviço"""
    __tablename__ = 'invites'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_email = db.Column(db.String(120), nullable=True)  # Mantido por compatibilidade
    invited_phone = db.Column(db.String(20), nullable=True)  # Campo principal para WhatsApp/Telegram
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
    
    @staticmethod
    def generate_token():
        """Gera um token único para o convite"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    @property
    def is_expired(self):
        """Verifica se o convite está expirado"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def can_be_accepted(self):
        """Verifica se o convite pode ser aceito"""
        return self.status == 'pendente' and not self.is_expired
    
    def __repr__(self):
        return f'<Invite {self.id}: {self.service_title} para {self.invited_email}>'


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

