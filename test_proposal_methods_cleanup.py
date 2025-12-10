#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Teste para validar que os métodos accept(), reject() e cancel() 
da classe Proposal não fazem limpeza duplicada de campos.

Tarefa 2: Remover limpeza duplicada dos métodos do modelo Proposal
"""

from app import app
from models import db, User, Invite, Proposal
from datetime import datetime, timedelta
from decimal import Decimal

def test_proposal_methods_cleanup():
    """Testa que os métodos da Proposal não fazem limpeza duplicada"""
    
    with app.app_context():
        # Limpar dados de teste anteriores
        Proposal.query.filter_by(prestador_id=9999).delete()
        Invite.query.filter_by(client_id=9999).delete()
        User.query.filter_by(id=9999).delete()
        db.session.commit()
        
        print("\n" + "="*70)
        print("TESTE: Métodos Proposal - Sem Limpeza Duplicada")
        print("="*70)
        
        # 1. Criar usuário de teste
        print("\n1. Criando usuário de teste...")
        user = User(
            id=9999,
            email='test_proposal@test.com',
            nome='Test User',
            cpf='12345678901',
            password_hash='hash',
            roles='cliente,prestador'
        )
        db.session.add(user)
        db.session.commit()
        print("   ✓ Usuário criado")
        
        # 2. Criar convite de teste
        print("\n2. Criando convite de teste...")
        invite = Invite(
            client_id=9999,
            invited_phone='11999999999',
            service_title='Teste Proposta',
            service_description='Teste',
            service_category='teste',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente'
        )
        db.session.add(invite)
        db.session.commit()
        print(f"   ✓ Convite criado (ID: {invite.id})")
        
        # 3. Criar proposta de teste
        print("\n3. Criando proposta de teste...")
        proposal = Proposal(
            invite_id=invite.id,
            prestador_id=9999,
            original_value=Decimal('100.00'),
            proposed_value=Decimal('150.00'),
            justification='Teste de proposta',
            status='pending'
        )
        db.session.add(proposal)
        db.session.commit()
        print(f"   ✓ Proposta criada (ID: {proposal.id})")
        
        # Simular que a proposta foi ativada no convite
        invite.has_active_proposal = True
        invite.current_proposal_id = proposal.id
        db.session.commit()
        
        print(f"\n   Estado inicial do convite:")
        print(f"   - has_active_proposal: {invite.has_active_proposal}")
        print(f"   - current_proposal_id: {invite.current_proposal_id}")
        print(f"   - effective_value: {invite.effective_value}")
        
        # 4. Testar método accept()
        print("\n4. Testando método accept()...")
        print("   Chamando proposal.accept()...")
        proposal.accept("Aprovado para teste")
        db.session.commit()
        
        print(f"\n   Após accept():")
        print(f"   - Proposta status: {proposal.status}")
        print(f"   - Proposta responded_at: {proposal.responded_at}")
        print(f"   - Convite effective_value: {invite.effective_value}")
        print(f"   - Convite has_active_proposal: {invite.has_active_proposal}")
        print(f"   - Convite current_proposal_id: {invite.current_proposal_id}")
        
        # Validações para accept()
        assert proposal.status == 'accepted', "Status deveria ser 'accepted'"
        assert proposal.responded_at is not None, "responded_at deveria estar setado"
        assert invite.effective_value == Decimal('150.00'), "effective_value deveria ser 150.00"
        # has_active_proposal e current_proposal_id NÃO devem ser limpos pelo método accept()
        assert invite.has_active_proposal == True, "has_active_proposal NÃO deve ser limpo por accept()"
        assert invite.current_proposal_id == proposal.id, "current_proposal_id NÃO deve ser limpo por accept()"
        print("\n   ✓ accept() funciona corretamente - seta effective_value mas não limpa campos")
        
        # 5. Testar método reject()
        print("\n5. Testando método reject()...")
        
        # Resetar proposta para testar reject
        proposal.status = 'pending'
        proposal.responded_at = None
        invite.has_active_proposal = True
        invite.current_proposal_id = proposal.id
        invite.effective_value = None
        db.session.commit()
        
        print("   Chamando proposal.reject()...")
        proposal.reject("Rejeitado para teste")
        db.session.commit()
        
        print(f"\n   Após reject():")
        print(f"   - Proposta status: {proposal.status}")
        print(f"   - Proposta responded_at: {proposal.responded_at}")
        print(f"   - Convite effective_value: {invite.effective_value}")
        print(f"   - Convite has_active_proposal: {invite.has_active_proposal}")
        print(f"   - Convite current_proposal_id: {invite.current_proposal_id}")
        
        # Validações para reject()
        assert proposal.status == 'rejected', "Status deveria ser 'rejected'"
        assert proposal.responded_at is not None, "responded_at deveria estar setado"
        # Campos do convite NÃO devem ser limpos pelo método reject()
        assert invite.has_active_proposal == True, "has_active_proposal NÃO deve ser limpo por reject()"
        assert invite.current_proposal_id == proposal.id, "current_proposal_id NÃO deve ser limpo por reject()"
        print("\n   ✓ reject() funciona corretamente - não limpa campos do convite")
        
        # 6. Testar método cancel()
        print("\n6. Testando método cancel()...")
        
        # Resetar proposta para testar cancel
        proposal.status = 'pending'
        proposal.responded_at = None
        invite.has_active_proposal = True
        invite.current_proposal_id = proposal.id
        invite.effective_value = None
        db.session.commit()
        
        print("   Chamando proposal.cancel()...")
        proposal.cancel()
        db.session.commit()
        
        print(f"\n   Após cancel():")
        print(f"   - Proposta status: {proposal.status}")
        print(f"   - Proposta responded_at: {proposal.responded_at}")
        print(f"   - Convite effective_value: {invite.effective_value}")
        print(f"   - Convite has_active_proposal: {invite.has_active_proposal}")
        print(f"   - Convite current_proposal_id: {invite.current_proposal_id}")
        
        # Validações para cancel()
        assert proposal.status == 'cancelled', "Status deveria ser 'cancelled'"
        assert proposal.responded_at is not None, "responded_at deveria estar setado"
        # Campos do convite NÃO devem ser limpos pelo método cancel()
        assert invite.has_active_proposal == True, "has_active_proposal NÃO deve ser limpo por cancel()"
        assert invite.current_proposal_id == proposal.id, "current_proposal_id NÃO deve ser limpo por cancel()"
        print("\n   ✓ cancel() funciona corretamente - não limpa campos do convite")
        
        # Limpar dados de teste
        print("\n7. Limpando dados de teste...")
        db.session.delete(proposal)
        db.session.delete(invite)
        db.session.delete(user)
        db.session.commit()
        print("   ✓ Dados de teste removidos")
        
        print("\n" + "="*70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*70)
        print("\nResumo:")
        print("- accept() seta effective_value mas não limpa has_active_proposal/current_proposal_id")
        print("- reject() não limpa nenhum campo do convite")
        print("- cancel() não limpa nenhum campo do convite")
        print("\nA limpeza dos campos será feita pelo InviteStateManager durante as transições.")
        print("="*70 + "\n")

if __name__ == '__main__':
    test_proposal_methods_cleanup()
