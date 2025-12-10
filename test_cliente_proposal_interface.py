#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da interface do cliente para aprovação de propostas
Tarefa 8: Desenvolver interface do cliente para aprovação de propostas
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Invite, Proposal
from services.auth_service import AuthService
from services.proposal_service import ProposalService
from services.balance_validator import BalanceValidator

class TestClienteProposalInterface:
    """Testes da interface do cliente para propostas"""
    
    @pytest.fixture
    def app(self):
        """Criar aplicação de teste"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Cliente de teste"""
        return app.test_client()
    
    @pytest.fixture
    def setup_users(self, app):
        """Configurar usuários de teste"""
        with app.app_context():
            # Cliente
            cliente = User(
                email='cliente@test.com',
                nome='Cliente Teste',
                cpf='12345678901',
                phone='11999999999',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            # Prestador
            prestador = User(
                email='prestador@test.com',
                nome='Prestador Teste',
                cpf='98765432100',
                phone='11888888888',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db.session.add_all([cliente, prestador])
            db.session.commit()
            
            return {
                'cliente': cliente,
                'prestador': prestador
            }
    
    @pytest.fixture
    def setup_invite_with_proposal(self, app, setup_users):
        """Configurar convite com proposta"""
        with app.app_context():
            users = setup_users
            
            # Criar convite
            invite = Invite(
                client_id=users['cliente'].id,
                invited_phone=users['prestador'].phone,
                service_title='Serviço de Teste',
                service_description='Descrição do serviço',
                service_category='limpeza',
                original_value=Decimal('100.00'),
                delivery_date=datetime.now() + timedelta(days=7),
                expires_at=datetime.now() + timedelta(days=3),
                status='proposta_enviada'
            )
            
            db.session.add(invite)
            db.session.flush()
            
            # Criar proposta
            proposal = Proposal(
                invite_id=invite.id,
                prestador_id=users['prestador'].id,
                original_value=Decimal('100.00'),
                proposed_value=Decimal('150.00'),
                justification='Serviço mais complexo que o esperado',
                status='pending'
            )
            
            db.session.add(proposal)
            db.session.flush()
            
            # Configurar proposta ativa no convite
            invite.has_active_proposal = True
            invite.current_proposal_id = proposal.id
            
            db.session.commit()
            
            return {
                'invite': invite,
                'proposal': proposal,
                'users': users
            }
    
    def test_ver_convite_com_proposta(self, client, setup_invite_with_proposal):
        """Testar visualização de convite com proposta ativa"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        assert response.status_code == 200
        
        # Verificar se a proposta é exibida
        html = response.get_data(as_text=True)
        assert 'Proposta de Alteração' in html
        assert 'R$ 100,00' in html  # Valor original
        assert 'R$ 150,00' in html  # Valor proposto
        assert 'Serviço mais complexo' in html  # Justificativa
        
        # Verificar botões de ação
        assert 'Aceitar Proposta' in html
        assert 'Rejeitar Proposta' in html
    
    def test_verificacao_saldo_proposta_ajax(self, client, setup_invite_with_proposal):
        """Testar verificação de saldo via AJAX"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Fazer requisição AJAX para verificar saldo
        response = client.get(f'/proposta/verificar-saldo/{data["proposal"].id}')
        
        assert response.status_code == 200
        
        json_data = response.get_json()
        assert json_data['success'] == True
        assert 'balance_check' in json_data
        assert 'proposed_value' in json_data
        assert json_data['proposed_value'] == 150.0
    
    def test_modal_rejeicao_proposta(self, client, setup_invite_with_proposal):
        """Testar modal de rejeição de proposta"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        html = response.get_data(as_text=True)
        
        # Verificar se modal de rejeição está presente
        assert 'rejectProposalModal' in html
        assert 'Motivo da rejeição' in html
        assert 'client_response_reason' in html
    
    def test_modal_adicionar_saldo(self, client, setup_invite_with_proposal):
        """Testar modal de adicionar saldo"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        html = response.get_data(as_text=True)
        
        # Verificar se modal de adicionar saldo está presente
        assert 'addBalanceModal' in html
        assert 'Saldo Insuficiente' in html
        assert 'Valor Necessário' in html
        assert 'Taxa de Contestação' in html
    
    def test_javascript_funcionalidades(self, client, setup_invite_with_proposal):
        """Testar se JavaScript necessário está presente"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        html = response.get_data(as_text=True)
        
        # Verificar funções JavaScript
        assert 'checkProposalBalance' in html
        assert 'displayBalanceStatus' in html
        assert 'showAddBalanceModal' in html
        assert 'acceptProposal' in html
    
    def test_comparacao_valores_visual(self, client, setup_invite_with_proposal):
        """Testar comparação visual de valores"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        html = response.get_data(as_text=True)
        
        # Verificar comparação de valores
        assert 'Valor Original' in html
        assert 'Valor Proposto' in html
        assert 'Diferença' in html
        assert '+R$ 50,00' in html  # Diferença de aumento
    
    def test_calculadora_valor_necessario(self, client, setup_invite_with_proposal):
        """Testar calculadora de valor necessário"""
        data = setup_invite_with_proposal
        
        # Fazer login como cliente
        with client.session_transaction() as sess:
            sess['user_id'] = data['users']['cliente'].id
            sess['user_roles'] = ['cliente']
        
        # Acessar página do convite
        response = client.get(f'/cliente/convites/{data["invite"].id}')
        
        html = response.get_data(as_text=True)
        
        # Verificar elementos da calculadora
        assert 'Valor da Proposta' in html
        assert 'Taxa de Contestação' in html
        assert 'Total Necessário' in html
        assert 'proposal-value' in html
        assert 'contestation-fee' in html

if __name__ == '__main__':
    pytest.main([__file__, '-v'])