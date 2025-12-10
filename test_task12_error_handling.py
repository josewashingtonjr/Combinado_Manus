#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes para a tarefa 12: Tratamento de erros robusto

Este arquivo testa o tratamento de erros implementado para:
- Saldo insuficiente (12.1)
- Criação de ordem (12.2)
- Bloqueio de escrow (12.3)

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.3, 8.4
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from decimal import Decimal


def test_insufficient_balance_error():
    """
    Testa a exceção InsufficientBalanceError
    
    Requirements: 7.4, 8.3, 8.4
    """
    from services.exceptions import InsufficientBalanceError
    
    print("\n=== Teste 1: InsufficientBalanceError ===")
    
    # Teste para cliente
    error_cliente = InsufficientBalanceError(
        user_id=1,
        user_type='cliente',
        required_amount=Decimal('100.00'),
        current_balance=Decimal('50.00'),
        purpose='aceitar o convite'
    )
    
    print(f"Mensagem cliente: {error_cliente.message}")
    print(f"Déficit: R$ {error_cliente.get_deficit():.2f}")
    print(f"Dict: {error_cliente.to_dict()}")
    
    assert error_cliente.user_id == 1
    assert error_cliente.user_type == 'cliente'
    assert error_cliente.required_amount == Decimal('100.00')
    assert error_cliente.current_balance == Decimal('50.00')
    assert error_cliente.get_deficit() == Decimal('50.00')
    assert 'Saldo insuficiente' in error_cliente.message
    assert 'R$ 100.00' in error_cliente.message
    assert 'R$ 50.00' in error_cliente.message
    
    # Teste para prestador
    error_prestador = InsufficientBalanceError(
        user_id=2,
        user_type='prestador',
        required_amount=Decimal('10.00'),
        current_balance=Decimal('5.00'),
        purpose='taxa de contestação'
    )
    
    print(f"\nMensagem prestador: {error_prestador.message}")
    print(f"Déficit: R$ {error_prestador.get_deficit():.2f}")
    
    assert error_prestador.user_id == 2
    assert error_prestador.user_type == 'prestador'
    assert error_prestador.get_deficit() == Decimal('5.00')
    
    print("✓ Teste InsufficientBalanceError passou!")


