#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar o sistema de papéis duais funcionais
Testa alternância de papéis e funcionamento de convites
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite
from services.role_service import RoleService
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta

def test_dual_role_system():
    """Teste completo do sistema de papéis duais"""
    
    with app.app_context():
        print("🧪 Iniciando teste do sistema de papéis duais...")
        
        # 1. Criar usuário dual (cliente + prestador)
        print("\n1️⃣ Criando usuário dual...")
        
        # Verificar se usuário já existe
        dual_user = User.query.filter_by(email='dual@test.com').first()
        if dual_user:
            print(f"   ✅ Usuário dual já existe: {dual_user.email}")
            # Atualizar roles se necessário
            if dual_user.roles != 'cliente,prestador':
                dual_user.roles = 'cliente,prestador'
                db.session.commit()
                print(f"   ✅ Papéis atualizados para: {dual_user.roles}")
        else:
            dual_user = User(
                email='dual@test.com',
                nome='Usuário Dual',
                cpf='12345678901',
                roles='cliente,prestador'  # Papéis duais
            )
            dual_user.set_password('123456')
            db.session.add(dual_user)
            try:
                db.session.commit()
                print(f"   ✅ Usuário dual criado: {dual_user.email}")
            except Exception as e:
                db.session.rollback()
                # Tentar encontrar por CPF se email falhou
                dual_user = User.query.filter_by(cpf='12345678901').first()
                if dual_user:
                    dual_user.roles = 'cliente,prestador'
                    db.session.commit()
                    print(f"   ✅ Usuário existente atualizado: {dual_user.email}")
                else:
                    print(f"   ❌ Erro ao criar usuário: {e}")
                    return False
        
        # Criar carteira para o usuário se não existir
        WalletService.ensure_user_has_wallet(dual_user.id)
        print(f"   ✅ Carteira garantida para usuário dual")
        
        # Adicionar saldo para testes
        WalletService.admin_sell_tokens_to_user(dual_user.id, 1000.0, "Saldo para testes")
        print(f"   ✅ Saldo adicionado: R$ 1.000,00")
        
        # 2. Testar detecção de papéis duais
        print("\n2️⃣ Testando detecção de papéis duais...")
        
        user_roles = RoleService.get_user_roles(dual_user.id)
        is_dual = RoleService.is_dual_role_user(dual_user.id)
        available_roles = RoleService.get_available_roles(dual_user.id)
        
        print(f"   📋 Papéis do usuário: {user_roles}")
        print(f"   🔄 É usuário dual: {is_dual}")
        print(f"   📝 Papéis disponíveis: {available_roles}")
        
        assert is_dual == True, "Usuário deveria ser detectado como dual"
        assert 'cliente' in user_roles, "Usuário deveria ter papel de cliente"
        assert 'prestador' in user_roles, "Usuário deveria ter papel de prestador"
        print("   ✅ Detecção de papéis duais funcionando")
        
        # 3. Testar alternância de papéis
        print("\n3️⃣ Testando alternância de papéis...")
        
        # Simular sessão
        from flask import session
        with app.test_request_context():
            session['user_id'] = dual_user.id
            
            # Inicializar sessão
            RoleService.initialize_user_session(dual_user.id)
            initial_role = RoleService.get_active_role()
            print(f"   🎭 Papel inicial: {initial_role}")
            
            # Alternar para outro papel
            success = RoleService.switch_role()
            new_role = RoleService.get_active_role()
            print(f"   🔄 Alternância bem-sucedida: {success}")
            print(f"   🎭 Novo papel: {new_role}")
            
            assert success == True, "Alternância deveria ser bem-sucedida"
            assert new_role != initial_role, "Papel deveria ter mudado"
            print("   ✅ Alternância de papéis funcionando")
            
            # Testar definição de papel específico
            success_cliente = RoleService.set_active_role('cliente')
            success_prestador = RoleService.set_active_role('prestador')
            
            print(f"   👤 Definir como cliente: {success_cliente}")
            print(f"   🔧 Definir como prestador: {success_prestador}")
            
            assert success_cliente == True, "Deveria conseguir definir como cliente"
            assert success_prestador == True, "Deveria conseguir definir como prestador"
            print("   ✅ Definição de papéis específicos funcionando")
        
        # 4. Criar usuário cliente simples para teste de convites
        print("\n4️⃣ Criando usuário cliente simples...")
        
        simple_client = User.query.filter_by(email='cliente@test.com').first()
        if not simple_client:
            simple_client = User(
                email='cliente@test.com',
                nome='Cliente Simples',
                cpf='98765432100',
                roles='cliente'
            )
            simple_client.set_password('123456')
            db.session.add(simple_client)
            db.session.commit()
            print(f"   ✅ Cliente simples criado: {simple_client.email}")
        
        # Criar carteira e adicionar saldo
        WalletService.ensure_user_has_wallet(simple_client.id)
        WalletService.admin_sell_tokens_to_user(simple_client.id, 500.0, "Saldo para testes")
        print(f"   ✅ Saldo adicionado ao cliente simples: R$ 500,00")
        
        # 5. Testar criação de convite como cliente
        print("\n5️⃣ Testando criação de convite como cliente...")
        
        with app.test_request_context():
            session['user_id'] = simple_client.id
            RoleService.initialize_user_session(simple_client.id)
            RoleService.set_active_role('cliente')
            
            # Criar convite para o usuário dual
            try:
                invite_result = InviteService.create_invite(
                    client_id=simple_client.id,
                    invited_email=dual_user.email,  # Convidar usuário dual
                    service_title='Teste de Serviço',
                    service_description='Descrição do serviço de teste',
                    original_value=100.0,
                    delivery_date=datetime.now() + timedelta(days=7)
                )
                print(f"   ✅ Convite criado: {invite_result['invite_id']}")
                invite_token = invite_result['token']
            except Exception as e:
                print(f"   ❌ Erro ao criar convite: {e}")
                return False
        
        # 6. Testar recebimento de convite como prestador (usuário dual)
        print("\n6️⃣ Testando recebimento de convite como prestador...")
        
        with app.test_request_context():
            session['user_id'] = dual_user.id
            RoleService.initialize_user_session(dual_user.id)
            RoleService.set_active_role('prestador')  # Alternar para prestador
            
            # Listar convites recebidos
            received_invites = InviteService.get_invites_for_email(dual_user.email)
            print(f"   📨 Convites recebidos: {len(received_invites)}")
            
            if received_invites:
                invite_data = received_invites[0]
                print(f"   📋 Primeiro convite: {invite_data['service_title']}")
                print(f"   💰 Valor: R$ {invite_data['original_value']:.2f}")
                print(f"   📅 Data de entrega: {invite_data['delivery_date']}")
                print(f"   ✅ Convite recebido corretamente")
            else:
                print(f"   ❌ Nenhum convite recebido")
                return False
        
        # 7. Testar aceitação de convite
        print("\n7️⃣ Testando aceitação de convite...")
        
        with app.test_request_context():
            session['user_id'] = dual_user.id
            RoleService.set_active_role('prestador')
            
            try:
                accept_result = InviteService.accept_invite(
                    token=invite_token,
                    provider_id=dual_user.id
                )
                print(f"   ✅ Convite aceito: {accept_result['message']}")
                print(f"   💰 Valor final: R$ {accept_result['final_value']:.2f}")
            except Exception as e:
                print(f"   ❌ Erro ao aceitar convite: {e}")
                return False
        
        # 8. Verificar contexto de templates
        print("\n8️⃣ Testando contexto de templates...")
        
        with app.test_request_context():
            session['user_id'] = dual_user.id
            RoleService.initialize_user_session(dual_user.id)
            
            context = RoleService.get_context_for_templates()
            print(f"   🎭 Papel ativo: {context['active_role']}")
            print(f"   📋 Papéis disponíveis: {context['available_roles']}")
            print(f"   🔄 Pode alternar: {context['can_switch_roles']}")
            print(f"   🎨 Cor do papel: {context['role_color']}")
            print(f"   🎯 Ícone do papel: {context['role_icon']}")
            
            assert context['can_switch_roles'] == True, "Deveria poder alternar papéis"
            assert len(context['available_roles']) == 2, "Deveria ter 2 papéis disponíveis"
            print("   ✅ Contexto de templates funcionando")
        
        print("\n🎉 Todos os testes do sistema de papéis duais passaram!")
        return True

