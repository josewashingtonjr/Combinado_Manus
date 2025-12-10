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
    """Modelo para ordens de serviço com sistema completo de gestão"""
    __tablename__ = 'orders'
    
    # Campos básicos
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    value = db.Column(db.Numeric(18, 2), nullable=False)
    
    # Status: aguardando_execucao, servico_executado, concluida, cancelada, contestada, resolvida
    status = db.Column(db.String(50), nullable=False, default='aguardando_execucao')
    
    # Datas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)  # Quando prestador marcou como concluído
    confirmed_at = db.Column(db.DateTime, nullable=True)  # Quando cliente confirmou
    service_deadline = db.Column(db.DateTime, nullable=False)  # Data de entrega do serviço
    confirmation_deadline = db.Column(db.DateTime, nullable=True)  # Prazo para cliente confirmar
    dispute_deadline = db.Column(db.DateTime, nullable=True)  # Prazo para contestar
    
    # Relacionamento com convite
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=True)
    
    # Campos de cancelamento
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    cancellation_fee = db.Column(db.Numeric(10, 2), nullable=True)
    cancellation_fee_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # % aplicada
    
    # Campos de contestação/disputa
    dispute_reason = db.Column(db.Text, nullable=True)
    dispute_opened_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    dispute_opened_at = db.Column(db.DateTime, nullable=True)
    dispute_resolved_at = db.Column(db.DateTime, nullable=True)
    dispute_resolution = db.Column(db.Text, nullable=True)
    dispute_evidence = db.Column(db.JSON, nullable=True)  # Array de URLs de provas
    dispute_client_statement = db.Column(db.Text, nullable=True)
    dispute_provider_response = db.Column(db.Text, nullable=True)
    dispute_admin_notes = db.Column(db.Text, nullable=True)
    dispute_winner = db.Column(db.String(20), nullable=True)  # 'client' ou 'provider'
    
    # Campos de taxas
    platform_fee = db.Column(db.Numeric(10, 2), nullable=True)  # Taxa da plataforma
    platform_fee_percentage = db.Column(db.Numeric(5, 2), nullable=True)  # % da taxa
    contestation_fee = db.Column(db.Numeric(10, 2), nullable=True)  # Taxa de contestação
    
    # Campos de configuração - taxas vigentes na criação da ordem
    platform_fee_percentage_at_creation = db.Column(db.Numeric(5, 2), nullable=True)
    contestation_fee_at_creation = db.Column(db.Numeric(10, 2), nullable=True)
    cancellation_fee_percentage_at_creation = db.Column(db.Numeric(5, 2), nullable=True)
    
    # Campo para confirmação automática
    auto_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    
    # Campo para URLs de provas de contestação
    dispute_evidence_urls = db.Column(db.JSON, nullable=True)  # Array de URLs de arquivos
    
    # Relacionamentos
    client = db.relationship('User', foreign_keys=[client_id], backref='created_orders')
    provider = db.relationship('User', foreign_keys=[provider_id], backref='accepted_orders')
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by], backref='cancelled_orders')
    dispute_opener = db.relationship('User', foreign_keys=[dispute_opened_by], backref='opened_disputes')
    transactions = db.relationship('Transaction', backref='order')
    
    __table_args__ = (
        db.CheckConstraint('value > 0', name='check_order_value_positive'),
    )
    
    @property
    def is_overdue(self):
        """Verifica se a ordem está atrasada"""
        if self.status == 'aguardando_execucao' and self.service_deadline:
            return datetime.utcnow() > self.service_deadline
        return False
    
    @property
    def can_be_cancelled(self):
        """Verifica se a ordem pode ser cancelada"""
        return self.status in ['aguardando_execucao']
    
    @property
    def can_be_marked_completed(self):
        """Verifica se prestador pode marcar como concluído"""
        return self.status == 'aguardando_execucao'
    
    @property
    def can_be_confirmed(self):
        """Verifica se cliente pode confirmar"""
        return self.status == 'servico_executado'
    
    @property
    def can_be_disputed(self):
        """Verifica se pode ser contestada"""
        if self.status != 'servico_executado':
            return False
        if self.dispute_deadline:
            return datetime.utcnow() <= self.dispute_deadline
        return True
    
    @property
    def hours_until_auto_confirmation(self):
        """Retorna horas restantes até confirmação automática"""
        if self.status != 'servico_executado' or not self.confirmation_deadline:
            return None
        
        time_remaining = self.confirmation_deadline - datetime.utcnow()
        hours = time_remaining.total_seconds() / 3600
        
        return max(0, hours)  # Não retornar valores negativos
    
    @property
    def is_near_auto_confirmation(self):
        """Verifica se está próximo da confirmação automática (menos de 12h)"""
        hours = self.hours_until_auto_confirmation
        return hours is not None and hours <= 12
    
    @property
    def status_display(self):
        """Retorna o status em formato legível em português"""
        status_map = {
            'aguardando_execucao': 'Aguardando Execução',
            'servico_executado': 'Serviço Executado',
            'concluida': 'Concluída',
            'cancelada': 'Cancelada',
            'contestada': 'Contestada',
            'resolvida': 'Resolvida'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_color_class(self):
        """Retorna a classe CSS de cor baseada no status"""
        color_map = {
            'aguardando_execucao': 'bg-status-aguardando_execucao',
            'servico_executado': 'bg-status-servico_executado',
            'concluida': 'bg-status-concluida',
            'cancelada': 'bg-status-cancelada',
            'contestada': 'bg-status-contestada',
            'resolvida': 'bg-status-resolvida'
        }
        return color_map.get(self.status, 'bg-secondary')
    
    @property
    def status_icon_class(self):
        """Retorna a classe do ícone FontAwesome baseada no status"""
        icon_map = {
            'aguardando_execucao': 'fas fa-clock',
            'servico_executado': 'fas fa-check-circle',
            'concluida': 'fas fa-check-double',
            'cancelada': 'fas fa-times-circle',
            'contestada': 'fas fa-exclamation-triangle',
            'resolvida': 'fas fa-gavel'
        }
        return icon_map.get(self.status, 'fas fa-question-circle')

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
    rejection_reason = db.Column(db.Text, nullable=True)  # Motivo da rejeição fornecido pelo prestador
    
    # Campos para sistema de propostas de alteração
    has_active_proposal = db.Column(db.Boolean, default=False, nullable=False)
    current_proposal_id = db.Column(db.Integer, nullable=True)  # FK será tratada no relacionamento
    effective_value = db.Column(db.Numeric(10, 2), nullable=True)  # Valor efetivo após proposta aceita
    
    # Campos para aceitação mútua
    client_accepted = db.Column(db.Boolean, default=False, nullable=False)
    client_accepted_at = db.Column(db.DateTime, nullable=True)
    provider_accepted = db.Column(db.Boolean, default=False, nullable=False)
    provider_accepted_at = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    client = db.relationship('User', foreign_keys=[client_id], backref='sent_invites')
    order = db.relationship('Order', backref=db.backref('invite', uselist=False), foreign_keys='Order.invite_id')
    
    # Índices para performance
    __table_args__ = (
        db.Index('idx_invite_mutual_acceptance', 'client_accepted', 'provider_accepted', 'status'),
    )
    
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
    def is_mutually_accepted(self):
        """Verifica se ambas as partes aceitaram"""
        return self.client_accepted and self.provider_accepted
    
    @property
    def pending_acceptance_from(self):
        """Retorna quem ainda precisa aceitar"""
        if not self.client_accepted:
            return 'cliente'
        if not self.provider_accepted:
            return 'prestador'
        return None
    
    @property
    def is_expired(self):
        """Verifica se o convite está expirado - expira na data do serviço"""
        return datetime.utcnow() > self.delivery_date
    
    @property
    def can_be_accepted(self):
        """Verifica se o convite pode ser aceito"""
        # Importar aqui para evitar import circular
        from services.invite_state_manager import InviteStateManager
        can_accept, _ = InviteStateManager.can_be_accepted(self)
        return can_accept
    
    def can_be_accepted_with_message(self):
        """Verifica se o convite pode ser aceito e retorna mensagem explicativa"""
        # Importar aqui para evitar import circular
        from services.invite_state_manager import InviteStateManager
        return InviteStateManager.can_be_accepted(self)
    
    @property
    def invite_link(self):
        """Gera o link do convite para ser enviado ao prestador"""
        from flask import url_for, request, has_request_context
        try:
            if has_request_context():
                return url_for('auth.convite_acesso', token=self.token, _external=True)
            else:
                # Fallback consistente - sempre retorna URL relativa
                return f"/auth/convite/{self.token}"
        except:
            # Fallback se houver erro
            return f"/auth/convite/{self.token}"
    
    @property
    def current_value(self):
        """Retorna o valor atual do convite (efetivo se houver proposta aceita, senão original)"""
        return self.effective_value if self.effective_value is not None else self.original_value
    
    @property
    def is_counter_proposal(self):
        """Verifica se este convite é uma contraproposta"""
        return self.service_title and '🔄 CONTRAPROPOSTA' in self.service_title
    
    def was_counter_proposal_created_by_client(self):
        """
        Verifica se a contraproposta foi criada pelo cliente
        Retorna True se cliente criou, False se prestador criou, None se não é contraproposta
        """
        if not self.is_counter_proposal:
            return None
        
        # Verificar na descrição quem criou a contraproposta
        # A descrição contém: "💡 Contraproposta de {nome}: {justificativa}"
        if self.service_description and '💡 Contraproposta de' in self.service_description:
            # Extrair o nome de quem criou
            try:
                # Pegar a última ocorrência (a mais recente)
                parts = self.service_description.split('💡 Contraproposta de ')
                if len(parts) > 1:
                    proposer_name = parts[-1].split(':')[0].strip()
                    # Verificar se é o nome do cliente
                    if self.client and proposer_name == self.client.nome:
                        return True
                    else:
                        return False
            except:
                pass
        
        return None
    
    def can_user_accept_counter_proposal(self, user_id):
        """
        Verifica se o usuário pode aceitar esta contraproposta
        Usuário NÃO pode aceitar se ele mesmo criou a contraproposta
        """
        if not self.is_counter_proposal:
            return True  # Não é contraproposta, pode aceitar normalmente
        
        # Verificar quem criou a contraproposta
        created_by_client = self.was_counter_proposal_created_by_client()
        
        if created_by_client is None:
            return True  # Não conseguiu determinar, permitir
        
        # Se cliente criou, cliente NÃO pode aceitar (deve aguardar prestador)
        if created_by_client and self.client_id == user_id:
            return False
        
        # Se prestador criou, prestador NÃO pode aceitar (deve aguardar cliente)
        # Verificar se o usuário é o prestador
        from models import User
        user = User.query.get(user_id)
        if user and not created_by_client and user.phone == self.invited_phone:
            return False
        
        return True
    
    @property
    def has_pending_proposal(self):
        """Verifica se há uma proposta pendente"""
        return self.has_active_proposal and self.current_proposal_id is not None
    
    def get_active_proposal(self):
        """Retorna a proposta ativa se existir"""
        if self.has_active_proposal and self.current_proposal_id:
            return Proposal.query.get(self.current_proposal_id)
        return None
    
    def set_active_proposal(self, proposal):
        """Define uma proposta como ativa para este convite"""
        self.has_active_proposal = True
        self.current_proposal_id = proposal.id
    
    def clear_active_proposal(self):
        """Remove a proposta ativa deste convite"""
        self.has_active_proposal = False
        self.current_proposal_id = None
    
    def get_current_state(self):
        """Retorna o estado atual do convite"""
        from services.invite_state_manager import InviteStateManager
        return InviteStateManager.get_current_state(self)
    
    def can_transition_to(self, target_state):
        """Verifica se pode transicionar para o estado alvo"""
        from services.invite_state_manager import InviteStateManager, InviteState
        if isinstance(target_state, str):
            target_state = InviteState(target_state)
        return InviteStateManager.can_transition_to(self, target_state)
    
    def transition_to(self, target_state, user_id=None, reason=None):
        """Executa transição de estado"""
        from services.invite_state_manager import InviteStateManager, InviteState
        if isinstance(target_state, str):
            target_state = InviteState(target_state)
        return InviteStateManager.transition_to_state(self, target_state, user_id, reason)
    
    def get_available_actions(self, user_role=None):
        """Retorna ações disponíveis baseadas no estado atual"""
        from services.invite_state_manager import InviteStateManager
        return InviteStateManager.get_available_actions(self, user_role)
    
    def get_state_description(self):
        """Retorna descrição amigável do estado atual"""
        from services.invite_state_manager import InviteStateManager
        return InviteStateManager.get_state_description(self)
    
    def can_create_proposal(self):
        """Verifica se uma proposta pode ser criada para este convite"""
        from services.invite_state_manager import InviteStateManager
        can_create, _ = InviteStateManager.can_create_proposal(self)
        return can_create
    
    def __repr__(self):
        return f'<Invite {self.id}: {self.service_title} para {self.invited_phone}>'


class Proposal(db.Model):
    """Modelo para propostas de alteração de convites"""
    __tablename__ = 'invite_proposals'
    id = db.Column(db.Integer, primary_key=True)
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=False)
    prestador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_value = db.Column(db.Numeric(10, 2), nullable=False)
    proposed_value = db.Column(db.Numeric(10, 2), nullable=False)
    justification = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, accepted, rejected, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)
    client_response_reason = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    invite = db.relationship('Invite', backref=db.backref('proposals', lazy='dynamic', cascade="all, delete-orphan"))
    prestador = db.relationship('User', foreign_keys=[prestador_id], backref='created_proposals')
    
    def __init__(self, **kwargs):
        super(Proposal, self).__init__(**kwargs)
        if not self.status:
            self.status = 'pending'
    
    __table_args__ = (
        db.CheckConstraint('original_value > 0', name='check_original_value_positive'),
        db.CheckConstraint('proposed_value > 0', name='check_proposed_value_positive'),
        db.CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'cancelled')", name='check_proposal_status_valid'),
    )
    
    @property
    def is_pending(self):
        """Verifica se a proposta está pendente"""
        return self.status == 'pending'
    
    @property
    def is_accepted(self):
        """Verifica se a proposta foi aceita"""
        return self.status == 'accepted'
    
    @property
    def is_rejected(self):
        """Verifica se a proposta foi rejeitada"""
        return self.status == 'rejected'
    
    @property
    def is_cancelled(self):
        """Verifica se a proposta foi cancelada"""
        return self.status == 'cancelled'
    
    @property
    def value_difference(self):
        """Calcula a diferença entre o valor proposto e o original"""
        return self.proposed_value - self.original_value
    
    @property
    def is_increase(self):
        """Verifica se a proposta é um aumento de valor"""
        return self.proposed_value > self.original_value
    
    @property
    def is_decrease(self):
        """Verifica se a proposta é uma diminuição de valor"""
        return self.proposed_value < self.original_value
    
    def accept(self, client_response_reason=None):
        """Aceita a proposta - atualiza apenas status e responded_at"""
        self.status = 'accepted'
        self.responded_at = datetime.utcnow()
        self.client_response_reason = client_response_reason
        
        # Atualizar effective_value no convite
        if self.invite:
            self.invite.effective_value = self.proposed_value
    
    def reject(self, client_response_reason=None):
        """Rejeita a proposta - atualiza apenas status e responded_at
        A limpeza dos campos do convite será feita pelo InviteStateManager"""
        self.status = 'rejected'
        self.responded_at = datetime.utcnow()
        self.client_response_reason = client_response_reason
    
    def cancel(self):
        """Cancela a proposta (ação do prestador) - atualiza apenas status e responded_at
        A limpeza dos campos do convite será feita pelo InviteStateManager"""
        self.status = 'cancelled'
        self.responded_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Proposal {self.id}: {self.original_value} -> {self.proposed_value} ({self.status})>'


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


