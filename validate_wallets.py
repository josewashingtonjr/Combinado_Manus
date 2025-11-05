#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import os
import sys

# Configurar para usar SQLite de teste
os.environ['DATABASE_URL'] = 'sqlite:///test_wallets.db'

from app import app, db
from models import User, Wallet
from services.wallet_service import WalletService

def validate_and_create_wallets():
    """Valida que todos os usuários tenham carteiras e cria as que estão faltando"""
    with app.app_context():
        print("🔍 Validando carteiras de usuários...")
        
        # Verificar usuários sem carteiras
        users_without_wallets = WalletService.validate_all_users_have_wallets()
        
        if not users_without_wallets:
            print("✅ Todos os usuários já possuem carteiras!")
            return
        
        print(f"⚠️  Encontrados {len(users_without_wallets)} usuários sem carteiras:")
        for user in users_without_wallets:
            print(f"   - {user.email} (ID: {user.id})")
        
        # Criar carteiras faltantes
        print("\n🔧 Criando carteiras faltantes...")
        created_count = WalletService.create_missing_wallets()
        
        print(f"✅ {created_count} carteiras criadas com sucesso!")
        
        # Verificar novamente
        remaining_users = WalletService.validate_all_users_have_wallets()
        if not remaining_users:
            print("✅ Validação final: Todos os usuários agora possuem carteiras!")
        else:
            print(f"❌ Ainda restam {len(remaining_users)} usuários sem carteiras")

def show_wallet_summary():
    """Mostra um resumo das carteiras no sistema"""
    with app.app_context():
        print("\n📊 Resumo das Carteiras:")
        print("=" * 50)
        
        users = User.query.filter_by(active=True).all()
        total_users = len(users)
        users_with_wallets = 0
        total_balance = 0.0
        total_escrow = 0.0
        
        for user in users:
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if wallet:
                users_with_wallets += 1
                total_balance += wallet.balance
                total_escrow += wallet.escrow_balance
                print(f"👤 {user.nome} ({user.email})")
                print(f"   Saldo: R$ {wallet.balance:.2f}")
                print(f"   Escrow: R$ {wallet.escrow_balance:.2f}")
                print(f"   Papéis: {user.roles}")
                print()
        
        print("=" * 50)
        print(f"Total de usuários: {total_users}")
        print(f"Usuários com carteiras: {users_with_wallets}")
        print(f"Saldo total no sistema: R$ {total_balance:.2f}")
        print(f"Total em escrow: R$ {total_escrow:.2f}")
        print(f"Total de tokens no sistema: R$ {total_balance + total_escrow:.2f}")

if __name__ == '__main__':
    validate_and_create_wallets()
    show_wallet_summary()