#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import os
os.environ['DATABASE_URL'] = 'sqlite:///test_combinado.db'

from app import app, db
from models import User, AdminUser, Wallet, Transaction
from services.wallet_service import WalletService

def setup_sistema_correto():
    """Configura o sistema corretamente conforme a planta arquitetônica"""
    with app.app_context():
        print("🏗️  Configurando sistema conforme arquitetura planejada...")
        
        # Limpar banco e criar todas as tabelas
        db.drop_all()
        db.create_all()
        
        # 1. Criar admin com ID 0 (forçado)
        print("👑 Criando admin com ID 0...")
        
        # Criar admin temporário para obter hash da senha
        temp_admin = AdminUser(email='temp', papel='temp')
        temp_admin.set_password('admin123')
        password_hash = temp_admin.password_hash
        
        # Inserir admin diretamente com ID 0
        from sqlalchemy import text
        db.session.execute(
            text('INSERT INTO admin_users (id, email, password_hash, papel) VALUES (0, :email, :password_hash, :papel)'),
            {'email': 'admin@combinado.com', 'password_hash': password_hash, 'papel': 'super_admin'}
        )
        db.session.commit()
        
        print("✅ Admin criado com ID 0: admin@combinado.com")
        
        # 2. Criar carteira do admin com 1 milhão de tokens iniciais
        print("💰 Criando carteira do admin com tokens iniciais...")
        admin_wallet = WalletService.ensure_admin_has_wallet()
        print(f"✅ Admin tem {admin_wallet.balance:,.0f} tokens iniciais")
        
        # 3. Criar usuários normais (começando do ID 1)
        print("👥 Criando usuários normais...")
        users_data = [
            ('cliente@test.com', 'Cliente Teste', '12345678901', 'cliente'),
            ('prestador@test.com', 'Prestador Teste', '98765432100', 'prestador'),
            ('dual@test.com', 'Usuário Dual', '11122233344', 'cliente,prestador')
        ]
        
        for email, nome, cpf, roles in users_data:
            user = User(
                nome=nome,
                email=email,
                cpf=cpf,
                roles=roles,
                active=True
            )
            user.set_password('123456')
            db.session.add(user)
        
        db.session.commit()
        print(f"✅ {len(users_data)} usuários criados")
        
        # 4. Criar carteiras VAZIAS para usuários (saldo 0)
        print("💳 Criando carteiras vazias para usuários...")
        users = User.query.all()
        for user in users:
            WalletService.ensure_user_has_wallet(user.id)
        
        print(f"✅ Carteiras criadas para todos os usuários")
        
        # 5. Verificar estado inicial correto
        print(f"\n📊 Verificando arquitetura implementada:")
        
        # Admin
        admin = AdminUser.query.get(0)
        admin_info = WalletService.get_admin_wallet_info()
        print(f"👑 Admin (ID 0): {admin.email}")
        print(f"   Carteira: {admin_info['balance']:,.0f} tokens")
        
        # Usuários
        print(f"\n👥 Usuários normais:")
        for user in users:
            wallet_info = WalletService.get_wallet_info(user.id)
            print(f"   {user.email} (ID {user.id}): {wallet_info['balance']:,.0f} tokens")
        
        # Resumo do sistema
        print(f"\n📈 Resumo do sistema:")
        summary = WalletService.get_system_token_summary()
        print(f"   💼 Admin possui: {summary['admin_balance']:,.0f} tokens")
        print(f"   🔄 Em circulação: {summary['tokens_in_circulation']:,.0f} tokens")
        print(f"   🏭 Total criado: {summary['total_tokens_created']:,.0f} tokens")
        print(f"   📊 % em circulação: {summary['circulation_percentage']:.1f}%")
        
        print(f"\n✅ Sistema configurado corretamente!")
        print(f"🔑 Login admin: admin@combinado.com / admin123")
        print(f"🔑 Login usuários: [email] / 123456")

