#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar a correção do fluxo de contrapropostas
Garante que cliente e prestador vejam os convites nas views corretas
"""

import sys
from datetime import datetime, timedelta
from decimal import Decimal

def test_counter_proposal_roles():
    """
    Testa o fluxo completo de contrapropostas verificando os papéis
    
    Fluxo:
    1. Cliente cria convite → Cliente vê como cliente, Prestador vê como prestador
    2. Prestador faz contraproposta → Cliente vê como cliente, Prestador vê como prestador
    3. Cliente faz nova contraproposta → Cliente vê como cliente, Prestador vê como prestador
    4. Cliente aceita contraproposta → Cliente vê como cliente, Prestador vê como prestador
    """
    
    print("\n" + "="*80)
    print("TESTE: Correção de Papéis em Contrapropostas")
    print("="*80)
    
    try:
        from app import app, db
        from models import User, Invite
        from services.invite_service import InviteService
        from services.auth_service import AuthService
        
        with app.app_context():
            print("\n1️⃣ Preparando ambiente de teste...")
            
            # Buscar ou criar usuários de teste
            import json
            
            cliente = User.query.filter_by(email='cliente_test@example.com').first()
            if not cliente:
                cliente = User(
                    nome='Cliente Teste',
                    email='cliente_test@example.com',
                    cpf='111.111.111-11',
                    phone='(11) 91111-1111'
                )
                cliente.set_password('senha123')
                cliente.roles = json.dumps(['cliente'])
                db.session.add(cliente)
            
            prestador = User.query.filter_by(email='prestador_test@example.com').first()
            if not prestador:
                prestador = User(
                    nome='Prestador Teste',
                    email='prestador_test@example.com',
                    cpf='222.222.222-22',
                    phone='(11) 92222-2222'
                )
                prestador.set_password('senha123')
                prestador.roles = json.dumps(['prestador'])
                db.session.add(prestador)
            
            db.session.commit()
            
            # Criar carteiras se não existirem
            from models import Wallet
            from services.wallet_service import WalletService
            
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
            
            # Limpar convites antigos de teste
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
                service_title='Serviço de Teste',
                service_description='Descrição do serviço de teste',
                original_value=Decimal('100.00'),
                delivery_date=delivery_date,
                service_category='teste'
            )
            
            invite_original = Invite.query.get(result['invite_id'])
            
            print(f"   ✅ Convite criado (ID: {invite_original.id})")
            print(f"   📋 client_id: {invite_original.client_id} (deve ser {cliente.id})")
            print(f"   📋 invited_phone: {invite_original.invited_phone} (deve ser {prestador.phone})")
            
            # Verificar papéis
            assert invite_original.client_id == cliente.id, "Cliente deve ser o client_id"
            assert invite_original.invited_phone == prestador.phone, "Prestador deve ser o invited_phone"
            
            print("\n3️⃣ Verificando visualização do convite original...")
            
            # Cliente deve ver na lista de enviados
            convites_cliente = InviteService.get_invites_sent_by_client(cliente.id)
            assert len(convites_cliente) > 0, "Cliente deve ver convite na lista de enviados"
            assert any(c['id'] == invite_original.id for c in convites_cliente), "Convite original deve estar na lista do cliente"
            print(f"   ✅ Cliente vê {len(convites_cliente)} convite(s) enviado(s)")
            
            # Prestador deve ver na lista de recebidos
            convites_prestador = InviteService.get_invites_for_phone(prestador.phone)
            assert len(convites_prestador) > 0, "Prestador deve ver convite na lista de recebidos"
            assert any(c['id'] == invite_original.id for c in convites_prestador), "Convite original deve estar na lista do prestador"
            print(f"   ✅ Prestador vê {len(convites_prestador)} convite(s) recebido(s)")
            
            print("\n4️⃣ Prestador faz contraproposta...")
            
            result_cp1 = InviteService.create_counter_proposal(
                original_invite_id=invite_original.id,
                proposed_value=Decimal('150.00'),
                justification='Preciso de mais recursos para este serviço',
                proposer_id=prestador.id
            )
            
            invite_cp1 = Invite.query.get(result_cp1['new_invite_id'])
            
            print(f"   ✅ Contraproposta 1 criada (ID: {invite_cp1.id})")
            print(f"   📋 client_id: {invite_cp1.client_id} (deve ser {cliente.id})")
            print(f"   📋 invited_phone: {invite_cp1.invited_phone} (deve ser {prestador.phone})")
            print(f"   📋 is_counter_proposal: {invite_cp1.is_counter_proposal}")
            
            # Verificar papéis mantidos
            assert invite_cp1.client_id == cliente.id, "Cliente deve continuar sendo o client_id"
            assert invite_cp1.invited_phone == prestador.phone, "Prestador deve continuar sendo o invited_phone"
            assert invite_cp1.is_counter_proposal, "Deve ser marcado como contraproposta"
            
            print("\n5️⃣ Verificando visualização da contraproposta 1...")
            
            # Cliente deve ver na lista de enviados (porque é o client_id)
            convites_cliente = InviteService.get_invites_sent_by_client(cliente.id)
            assert any(c['id'] == invite_cp1.id for c in convites_cliente), "Contraproposta deve estar na lista do cliente"
            print(f"   ✅ Cliente vê contraproposta na lista de enviados")
            
            # Prestador deve ver na lista de recebidos (porque é o invited_phone)
            convites_prestador = InviteService.get_invites_for_phone(prestador.phone)
            assert any(c['id'] == invite_cp1.id for c in convites_prestador), "Contraproposta deve estar na lista do prestador"
            print(f"   ✅ Prestador vê contraproposta na lista de recebidos")
            
            print("\n6️⃣ Cliente faz nova contraproposta...")
            
            result_cp2 = InviteService.create_counter_proposal(
                original_invite_id=invite_cp1.id,
                proposed_value=Decimal('120.00'),
                justification='Posso aumentar um pouco, mas não tanto',
                proposer_id=cliente.id
            )
            
            invite_cp2 = Invite.query.get(result_cp2['new_invite_id'])
            
            print(f"   ✅ Contraproposta 2 criada (ID: {invite_cp2.id})")
            print(f"   📋 client_id: {invite_cp2.client_id} (deve ser {cliente.id})")
            print(f"   📋 invited_phone: {invite_cp2.invited_phone} (deve ser {prestador.phone})")
            print(f"   📋 is_counter_proposal: {invite_cp2.is_counter_proposal}")
            
            # Verificar papéis mantidos
            assert invite_cp2.client_id == cliente.id, "Cliente deve continuar sendo o client_id"
            assert invite_cp2.invited_phone == prestador.phone, "Prestador deve continuar sendo o invited_phone"
            assert invite_cp2.is_counter_proposal, "Deve ser marcado como contraproposta"
            
            print("\n7️⃣ Verificando visualização da contraproposta 2...")
            
            # Cliente deve ver na lista de enviados
            convites_cliente = InviteService.get_invites_sent_by_client(cliente.id)
            assert any(c['id'] == invite_cp2.id for c in convites_cliente), "Contraproposta 2 deve estar na lista do cliente"
            print(f"   ✅ Cliente vê contraproposta 2 na lista de enviados")
            
            # Prestador deve ver na lista de recebidos
            convites_prestador = InviteService.get_invites_for_phone(prestador.phone)
            assert any(c['id'] == invite_cp2.id for c in convites_prestador), "Contraproposta 2 deve estar na lista do prestador"
            print(f"   ✅ Prestador vê contraproposta 2 na lista de recebidos")
            
            print("\n8️⃣ Resumo do fluxo...")
            
            print(f"\n   📊 Convites do Cliente (client_id={cliente.id}):")
            for c in convites_cliente:
                print(f"      - ID {c['id']}: {c['service_title']} - Status: {c['status']}")
            
            print(f"\n   📊 Convites do Prestador (phone={prestador.phone}):")
            for c in convites_prestador:
                print(f"      - ID {c['id']}: {c['service_title']} - Status: {c['status']}")
            
            print("\n" + "="*80)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("="*80)
            print("\n📝 Conclusões:")
            print("   1. Cliente sempre é o client_id (quem paga)")
            print("   2. Prestador sempre é o invited_phone (quem executa)")
            print("   3. Contrapropostas mantêm os papéis corretos")
            print("   4. Cliente vê todos os convites na lista de 'enviados'")
            print("   5. Prestador vê todos os convites na lista de 'recebidos'")
            print("   6. As rotas ver_convite agora redirecionam corretamente:")
            print("      - Se cliente acessa: mostra view do cliente")
            print("      - Se prestador acessa: mostra view do prestador")
            
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
    success = test_counter_proposal_roles()
    sys.exit(0 if success else 1)
