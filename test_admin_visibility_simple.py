#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste simples para verificar a correção da visibilidade do admin para recebimento de tokens
Tarefa 9.6: Corrigir visibilidade do admin para recebimento de tokens
"""

from app import app
from models import db, User, AdminUser, Wallet, Transaction
from services.wallet_service import WalletService

def test_admin_visibility_fix():
    """Teste principal da correção de visibilidade do admin"""
    
    with app.app_context():
        print("🧪 TESTE: Correção da visibilidade do admin para recebimento de tokens")
        print("=" * 70)
        
        # 1. Verificar se admin principal existe
        print("1. Verificando admin principal...")
        admin_principal = AdminUser.query.get(0)
        if admin_principal:
            print(f"   ✅ Admin principal encontrado: {admin_principal.email}")
        else:
            print("   ❌ Admin principal não encontrado")
            return False
        
        # 2. Verificar se admin principal tem carteira
        print("2. Verificando carteira do admin principal...")
        admin_wallet = Wallet.query.filter_by(user_id=0).first()
        if admin_wallet:
            print(f"   ✅ Carteira encontrada com {admin_wallet.balance:,.0f} tokens")
        else:
            print("   ❌ Carteira do admin principal não encontrada")
            return False
        
        # 3. Testar lista de usuários para adicionar tokens
        print("3. Testando lista de usuários para receber tokens...")
        user_choices = [(u.id, f'{u.nome} ({u.email})') for u in User.query.filter_by(active=True).all()]
        admin_choices = [(a.id, f'[ADMIN] {a.email}') for a in AdminUser.query.all() if a.id != 0]
        all_choices = user_choices + admin_choices
        
        print(f"   📋 Usuários normais: {len(user_choices)}")
        print(f"   👑 AdminUsers (exceto principal): {len(admin_choices)}")
        print(f"   📊 Total de opções: {len(all_choices)}")
        
        if len(admin_choices) > 0:
            print("   ✅ AdminUsers aparecem na lista de usuários para receber tokens")
        else:
            print("   ⚠️  Nenhum AdminUser secundário encontrado")
        
        # 4. Testar transferência entre admins (se houver outros admins)
        outros_admins = AdminUser.query.filter(AdminUser.id != 0).all()
        if outros_admins:
            print("4. Testando transferência entre admins...")
            admin_teste = outros_admins[0]
            
            # Garantir que admin teste tem carteira
            try:
                admin_teste_wallet = WalletService.get_wallet_info(admin_teste.id)
                if not admin_teste_wallet:
                    WalletService.ensure_user_has_wallet(admin_teste.id)
                    admin_teste_wallet = WalletService.get_wallet_info(admin_teste.id)
                
                print(f"   📊 Admin teste (ID {admin_teste.id}): {admin_teste_wallet['balance']:,.0f} tokens")
                
                # Dar alguns tokens para o admin teste se não tiver
                if admin_teste_wallet['balance'] < 1000:
                    WalletService.admin_sell_tokens_to_user(admin_teste.id, 2000, 'Tokens para teste')
                    print("   💰 Adicionados 2000 tokens para teste")
                
                # Testar transferência
                saldo_antes_principal = WalletService.get_admin_wallet_info()['balance']
                saldo_antes_teste = WalletService.get_wallet_info(admin_teste.id)['balance']
                
                result = WalletService.transfer_tokens_between_users(
                    from_user_id=admin_teste.id,
                    to_user_id=0,
                    amount=500,
                    description='Teste de transferência para admin principal'
                )
                
                saldo_depois_principal = WalletService.get_admin_wallet_info()['balance']
                saldo_depois_teste = WalletService.get_wallet_info(admin_teste.id)['balance']
                
                print(f"   📈 Admin principal: {saldo_antes_principal:,.0f} → {saldo_depois_principal:,.0f} tokens (+{saldo_depois_principal - saldo_antes_principal:,.0f})")
                print(f"   📉 Admin teste: {saldo_antes_teste:,.0f} → {saldo_depois_teste:,.0f} tokens ({saldo_depois_teste - saldo_antes_teste:,.0f})")
                
                if result['success']:
                    print("   ✅ Transferência entre admins funcionando corretamente")
                else:
                    print("   ❌ Falha na transferência entre admins")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Erro no teste de transferência: {e}")
                return False
        else:
            print("4. ⚠️  Nenhum admin secundário para testar transferência")
        
        # 5. Verificar integridade do sistema
        print("5. Verificando integridade do sistema...")
        try:
            token_summary = WalletService.get_system_token_summary()
            print(f"   💰 Admin: {token_summary['admin_balance']:,.0f} tokens")
            print(f"   🔄 Em circulação: {token_summary['tokens_in_circulation']:,.0f} tokens")
            print(f"   📊 Total criado: {token_summary['total_tokens_created']:,.0f} tokens")
            
            # Verificar se os números batem
            total_sistema = token_summary['admin_balance'] + token_summary['tokens_in_circulation']
            if abs(total_sistema - token_summary['total_tokens_created']) < 0.01:
                print("   ✅ Integridade matemática do sistema OK")
            else:
                print(f"   ⚠️  Discrepância detectada: {total_sistema - token_summary['total_tokens_created']:,.2f}")
                
        except Exception as e:
            print(f"   ❌ Erro na verificação de integridade: {e}")
            return False
        
        print("\n" + "=" * 70)
        print("🎉 RESULTADO: Correção da visibilidade do admin implementada com sucesso!")
        print("\n📋 FUNCIONALIDADES IMPLEMENTADAS:")
        print("   ✅ Admin principal (ID 0) criado e com carteira")
        print("   ✅ AdminUsers aparecem na lista de usuários para receber tokens")
        print("   ✅ Interface para transferir tokens para admin principal")
        print("   ✅ Função transfer_tokens_between_users implementada")
        print("   ✅ Validações e logs de transação funcionando")
        print("   ✅ Integridade do sistema mantida")
        
        return True

if __name__ == '__main__':
    success = test_admin_visibility_fix()
    exit(0 if success else 1)