#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar o bloqueio de aceite/recusa de contrapropostas pelo criador
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal

def test_counter_proposal_accept_block():
    """
    Testa se quem cria a contraproposta não pode aceitar/recusar a própria contraproposta
    """
    
    print("\n" + "="*80)
    print("TESTE: Bloqueio de Aceite/Recusa pelo Criador da Contraproposta")
    print("="*80)
    
    try:
        from app import app, db
        from models import User, Invite, Wallet
        from services.invite_service import InviteService
        import json
        
        with app.app_context():
            print("\n1️⃣ Preparando ambiente de teste...")
            
            # Buscar ou criar usuários de teste
            cliente = User.query.filter_by(email='cliente_cp_test@example.com').first()
            if not cliente:
                cliente = User(
                    nome='Cliente CP Test',
                    email='cliente_cp_test@example.com',
                    cpf='333.333.333-33',
                    phone='(11) 93333-3333'
                )
                cliente.set_password('senha123')
                cliente.roles = json.dumps(['cliente'])
                db.session.add(cliente)
            
            prestador = User.query.filter_by(email='prestador_cp_test@example.com').first()
            if not prestador:
                prestador = User(
                    nome='Prestador CP Test',
                    email='prestador_cp_test@example.com',
                    cpf='444.444.444-44',
                    phone='(11) 94444-4444'
                )
                prestador.set_password('senha123')
                prestador.roles = json.dumps(['prestador'])
                db.session.add(prestador)
            
            db.session.commit()
            
            # Criar carteiras
            wallet_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            if not wallet_cliente:
                wallet_cliente = Wallet(user_id=cliente.id, balance=Decimal('1000.00'))
                db.session.add(wallet_cliente)
            
            wallet_prestador = Wallet.query.filter_by(user_id=prestador.id).first()
            if not wallet_prestador:
                wallet_prestador = Wallet(user_id=prestador.id, balance=Decimal('1000.00'))
                db.session.add(wallet_prestador)
            
            db.session.commit()
            
            print(f"   ✅ Cliente: {cliente.nome} (ID: {cliente.id})")
            print(f"   ✅ Prestador: {prestador.nome} (ID: {prestador.id})")
            
            # Limpar convites antigos
            Invite.query.filter(
                (Invite.client_id == cliente.id) | 
                (Invite.invited_phone == prestador.phone)
            ).delete()
            db.session.commit()
            
            print("\n2️⃣ Cliente cria convite original...")
            
            delivery_date = datetime.now() + timedelta(days=7)
            
            result = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Bloqueio CP',
                service_description='Teste de bloqueio de aceite',
                original_value=Decimal('100.00'),
                delivery_date=delivery_date,
                service_category='teste'
            )
            
            invite_original = Invite.query.get(result['invite_id'])
            print(f"   ✅ Convite criado (ID: {invite_original.id})")
            
            print("\n3️⃣ Prestador faz contraproposta...")
            
            result_cp1 = InviteService.create_counter_proposal(
                original_invite_id=invite_original.id,
                proposed_value=Decimal('150.00'),
                justification='Preciso de mais recursos',
                proposer_id=prestador.id
            )
            
            invite_cp1 = Invite.query.get(result_cp1['new_invite_id'])
            print(f"   ✅ Contraproposta criada (ID: {invite_cp1.id})")
            
            # Verificar quem criou
            created_by_client = invite_cp1.was_counter_proposal_created_by_client()
            print(f"   📋 Criada pelo cliente: {created_by_client}")
            assert created_by_client == False, "Contraproposta deve ter sido criada pelo prestador"
            
            # Verificar se prestador pode aceitar (NÃO DEVE PODER)
            can_prestador_accept = invite_cp1.can_user_accept_counter_proposal(prestador.id)
            print(f"   📋 Prestador pode aceitar: {can_prestador_accept}")
            assert can_prestador_accept == False, "Prestador NÃO deve poder aceitar sua própria contraproposta"
            
            # Verificar se cliente pode aceitar (DEVE PODER)
            can_cliente_accept = invite_cp1.can_user_accept_counter_proposal(cliente.id)
            print(f"   📋 Cliente pode aceitar: {can_cliente_accept}")
            assert can_cliente_accept == True, "Cliente DEVE poder aceitar contraproposta do prestador"
            
            print("\n4️⃣ Cliente faz contraproposta...")
            
            result_cp2 = InviteService.create_counter_proposal(
                original_invite_id=invite_cp1.id,
                proposed_value=Decimal('120.00'),
                justification='Posso aumentar um pouco',
                proposer_id=cliente.id
            )
            
            invite_cp2 = Invite.query.get(result_cp2['new_invite_id'])
            print(f"   ✅ Contraproposta criada (ID: {invite_cp2.id})")
            
            # Verificar quem criou
            created_by_client = invite_cp2.was_counter_proposal_created_by_client()
            print(f"   📋 Criada pelo cliente: {created_by_client}")
            assert created_by_client == True, "Contraproposta deve ter sido criada pelo cliente"
            
            # Verificar se cliente pode aceitar (NÃO DEVE PODER)
            can_cliente_accept = invite_cp2.can_user_accept_counter_proposal(cliente.id)
            print(f"   📋 Cliente pode aceitar: {can_cliente_accept}")
            assert can_cliente_accept == False, "Cliente NÃO deve poder aceitar sua própria contraproposta"
            
            # Verificar se prestador pode aceitar (DEVE PODER)
            can_prestador_accept = invite_cp2.can_user_accept_counter_proposal(prestador.id)
            print(f"   📋 Prestador pode aceitar: {can_prestador_accept}")
            assert can_prestador_accept == True, "Prestador DEVE poder aceitar contraproposta do cliente"
            
            print("\n5️⃣ Testando convite original (não é contraproposta)...")
            
            # Criar novo convite original
            result_original = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Convite Normal',
                service_description='Não é contraproposta',
                original_value=Decimal('200.00'),
                delivery_date=delivery_date,
                service_category='teste'
            )
            
            invite_normal = Invite.query.get(result_original['invite_id'])
            print(f"   ✅ Convite normal criado (ID: {invite_normal.id})")
            
            # Verificar se é contraproposta
            is_cp = invite_normal.is_counter_proposal
            print(f"   📋 É contraproposta: {is_cp}")
            assert is_cp == False, "Convite normal não deve ser contraproposta"
            
            # Verificar se prestador pode aceitar (DEVE PODER)
            can_prestador_accept = invite_normal.can_user_accept_counter_proposal(prestador.id)
            print(f"   📋 Prestador pode aceitar: {can_prestador_accept}")
            assert can_prestador_accept == True, "Prestador DEVE poder aceitar convite normal"
            
            print("\n" + "="*80)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("="*80)
            print("\n📝 Conclusões:")
            print("   1. Prestador cria contraproposta → Prestador NÃO pode aceitar/recusar")
            print("   2. Cliente cria contraproposta → Cliente NÃO pode aceitar/recusar")
            print("   3. Quem recebe a contraproposta PODE aceitar/recusar")
            print("   4. Convites normais (não contrapropostas) funcionam normalmente")
            print("   5. Sistema identifica corretamente quem criou a contraproposta")
            
            return True
            
    except AssertionError as e:
        print(f"\n❌ ERRO DE VALIDAÇÃO: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_counter_proposal_accept_block()
    sys.exit(0 if success else 1)
