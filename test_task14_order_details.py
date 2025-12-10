#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para Task 14: Criar rotas de ordens - Detalhes
Testa a rota GET /ordens/<id> para exibir detalhes da ordem
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Order, Wallet, SystemConfig
from services.wallet_service import WalletService
from services.config_service import ConfigService
import secrets
import string


def generate_unique_cpf():
    """Gera um CPF único para testes"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(11)])


def test_order_details_route():
    """Testa a rota GET /ordens/<id> para visualização de detalhes"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Task 14 - Rota de Detalhes da Ordem")
        print("="*80 + "\n")
        
        # Limpar dados de teste anteriores
        test_users = User.query.filter(User.email.like('test_task14_%@test.com')).all()
        for user in test_users:
            Wallet.query.filter_by(user_id=user.id).delete()
        User.query.filter(User.email.like('test_task14_%@test.com')).delete()
        db.session.commit()
        
        # Criar usuários de teste
        cpf_cliente = generate_unique_cpf()
        cpf_prestador = generate_unique_cpf()
        
        cliente = User(
            nome='Test Task 14 Cliente',
            email='test_task14_cliente@test.com',
            cpf=cpf_cliente,
            phone='11999999014',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            nome='Test Task 14 Prestador',
            email='test_task14_prestador@test.com',
            cpf=cpf_prestador,
            phone='11999999015',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add(cliente)
        db.session.add(prestador)
        db.session.commit()
        
        print(f"✓ Usuários criados: Cliente ID={cliente.id}, Prestador ID={prestador.id}")
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        print("✓ Carteiras criadas")
        
        # Adicionar saldo
        WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Saldo inicial teste')
        WalletService.credit_wallet(prestador.id, Decimal('100.00'), 'Saldo inicial teste')
        print("✓ Saldo adicionado")
        
        # Garantir que as configurações existem
        ConfigService.get_platform_fee_percentage()
        ConfigService.get_contestation_fee()
        ConfigService.get_cancellation_fee_percentage()
        
        # Criar ordem de teste
        order = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Teste de Visualização de Ordem',
            description='Ordem criada para testar a visualização de detalhes',
            value=Decimal('200.00'),
            status='aguardando_execucao',
            service_deadline=datetime.utcnow() + timedelta(days=7),
            platform_fee_percentage_at_creation=Decimal('5.0'),
            contestation_fee_at_creation=Decimal('10.00'),
            cancellation_fee_percentage_at_creation=Decimal('10.0'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.commit()
        
        print(f"✓ Ordem criada: ID={order.id}, Status={order.status}, Valor=R$ {order.value}")
        
        # Testar acesso à rota com o cliente
        with app.test_client() as client_test:
            # Login como cliente
            response = client_test.post('/auth/login', data={
                'email': 'test_task14_cliente@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            assert response.status_code == 200, "Login do cliente falhou"
            print("✓ Cliente logado com sucesso")
            
            # Acessar detalhes da ordem
            response = client_test.get(f'/ordens/{order.id}', follow_redirects=True)
            assert response.status_code == 200, f"Falha ao acessar detalhes da ordem: {response.status_code}"
            print(f"✓ Cliente acessou detalhes da ordem {order.id}")
            
            # Verificar se os dados estão presentes na resposta
            response_data = response.data.decode('utf-8')
            assert 'Teste de Visualização de Ordem' in response_data, "Título da ordem não encontrado"
            assert 'R$ 200,00' in response_data or '200.00' in response_data, "Valor da ordem não encontrado"
            print("✓ Dados da ordem presentes na resposta")
            
            # Logout
            client_test.get('/auth/logout')
        
        # Testar acesso à rota com o prestador
        with app.test_client() as client_test:
            # Login como prestador
            response = client_test.post('/auth/login', data={
                'email': 'test_task14_prestador@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            assert response.status_code == 200, "Login do prestador falhou"
            print("✓ Prestador logado com sucesso")
            
            # Acessar detalhes da ordem
            response = client_test.get(f'/ordens/{order.id}', follow_redirects=True)
            assert response.status_code == 200, f"Falha ao acessar detalhes da ordem: {response.status_code}"
            print(f"✓ Prestador acessou detalhes da ordem {order.id}")
            
            # Verificar se os dados estão presentes na resposta
            response_data = response.data.decode('utf-8')
            assert 'Teste de Visualização de Ordem' in response_data, "Título da ordem não encontrado"
            print("✓ Dados da ordem presentes na resposta para prestador")
            
            # Logout
            client_test.get('/auth/logout')
        
        # Testar ordem com status servico_executado (para testar contador)
        order.status = 'servico_executado'
        order.completed_at = datetime.utcnow()
        order.confirmation_deadline = datetime.utcnow() + timedelta(hours=36)
        order.dispute_deadline = order.confirmation_deadline
        db.session.commit()
        
        print(f"✓ Ordem atualizada para status 'servico_executado'")
        
        with app.test_client() as client_test:
            # Login como cliente
            response = client_test.post('/auth/login', data={
                'email': 'test_task14_cliente@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            # Acessar detalhes da ordem
            response = client_test.get(f'/ordens/{order.id}', follow_redirects=True)
            assert response.status_code == 200, "Falha ao acessar ordem com status servico_executado"
            print("✓ Cliente acessou ordem com status 'servico_executado'")
            
            # Verificar se hours_remaining está sendo calculado
            assert order.hours_until_auto_confirmation is not None, "Horas restantes não calculadas"
            print(f"✓ Horas restantes calculadas: {order.hours_until_auto_confirmation:.2f}h")
            
            # Logout
            client_test.get('/auth/logout')
        
        # Testar acesso negado para usuário não autorizado
        cpf_outro = generate_unique_cpf()
        outro_usuario = User(
            nome='Outro Usuário',
            email='test_task14_outro@test.com',
            cpf=cpf_outro,
            phone='11999999016',
            roles='cliente'
        )
        outro_usuario.set_password('senha123')
        db.session.add(outro_usuario)
        db.session.commit()
        
        with app.test_client() as client_test:
            # Login como outro usuário
            response = client_test.post('/auth/login', data={
                'email': 'test_task14_outro@test.com',
                'password': 'senha123'
            }, follow_redirects=True)
            
            # Tentar acessar ordem de outro usuário
            response = client_test.get(f'/ordens/{order.id}', follow_redirects=True)
            response_data = response.data.decode('utf-8')
            
            # Deve ser redirecionado ou receber mensagem de erro
            assert 'não tem permissão' in response_data or response.status_code == 403, \
                "Usuário não autorizado conseguiu acessar ordem"
            print("✓ Acesso negado para usuário não autorizado")
            
            # Logout
            client_test.get('/auth/logout')
        
        # Limpar dados de teste
        test_users = User.query.filter(User.email.like('test_task14_%@test.com')).all()
        for user in test_users:
            Wallet.query.filter_by(user_id=user.id).delete()
        User.query.filter(User.email.like('test_task14_%@test.com')).delete()
        db.session.commit()
        print("✓ Dados de teste removidos\n")
        
        print("="*80)
        print("✅ TODOS OS TESTES DA TASK 14 PASSARAM COM SUCESSO!")
        print("="*80 + "\n")


if __name__ == '__main__':
    try:
        test_order_details_route()
        print("✅ Task 14 implementada com sucesso!")
    except AssertionError as e:
        print(f"\n❌ ERRO: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
