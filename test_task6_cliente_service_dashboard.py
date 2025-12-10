#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Teste para validar a implementação da Tarefa 6:
Atualizar ClienteService para usar DashboardDataService
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, Order, Wallet
from services.cliente_service import ClienteService
from services.dashboard_data_service import DashboardDataService
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
def sample_data(app):
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
        
        user_id = user.id
        
        # Criar carteira para o usuário
        WalletService.ensure_user_has_wallet(user_id)
        
        # Adicionar saldo inicial
        WalletService.credit_wallet(
            user_id, 
            500.0, 
            "Saldo inicial para testes",
            "deposito"
        )
        
        # Criar prestador
        provider = User(
            email='prestador@test.com',
            nome='Prestador Teste',
            cpf='987.654.321-00',
            phone='11888888888',
            roles='prestador',
            active=True
        )
        provider.set_password('password123')
        db.session.add(provider)
        db.session.commit()
        
        provider_id = provider.id
        
        # Criar ordens de teste com service_deadline
        order_ids = []
        for i in range(3):
            order = Order(
                client_id=user_id,
                provider_id=provider_id if i < 2 else None,
                title=f'Ordem {i}',
                description=f'Descrição da ordem {i}',
                value=150.0 + i * 25,
                status='aceita' if i == 0 else ('em_andamento' if i == 1 else 'concluida'),
                service_deadline=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            db.session.add(order)
            db.session.flush()
            order_ids.append(order.id)
        
        db.session.commit()
        
        return {
            'user_id': user_id,
            'provider_id': provider_id,
            'order_ids': order_ids
        }

class TestTask6ClienteServiceDashboard:
    """Testes para a Tarefa 6: Atualizar ClienteService para usar DashboardDataService"""
    
    def test_get_dashboard_data_uses_dashboard_service(self, app, sample_data):
        """Testa se get_dashboard_data usa DashboardDataService.get_dashboard_metrics"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            # Obter dados do dashboard
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar que os dados incluem informações do DashboardDataService
            assert 'ordens_em_aberto' in dashboard_data, "Deve incluir ordens_em_aberto"
            assert 'fundos_bloqueados_detalhados' in dashboard_data, "Deve incluir fundos_bloqueados_detalhados"
            assert 'ordens_por_status' in dashboard_data, "Deve incluir ordens_por_status"
            
            print("\n✓ get_dashboard_data usa DashboardDataService corretamente")
    
    def test_dashboard_data_includes_open_orders(self, app, sample_data):
        """Testa se dashboard_data inclui ordens em aberto"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar ordens em aberto
            ordens_em_aberto = dashboard_data['ordens_em_aberto']
            assert isinstance(ordens_em_aberto, list), "ordens_em_aberto deve ser uma lista"
            
            # Deve ter 2 ordens em aberto (aceita e em_andamento)
            assert len(ordens_em_aberto) == 2, f"Deve ter 2 ordens em aberto, encontrou {len(ordens_em_aberto)}"
            
            # Verificar estrutura das ordens
            for ordem in ordens_em_aberto:
                assert 'id' in ordem
                assert 'title' in ordem
                assert 'value' in ordem
                assert 'status' in ordem
                assert 'related_user_name' in ordem
            
            print(f"\n✓ Dashboard inclui {len(ordens_em_aberto)} ordens em aberto")
    
    def test_dashboard_data_includes_blocked_funds(self, app, sample_data):
        """Testa se dashboard_data inclui fundos bloqueados detalhados"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar fundos bloqueados
            fundos_bloqueados = dashboard_data['fundos_bloqueados_detalhados']
            assert isinstance(fundos_bloqueados, list), "fundos_bloqueados_detalhados deve ser uma lista"
            
            # Verificar estrutura
            for item in fundos_bloqueados:
                assert 'order_id' in item
                assert 'title' in item
                assert 'amount' in item
                assert 'status' in item
            
            print(f"\n✓ Dashboard inclui detalhamento de fundos bloqueados")
    
    def test_dashboard_data_includes_alerts(self, app, sample_data):
        """Testa se dashboard_data inclui alertas apropriados"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar alertas
            alertas = dashboard_data['alertas']
            assert isinstance(alertas, list), "alertas deve ser uma lista"
            
            # Verificar estrutura dos alertas
            for alerta in alertas:
                assert 'tipo' in alerta or 'type' in alerta
                assert 'mensagem' in alerta or 'message' in alerta
            
            print(f"\n✓ Dashboard inclui {len(alertas)} alertas")
    
    def test_get_open_orders_for_client_method(self, app, sample_data):
        """Testa o método get_open_orders_for_client"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            # Chamar o novo método
            open_orders = ClienteService.get_open_orders_for_client(user_id)
            
            # Verificar retorno
            assert isinstance(open_orders, list), "Deve retornar uma lista"
            assert len(open_orders) == 2, f"Deve retornar 2 ordens em aberto, retornou {len(open_orders)}"
            
            # Verificar estrutura
            for ordem in open_orders:
                assert 'id' in ordem
                assert 'title' in ordem
                assert 'value' in ordem
                assert 'status' in ordem
                assert 'related_user_name' in ordem
                assert 'status_display' in ordem
            
            print(f"\n✓ get_open_orders_for_client retorna {len(open_orders)} ordens formatadas")
    
    def test_dashboard_data_balance_info(self, app, sample_data):
        """Testa se informações de saldo estão corretas"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar campos de saldo
            assert 'saldo_atual' in dashboard_data
            assert 'tokens_disponiveis' in dashboard_data
            assert 'saldo_bloqueado' in dashboard_data
            
            # Verificar que são valores numéricos
            assert isinstance(dashboard_data['saldo_atual'], (int, float))
            assert isinstance(dashboard_data['tokens_disponiveis'], (int, float))
            assert isinstance(dashboard_data['saldo_bloqueado'], (int, float))
            
            # Saldo deve ser positivo (adicionamos 500.0)
            assert dashboard_data['saldo_atual'] > 0
            
            print(f"\n✓ Saldo disponível: R$ {dashboard_data['saldo_atual']:.2f}")
            print(f"✓ Saldo bloqueado: R$ {dashboard_data['saldo_bloqueado']:.2f}")
    
    def test_dashboard_data_orders_count(self, app, sample_data):
        """Testa se contadores de ordens estão corretos"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar contadores
            assert 'ordens_ativas' in dashboard_data
            assert 'ordens_concluidas' in dashboard_data
            
            # Deve ter 2 ordens ativas (aceita + em_andamento)
            assert dashboard_data['ordens_ativas'] == 2, \
                f"Deve ter 2 ordens ativas, encontrou {dashboard_data['ordens_ativas']}"
            
            # Deve ter 1 ordem concluída
            assert dashboard_data['ordens_concluidas'] == 1, \
                f"Deve ter 1 ordem concluída, encontrou {dashboard_data['ordens_concluidas']}"
            
            print(f"\n✓ Ordens ativas: {dashboard_data['ordens_ativas']}")
            print(f"✓ Ordens concluídas: {dashboard_data['ordens_concluidas']}")
    
    def test_integration_with_dashboard_data_service(self, app, sample_data):
        """Testa integração completa com DashboardDataService"""
        with app.app_context():
            user_id = sample_data['user_id']
            
            # Obter dados diretamente do DashboardDataService
            metrics = DashboardDataService.get_dashboard_metrics(user_id, 'cliente')
            
            # Obter dados via ClienteService
            dashboard_data = ClienteService.get_dashboard_data(user_id)
            
            # Verificar consistência
            assert dashboard_data['saldo_atual'] == metrics['balance']['available'], \
                "Saldo disponível deve ser consistente"
            
            assert dashboard_data['saldo_bloqueado'] == metrics['balance']['blocked'], \
                "Saldo bloqueado deve ser consistente"
            
            assert dashboard_data['ordens_ativas'] == metrics['open_orders_count'], \
                "Contagem de ordens ativas deve ser consistente"
            
            print("\n✓ Integração com DashboardDataService está consistente")

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
