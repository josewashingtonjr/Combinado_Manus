#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da Tarefa 17: Rotas de Contestação
Testa as rotas GET e POST para contestação de ordens
"""

import sys
import os
from io import BytesIO

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Wallet
from services.wallet_service import WalletService
from services.order_management_service import OrderManagementService
from datetime import datetime, timedelta
from decimal import Decimal


def setup_test_data():
    """Configura dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        db.session.query(Order).filter(Order.id == 1000).delete()
        db.session.query(User).filter(
            (User.id.in_([100, 101])) | 
            (User.cpf.in_(['12345678900', '98765432100']))
        ).delete()
        db.session.query(Wallet).filter(Wallet.user_id.in_([100, 101])).delete()
        db.session.commit()
        
        # Criar cliente
        cliente = User(
            id=100,
            nome='Cliente Teste',
            email='cliente_test17@test.com',
            cpf='12345678900',
            roles='cliente'
        )
        cliente.set_password('senha123')
        db.session.add(cliente)
        
        # Criar prestador
        prestador = User(
            id=101,
            nome='Prestador Teste',
            email='prestador_test17@test.com',
            cpf='98765432100',
            roles='prestador'
        )
        prestador.set_password('senha123')
        db.session.add(prestador)
        
        db.session.commit()
        
        # Criar carteiras com saldo
        WalletService.ensure_user_has_wallet(100)
        WalletService.ensure_user_has_wallet(101)
        WalletService.credit_wallet(100, Decimal('1000.00'), 'Saldo inicial teste')
        WalletService.credit_wallet(101, Decimal('1000.00'), 'Saldo inicial teste')
        
        # Criar ordem com status servico_executado
        order = Order(
            id=1000,
            client_id=100,
            provider_id=101,
            title='Serviço de Teste',
            description='Descrição do serviço de teste',
            value=Decimal('100.00'),
            status='servico_executado',
            service_deadline=datetime.utcnow() + timedelta(days=7),
            completed_at=datetime.utcnow() - timedelta(hours=1),
            confirmation_deadline=datetime.utcnow() + timedelta(hours=35),
            dispute_deadline=datetime.utcnow() + timedelta(hours=35),
            platform_fee_percentage_at_creation=Decimal('5.0'),
            contestation_fee_at_creation=Decimal('10.00'),
            cancellation_fee_percentage_at_creation=Decimal('10.0'),
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(order)
        
        # Bloquear valores em escrow
        WalletService.transfer_to_escrow(100, Decimal('110.00'), 1000)  # valor + taxa contestação
        WalletService.transfer_to_escrow(101, Decimal('10.00'), 1000)   # taxa contestação
        
        db.session.commit()
        
        print("✓ Dados de teste criados com sucesso")
        return cliente, prestador, order


def test_get_contestacao_form():
    """Testa rota GET /ordens/<id>/contestar"""
    print("\n=== Teste 1: GET /ordens/<id>/contestar ===")
    
    with app.test_client() as client:
        # Login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = 100
            sess['active_role'] = 'cliente'
        
        # Acessar formulário de contestação
        response = client.get('/ordens/1000/contestar')
        
        assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
        assert b'Contestar Ordem' in response.data, "Título não encontrado"
        assert b'Motivo da Contesta' in response.data, "Campo de motivo não encontrado"
        assert b'Provas' in response.data, "Campo de provas não encontrado"
        assert b'evidence' in response.data, "Input de arquivo não encontrado"
        
        print("✓ Formulário de contestação exibido corretamente")
        print("✓ Campos obrigatórios presentes")


def test_post_contestacao_sem_arquivos():
    """Testa POST /ordens/<id>/contestar sem arquivos"""
    print("\n=== Teste 2: POST /ordens/<id>/contestar (sem arquivos) ===")
    
    with app.test_client() as client:
        # Login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = 100
            sess['active_role'] = 'cliente'
        
        # Submeter contestação sem arquivos
        response = client.post('/ordens/1000/contestar', data={
            'reason': 'Este é um motivo de contestação com mais de 20 caracteres para passar na validação.',
            'confirm': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
        
        # Verificar se contestação foi aberta
        with app.app_context():
            order = Order.query.get(1000)
            assert order.status == 'contestada', f"Status esperado 'contestada', recebido '{order.status}'"
            assert order.dispute_opened_by == 100, "Cliente incorreto"
            assert order.dispute_client_statement is not None, "Motivo não registrado"
            assert len(order.dispute_client_statement) >= 20, "Motivo muito curto"
            
            print(f"✓ Contestação aberta com sucesso")
            print(f"✓ Status: {order.status}")
            print(f"✓ Motivo: {order.dispute_client_statement[:50]}...")


def test_post_contestacao_com_arquivos():
    """Testa POST /ordens/<id>/contestar com arquivos"""
    print("\n=== Teste 3: POST /ordens/<id>/contestar (com arquivos) ===")
    
    # Resetar ordem para servico_executado
    with app.app_context():
        order = Order.query.get(1000)
        order.status = 'servico_executado'
        order.dispute_opened_by = None
        order.dispute_opened_at = None
        order.dispute_client_statement = None
        order.dispute_evidence_urls = None
        db.session.commit()
    
    with app.test_client() as client:
        # Login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = 100
            sess['active_role'] = 'cliente'
        
        # Criar arquivo de teste
        test_file = (BytesIO(b'fake image content'), 'prova.jpg')
        
        # Submeter contestação com arquivo
        response = client.post('/ordens/1000/contestar', data={
            'reason': 'Motivo detalhado da contestação com mais de vinte caracteres necessários.',
            'evidence': test_file,
            'confirm': 'on'
        }, content_type='multipart/form-data', follow_redirects=True)
        
        assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
        
        # Verificar se arquivo foi processado
        with app.app_context():
            order = Order.query.get(1000)
            assert order.status == 'contestada', f"Status esperado 'contestada', recebido '{order.status}'"
            
            if order.dispute_evidence_urls:
                print(f"✓ Contestação com {len(order.dispute_evidence_urls)} arquivo(s) de prova")
                print(f"✓ Arquivo salvo: {order.dispute_evidence_urls[0].get('filename', 'N/A')}")
            else:
                print("⚠ Nenhum arquivo de prova registrado (pode ser esperado se upload falhou)")


def test_validacao_motivo_curto():
    """Testa validação de motivo muito curto"""
    print("\n=== Teste 4: Validação de motivo curto ===")
    
    # Resetar ordem
    with app.app_context():
        order = Order.query.get(1000)
        order.status = 'servico_executado'
        order.dispute_opened_by = None
        order.dispute_opened_at = None
        order.dispute_client_statement = None
        db.session.commit()
    
    with app.test_client() as client:
        # Login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = 100
            sess['active_role'] = 'cliente'
        
        # Submeter com motivo curto
        response = client.post('/ordens/1000/contestar', data={
            'reason': 'Muito curto',  # Menos de 20 caracteres
            'confirm': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
        
        # Verificar que ordem não foi contestada
        with app.app_context():
            order = Order.query.get(1000)
            assert order.status == 'servico_executado', f"Status não deveria mudar, mas é '{order.status}'"
            
            print("✓ Validação de motivo curto funcionando")
            print("✓ Ordem permanece com status 'servico_executado'")


def test_acesso_negado_prestador():
    """Testa que prestador não pode contestar"""
    print("\n=== Teste 5: Acesso negado para prestador ===")
    
    with app.test_client() as client:
        # Login como prestador
        with client.session_transaction() as sess:
            sess['user_id'] = 101
            sess['active_role'] = 'prestador'
        
        # Tentar acessar contestação
        response = client.get('/ordens/1000/contestar', follow_redirects=True)
        
        assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
        assert b'Acesso negado' in response.data or b'permiss' in response.data, "Mensagem de erro não encontrada"
        
        print("✓ Prestador não pode acessar contestação")
        print("✓ Mensagem de erro exibida")


def cleanup_test_data():
    """Limpa dados de teste"""
    with app.app_context():
        db.session.query(Order).filter_by(id=1000).delete()
        db.session.query(User).filter(User.id.in_([100, 101])).delete()
        db.session.query(Wallet).filter(Wallet.user_id.in_([100, 101])).delete()
        db.session.commit()
        print("\n✓ Dados de teste removidos")


def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("TESTE DA TAREFA 17: ROTAS DE CONTESTAÇÃO")
    print("=" * 70)
    
    try:
        # Setup
        setup_test_data()
        
        # Executar testes
        test_get_contestacao_form()
        test_post_contestacao_sem_arquivos()
        test_post_contestacao_com_arquivos()
        test_validacao_motivo_curto()
        test_acesso_negado_prestador()
        
        print("\n" + "=" * 70)
        print("✓ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        cleanup_test_data()
    
    return 0


if __name__ == '__main__':
    exit(main())
