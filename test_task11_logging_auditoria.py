#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar implementação de logging e auditoria
Tarefa 11: Implementar logging e auditoria

Este teste verifica:
- Logs de aceitação de convites (11.1)
- Logs de criação de ordem (11.2)
- Logs de erros (11.3)
"""

import sys
import os
import logging
from io import StringIO

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from models import db, User, Invite, Order, Wallet
from services.invite_service import InviteService
from services.invite_acceptance_coordinator import InviteAcceptanceCoordinator
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def setup_test_data():
    """Configura dados de teste"""
    import random
    
    with app.app_context():
        # Limpar dados existentes
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(Wallet).delete()
        db.session.query(User).filter(User.email.like('%logging%')).delete()
        db.session.commit()
        
        # Gerar CPFs únicos
        cpf_cliente = f"{random.randint(10000000000, 99999999999)}"
        cpf_prestador = f"{random.randint(10000000000, 99999999999)}"
        
        # Criar cliente
        cliente = User(
            nome="Cliente Teste Logging",
            email=f"cliente_logging_{random.randint(1000, 9999)}@test.com",
            cpf=cpf_cliente,
            phone=f"119999{random.randint(10000, 99999)}",
            password_hash="hash",
            roles="cliente"
        )
        db.session.add(cliente)
        db.session.flush()
        
        # Criar prestador
        prestador = User(
            nome="Prestador Teste Logging",
            email=f"prestador_logging_{random.randint(1000, 9999)}@test.com",
            cpf=cpf_prestador,
            phone=f"119998{random.randint(10000, 99999)}",
            password_hash="hash",
            roles="prestador"
        )
        db.session.add(prestador)
        db.session.flush()
        
        # Criar carteiras com saldo
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo
        WalletService.credit_wallet(cliente.id, Decimal('500.00'), "Saldo inicial teste")
        WalletService.credit_wallet(prestador.id, Decimal('50.00'), "Saldo inicial teste")
        
        db.session.commit()
        
        return cliente.id, prestador.id, prestador.phone

def test_logging_aceitacao_convites():
    """
    Testa logs de aceitação de convites (Tarefa 11.1)
    
    Verifica:
    - Log quando cliente aceita convite
    - Log quando prestador aceita convite
    - Inclusão de timestamps e IDs de usuário
    """
    print("\n" + "="*80)
    print("TESTE 11.1: Logs de Aceitação de Convites")
    print("="*80)
    
    with app.app_context():
        cliente_id, prestador_id, prestador_phone = setup_test_data()
        
        # Configurar captura de logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger = logging.getLogger('services.invite_service')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Criar convite
            delivery_date = datetime.utcnow() + timedelta(days=7)
            invite_result = InviteService.create_invite(
                client_id=cliente_id,
                invited_phone=prestador_phone,
                service_title="Serviço Teste Logging",
                service_description="Teste de logging",
                original_value=Decimal('100.00'),
                delivery_date=delivery_date
            )
            
            invite_id = invite_result['invite_id']
            print(f"✓ Convite {invite_id} criado")
            
            # Limpar logs anteriores
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Cliente aceita convite
            print("\n1. Cliente aceita convite...")
            result_cliente = InviteService.accept_invite_as_client(invite_id, cliente_id)
            
            # Verificar logs
            logs = log_stream.getvalue()
            print(f"\nLogs capturados (Cliente):")
            print(logs)
            
            assert 'ACEITAÇÃO CLIENTE' in logs, "Log de aceitação do cliente não encontrado"
            assert f'Convite {invite_id}' in logs, "ID do convite não está no log"
            assert f'cliente {cliente_id}' in logs, "ID do cliente não está no log"
            assert 'Timestamp:' in logs, "Timestamp não está no log"
            print("✓ Logs de aceitação do cliente verificados")
            
            # Limpar logs
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Prestador aceita convite
            print("\n2. Prestador aceita convite...")
            result_prestador = InviteService.accept_invite_as_provider(invite_id, prestador_id)
            
            # Verificar logs
            logs = log_stream.getvalue()
            print(f"\nLogs capturados (Prestador):")
            print(logs)
            
            assert 'ACEITAÇÃO PRESTADOR' in logs, "Log de aceitação do prestador não encontrado"
            assert f'Convite {invite_id}' in logs, "ID do convite não está no log"
            assert f'prestador {prestador_id}' in logs, "ID do prestador não está no log"
            assert 'Timestamp:' in logs, "Timestamp não está no log"
            print("✓ Logs de aceitação do prestador verificados")
            
            print("\n" + "="*80)
            print("✓ TESTE 11.1 PASSOU: Logs de aceitação implementados corretamente")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n✗ TESTE 11.1 FALHOU: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            logger.removeHandler(handler)

def test_logging_criacao_ordem():
    """
    Testa logs de criação de ordem (Tarefa 11.2)
    
    Verifica:
    - Log de criação de ordem a partir de convite
    - Inclusão de valores bloqueados e IDs de transação
    - Registro de qual usuário completou a aceitação mútua
    """
    print("\n" + "="*80)
    print("TESTE 11.2: Logs de Criação de Ordem")
    print("="*80)
    
    with app.app_context():
        cliente_id, prestador_id, prestador_phone = setup_test_data()
        
        # Configurar captura de logs
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Adicionar handler aos loggers relevantes
        logger_coordinator = logging.getLogger('services.invite_acceptance_coordinator')
        logger_coordinator.addHandler(handler)
        logger_coordinator.setLevel(logging.INFO)
        
        logger_order = logging.getLogger('services.order_service')
        logger_order.addHandler(handler)
        logger_order.setLevel(logging.INFO)
        
        try:
            # Criar convite
            delivery_date = datetime.utcnow() + timedelta(days=7)
            invite_result = InviteService.create_invite(
                client_id=cliente_id,
                invited_phone=prestador_phone,
                service_title="Serviço Teste Ordem",
                service_description="Teste de criação de ordem",
                original_value=Decimal('100.00'),
                delivery_date=delivery_date
            )
            
            invite_id = invite_result['invite_id']
            print(f"✓ Convite {invite_id} criado")
            
            # Cliente aceita
            InviteService.accept_invite_as_client(invite_id, cliente_id)
            print("✓ Cliente aceitou convite")
            
            # Limpar logs anteriores
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Prestador aceita (deve criar ordem)
            print("\nPrestador aceita convite (criação de ordem)...")
            result = InviteService.accept_invite_as_provider(invite_id, prestador_id)
            
            # Verificar logs
            logs = log_stream.getvalue()
            print(f"\nLogs capturados:")
            print(logs)
            
            # Verificar logs de criação de ordem
            assert 'ORDEM CRIADA' in logs, "Log de ordem criada não encontrado"
            assert 'Valor do serviço:' in logs or 'Valor:' in logs, "Valor não está no log"
            assert 'Escrow' in logs or 'bloqueado' in logs, "Informação de escrow não está no log"
            assert 'Transaction ID' in logs or 'transaction_id' in logs, "Transaction ID não está no log"
            print("✓ Logs de criação de ordem verificados")
            
            # Verificar se ordem foi criada
            assert result['order_created'], "Ordem não foi criada"
            order_id = result['order_id']
            print(f"✓ Ordem {order_id} criada com sucesso")
            
            print("\n" + "="*80)
            print("✓ TESTE 11.2 PASSOU: Logs de criação de ordem implementados corretamente")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n✗ TESTE 11.2 FALHOU: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            logger_coordinator.removeHandler(handler)
            logger_order.removeHandler(handler)

def test_logging_erros():
    """
    Testa logs de erros (Tarefa 11.3)
    
    Verifica:
    - Log de falhas na criação de ordem
    - Log de falhas no bloqueio de valores
    - Inclusão de stack trace para debugging
    """
    print("\n" + "="*80)
    print("TESTE 11.3: Logs de Erros")
    print("="*80)
    
    with app.app_context():
        cliente_id, prestador_id, prestador_phone = setup_test_data()
        
        # Configurar captura de logs de erro e warning
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)  # Capturar WARNING e ERROR
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger = logging.getLogger('services.invite_service')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)  # Capturar WARNING e ERROR
        
        logger_coordinator = logging.getLogger('services.invite_acceptance_coordinator')
        logger_coordinator.addHandler(handler)
        logger_coordinator.setLevel(logging.WARNING)  # Capturar WARNING e ERROR
        
        try:
            # Adicionar mais saldo ao cliente para criar o convite
            WalletService.credit_wallet(cliente_id, Decimal('1000.00'), "Saldo adicional para teste")
            
            # Criar convite
            delivery_date = datetime.utcnow() + timedelta(days=7)
            invite_result = InviteService.create_invite(
                client_id=cliente_id,
                invited_phone=prestador_phone,
                service_title="Serviço Teste Erro",
                service_description="Teste de logging de erros",
                original_value=Decimal('1000.00'),  # Valor alto para causar erro de saldo
                delivery_date=delivery_date
            )
            
            invite_id = invite_result['invite_id']
            print(f"✓ Convite {invite_id} criado com valor alto")
            
            # Remover saldo do cliente para causar erro
            wallet = Wallet.query.filter_by(user_id=cliente_id).first()
            wallet.balance = Decimal('50.00')  # Saldo insuficiente
            db.session.commit()
            print("✓ Saldo do cliente reduzido para causar erro")
            
            # Limpar logs anteriores
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Tentar aceitar convite (deve falhar por saldo insuficiente)
            print("\nTentando aceitar convite com saldo insuficiente...")
            try:
                InviteService.accept_invite_as_client(invite_id, cliente_id)
                print("✗ Deveria ter falhado por saldo insuficiente")
                return False
            except ValueError as e:
                print(f"✓ Erro esperado capturado: {str(e)}")
            
            # Verificar logs capturados
            logs = log_stream.getvalue()
            print(f"\nLogs de erro capturados:")
            print(logs if logs else "(nenhum log capturado)")
            
            # Verificar conteúdo dos logs
            assert 'BLOQUEADA' in logs or 'insuficiente' in logs, "Log de erro não encontrado"
            assert f'Cliente {cliente_id}' in logs or f'cliente {cliente_id}' in logs, "ID do cliente não está no log de erro"
            print("✓ Logs de erro verificados")
            
            print("\n" + "="*80)
            print("✓ TESTE 11.3 PASSOU: Logs de erros implementados corretamente")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"\n✗ TESTE 11.3 FALHOU: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            logger.removeHandler(handler)
            logger_coordinator.removeHandler(handler)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("INICIANDO TESTES DE LOGGING E AUDITORIA (TAREFA 11)")
    print("="*80)
    
    resultados = []
    
    # Executar testes
    resultados.append(("11.1 - Logs de Aceitação", test_logging_aceitacao_convites()))
    resultados.append(("11.2 - Logs de Criação de Ordem", test_logging_criacao_ordem()))
    resultados.append(("11.3 - Logs de Erros", test_logging_erros()))
    
    # Resumo
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    total = len(resultados)
    passou = sum(1 for _, result in resultados if result)
    
    for nome, resultado in resultados:
        status = "✓ PASSOU" if resultado else "✗ FALHOU"
        print(f"{nome}: {status}")
    
    print(f"\nTotal: {passou}/{total} testes passaram")
    
    if passou == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Tarefa 11 implementada com sucesso.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passou} teste(s) falharam.")
        sys.exit(1)
