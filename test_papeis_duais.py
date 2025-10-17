#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar o sistema de papéis duais funcionais
Tarefa 11.3: Implementar sistema de papéis duais funcionais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User
from services.role_service import RoleService
from services.auth_service import AuthService

def test_papeis_duais():
    """Testa o sistema de papéis duais"""
    
    with app.app_context():
        print("\n👥 Iniciando teste do sistema de papéis duais...")
        
        # 1. Verificar se existe usuário dual
        print("\n1️⃣ Verificando usuário dual...")
        
        dual_user = User.query.filter_by(email="dual@teste.com").first()
        
        if not dual_user:
            print("   Criando usuário dual para teste...")
            dual_user = User(
                nome="Usuário Dual",
                email="dual@teste.com",
                cpf="11122233344",
                phone="(11) 77777-7777",
                roles="cliente,prestador",  # Ambos os papéis
                active=True
            )
            dual_user.set_password("dual12345")
            db.session.add(dual_user)
            db.session.commit()
            print("   ✅ Usuário dual criado")
        
        print(f"   📧 Usuário dual: {dual_user.email}")
        print(f"   🎭 Papéis: {dual_user.roles}")
        
        # 2. Testar RoleService - obter papéis
        print("\n2️⃣ Testando RoleService - obter papéis...")
        
        roles = RoleService.get_user_roles(dual_user.id)
        print(f"   📋 Papéis obtidos: {roles}")
        
        assert len(roles) == 2, f"Deveria ter 2 papéis, mas tem {len(roles)}"
        assert 'cliente' in roles, "Deveria ter papel de cliente"
        assert 'prestador' in roles, "Deveria ter papel de prestador"
        print("   ✅ Papéis obtidos corretamente")
        
        # 3. Testar detecção de usuário dual
        print("\n3️⃣ Testando detecção de usuário dual...")
        
        is_dual = RoleService.is_dual_role_user(dual_user.id)
        assert is_dual == True, "Deveria detectar como usuário dual"
        print("   ✅ Usuário dual detectado corretamente")
        
        # 4. Testar verificação de papéis específicos
        print("\n4️⃣ Testando verificação de papéis específicos...")
        
        has_cliente = RoleService.has_role(dual_user.id, 'cliente')
        has_prestador = RoleService.has_role(dual_user.id, 'prestador')
        has_admin = RoleService.has_role(dual_user.id, 'admin')
        
        assert has_cliente == True, "Deveria ter papel de cliente"
        assert has_prestador == True, "Deveria ter papel de prestador"
        assert has_admin == False, "Não deveria ter papel de admin"
        print("   ✅ Verificação de papéis específicos funcionando")
        
        # 5. Testar inicialização de sessão
        print("\n5️⃣ Testando inicialização de sessão...")
        
        # Simular contexto de aplicação Flask
        with app.test_request_context():
            from flask import session
            
            # Inicializar sessão do usuário
            success = RoleService.initialize_user_session(dual_user.id)
            assert success == True, "Deveria inicializar sessão com sucesso"
            
            # Verificar papel ativo padrão
            active_role = RoleService.get_active_role()
            print(f"   🎯 Papel ativo padrão: {active_role}")
            assert active_role in ['cliente', 'prestador'], f"Papel ativo inválido: {active_role}"
            print("   ✅ Sessão inicializada corretamente")
            
            # 6. Testar alternância de papéis
            print("\n6️⃣ Testando alternância de papéis...")
            
            # Definir papel específico
            success_cliente = RoleService.set_active_role('cliente')
            assert success_cliente == True, "Deveria conseguir definir papel de cliente"
            
            current_role = RoleService.get_active_role()
            assert current_role == 'cliente', f"Papel ativo deveria ser cliente, mas é {current_role}"
            print("   ✅ Papel definido para cliente")
            
            # Alternar para prestador
            success_prestador = RoleService.set_active_role('prestador')
            assert success_prestador == True, "Deveria conseguir definir papel de prestador"
            
            current_role = RoleService.get_active_role()
            assert current_role == 'prestador', f"Papel ativo deveria ser prestador, mas é {current_role}"
            print("   ✅ Papel alterado para prestador")
            
            # Tentar papel inválido
            success_invalid = RoleService.set_active_role('admin')
            assert success_invalid == False, "Não deveria conseguir definir papel de admin"
            print("   ✅ Validação de papel inválido funcionando")
            
            # 7. Testar alternância automática
            print("\n7️⃣ Testando alternância automática...")
            
            # Definir papel inicial
            RoleService.set_active_role('cliente')
            
            # Alternar automaticamente
            switch_success = RoleService.switch_role()
            assert switch_success == True, "Deveria conseguir alternar papel"
            
            new_role = RoleService.get_active_role()
            assert new_role == 'prestador', f"Deveria alternar para prestador, mas é {new_role}"
            print("   ✅ Alternância automática funcionando")
            
            # 8. Testar contexto para templates
            print("\n8️⃣ Testando contexto para templates...")
            
            # Simular sessão com usuário logado
            session['user_id'] = dual_user.id
            
            context = RoleService.get_context_for_templates()
            
            assert context['active_role'] is not None, "Deveria ter papel ativo"
            assert len(context['available_roles']) == 2, "Deveria ter 2 papéis disponíveis"
            assert context['is_dual_role'] == True, "Deveria ser usuário dual"
            assert context['can_switch_roles'] == True, "Deveria poder alternar papéis"
            
            print(f"   🎯 Papel ativo: {context['active_role']}")
            print(f"   📋 Papéis disponíveis: {context['available_roles']}")
            print(f"   🔄 Pode alternar: {context['can_switch_roles']}")
            print("   ✅ Contexto para templates funcionando")
        
        # 9. Testar usuário com papel único
        print("\n9️⃣ Testando usuário com papel único...")
        
        cliente_only = User.query.filter_by(email="cliente@teste.com").first()
        if cliente_only:
            is_dual_single = RoleService.is_dual_role_user(cliente_only.id)
            assert is_dual_single == False, "Usuário com papel único não deveria ser dual"
            print("   ✅ Usuário com papel único detectado corretamente")
        
        print("\n🎉 TESTE DE PAPÉIS DUAIS CONCLUÍDO COM SUCESSO!")
        print("   ✅ Detecção de usuários duais funcionando")
        print("   ✅ Alternância de papéis funcionando")
        print("   ✅ Validações de segurança funcionando")
        print("   ✅ Contexto para templates funcionando")
        print("   ✅ Inicialização de sessão funcionando")
        
        return True

if __name__ == '__main__':
    try:
        test_papeis_duais()
        print("\n✅ TODOS OS TESTES PASSARAM!")
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)