# ==============================================================================
#  MODELOS DE AUDITORIA E MONITORAMENTO DE PROPOSTAS
# ==============================================================================

class ProposalAuditLog(db.Model):
    """Modelo para auditoria completa de ações relacionadas a propostas"""
    __tablename__ = 'proposal_audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('invite_proposals.id'), nullable=False)
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # created, approved, rejected, cancelled, modified
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    actor_admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    actor_role = db.Column(db.String(20), nullable=False)  # cliente, prestador, admin, system
    
    # Dados da ação
    previous_data = db.Column(db.Text, nullable=True)  # JSON com estado anterior
    new_data = db.Column(db.Text, nullable=True)  # JSON com novo estado
    reason = db.Column(db.Text, nullable=True)  # Motivo/justificativa da ação
    
    # Metadados técnicos
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    
    # Dados financeiros
    original_value = db.Column(db.Numeric(10, 2), nullable=True)
    proposed_value = db.Column(db.Numeric(10, 2), nullable=True)
    value_difference = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    proposal = db.relationship('Proposal', backref='audit_logs')
    invite = db.relationship('Invite', backref='proposal_audit_logs')
    actor_user = db.relationship('User', foreign_keys=[actor_user_id])
    actor_admin = db.relationship('AdminUser', foreign_keys=[actor_admin_id])
    
    def __repr__(self):
        return f'<ProposalAuditLog {self.action_type} - Proposal:{self.proposal_id} by {self.actor_role}>'


