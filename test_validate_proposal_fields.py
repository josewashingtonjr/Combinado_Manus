#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validação de integridade dos campos de proposta após transições
Requirements: 9.4, 9.5, 10.5
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Proposal
from services.invite_state_manager import InviteStateManager, InviteState

def setup_test_data():
    """Criar dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        db.session.query(Proposal).delete()
        db.session.query(Invite).delete()
        db.session.commit()
        
        # Buscar ou criar usuários
        cliente = User.query.filter_by(cpf='12345678901').first()
        if not cliente:
            cliente = User(
                nome='Cliente Validação',
                email='cliente_val@test.com',
                roles='cliente',
                cpf='12345678901'
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
            db.session.commit()
        
        prestador = User.query.filter_by(cpf='98765432109').first()
        if not prestador:
            prestador = User(
                nome='Prestador Validação',
                email='prestador_val@test.com',
                roles='prestador',
                cpf='98765432109'
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
            db.session.commit()
        
        return cliente, prestador

def test_validate_pendente_state():
    """Testar validação do estado PENDENTE"""
    print("\n=== Teste 1: Validação Estado PENDENTE ===")
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar convite no estado PENDENTE
        invite = Invite(
            client_id=cliente.id,
            prestador_id=prestador.id,
            service_title='Teste Validação PENDENTE',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        # Validar - deve estar OK
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PENDENTE)
        
        if is_valid:
            print("✅ Estado PENDENTE válido (campos limpos)")
        else:
            print(f"❌ Estado PENDENTE inválido: {errors}")
            return False
        
        # Simular inconsistência: setar has_active_proposal sem proposta
        invite.has_active_proposal = True
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PENDENTE)
        
        if not is_valid and any('has_active_proposal' in err for err in errors):
            print("✅ Inconsistência detectada corretamente (has_active_proposal=True em PENDENTE)")
        else:
            print(f"❌ Falhou em detectar inconsistência: {errors}")
            return False
        
        return True

def test_validate_proposta_enviada_state():
    """Testar validação do estado PROPOSTA_ENVIADA"""
    print("\n=== Teste 2: Validação Estado PROPOSTA_ENVIADA ===")
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            prestador_id=prestador.id,
            service_title='Teste Validação PROPOSTA_ENVIADA',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar proposta
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Teste validação',
            status='pending'
        )
        db.session.add(proposal)
        
        # Setar campos de proposta ativa
        invite.has_active_proposal = True
        invite.current_proposal_id = proposal.id
        db.session.commit()
        
        # Validar - deve estar OK
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PROPOSTA_ENVIADA)
        
        if is_valid:
            print("✅ Estado PROPOSTA_ENVIADA válido (campos corretos)")
        else:
            print(f"❌ Estado PROPOSTA_ENVIADA inválido: {errors}")
            return False
        
        # Simular inconsistência: limpar has_active_proposal
        invite.has_active_proposal = False
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PROPOSTA_ENVIADA)
        
        if not is_valid and any('has_active_proposal' in err for err in errors):
            print("✅ Inconsistência detectada corretamente (has_active_proposal=False em PROPOSTA_ENVIADA)")
        else:
            print(f"❌ Falhou em detectar inconsistência: {errors}")
            return False
        
        return True

def test_validate_proposta_aceita_state():
    """Testar validação do estado PROPOSTA_ACEITA"""
    print("\n=== Teste 3: Validação Estado PROPOSTA_ACEITA ===")
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            prestador_id=prestador.id,
            service_title='Teste Validação PROPOSTA_ACEITA',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar proposta aceita
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Teste validação',
            status='accepted',
            responded_at=datetime.utcnow()
        )
        db.session.add(proposal)
        
        # Setar campos corretos para PROPOSTA_ACEITA
        invite.has_active_proposal = False  # Deve ser False
        invite.current_proposal_id = proposal.id  # Mantém referência
        invite.effective_value = Decimal('150.00')  # Valor efetivo
        db.session.commit()
        
        # Validar - deve estar OK
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PROPOSTA_ACEITA)
        
        if is_valid:
            print("✅ Estado PROPOSTA_ACEITA válido (campos corretos)")
        else:
            print(f"❌ Estado PROPOSTA_ACEITA inválido: {errors}")
            return False
        
        # Simular inconsistência: effective_value diferente de proposed_value
        invite.effective_value = Decimal('200.00')
        is_valid, errors = InviteStateManager.validate_proposal_fields(invite, InviteState.PROPOSTA_ACEITA)
        
        if not is_valid and any('não corresponde' in err for err in errors):
            print("✅ Inconsistência detectada corretamente (effective_value diferente de proposed_value)")
        else:
            print(f"❌ Falhou em detectar inconsistência: {errors}")
            return False
        
        return True

def test_validate_after_transition():
    """Testar validação automática após transição"""
    print("\n=== Teste 4: Validação Automática Após Transição ===")
    
    with app.app_context():
        cliente, prestador = setup_test_data()
        
        # Criar convite
        invite = Invite(
            client_id=cliente.id,
            prestador_id=prestador.id,
            service_title='Teste Validação Transição',
            service_description='Descrição teste',
            original_value=Decimal('100.00'),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        # Criar proposta
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=prestador.id,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Teste validação',
            status='pending'
        )
        db.session.add(proposal)
        
        # Setar campos de proposta ativa
        invite.has_active_proposal = True
        invite.current_proposal_id = proposal.id
        db.session.commit()
        
        # Transicionar para PROPOSTA_ENVIADA (deve validar automaticamente)
        try:
            result = InviteStateManager.transition_to_state(
                invite, 
                InviteState.PROPOSTA_ENVIADA,
                prestador.id,
                "Teste de validação"
            )
            print(f"✅ Transição para PROPOSTA_ENVIADA validada com sucesso")
        except ValueError as e:
            print(f"❌ Transição falhou na validação: {e}")
            return False
        
        # Aceitar proposta
        proposal.status = 'accepted'
        proposal.responded_at = datetime.utcnow()
        invite.effective_value = proposal.proposed_value
        db.session.commit()
        
        # Transicionar para PROPOSTA_ACEITA (deve validar automaticamente)
        try:
            result = InviteStateManager.transition_to_state(
                invite,
                InviteState.PROPOSTA_ACEITA,
                cliente.id,
                "Cliente aceitou proposta"
            )
            print(f"✅ Transição para PROPOSTA_ACEITA validada com sucesso")
        except ValueError as e:
            print(f"❌ Transição falhou na validação: {e}")
            return False
        
        # Verificar que has_active_proposal foi limpo
        if not invite.has_active_proposal:
            print("✅ has_active_proposal foi limpo corretamente")
        else:
            print("❌ has_active_proposal não foi limpo")
            return False
        
        return True

def run_all_tests():
    """Executar todos os testes"""
    print("=" * 60)
    print("TESTES DE VALIDAÇÃO DE INTEGRIDADE DOS CAMPOS DE PROPOSTA")
    print("=" * 60)
    
    tests = [
        test_validate_pendente_state,
        test_validate_proposta_enviada_state,
        test_validate_proposta_aceita_state,
        test_validate_after_transition
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total}")
    
    if passed == total:
        print("✅ TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