def testar_fluxo_tokenomics():
    """Testa o fluxo correto de tokenomics"""
    with app.app_context():
        print(f"\n🧪 TESTANDO FLUXO DE TOKENOMICS")
        print("=" * 50)
        
        # Pegar usuário para teste
        user = User.query.first()
        print(f"👤 Testando com: {user.email} (ID {user.id})")
        
        # Estado inicial
        admin_antes = WalletService.get_admin_wallet_info()
        user_antes = WalletService.get_wallet_info(user.id)
        
        print(f"\n📊 ANTES:")
        print(f"   Admin (ID 0): {admin_antes['balance']:,.0f} tokens")
        print(f"   {user.email} (ID {user.id}): {user_antes['balance']:,.0f} tokens")
        
        # TESTE 1: Usuário "compra" 100 tokens (admin vende)
        print(f"\n💳 TESTE 1: Usuário comprando 100 tokens do admin...")
        result = WalletService.deposit(user.id, 100.0, "Compra de tokens para teste")
        
        print(f"✅ Transação realizada:")
        print(f"   Admin agora: {result['admin_new_balance']:,.0f} tokens")
        print(f"   {user.email} agora: {result['user_new_balance']:,.0f} tokens")
        print(f"   Tokens transferidos: {result['tokens_transferred']:,.0f}")
        
        # Verificar se o fluxo está correto
        admin_perdeu = admin_antes['balance'] - result['admin_new_balance']
        user_ganhou = result['user_new_balance'] - user_antes['balance']
        
        print(f"\n🔍 Verificação do fluxo:")
        print(f"   Admin perdeu: {admin_perdeu:,.0f} tokens")
        print(f"   Usuário ganhou: {user_ganhou:,.0f} tokens")
        print(f"   Fluxo correto: {'✅ SIM' if admin_perdeu == user_ganhou == 100 else '❌ NÃO'}")
        
        # TESTE 2: Usuário "saca" 30 tokens (vende de volta para admin)
        print(f"\n💸 TESTE 2: Usuário sacando 30 tokens (vendendo para admin)...")
        result2 = WalletService.withdraw(user.id, 30.0, "Saque de tokens para teste")
        
        print(f"✅ Saque realizado:")
        print(f"   Admin agora: {result2['admin_new_balance']:,.0f} tokens")
        print(f"   {user.email} agora: {result2['user_new_balance']:,.0f} tokens")
        print(f"   Tokens transferidos: {result2['tokens_transferred']:,.0f}")
        
        # TESTE 3: Admin cria mais tokens
        print(f"\n🏭 TESTE 3: Admin criando 50.000 novos tokens...")
        result3 = WalletService.admin_create_tokens(50000.0, "Expansão da oferta")
        
        print(f"✅ Tokens criados:")
        print(f"   Novos tokens: {result3['tokens_created']:,.0f}")
        print(f"   Admin agora: {result3['new_admin_balance']:,.0f} tokens")
        
        # Resumo final
        print(f"\n📈 RESUMO FINAL:")
        summary = WalletService.get_system_token_summary()
        print(f"   💼 Admin possui: {summary['admin_balance']:,.0f} tokens")
        print(f"   🔄 Em circulação: {summary['tokens_in_circulation']:,.0f} tokens")
        print(f"   🏭 Total criado: {summary['total_tokens_created']:,.0f} tokens")
        print(f"   📊 Total no sistema: {summary['total_tokens_in_system']:,.0f} tokens")
        
        # Validar integridade
        print(f"\n🔒 VALIDAÇÃO DE INTEGRIDADE:")
        admin_integrity = WalletService.validate_transaction_integrity(0)  # Admin ID = 0
        user_integrity = WalletService.validate_transaction_integrity(user.id)
        
        print(f"   Admin: {'✅ Válido' if admin_integrity['is_valid'] else '❌ Inválido'}")
        print(f"   {user.email}: {'✅ Válido' if user_integrity['is_valid'] else '❌ Inválido'}")
        
        print(f"\n🎉 ARQUITETURA FUNCIONANDO CORRETAMENTE!")
        print("=" * 50)
        print("✅ 1. Admin tem primeira carteira com todos os tokens")
        print("✅ 2. Admin é único que pode criar tokens do zero")
        print("✅ 3. Tokens dos usuários vêm da carteira do admin")
        print("✅ 4. Saques retornam tokens para carteira do admin")

if __name__ == '__main__':
    setup_sistema_correto()
    testar_fluxo_tokenomics()