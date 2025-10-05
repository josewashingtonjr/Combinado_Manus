#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""Teste completo de login simulando a rota"""

from app import app
from models import User
import secrets

def test_login():
    with app.app_context():
        print("=" * 60)
        print("TESTE COMPLETO DE LOGIN")
        print("=" * 60)
        
        # Dados de teste
        email = "cliente@teste.com"
        password = "cliente123"
        
        print(f"\n1. Buscando usuário: {email}")
        user = User.query.filter_by(email=email, active=True).first()
        
        if not user:
            print("❌ FALHA: Usuário não encontrado")
            return False
        
        print(f"✅ Usuário encontrado: ID={user.id}, Nome={user.nome}")
        
        print(f"\n2. Verificando senha...")
        password_valid = user.check_password(password)
        
        if not password_valid:
            print("❌ FALHA: Senha incorreta")
            return False
        
        print(f"✅ Senha válida")
        
        print(f"\n3. Gerando token de sessão...")
        token = secrets.token_urlsafe(32)
        print(f"✅ Token gerado: {token[:20]}...")
        
        print(f"\n4. Dados da sessão:")
        print(f"   - user_id: {user.id}")
        print(f"   - user_token: {token[:20]}...")
        print(f"   - user_role: {user.roles}")
        
        print(f"\n5. Determinando redirecionamento...")
        roles = user.roles.split(',') if user.roles else []
        primary_role = roles[0] if roles else 'cliente'
        print(f"   - Roles: {roles}")
        print(f"   - Primary role: {primary_role}")
        
        redirect_map = {
            'cliente': '/app/home',
            'prestador': '/prestador/dashboard',
            'admin': '/admin/dashboard'
        }
        redirect_url = redirect_map.get(primary_role, '/app/home')
        print(f"   - Redirect URL: {redirect_url}")
        
        print(f"\n{'=' * 60}")
        print("✅ TESTE DE LOGIN: SUCESSO")
        print(f"{'=' * 60}")
        
        return True

if __name__ == '__main__':
    test_login()
