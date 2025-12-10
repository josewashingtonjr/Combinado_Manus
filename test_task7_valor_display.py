"""
Teste para validar a exibição correta de valores no template do prestador
Tarefa 7: Atualizar template do prestador para exibir valor correto
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models import db, User, Invite, Proposal, InviteState
from app import create_app


@pytest.fixture
def app():
    """Criar aplicação de teste"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste"""
    return app.test_client()


@pytest.fixture
def setup_users(app):
    """Criar usuários de teste"""
    with app.app_context():
        # Cliente
        cliente = User(
            nome='Cliente Teste',
            email='cliente@test.com',
            papel='cliente'
        )
        cliente.set_password('senha123')
        db.session.add(cliente)
        
        # Prestador
        prestador = User(
            nome='Prestador Teste',
            email='prestador@test.com',
            papel='prestador'
        )
        prestador.set_password('senha123')
        db.session.add(prestador)
        
        db.session.commit()
        
        return {
            'cliente_id': cliente.id,
            'prestador_id': prestador.id,
            'cliente_email': cliente.email,
            'prestador_email': prestador.email
        }


def login_prestador(client, email='prestador@test.com'):
    """Fazer login como prestador"""
    return client.post('/auth/user/login', data={
        'email': email,
        'password': 'senha123'
    }, follow_redirects=True)


def test_display_original_value_sem_proposta(app, client, setup_users):
    """
    Testar que o template mostra original_value quando não há proposta
    Requirements: 4.2, 5.2
    """
    with app.app_context():
        # Criar convite sem proposta
        cliente = User.query.get(setup_users['cliente_id'])
        prestador = User.query.get(setup_users['prestador_id'])
        
        invite = Invite(
            client_id=cliente.id,
            service_title='Serviço Teste',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            expires_at=datetime.utcnow() + timedelta(days=3),
            status=InviteState.PENDENTE.value
        )
        db.session.add(invite)
        db.session.commit()
        
        token = invite.token
    
    # Login como prestador
    login_prestador(client)
    
    # Acessar página do convite
    response = client.get(f'/prestador/convite/{token}')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Verificar que mostra valor original
    assert 'R$ 100,00' in html
    assert 'Valor do Serviço:' in html
    
    # Verificar que NÃO mostra proposta pendente
    assert 'Aguardando resposta do cliente' not in html
    assert 'Proposta aprovada' not in html
    
    # Verificar ícone correto (tag para valor original)
    assert 'fa-tag' in html or 'Valor definido pelo cliente' in html


def test_display_proposed_value_com_proposta_pendente(app, client, setup_users):
    """
    Testar que o template mostra proposed_value quando proposta está pendente
    Requirements: 4.2, 5.2
    """
    with app.app_context():
        cliente = User.query.get(setup_users['cliente_id'])
        prestador = User.query.get(setup_users['prestador_id'])
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            service_title='Serviço Teste',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            expires_at=datetime.utcnow() + timedelta(days=3),
            status=InviteState.PROPOSTA_ENVIADA.value,
            has_active_proposal=True
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar proposta pendente
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Preciso de mais recursos',
            status='pending'
        )
        db.session.add(proposal)
        invite.current_proposal_id = proposal.id
        db.session.commit()
        
        token = invite.token
    
    # Login como prestador
    login_prestador(client)
    
    # Acessar página do convite
    response = client.get(f'/prestador/convite/{token}')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Verificar que mostra valor proposto
    assert 'R$ 150,00' in html
    
    # Verificar que mostra valor original como referência
    assert 'R$ 100,00' in html
    assert 'Valor original:' in html
    
    # Verificar indicação de proposta pendente
    assert 'Aguardando resposta do cliente' in html
    
    # Verificar cálculo de diferença
    assert 'Aumento de' in html or 'R$ 50,00' in html
    
    # Verificar ícone de relógio (pendente)
    assert 'fa-clock' in html


def test_display_effective_value_com_proposta_aceita(app, client, setup_users):
    """
    Testar que o template mostra effective_value quando proposta foi aceita
    Requirements: 4.2, 5.2
    """
    with app.app_context():
        cliente = User.query.get(setup_users['cliente_id'])
        prestador = User.query.get(setup_users['prestador_id'])
        
        # Criar convite com proposta aceita
        invite = Invite(
            client_id=cliente.id,
            service_title='Serviço Teste',
            service_description='Descrição do serviço',
            original_value=Decimal('100.00'),
            effective_value=Decimal('150.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            expires_at=datetime.utcnow() + timedelta(days=3),
            status=InviteState.PROPOSTA_ACEITA.value,
            has_active_proposal=False
        )
        db.session.add(invite)
        db.session.flush()
        
        # Criar proposta aceita (para referência histórica)
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Preciso de mais recursos',
            status='accepted',
            responded_at=datetime.utcnow()
        )
        db.session.add(proposal)
        invite.current_proposal_id = proposal.id
        db.session.commit()
        
        token = invite.token
    
    # Login como prestador
    login_prestador(client)
    
    # Acessar página do convite
    response = client.get(f'/prestador/convite/{token}')
    
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Verificar que mostra valor efetivo
    assert 'R$ 150,00' in html
    
    # Verificar que mostra valor original riscado
    assert 'Valor original:' in html
    assert '<s' in html  # Tag de texto riscado
    assert 'R$ 100,00' in html
    
    # Verificar indicação de proposta aprovada
    assert 'Proposta aprovada' in html or 'aprovada pelo cliente' in html
    
    # Verificar ícone de check (aprovado)
    assert 'fa-check-circle' in html
    
    # Verificar cor verde (sucesso)
    assert 'text-success' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
