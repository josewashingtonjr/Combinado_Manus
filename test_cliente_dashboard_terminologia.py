#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, Order, Transaction, Wallet
from services.cliente_service import ClienteService
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
def sample_user_data(app):
    """Cria dados de exemplo para os testes"""
    with app.app_context():
        # Criar usuário cliente
        user = User(
            email='cliente@test.com',
            nome='Cliente Teste',
            cpf='123.456.789-00',
            phone='11999999999',
            roles='cliente',
            active=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira para o usuário
        WalletService.ensure_user_has_wallet(user.id)
        
        # Adicionar saldo inicial
        WalletService.credit_wallet(
            user.id, 
            500.0, 
            "Saldo inicial para testes",
            "deposito"
        )
        
        # Criar algumas transações de teste
        transactions = []
        for i in range(5):
            transaction = Transaction(
                user_id=user.id,
                type='compra_tokens' if i % 2 == 0 else 'pagamento',
                amount=100.0 if i % 2 == 0 else -50.0,
                description=f'Transação de teste {i}',
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            transactions.append(transaction)
            db.session.add(transaction)
        
        # Criar algumas ordens de teste
        orders = []
        for i in range(3):
            order = Order(
                client_id=user.id,
                title=f'Ordem {i}',
                description=f'Descrição da ordem {i}',
                value=150.0 + i * 25,
                status='concluida' if i == 0 else ('em_andamento' if i == 1 else 'disponivel')
            )
            orders.append(order)
            db.session.add(order)
        
        db.session.commit()
        
        return {
            'user': user,
            'transactions': transactions,
            'orders': orders
        }

class TestClienteDashboardTerminologia:
    """Testes para terminologia em R$ no dashboard do cliente"""
    
    def test_dashboard_data_real_values(self, app, sample_user_data):
        """Testa se o dashboard retorna dados reais da carteira"""
        with app.app_context():
            user = sample_user_data['user']
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Verificar se retorna valores reais (não zeros)
            assert dashboard_data['saldo_atual'] > 0
            assert dashboard_data['tokens_disponiveis'] > 0
            assert dashboard_data['transacoes_mes'] >= 0
            assert isinstance(dashboard_data['ordens_ativas'], int)
            assert isinstance(dashboard_data['ordens_concluidas'], int)
    
    def test_dashboard_data_structure(self, app, sample_user_data):
        """Testa a estrutura dos dados do dashboard"""
        with app.app_context():
            user = sample_user_data['user']
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Verificar campos obrigatórios
            required_fields = [
                'saldo_atual', 'tokens_disponiveis', 'saldo_bloqueado',
                'transacoes_mes', 'ordens_ativas', 'ordens_concluidas',
                'gasto_total_mes', 'economia_mes', 'ultima_transacao',
                'proximas_ordens', 'alertas'
            ]
            
            for field in required_fields:
                assert field in dashboard_data, f"Campo {field} não encontrado nos dados do dashboard"
    
    def test_wallet_data_real_values(self, app, sample_user_data):
        """Testa se os dados da carteira são reais"""
        with app.app_context():
            user = sample_user_data['user']
            wallet_data = ClienteService.get_wallet_data(user.id)
            
            # Verificar valores reais
            assert wallet_data['saldo_atual'] > 0
            assert wallet_data['tokens_disponiveis'] > 0
            assert isinstance(wallet_data['transacoes_recentes'], list)
            assert isinstance(wallet_data['estatisticas'], dict)
    
    def test_alertas_saldo_baixo(self, app, sample_user_data):
        """Testa sistema de alertas para saldo baixo"""
        with app.app_context():
            user = sample_user_data['user']
            
            # Reduzir saldo para testar alerta
            WalletService.debit_wallet(
                user.id,
                480.0,  # Deixar apenas R$ 20,00
                "Teste de saldo baixo",
                "teste"
            )
            
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Verificar se há alerta de saldo baixo
            alertas = dashboard_data['alertas']
            assert len(alertas) > 0
            
            # Verificar se há alerta de saldo baixo
            alerta_saldo_baixo = any(
                'Saldo baixo' in alerta['mensagem'] 
                for alerta in alertas
            )
            assert alerta_saldo_baixo, "Alerta de saldo baixo não foi gerado"
    
    def test_terminologia_sem_tokens(self, app, sample_user_data):
        """Testa se a terminologia não menciona 'tokens' para clientes"""
        with app.app_context():
            user = sample_user_data['user']
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Verificar alertas - não devem mencionar "tokens"
            for alerta in dashboard_data['alertas']:
                assert 'token' not in alerta['mensagem'].lower(), \
                    f"Alerta menciona 'tokens': {alerta['mensagem']}"
                assert 'saldo' in alerta['mensagem'].lower() or \
                       'R$' in alerta['mensagem'] or \
                       'ordem' in alerta['mensagem'].lower(), \
                    f"Alerta não usa terminologia adequada: {alerta['mensagem']}"
    
    def test_historico_transacoes_format(self, app, sample_user_data):
        """Testa formato do histórico de transações"""
        with app.app_context():
            user = sample_user_data['user']
            wallet_data = ClienteService.get_wallet_data(user.id)
            
            transacoes = wallet_data['transacoes_recentes']
            
            if transacoes:
                transacao = transacoes[0]
                
                # Verificar campos obrigatórios
                assert 'data' in transacao
                assert 'tipo' in transacao
                assert 'valor' in transacao
                assert 'descricao' in transacao
                assert 'status' in transacao
                
                # Verificar formato da data
                assert '/' in transacao['data']  # Formato brasileiro
    
    def test_estatisticas_financeiras(self, app, sample_user_data):
        """Testa cálculo das estatísticas financeiras"""
        with app.app_context():
            user = sample_user_data['user']
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Verificar se estatísticas são calculadas
            assert 'total_gasto_historico' in dashboard_data
            assert 'media_valor_ordem' in dashboard_data
            assert 'taxa_conclusao' in dashboard_data
            
            # Verificar se valores são numéricos
            assert isinstance(dashboard_data['total_gasto_historico'], (int, float))
            assert isinstance(dashboard_data['media_valor_ordem'], (int, float))
            assert isinstance(dashboard_data['taxa_conclusao'], (int, float))
            
            # Taxa de conclusão deve estar entre 0 e 100
            assert 0 <= dashboard_data['taxa_conclusao'] <= 100
    
    def test_proximas_ordens_format(self, app, sample_user_data):
        """Testa formato das próximas ordens"""
        with app.app_context():
            user = sample_user_data['user']
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            proximas_ordens = dashboard_data['proximas_ordens']
            
            if proximas_ordens:
                ordem = proximas_ordens[0]
                
                # Verificar campos obrigatórios
                assert 'titulo' in ordem
                assert 'data' in ordem
                assert 'status' in ordem
                assert 'valor' in ordem
                
                # Verificar formato da data
                assert '/' in ordem['data']  # Formato brasileiro
    
    def test_integration_with_wallet_service(self, app, sample_user_data):
        """Testa integração com WalletService"""
        with app.app_context():
            user = sample_user_data['user']
            
            # Obter dados via ClienteService
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            
            # Obter dados via WalletService
            wallet_info = WalletService.get_wallet_info(user.id)
            
            # Verificar consistência
            assert dashboard_data['saldo_atual'] == wallet_info['balance']
            assert dashboard_data['saldo_bloqueado'] == wallet_info['escrow_balance']
    
    def test_performance_dashboard_data(self, app, sample_user_data):
        """Testa performance da obtenção de dados do dashboard"""
        with app.app_context():
            user = sample_user_data['user']
            
            import time
            start_time = time.time()
            dashboard_data = ClienteService.get_dashboard_data(user.id)
            end_time = time.time()
            
            # Deve executar em menos de 1 segundo
            assert (end_time - start_time) < 1.0
            
            # Deve retornar dados válidos
            assert dashboard_data is not None
            assert isinstance(dashboard_data, dict)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])