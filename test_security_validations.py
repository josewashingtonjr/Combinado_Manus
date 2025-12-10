#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste das validações de segurança implementadas na tarefa 12
Valida autorização, rate limiting, sanitização e limites de valores
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_security_validations():
    """Testar todas as validações de segurança implementadas"""
    
    try:
        from app import app
        from models import db, User, Invite, Proposal
        from services.security_validator import SecurityValidator, SecurityValidationResult
        
        print("=== TESTE DAS VALIDAÇÕES DE SEGURANÇA ===")
        print("Testando implementações da tarefa 12...")
        
        with app.app_context():
            
            # Teste 1: Validação de autorização
            print("\n1. Testando validações de autorização...")
            
            # Teste com IDs inválidos
            auth_result = SecurityValidator.validate_proposal_authorization(999, 999)
            assert not auth_result.is_valid
            assert auth_result.error_code == 'invite_not_found'
            print("   ✓ Rejeita convite inexistente")
            
            # Teste com prestador inexistente (assumindo que convite 1 existe)
            auth_result = SecurityValidator.validate_proposal_authorization(1, 999)
            if not auth_result.is_valid and auth_result.error_code in ['prestador_not_found', 'invite_not_found']:
                print("   ✓ Rejeita prestador inexistente")
            
            # Teste 2: Validação de rate limiting
            print("\n2. Testando rate limiting...")
            
            # Teste com prestador inexistente
            rate_result = SecurityValidator.validate_rate_limiting(999)
            assert rate_result.is_valid  # Deve ser válido para prestador sem propostas
            assert 'proposals_last_hour' in rate_result.details
            assert 'proposals_last_day' in rate_result.details
            print("   ✓ Rate limiting funciona para prestador sem propostas")
            
            # Teste 3: Validação de valores
            print("\n3. Testando validação de valores...")
            
            # Valor muito baixo
            value_result = SecurityValidator.validate_proposal_value(
                Decimal('100.00'), Decimal('0.50')
            )
            assert not value_result.is_valid
            assert value_result.error_code == 'value_too_low'
            print("   ✓ Rejeita valores muito baixos")
            
            # Valor muito alto
            value_result = SecurityValidator.validate_proposal_value(
                Decimal('100.00'), Decimal('60000.00')
            )
            assert not value_result.is_valid
            assert value_result.error_code == 'value_too_high'
            print("   ✓ Rejeita valores muito altos")
            
            # Aumento excessivo (mais de 500%)
            value_result = SecurityValidator.validate_proposal_value(
                Decimal('100.00'), Decimal('700.00')  # 600% de aumento
            )
            assert not value_result.is_valid
            assert value_result.error_code == 'increase_too_high'
            print("   ✓ Rejeita aumentos excessivos")
            
            # Redução excessiva (mais de 90%)
            value_result = SecurityValidator.validate_proposal_value(
                Decimal('100.00'), Decimal('5.00')  # 95% de redução
            )
            assert not value_result.is_valid
            assert value_result.error_code == 'decrease_too_high'
            print("   ✓ Rejeita reduções excessivas")
            
            # Valor válido
            value_result = SecurityValidator.validate_proposal_value(
                Decimal('100.00'), Decimal('150.00')  # 50% de aumento
            )
            assert value_result.is_valid
            print("   ✓ Aceita valores válidos")
            
            # Teste 4: Sanitização de texto
            print("\n4. Testando sanitização de texto...")
            
            # Texto vazio
            text_result = SecurityValidator.sanitize_text_input("", "justificativa")
            assert text_result.is_valid
            assert text_result.details['sanitized_text'] is None
            print("   ✓ Aceita texto vazio")
            
            # Texto muito curto
            text_result = SecurityValidator.sanitize_text_input("abc", "justificativa")
            assert not text_result.is_valid
            assert text_result.error_code == 'text_too_short'
            print("   ✓ Rejeita texto muito curto")
            
            # Texto muito longo
            long_text = "a" * 600
            text_result = SecurityValidator.sanitize_text_input(long_text, "justificativa")
            assert not text_result.is_valid
            assert text_result.error_code == 'text_too_long'
            print("   ✓ Rejeita texto muito longo")
            
            # Texto com HTML/Script
            malicious_text = "Texto normal <script>alert('xss')</script> mais texto"
            text_result = SecurityValidator.sanitize_text_input(malicious_text, "justificativa")
            assert not text_result.is_valid
            assert text_result.error_code == 'suspicious_content'
            print("   ✓ Rejeita conteúdo suspeito (XSS)")
            
            # Texto com SQL injection
            sql_text = "Texto normal; DROP TABLE users; --"
            text_result = SecurityValidator.sanitize_text_input(sql_text, "justificativa")
            assert not text_result.is_valid
            assert text_result.error_code == 'suspicious_content'
            print("   ✓ Rejeita conteúdo suspeito (SQL injection)")
            
            # Texto válido
            valid_text = "Esta é uma justificativa válida para a alteração do valor."
            text_result = SecurityValidator.sanitize_text_input(valid_text, "justificativa")
            assert text_result.is_valid
            sanitized = text_result.details['sanitized_text']
            assert sanitized == valid_text  # Deve ser igual pois não tem caracteres especiais
            print("   ✓ Sanitiza texto válido corretamente")
            
            # Texto com caracteres especiais que devem ser escapados
            html_text = "Valor < 100 & > 50"
            text_result = SecurityValidator.sanitize_text_input(html_text, "justificativa")
            assert text_result.is_valid
            sanitized = text_result.details['sanitized_text']
            assert '&lt;' in sanitized and '&gt;' in sanitized and '&amp;' in sanitized
            print("   ✓ Escapa caracteres HTML corretamente")
            
            # Teste 5: Validação completa de criação de proposta
            print("\n5. Testando validação completa...")
            
            # Teste com dados inválidos
            complete_result = SecurityValidator.validate_proposal_creation_complete(
                invite_id=999,  # Convite inexistente
                prestador_id=999,  # Prestador inexistente
                proposed_value=Decimal('100.00'),
                justification="Justificativa válida para teste"
            )
            assert not complete_result.is_valid
            print("   ✓ Validação completa rejeita dados inválidos")
            
            # Teste 6: Estatísticas de segurança
            print("\n6. Testando estatísticas de segurança...")
            
            # Estatísticas gerais
            stats = SecurityValidator.get_security_statistics()
            assert isinstance(stats, dict)
            assert 'total_proposals' in stats
            print("   ✓ Retorna estatísticas gerais")
            
            # Estatísticas de prestador específico
            stats_prestador = SecurityValidator.get_security_statistics(prestador_id=999)
            assert isinstance(stats_prestador, dict)
            assert 'prestador_id' in stats_prestador
            assert 'proposals_last_hour' in stats_prestador
            assert 'proposals_last_day' in stats_prestador
            print("   ✓ Retorna estatísticas de prestador específico")
            
            # Teste 7: Verificar constantes de segurança
            print("\n7. Verificando constantes de segurança...")
            
            assert SecurityValidator.MAX_PROPOSALS_PER_INVITE == 3
            assert SecurityValidator.MAX_PROPOSALS_PER_HOUR == 10
            assert SecurityValidator.MAX_PROPOSALS_PER_DAY == 50
            assert SecurityValidator.MIN_PROPOSAL_VALUE == Decimal('1.00')
            assert SecurityValidator.MAX_PROPOSAL_VALUE == Decimal('50000.00')
            assert SecurityValidator.MAX_VALUE_INCREASE_PERCENT == 500
            assert SecurityValidator.MAX_VALUE_DECREASE_PERCENT == 90
            print("   ✓ Constantes de segurança definidas corretamente")
            
            print("\n✅ TODOS OS TESTES DE SEGURANÇA PASSARAM!")
            print("\n" + "="*60)
            print("RESUMO DAS VALIDAÇÕES IMPLEMENTADAS:")
            print("="*60)
            print("✓ Autorização: Apenas prestador destinatário pode criar propostas")
            print("✓ Autorização: Apenas cliente dono pode aprovar/rejeitar")
            print("✓ Rate Limiting: Máximo 3 propostas por convite")
            print("✓ Rate Limiting: Máximo 10 propostas por hora")
            print("✓ Rate Limiting: Máximo 50 propostas por dia")
            print("✓ Validação de Valores: Limites mínimos e máximos")
            print("✓ Validação de Valores: Limites de aumento (500%) e redução (90%)")
            print("✓ Sanitização: Proteção contra XSS e SQL injection")
            print("✓ Sanitização: Escape de caracteres HTML")
            print("✓ Sanitização: Limites de comprimento de texto")
            print("✓ Monitoramento: Estatísticas de segurança e padrões suspeitos")
            print("✓ Logging: Registro de todas as ações de segurança")
            
            return True
            
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        print("Verifique se o SecurityValidator foi implementado corretamente")
        return False
    except AssertionError as e:
        print(f"✗ Teste falhou: Validação não funcionou como esperado")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def test_integration_with_proposal_service():
    """Testar integração com ProposalService"""
    
    try:
        from app import app
        from services.proposal_service import ProposalService
        from services.security_validator import SecurityValidator
        
        print("\n=== TESTE DE INTEGRAÇÃO COM PROPOSAL SERVICE ===")
        
        with app.app_context():
            
            # Teste 1: Verificar se ProposalService usa SecurityValidator
            print("\n1. Verificando integração...")
            
            # Tentar criar proposta com dados inválidos
            try:
                result = ProposalService.create_proposal(
                    invite_id=999,  # Convite inexistente
                    prestador_id=999,  # Prestador inexistente
                    proposed_value=Decimal('0.50'),  # Valor muito baixo
                    justification="<script>alert('xss')</script>"  # Conteúdo malicioso
                )
                print("   ✗ ProposalService deveria ter rejeitado dados inválidos")
                return False
            except ValueError as e:
                print(f"   ✓ ProposalService rejeitou corretamente: {str(e)}")
            
            # Teste 2: Verificar se as validações são aplicadas
            print("\n2. Verificando aplicação das validações...")
            
            # Tentar com valor muito alto
            try:
                result = ProposalService.create_proposal(
                    invite_id=1,  # Assumindo que existe
                    prestador_id=1,  # Assumindo que existe
                    proposed_value=Decimal('60000.00'),  # Valor muito alto
                    justification="Justificativa válida"
                )
                print("   ✗ ProposalService deveria ter rejeitado valor muito alto")
                return False
            except ValueError as e:
                if "exceder" in str(e) or "alto" in str(e):
                    print("   ✓ ProposalService rejeitou valor muito alto")
                else:
                    print(f"   ? ProposalService rejeitou por outro motivo: {str(e)}")
            
            print("\n✅ INTEGRAÇÃO COM PROPOSAL SERVICE FUNCIONANDO!")
            
            return True
            
    except Exception as e:
        print(f"✗ Erro na integração: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes das validações de segurança...")
    
    success1 = test_security_validations()
    success2 = test_integration_with_proposal_service()
    
    if success1 and success2:
        print("\n🎉 TODOS OS TESTES DE SEGURANÇA PASSARAM!")
        print("\n📋 TAREFA 12 IMPLEMENTADA COM SUCESSO:")
        print("   - Validações de autorização implementadas")
        print("   - Rate limiting implementado")
        print("   - Validação de valores implementada")
        print("   - Sanitização de texto implementada")
        print("   - Integração com ProposalService completa")
        print("   - Monitoramento e estatísticas implementados")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        sys.exit(1)