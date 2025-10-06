#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serviço de Validações e Mensagens de Erro Personalizadas
Implementa validações específicas e mensagens diferenciadas por tipo de usuário
"""

from flask import session, request, has_request_context
from decimal import Decimal, InvalidOperation
import re
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    """Serviço para validações e mensagens de erro personalizadas"""
    
    @staticmethod
    def get_user_type():
        """Detectar tipo de usuário atual"""
        # Verificar se estamos em contexto de requisição
        if not has_request_context():
            return 'guest'
        
        try:
            if session.get('admin_id'):
                return 'admin'
            elif session.get('user_id'):
                return 'user'
            else:
                return 'guest'
        except RuntimeError:
            # Fallback se não conseguir acessar session
            return 'guest'
    
    @staticmethod
    def format_error_message(base_message, user_type=None, context=None):
        """Formatar mensagem de erro baseada no tipo de usuário"""
        if user_type is None:
            user_type = ValidationService.get_user_type()
        
        # Mensagens específicas por tipo de usuário
        if user_type == 'admin':
            # Administradores veem mensagens técnicas
            if 'saldo' in base_message.lower():
                return base_message.replace('saldo', 'tokens').replace('R$', 'tokens')
            return f"[ADMIN] {base_message}"
        
        elif user_type == 'user':
            # Usuários veem mensagens amigáveis em R$
            if 'token' in base_message.lower():
                return base_message.replace('tokens', 'saldo').replace('token', 'saldo')
            return base_message
        
        else:
            # Visitantes veem mensagens genéricas
            return base_message
    
    @staticmethod
    def validate_balance(amount, user_balance, user_type=None):
        """Validar saldo suficiente com mensagem personalizada"""
        try:
            amount = Decimal(str(amount))
            user_balance = Decimal(str(user_balance))
            
            if amount <= 0:
                return False, ValidationService.format_error_message(
                    "O valor deve ser maior que zero.", user_type
                )
            
            if user_balance < amount:
                if user_type == 'admin':
                    return False, f"Tokens insuficientes. Disponível: {user_balance} tokens, necessário: {amount} tokens."
                else:
                    return False, f"Saldo insuficiente. Disponível: R$ {user_balance:,.2f}, necessário: R$ {amount:,.2f}."
            
            return True, "Saldo suficiente."
            
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"Erro na validação de saldo: {e}")
            return False, ValidationService.format_error_message(
                "Valor inválido fornecido.", user_type
            )
    
    @staticmethod
    def validate_cpf(cpf):
        """Validar CPF brasileiro"""
        if not cpf:
            return False, "CPF é obrigatório."
        
        # Remover caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        # Verificar se tem 11 dígitos
        if len(cpf) != 11:
            return False, "CPF deve ter 11 dígitos."
        
        # Verificar se não são todos iguais
        if cpf == cpf[0] * 11:
            return False, "CPF inválido."
        
        # Validar dígitos verificadores
        def calculate_digit(cpf_partial):
            sum_val = sum(int(cpf_partial[i]) * (len(cpf_partial) + 1 - i) for i in range(len(cpf_partial)))
            remainder = sum_val % 11
            return 0 if remainder < 2 else 11 - remainder
        
        if int(cpf[9]) != calculate_digit(cpf[:9]):
            return False, "CPF inválido."
        
        if int(cpf[10]) != calculate_digit(cpf[:10]):
            return False, "CPF inválido."
        
        return True, "CPF válido."
    
    @staticmethod
    def validate_phone(phone):
        """Validar telefone brasileiro"""
        if not phone:
            return True, "Telefone é opcional."  # Campo opcional
        
        # Remover caracteres não numéricos
        phone_clean = re.sub(r'[^0-9]', '', phone)
        
        # Verificar formato brasileiro (10 ou 11 dígitos)
        if len(phone_clean) not in [10, 11]:
            return False, "Telefone deve ter 10 ou 11 dígitos (com DDD)."
        
        # Verificar se começa com DDD válido
        ddd = phone_clean[:2]
        valid_ddds = ['11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
                      '21', '22', '24',  # RJ/ES
                      '27', '28',  # ES
                      '31', '32', '33', '34', '35', '37', '38',  # MG
                      '41', '42', '43', '44', '45', '46',  # PR/SC
                      '47', '48', '49',  # SC
                      '51', '53', '54', '55',  # RS
                      '61',  # DF/GO/TO
                      '62', '64',  # GO/TO
                      '63',  # TO
                      '65', '66',  # MT/MS
                      '67',  # MS
                      '68',  # AC
                      '69',  # RO/AC
                      '71', '73', '74', '75', '77',  # BA/SE
                      '79',  # SE
                      '81', '87',  # PE/AL
                      '82',  # AL
                      '83',  # PB
                      '84',  # RN
                      '85', '88',  # CE
                      '86', '89',  # PI
                      '91', '93', '94',  # PA/AM
                      '92', '97',  # AM/RR
                      '95',  # RR
                      '96',  # AP
                      '98', '99']  # MA
        
        if ddd not in valid_ddds:
            return False, "DDD inválido."
        
        return True, "Telefone válido."
    
    @staticmethod
    def validate_email(email):
        """Validar formato de email"""
        if not email:
            return False, "Email é obrigatório."
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "Formato de email inválido."
        
        if len(email) > 120:
            return False, "Email muito longo (máximo 120 caracteres)."
        
        return True, "Email válido."
    
    @staticmethod
    def validate_password(password, confirm_password=None):
        """Validar senha com critérios de segurança"""
        if not password:
            return False, "Senha é obrigatória."
        
        if len(password) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres."
        
        if len(password) > 128:
            return False, "Senha muito longa (máximo 128 caracteres)."
        
        # Verificar se tem pelo menos uma letra e um número
        if not re.search(r'[a-zA-Z]', password):
            return False, "Senha deve conter pelo menos uma letra."
        
        if not re.search(r'[0-9]', password):
            return False, "Senha deve conter pelo menos um número."
        
        # Verificar confirmação se fornecida
        if confirm_password is not None and password != confirm_password:
            return False, "Senhas não coincidem."
        
        return True, "Senha válida."
    
    @staticmethod
    def validate_order_value(value, user_type=None):
        """Validar valor de ordem de serviço"""
        try:
            value = Decimal(str(value))
            
            if value <= 0:
                return False, ValidationService.format_error_message(
                    "O valor deve ser maior que zero.", user_type
                )
            
            if value < Decimal('1.00'):
                if user_type == 'admin':
                    return False, "Valor mínimo: 1 token."
                else:
                    return False, "Valor mínimo: R$ 1,00."
            
            if value > Decimal('100000.00'):
                if user_type == 'admin':
                    return False, "Valor máximo: 100.000 tokens."
                else:
                    return False, "Valor máximo: R$ 100.000,00."
            
            return True, "Valor válido."
            
        except (InvalidOperation, ValueError, TypeError):
            return False, ValidationService.format_error_message(
                "Valor inválido fornecido.", user_type
            )
    
    @staticmethod
    def validate_database_connection():
        """Validar conexão com banco de dados"""
        try:
            from models import db
            from sqlalchemy import text
            # Tentar uma query simples
            db.session.execute(text('SELECT 1'))
            return True, "Conexão com banco de dados OK."
        except Exception as e:
            logger.error(f"Erro de conexão com banco de dados: {e}")
            return False, "Erro de conexão com banco de dados. Tente novamente em alguns minutos."
    
    @staticmethod
    def validate_tokenomics_operation(operation_type, amount, user_balance, admin_balance=None, user_type=None):
        """Validar operações específicas de tokenomics"""
        if user_type is None:
            user_type = ValidationService.get_user_type()
        
        try:
            amount = Decimal(str(amount))
            user_balance = Decimal(str(user_balance))
            
            if operation_type == 'purchase':
                # Validar compra de tokens
                if user_type == 'admin':
                    return True, "Admin pode criar tokens livremente."
                else:
                    # Usuário comprando tokens do admin
                    return ValidationService.validate_balance(amount, user_balance, user_type)
            
            elif operation_type == 'withdrawal':
                # Validar saque
                if amount < Decimal('10.00'):
                    if user_type == 'admin':
                        return False, "Saque mínimo: 10 tokens."
                    else:
                        return False, "Saque mínimo: R$ 10,00."
                
                return ValidationService.validate_balance(amount, user_balance, user_type)
            
            elif operation_type == 'transfer':
                # Validar transferência
                if amount < Decimal('1.00'):
                    if user_type == 'admin':
                        return False, "Transferência mínima: 1 token."
                    else:
                        return False, "Transferência mínima: R$ 1,00."
                
                return ValidationService.validate_balance(amount, user_balance, user_type)
            
            elif operation_type == 'escrow':
                # Validar bloqueio em escrow
                return ValidationService.validate_balance(amount, user_balance, user_type)
            
            else:
                return False, "Tipo de operação inválido."
                
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"Erro na validação de tokenomics: {e}")
            return False, ValidationService.format_error_message(
                "Erro na validação da operação.", user_type
            )
    
    @staticmethod
    def log_validation_error(validation_type, error_message, context=None):
        """Log de erros de validação para auditoria"""
        user_context = {
            'user_type': ValidationService.get_user_type(),
            'validation_type': validation_type,
            'error_message': error_message,
            'context': context or {}
        }
        
        # Adicionar informações de sessão e request se disponíveis
        if has_request_context():
            try:
                user_context.update({
                    'admin_id': session.get('admin_id'),
                    'user_id': session.get('user_id'),
                    'ip': request.remote_addr if request else 'N/A'
                })
            except RuntimeError:
                user_context.update({
                    'admin_id': 'N/A',
                    'user_id': 'N/A',
                    'ip': 'N/A'
                })
        else:
            user_context.update({
                'admin_id': 'N/A',
                'user_id': 'N/A',
                'ip': 'N/A'
            })
        
        logger.warning(f"Erro de validação: {validation_type} - {error_message} | Contexto: {user_context}")
    
    @staticmethod
    def get_form_errors_formatted(form, user_type=None):
        """Formatar erros de formulário baseado no tipo de usuário"""
        if user_type is None:
            user_type = ValidationService.get_user_type()
        
        formatted_errors = {}
        
        for field_name, errors in form.errors.items():
            formatted_errors[field_name] = []
            for error in errors:
                formatted_error = ValidationService.format_error_message(error, user_type)
                formatted_errors[field_name].append(formatted_error)
        
        return formatted_errors