class ProposalMetrics(db.Model):
    """Modelo para métricas agregadas de propostas por período"""
    __tablename__ = 'proposal_metrics'
    id = db.Column(db.Integer, primary_key=True)
    
    # Período da métrica
    metric_date = db.Column(db.Date, nullable=False)
    metric_type = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    
    # Contadores básicos
    total_proposals = db.Column(db.Integer, nullable=False, default=0)
    proposals_created = db.Column(db.Integer, nullable=False, default=0)
    proposals_approved = db.Column(db.Integer, nullable=False, default=0)
    proposals_rejected = db.Column(db.Integer, nullable=False, default=0)
    proposals_cancelled = db.Column(db.Integer, nullable=False, default=0)
    
    # Métricas de valor
    total_original_value = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    total_proposed_value = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    total_approved_value = db.Column(db.Numeric(18, 2), nullable=False, default=0.00)
    
    # Métricas de comportamento
    proposals_with_increase = db.Column(db.Integer, nullable=False, default=0)
    proposals_with_decrease = db.Column(db.Integer, nullable=False, default=0)
    average_response_time_hours = db.Column(db.Numeric(8, 2), nullable=True)
    
    # Métricas de usuários únicos
    unique_prestadores = db.Column(db.Integer, nullable=False, default=0)
    unique_clientes = db.Column(db.Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('metric_date', 'metric_type', name='unique_metric_date_type'),
    )
    
    @property
    def approval_rate(self):
        """Taxa de aprovação das propostas"""
        total_responded = self.proposals_approved + self.proposals_rejected
        return (self.proposals_approved / total_responded * 100) if total_responded > 0 else 0
    
    @property
    def average_value_increase(self):
        """Aumento médio de valor nas propostas"""
        if self.proposals_with_increase > 0:
            return (self.total_proposed_value - self.total_original_value) / self.proposals_with_increase
        return 0
    
    def __repr__(self):
        return f'<ProposalMetrics {self.metric_date} - {self.metric_type}: {self.total_proposals} propostas>'


