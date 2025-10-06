#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import os
os.environ['DATABASE_URL'] = 'sqlite:///test_wallets.db'

from app import app, db
from models import User
from services.wallet_service import WalletService

def create_test_user():
    """Criar usuário de teste para a área do cliente"""
    with app.app_context():
        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(email='cliente@teste.com').first()
        if existing_user:
            print("✅ Usuário de teste já existe: cliente@teste.com")
            return
        
        # Criar usuário de teste
        user = User(
            nome='Cliente Teste',
            email='cliente@teste.com',
            cpf='12345678901',
            phone='(11) 99999-9999',
            roles='cliente',
            active=True
        )
        user.set_password('123456')
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira automaticamente
        try:
            wallet = WalletService.ensure_user_has_wallet(user.id)
            print("✅ Usuário de teste criado:")
            print("   Email: cliente@teste.com")
            print("   Senha: 123456")
            print("   Papel: cliente")
            print(f"   Carteira criada com ID: {wallet.id}")
        except Exception as e:
            print(f"❌ Erro ao criar carteira: {e}")

if __name__ == '__main__':
    create_test_user()
