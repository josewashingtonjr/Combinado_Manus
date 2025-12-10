#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import pytest
import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Wallet
from services.balance_validator import BalanceValidator, BalanceStatus
from services.wallet_service import WalletService

@pytest.fixture
def app():
    """Fixture para criar app de teste"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client_user(app):
    """Fixture para criar usuário cliente de teste"""
    with app.app_context():
        user = User(
            email='cliente@test.com',
            nome='Cliente Teste',
            cpf='12345678901',
            roles='cliente'
        )
        user.set_password('senha123')
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira com saldo inicial
        WalletService.ensure_user_has_wallet(user.id)
        WalletService.credit_wallet(user.id, Decimal('100.00'), 'Saldo inicial de teste')
        
        return user

def test_calculate_required_balance(app):
    """Testa o cálculo do saldo necessário"""
    with app.app_context():
        # Teste com valor válido
        proposed_value = Decimal('50.00')
        required = BalanceValidator.calculate_required_balance(proposed_value)
        
        # Deve ser valor proposto + taxa de contestação (R$ 10,00)
        expected = proposed_value + Decimal('10.00')
        assert required == expected
        
        # Teste com valor zero - deve dar erro
        with pytest.raises(ValueError, match="Valor proposto deve ser positivo"):
            BalanceValidator.calculate_required_balance(Decimal('0.00'))
        
        # Teste com valor negativo - deve dar erro
        with pytest.raises(ValueError, match="Valor proposto deve ser positivo"):
            BalanceValidator.calculate_required_balance(Decimal('-10.00'))

def test_check_sufficiency_with_sufficient_balance(app, client_user):
    """Testa verificação de suficiência com saldo suficiente"""
    with app.app_context():
        required_amount = Decimal('50.00')  # Cliente tem R$ 100,00
        
        status = BalanceValidator.check_sufficiency(client_user.id, required_amount)
        
        assert isinstance(status, BalanceStatus)
        assert status.is_sufficient == True
        assert status.current_balance == Decimal('100.00')
        assert status.required_amount == required_amount
        assert status.shortfall == Decimal('0.00')
        assert status.suggested_top_up == Decimal('0.00')

def test_check_sufficiency_with_insufficient_balance(app, client_user):
    """Testa verificação de suficiência com saldo insuficiente"""
    with app.app_context():
        required_amount = Decimal('150.00')  # Cliente tem apenas R$ 100,00
        
        status = BalanceValidator.check_sufficiency(client_user.id, required_amount)
        
        assert isinstance(status, BalanceStatus)
        assert status.is_sufficient == False
        assert status.current_balance == Decimal('100.00')
        assert status.required_amount == required_amount
        assert status.shortfall == Decimal('50.00')
        assert status.suggested_top_up > Decimal('50.00')  # Deve incluir margem

def test_suggest_top_up_amount(app):
    """Testa sugestão de valor para recarga"""
    with app.app_context():
        # Caso 1: Saldo suficiente - não precisa recarregar
        current = Decimal('100.00')
        required = Decimal('80.00')
        suggestion = BalanceValidator.suggest_top_up_amount(current, required)
        assert suggestion == Decimal('0.00')
        
        # Caso 2: Déficit pequeno - deve arredondar para múltiplos de 10
        current = Decimal('45.00')
        required = Decimal('50.00')  # Déficit de R$ 5,00
        suggestion = BalanceValidator.suggest_top_up_amount(current, required)
        # Déficit R$ 5,00 + margem R$ 5,00 = R$ 10,00 → arredondado para R$ 10,00
        assert suggestion == Decimal('10.00')
        
        # Caso 3: Déficit maior
        current = Decimal('20.00')
        required = Decimal('100.00')  # Déficit de R$ 80,00
        suggestion = BalanceValidator.suggest_top_up_amount(current, required)
        # Déficit R$ 80,00 + margem R$ 8,00 = R$ 88,00 → arredondado para R$ 90,00
        assert suggestion == Decimal('90.00')

def test_validate_proposal_balance(app, client_user):
    """Testa validação completa de proposta"""
    with app.app_context():
        # Caso 1: Proposta que o cliente pode aceitar
        proposed_value = Decimal('80.00')  # + R$ 10,00 taxa = R$ 90,00 total
        
        status = BalanceValidator.validate_proposal_balance(client_user.id, proposed_value)
        
        assert status.is_sufficient == True
        assert status.required_amount == Decimal('90.00')  # 80 + 10 taxa
        assert status.current_balance == Decimal('100.00')
        
        # Caso 2: Proposta que excede o saldo
        proposed_value = Decimal('100.00')  # + R$ 10,00 taxa = R$ 110,00 total
        
        status = BalanceValidator.validate_proposal_balance(client_user.id, proposed_value)
        
        assert status.is_sufficient == False
        assert status.required_amount == Decimal('110.00')
        assert status.shortfall == Decimal('10.00')

def test_reserve_funds_success(app, client_user):
    """Testa reserva de fundos com sucesso"""
    with app.app_context():
        amount_to_reserve = Decimal('50.00')
        
        result = BalanceValidator.reserve_funds(
            client_user.id, 
            amount_to_reserve, 
            "Teste de reserva"
        )
        
        assert result['success'] == True
        assert result['reserved_amount'] == amount_to_reserve
        assert result['new_balance'] == Decimal('50.00')  # 100 - 50
        assert result['new_escrow_balance'] == amount_to_reserve

def test_reserve_funds_insufficient_balance(app, client_user):
    """Testa reserva de fundos com saldo insuficiente"""
    with app.app_context():
        amount_to_reserve = Decimal('150.00')  # Mais que os R$ 100,00 disponíveis
        
        with pytest.raises(ValueError, match="Saldo insuficiente para reserva"):
            BalanceValidator.reserve_funds(
                client_user.id, 
                amount_to_reserve, 
                "Teste de reserva impossível"
            )

def test_get_balance_summary(app, client_user):
    """Testa obtenção de resumo de saldo"""
    with app.app_context():
        summary = BalanceValidator.get_balance_summary(client_user.id)
        
        assert summary['client_id'] == client_user.id
        assert summary['balance'] == Decimal('100.00')
        assert summary['escrow_balance'] == Decimal('0.00')
        assert summary['total_balance'] == Decimal('100.00')
        assert summary['available_for_proposals'] == Decimal('100.00')
        assert summary['contestation_fee'] == Decimal('10.00')
        assert 'error' not in summary

def test_get_contestation_fee(app):
    """Testa obtenção da taxa de contestação"""
    with app.app_context():
        fee = BalanceValidator.get_contestation_fee()
        assert isinstance(fee, Decimal)
        assert fee == Decimal('10.00')  # Valor padrão

if __name__ == '__main__':
    pytest.main([__file__, '-v'])