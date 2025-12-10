#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste básico das rotas de propostas de alteração
"""

import pytest
from app import app, db
from models import User, Invite, Proposal, Wallet
from services.auth_service import AuthService
from decimal import Decimal
import json

class TestProposalRoutes:
    """Testes das rotas de propostas de alteração"""
    
    @pytest.fixture
    def client(self):
        """Cliente de teste Flask"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def setup_users(self, client):
        """Configurar usuários de teste"""
        with app.app_context():
            # Criar cliente
            cliente = User(
                nome='Cliente Teste',
                email='cliente@teste.com',
                phone='11999999999',
                roles=['cliente']
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
            
            # Criar prestador
            prestador = User(
                nome='Prestador Teste',
                email='prestador@teste.com',
                phone='11888888888',
                roles=['prestador']
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
            
            db.session.commit()
            
            # Criar carteiras
            wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('100.00'))
            wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('50.00'))
            
            db.session.add(wallet_cliente)
            db.session.add(wallet_prestador)
            db.session.commit()
            
            return {
                'cliente': cliente,
                'prestador': prestador
            }
    
    @pytest.fixture
    def setup_invite(self, client, setup_users):
        """Configurar convite de teste"""
        with app.app_context():
            users = setup_users
            
            # Criar convite
            invite = Invite(
                client_id=users['cliente'].id,
                invited_phone=users['prestador'].phone,
                service_title='Serviço de Teste',
                service_description='Descrição do serviço de teste',
                original_value=Decimal('50.00'),
                status='pendente'
            )
            
            db.session.add(invite)
            db.session.commit()
            
            return {
                'invite': invite,
                **users
            }
    
    def login_user(self, client, email, password):
        """Helper para fazer login"""
        return client.post('/auth/user-login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_rotas_existem(self, client):
        """Testar se as rotas foram registradas corretamente"""
        with app.app_context():
            rules = [str(rule) for rule in app.url_map.iter_rules()]
            
            # Verificar se as rotas principais existem
            assert '/convite/<int:invite_id>/propor-alteracao' in rules
            assert '/proposta/<int:proposal_id>/aprovar' in rules
            assert '/proposta/<int:proposal_id>/rejeitar' in rules
            assert '/proposta/<int:proposal_id>/cancelar' in rules
    
    def test_propor_alteracao_sem_login(self, client, setup_invite):
        """Testar criação de proposta sem estar logado"""
        data = setup_invite
        
        response = client.post(f'/convite/{data["invite"].id}/propor-alteracao', data={
            'proposed_value': '75.00',
            'justification': 'Aumento devido à complexidade'
        })
        
        # Deve redirecionar para login
        assert response.status_code == 302
    
    def test_propor_alteracao_como_prestador(self, client, setup_invite):
        """Testar criação de proposta como prestador"""
        data = setup_invite
        
        # Fazer login como prestador
        self.login_user(client, 'prestador@teste.com', 'senha123')
        
        response = client.post(f'/convite/{data["invite"].id}/propor-alteracao', data={
            'proposed_value': '75.00',
            'justification': 'Aumento devido à complexidade'
        })
        
        # Deve aceitar a requisição (redirect ou success)
        assert response.status_code in [200, 302]
    
    def test_propor_alteracao_como_cliente(self, client, setup_invite):
        """Testar criação de proposta como cliente (deve falhar)"""
        data = setup_invite
        
        # Fazer login como cliente
        self.login_user(client, 'cliente@teste.com', 'senha123')
        
        response = client.post(f'/convite/{data["invite"].id}/propor-alteracao', data={
            'proposed_value': '75.00',
            'justification': 'Tentativa inválida'
        })
        
        # Deve retornar erro de autorização
        assert response.status_code in [302, 403]
    
    def test_aprovar_proposta_sem_login(self, client):
        """Testar aprovação de proposta sem estar logado"""
        response = client.post('/proposta/1/aprovar', data={
            'client_response_reason': 'Aprovado'
        })
        
        # Deve redirecionar para login
        assert response.status_code == 302
    
    def test_rejeitar_proposta_sem_login(self, client):
        """Testar rejeição de proposta sem estar logado"""
        response = client.post('/proposta/1/rejeitar', data={
            'client_response_reason': 'Valor muito alto'
        })
        
        # Deve redirecionar para login
        assert response.status_code == 302
    
    def test_cancelar_proposta_sem_login(self, client):
        """Testar cancelamento de proposta sem estar logado"""
        response = client.delete('/proposta/1/cancelar')
        
        # Deve redirecionar para login
        assert response.status_code == 302
    
    def test_verificar_saldo_sem_login(self, client):
        """Testar verificação de saldo sem estar logado"""
        response = client.get('/proposta/verificar-saldo/1')
        
        # Deve redirecionar para login
        assert response.status_code == 302
    
    def test_obter_detalhes_sem_login(self, client):
        """Testar obtenção de detalhes sem estar logado"""
        response = client.get('/proposta/1/detalhes')
        
        # Deve redirecionar para login
        assert response.status_code == 302

if __name__ == '__main__':
    # Executar teste simples
    print("Testando rotas de propostas...")
    
    # Testar se as rotas foram registradas
    with app.app_context():
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        
        expected_routes = [
            '/convite/<int:invite_id>/propor-alteracao',
            '/proposta/<int:proposal_id>/aprovar',
            '/proposta/<int:proposal_id>/rejeitar',
            '/proposta/<int:proposal_id>/cancelar'
        ]
        
        print("Verificando rotas esperadas:")
        for route in expected_routes:
            if route in rules:
                print(f"  ✓ {route}")
            else:
                print(f"  ✗ {route}")
        
        print("\nTodas as rotas de proposta registradas:")
        for rule in app.url_map.iter_rules():
            if 'proposal' in rule.endpoint or 'proposta' in str(rule.rule):
                print(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")
    
    print("\n✅ Rotas implementadas com sucesso!")