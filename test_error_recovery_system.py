#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do Sistema de Recuperação de Erros e Tratamento de Casos Extremos

Este script testa as funcionalidades implementadas na tarefa 14:
- Tratamento para ações simultâneas (concorrência)
- Recovery para estados inconsistentes
- Validação de integridade de dados
- Rollback automático em falhas de transação
- Mensagens de erro claras para usuários

Requirements: 3.3, 4.4, 7.4
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Invite, Proposal, Wallet
from services.error_recovery_service import ErrorRecoveryService, InconsistencyReport, RecoveryAction
from services.error_handling_middleware import ErrorHandlingMiddleware
from services.atomic_transaction_manager import (
    InsufficientBalanceError,
    ConcurrentOperationError,
    TransactionIntegrityError,
    atomic_financial_operation
)
from services.proposal_service import ProposalService
from decimal import Decimal
from datetime import datetime, timedelta
import threading
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_data():
    """Configura dados de teste"""
    print("🔧 Configurando dados de teste...")
    
    # Limpar dados existentes
    db.session.query(Proposal).delete()
    db.session.query(Invite).delete()
    db.session.query(Wallet).delete()
    db.session.query(User).filter(User.nome.like('Teste%')).delete()
    db.session.commit()
    
    # Criar usuários de teste
    cliente = User(
        nome='Teste Cliente',
        email='cliente@teste.com',
        telefone='11999999001',
        role='cliente',
        password_hash='hash_teste'
    )
    
    prestador = User(
        nome='Teste Prestador',
        email='prestador@teste.com',
        telefone='11999999002',
        role='prestador',
        password_hash='hash_teste'
    )
    
    db.session.add_all([cliente, prestador])
    db.session.commit()
    
    # Criar carteira para o cliente
    carteira = Wallet(
        user_id=cliente.id,
        balance=Decimal('100.00'),
        escrow_balance=Decimal('0.00')
    )
    
    db.session.add(carteira)
    db.session.commit()
    
    # Criar convite de teste
    convite = Invite(
        client_id=cliente.id,
        invited_phone=prestador.telefone,
        service_title='Serviço de Teste',
        service_description='Descrição do serviço de teste',
        original_value=Decimal('50.00'),
        delivery_date=datetime.utcnow() + timedelta(days=7),
        status='pendente'
    )
    
    db.session.add(convite)
    db.session.commit()
    
    print(f"✅ Dados criados: Cliente ID {cliente.id}, Prestador ID {prestador.id}, Convite ID {convite.id}")
    
    return {
        'cliente_id': cliente.id,
        'prestador_id': prestador.id,
        'convite_id': convite.id
    }

def test_concurrent_proposal_creation(test_data):
    """Testa criação simultânea de propostas"""
    print("\n🔄 Testando criação simultânea de propostas...")
    
    invite_id = test_data['convite_id']
    prestador_id = test_data['prestador_id']
    
    results = []
    errors = []
    
    def create_proposal_thread(thread_id):
        try:
            result = ErrorRecoveryService.handle_concurrent_proposal_creation(
                invite_id=invite_id,
                prestador_id=prestador_id,
                proposed_value=Decimal('75.00'),
                justification=f'Proposta da thread {thread_id}'
            )
            results.append((thread_id, result))
        except Exception as e:
            errors.append((thread_id, str(e)))
    
    # Criar múltiplas threads para simular concorrência
    threads = []
    for i in range(3):
        thread = threading.Thread(target=create_proposal_thread, args=(i,))
        threads.append(thread)
    
    # Iniciar todas as threads simultaneamente
    for thread in threads:
        thread.start()
    
    # Aguardar conclusão
    for thread in threads:
        thread.join()
    
    print(f"📊 Resultados: {len(results)} sucessos, {len(errors)} erros")
    
    # Verificar que apenas uma proposta foi criada
    proposals_count = db.session.query(Proposal).filter_by(invite_id=invite_id).count()
    
    if proposals_count == 1:
        print("✅ Controle de concorrência funcionou - apenas 1 proposta criada")
    else:
        print(f"❌ Falha no controle de concorrência - {proposals_count} propostas criadas")
    
    return proposals_count == 1

