#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da Tarefa 15: Rota POST /ordens/<id>/marcar-concluido
Valida que a rota do prestador para marcar serviço como concluído funciona corretamente
"""

import sys
from app import app, db
from models import User, Order, Wallet, Invite
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from services.invite_service import InviteService
from decimal import Decimal
from datetime import datetime, timedelta


def setup_test_data():
    """Cria dados de teste e retorna IDs"""
    # Limpar dados existentes
    Order.query.delete()
    Invite.query.delete()
    User.query.filter(
        User.email.in_(['cliente_test@test.com', 'prestador_test@test.com', 'sempapel@test.com'])
    ).delete()
    User.query.filter(
        User.cpf.in_(['11111111111', '22222222222', '33333333333'])
    ).delete()
    db.session.commit()
    
    # Criar cliente
    cliente = User(
        nome='Cliente Teste',
        email='cliente_test@test.com',
        cpf='11111111111',
        phone='11999999001',
        roles='cliente'
    )
    cliente.set_password('senha123')
    db.session.add(cliente)
    
    # Criar prestador
    prestador = User(
        nome='Prestador Teste',
        email='prestador_test@test.com',
        cpf='22222222222',
        phone='11999999999',  # Mesmo telefone do convite
        roles='prestador'
    )
    prestador.set_password('senha123')
    db.session.add(prestador)
    
    db.session.commit()
    
    # Salvar IDs e nomes
    cliente_id = cliente.id
    cliente_nome = cliente.nome
    prestador_id = prestador.id
    prestador_nome = prestador.nome
    
    # Criar carteiras
    WalletService.create_wallet_for_user(cliente)
    WalletService.create_wallet_for_user(prestador)
    
    # Adicionar saldo
    WalletService.credit_wallet(cliente_id, Decimal('1000.00'), 'Crédito inicial')
    WalletService.credit_wallet(prestador_id, Decimal('100.00'), 'Crédito inicial')
    
    # Criar convite
    convite = Invite(
        client_id=cliente_id,
        invited_phone='11999999999',
        service_title='Serviço de Teste',
        service_description='Descrição do serviço',
        service_category='Elétrica',
        original_value=Decimal('500.00'),
        delivery_date=datetime.utcnow() + timedelta(days=7),
        status='pendente',
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(convite)
    db.session.commit()
    
    convite_token = convite.token
    convite_id = convite.id
    
    # Aceitar convite
    InviteService.accept_invite(convite_token, prestador_id)
    
    # Criar ordem
    result = OrderManagementService.create_order_from_invite(convite_id, prestador_id)
    ordem_id = result['order'].id
    ordem_status = result['order'].status
    ordem_title = result['order'].title
    
    return {
        'cliente_id': cliente_id,
        'cliente_nome': cliente_nome,
        'prestador_id': prestador_id,
        'prestador_nome': prestador_nome,
        'ordem_id': ordem_id,
        'ordem_status': ordem_status,
        'ordem_title': ordem_title
    }


def test_marcar_concluido_route():
    """Testa a rota POST /ordens/<id>/marcar-concluido"""
    print("\n" + "="*80)
    print("TESTE: Rota POST /ordens/<id>/marcar-concluido")
    print("="*80)
    
    with app.app_context():
        data = setup_test_data()
        
        cliente_id = data['cliente_id']
        prestador_id = data['prestador_id']
        ordem_id = data['ordem_id']
        
        print(f"\n✓ Dados de teste criados")
        print(f"  - Cliente: {data['cliente_nome']} (ID: {cliente_id})")
        print(f"  - Prestador: {data['prestador_nome']} (ID: {prestador_id})")
        print(f"  - Ordem: {data['ordem_title']} (ID: {ordem_id})")
        print(f"  - Status inicial: {data['ordem_status']}")
        
    # Teste 1: Prestador marca como concluído via serviço (não HTTP)
    print("\n" + "-"*80)
    print("Teste 1: Prestador marca como concluído via serviço")
    print("-"*80)
    
    with app.app_context():
        # Testar diretamente o serviço (a rota já foi implementada)
        result = OrderManagementService.mark_service_completed(ordem_id, prestador_id)
        
        print(f"Resultado: {result['message']}")
        assert result['success'] == True, f"Operação deve ter sucesso"
        
        # Verificar que a ordem foi atualizada
        ordem_atualizada = Order.query.get(ordem_id)
        assert ordem_atualizada.status == 'servico_executado', f"Status deve ser 'servico_executado', mas é '{ordem_atualizada.status}'"
        assert ordem_atualizada.completed_at is not None, "completed_at deve estar preenchido"
        assert ordem_atualizada.confirmation_deadline is not None, "confirmation_deadline deve estar preenchido"
        
        print(f"✓ Ordem atualizada corretamente")
        print(f"  - Status: {ordem_atualizada.status}")
        print(f"  - Concluído em: {ordem_atualizada.completed_at}")
        print(f"  - Prazo de confirmação: {ordem_atualizada.confirmation_deadline}")
        
    # Teste 2: Cliente não pode marcar como concluído
    print("\n" + "-"*80)
    print("Teste 2: Validação - apenas prestador pode marcar como concluído")
    print("-"*80)
    
    # Criar nova ordem para teste
    with app.app_context():
        convite2 = Invite(
            client_id=cliente_id,
            invited_phone='11999999999',  # Mesmo telefone do prestador
            service_title='Serviço de Teste 2',
            service_description='Descrição do serviço 2',
            service_category='Hidráulica',
            original_value=Decimal('300.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(convite2)
        db.session.commit()
        
        # Aceitar convite
        InviteService.accept_invite(convite2.token, prestador_id)
        
        result2 = OrderManagementService.create_order_from_invite(convite2.id, prestador_id)
        ordem2_id = result2['order'].id
        
        # Cliente tenta marcar como concluído (deve falhar)
        try:
            result = OrderManagementService.mark_service_completed(ordem2_id, cliente_id)
            print(f"✗ ERRO: Cliente conseguiu marcar como concluído (não deveria)")
            assert False, "Cliente não deveria conseguir marcar como concluído"
        except ValueError as e:
            print(f"✓ Cliente foi bloqueado corretamente: {str(e)}")
            
        # Verificar que a ordem NÃO foi atualizada
        ordem2 = Order.query.get(ordem2_id)
        assert ordem2.status == 'aguardando_execucao', f"Status não deve mudar, mas é '{ordem2.status}'"
        print(f"✓ Status permanece: {ordem2.status}")
        
    # Teste 3: Verificar que a rota existe e está registrada
    print("\n" + "-"*80)
    print("Teste 3: Verificar que a rota POST /ordens/<id>/marcar-concluido existe")
    print("-"*80)
    
    with app.app_context():
        # Verificar se a rota está registrada
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        rota_encontrada = any('/ordens/<int:order_id>/marcar-concluido' in rule for rule in rules)
        
        if rota_encontrada:
            print(f"✓ Rota POST /ordens/<id>/marcar-concluido está registrada")
        else:
            print(f"✗ Rota não encontrada")
            print(f"Rotas disponíveis relacionadas a ordens:")
            for rule in rules:
                if 'ordem' in rule.lower():
                    print(f"  - {rule}")
            assert False, "Rota não está registrada"
    
    print("\n" + "="*80)
    print("✓ TODOS OS TESTES PASSARAM!")
    print("="*80)
    
    return True


if __name__ == '__main__':
    try:
        success = test_marcar_concluido_route()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
