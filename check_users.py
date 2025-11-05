#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para verificar usuários no banco de dados
Seguindo o plano do projeto Combinado
"""

from app import app
from models import db, User, AdminUser

def check_users():
    """Verificar usuários no banco de dados"""
    with app.app_context():
        print("🔍 Verificando usuários no banco de dados...")
        
        # Verificar administradores
        print("\n=== ADMINISTRADORES ===")
        admins = AdminUser.query.all()
        for admin in admins:
            print(f"ID: {admin.id}")
            print(f"Email: {admin.email}")
            print(f"Papel: {admin.papel}")
            print(f"Password Hash: {admin.password_hash[:50]}...")
            
            # Testar senha
            test_password = 'admin12345'
            is_valid = admin.check_password(test_password)
            print(f"Senha '{test_password}' válida: {is_valid}")
            print("-" * 50)
        
        # Verificar usuários
        print("\n=== USUÁRIOS ===")
        users = User.query.all()
        for user in users:
            print(f"ID: {user.id}")
            print(f"Nome: {user.nome}")
            print(f"Email: {user.email}")
            print(f"Roles: {user.roles}")
            print(f"Ativo: {user.active}")
            print(f"Password Hash: {user.password_hash[:50]}...")
            
            # Testar senhas
            test_passwords = ['cliente123', '123456', 'prestador123', 'dual12345']
            for test_pass in test_passwords:
                is_valid = user.check_password(test_pass)
                if is_valid:
                    print(f"✅ Senha '{test_pass}' válida")
                    break
            else:
                print("❌ Nenhuma senha testada é válida")
            print("-" * 50)
        
        print(f"\nTotal de administradores: {len(admins)}")
        print(f"Total de usuários: {len(users)}")

if __name__ == '__main__':
    check_users()
