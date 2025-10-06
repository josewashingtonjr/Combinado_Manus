#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from app import app, db
from models import User
from services.wallet_service import WalletService

def create_prestador_user():
    """Criar usuário de teste para a área do prestador"""
    with app.app_context():
        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(email='prestador@teste.com').first()
        if existing_user:
            print("✅ Usuário prestador já existe: prestador@teste.com")
            return
        
        # Criar usuário prestador
        user = User(
            nome='Prestador Teste',
            email='prestador@teste.com',
            cpf='98765432100',
            phone='(11) 88888-8888',
            roles='prestador',
            active=True
        )
        user.set_password('123456')
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira automaticamente
        try:
            wallet = WalletService.ensure_user_has_wallet(user.id)
            print("✅ Usuário prestador criado:")
            print("   Email: prestador@teste.com")
            print("   Senha: 123456")
            print("   Papel: prestador")
            print(f"   Carteira criada com ID: {wallet.id}")
        except Exception as e:
            print(f"❌ Erro ao criar carteira: {e}")

def create_dual_user():
    """Criar usuário que é cliente E prestador"""
    with app.app_context():
        # Verificar se o usuário já existe
        existing_user = User.query.filter_by(email='dual@teste.com').first()
        if existing_user:
            print("✅ Usuário dual já existe: dual@teste.com")
            return
        
        # Criar usuário com ambos os papéis
        user = User(
            nome='Usuário Dual',
            email='dual@teste.com',
            cpf='11122233344',
            phone='(11) 77777-7777',
            roles='cliente,prestador',  # Ambos os papéis
            active=True
        )
        user.set_password('123456')
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira automaticamente
        try:
            wallet = WalletService.ensure_user_has_wallet(user.id)
            print("✅ Usuário dual criado:")
            print("   Email: dual@teste.com")
            print("   Senha: 123456")
            print("   Papéis: cliente e prestador")
            print(f"   Carteira criada com ID: {wallet.id}")
        except Exception as e:
            print(f"❌ Erro ao criar carteira: {e}")

if __name__ == '__main__':
    create_prestador_user()
    create_dual_user()
