#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do gerenciador de estados dos convites
Valida transições de estado, bloqueios e auditoria
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sys
import os

# Configurar Flask app
from flask import Flask
from models import db
from config import Config

def create_test_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app
from models import db, User, Invite, Proposal
from services.invite_state_manager import InviteStateManager, InviteState
from services.proposal_service import ProposalService
from services.invite_service import InviteService
from datetime import datetime, timedelta
from decimal import Decimal

def test_invite_state_transitions():
    """Testa as transições de estado dos convites"""
    
    app = create_test_app()
    
    with app.app_context():
        # Limpar dados de teste
        db.session.query(Proposal).delete()
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        print("=== TESTE: Transições de Estado dos Convites ===")
        
        # Criar usuários de teste
        cliente = User(
            email='cliente@teste.com',
            nome='Cliente Teste',
            cpf='12345678901',
            phone='11999999999',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            email='prestador@teste.com',
            nome='Prestador Teste',
            cpf='98765432100',
            phone='11888888888',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras e adicionar saldo para os testes
        from services.wallet_service import WalletService
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo suficiente para o cliente (valor da proposta + taxa)
        WalletService.credit_wallet(cliente.id, 500.00, "Saldo para testes")
        WalletService.credit_wallet(prestador.id, 100.00, "Saldo para testes")
        
        # Criar convite
        delivery_date = datetime.utcnow() + timedelta(days=7)
        convite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste',
            service_description='Descrição do serviço de teste',
            original_value=Decimal('100.00'),
            delivery_date=delivery_date,
            status='pendente'
        )
        
        db.session.add(convite)
        db.session.commit()
        
        print(f"✓ Convite criado: ID {convite.id}")
        
        # Teste 1: Estado inicial
        current_state = InviteStateManager.get_current_state(convite)
        print(f"✓ Estado inicial: {current_state.value}")
        assert current_state == InviteState.PENDENTE, f"Estado inicial deveria ser PENDENTE, mas é {current_state.value}"
        
        # Teste 2: Verificar se pode ser aceito
        can_accept, reason = InviteStateManager.can_be_accepted(convite)
        print(f"✓ Pode ser aceito: {can_accept} - {reason}")
        assert can_accept, f"Convite deveria poder ser aceito: {reason}"
        
        # Teste 3: Verificar se pode criar proposta
        can_create_proposal, reason = InviteStateManager.can_create_proposal(convite)
        print(f"✓ Pode criar proposta: {can_create_proposal} - {reason}")
        assert can_create_proposal, f"Deveria poder criar proposta: {reason}"
        
        # Teste 4: Criar proposta (transição para PROPOSTA_ENVIADA)
        try:
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('120.00'),
                justification='Aumento devido à complexidade'
            )
            print(f"✓ Proposta criada: {result['message']}")
            
            # Verificar estado após criar proposta
            db.session.refresh(convite)
            current_state = InviteStateManager.get_current_state(convite)
            print(f"✓ Estado após proposta: {current_state.value}")
            assert current_state == InviteState.PROPOSTA_ENVIADA, f"Estado deveria ser PROPOSTA_ENVIADA, mas é {current_state.value}"
            
        except Exception as e:
            print(f"✗ Erro ao criar proposta: {str(e)}")
            return False
        
        # Teste 5: Verificar bloqueio de aceitação durante proposta
        can_accept, reason = InviteStateManager.can_be_accepted(convite)
        print(f"✓ Pode ser aceito com proposta pendente: {can_accept} - {reason}")
        assert not can_accept, f"Convite NÃO deveria poder ser aceito com proposta pendente"
        assert "aguardando aprovação" in reason.lower(), f"Motivo deveria mencionar aprovação: {reason}"
        
        # Teste 6: Verificar bloqueio de nova proposta
        can_create_proposal, reason = InviteStateManager.can_create_proposal(convite)
        print(f"✓ Pode criar nova proposta: {can_create_proposal} - {reason}")
        assert not can_create_proposal, f"NÃO deveria poder criar nova proposta: {reason}"
        
        # Teste 7: Aprovar proposta (transição para PROPOSTA_ACEITA)
        try:
            proposal = convite.get_active_proposal()
            
            # Debug: verificar estado antes da aprovação
            db.session.refresh(convite)
            debug_state = InviteStateManager.get_current_state(convite)
            print(f"DEBUG: Estado antes da aprovação: {debug_state.value}")
            print(f"DEBUG: has_active_proposal: {convite.has_active_proposal}")
            print(f"DEBUG: current_proposal_id: {convite.current_proposal_id}")
            print(f"DEBUG: proposal status: {proposal.status if proposal else 'None'}")
            
            result = ProposalService.approve_proposal(
                proposal_id=proposal.id,
                client_id=cliente.id,
                client_response_reason='Valor justo'
            )
            print(f"✓ Proposta aprovada: {result['message']}")
            
            # Verificar estado após aprovação
            db.session.refresh(convite)
            current_state = InviteStateManager.get_current_state(convite)
            print(f"✓ Estado após aprovação: {current_state.value}")
            assert current_state == InviteState.PROPOSTA_ACEITA, f"Estado deveria ser PROPOSTA_ACEITA, mas é {current_state.value}"
            
        except Exception as e:
            print(f"✗ Erro ao aprovar proposta: {str(e)}")
            return False
        
        # Teste 8: Verificar que agora pode ser aceito
        can_accept, reason = InviteStateManager.can_be_accepted(convite)
        print(f"✓ Pode ser aceito após aprovação: {can_accept} - {reason}")
        assert can_accept, f"Convite deveria poder ser aceito após aprovação da proposta: {reason}"
        
        # Teste 9: Aceitar convite (transição para ACEITO)
        try:
            result = InviteService.accept_invite(
                token=convite.token,
                provider_id=prestador.id,
                final_value=float(convite.effective_value)
            )
            print(f"✓ Convite aceito: {result['message']}")
            
            # Verificar estado após aceitação
            db.session.refresh(convite)
            current_state = InviteStateManager.get_current_state(convite)
            print(f"✓ Estado após aceitação: {current_state.value}")
            assert current_state == InviteState.ACEITO, f"Estado deveria ser ACEITO, mas é {current_state.value}"
            
        except Exception as e:
            print(f"✗ Erro ao aceitar convite: {str(e)}")
            return False
        
        # Teste 10: Verificar ações disponíveis
        actions = InviteStateManager.get_available_actions(convite)
        print(f"✓ Ações disponíveis: {actions}")
        assert 'converter_em_ordem' in actions.get('client', []), "Cliente deveria poder converter em ordem"
        
        # Teste 11: Verificar descrição do estado
        description = InviteStateManager.get_state_description(convite)
        print(f"✓ Descrição do estado: {description['status']}")
        assert description['status'] == 'Convite Aceito', f"Descrição incorreta: {description['status']}"
        
        print("\n=== TESTE: Fluxo de Rejeição de Proposta ===")
        
        # Criar novo convite para testar rejeição
        convite2 = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste 2',
            service_description='Descrição do serviço de teste 2',
            original_value=Decimal('200.00'),
            delivery_date=delivery_date,
            status='pendente'
        )
        
        db.session.add(convite2)
        db.session.commit()
        
        # Criar proposta
        result = ProposalService.create_proposal(
            invite_id=convite2.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('250.00'),
            justification='Aumento devido à complexidade'
        )
        print(f"✓ Segunda proposta criada: {result['message']}")
        
        # Rejeitar proposta
        proposal2 = convite2.get_active_proposal()
        result = ProposalService.reject_proposal(
            proposal_id=proposal2.id,
            client_id=cliente.id,
            client_response_reason='Valor muito alto'
        )
        print(f"✓ Proposta rejeitada: {result['message']}")
        
        # Verificar estado após rejeição
        db.session.refresh(convite2)
        current_state = InviteStateManager.get_current_state(convite2)
        print(f"✓ Estado após rejeição: {current_state.value}")
        assert current_state == InviteState.PROPOSTA_REJEITADA, f"Estado deveria ser PROPOSTA_REJEITADA, mas é {current_state.value}"
        
        # Verificar que pode aceitar valor original
        can_accept, reason = InviteStateManager.can_be_accepted(convite2)
        print(f"✓ Pode aceitar valor original após rejeição: {can_accept} - {reason}")
        assert can_accept, f"Deveria poder aceitar valor original após rejeição: {reason}"
        
        print("\n=== TESTE: Cancelamento de Proposta ===")
        
        # Criar terceiro convite para testar cancelamento
        convite3 = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste 3',
            service_description='Descrição do serviço de teste 3',
            original_value=Decimal('150.00'),
            delivery_date=delivery_date,
            status='pendente'
        )
        
        db.session.add(convite3)
        db.session.commit()
        
        # Criar proposta
        result = ProposalService.create_proposal(
            invite_id=convite3.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('180.00'),
            justification='Ajuste de preço'
        )
        print(f"✓ Terceira proposta criada: {result['message']}")
        
        # Cancelar proposta
        proposal3 = convite3.get_active_proposal()
        result = ProposalService.cancel_proposal(
            proposal_id=proposal3.id,
            prestador_id=prestador.id
        )
        print(f"✓ Proposta cancelada: {result['message']}")
        
        # Verificar estado após cancelamento
        db.session.refresh(convite3)
        current_state = InviteStateManager.get_current_state(convite3)
        print(f"✓ Estado após cancelamento: {current_state.value}")
        assert current_state == InviteState.PENDENTE, f"Estado deveria voltar para PENDENTE, mas é {current_state.value}"
        
        # Verificar que pode aceitar normalmente
        can_accept, reason = InviteStateManager.can_be_accepted(convite3)
        print(f"✓ Pode aceitar após cancelamento: {can_accept} - {reason}")
        assert can_accept, f"Deveria poder aceitar após cancelamento: {reason}"
        
        print("\n✅ TODOS OS TESTES DE ESTADO PASSARAM!")
        return True

