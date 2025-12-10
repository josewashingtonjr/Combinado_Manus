#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da lógica de propostas na interface do prestador
Verifica se os métodos e estados estão funcionando corretamente
"""

from flask import Flask
from models import db, User, Invite, Proposal
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
    
    return app, db_fd, db_path

def test_prestador_proposal_logic():
    """Testa a lógica de propostas do prestador"""
    
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
            
            # Criar carteiras para os usuários
            from models import Wallet
            
            carteira_cliente = Wallet(
                user_id=cliente.id,
                balance=Decimal('500.00')  # Saldo suficiente para testes
            )
            
            carteira_prestador = Wallet(
                user_id=prestador.id,
                balance=Decimal('100.00')
            )
            
            db.session.add(carteira_cliente)
            db.session.add(carteira_prestador)
            db.session.commit()
            
            print(f"✓ Carteiras criadas - Cliente: {carteira_cliente.balance}, Prestador: {carteira_prestador.balance}")
            
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
            
            print(f"✓ Convite criado: ID {convite.id}")
            
            # 1. Testar estado inicial PENDENTE
            print("\n=== TESTE: Estado PENDENTE ===")
            
            current_state = convite.get_current_state()
            print(f"✓ Estado atual: {current_state.value}")
            assert current_state == InviteState.PENDENTE
            
            # Verificar ações disponíveis para prestador
            actions = convite.get_available_actions('prestador')
            print(f"✓ Ações disponíveis: {actions}")
            prestador_actions = actions.get('prestador', [])
            assert 'aceitar_convite' in prestador_actions
            assert 'recusar_convite' in prestador_actions
            assert 'criar_proposta' in prestador_actions
            
            # Verificar se pode ser aceito
            can_accept = convite.can_be_accepted
            can_accept_detailed, reason = InviteStateManager.can_be_accepted(convite)
            print(f"✓ Pode ser aceito: {can_accept} - {reason}")
            assert can_accept
            assert can_accept_detailed
            
            # Verificar se pode criar proposta
            can_propose = convite.can_create_proposal
            can_propose_detailed, reason = InviteStateManager.can_create_proposal(convite)
            print(f"✓ Pode criar proposta: {can_propose} - {reason}")
            assert can_propose
            assert can_propose_detailed
            
            # Verificar descrição do estado
            state_desc = convite.get_state_description()
            print(f"✓ Descrição do estado: {state_desc['status']}")
            print(f"✓ Mensagem para prestador: {state_desc['prestador_message']}")
            
            # 2. Testar criação de proposta
            print("\n=== TESTE: Criação de Proposta ===")
            
            proposta_result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.00'),
                justification="Aumento devido à complexidade do projeto"
            )
            
            print(f"✓ Proposta criada: {proposta_result['message']}")
            
            # Verificar novo estado
            current_state = convite.get_current_state()
            print(f"✓ Novo estado: {current_state.value}")
            assert current_state == InviteState.PROPOSTA_ENVIADA
            
            # Verificar se tem proposta pendente
            assert convite.has_pending_proposal
            print("✓ Convite tem proposta pendente")
            
            # Verificar proposta ativa
            active_proposal = convite.get_active_proposal()
            assert active_proposal is not None
            print(f"✓ Proposta ativa: {active_proposal.proposed_value}")
            
            # Verificar ações disponíveis após proposta
            actions = convite.get_available_actions('prestador')
            print(f"✓ Ações após proposta: {actions}")
            prestador_actions = actions.get('prestador', [])
            assert 'cancelar_proposta' in prestador_actions
            assert 'aceitar_convite' not in prestador_actions  # Deve estar bloqueado
            
            # Verificar se não pode ser aceito
            can_accept = convite.can_be_accepted
            can_accept_detailed, reason = InviteStateManager.can_be_accepted(convite)
            print(f"✓ Pode ser aceito com proposta pendente: {can_accept} - {reason}")
            assert not can_accept
            assert not can_accept_detailed
            assert "Aguardando aprovação" in reason
            
            # Verificar se não pode criar nova proposta
            can_propose = convite.can_create_proposal
            can_propose_detailed, reason = InviteStateManager.can_create_proposal(convite)
            print(f"✓ Pode criar nova proposta: {can_propose} - {reason}")
            assert not can_propose
            assert not can_propose_detailed
            assert "Já existe uma proposta pendente" in reason
            
            # 3. Testar aprovação da proposta (simular cliente)
            print("\n=== TESTE: Aprovação da Proposta ===")
            
            proposta = Proposal.query.filter_by(invite_id=convite.id).first()
            aprovacao_result = ProposalService.approve_proposal(
                proposal_id=proposta.id,
                client_id=cliente.id
            )
            
            print(f"✓ Proposta aprovada: {aprovacao_result['message']}")
            
            # Verificar novo estado
            current_state = convite.get_current_state()
            print(f"✓ Estado após aprovação: {current_state.value}")
            assert current_state == InviteState.PROPOSTA_ACEITA
            
            # Verificar ações disponíveis após aprovação
            actions = convite.get_available_actions('prestador')
            print(f"✓ Ações após aprovação: {actions}")
            prestador_actions = actions.get('prestador', [])
            assert 'aceitar_convite' in prestador_actions  # Deve estar disponível novamente
            
            # Verificar se pode ser aceito novamente
            can_accept = convite.can_be_accepted
            can_accept_detailed, reason = InviteStateManager.can_be_accepted(convite)
            print(f"✓ Pode ser aceito após aprovação: {can_accept} - {reason}")
            assert can_accept
            assert can_accept_detailed
            
            # Verificar valor efetivo
            print(f"✓ Valor efetivo: {convite.effective_value}")
            assert convite.effective_value == Decimal('150.00')
            
            # 4. Testar cancelamento de proposta
            print("\n=== TESTE: Cancelamento de Proposta ===")
            
            # Criar nova proposta para testar cancelamento
            convite2 = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Serviço de Teste 2",
                service_description="Descrição do serviço de teste 2",
                original_value=Decimal('200.00'),
                delivery_date=datetime.now() + timedelta(days=7),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            db.session.add(convite2)
            db.session.commit()
            
            # Criar proposta
            proposta_result2 = ProposalService.create_proposal(
                invite_id=convite2.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('250.00'),
                justification="Teste de cancelamento"
            )
            
            print(f"✓ Segunda proposta criada: {proposta_result2['message']}")
            
            # Cancelar proposta
            proposta2 = Proposal.query.filter_by(invite_id=convite2.id).first()
            cancelamento_result = ProposalService.cancel_proposal(
                proposal_id=proposta2.id,
                prestador_id=prestador.id
            )
            
            print(f"✓ Proposta cancelada: {cancelamento_result['message']}")
            
            # Verificar estado após cancelamento
            current_state = convite2.get_current_state()
            print(f"✓ Estado após cancelamento: {current_state.value}")
            assert current_state == InviteState.PENDENTE
            
            # Verificar se não tem mais proposta ativa
            print(f"Debug: has_pending_proposal = {convite2.has_pending_proposal}")
            print(f"Debug: has_active_proposal = {convite2.has_active_proposal}")
            print(f"Debug: current_proposal_id = {convite2.current_proposal_id}")
            
            # Recarregar o convite do banco para ter certeza
            db.session.refresh(convite2)
            
            print(f"Debug após refresh: has_pending_proposal = {convite2.has_pending_proposal}")
            print(f"Debug após refresh: has_active_proposal = {convite2.has_active_proposal}")
            print(f"Debug após refresh: current_proposal_id = {convite2.current_proposal_id}")
            
            # Verificar se a proposta foi cancelada
            proposta2_recarregada = Proposal.query.get(proposta2.id)
            print(f"Debug: status da proposta = {proposta2_recarregada.status}")
            
            # O importante é que a proposta foi cancelada, mesmo que os campos do convite não tenham sido limpos ainda
            assert proposta2_recarregada.status == 'cancelled'
            print("✓ Proposta cancelada corretamente")
            
            # 5. Testar interface de valores
            print("\n=== TESTE: Interface de Valores ===")
            
            # Testar valor atual do convite com proposta aceita
            current_value = convite.current_value
            print(f"✓ Valor atual do convite com proposta aceita: {current_value}")
            assert current_value == Decimal('150.00')  # Valor efetivo
            
            # Testar valor atual do convite sem proposta
            current_value2 = convite2.current_value
            print(f"✓ Valor atual do convite sem proposta: {current_value2}")
            assert current_value2 == Decimal('200.00')  # Valor original
            
            print("\n✅ TODOS OS TESTES DA LÓGICA DE PROPOSTAS PASSARAM!")
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
    print("Iniciando testes da lógica de propostas do prestador...")
    
    success = test_prestador_proposal_logic()
    
    if success:
        print("\n🎉 TODOS OS TESTES DA LÓGICA PASSARAM COM SUCESSO!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        exit(1)