def test_invite_functionality_with_roles():
    """Teste específico para funcionalidade de convites com papéis duais"""
    
    with app.app_context():
        print("\n🧪 Testando funcionalidade de convites com papéis duais...")
        
        # Buscar usuários de teste
        dual_user = User.query.filter_by(email='dual@test.com').first()
        simple_client = User.query.filter_by(email='cliente@test.com').first()
        
        if not dual_user or not simple_client:
            print("   ❌ Usuários de teste não encontrados. Execute o teste principal primeiro.")
            return False
        
        # Teste: usuário dual criando convite como cliente
        print("\n1️⃣ Usuário dual criando convite como cliente...")
        
        with app.test_request_context():
            session['user_id'] = dual_user.id
            RoleService.initialize_user_session(dual_user.id)
            RoleService.set_active_role('cliente')  # Papel de cliente
            
            try:
                invite_result = InviteService.create_invite(
                    client_id=dual_user.id,
                    invited_email=simple_client.email,  # Convidar cliente simples
                    service_title='Serviço do Usuário Dual',
                    service_description='Convite criado por usuário dual no papel de cliente',
                    original_value=150.0,
                    delivery_date=datetime.now() + timedelta(days=5)
                )
                print(f"   ✅ Convite criado por usuário dual como cliente")
                dual_invite_token = invite_result['token']
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                return False
        
        # Teste: mesmo usuário dual recebendo convite como prestador
        print("\n2️⃣ Verificando se usuário dual pode receber convites como prestador...")
        
        # Criar convite do cliente simples para o usuário dual
        try:
            invite_to_dual = InviteService.create_invite(
                client_id=simple_client.id,
                invited_email=dual_user.email,
                service_title='Serviço para Usuário Dual',
                service_description='Convite para usuário dual atuar como prestador',
                original_value=200.0,
                delivery_date=datetime.now() + timedelta(days=10)
            )
            print(f"   ✅ Convite criado para usuário dual")
        except Exception as e:
            print(f"   ❌ Erro ao criar convite para dual: {e}")
            return False
        
        # Verificar se usuário dual pode ver convites em ambos os papéis
        with app.test_request_context():
            session['user_id'] = dual_user.id
            
            # Como cliente - ver convites enviados
            RoleService.set_active_role('cliente')
            sent_invites = InviteService.get_invites_sent_by_client(dual_user.id)
            print(f"   📤 Convites enviados como cliente: {len(sent_invites)}")
            
            # Como prestador - ver convites recebidos
            RoleService.set_active_role('prestador')
            received_invites = InviteService.get_invites_for_email(dual_user.email)
            print(f"   📨 Convites recebidos como prestador: {len(received_invites)}")
            
            if len(sent_invites) > 0 and len(received_invites) > 0:
                print("   ✅ Usuário dual pode gerenciar convites em ambos os papéis")
            else:
                print("   ❌ Problema na gestão de convites por papel")
                return False
        
        print("\n🎉 Funcionalidade de convites com papéis duais funcionando!")
        return True

if __name__ == '__main__':
    print("🚀 Executando testes do sistema de papéis duais...")
    
    # Executar testes
    test1_success = test_dual_role_system()
    test2_success = test_invite_functionality_with_roles()
    
    if test1_success and test2_success:
        print("\n✅ Todos os testes passaram! Sistema de papéis duais implementado com sucesso.")
        exit(0)
    else:
        print("\n❌ Alguns testes falharam. Verifique a implementação.")
        exit(1)