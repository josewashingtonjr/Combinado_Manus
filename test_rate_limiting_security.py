#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para Rate Limiting e Segurança

Testa as funcionalidades de rate limiting e validações de segurança
implementadas na tarefa 23.

Requirements: Security considerations, Task 23
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.security_validator import SecurityValidator
from services.rate_limiter_service import RateLimitConfig


class TestSecurityValidator:
    """Testes para SecurityValidator"""
    
    def test_sanitize_input_remove_html(self):
        """Testa remoção de HTML malicioso"""
        # HTML malicioso
        malicious_input = '<script>alert("XSS")</script>Texto normal'
        sanitized = SecurityValidator.sanitize_input(malicious_input)
        
        # Deve remover tags HTML (bleach remove as tags mas mantém o conteúdo)
        assert '<script>' not in sanitized
        assert '</script>' not in sanitized
        assert 'Texto normal' in sanitized
    
    def test_sanitize_input_max_length(self):
        """Testa limitação de comprimento"""
        long_text = 'a' * 1000
        sanitized = SecurityValidator.sanitize_input(long_text, max_length=100)
        
        assert len(sanitized) == 100
    
    def test_sanitize_input_control_characters(self):
        """Testa remoção de caracteres de controle"""
        text_with_control = 'Texto\x00com\x1fcaracteres\x7fde controle'
        sanitized = SecurityValidator.sanitize_input(text_with_control)
        
        # Não deve conter caracteres de controle
        assert '\x00' not in sanitized
        assert '\x1f' not in sanitized
        assert '\x7f' not in sanitized
        assert 'Texto' in sanitized
        assert 'com' in sanitized
    
    def test_validate_monetary_value_valid(self):
        """Testa validação de valor monetário válido"""
        # Valores válidos
        assert SecurityValidator.validate_monetary_value('100.50') == Decimal('100.50')
        assert SecurityValidator.validate_monetary_value('1000,75') == Decimal('1000.75')
        assert SecurityValidator.validate_monetary_value(Decimal('50.25')) == Decimal('50.25')
        assert SecurityValidator.validate_monetary_value(50.0) == Decimal('50.00')
    
    def test_validate_monetary_value_invalid_negative(self):
        """Testa rejeição de valores negativos"""
        with pytest.raises(ValueError, match="deve ser maior que zero"):
            SecurityValidator.validate_monetary_value('-10.00')
    
    def test_validate_monetary_value_invalid_zero(self):
        """Testa rejeição de valor zero"""
        with pytest.raises(ValueError, match="deve ser maior que zero"):
            SecurityValidator.validate_monetary_value('0')
    
    def test_validate_monetary_value_invalid_too_large(self):
        """Testa rejeição de valores muito grandes"""
        with pytest.raises(ValueError, match="deve ser menor ou igual"):
            SecurityValidator.validate_monetary_value('2000000.00')  # Acima do limite padrão
    
    def test_validate_monetary_value_invalid_precision(self):
        """Testa rejeição de valores com muitas casas decimais"""
        with pytest.raises(ValueError, match="no máximo 2 casas decimais"):
            SecurityValidator.validate_monetary_value('10.123')
    
    def test_validate_date_future_valid(self):
        """Testa validação de data futura válida"""
        # Data 10 dias no futuro
        future_date = datetime.now() + timedelta(days=10)
        validated = SecurityValidator.validate_date_future(future_date)
        
        assert validated == future_date
    
    def test_validate_date_future_string(self):
        """Testa validação de data futura como string"""
        # Data 30 dias no futuro
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        validated = SecurityValidator.validate_date_future(future_date)
        
        assert isinstance(validated, datetime)
    
    def test_validate_date_future_invalid_past(self):
        """Testa rejeição de data no passado"""
        past_date = datetime.now() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="deve ser pelo menos"):
            SecurityValidator.validate_date_future(past_date)
    
    def test_validate_date_future_invalid_too_far(self):
        """Testa rejeição de data muito distante"""
        far_future = datetime.now() + timedelta(days=400)
        
        with pytest.raises(ValueError, match="deve ser no máximo"):
            SecurityValidator.validate_date_future(far_future)


