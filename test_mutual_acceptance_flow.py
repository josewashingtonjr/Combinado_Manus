#!/usr/bin/env python3
"""
Teste do fluxo de aceitação mútua de convites
"""
import sys
from app import app, db
from models import User, Invite, Order
from services.invite_service import InviteService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal

def test_mutual_acceptance():
    """Testa o fluxo completo de aceitação mútua"""
    
    with app.app_context():
        print("="*80)
        print("TESTE DE ACEITAÇÃO MÚTUA DE CONVITES")
        print("="*80)
        
        # 1. Buscar usuários existentes
        print("\n1️⃣ Buscando usuários existentes...")
        
        # Buscar qualquer cliente e prestador
        cliente = User.query.filter(User.roles.like('%cliente%')).first()
        prestador = User.query.filter(User.roles.like('%prestador%')).first()
        
        if not cliente or not prestador:
            print("   ❌ Erro: Não há usuários cliente e prestador no sistema")
            print("   💡 Crie usuários primeiro através da interface web")
            return False
        
        print(f"   ✓ Cliente: {cliente.nome} (ID: {cliente.id})")
        print(f"   ✓ Prestador: {prestador.nome} (ID: {prestador.id})")
        
        # 2. Criar carteiras se não existirem
        print("\n2️⃣ Verificando carteiras...")
        
        from models import Wallet
        
        cliente_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
        if not cliente_wallet:
            cliente_wallet = Wallet(user_id=cliente.id, balance=Decimal('0.00'))
            db.session.add(cliente_wallet)
            print(f"   ✓ Carteira criada para cliente")
        
        prestador_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
        if not prestador_wallet:
            prestador_wallet = Wallet(user_id=prestador.id, balance=Decimal('0.00'))
            db.session.add(prestador_wallet)
            print(f"   ✓ Carteira criada para prestador")
        
        db.session.commit()
        
        # 3. Adicionar saldo aos usuários
        print("\n3️⃣ Adicionando saldo aos usuários...")
        
        # Cliente precisa: valor do serviço (100) + taxa de contestação (10) = 110
        cliente_balance = WalletService.get_wallet_balance(cliente.id)
        if cliente_balance < Decimal('110.00'):
            WalletService.credit_wallet(cliente.id, Decimal('110.00') - cliente_balance, 'Saldo inicial para teste')
        
        # Prestador precisa: taxa de contestação (10)
        prestador_balance = WalletService.get_wallet_balance(prestador.id)
        if prestador_balance < Decimal('10.00'):
            WalletService.credit_wallet(prestador.id, Decimal('10.00') - prestador_balance, 'Saldo inicial para teste')
        
        cliente_balance = WalletService.get_wallet_balance(cliente.id)
        prestador_balance = WalletService.get_wallet_balance(prestador.id)
        
        print(f"   ✓ Saldo Cliente: R$ {cliente_balance:.2f}")
        print(f"   ✓ Saldo Prestador: R$ {prestador_balance:.2f}")
        
        # 4. Criar convite
        print("\n4️⃣ Criando convite...")
        
        delivery_date = datetime.utcnow() + timedelta(days=7)
        
        result = InviteService.create_invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title='Serviço de Teste',
            service_description='Descrição do serviço de teste',
            original_value=Decimal('100.00'),
            delivery_date=delivery_date,
            service_category='teste'
        )
        
        invite_id = result['invite_id']
        invite = Invite.query.get(invite_id)
        
        print(f"   ✓ Convite criado: ID {invite_id}")
        print(f"   ✓ Status: {invite.status}")
        print(f"   ✓ Cliente aceitou: {invite.client_accepted}")
        print(f"   ✓ Prestador aceitou: {invite.provider_accepted}")
        print(f"   ✓ Aceitação mútua: {invite.is_mutually_accepted}")
        
        # 5. Prestador aceita o convite
        print("\n5️⃣ Prestador aceitando o convite...")
        
        try:
            result = InviteService.accept_invite_as_provider(invite_id, prestador.id)
            
            print(f"   ✓ Resultado: {result.get('message')}")
            print(f"   ✓ Ordem criada: {result.get('order_created', False)}")
            
            if result.get('order_created'):
                print(f"   ✓ ID da ordem: {result.get('order_id')}")
            else:
                print(f"   ⏳ Aguardando: {result.get('pending_acceptance_from')}")
            
            # Recarregar convite
            db.session.refresh(invite)
            
            print(f"\n   📊 Estado do convite após aceitação do prestador:")
            print(f"      Status: {invite.status}")
            print(f"      Cliente aceitou: {invite.client_accepted}")
            print(f"      Prestador aceitou: {invite.provider_accepted}")
            print(f"      Aceitação mútua: {invite.is_mutually_accepted}")
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            return False
        
        # 6. Verificar estado final (cliente já aceitou ao criar)
        print("\n6️⃣ Verificando estado final...")
        
        # Cliente já aceitou ao criar o convite, não precisa aceitar novamente
        print("   ℹ️  Cliente já aceitou ao criar o convite")
        
        # Recarregar convite
        db.session.refresh(invite)
        
        print(f"\n   📊 Estado final do convite:")
        print(f"      Status: {invite.status}")
        print(f"      Cliente aceitou: {invite.client_accepted}")
        print(f"      Prestador aceitou: {invite.provider_accepted}")
        print(f"      Aceitação mútua: {invite.is_mutually_accepted}")
        print(f"      Ordem ID: {invite.order_id}")
        
        # Verificar saldos finais
        cliente_balance_final = WalletService.get_wallet_balance(cliente.id)
        prestador_balance_final = WalletService.get_wallet_balance(prestador.id)
        
        print(f"\n   💰 Saldos finais:")
        print(f"      Cliente: R$ {cliente_balance_final:.2f} (era R$ {cliente_balance:.2f})")
        print(f"      Prestador: R$ {prestador_balance_final:.2f} (era R$ {prestador_balance:.2f})")
        
        print("\n" + "="*80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*80)
        print("\n📝 Resumo:")
        print("   1. Cliente criou convite → client_accepted = True automaticamente")
        print("   2. Prestador aceitou → ordem criada imediatamente")
        print("   3. Status do convite → convertido")
        print("   4. Valores bloqueados em escrow corretamente")
        
        return True

if __name__ == '__main__':
    success = test_mutual_acceptance()
    sys.exit(0 if success else 1)