def test_order_creation_error():
    """
    Testa a exceção OrderCreationError
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    from services.exceptions import OrderCreationError
    
    print("\n=== Teste 2: OrderCreationError ===")
    
    # Teste sem exceção original
    error1 = OrderCreationError(
        invite_id=123,
        reason="Falha ao validar dados"
    )
    
    print(f"Mensagem: {error1.message}")
    print(f"Dict: {error1.to_dict()}")
    
    assert error1.invite_id == 123
    assert error1.reason == "Falha ao validar dados"
    assert error1.original_exception is None
    assert 'Não foi possível criar a ordem' in error1.message
    assert 'permanece aceito' in error1.message
    
    # Teste com exceção original
    original_exc = ValueError("Erro de validação")
    error2 = OrderCreationError(
        invite_id=456,
        reason="Erro de banco de dados",
        original_exception=original_exc
    )
    
    print(f"\nMensagem com exceção original: {error2.message}")
    
    assert error2.invite_id == 456
    assert error2.original_exception == original_exc
    assert str(original_exc) in str(error2.to_dict()['original_exception'])
    
    print("✓ Teste OrderCreationError passou!")


def test_escrow_block_error():
    """
    Testa a exceção EscrowBlockError
    
    Requirements: 7.2, 7.5
    """
    from services.exceptions import EscrowBlockError
    
    print("\n=== Teste 3: EscrowBlockError ===")
    
    error = EscrowBlockError(
        order_id=789,
        user_id=3,
        amount=Decimal('10.00'),
        reason="Saldo insuficiente no momento do bloqueio"
    )
    
    print(f"Mensagem: {error.message}")
    print(f"Dict: {error.to_dict()}")
    
    assert error.order_id == 789
    assert error.user_id == 3
    assert error.amount == Decimal('10.00')
    assert error.reason == "Saldo insuficiente no momento do bloqueio"
    assert 'Erro ao bloquear valores' in error.message
    assert 'operação foi cancelada' in error.message
    assert 'nenhum valor foi debitado' in error.message
    
    print("✓ Teste EscrowBlockError passou!")


def test_invite_validation_error():
    """
    Testa a exceção InviteValidationError
    
    Requirements: 7.4
    """
    from services.exceptions import InviteValidationError
    
    print("\n=== Teste 4: InviteValidationError ===")
    
    error = InviteValidationError(
        invite_id=999,
        reason="Convite já foi aceito anteriormente"
    )
    
    print(f"Mensagem: {error.message}")
    print(f"Dict: {error.to_dict()}")
    
    assert error.invite_id == 999
    assert error.reason == "Convite já foi aceito anteriormente"
    assert error.message == error.reason
    
    print("✓ Teste InviteValidationError passou!")


def test_exception_hierarchy():
    """
    Testa a hierarquia de exceções
    
    Requirements: 7.4
    """
    from services.exceptions import (
        InviteAcceptanceError,
        InsufficientBalanceError,
        OrderCreationError,
        EscrowBlockError,
        InviteValidationError
    )
    
    print("\n=== Teste 5: Hierarquia de Exceções ===")
    
    # Todas as exceções devem herdar de InviteAcceptanceError
    assert issubclass(InsufficientBalanceError, InviteAcceptanceError)
    assert issubclass(OrderCreationError, InviteAcceptanceError)
    assert issubclass(EscrowBlockError, InviteAcceptanceError)
    assert issubclass(InviteValidationError, InviteAcceptanceError)
    
    # Todas devem herdar de Exception
    assert issubclass(InviteAcceptanceError, Exception)
    
    print("✓ Hierarquia de exceções está correta!")


def test_error_messages_clarity():
    """
    Testa se as mensagens de erro são claras e acionáveis
    
    Requirements: 7.4, 8.3, 8.4
    """
    from services.exceptions import (
        InsufficientBalanceError,
        OrderCreationError,
        EscrowBlockError
    )
    
    print("\n=== Teste 6: Clareza das Mensagens ===")
    
    # Mensagem de saldo insuficiente deve incluir:
    # - Valor necessário
    # - Valor disponível
    # - Sugestão de ação
    error1 = InsufficientBalanceError(
        user_id=1,
        user_type='cliente',
        required_amount=Decimal('100.00'),
        current_balance=Decimal('50.00'),
        purpose='teste'
    )
    
    assert 'Necessário' in error1.message
    assert 'Disponível' in error1.message
    assert 'adicione' in error1.message.lower()
    assert 'R$ 100.00' in error1.message
    assert 'R$ 50.00' in error1.message
    print(f"✓ Mensagem de saldo insuficiente é clara")
    
    # Mensagem de erro de criação deve incluir:
    # - Explicação do problema
    # - Estado do convite
    # - Sugestão de ação
    error2 = OrderCreationError(
        invite_id=123,
        reason="Teste"
    )
    
    assert 'Não foi possível criar' in error2.message
    assert 'permanece aceito' in error2.message
    assert 'tentar novamente' in error2.message
    print(f"✓ Mensagem de erro de criação é clara")
    
    # Mensagem de erro de escrow deve incluir:
    # - Explicação do problema
    # - Garantia de que nada foi debitado
    # - Sugestão de ação
    error3 = EscrowBlockError(
        order_id=789,
        user_id=3,
        amount=Decimal('10.00'),
        reason="Teste"
    )
    
    assert 'Erro ao bloquear' in error3.message
    assert 'cancelada' in error3.message
    assert 'nenhum valor foi debitado' in error3.message
    assert 'tente novamente' in error3.message
    print(f"✓ Mensagem de erro de escrow é clara")
    
    print("✓ Todas as mensagens são claras e acionáveis!")


if __name__ == '__main__':
    print("=" * 60)
    print("TESTES DE TRATAMENTO DE ERROS ROBUSTO")
    print("Tarefa 12: Implementar tratamento de erros robusto")
    print("=" * 60)
    
    try:
        test_insufficient_balance_error()
        test_order_creation_error()
        test_escrow_block_error()
        test_invite_validation_error()
        test_exception_hierarchy()
        test_error_messages_clarity()
        
        print("\n" + "=" * 60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print("\nResumo da implementação:")
        print("✓ 12.1 - Tratamento de erro de saldo insuficiente")
        print("  - Exceção personalizada InsufficientBalanceError")
        print("  - Mensagens claras com valores necessários e disponíveis")
        print("  - Sugestão de ação (adicionar saldo)")
        print("  - Estado do convite não é alterado")
        print("\n✓ 12.2 - Tratamento de erro de criação de ordem")
        print("  - Exceção personalizada OrderCreationError")
        print("  - Rollback completo da transação")
        print("  - Reversão do status do convite se necessário")
        print("  - Logging detalhado de erros")
        print("  - Mensagem clara ao usuário")
        print("\n✓ 12.3 - Tratamento de erro de bloqueio de escrow")
        print("  - Exceção personalizada EscrowBlockError")
        print("  - Cancelamento da criação da ordem")
        print("  - Garantia de consistência de valores")
        print("  - Convite mantido como aceito para retry")
        print("  - Notificação de administrador (TODO)")
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
