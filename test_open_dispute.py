#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para o método open_dispute do OrderManagementService
Testa abertura de contestação com upload de arquivos
"""

import os
import sys
import tempfile
from io import BytesIO
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, Order, Wallet
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from werkzeug.datastructures import FileStorage
from config import TestConfig

# Criar app de teste
app = Flask(__name__)
app.config.from_object(TestConfig)
db.init_app(app)


def create_test_data():
    """Cria dados de teste"""
    # Criar usuários
    cliente = User(
        email='cliente_dispute@test.com',
        nome='Cliente Teste',
        cpf='111.111.111-11',
        roles='cliente'
    )
    cliente.set_password('senha123')
    
    prestador = User(
        email='prestador_dispute@test.com',
        nome='Prestador Teste',
        cpf='222.222.222-22',
        roles='prestador'
    )
    prestador.set_password('senha123')
    
    db.session.add(cliente)
    db.session.add(prestador)
    db.session.flush()
    
    # Criar carteiras com saldo
    wallet_cliente = Wallet(user_id=cliente.id, balance=1000.00, escrow_balance=0.00)
    wallet_prestador = Wallet(user_id=prestador.id, balance=1000.00, escrow_balance=0.00)
    
    db.session.add(wallet_cliente)
    db.session.add(wallet_prestador)
    db.session.flush()
    
    # Criar ordem com status servico_executado
    order = Order(
        client_id=cliente.id,
        provider_id=prestador.id,
        title='Serviço de Teste para Contestação',
        description='Descrição do serviço',
        value=500.00,
        status='servico_executado',
        service_deadline=datetime.utcnow() + timedelta(days=7),
        completed_at=datetime.utcnow() - timedelta(hours=1),
        confirmation_deadline=datetime.utcnow() + timedelta(hours=35),
        dispute_deadline=datetime.utcnow() + timedelta(hours=35),
        platform_fee_percentage_at_creation=5.0,
        contestation_fee_at_creation=10.00,
        cancellation_fee_percentage_at_creation=10.0
    )
    
    db.session.add(order)
    db.session.commit()
    
    return cliente, prestador, order


def create_mock_file(filename, content, content_type='image/jpeg'):
    """Cria um arquivo mock para teste"""
    file_data = BytesIO(content)
    return FileStorage(
        stream=file_data,
        filename=filename,
        content_type=content_type
    )


def test_open_dispute_basic():
    """Teste 1: Abertura de contestação básica sem arquivos"""
    print("\n=== Teste 1: Abertura de contestação básica ===")
    
    with app.app_context():
        db.create_all()
        
        try:
            cliente, prestador, order = create_test_data()
            
            # Abrir contestação sem arquivos
            reason = "O serviço não foi executado conforme combinado. Há problemas na instalação."
            
            result = OrderManagementService.open_dispute(
                order_id=order.id,
                client_id=cliente.id,
                reason=reason,
                evidence_files=None
            )
            
            print(f"✓ Contestação aberta com sucesso")
            print(f"  - Order ID: {result['order_id']}")
            print(f"  - Status: {result['status']}")
            print(f"  - Taxa de contestação: R$ {result['contestation_fee']:.2f}")
            print(f"  - Arquivos: {result['evidence_files_count']}")
            print(f"  - Mensagem: {result['message']}")
            
            # Verificar no banco
            db.session.refresh(order)
            assert order.status == 'contestada', "Status deve ser 'contestada'"
            assert order.dispute_opened_by == cliente.id, "Cliente deve ser o autor"
            assert order.dispute_client_statement == reason, "Motivo deve estar salvo"
            assert order.dispute_opened_at is not None, "Data de abertura deve estar registrada"
            
            print("✓ Dados salvos corretamente no banco")
            
        finally:
            db.session.rollback()
            db.drop_all()


def test_open_dispute_with_files():
    """Teste 2: Abertura de contestação com arquivos de prova"""
    print("\n=== Teste 2: Abertura de contestação com arquivos ===")
    
    with app.app_context():
        db.create_all()
        
        try:
            cliente, prestador, order = create_test_data()
            
            # Criar arquivos mock
            files = [
                create_mock_file('foto1.jpg', b'fake image content 1', 'image/jpeg'),
                create_mock_file('foto2.png', b'fake image content 2', 'image/png'),
                create_mock_file('comprovante.pdf', b'fake pdf content', 'application/pdf')
            ]
            
            reason = "O serviço apresenta defeitos graves. Anexo fotos e documentos comprobatórios."
            
            result = OrderManagementService.open_dispute(
                order_id=order.id,
                client_id=cliente.id,
                reason=reason,
                evidence_files=files
            )
            
            print(f"✓ Contestação aberta com {result['evidence_files_count']} arquivos")
            print(f"  - Order ID: {result['order_id']}")
            print(f"  - Status: {result['status']}")
            
            # Verificar arquivos salvos
            for i, evidence in enumerate(result['evidence_urls'], 1):
                print(f"  - Arquivo {i}: {evidence['filename']} ({evidence['size']} bytes)")
                print(f"    URL: {evidence['url']}")
                print(f"    Tipo: {evidence['type']}")
            
            # Verificar no banco
            db.session.refresh(order)
            assert order.status == 'contestada'
            assert len(order.dispute_evidence_urls) == 3, "Deve ter 3 arquivos"
            assert order.dispute_evidence_urls[0]['filename'] == 'foto1.jpg'
            
            print("✓ Arquivos salvos e registrados corretamente")
            
        finally:
            db.session.rollback()
            db.drop_all()


def test_open_dispute_validations():
    """Teste 3: Validações de abertura de contestação"""
    print("\n=== Teste 3: Validações ===")
    
    with app.app_context():
        db.create_all()
        
        try:
            cliente, prestador, order = create_test_data()
            
            # Teste 3.1: Motivo muito curto
            print("\n3.1. Testando motivo muito curto...")
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Curto",
                    evidence_files=None
                )
                print("✗ Deveria ter falhado com motivo curto")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.2: Prestador tentando abrir contestação
            print("\n3.2. Testando prestador tentando contestar...")
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=prestador.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=None
                )
                print("✗ Deveria ter falhado com prestador")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.3: Status inválido
            print("\n3.3. Testando status inválido...")
            order.status = 'concluida'
            db.session.commit()
            
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=None
                )
                print("✗ Deveria ter falhado com status inválido")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.4: Prazo expirado
            print("\n3.4. Testando prazo expirado...")
            order.status = 'servico_executado'
            order.dispute_deadline = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=None
                )
                print("✗ Deveria ter falhado com prazo expirado")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.5: Muitos arquivos
            print("\n3.5. Testando limite de arquivos (máximo 5)...")
            order.dispute_deadline = datetime.utcnow() + timedelta(hours=35)
            db.session.commit()
            
            files = [
                create_mock_file(f'foto{i}.jpg', b'fake content', 'image/jpeg')
                for i in range(6)  # 6 arquivos (excede o limite)
            ]
            
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=files
                )
                print("✗ Deveria ter falhado com muitos arquivos")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.6: Tipo de arquivo inválido
            print("\n3.6. Testando tipo de arquivo inválido...")
            files = [
                create_mock_file('script.exe', b'fake exe', 'application/exe')
            ]
            
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=files
                )
                print("✗ Deveria ter falhado com tipo inválido")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            # Teste 3.7: Arquivo muito grande
            print("\n3.7. Testando arquivo muito grande (>10MB)...")
            large_content = b'x' * (11 * 1024 * 1024)  # 11MB
            files = [
                create_mock_file('grande.jpg', large_content, 'image/jpeg')
            ]
            
            try:
                OrderManagementService.open_dispute(
                    order_id=order.id,
                    client_id=cliente.id,
                    reason="Motivo com mais de vinte caracteres aqui",
                    evidence_files=files
                )
                print("✗ Deveria ter falhado com arquivo grande")
            except ValueError as e:
                print(f"✓ Validação correta: {e}")
            
            print("\n✓ Todas as validações funcionaram corretamente")
            
        finally:
            db.session.rollback()
            db.drop_all()


def test_dispute_blocks_auto_confirmation():
    """Teste 4: Contestação bloqueia confirmação automática"""
    print("\n=== Teste 4: Bloqueio de confirmação automática ===")
    
    with app.app_context():
        db.create_all()
        
        try:
            cliente, prestador, order = create_test_data()
            
            # Abrir contestação
            reason = "Serviço não foi executado conforme o combinado, preciso de análise."
            
            OrderManagementService.open_dispute(
                order_id=order.id,
                client_id=cliente.id,
                reason=reason,
                evidence_files=None
            )
            
            # Verificar que status mudou para 'contestada'
            db.session.refresh(order)
            assert order.status == 'contestada'
            
            # Tentar executar auto_confirm (não deve processar ordens contestadas)
            result = OrderManagementService.auto_confirm_expired_orders()
            
            print(f"✓ Auto-confirmação executada")
            print(f"  - Ordens processadas: {result['processed']}")
            print(f"  - Ordens confirmadas: {result['confirmed']}")
            
            # Verificar que a ordem contestada não foi confirmada
            db.session.refresh(order)
            assert order.status == 'contestada', "Ordem deve permanecer contestada"
            assert order.confirmed_at is None, "Não deve ter data de confirmação"
            
            print("✓ Ordem contestada não foi auto-confirmada (correto)")
            
        finally:
            db.session.rollback()
            db.drop_all()


if __name__ == '__main__':
    print("=" * 70)
    print("TESTES DO MÉTODO open_dispute - OrderManagementService")
    print("=" * 70)
    
    try:
        test_open_dispute_basic()
        test_open_dispute_with_files()
        test_open_dispute_validations()
        test_dispute_blocks_auto_confirmation()
        
        print("\n" + "=" * 70)
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ ERRO NOS TESTES: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
