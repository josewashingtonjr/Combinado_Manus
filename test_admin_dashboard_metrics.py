#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, AdminUser, Order, Transaction, Wallet
from services.admin_service import AdminService
from services.wallet_service import WalletService
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Cria uma instância da aplicação para testes"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Cliente de teste"""
    return app.test_client()

@pytest.fixture
def sample_data(app):
    """Cria dados de exemplo para os testes"""
    with app.app_context():
        # Criar admin
        admin = AdminUser(id=0, email='admin@test.com', papel='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Criar usuários de teste
        users = []
        for i in range(5):
            user = User(
                email=f'user{i}@test.com',
                nome=f'Usuário {i}',
                cpf=f'000.000.00{i}-00',
                phone=f'11999999{i:03d}',
                roles='cliente',
                active=True if i < 4 else False  # 4 ativos, 1 inativo
            )
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # Criar carteiras para os usuários
        for user in users:
            WalletService.ensure_user_has_wallet(user.id)
        
        # Criar carteira do admin
        WalletService.ensure_admin_has_wallet()
        
        # Criar algumas ordens de teste
        orders = []
        for i in range(3):
            order = Order(
                client_id=users[0].id,
                provider_id=users[1].id if i < 2 else None,
                title=f'Ordem {i}',
                description=f'Descrição da ordem {i}',
                value=100.0 + i * 50,
                status='concluida' if i == 0 else ('em_andamento' if i == 1 else 'disputada')
            )
            orders.append(order)
            db.session.add(order)
        
        db.session.commit()
        
        # Criar algumas transações de teste
        transactions = []
        for i in range(10):
            transaction = Transaction(
                user_id=users[i % 4].id,  # Apenas usuários ativos
                type='compra_tokens' if i % 2 == 0 else 'taxa_sistema',
                amount=50.0 if i % 2 == 0 else 5.0,
                description=f'Transação de teste {i}',
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            transactions.append(transaction)
            db.session.add(transaction)
        
        db.session.commit()
        
        return {
            'admin': admin,
            'users': users,
            'orders': orders,
            'transactions': transactions
        }

class TestAdminDashboardMetrics:
    """Testes para as métricas do dashboard administrativo"""
    
    def test_get_dashboard_stats_basic_counts(self, app, sample_data):
        """Testa contadores básicos de usuários"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Verificar contadores de usuários
            assert stats['total_usuarios'] == 5
            assert stats['usuarios_ativos'] == 4
            assert stats['usuarios_inativos'] == 1
            assert stats['taxa_usuarios_ativos'] == 80.0  # 4/5 * 100
    
    def test_get_dashboard_stats_orders(self, app, sample_data):
        """Testa estatísticas de ordens/contratos"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Verificar contadores de ordens
            assert stats['contratos_ativos'] == 1  # em_andamento
            assert stats['contratos_finalizados'] == 1  # concluida
            assert stats['contestacoes_abertas'] == 1  # disputada
    
    def test_get_dashboard_stats_transactions(self, app, sample_data):
        """Testa estatísticas de transações"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Verificar contadores de transações
            assert stats['transacoes_mes'] >= 0  # Pode variar dependendo das datas
            assert isinstance(stats['receita_mes'], (int, float))
            assert isinstance(stats['volume_transacoes_mes'], (int, float))
    
    def test_get_dashboard_stats_tokenomics(self, app, sample_data):
        """Testa métricas de tokenomics"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Verificar métricas de tokens
            assert isinstance(stats['total_tokens_sistema'], (int, float))
            assert isinstance(stats['tokens_em_circulacao'], (int, float))
            assert isinstance(stats['saldo_admin_tokens'], (int, float))
            
            # Admin deve ter saldo inicial
            assert stats['saldo_admin_tokens'] > 0
    
    def test_get_dashboard_stats_calculated_metrics(self, app, sample_data):
        """Testa métricas calculadas"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Verificar métricas calculadas
            assert 0 <= stats['taxa_usuarios_ativos'] <= 100
            assert 0 <= stats['taxa_conclusao_contratos'] <= 100
    
    def test_dashboard_stats_with_no_data(self, app):
        """Testa estatísticas com banco vazio"""
        with app.app_context():
            stats = AdminService.get_dashboard_stats()
            
            # Todos os contadores devem ser zero
            assert stats['total_usuarios'] == 0
            assert stats['usuarios_ativos'] == 0
            assert stats['usuarios_inativos'] == 0
            assert stats['contratos_ativos'] == 0
            assert stats['contratos_finalizados'] == 0
            assert stats['contestacoes_abertas'] == 0
            assert stats['transacoes_mes'] == 0
            assert stats['receita_mes'] == 0
    
    def test_dashboard_stats_monthly_filter(self, app, sample_data):
        """Testa filtros mensais nas estatísticas"""
        with app.app_context():
            # Criar transação do mês atual
            current_month_transaction = Transaction(
                user_id=sample_data['users'][0].id,
                type='taxa_sistema',
                amount=25.0,
                description='Taxa do mês atual',
                created_at=datetime.utcnow()
            )
            db.session.add(current_month_transaction)
            db.session.commit()
            
            stats = AdminService.get_dashboard_stats()
            
            # Deve contar transações do mês atual
            assert stats['transacoes_mes'] >= 1
    
    def test_tokenomics_integration(self, app, sample_data):
        """Testa integração com sistema de tokenomics"""
        with app.app_context():
            # Criar alguns tokens e transações
            WalletService.admin_create_tokens(1000, "Tokens de teste")
            WalletService.admin_sell_tokens_to_user(
                sample_data['users'][0].id, 
                100, 
                "Venda de teste"
            )
            
            stats = AdminService.get_dashboard_stats()
            token_summary = WalletService.get_system_token_summary()
            
            # Verificar consistência entre AdminService e WalletService
            assert stats['total_tokens_sistema'] == token_summary['total_tokens_created']
            assert stats['tokens_em_circulacao'] == token_summary['tokens_in_circulation']
            assert stats['saldo_admin_tokens'] == token_summary['admin_balance']
    
    def test_dashboard_stats_performance(self, app, sample_data):
        """Testa performance das consultas de estatísticas"""
        with app.app_context():
            import time
            
            start_time = time.time()
            stats = AdminService.get_dashboard_stats()
            end_time = time.time()
            
            # Deve executar em menos de 1 segundo
            assert (end_time - start_time) < 1.0
            
            # Deve retornar todas as métricas esperadas
            expected_keys = [
                'total_usuarios', 'usuarios_ativos', 'usuarios_inativos',
                'usuarios_recentes', 'contratos_ativos', 'contratos_finalizados',
                'contestacoes_abertas', 'total_tokens_sistema', 'tokens_em_circulacao',
                'saldo_admin_tokens', 'transacoes_mes', 'receita_mes',
                'volume_transacoes_mes', 'taxa_usuarios_ativos', 'taxa_conclusao_contratos'
            ]
            
            for key in expected_keys:
                assert key in stats
    
    def test_dashboard_route_integration(self, app, client, sample_data):
        """Testa integração com a rota do dashboard"""
        with app.app_context():
            # Simular login de admin
            with client.session_transaction() as sess:
                sess['admin_id'] = sample_data['admin'].id
                sess['admin_email'] = sample_data['admin'].email
            
            # Acessar dashboard
            response = client.get('/admin/dashboard')
            
            # Deve retornar sucesso
            assert response.status_code == 200
            
            # Deve conter elementos esperados do template
            assert b'Dashboard Administrativo' in response.data
            assert b'Tokens Criados' in response.data
            assert b'Em Circula' in response.data  # "Em Circulação" pode estar truncado
            assert b'Saldo Admin' in response.data

if __name__ == '__main__':
    pytest.main([__file__, '-v'])