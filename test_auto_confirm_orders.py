#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do método auto_confirm_expired_orders()
Valida a confirmação automática de ordens após 36h
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Order, User, Wallet, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from decimal import Decimal


def setup_test_data():
    """Cria dados de teste"""
    with app.app_context():
        # Limpar dados existentes
        Order.query.delete()
        Invite.query.delete()
        db.session.commit()
        
        # Criar usuários de teste se não existirem
        cliente = User.query.filter_by(email='cliente_test@test.com').first()
        if not cliente:
            cliente = User(
                nome='Cliente Teste',
                email='cliente_test@test.com',
                cpf='11111111111',
                phone='11999999001',
                roles='cliente'
            )
            cliente.set_password('senha123')
            db.session.add(cliente)
            db.session.commit()
        
        prestador = User.query.filter_by(email='prestador_test@test.com').first()
        if not prestador:
            prestador = User(
                nome='Prestador Teste',
                email='prestador_test@test.com',
                cpf='22222222222',
                phone='11999999002',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db.session.add(prestador)
            db.session.commit()
        
        # Salvar IDs
        cliente_id = cliente.id
        prestador_id = prestador.id
        
        # Garantir que ambos têm carteiras
        WalletService.ensure_user_has_wallet(cliente_id)
        WalletService.ensure_user_has_wallet(prestador_id)
        
        # Verificar saldo atual e adicionar o necessário
        cliente_wallet = Wallet.query.filter_by(user_id=cliente_id).first()
        prestador_wallet = Wallet.query.filter_by(user_id=prestador_id).first()
        
        # Adicionar saldo suficiente se necessário
        if cliente_wallet.balance < Decimal('500.00'):
            WalletService.admin_sell_tokens_to_user(cliente_id, Decimal('2000.00'), 'Crédito inicial teste')
        
        if prestador_wallet.balance < Decimal('50.00'):
            WalletService.admin_sell_tokens_to_user(prestador_id, Decimal('200.00'), 'Crédito inicial teste')
        
        # Buscar novamente para ter objetos anexados à sessão
        cliente = User.query.get(cliente_id)
        prestador = User.query.get(prestador_id)
        
        return cliente, prestador


def test_auto_confirm_expired_orders():
    """Testa a confirmação automática de ordens expiradas"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Confirmação Automática de Ordens Expiradas")
        print("="*80)
        
        # 1. Setup
        cliente, prestador = setup_test_data()
        
        print(f"\n1. Criando convite e ordem de teste...")
        print(f"   Cliente: {cliente.nome} (ID: {cliente.id})")
        print(f"   Prestador: {prestador.nome} (ID: {prestador.id})")
        
        # Criar convite
        convite = Invite(
            client_id=cliente.id,
            invited_phone='11999999999',
            service_title='Teste Auto Confirmação',
            service_description='Serviço para testar confirmação automática',
            original_value=Decimal('100.00'),
            effective_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            created_at=datetime.utcnow()
        )
        db.session.add(convite)
        db.session.commit()
        
        # Criar ordem a partir do convite
        result = OrderManagementService.create_order_from_invite(convite.id, prestador.id)
        ordem_id = result['order_id']
        
        print(f"   ✓ Ordem {ordem_id} criada com sucesso")
        print(f"   Valor: R$ {result['effective_value']:.2f}")
        
        # 2. Marcar como concluído
        print(f"\n2. Prestador marca serviço como concluído...")
        result = OrderManagementService.mark_service_completed(ordem_id, prestador.id)
        
        print(f"   ✓ Status: {result['status']}")
        print(f"   Prazo para confirmação: {result['hours_to_confirm']}h")
        print(f"   Deadline: {result['confirmation_deadline']}")
        
        # 3. Simular expiração do prazo (alterar manualmente a deadline)
        print(f"\n3. Simulando expiração do prazo de 36h...")
        ordem = Order.query.get(ordem_id)
        ordem.confirmation_deadline = datetime.utcnow() - timedelta(hours=1)  # Expirado há 1 hora
        ordem.completed_at = datetime.utcnow() - timedelta(hours=37)  # Concluído há 37 horas
        db.session.commit()
        
        print(f"   ✓ Deadline alterada para: {ordem.confirmation_deadline}")
        print(f"   ✓ Ordem agora está expirada")
        
        # 4. Verificar saldos antes da confirmação automática
        print(f"\n4. Saldos ANTES da confirmação automática:")
        cliente_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
        prestador_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
        
        print(f"   Cliente:")
        print(f"     - Disponível: R$ {cliente_wallet.balance:.2f}")
        print(f"     - Bloqueado: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"   Prestador:")
        print(f"     - Disponível: R$ {prestador_wallet.balance:.2f}")
        print(f"     - Bloqueado: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # 5. Executar confirmação automática
        print(f"\n5. Executando job de confirmação automática...")
        result = OrderManagementService.auto_confirm_expired_orders()
        
        print(f"\n   RESULTADO DO JOB:")
        print(f"   - Ordens processadas: {result['processed']}")
        print(f"   - Ordens confirmadas: {result['confirmed']}")
        print(f"   - Erros: {len(result['errors'])}")
        print(f"   - Timestamp: {result['timestamp']}")
        
        if result['errors']:
            print(f"\n   ERROS ENCONTRADOS:")
            for error in result['errors']:
                print(f"     - {error}")
        
        # 6. Verificar resultado
        print(f"\n6. Verificando resultado da confirmação automática...")
        ordem = Order.query.get(ordem_id)
        
        print(f"   Status da ordem: {ordem.status}")
        print(f"   Auto confirmada: {ordem.auto_confirmed}")
        print(f"   Confirmada em: {ordem.confirmed_at}")
        print(f"   Taxa da plataforma: R$ {ordem.platform_fee:.2f}")
        
        # 7. Verificar saldos após confirmação
        print(f"\n7. Saldos DEPOIS da confirmação automática:")
        db.session.refresh(cliente_wallet)
        db.session.refresh(prestador_wallet)
        
        print(f"   Cliente:")
        print(f"     - Disponível: R$ {cliente_wallet.balance:.2f}")
        print(f"     - Bloqueado: R$ {cliente_wallet.escrow_balance:.2f}")
        print(f"   Prestador:")
        print(f"     - Disponível: R$ {prestador_wallet.balance:.2f}")
        print(f"     - Bloqueado: R$ {prestador_wallet.escrow_balance:.2f}")
        
        # 8. Validações
        print(f"\n8. Validações:")
        
        assert result['processed'] == 1, "Deveria ter processado 1 ordem"
        print(f"   ✓ Processou 1 ordem")
        
        assert result['confirmed'] == 1, "Deveria ter confirmado 1 ordem"
        print(f"   ✓ Confirmou 1 ordem")
        
        assert len(result['errors']) == 0, f"Não deveria ter erros: {result['errors']}"
        print(f"   ✓ Sem erros")
        
        assert ordem.status == 'concluida', f"Status deveria ser 'concluida', mas é '{ordem.status}'"
        print(f"   ✓ Status = 'concluida'")
        
        assert ordem.auto_confirmed == True, "Deveria estar marcada como auto_confirmed"
        print(f"   ✓ auto_confirmed = True")
        
        assert ordem.confirmed_at is not None, "Deveria ter confirmed_at preenchido"
        print(f"   ✓ confirmed_at preenchido")
        
        assert ordem.platform_fee > 0, "Deveria ter taxa da plataforma calculada"
        print(f"   ✓ Taxa da plataforma calculada: R$ {ordem.platform_fee:.2f}")
        
        # Verificar que os valores foram desbloqueados
        assert cliente_wallet.escrow_balance == 0, "Cliente não deveria ter saldo bloqueado"
        print(f"   ✓ Saldo bloqueado do cliente zerado")
        
        assert prestador_wallet.escrow_balance == 0, "Prestador não deveria ter saldo bloqueado"
        print(f"   ✓ Saldo bloqueado do prestador zerado")
        
        # Verificar que o prestador recebeu o pagamento
        assert prestador_wallet.balance > Decimal('100.00'), "Prestador deveria ter recebido pagamento"
        print(f"   ✓ Prestador recebeu pagamento")
        
        print(f"\n" + "="*80)
        print("✓ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*80)


def test_auto_confirm_with_errors():
    """Testa que erros individuais não interrompem o processamento"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Tratamento de Erros Individuais")
        print("="*80)
        
        # Criar uma ordem válida e uma inválida
        cliente, prestador = setup_test_data()
        
        # Criar ordem válida
        convite1 = Invite(
            client_id=cliente.id,
            invited_phone='11999999999',
            service_title='Ordem Válida',
            service_description='Esta ordem deve ser confirmada',
            original_value=Decimal('50.00'),
            effective_value=Decimal('50.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            created_at=datetime.utcnow()
        )
        db.session.add(convite1)
        db.session.commit()
        
        result1 = OrderManagementService.create_order_from_invite(convite1.id, prestador.id)
        ordem1_id = result1['order_id']
        
        OrderManagementService.mark_service_completed(ordem1_id, prestador.id)
        
        ordem1 = Order.query.get(ordem1_id)
        ordem1.confirmation_deadline = datetime.utcnow() - timedelta(hours=1)
        ordem1.completed_at = datetime.utcnow() - timedelta(hours=37)
        db.session.commit()
        
        print(f"   ✓ Ordem válida criada: {ordem1_id}")
        
        # Executar confirmação automática
        print(f"\n   Executando job de confirmação automática...")
        result = OrderManagementService.auto_confirm_expired_orders()
        
        print(f"\n   RESULTADO:")
        print(f"   - Processadas: {result['processed']}")
        print(f"   - Confirmadas: {result['confirmed']}")
        print(f"   - Erros: {len(result['errors'])}")
        
        # Validar que pelo menos a ordem válida foi confirmada
        assert result['confirmed'] >= 1, "Pelo menos 1 ordem deveria ter sido confirmada"
        print(f"\n   ✓ Pelo menos 1 ordem foi confirmada com sucesso")
        
        print(f"\n" + "="*80)
        print("✓ TESTE DE TRATAMENTO DE ERROS CONCLUÍDO!")
        print("="*80)


if __name__ == '__main__':
    try:
        test_auto_confirm_expired_orders()
        test_auto_confirm_with_errors()
        
        print("\n" + "="*80)
        print("TODOS OS TESTES PASSARAM! ✓")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ ERRO DE VALIDAÇÃO: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