def test_invalid_transitions():
    """Testa transições inválidas para garantir que são bloqueadas"""
    
    print("\n=== TESTE: Transições Inválidas ===")
    
    # Criar um convite aceito para testar transições inválidas
    app = create_test_app()
    
    with app.app_context():
        from services.wallet_service import WalletService
        
        # Criar usuários
        cliente = User(
            email='cliente2@teste.com',
            nome='Cliente Teste 2',
            cpf='11111111111',
            phone='11777777777',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            email='prestador2@teste.com',
            nome='Prestador Teste 2',
            cpf='22222222222',
            phone='11666666666',
            roles='prestador'
        )
        prestador.set_password('senha123')
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        WalletService.credit_wallet(cliente.id, 500.00, "Saldo para testes")
        WalletService.credit_wallet(prestador.id, 100.00, "Saldo para testes")
        
        # Criar convite aceito
        delivery_date = datetime.utcnow() + timedelta(days=7)
        convite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste Inválido',
            service_description='Descrição do serviço de teste inválido',
            original_value=Decimal('100.00'),
            delivery_date=delivery_date,
            status='aceito'
        )
        
        db.session.add(convite)
        db.session.commit()
        
        # Tentar transição inválida
        try:
            # Tentar ir direto de ACEITO para PROPOSTA_ENVIADA (inválido)
            convite.transition_to(InviteState.PROPOSTA_ENVIADA, None, "Teste inválido")
            print("✗ Transição inválida foi permitida!")
            return False
        except ValueError as e:
            print(f"✓ Transição inválida bloqueada corretamente: {str(e)}")
        
        # Testar verificação de transição
        can_transition, reason = InviteStateManager.can_transition_to(convite, InviteState.PROPOSTA_ENVIADA)
        print(f"✓ Verificação de transição: {can_transition} - {reason}")
        assert not can_transition, "Transição inválida deveria ser bloqueada"
        
        print("✅ TESTES DE TRANSIÇÕES INVÁLIDAS PASSARAM!")
        return True

if __name__ == '__main__':
    print("Iniciando testes do gerenciador de estados dos convites...")
    
    success = True
    
    try:
        success &= test_invite_state_transitions()
        success &= test_invalid_transitions()
        
        if success:
            print("\n🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
        else:
            print("\n❌ ALGUNS TESTES FALHARAM!")
            
    except Exception as e:
        print(f"\n💥 ERRO DURANTE OS TESTES: {str(e)}")
        import traceback
        traceback.print_exc()
        success = False
    
    exit(0 if success else 1)