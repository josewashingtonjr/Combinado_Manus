#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a correção da funcionalidade de troca de senha do admin
Tarefa 11.1: Corrigir erro 500 na troca de senha do admin
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import AdminUser
from services.admin_service import AdminService

def test_admin_password_change():
    """Testa a funcionalidade de troca de senha do admin"""
    
    with app.app_context():
        print("\n🔐 Iniciando teste de troca de senha do admin...")
        
        # 1. Buscar admin existente
        admin = AdminUser.query.filter_by(email="admin@combinado.com").first()
        
        if not admin:
            print("❌ Admin não encontrado. Criando admin de teste...")
            admin = AdminUser(
                email="admin@combinado.com",
                papel="admin"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin de teste criado")
        
        print(f"   📧 Admin encontrado: {admin.email}")
        
        # 2. Testar troca de senha com dados válidos
        print("\n2️⃣ Testando troca de senha com dados válidos...")
        
        result = AdminService.change_admin_password(
            admin_id=admin.id,
            current_password="admin123",  # Senha atual do admin
            new_password="novasenha123"
        )
        
        print(f"   ✅ Resultado: {result}")
        assert result['success'] == True, f"Deveria ter sucesso: {result}"
        print("   ✅ Troca de senha bem-sucedida")
        
        # 3. Verificar se a nova senha funciona
        print("\n3️⃣ Verificando se nova senha funciona...")
        
        # Recarregar admin do banco
        db.session.refresh(admin)
        
        # Testar nova senha
        assert admin.check_password("novasenha123"), "Nova senha deveria funcionar"
        print("   ✅ Nova senha funciona corretamente")
        
        # Testar senha antiga (não deveria funcionar)
        assert not admin.check_password("admin123"), "Senha antiga não deveria funcionar"
        print("   ✅ Senha antiga não funciona mais")
        
        # 4. Testar validações de erro
        print("\n4️⃣ Testando validações de erro...")
        
        # Senha atual incorreta
        result_erro1 = AdminService.change_admin_password(
            admin_id=admin.id,
            current_password="senhaerrada",
            new_password="outrasenha123"
        )
        
        assert result_erro1['success'] == False, "Deveria falhar com senha incorreta"
        assert "incorreta" in result_erro1['error'].lower(), f"Mensagem de erro inadequada: {result_erro1['error']}"
        print("   ✅ Validação de senha atual incorreta funcionando")
        
        # Nova senha muito curta
        result_erro2 = AdminService.change_admin_password(
            admin_id=admin.id,
            current_password="novasenha123",
            new_password="123"
        )
        
        assert result_erro2['success'] == False, "Deveria falhar com senha muito curta"
        assert "6 caracteres" in result_erro2['error'], f"Mensagem de erro inadequada: {result_erro2['error']}"
        print("   ✅ Validação de senha muito curta funcionando")
        
        # Admin inexistente
        result_erro3 = AdminService.change_admin_password(
            admin_id=99999,
            current_password="qualquersenha",
            new_password="novasenha123"
        )
        
        assert result_erro3['success'] == False, "Deveria falhar com admin inexistente"
        assert "não encontrado" in result_erro3['error'].lower(), f"Mensagem de erro inadequada: {result_erro3['error']}"
        print("   ✅ Validação de admin inexistente funcionando")
        
        # 5. Restaurar senha original para outros testes
        print("\n5️⃣ Restaurando senha original...")
        
        result_restore = AdminService.change_admin_password(
            admin_id=admin.id,
            current_password="novasenha123",
            new_password="admin123"  # Restaurar senha original
        )
        
        assert result_restore['success'] == True, f"Deveria restaurar senha: {result_restore}"
        print("   ✅ Senha original restaurada")
        
        print("\n🎉 TESTE DE TROCA DE SENHA CONCLUÍDO COM SUCESSO!")
        print("   ✅ Funcionalidade implementada corretamente")
        print("   ✅ Validações funcionando")
        print("   ✅ Tratamento de erros robusto")
        
        return True

if __name__ == '__main__':
    try:
        test_admin_password_change()
        print("\n✅ TODOS OS TESTES PASSARAM!")
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)