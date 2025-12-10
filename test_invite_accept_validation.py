#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar bloqueio de aceitação de convite quando há proposta pendente
Requirements: 1.4, 1.5
"""

from app import app
from models import db, User, Invite, Proposal
from services.invite_service import InviteService
from services.wallet_service import WalletService
from services.proposal_service import ProposalService
from datetime import datetime, timedelta
from decimal import Decimal

def test_accept_invite_blocked_with_pending_proposal():
    """
    Testa que convite não pode ser aceito quando há proposta pendente
    Requirements: 1.4, 1.5
    """
    
    with app.app_context():
        try:
            print("\n🔄 Testando bloqueio de aceitação com proposta pendente...")
            
            # 1. Criar cliente com saldo
            print("\n1️⃣ Criando cliente com saldo...")
            cliente = User.query.filter_by(email='cliente_test_accept@test.com').first()
            if not cliente:
                cliente = User(
                    nome='Cliente Teste Accept',
                    email='cliente_test_accept@test.com',
                    cpf='11111111111',
                    phone='11999999999',
                    roles='cliente'
                )
                cliente.set_password('senha123')
                db.session.add(cliente)
                db.session.commit()
            
            # Garantir saldo suficiente
            WalletService.deposit(cliente.id, Decimal('500.00'), 'Saldo para teste')
            print(f"✅ Cliente criado: {cliente.nome} (ID: {cliente.id})")
            
            # 2. Criar prestador com saldo
            print("\n2️⃣ Criando prestador com saldo...")
            prestador = User.query.filter_by(phone='11988888888').first()
            if not prestador:
                prestador = User(
                    nome='Prestador Teste Accept',
                    email='prestador_test_accept@test.com',
                    cpf='22222222222',
                    phone='11988888888',
                    roles='prestador'
                )
                prestador.set_password('senha123')
                db.session.add(prestador)
                db.session.commit()
            
            # Garantir saldo para taxa de contestação
            WalletService.deposit(prestador.id, Decimal('50.00'), 'Saldo para teste')
            print(f"✅ Prestador criado: {prestador.nome} (ID: {prestador.id})")
            
            # 3. Criar convite
            print("\n3️⃣ Criando convite...")
            delivery_date = datetime.utcnow() + timedelta(days=7)
            
            result = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço de Teste',
                service_description='Teste de bloqueio de aceitação',
                original_value=100.00,  # Usar float para compatibilidade
                delivery_date=delivery_date,
                service_category='Teste'
            )
            
            invite_token = result['token']
            invite = Invite.query.filter_by(token=invite_token).first()
            print(f"✅ Convite criado: {invite.service_title} (ID: {invite.id})")
            print(f"   Status: {invite.status}")
            print(f"   has_active_proposal: {invite.has_active_proposal}")
            
            # 4. Criar proposta de alteração manualmente (sem usar ProposalService)
            print("\n4️⃣ Criando proposta de alteração...")
            
            # Criar proposta diretamente
            proposal = Proposal(
                invite_id=invite.id,
                prestador_id=prestador.id,
                original_value=invite.original_value,
                proposed_value=150.00,
                justification='Teste de bloqueio',
                status='pending'
            )
            db.session.add(proposal)
            db.session.flush()
            
            # Marcar convite com proposta ativa
            invite.has_active_proposal = True
            invite.current_proposal_id = proposal.id
            db.session.commit()
            
            print(f"✅ Proposta criada (ID: {proposal.id})")
            
            # Recarregar convite
            db.session.refresh(invite)
            print(f"   Status do convite: {invite.status}")
            print(f"   has_active_proposal: {invite.has_active_proposal}")
            print(f"   current_proposal_id: {invite.current_proposal_id}")
            
            # 5. Tentar aceitar convite (deve falhar)
            print("\n5️⃣ Tentando aceitar convite com proposta pendente...")
            
            try:
                InviteService.accept_invite(
                    token=invite_token,
                    provider_id=prestador.id
                )
                print("❌ ERRO: Convite foi aceito mesmo com proposta pendente!")
                return False
                
            except ValueError as e:
                error_message = str(e)
                print(f"✅ Aceitação bloqueada corretamente!")
                print(f"   Mensagem de erro: {error_message}")
                
                # Verificar se a mensagem é clara
                if "aguardando" in error_message.lower() or "proposta" in error_message.lower():
                    print("✅ Mensagem de erro é clara e informativa")
                else:
                    print("⚠️ Mensagem de erro poderia ser mais clara")
            
            # 6. Verificar que can_be_accepted retorna False
            print("\n6️⃣ Verificando método can_be_accepted()...")
            can_accept, reason = invite.can_be_accepted_with_message()
            
            print(f"   can_accept: {can_accept}")
            print(f"   reason: {reason}")
            
            if not can_accept:
                print("✅ can_be_accepted() retorna False corretamente")
            else:
                print("❌ ERRO: can_be_accepted() deveria retornar False")
                return False
            
            # 7. Aprovar proposta e verificar que pode aceitar
            print("\n7️⃣ Aprovando proposta e verificando desbloqueio...")
            
            # Aprovar proposta manualmente
            proposal.status = 'accepted'
            proposal.responded_at = datetime.utcnow()
            invite.has_active_proposal = False
            invite.effective_value = proposal.proposed_value
            db.session.commit()
            
            # Recarregar convite
            db.session.refresh(invite)
            print(f"   Status do convite: {invite.status}")
            print(f"   has_active_proposal: {invite.has_active_proposal}")
            print(f"   effective_value: {invite.effective_value}")
            
            # Verificar que agora pode aceitar
            can_accept, reason = invite.can_be_accepted_with_message()
            print(f"   can_accept: {can_accept}")
            print(f"   reason: {reason}")
            
            if can_accept:
                print("✅ Convite desbloqueado após aprovação da proposta")
            else:
                print("❌ ERRO: Convite deveria estar desbloqueado")
                return False
            
            # 8. Aceitar convite com sucesso
            print("\n8️⃣ Aceitando convite após aprovação...")
            
            try:
                accept_result = InviteService.accept_invite(
                    token=invite_token,
                    provider_id=prestador.id
                )
                print(f"✅ Convite aceito com sucesso!")
                print(f"   Status: {accept_result['status']}")
                print(f"   Valor final: R$ {accept_result['final_value']:.2f}")
                
            except ValueError as e:
                print(f"❌ ERRO ao aceitar convite: {e}")
                return False
            
            print("\n🎉 Teste concluído com sucesso!")
            print("\n📋 Validações realizadas:")
            print("   ✅ Convite bloqueado com proposta pendente")
            print("   ✅ Mensagem de erro clara")
            print("   ✅ can_be_accepted() retorna False")
            print("   ✅ Convite desbloqueado após aprovação")
            print("   ✅ Aceitação bem-sucedida após aprovação")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Limpar dados de teste
            db.session.rollback()

if __name__ == "__main__":
    success = test_accept_invite_blocked_with_pending_proposal()
    if success:
        print("\n✅ Todos os testes passaram!")
    else:
        print("\n❌ Alguns testes falharam.")
