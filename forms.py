#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange

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
