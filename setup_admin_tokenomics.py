#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import os
os.environ['DATABASE_URL'] = 'sqlite:///test_wallets.db'

from app import app, db
from models import User, AdminUser, Wallet, Transaction
from services.wallet_service import WalletService

def setup_admin_tokenomics():
    """Configura o sistema com admin tendo a primeira carteira e todos os tokens"""
    with app.app_context():
        print("🔧 Configurando sistema de tokenomics com admin...")
        
        # 1. Criar admin se não existir
        admin = AdminUser.query.get(1)
        if not admin:
            print("📝 Criando usuário admin...")
            admin = AdminUser(
                id=1,
                email='admin@combinado.com',
                papel='super_admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin criado: {admin.email}")
        else:
            print(f"✅ Admin já existe: {admin.email}")
        
        # 2. Garantir que admin tem carteira com tokens iniciais
        print("💰 Configurando carteira do admin...")
        admin_wallet = WalletService.ensure_admin_has_wallet()
        print(f"✅ Admin tem carteira com {admin_wallet.balance:,.0f} tokens")
        
        # 3. Verificar tokens em circulação
        print("\n📊 Resumo do sistema de tokens:")
        summary = WalletService.get_system_token_summary()
        
        print(f"💼 Tokens na carteira do admin: {summary['admin_balance']:,.0f}")
        print(f"🔄 Tokens em circulação: {summary['tokens_in_circulation']:,.0f}")
        print(f"🏭 Total de tokens criados: {summary['total_tokens_created']:,.0f}")
        print(f"📈 % em circulação: {summary['circulation_percentage']:.1f}%")
        
        # 4. Mostrar usuários e suas carteiras
        print("\n👥 Usuários no sistema:")
        users = User.query.all()
        for user in users:
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if wallet:
                print(f"   {user.email}: {wallet.balance:,.2f} tokens (Escrow: {wallet.escrow_balance:,.2f})")
            else:
                print(f"   {user.email}: SEM CARTEIRA")
        
        print(f"\n✅ Sistema configurado corretamente!")
        print(f"🔑 Admin: admin@combinado.com / admin123")
        print(f"💰 Admin possui {admin_wallet.balance:,.0f} tokens para vender aos usuários")

def test_tokenomics_flow():
    """Testa o fluxo completo de tokenomics"""
    with app.app_context():
        print("\n🧪 Testando fluxo de tokenomics...")
        
        # Pegar um usuário para teste
        user = User.query.first()
        if not user:
            print("❌ Nenhum usuário encontrado para teste")
            return
        
        print(f"👤 Testando com usuário: {user.email}")
        
        # Estado inicial
        admin_info_before = WalletService.get_admin_wallet_info()
        user_info_before = WalletService.get_wallet_info(user.id)
        
        print(f"📊 Estado inicial:")
        print(f"   Admin: {admin_info_before['balance']:,.2f} tokens")
        print(f"   {user.email}: {user_info_before['balance']:,.2f} tokens")
        
        # Usuário "compra" tokens (admin vende)
        print(f"\n💳 Usuário comprando 100 tokens...")
        result = WalletService.deposit(user.id, 100.0, "Compra de tokens para teste")
        
        print(f"✅ Compra realizada:")
        print(f"   Admin agora tem: {result['admin_new_balance']:,.2f} tokens")
        print(f"   {user.email} agora tem: {result['user_new_balance']:,.2f} tokens")
        
        # Usuário "saca" tokens (vende de volta para admin)
        print(f"\n💸 Usuário sacando 50 tokens...")
        result = WalletService.withdraw(user.id, 50.0, "Saque de tokens para teste")
        
        print(f"✅ Saque realizado:")
        print(f"   Admin agora tem: {result['admin_new_balance']:,.2f} tokens")
        print(f"   {user.email} agora tem: {result['user_new_balance']:,.2f} tokens")
        
        # Verificar integridade
        print(f"\n🔒 Verificando integridade...")
        admin_integrity = WalletService.validate_transaction_integrity(1)  # Admin ID = 1
        user_integrity = WalletService.validate_transaction_integrity(user.id)
        
        print(f"   Admin: {'✅ Válido' if admin_integrity['is_valid'] else '❌ Inválido'}")
        print(f"   {user.email}: {'✅ Válido' if user_integrity['is_valid'] else '❌ Inválido'}")
        
        # Resumo final
        print(f"\n📈 Resumo final do sistema:")
        summary = WalletService.get_system_token_summary()
        print(f"   Total de tokens no sistema: {summary['total_tokens_in_system']:,.0f}")
        print(f"   Tokens em circulação: {summary['tokens_in_circulation']:,.0f}")
        print(f"   Tokens na carteira do admin: {summary['admin_balance']:,.0f}")

def test_admin_create_tokens():
    """Testa a criação de novos tokens pelo admin"""
    with app.app_context():
        print("\n🏭 Testando criação de novos tokens pelo admin...")
        
        # Estado antes
        summary_before = WalletService.get_system_token_summary()
        print(f"📊 Antes: {summary_before['total_tokens_created']:,.0f} tokens criados")
        
        # Admin cria mais tokens
        print("💰 Admin criando 50.000 novos tokens...")
        result = WalletService.admin_create_tokens(50000.0, "Expansão da oferta de tokens")
        
        print(f"✅ Tokens criados com sucesso!")
        print(f"   Novos tokens: {result['tokens_created']:,.0f}")
        print(f"   Saldo do admin: {result['new_admin_balance']:,.0f}")
        
        # Estado depois
        summary_after = WalletService.get_system_token_summary()
        print(f"📊 Depois: {summary_after['total_tokens_created']:,.0f} tokens criados")
        print(f"📈 Aumento: {summary_after['total_tokens_created'] - summary_before['total_tokens_created']:,.0f} tokens")

if __name__ == '__main__':
    setup_admin_tokenomics()
    test_tokenomics_flow()
    test_admin_create_tokens()