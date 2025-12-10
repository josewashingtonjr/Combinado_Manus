#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste de renderização do template do prestador
Verifica se o template renderiza corretamente com os novos campos
"""

from flask import Flask, render_template_string
from models import db, User, Invite, Proposal, Wallet
from services.invite_state_manager import InviteStateManager, InviteState
from services.proposal_service import ProposalService
from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import os

def create_test_app():
    """Cria app de teste"""
    app = Flask(__name__)
    
    # Configuração de teste
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Inicializar extensões
    db.init_app(app)
    
    # Registrar filtro de formatação de moeda
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None:
            return "R$ 0,00"
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return app, db_fd, db_path

def test_template_rendering():
    """Testa se o template renderiza corretamente com os novos campos"""
    
    app, db_fd, db_path = create_test_app()
    
    try:
        with app.app_context():
            # Criar tabelas
            db.create_all()
            
            # Criar usuários de teste
            cliente = User(
                nome="Cliente Teste",
                email="cliente@teste.com",
                phone="11999999999",
                cpf="12345678901",
                password_hash="hash_teste",
                roles="cliente"
            )
            
            prestador = User(
                nome="Prestador Teste", 
                email="prestador@teste.com",
                phone="11888888888",
                cpf="98765432100",
                password_hash="hash_teste",
                roles="prestador"
            )
            
            db.session.add(cliente)
            db.session.add(prestador)
            db.session.commit()
            
            # Criar carteiras
            carteira_cliente = Wallet(user_id=cliente.id, balance=Decimal('500.00'))
            carteira_prestador = Wallet(user_id=prestador.id, balance=Decimal('100.00'))
            
            db.session.add(carteira_cliente)
            db.session.add(carteira_prestador)
            db.session.commit()
            
            # Criar convite de teste
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Serviço de Teste",
                service_description="Descrição do serviço de teste",
                original_value=Decimal('100.00'),
                delivery_date=datetime.now() + timedelta(days=7),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            db.session.add(convite)
            db.session.commit()
            
            print(f"✓ Dados de teste criados")
            
            # Testar template básico com estado PENDENTE
            print("\n=== TESTE: Template Estado PENDENTE ===")
            
            template_test = """
            {% set current_state = invite.get_current_state() %}
            {% set state_info = invite.get_state_description() %}
            {% set available_actions = invite.get_available_actions('prestador') %}
            
            Estado: {{ current_state.value }}
            Status: {{ state_info.status }}
            Mensagem: {{ state_info.prestador_message }}
            Ações: {{ available_actions.prestador|join(', ') }}
            Valor Original: {{ invite.original_value|format_currency }}
            Pode Aceitar: {{ invite.can_be_accepted }}
            Pode Propor: {{ invite.can_create_proposal }}
            """
            
            result = render_template_string(template_test, invite=convite, user=prestador)
            print("✓ Template renderizado com sucesso para estado PENDENTE")
            print(f"Resultado:\n{result.strip()}")
            
            # Criar proposta e testar template com estado PROPOSTA_ENVIADA
            print("\n=== TESTE: Template Estado PROPOSTA_ENVIADA ===")
            
            proposta_result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.00'),
                justification="Aumento devido à complexidade"
            )
            
            template_test_proposta = """
            {% set current_state = invite.get_current_state() %}
            {% set state_info = invite.get_state_description() %}
            {% set available_actions = invite.get_available_actions('prestador') %}
            {% set active_proposal = invite.get_active_proposal() %}
            
            Estado: {{ current_state.value }}
            Status: {{ state_info.status }}
            Tem Proposta Pendente: {{ invite.has_pending_proposal }}
            {% if active_proposal %}
            Valor Proposto: {{ active_proposal.proposed_value|format_currency }}
            Justificativa: {{ active_proposal.justification }}
            {% endif %}
            Ações: {{ available_actions.prestador|join(', ') }}
            Pode Aceitar: {{ invite.can_be_accepted }}
            """
            
            result = render_template_string(template_test_proposta, invite=convite, user=prestador)
            print("✓ Template renderizado com sucesso para estado PROPOSTA_ENVIADA")
            print(f"Resultado:\n{result.strip()}")
            
            # Aprovar proposta e testar template com estado PROPOSTA_ACEITA
            print("\n=== TESTE: Template Estado PROPOSTA_ACEITA ===")
            
            proposta = Proposal.query.filter_by(invite_id=convite.id).first()
            aprovacao_result = ProposalService.approve_proposal(
                proposal_id=proposta.id,
                client_id=cliente.id
            )
            
            template_test_aceita = """
            {% set current_state = invite.get_current_state() %}
            {% set state_info = invite.get_state_description() %}
            {% set available_actions = invite.get_available_actions('prestador') %}
            
            Estado: {{ current_state.value }}
            Status: {{ state_info.status }}
            Valor Efetivo: {{ invite.effective_value|format_currency }}
            Valor Atual: {{ invite.current_value|format_currency }}
            Ações: {{ available_actions.prestador|join(', ') }}
            Pode Aceitar: {{ invite.can_be_accepted }}
            """
            
            result = render_template_string(template_test_aceita, invite=convite, user=prestador)
            print("✓ Template renderizado com sucesso para estado PROPOSTA_ACEITA")
            print(f"Resultado:\n{result.strip()}")
            
            print("\n✅ TODOS OS TESTES DE TEMPLATE PASSARAM!")
            return True
                
    except Exception as e:
        print(f"✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar arquivos temporários
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass

if __name__ == '__main__':
    print("Iniciando testes de renderização do template...")
    
    success = test_template_rendering()
    
    if success:
        print("\n🎉 TODOS OS TESTES DE TEMPLATE PASSARAM COM SUCESSO!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        exit(1)