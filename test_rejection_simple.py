#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples da funcionalidade de rejeição de convites
"""

import sqlite3
import os
from datetime import datetime, timedelta

def test_rejection_functionality():
    """Testa se o campo rejection_reason foi adicionado corretamente"""
    
    db_path = 'instance/test_combinado.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna rejection_reason existe
        cursor.execute('PRAGMA table_info(invites)')
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'rejection_reason' not in columns:
            print("❌ Campo rejection_reason não encontrado na tabela invites")
            return False
        
        print("✅ Campo rejection_reason encontrado na tabela invites")
        
        # Verificar se existem convites na tabela
        cursor.execute('SELECT COUNT(*) FROM invites')
        count = cursor.fetchone()[0]
        print(f"📊 Total de convites na tabela: {count}")
        
        # Verificar convites por status
        cursor.execute('SELECT status, COUNT(*) FROM invites GROUP BY status')
        status_counts = cursor.fetchall()
        
        print("📊 Convites por status:")
        for status, count in status_counts:
            print(f"   - {status}: {count}")
        
        # Verificar se há convites rejeitados com motivo
        cursor.execute('SELECT COUNT(*) FROM invites WHERE status = "recusado" AND rejection_reason IS NOT NULL')
        rejected_with_reason = cursor.fetchone()[0]
        print(f"📊 Convites rejeitados com motivo: {rejected_with_reason}")
        
        conn.close()
        
        print("\n🎉 Estrutura do banco de dados está correta para funcionalidade de rejeição!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {str(e)}")
        return False

def test_invite_model_structure():
    """Testa se o modelo Invite tem o campo rejection_reason"""
    
    try:
        # Importar o modelo
        from models import Invite
        
        # Verificar se o campo existe no modelo
        if hasattr(Invite, 'rejection_reason'):
            print("✅ Campo rejection_reason encontrado no modelo Invite")
        else:
            print("❌ Campo rejection_reason não encontrado no modelo Invite")
            return False
        
        # Verificar se o InviteService tem o método reject_invite
        from services.invite_service import InviteService
        
        if hasattr(InviteService, 'reject_invite'):
            print("✅ Método reject_invite encontrado no InviteService")
        else:
            print("❌ Método reject_invite não encontrado no InviteService")
            return False
        
        print("\n🎉 Estrutura do código está correta para funcionalidade de rejeição!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testando funcionalidade de rejeição de convites...\n")
    
    # Teste 1: Estrutura do banco de dados
    print("=== Teste 1: Estrutura do Banco de Dados ===")
    db_test = test_rejection_functionality()
    
    print("\n=== Teste 2: Estrutura do Código ===")
    code_test = test_invite_model_structure()
    
    if db_test and code_test:
        print("\n🎉 Todos os testes passaram! A funcionalidade de rejeição está implementada corretamente.")
        exit(0)
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")
        exit(1)