class ProposalAlert(db.Model):
    """Modelo para alertas sobre padrões suspeitos em propostas"""
    __tablename__ = 'proposal_alerts'
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo e severidade do alerta
    alert_type = db.Column(db.String(50), nullable=False)  # suspicious_pattern, high_rejection_rate, unusual_values, etc.
    severity = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, critical
    
    # Dados do alerta
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Entidades relacionadas
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('invite_proposals.id'), nullable=True)
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=True)
    
    # Dados do padrão detectado
    pattern_data = db.Column(db.Text, nullable=True)  # JSON com detalhes do padrão
    threshold_exceeded = db.Column(db.String(100), nullable=True)  # Qual limite foi ultrapassado
    
    # Status do alerta
    status = db.Column(db.String(20), nullable=False, default='active')  # active, investigating, resolved, false_positive
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id])
    proposal = db.relationship('Proposal', foreign_keys=[proposal_id])
    invite = db.relationship('Invite', foreign_keys=[invite_id])
    resolver = db.relationship('AdminUser', foreign_keys=[resolved_by])
    
    def resolve(self, admin_id, notes=None):
        """Marca o alerta como resolvido"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = admin_id
        self.resolution_notes = notes
    
    def mark_false_positive(self, admin_id, notes=None):
        """Marca o alerta como falso positivo"""
        self.status = 'false_positive'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = admin_id
        self.resolution_notes = notes
    
    def __repr__(self):
        return f'<ProposalAlert {self.alert_type} - {self.severity}: {self.title}>'



# ==============================================================================
#  MODELOS DE PRÉ-ORDEM (SISTEMA DE NEGOCIAÇÃO)
# ==============================================================================

class PreOrderStatus(enum.Enum):
    """Estados possíveis de uma pré-ordem"""
    EM_NEGOCIACAO = "em_negociacao"
    AGUARDANDO_RESPOSTA = "aguardando_resposta"
    PRONTO_CONVERSAO = "pronto_conversao"
    CONVERTIDA = "convertida"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"


class PreOrder(db.Model):
    """
    Modelo para pré-ordens - estágio intermediário de negociação entre convite aceito e ordem definitiva.
    
    Fluxo: Convite → PreOrder (negociação) → Order (valores bloqueados)
    
    A pré-ordem permite que ambas as partes negociem valor, prazo e condições antes de bloquear
    valores em escrow. Somente quando ambas as partes aceitam os termos finais, a pré-ordem é
    convertida em ordem definitiva com bloqueio de valores.
    """
    __tablename__ = 'pre_orders'
    
    # Identificação
    id = db.Column(db.Integer, primary_key=True)
    invite_id = db.Column(db.Integer, db.ForeignKey('invites.id'), nullable=False, unique=True)
    
    # Partes envolvidas
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados do serviço (copiados do convite, podem ser modificados via propostas)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    current_value = db.Column(db.Numeric(18, 2), nullable=False)  # Valor atual negociado
    original_value = db.Column(db.Numeric(18, 2), nullable=False)  # Valor inicial do convite
    delivery_date = db.Column(db.DateTime, nullable=False)
    service_category = db.Column(db.String(100), nullable=True)
    
    # Estado da negociação
    status = db.Column(db.String(50), nullable=False, default=PreOrderStatus.EM_NEGOCIACAO.value)
    client_accepted_terms = db.Column(db.Boolean, default=False, nullable=False)
    provider_accepted_terms = db.Column(db.Boolean, default=False, nullable=False)
    client_accepted_at = db.Column(db.DateTime, nullable=True)
    provider_accepted_at = db.Column(db.DateTime, nullable=True)
    
    # Proposta ativa
    has_active_proposal = db.Column(db.Boolean, default=False, nullable=False)
    active_proposal_id = db.Column(db.Integer, db.ForeignKey('pre_order_proposals.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)  # Prazo para negociação (7 dias padrão)
    converted_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    # Cancelamento
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    # Conversão
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, unique=True)
    
    # Relacionamentos
    invite = db.relationship('Invite', backref=db.backref('pre_order', uselist=False))
    client = db.relationship('User', foreign_keys=[client_id], backref='pre_orders_as_client')
    provider = db.relationship('User', foreign_keys=[provider_id], backref='pre_orders_as_provider')
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by])
    order = db.relationship('Order', backref=db.backref('pre_order', uselist=False))
    proposals = db.relationship('PreOrderProposal', backref='pre_order', lazy='dynamic', 
                                foreign_keys='PreOrderProposal.pre_order_id')
    history = db.relationship('PreOrderHistory', backref='pre_order', lazy='dynamic', 
                             order_by='PreOrderHistory.created_at.desc()')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('current_value > 0', name='check_pre_order_current_value_positive'),
        db.CheckConstraint('original_value > 0', name='check_pre_order_original_value_positive'),
        db.CheckConstraint('expires_at > created_at', name='check_pre_order_expires_after_creation'),
        db.Index('idx_pre_orders_status', 'status'),
        db.Index('idx_pre_orders_client', 'client_id'),
        db.Index('idx_pre_orders_provider', 'provider_id'),
        db.Index('idx_pre_orders_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self):
        """Verifica se a pré-ordem expirou"""
        return datetime.utcnow() > self.expires_at and self.status not in [
            PreOrderStatus.CONVERTIDA.value,
            PreOrderStatus.CANCELADA.value,
            PreOrderStatus.EXPIRADA.value
        ]
    
    @property
    def can_be_converted(self):
        """Verifica se a pré-ordem pode ser convertida em ordem"""
        return (
            self.status == PreOrderStatus.PRONTO_CONVERSAO.value and
            self.client_accepted_terms and
            self.provider_accepted_terms and
            not self.is_expired
        )
    
    @property
    def days_until_expiration(self):
        """Retorna dias restantes até expiração"""
        if self.status in [PreOrderStatus.CONVERTIDA.value, PreOrderStatus.CANCELADA.value, PreOrderStatus.EXPIRADA.value]:
            return 0
        
        time_remaining = self.expires_at - datetime.utcnow()
        days = time_remaining.total_seconds() / 86400  # 86400 segundos em um dia
        return max(0, days)
    
    @property
    def is_near_expiration(self):
        """Verifica se está próximo da expiração (menos de 24h)"""
        return self.days_until_expiration <= 1 and self.days_until_expiration > 0
    
    @property
    def has_mutual_acceptance(self):
        """Verifica se ambas as partes aceitaram os termos"""
        return self.client_accepted_terms and self.provider_accepted_terms
    
    @property
    def pending_acceptance_from(self):
        """Retorna quem ainda precisa aceitar os termos"""
        if not self.client_accepted_terms and not self.provider_accepted_terms:
            return 'ambos'
        elif not self.client_accepted_terms:
            return 'cliente'
        elif not self.provider_accepted_terms:
            return 'prestador'
        return None
    
    @property
    def value_difference_from_original(self):
        """Calcula diferença entre valor atual e original"""
        return self.current_value - self.original_value
    
    @property
    def value_change_percentage(self):
        """Calcula percentual de mudança do valor"""
        if self.original_value == 0:
            return 0
        return ((self.current_value - self.original_value) / self.original_value) * 100
    
    @property
    def status_display(self):
        """Retorna status em formato legível"""
        status_map = {
            PreOrderStatus.EM_NEGOCIACAO.value: 'Em Negociação',
            PreOrderStatus.AGUARDANDO_RESPOSTA.value: 'Aguardando Resposta',
            PreOrderStatus.PRONTO_CONVERSAO.value: 'Pronto para Conversão',
            PreOrderStatus.CONVERTIDA.value: 'Convertida em Ordem',
            PreOrderStatus.CANCELADA.value: 'Cancelada',
            PreOrderStatus.EXPIRADA.value: 'Expirada'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_color_class(self):
        """Retorna classe CSS de cor baseada no status"""
        color_map = {
            PreOrderStatus.EM_NEGOCIACAO.value: 'bg-info',
            PreOrderStatus.AGUARDANDO_RESPOSTA.value: 'bg-warning',
            PreOrderStatus.PRONTO_CONVERSAO.value: 'bg-success',
            PreOrderStatus.CONVERTIDA.value: 'bg-primary',
            PreOrderStatus.CANCELADA.value: 'bg-danger',
            PreOrderStatus.EXPIRADA.value: 'bg-secondary'
        }
        return color_map.get(self.status, 'bg-secondary')
    
    def get_active_proposal(self):
        """Retorna a proposta ativa se existir"""
        if self.has_active_proposal and self.active_proposal_id:
            return PreOrderProposal.query.get(self.active_proposal_id)
        return None
    
    def __repr__(self):
        return f'<PreOrder {self.id}: {self.title} - {self.status}>'


class ProposalStatus(enum.Enum):
    """Estados possíveis de uma proposta de pré-ordem"""
    PENDENTE = "pendente"
    ACEITA = "aceita"
    REJEITADA = "rejeitada"
    CANCELADA = "cancelada"


class PreOrderProposal(db.Model):
    """
    Modelo para propostas de alteração em pré-ordens.
    
    Permite que cliente ou prestador proponham mudanças em valor, prazo ou descrição
    durante a negociação da pré-ordem.
    """
    __tablename__ = 'pre_order_proposals'
    
    id = db.Column(db.Integer, primary_key=True)
    pre_order_id = db.Column(db.Integer, db.ForeignKey('pre_orders.id'), nullable=False)
    
    # Autor da proposta
    proposed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Alterações propostas (nullable = pode propor apenas alguns campos)
    proposed_value = db.Column(db.Numeric(18, 2), nullable=True)
    proposed_delivery_date = db.Column(db.DateTime, nullable=True)
    proposed_description = db.Column(db.Text, nullable=True)
    justification = db.Column(db.Text, nullable=False)  # Sempre obrigatório
    
    # Estado
    status = db.Column(db.String(50), nullable=False, default=ProposalStatus.PENDENTE.value)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    proposer = db.relationship('User', foreign_keys=[proposed_by], backref='pre_order_proposals')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('LENGTH(justification) >= 50', name='check_proposal_justification_min_length'),
        db.CheckConstraint(
            'proposed_value IS NOT NULL OR proposed_delivery_date IS NOT NULL OR proposed_description IS NOT NULL',
            name='check_proposal_at_least_one_change'
        ),
        db.Index('idx_pre_order_proposals_status', 'status'),
        db.Index('idx_pre_order_proposals_pre_order', 'pre_order_id', 'created_at'),
    )
    
    @property
    def is_pending(self):
        """Verifica se a proposta está pendente"""
        return self.status == ProposalStatus.PENDENTE.value
    
    @property
    def is_accepted(self):
        """Verifica se a proposta foi aceita"""
        return self.status == ProposalStatus.ACEITA.value
    
    @property
    def is_rejected(self):
        """Verifica se a proposta foi rejeitada"""
        return self.status == ProposalStatus.REJEITADA.value
    
    @property
    def is_cancelled(self):
        """Verifica se a proposta foi cancelada"""
        return self.status == ProposalStatus.CANCELADA.value
    
    @property
    def value_difference(self):
        """Calcula diferença de valor proposto vs atual da pré-ordem"""
        if self.proposed_value and self.pre_order:
            return self.proposed_value - self.pre_order.current_value
        return None
    
    @property
    def is_value_increase(self):
        """Verifica se propõe aumento de valor"""
        diff = self.value_difference
        return diff is not None and diff > 0
    
    @property
    def is_value_decrease(self):
        """Verifica se propõe redução de valor"""
        diff = self.value_difference
        return diff is not None and diff < 0
    
    @property
    def is_extreme_proposal(self):
        """Verifica se é uma proposta extrema (>100% aumento ou >50% redução)"""
        if not self.proposed_value or not self.pre_order:
            return False
        
        current = self.pre_order.current_value
        if current == 0:
            return False
        
        change_percent = ((self.proposed_value - current) / current) * 100
        return change_percent > 100 or change_percent < -50
    
    @property
    def status_display(self):
        """Retorna status em formato legível"""
        status_map = {
            ProposalStatus.PENDENTE.value: 'Pendente',
            ProposalStatus.ACEITA.value: 'Aceita',
            ProposalStatus.REJEITADA.value: 'Rejeitada',
            ProposalStatus.CANCELADA.value: 'Cancelada'
        }
        return status_map.get(self.status, self.status.title())
    
    def __repr__(self):
        return f'<PreOrderProposal {self.id}: PreOrder {self.pre_order_id} - {self.status}>'


class PreOrderHistory(db.Model):
    """
    Modelo para histórico de eventos em pré-ordens.
    
    Registra todas as ações e mudanças de estado para auditoria e rastreabilidade.
    """
    __tablename__ = 'pre_order_history'
    
    id = db.Column(db.Integer, primary_key=True)
    pre_order_id = db.Column(db.Integer, db.ForeignKey('pre_orders.id'), nullable=False)
    
    # Evento
    event_type = db.Column(db.String(50), nullable=False)  # created, proposal_sent, proposal_accepted, etc.
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = Sistema
    description = db.Column(db.Text, nullable=False)
    
    # Dados do evento (JSON para flexibilidade)
    event_data = db.Column(db.JSON, nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    actor = db.relationship('User', foreign_keys=[actor_id])
    
    # Índices
    __table_args__ = (
        db.Index('idx_pre_order_history_pre_order', 'pre_order_id', 'created_at'),
    )
    
    @property
    def event_type_display(self):
        """Retorna tipo de evento em formato legível"""
        event_map = {
            'created': 'Pré-ordem Criada',
            'proposal_sent': 'Proposta Enviada',
            'proposal_accepted': 'Proposta Aceita',
            'proposal_rejected': 'Proposta Rejeitada',
            'proposal_cancelled': 'Proposta Cancelada',
            'terms_accepted_client': 'Cliente Aceitou Termos',
            'terms_accepted_provider': 'Prestador Aceitou Termos',
            'converted': 'Convertida em Ordem',
            'cancelled': 'Cancelada',
            'expired': 'Expirada',
            'value_updated': 'Valor Atualizado',
            'date_updated': 'Prazo Atualizado'
        }
        return event_map.get(self.event_type, self.event_type.replace('_', ' ').title())
    
    def __repr__(self):
        return f'<PreOrderHistory {self.id}: {self.event_type} - PreOrder {self.pre_order_id}>'