def test_data_integrity_detection():
    """Testa detecção de inconsistências de dados"""
    print("\n🔍 Testando detecção de inconsistências...")
    
    # Criar inconsistência artificial - convite com flag ativa mas sem proposal_id
    convite = db.session.query(Invite).first()
    if convite:
        convite.has_active_proposal = True
        convite.current_proposal_id = None
        db.session.commit()
        
        print("🔧 Inconsistência artificial criada")
    
    # Detectar inconsistências
    inconsistencies = ErrorRecoveryService.detect_data_inconsistencies()
    
    print(f"📊 Inconsistências detectadas: {len(inconsistencies)}")
    
    orphaned_flags = [inc for inc in inconsistencies if inc.inconsistency_type == 'orphaned_active_flag']
    
    if orphaned_flags:
        print("✅ Inconsistência de flag órfã detectada corretamente")
        return True
    else:
        print("❌ Inconsistência não detectada")
        return False

def test_automatic_recovery():
    """Testa recuperação automática de inconsistências"""
    print("\n🔧 Testando recuperação automática...")
    
    # Detectar inconsistências
    inconsistencies = ErrorRecoveryService.detect_data_inconsistencies()
    
    if not inconsistencies:
        print("ℹ️ Nenhuma inconsistência para recuperar")
        return True
    
    recovery_results = []
    
    for inconsistency in inconsistencies:
        print(f"🔧 Recuperando: {inconsistency.description}")
        
        result = ErrorRecoveryService.recover_from_inconsistency(inconsistency)
        recovery_results.append(result)
        
        print(f"📊 Resultado: {'✅' if result.success else '❌'} {result.message}")
    
    # Verificar se inconsistências foram resolvidas
    remaining_inconsistencies = ErrorRecoveryService.detect_data_inconsistencies()
    
    if len(remaining_inconsistencies) < len(inconsistencies):
        print("✅ Recuperação automática funcionou")
        return True
    else:
        print("❌ Recuperação automática falhou")
        return False

def test_balance_validation_errors():
    """Testa tratamento de erros de saldo"""
    print("\n💰 Testando tratamento de erros de saldo...")
    
    # Criar proposta que requer mais saldo do que disponível
    convite = db.session.query(Invite).first()
    prestador_id = convite.invited_phone  # Assumindo que é o ID do prestador
    
    # Buscar prestador real
    prestador = db.session.query(User).filter_by(telefone=convite.invited_phone).first()
    if not prestador:
        print("❌ Prestador não encontrado")
        return False
    
    try:
        # Tentar criar proposta com valor alto
        result = ProposalService.create_proposal(
            invite_id=convite.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('200.00'),  # Mais que o saldo disponível
            justification='Proposta de teste com valor alto'
        )
        
        if result.get('success'):
            proposal_id = result['proposal_id']
            
            # Tentar aprovar (deve falhar por saldo insuficiente)
            try:
                approval_result = ProposalService.approve_proposal(
                    proposal_id=proposal_id,
                    client_id=convite.client_id,
                    client_response_reason='Teste de saldo insuficiente'
                )
                
                if not approval_result.get('success') and 'insufficient_balance' in approval_result.get('error', ''):
                    print("✅ Erro de saldo insuficiente tratado corretamente")
                    return True
                else:
                    print("❌ Erro de saldo não foi detectado")
                    return False
                    
            except InsufficientBalanceError as e:
                print("✅ Exceção de saldo insuficiente capturada corretamente")
                print(f"📊 Detalhes: {e.details}")
                return True
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_rollback_functionality():
    """Testa funcionalidade de rollback"""
    print("\n↩️ Testando funcionalidade de rollback...")
    
    # Simular operação que falha e precisa de rollback
    operation_data = {
        'operation_type': 'proposal_creation',
        'entity_id': 999,  # ID inexistente
        'proposal_id': 999,
        'invite_id': 1
    }
    
    try:
        result = ErrorRecoveryService.rollback_failed_operation(
            'proposal_creation',
            operation_data
        )
        
        if result.success:
            print("✅ Rollback executado com sucesso")
            print(f"📊 Detalhes: {result.message}")
            return True
        else:
            print(f"❌ Rollback falhou: {result.message}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no rollback: {e}")
        return False

