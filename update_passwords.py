#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para atualizar senhas no banco de dados para 8 caracteres
Seguindo o plano do projeto Combinado
"""

from app import app
from models import db, User, AdminUser

def update_passwords():
    """Atualizar senhas para 8 caracteres"""
    with app.app_context():
        print("🔄 Atualizando senhas no banco de dados...")
        
        # Atualizar senha do administrador
        admin = AdminUser.query.filter_by(email='admin@combinado.com').first()
        if admin:
            admin.set_password('admin12345')  # 8+ caracteres
            print("✅ Senha do admin atualizada: admin12345")
        
        # Atualizar senhas dos usuários
        users_to_update = [
            ('cliente@teste.com', 'cliente123'),
            ('prestador@teste.com', 'prestador123'),
            ('dual@teste.com', 'dual12345')
        ]
        
        for email, new_password in users_to_update:
            user = User.query.filter_by(email=email).first()
            if user:
                user.set_password(new_password)
                print(f"✅ Senha atualizada para {email}: {new_password}")
        
        # Salvar mudanças
        db.session.commit()
        print("🎉 Todas as senhas foram atualizadas com sucesso!")
        
        print("\n📋 Novas credenciais:")
        print("Admin: admin@combinado.com / admin12345")
        print("Cliente: cliente@teste.com / cliente123")
        print("Prestador: prestador@teste.com / prestador123")
        print("Dual: dual@teste.com / dual12345")

if __name__ == '__main__':
    update_passwords()
