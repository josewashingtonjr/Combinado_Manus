#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import os
from app import app, db, init_db
from models import User, AdminUser
from services.validation_service import ValidationService
from flask import session
from decimal import Decimal

class TestValidationService:
    """Testes para o serviço de validações e mensagens personalizadas"""
    
    @pytest.fixture
    def client(self):
        """Configurar cliente de teste"""
        # Criar banco de dados temporário
        db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                init_db()
                yield client
        
        os.close(db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_get_user_type_admin(self, client):
        """Testar detecção de tipo de usuário - admin"""
        with client.session_transaction() as sess:
            sess['admin_id'] = 1
            sess['user_id'] = None
        
        with app.app_context():
            user_type = ValidationService.get_user_type()
            assert user_type == 'admin'
    
    def test_get_user_type_user(self, client):
        """Testar detecção de tipo de usuário - usuário regular"""
        with client.session_transaction() as sess:
            sess['admin_id'] = None
            sess['user_id'] = 1
        
        with app.app_context():
            user_type = ValidationService.get_user_type()
            assert user_type == 'user'
    
    def test_get_user_type_guest(self, client):
        """Testar detecção de tipo de usuário - visitante"""
        with client.session_transaction() as sess:
            sess.clear()
        
        with app.app_context():
            user_type = ValidationService.get_user_type()
            assert user_type == 'guest'
    
    def test_format_error_message_admin(self, client):
        """Testar formatação de mensagem para admin"""
        message = "Saldo insuficiente: R$ 100,00"
        formatted = ValidationService.format_error_message(message, 'admin')
        
        assert 'tokens' in formatted
        assert 'R$' not in formatted
        assert '[ADMIN]' in formatted
    
    def test_format_error_message_user(self, client):
        """Testar formatação de mensagem para usuário"""
        message = "Tokens insuficientes: 100 tokens"
        formatted = ValidationService.format_error_message(message, 'user')
        
        assert 'saldo' in formatted
        assert 'tokens' not in formatted
    
    def test_validate_balance_sufficient(self, client):
        """Testar validação de saldo suficiente"""
        is_valid, message = ValidationService.validate_balance(50, 100, 'user')
        
        assert is_valid == True
        assert "suficiente" in message
    
    def test_validate_balance_insufficient_user(self, client):
        """Testar validação de saldo insuficiente para usuário"""
        is_valid, message = ValidationService.validate_balance(150, 100, 'user')
        
        assert is_valid == False
        assert "R$" in message
        assert "insuficiente" in message
        assert "100" in message
        assert "150" in message
    
    def test_validate_balance_insufficient_admin(self, client):
        """Testar validação de saldo insuficiente para admin"""
        is_valid, message = ValidationService.validate_balance(150, 100, 'admin')
        
        assert is_valid == False
        assert "tokens" in message
        assert "insuficientes" in message
        assert "100" in message
        assert "150" in message
    
    def test_validate_balance_invalid_amount(self, client):
        """Testar validação com valor inválido"""
        is_valid, message = ValidationService.validate_balance(-10, 100, 'user')
        
        assert is_valid == False
        assert "maior que zero" in message
    
    def test_validate_cpf_valid(self, client):
        """Testar validação de CPF válido"""
        # CPF válido: 11144477735
        is_valid, message = ValidationService.validate_cpf("111.444.777-35")
        
        assert is_valid == True
        assert "válido" in message
    
    def test_validate_cpf_invalid_format(self, client):
        """Testar validação de CPF com formato inválido"""
        is_valid, message = ValidationService.validate_cpf("123456789")
        
        assert is_valid == False
        assert "11 dígitos" in message
    
    def test_validate_cpf_invalid_digits(self, client):
        """Testar validação de CPF com dígitos inválidos"""
        is_valid, message = ValidationService.validate_cpf("11111111111")
        
        assert is_valid == False
        assert "inválido" in message
    
    def test_validate_cpf_empty(self, client):
        """Testar validação de CPF vazio"""
        is_valid, message = ValidationService.validate_cpf("")
        
        assert is_valid == False
        assert "obrigatório" in message
    
    def test_validate_phone_valid(self, client):
        """Testar validação de telefone válido"""
        is_valid, message = ValidationService.validate_phone("11987654321")
        
        assert is_valid == True
        assert "válido" in message
    
    def test_validate_phone_invalid_ddd(self, client):
        """Testar validação de telefone com DDD inválido"""
        is_valid, message = ValidationService.validate_phone("00987654321")
        
        assert is_valid == False
        assert "DDD inválido" in message
    
    def test_validate_phone_invalid_length(self, client):
        """Testar validação de telefone com tamanho inválido"""
        is_valid, message = ValidationService.validate_phone("119876543")
        
        assert is_valid == False
        assert "10 ou 11 dígitos" in message
    
    def test_validate_phone_empty_optional(self, client):
        """Testar validação de telefone vazio (campo opcional)"""
        is_valid, message = ValidationService.validate_phone("")
        
        assert is_valid == True
        assert "opcional" in message
    
    def test_validate_email_valid(self, client):
        """Testar validação de email válido"""
        is_valid, message = ValidationService.validate_email("teste@exemplo.com")
        
        assert is_valid == True
        assert "válido" in message
    
    def test_validate_email_invalid_format(self, client):
        """Testar validação de email com formato inválido"""
        is_valid, message = ValidationService.validate_email("email_invalido")
        
        assert is_valid == False
        assert "inválido" in message
    
    def test_validate_email_empty(self, client):
        """Testar validação de email vazio"""
        is_valid, message = ValidationService.validate_email("")
        
        assert is_valid == False
        assert "obrigatório" in message
    
    def test_validate_email_too_long(self, client):
        """Testar validação de email muito longo"""
        long_email = "a" * 110 + "@exemplo.com"
        is_valid, message = ValidationService.validate_email(long_email)
        
        assert is_valid == False
        assert "muito longo" in message
    
    def test_validate_password_valid(self, client):
        """Testar validação de senha válida"""
        is_valid, message = ValidationService.validate_password("senha123", "senha123")
        
        assert is_valid == True
        assert "válida" in message
    
    def test_validate_password_too_short(self, client):
        """Testar validação de senha muito curta"""
        is_valid, message = ValidationService.validate_password("123")
        
        assert is_valid == False
        assert "6 caracteres" in message
    
    def test_validate_password_no_letter(self, client):
        """Testar validação de senha sem letra"""
        is_valid, message = ValidationService.validate_password("123456")
        
        assert is_valid == False
        assert "letra" in message
    
    def test_validate_password_no_number(self, client):
        """Testar validação de senha sem número"""
        is_valid, message = ValidationService.validate_password("senhasenha")
        
        assert is_valid == False
        assert "número" in message
    
    def test_validate_password_mismatch(self, client):
        """Testar validação de senhas que não coincidem"""
        is_valid, message = ValidationService.validate_password("senha123", "senha456")
        
        assert is_valid == False
        assert "não coincidem" in message
    
    def test_validate_order_value_valid_user(self, client):
        """Testar validação de valor de ordem válido para usuário"""
        is_valid, message = ValidationService.validate_order_value(50.00, 'user')
        
        assert is_valid == True
        assert "válido" in message
    
    def test_validate_order_value_too_low_user(self, client):
        """Testar validação de valor muito baixo para usuário"""
        is_valid, message = ValidationService.validate_order_value(0.50, 'user')
        
        assert is_valid == False
        assert "R$ 1,00" in message
    
    def test_validate_order_value_too_low_admin(self, client):
        """Testar validação de valor muito baixo para admin"""
        is_valid, message = ValidationService.validate_order_value(0.50, 'admin')
        
        assert is_valid == False
        assert "1 token" in message
    
    def test_validate_order_value_too_high_user(self, client):
        """Testar validação de valor muito alto para usuário"""
        is_valid, message = ValidationService.validate_order_value(200000.00, 'user')
        
        assert is_valid == False
        assert "R$ 100.000,00" in message
    
    def test_validate_order_value_too_high_admin(self, client):
        """Testar validação de valor muito alto para admin"""
        is_valid, message = ValidationService.validate_order_value(200000.00, 'admin')
        
        assert is_valid == False
        assert "100.000 tokens" in message
    
    def test_validate_tokenomics_purchase_admin(self, client):
        """Testar validação de compra/criação de tokens para admin"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'purchase', 1000, 0, user_type='admin'
        )
        
        # Admin pode criar tokens livremente
        assert is_valid == True
        assert "livremente" in message
    
    def test_validate_tokenomics_withdrawal_minimum(self, client):
        """Testar validação de saque com valor mínimo"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'withdrawal', 5, 100, user_type='user'
        )
        
        assert is_valid == False
        assert "R$ 10,00" in message
    
    def test_validate_tokenomics_withdrawal_minimum_admin(self, client):
        """Testar validação de saque com valor mínimo para admin"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'withdrawal', 5, 100, user_type='admin'
        )
        
        assert is_valid == False
        assert "10 tokens" in message
    
    def test_validate_tokenomics_transfer_minimum_user(self, client):
        """Testar validação de transferência com valor mínimo para usuário"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'transfer', 0.50, 100, user_type='user'
        )
        
        assert is_valid == False
        assert "R$ 1,00" in message
    
    def test_validate_tokenomics_transfer_minimum_admin(self, client):
        """Testar validação de transferência com valor mínimo para admin"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'transfer', 0.50, 100, user_type='admin'
        )
        
        assert is_valid == False
        assert "1 token" in message
    
    def test_validate_tokenomics_invalid_operation(self, client):
        """Testar validação com tipo de operação inválido"""
        is_valid, message = ValidationService.validate_tokenomics_operation(
            'invalid_operation', 100, 100
        )
        
        assert is_valid == False
        assert "inválido" in message
    
    def test_validate_database_connection_success(self, client):
        """Testar validação de conexão com banco bem-sucedida"""
        with app.app_context():
            is_valid, message = ValidationService.validate_database_connection()
            
            assert is_valid == True
            assert "OK" in message
    
    def test_terminology_consistency_across_validations(self, client):
        """Testar consistência de terminologia em diferentes validações"""
        # Teste para admin
        admin_balance_msg = ValidationService.validate_balance(150, 100, 'admin')[1]
        admin_order_msg = ValidationService.validate_order_value(0.50, 'admin')[1]
        
        assert 'tokens' in admin_balance_msg
        assert 'tokens' in admin_order_msg
        assert 'R$' not in admin_balance_msg
        assert 'R$' not in admin_order_msg
        
        # Teste para usuário
        user_balance_msg = ValidationService.validate_balance(150, 100, 'user')[1]
        user_order_msg = ValidationService.validate_order_value(0.50, 'user')[1]
        
        assert 'R$' in user_balance_msg
        assert 'R$' in user_order_msg
        assert 'tokens' not in user_balance_msg
        assert 'tokens' not in user_order_msg

if __name__ == '__main__':
    pytest.main([__file__, '-v'])