def test_user_friendly_messages():
    """Testa geração de mensagens amigáveis"""
    print("\n💬 Testando mensagens amigáveis para usuários...")
    
    # Testar diferentes tipos de erro
    test_cases = [
        (
            InsufficientBalanceError(
                current_balance=Decimal('50.00'),
                required_amount=Decimal('100.00'),
                user_id=1
            ),
            "saldo insuficiente"
        ),
        (
            ConcurrentOperationError("Operação simultânea detectada"),
            "operação simultânea"
        ),
        (
            TransactionIntegrityError("Erro de integridade"),
            "erro interno"
        ),
        (
            ValueError("Item not found"),
            "não foi encontrado"
        )
    ]
    
    all_passed = True
    
    for error, expected_keyword in test_cases:
        message = ErrorRecoveryService.generate_user_friendly_error_message(error)
        
        if expected_keyword.lower() in message.lower():
            print(f"✅ Mensagem para {error.__class__.__name__}: OK")
        else:
            print(f"❌ Mensagem para {error.__class__.__name__}: Falhou")
            print(f"   Esperado conter: {expected_keyword}")
            print(f"   Recebido: {message}")
            all_passed = False
    
    return all_passed

def test_consistency_check():
    """Testa verificação completa de consistência"""
    print("\n🔍 Testando verificação completa de consistência...")
    
    try:
        result = ErrorRecoveryService.run_consistency_check()
        
        if result.get('success'):
            print("✅ Verificação de consistência executada com sucesso")
            print(f"📊 Inconsistências detectadas: {result.get('inconsistencies_detected', 0)}")
            print(f"📊 Recuperações automáticas: {result.get('automatic_recoveries', 0)}")
            print(f"📊 Recuperações bem-sucedidas: {result.get('successful_recoveries', 0)}")
            print(f"⏱️ Duração: {result.get('duration_seconds', 0):.3f}s")
            return True
        else:
            print(f"❌ Verificação de consistência falhou: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na verificação de consistência: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema de Recuperação de Erros")
    print("=" * 60)
    
    # Criar aplicação Flask
    app = create_app()
    
    with app.app_context():
        # Configurar dados de teste
        test_data = setup_test_data()
        
        # Executar testes
        tests = [
            ("Criação Simultânea de Propostas", lambda: test_concurrent_proposal_creation(test_data)),
            ("Detecção de Inconsistências", test_data_integrity_detection),
            ("Recuperação Automática", test_automatic_recovery),
            ("Validação de Saldo", test_balance_validation_errors),
            ("Funcionalidade de Rollback", test_rollback_functionality),
            ("Mensagens Amigáveis", test_user_friendly_messages),
            ("Verificação de Consistência", test_consistency_check)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            
            try:
                start_time = time.time()
                success = test_func()
                duration = time.time() - start_time
                
                results.append((test_name, success, duration))
                
                status = "✅ PASSOU" if success else "❌ FALHOU"
                print(f"\n{status} - {test_name} ({duration:.3f}s)")
                
            except Exception as e:
                results.append((test_name, False, 0))
                print(f"\n❌ ERRO - {test_name}: {e}")
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        for test_name, success, duration in results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name:<35} ({duration:.3f}s)")
        
        print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 Todos os testes passaram! Sistema de recuperação de erros funcionando corretamente.")
        else:
            print("⚠️ Alguns testes falharam. Verifique os logs acima para detalhes.")
        
        return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)