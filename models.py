#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

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
    
    client = db.relationship('User', foreign_keys=[client_id], backref='created_orders')
    provider = db.relationship('User', foreign_keys=[provider_id], backref='accepted_orders')
    transactions = db.relationship('Transaction', backref='order')

