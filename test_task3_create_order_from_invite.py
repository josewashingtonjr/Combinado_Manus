#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a implementação da Tarefa 3:
OrderManagementService.create_order_from_invite()
"""

import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_create_order_from_invite():
    """Testa a criação de ordem a partir de convite"""
    
    print("\n" + "="*80)
    print("TESTE: OrderManagementService.create_order_from_invite()")
    print("="*80)
    
    try:
        from app import app
        from models import db, User, Invite, Order, Wallet
        from services.order_management_service import OrderManagementService
        from services.wallet_service import WalletService
        from services.config_service import ConfigService
        from datetime import datetime, timedelta
        
        with app.app_context():
            # Limpar dados de teste anteriores
            print("\n1️⃣ Limpando dados de teste anteriores...")
            Order.query.filter(Order.title.like('%TESTE TAREFA 3%')).delete()
            Invite.query.filter(Invite.service_title.like('%TESTE TAREFA 3%')).delete()
            db.session.commit()
            print("   ✅ Dados limpos")
            
            # Criar usuários de teste
            print("\n2️⃣ Criando usuários de teste...")
            
            # Cliente
            cliente = User.query.filter_by(email='cliente_teste_t3@example.com').first()
            if not cliente:
                cliente = User(
                    email='cliente_teste_t3@example.com',
                    nome='Cliente Teste T3',
                    cpf='11111111111',
                    phone='11999999001',
                    roles='cliente'
                )
                cliente.set_password('senha123')
                db.session.add(cliente)
                db.session.flush()
            
            # Prestador
            prestador = User.query.filter_by(email='prestador_teste_t3@example.com').first()
            if not prestador:
                prestador = User(
                    email='prestador_teste_t3@example.com',
                    nome='Prestador Teste T3',
                    cpf='22222222222',
                    phone='11999999002',
                    roles='prestador'
                )
                prestador.set_password('senha123')
                db.session.add(prestador)
                db.session.flush()
            
            db.session.commit()
            print(f"   ✅ Cliente criado: ID {cliente.id}")
            print(f"   ✅ Prestador criado: ID {prestador.id}")
            
            # Garantir carteiras
            print("\n3️⃣ Garantindo carteiras...")
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            print("   ✅ Carteiras criadas")
            
            # Adicionar saldo aos usuários
            print("\n4️⃣ Adicionando saldo aos usuários...")
            
            # Obter taxas atuais
            contestation_fee = ConfigService.get_contestation_fee()
            service_value = Decimal('150.00')
            
            # Cliente precisa: valor do serviço + taxa de contestação
            client_needed = service_value + contestation_fee
            WalletService.credit_wallet(
                cliente.id,
                client_needed,
                "Crédito para teste tarefa 3",
                "credito"
            )
            
            # Prestador precisa: taxa de contestação
            WalletService.credit_wallet(
                prestador.id,
                contestation_fee,
                "Crédito para teste tarefa 3",
                "credito"
            )
            
            print(f"   ✅ Cliente: R$ {client_needed:.2f}")
            print(f"   ✅ Prestador: R$ {contestation_fee:.2f}")
            
            # Criar convite aceito
            print("\n5️⃣ Criando convite aceito...")
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='TESTE TAREFA 3 - Instalação Elétrica',
                service_description='Instalação de tomadas e interruptores',
                service_category='eletricista',
                original_value=service_value,
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db.session.add(invite)
            db.session.commit()
            print(f"   ✅ Convite criado: ID {invite.id}")
            print(f"   📋 Valor: R$ {invite.current_value:.2f}")
            print(f"   📋 Status: {invite.status}")
            
            # Testar criação de ordem
            print("\n6️⃣ Testando create_order_from_invite()...")
            print(f"   📞 Chamando OrderManagementService.create_order_from_invite({invite.id}, {prestador.id})")
            
            result = OrderManagementService.create_order_from_invite(
                invite_id=invite.id,
                provider_id=prestador.id
            )
            
            print(f"   ✅ Ordem criada com sucesso!")
            print(f"   📋 Order ID: {result['order_id']}")
            print(f"   📋 Status: {result['order'].status}")
            print(f"   📋 Valor efetivo: R$ {result['effective_value']:.2f}")
            print(f"   📋 Valor original: R$ {result['original_value']:.2f}")
            
            # Validar resultado
            print("\n7️⃣ Validando resultado...")
            
            order = result['order']
            
            # Verificar campos da ordem
            assert order.client_id == cliente.id, "Cliente incorreto"
            assert order.provider_id == prestador.id, "Prestador incorreto"
            assert order.status == 'aguardando_execucao', f"Status incorreto: {order.status}"
            assert order.value == service_value, f"Valor incorreto: {order.value}"
            assert order.invite_id == invite.id, "Invite ID incorreto"
            print("   ✅ Campos da ordem corretos")
            
            # Verificar taxas armazenadas
            assert order.platform_fee_percentage_at_creation is not None, "Taxa da plataforma não armazenada"
            assert order.contestation_fee_at_creation is not None, "Taxa de contestação não armazenada"
            assert order.cancellation_fee_percentage_at_creation is not None, "Taxa de cancelamento não armazenada"
            print("   ✅ Taxas armazenadas corretamente")
            print(f"      - Taxa plataforma: {order.platform_fee_percentage_at_creation}%")
            print(f"      - Taxa contestação: R$ {order.contestation_fee_at_creation:.2f}")
            print(f"      - Taxa cancelamento: {order.cancellation_fee_percentage_at_creation}%")
            
            # Verificar convite atualizado
            db.session.refresh(invite)
            assert invite.status == 'convertido', f"Status do convite incorreto: {invite.status}"
            assert invite.order_id == order.id, "Order ID não atualizado no convite"
            print("   ✅ Convite atualizado corretamente")
            
            # Verificar saldos em escrow
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            expected_client_escrow = service_value + contestation_fee
            expected_provider_escrow = contestation_fee
            
            assert client_wallet.escrow_balance == expected_client_escrow, \
                f"Escrow do cliente incorreto: {client_wallet.escrow_balance} != {expected_client_escrow}"
            assert provider_wallet.escrow_balance == expected_provider_escrow, \
                f"Escrow do prestador incorreto: {provider_wallet.escrow_balance} != {expected_provider_escrow}"
            
            print("   ✅ Valores bloqueados em escrow corretamente")
            print(f"      - Cliente: R$ {client_wallet.escrow_balance:.2f}")
            print(f"      - Prestador: R$ {provider_wallet.escrow_balance:.2f}")
            
            # Verificar transações registradas
            from models import Transaction
            transactions = Transaction.query.filter_by(order_id=order.id).all()
            assert len(transactions) >= 2, f"Transações insuficientes: {len(transactions)}"
            print(f"   ✅ {len(transactions)} transações registradas")
            
            print("\n" + "="*80)
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*80)
            print("\n📊 Resumo:")
            print(f"   - Ordem criada: #{order.id}")
            print(f"   - Cliente: {cliente.nome} (ID {cliente.id})")
            print(f"   - Prestador: {prestador.nome} (ID {prestador.id})")
            print(f"   - Valor: R$ {order.value:.2f}")
            print(f"   - Status: {order.status}")
            print(f"   - Escrow cliente: R$ {client_wallet.escrow_balance:.2f}")
            print(f"   - Escrow prestador: R$ {provider_wallet.escrow_balance:.2f}")
            print(f"   - Transações: {len(transactions)}")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_create_order_from_invite()
    sys.exit(0 if success else 1)
