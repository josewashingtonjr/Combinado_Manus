#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TextAreaField, DecimalField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from services.validation_service import ValidationService

# ==============================================================================
#  FORMULÁRIOS DE AUTENTICAÇÃO
# ==============================================================================

class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class UserLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

# ==============================================================================
#  FORMULÁRIOS ADMINISTRATIVOS
# ==============================================================================

class CreateUserForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', 
                                   validators=[DataRequired(), EqualTo('password')])
    roles = SelectField('Papel do Usuário', 
                       choices=[('cliente', 'Cliente'), ('prestador', 'Prestador')],
                       validators=[DataRequired()])
    submit = SubmitField('Criar Usuário')
    
    def validate_cpf(self, field):
        """Validação personalizada de CPF"""
        is_valid, message = ValidationService.validate_cpf(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    def validate_phone(self, field):
        """Validação personalizada de telefone"""
        is_valid, message = ValidationService.validate_phone(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    def validate_email(self, field):
        """Validação personalizada de email"""
        is_valid, message = ValidationService.validate_email(field.data)
        if not is_valid:
            raise ValidationError(message)
        
        # Verificar se email já existe
        from models import User, AdminUser
        existing_user = User.query.filter_by(email=field.data).first()
        existing_admin = AdminUser.query.filter_by(email=field.data).first()
        
        if existing_user or existing_admin:
            raise ValidationError("Este email já está em uso.")
    
    def validate_password(self, field):
        """Validação personalizada de senha"""
        is_valid, message = ValidationService.validate_password(
            field.data, self.confirm_password.data
        )
        if not is_valid:
            raise ValidationError(message)

class EditUserForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    roles = SelectField('Papel do Usuário', 
                       choices=[('cliente', 'Cliente'), ('prestador', 'Prestador')],
                       validators=[DataRequired()])
    active = BooleanField('Usuário Ativo')
    submit = SubmitField('Salvar Alterações')
    
    def __init__(self, original_email=None, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_cpf(self, field):
        """Validação personalizada de CPF"""
        is_valid, message = ValidationService.validate_cpf(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    def validate_phone(self, field):
        """Validação personalizada de telefone"""
        is_valid, message = ValidationService.validate_phone(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    def validate_email(self, field):
        """Validação personalizada de email"""
        is_valid, message = ValidationService.validate_email(field.data)
        if not is_valid:
            raise ValidationError(message)
        
        # Verificar se email já existe (exceto o próprio usuário)
        if field.data != self.original_email:
            from models import User, AdminUser
            existing_user = User.query.filter_by(email=field.data).first()
            existing_admin = AdminUser.query.filter_by(email=field.data).first()
            
            if existing_user or existing_admin:
                raise ValidationError("Este email já está em uso.")

class SystemConfigForm(FlaskForm):
    taxa_sistema = DecimalField('Taxa do Sistema (%)', 
                               validators=[DataRequired(), NumberRange(min=0, max=100)],
                               places=2)
    valor_token = DecimalField('Valor do Token (R$)', 
                              validators=[DataRequired(), NumberRange(min=0.01)],
                              places=2)
    sistema_ativo = BooleanField('Sistema Ativo')
    manutencao = BooleanField('Modo Manutenção')
    observacoes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Configurações')

class AddTokensForm(FlaskForm):
    user_id = SelectField('Usuário', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Quantidade de Tokens', 
                         validators=[DataRequired(), NumberRange(min=0.01)],
                         places=2)
    description = TextAreaField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Adicionar Tokens')

class CreateTokensForm(FlaskForm):
    """Formulário para admin criar novos tokens no sistema"""
    amount = DecimalField('Quantidade de Tokens', 
                         validators=[DataRequired(), NumberRange(min=1.00)],
                         places=0)
    description = TextAreaField('Descrição', 
                               validators=[DataRequired(), Length(min=10, max=500)],
                               default='Criação de tokens pelo admin')
    submit = SubmitField('Criar Tokens')
    
    def validate_amount(self, field):
        """Validação personalizada para criação de tokens"""
        if field.data <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")
        
        if field.data > 1000000:  # Limite de 1 milhão por operação
            raise ValidationError("Quantidade máxima por operação: 1.000.000 tokens.")
    
    def validate_description(self, field):
        """Validação da descrição"""
        if not field.data or len(field.data.strip()) < 10:
            raise ValidationError("Descrição deve ter pelo menos 10 caracteres.")

# ==============================================================================
#  FORMULÁRIOS DE ORDENS DE SERVIÇO
# ==============================================================================

class CreateOrderForm(FlaskForm):
    title = StringField('Título do Serviço', 
                       validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Descrição Detalhada', 
                               validators=[DataRequired(), Length(min=20, max=1000)])
    value = DecimalField('Valor (R$)', 
                        validators=[DataRequired(), NumberRange(min=1.00)],
                        places=2)
    submit = SubmitField('Criar Ordem')
    
    def validate_value(self, field):
        """Validação personalizada de valor da ordem"""
        user_type = ValidationService.get_user_type()
        is_valid, message = ValidationService.validate_order_value(field.data, user_type)
        if not is_valid:
            raise ValidationError(message)

# ==============================================================================
#  FORMULÁRIOS DE TOKENOMICS (ESPECÍFICOS POR TIPO DE USUÁRIO)
# ==============================================================================

class TokenPurchaseForm(FlaskForm):
    """Formulário para compra de tokens (usuários) ou criação de tokens (admin)"""
    amount = DecimalField('Quantidade', 
                         validators=[DataRequired(), NumberRange(min=0.01)],
                         places=2)
    description = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Confirmar')
    
    def validate_amount(self, field):
        """Validação personalizada baseada no tipo de usuário"""
        user_type = ValidationService.get_user_type()
        
        if user_type == 'admin':
            # Admin criando tokens - sem limite específico
            if field.data <= 0:
                raise ValidationError("Quantidade deve ser maior que zero.")
        else:
            # Usuário comprando tokens - validar com saldo
            is_valid, message = ValidationService.validate_tokenomics_operation(
                'purchase', field.data, 0  # Saldo será verificado na view
            )
            if not is_valid:
                raise ValidationError(message)

class TokenWithdrawalForm(FlaskForm):
    """Formulário para saque de tokens"""
    amount = DecimalField('Quantidade para Saque', 
                         validators=[DataRequired(), NumberRange(min=10.00)],
                         places=2)
    bank_account = StringField('Conta Bancária', validators=[DataRequired()])
    submit = SubmitField('Solicitar Saque')
    
    def validate_amount(self, field):
        """Validação personalizada de saque"""
        user_type = ValidationService.get_user_type()
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'withdrawal', field.data, 0  # Saldo será verificado na view
        )
        if not is_valid:
            raise ValidationError(message)

class TokenTransferForm(FlaskForm):
    """Formulário para transferência de tokens entre usuários"""
    recipient_email = StringField('Email do Destinatário', 
                                 validators=[DataRequired(), Email()])
    amount = DecimalField('Quantidade', 
                         validators=[DataRequired(), NumberRange(min=1.00)],
                         places=2)
    description = TextAreaField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Transferir')
    
    def validate_amount(self, field):
        """Validação personalizada de transferência"""
        user_type = ValidationService.get_user_type()
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'transfer', field.data, 0  # Saldo será verificado na view
        )
        if not is_valid:
            raise ValidationError(message)
    
    def validate_recipient_email(self, field):
        """Validar se o destinatário existe"""
        from models import User
        recipient = User.query.filter_by(email=field.data).first()
        if not recipient:
            raise ValidationError("Usuário destinatário não encontrado.")

# ==============================================================================
#  FORMULÁRIOS COM VALIDAÇÃO DE CONEXÃO DE BANCO
# ==============================================================================

class DatabaseDependentForm(FlaskForm):
    """Classe base para formulários que dependem do banco de dados"""
    
    def validate(self):
        """Validação que inclui verificação de conexão com banco"""
        # Verificar conexão com banco primeiro
        db_valid, db_message = ValidationService.validate_database_connection()
        if not db_valid:
            self.form_errors = [db_message]
            return False
        
        # Continuar com validação normal
        return super().validate()

class SafeCreateOrderForm(DatabaseDependentForm):
    """Formulário de criação de ordem com validação de banco"""
    title = StringField('Título do Serviço', 
                       validators=[DataRequired(), Length(min=5, max=100)])
    description = TextAreaField('Descrição Detalhada', 
                               validators=[DataRequired(), Length(min=20, max=1000)])
    value = DecimalField('Valor', 
                        validators=[DataRequired(), NumberRange(min=1.00)],
                        places=2)
    submit = SubmitField('Criar Ordem')
    
    def validate_value(self, field):
        """Validação com verificação de saldo do usuário"""
        user_type = ValidationService.get_user_type()
        
        # Validar valor básico
        is_valid, message = ValidationService.validate_order_value(field.data, user_type)
        if not is_valid:
            raise ValidationError(message)
        
        # Verificar saldo do usuário (se não for admin)
        if user_type != 'admin':
            try:
                from flask import session
                from services.wallet_service import WalletService
                
                user_id = session.get('user_id')
                if user_id:
                    wallet_info = WalletService.get_wallet_info(user_id)
                    if wallet_info:
                        balance_valid, balance_message = ValidationService.validate_balance(
                            field.data, wallet_info['balance'], user_type
                        )
                        if not balance_valid:
                            raise ValidationError(balance_message)
            except Exception as e:
                ValidationService.log_validation_error('order_value', str(e))
                raise ValidationError("Erro ao verificar saldo. Tente novamente.")

# ==============================================================================
#  FORMULÁRIOS DE CONVITES COM VALIDAÇÕES ESPECÍFICAS
# ==============================================================================

class CreateInviteForm(FlaskForm):
    """Formulário para criação de convites"""
    invited_email = StringField('Email do Prestador', 
                               validators=[DataRequired(), Email()])
    service_title = StringField('Título do Serviço', 
                               validators=[DataRequired(), Length(min=5, max=200)])
    service_description = TextAreaField('Descrição do Serviço', 
                                       validators=[DataRequired(), Length(min=20, max=1000)])
    original_value = DecimalField('Valor Proposto', 
                                 validators=[DataRequired(), NumberRange(min=1.00)],
                                 places=2)
    submit = SubmitField('Enviar Convite')
    
    def validate_original_value(self, field):
        """Validação de valor do convite com verificação de saldo"""
        user_type = ValidationService.get_user_type()
        
        # Validar valor básico
        is_valid, message = ValidationService.validate_order_value(field.data, user_type)
        if not is_valid:
            raise ValidationError(message)
        
        # Verificar se cliente tem saldo suficiente (valor + taxa de contestação)
        try:
            from flask import session
            from services.wallet_service import WalletService
            from decimal import Decimal
            
            user_id = session.get('user_id')
            if user_id and user_type != 'admin':
                wallet_info = WalletService.get_wallet_info(user_id)
                if wallet_info:
                    # Valor + taxa de contestação (assumindo 10% como exemplo)
                    total_needed = field.data + (field.data * Decimal('0.10'))
                    
                    balance_valid, balance_message = ValidationService.validate_balance(
                        total_needed, wallet_info['balance'], user_type
                    )
                    if not balance_valid:
                        if user_type == 'admin':
                            raise ValidationError(f"Tokens insuficientes para convite + taxa de contestação. Necessário: {total_needed} tokens.")
                        else:
                            raise ValidationError(f"Saldo insuficiente para convite + taxa de contestação. Necessário: R$ {total_needed:,.2f}.")
        except Exception as e:
            ValidationService.log_validation_error('invite_value', str(e))
            raise ValidationError("Erro ao verificar saldo para convite. Tente novamente.")

class RespondInviteForm(FlaskForm):
    """Formulário para responder convites"""
    action = SelectField('Ação', 
                        choices=[('accept', 'Aceitar'), ('reject', 'Recusar'), ('negotiate', 'Negociar')],
                        validators=[DataRequired()])
    final_value = DecimalField('Valor Final (se negociando)', 
                              validators=[Optional(), NumberRange(min=1.00)],
                              places=2)
    response_message = TextAreaField('Mensagem', validators=[Optional()])
    submit = SubmitField('Confirmar Resposta')
    
    def validate_final_value(self, field):
        """Validação de valor final na negociação"""
        if self.action.data == 'negotiate' and not field.data:
            raise ValidationError("Valor final é obrigatório ao negociar.")
        
        if field.data:
            user_type = ValidationService.get_user_type()
            is_valid, message = ValidationService.validate_order_value(field.data, user_type)
            if not is_valid:
                raise ValidationError(message)
