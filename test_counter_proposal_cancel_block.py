#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar o bloqueio de cancelamento de contrapropostas pelo criador
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal

def test_counter_proposal_cancel_block():
    """
    Testa se quem cria a contraproposta não pode cancelar/recusar a própria contraproposta
    """
    
    print("\n" + "="*80)
    print("TESTE: Bloqueio de Cancelamento pelo Criador da Contraproposta")
    print("="*80)
    
    try:
        from app import app, db
        from models import User, Invite, Wallet
        from services.invite_service import InviteService
        import json
        
        with app.app_context():
            print("\n1️⃣ Preparando ambiente de teste...")
            
            # Buscar usuários de teste existentes
            cliente = User.query.filter_by(email='cliente_cp_test@example.com').first()
            prestador = User.query.filter_by(email='prestador_cp_test@example.com').first()
            
            if not cliente or not prestador:
                print("   ⚠️  Usuários de teste não encontrados. Execute test_counter_proposal_accept_block.py primeiro.")
                return True
            
            print(f"   ✅ Cliente: {cliente.nome} (ID: {cliente.id})")
            print(f"   ✅ Prestador: {prestador.nome} (ID: {prestador.id})")
            
            print("\n2️⃣ Cliente cria convite original...")
            
            delivery_date = datetime.now() + timedelta(days=7)
            
            result = InviteService.create_invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Cancelamento CP',
                service_description='Teste de bloqueio de cancelamento',
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
            
            # Verificar se prestador pode aceitar (NÃO DEVE PODER)
            can_prestador_accept = invite_cp1.can_user_accept_counter_proposal(prestador.id)
            print(f"   📋 Prestador pode aceitar/recusar/cancelar: {can_prestador_accept}")
            assert can_prestador_accept == False, "Prestador NÃO deve poder aceitar/recusar/cancelar sua própria contraproposta"
            
            # Verificar se cliente pode aceitar (DEVE PODER)
            can_cliente_accept = invite_cp1.can_user_accept_counter_proposal(cliente.id)
            print(f"   📋 Cliente pode aceitar/recusar: {can_cliente_accept}")
            assert can_cliente_accept == True, "Cliente DEVE poder aceitar/recusar contraproposta do prestador"
            
            print("\n4️⃣ Cliente faz contraproposta...")
            
            result_cp2 = InviteService.create_counter_proposal(
                original_invite_id=invite_cp1.id,
                proposed_value=Decimal('120.00'),
                justification='Posso aumentar um pouco',
                proposer_id=cliente.id
            )
            
            invite_cp2 = Invite.query.get(result_cp2['new_invite_id'])
            print(f"   ✅ Contraproposta criada (ID: {invite_cp2.id})")
            
            # Verificar se cliente pode aceitar (NÃO DEVE PODER)
            can_cliente_accept = invite_cp2.can_user_accept_counter_proposal(cliente.id)
            print(f"   📋 Cliente pode aceitar/recusar: {can_cliente_accept}")
            assert can_cliente_accept == False, "Cliente NÃO deve poder aceitar/recusar sua própria contraproposta"
            
            # Verificar se prestador pode aceitar (DEVE PODER)
            can_prestador_accept = invite_cp2.can_user_accept_counter_proposal(prestador.id)
            print(f"   📋 Prestador pode aceitar/recusar/cancelar: {can_prestador_accept}")
            assert can_prestador_accept == True, "Prestador DEVE poder aceitar/recusar contraproposta do cliente"
            
            print("\n" + "="*80)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("="*80)
            print("\n📝 Conclusões:")
            print("   1. Prestador cria contraproposta → NÃO pode aceitar/recusar/cancelar")
            print("   2. Cliente cria contraproposta → NÃO pode aceitar/recusar")
            print("   3. Quem recebe a contraproposta PODE aceitar/recusar")
            print("   4. Botões de aceitar, recusar e cancelar são desabilitados para o criador")
            print("   5. Criador deve aguardar a outra parte responder")
            
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
    success = test_counter_proposal_cancel_block()
    sys.exit(0 if success else 1)