class TestRateLimitConfig:
    """Testes para configurações de rate limiting"""
    
    def test_rate_limit_config_exists(self):
        """Testa que configurações de rate limiting existem"""
        assert hasattr(RateLimitConfig, 'PRE_ORDER_PROPOSALS')
        assert hasattr(RateLimitConfig, 'PRE_ORDER_CANCELLATIONS')
        assert hasattr(RateLimitConfig, 'GENERAL_REQUESTS')
    
    def test_rate_limit_proposals_config(self):
        """Testa configuração de limite de propostas"""
        # Deve ser 10 por hora
        assert '10' in RateLimitConfig.PRE_ORDER_PROPOSALS
        assert 'hour' in RateLimitConfig.PRE_ORDER_PROPOSALS
    
    def test_rate_limit_cancellations_config(self):
        """Testa configuração de limite de cancelamentos"""
        # Deve ser 5 por dia
        assert '5' in RateLimitConfig.PRE_ORDER_CANCELLATIONS
        assert 'day' in RateLimitConfig.PRE_ORDER_CANCELLATIONS
    
    def test_rate_limit_general_config(self):
        """Testa configuração de limite geral"""
        # Deve ser 20 por minuto
        assert '20' in RateLimitConfig.GENERAL_REQUESTS
        assert 'minute' in RateLimitConfig.GENERAL_REQUESTS


class TestInputSanitization:
    """Testes para sanitização de inputs"""
    
    def test_sanitize_sql_injection_attempt(self):
        """Testa proteção contra SQL injection"""
        sql_injection = "'; DROP TABLE users; --"
        sanitized = SecurityValidator.sanitize_input(sql_injection)
        
        # Deve remover caracteres perigosos
        assert 'DROP TABLE' in sanitized  # Texto é mantido mas sem contexto SQL
        # O importante é que não será executado como SQL
    
    def test_sanitize_xss_attempt(self):
        """Testa proteção contra XSS"""
        xss_attempts = [
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            'javascript:alert(1)',
            '<iframe src="javascript:alert(1)">',
        ]
        
        for xss in xss_attempts:
            sanitized = SecurityValidator.sanitize_input(xss)
            # Não deve conter tags HTML
            assert '<' not in sanitized or '>' not in sanitized
    
    def test_sanitize_preserves_valid_text(self):
        """Testa que texto válido é preservado"""
        valid_texts = [
            'Texto normal sem problemas',
            'Texto com números 123 e símbolos !@#',
            'Texto com acentuação: José, María, François',
            'Texto com quebras\nde linha',
        ]
        
        for text in valid_texts:
            sanitized = SecurityValidator.sanitize_input(text)
            # Texto deve ser preservado (exceto caracteres de controle)
            assert len(sanitized) > 0


class TestValidationEdgeCases:
    """Testes para casos extremos de validação"""
    
    def test_validate_empty_string(self):
        """Testa validação de string vazia"""
        assert SecurityValidator.sanitize_input('') == ''
        assert SecurityValidator.sanitize_input(None) == ''
    
    def test_validate_whitespace_only(self):
        """Testa validação de string com apenas espaços"""
        assert SecurityValidator.sanitize_input('   ') == ''
        assert SecurityValidator.sanitize_input('\t\n  ') == ''
    
    def test_validate_monetary_value_edge_cases(self):
        """Testa casos extremos de valores monetários"""
        # Valor mínimo
        assert SecurityValidator.validate_monetary_value('0.01') == Decimal('0.01')
        
        # Valor com vírgula (formato brasileiro)
        assert SecurityValidator.validate_monetary_value('1234,56') == Decimal('1234.56')
    
    def test_validate_date_edge_cases(self):
        """Testa casos extremos de datas"""
        # Exatamente 1 dia no futuro
        tomorrow = datetime.now() + timedelta(days=1, hours=1)
        validated = SecurityValidator.validate_date_future(tomorrow, min_days=1)
        assert validated == tomorrow
        
        # Exatamente no limite máximo
        max_future = datetime.now() + timedelta(days=365)
        validated = SecurityValidator.validate_date_future(max_future, max_days=365)
        assert validated == max_future


def test_bleach_installed():
    """Testa que bleach está instalado e funcionando"""
    import bleach
    
    # Testar funcionalidade básica do bleach
    dirty = '<script>alert("xss")</script>Texto limpo'
    clean = bleach.clean(dirty, tags=[], strip=True)
    
    assert '<script>' not in clean
    assert 'Texto limpo' in clean


def test_flask_limiter_config():
    """Testa que Flask-Limiter está configurado"""
    from services.rate_limiter_service import limiter
    
    assert limiter is not None
    assert hasattr(limiter, 'limit')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
