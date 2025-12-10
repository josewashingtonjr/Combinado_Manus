#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Integração - Fluxos Completos do Sistema de Ordens
Valida os fluxos end-to-end do sistema de gestão de ordens
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models import db, User, Order, Invite, Wallet, Transaction
from services.order_management_service import OrderManagementService
from services.wallet_service import WalletService
from services.config_service import ConfigService


class TestCompleteOrderFlow:
    """Testes do fluxo completo: criação → conclusão → confirmação manual"""
    
    def test_full_order_flow_with_manual_confirmation(self, app, db_session):
        """
        Testa o fluxo completo de uma ordem com confirmação manual
        
        Fluxo:
        1. Cliente cria convite
        2. Prestador aceita convite
        3. Ordem é criada com bloqueio de valores
        4. Prestador marca serviço como concluído
        5. Cliente confirma manualmente
        6. Pagamentos são processados corretamente
        """
        with app.app_context():
            # Setup: Criar usuários
            cliente = User(
                email='cliente_flow1@test.com',
                nome='Cliente Flow 1',
                cpf='11111111111',
                phone='11999990001',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_flow1@test.com',
                nome='Prestador Flow 1',
                cpf='22222222222',
                phone='11999990002',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Setup: Criar carteiras com saldo
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            
            # Passo 1: Cliente cria convite
            invite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Instalação de Ar Condicionado',
                service_description='Instalação completa com suporte',
                service_category='instalador',
                original_value=Decimal('300.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite)
            db_session.commit()
            
            # Passo 2 e 3: Ordem é criada a partir do convite
            result_create = OrderManagementService.create_order_from_invite(invite.id, prestador.id)
            
            assert result_create['success'] is True
            order_id = result_create['order_id']
            order = result_create['order']
            
            # Validar estado inicial da ordem
            assert order.status == 'aguardando_execucao'
            assert order.value == Decimal('300.00')
            
            # Validar bloqueios de escrow
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            contestation_fee = result_create['contestation_fee']
            assert client_wallet.escrow_balance == Decimal('300.00') + Decimal(str(contestation_fee))
            assert provider_wallet.escrow_balance == Decimal(str(contestation_fee))
            
            # Passo 4: Prestador marca como concluído
            result_complete = OrderManagementService.mark_service_completed(order_id, prestador.id)
            
            assert result_complete['success'] is True
            assert result_complete['status'] == 'servico_executado'
            assert result_complete['hours_to_confirm'] == 36
            
            db_session.refresh(order)
            assert order.status == 'servico_executado'
            assert order.completed_at is not None
            assert order.confirmation_deadline is not None
            
            # Passo 5: Cliente confirma manualmente
            result_confirm = OrderManagementService.confirm_service(order_id, cliente.id)
            
            assert result_confirm['success'] is True
            assert result_confirm['status'] == 'concluida'
            assert result_confirm['confirmation_type'] == 'manual'
            
            # Passo 6: Validar pagamentos processados
            db_session.refresh(order)
            assert order.status == 'concluida'
            assert order.confirmed_at is not None
            assert order.auto_confirmed is False
            
            # Validar valores finais nas carteiras
            db_session.refresh(client_wallet)
            db_session.refresh(provider_wallet)
            
            # Cliente deve ter recebido devolução da taxa de contestação
            # Prestador deve ter recebido valor líquido + devolução da taxa de contestação
            platform_fee = Decimal('300.00') * Decimal('0.05')  # 5%
            provider_net = Decimal('300.00') - platform_fee
            
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.balance > Decimal('50.00')  # Saldo inicial + pagamento


class TestAutoConfirmationFlow:
    """Testes do fluxo de confirmação automática após 36h"""
    
    def test_auto_confirmation_after_36_hours(self, app, db_session):
        """
        Testa confirmação automática quando cliente não confirma em 36h
        
        Fluxo:
        1. Ordem é criada e marcada como concluída
        2. 36 horas se passam (simulado)
        3. Job de confirmação automática é executado
        4. Ordem é confirmada automaticamente
        5. Pagamentos são processados
        """
        with app.app_context():
            # Setup: Criar usuários
            cliente = User(
                email='cliente_auto@test.com',
                nome='Cliente Auto',
                cpf='33333333333',
                phone='11999990003',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_auto@test.com',
                nome='Prestador Auto',
                cpf='44444444444',
                phone='11999990004',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Setup: Criar carteiras com saldo
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('250.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Crédito', 'credito')
            
            # Passo 1: Criar ordem em status servico_executado com prazo expirado
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço para Auto-Confirmação',
                description='Teste de confirmação automática',
                value=service_value,
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow() - timedelta(hours=48),  # 48h atrás
                confirmation_deadline=datetime.utcnow() - timedelta(hours=12),  # Expirado há 12h
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            # Transferir para escrow
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Passo 3: Executar job de confirmação automática
            result = OrderManagementService.auto_confirm_expired_orders()
            
            # Passo 4: Validar que ordem foi confirmada automaticamente
            assert result['processed'] >= 1
            assert result['confirmed'] >= 1
            
            db_session.refresh(order)
            assert order.status == 'concluida'
            assert order.confirmed_at is not None
            assert order.auto_confirmed is True
            
            # Passo 5: Validar pagamentos processados
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.escrow_balance == Decimal('0.00')


class TestCancellationFlow:
    """Testes do fluxo de cancelamento com multas"""
    
    def test_cancellation_by_client_with_penalty(self, app, db_session):
        """
        Testa cancelamento pelo cliente com aplicação de multa
        
        Fluxo:
        1. Ordem é criada
        2. Cliente cancela a ordem
        3. Multa é calculada (10% do valor)
        4. 50% da multa vai para plataforma
        5. 50% da multa vai para prestador (parte prejudicada)
        6. Valor restante é devolvido ao cliente
        7. Taxas de contestação são devolvidas
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_cancel@test.com',
                nome='Cliente Cancel',
                cpf='55555555555',
                phone='11999990005',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_cancel@test.com',
                nome='Prestador Cancel',
                cpf='66666666666',
                phone='11999990006',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Crédito', 'credito')
            
            # Criar ordem
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço a Cancelar',
                description='Teste de cancelamento',
                value=service_value,
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Saldos iniciais
            client_wallet_before = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet_before = Wallet.query.filter_by(user_id=prestador.id).first()
            initial_client_balance = client_wallet_before.balance
            initial_provider_balance = provider_wallet_before.balance
            
            # Passo 2: Cliente cancela
            result = OrderManagementService.cancel_order(
                order.id,
                cliente.id,
                'Mudança de planos, não preciso mais do serviço'
            )
            
            # Validações
            assert result['success'] is True
            assert result['status'] == 'cancelada'
            assert result['cancelled_by'] == 'cliente'
            assert result['injured_party'] == 'prestador'
            
            # Passo 3: Validar multa calculada
            cancellation_fee = Decimal('200.00') * Decimal('0.10')  # 10%
            assert result['cancellation_fee'] == float(cancellation_fee)
            
            # Passo 4 e 5: Validar distribuição da multa
            platform_share = cancellation_fee / Decimal('2')
            injured_party_share = cancellation_fee / Decimal('2')
            
            assert result['platform_share'] == float(platform_share)
            assert result['injured_party_share'] == float(injured_party_share)
            
            # Passo 6 e 7: Validar devoluções
            db_session.refresh(client_wallet_before)
            db_session.refresh(provider_wallet_before)
            
            # Cliente recebe: valor - multa + taxa de contestação devolvida
            expected_client_return = service_value - cancellation_fee + contestation_fee
            # Prestador recebe: 50% da multa + taxa de contestação devolvida
            expected_provider_gain = injured_party_share + contestation_fee
            
            assert client_wallet_before.balance == initial_client_balance + expected_client_return
            assert provider_wallet_before.balance == initial_provider_balance + expected_provider_gain
            assert client_wallet_before.escrow_balance == Decimal('0.00')
            assert provider_wallet_before.escrow_balance == Decimal('0.00')
    
    def test_cancellation_by_provider_with_penalty(self, app, db_session):
        """
        Testa cancelamento pelo prestador com aplicação de multa
        
        Fluxo similar ao cancelamento por cliente, mas:
        - Prestador paga a multa do seu saldo disponível
        - Cliente recebe valor completo de volta
        - Cliente recebe 50% da multa como compensação
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_pcancel@test.com',
                nome='Cliente PCancel',
                cpf='77777777777',
                phone='11999990007',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_pcancel@test.com',
                nome='Prestador PCancel',
                cpf='88888888888',
                phone='11999990008',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('200.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Crédito', 'credito')
            # Prestador precisa de saldo para pagar a multa
            WalletService.credit_wallet(prestador.id, Decimal('100.00'), 'Crédito', 'credito')
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço a Cancelar por Prestador',
                description='Teste',
                value=service_value,
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Prestador cancela
            result = OrderManagementService.cancel_order(
                order.id,
                prestador.id,
                'Não consigo realizar o serviço no prazo'
            )
            
            assert result['success'] is True
            assert result['cancelled_by'] == 'prestador'
            assert result['injured_party'] == 'cliente'
            
            # Cliente deve receber valor completo + 50% da multa + taxa de contestação
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            assert client_wallet.escrow_balance == Decimal('0.00')


class TestDisputeFlow:
    """Testes do fluxo de contestação e arbitragem"""
    
    def test_dispute_flow_client_wins(self, app, db_session):
        """
        Testa fluxo de contestação onde cliente ganha
        
        Fluxo:
        1. Ordem é marcada como concluída
        2. Cliente abre contestação
        3. Admin arbitra a favor do cliente
        4. Cliente recebe valor de volta
        5. Taxa de contestação do cliente vai para plataforma
        6. Taxa de contestação do prestador é devolvida
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_dispute@test.com',
                nome='Cliente Dispute',
                cpf='99999999999',
                phone='11999990009',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_dispute@test.com',
                nome='Prestador Dispute',
                cpf='10101010101',
                phone='11999990010',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('300.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Crédito', 'credito')
            
            # Passo 1: Criar ordem concluída
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Contestado',
                description='Teste de contestação',
                value=service_value,
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36),
                dispute_deadline=datetime.utcnow() + timedelta(hours=36),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Passo 2: Cliente abre contestação
            result_dispute = OrderManagementService.open_dispute(
                order.id,
                cliente.id,
                'O serviço não foi realizado conforme combinado. Há vários problemas.'
            )
            
            assert result_dispute['success'] is True
            assert result_dispute['status'] == 'contestada'
            
            db_session.refresh(order)
            assert order.status == 'contestada'
            assert order.dispute_opened_by == cliente.id
            
            # Passo 3: Admin arbitra a favor do cliente
            result_resolve = OrderManagementService.resolve_dispute(
                order.id,
                1,  # admin_id
                'client',
                'Análise das provas confirma que o serviço não foi realizado adequadamente'
            )
            
            assert result_resolve['success'] is True
            assert result_resolve['status'] == 'resolvida'
            assert result_resolve['winner'] == 'client'
            
            # Passo 4, 5, 6: Validar pagamentos
            db_session.refresh(order)
            assert order.status == 'resolvida'
            assert order.dispute_winner == 'client'
            
            client_wallet = Wallet.query.filter_by(user_id=cliente.id).first()
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert client_wallet.escrow_balance == Decimal('0.00')
            assert provider_wallet.escrow_balance == Decimal('0.00')
    
    def test_dispute_flow_provider_wins(self, app, db_session):
        """
        Testa fluxo de contestação onde prestador ganha
        
        Fluxo:
        1. Ordem é marcada como concluída
        2. Cliente abre contestação
        3. Admin arbitra a favor do prestador
        4. Prestador recebe valor líquido (valor - taxa plataforma)
        5. Plataforma recebe taxa da plataforma
        6. Taxa de contestação do prestador é devolvida
        7. Taxa de contestação do cliente vai para plataforma
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_pdispute@test.com',
                nome='Cliente PDispute',
                cpf='11111111112',
                phone='11999990011',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_pdispute@test.com',
                nome='Prestador PDispute',
                cpf='22222222223',
                phone='11999990012',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            service_value = Decimal('400.00')
            contestation_fee = Decimal('10.00')
            
            WalletService.credit_wallet(cliente.id, service_value + contestation_fee, 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, contestation_fee, 'Crédito', 'credito')
            
            order = Order(
                client_id=cliente.id,
                provider_id=prestador.id,
                title='Serviço Bem Feito',
                description='Teste',
                value=service_value,
                status='servico_executado',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                completed_at=datetime.utcnow(),
                confirmation_deadline=datetime.utcnow() + timedelta(hours=36),
                dispute_deadline=datetime.utcnow() + timedelta(hours=36),
                platform_fee_percentage_at_creation=Decimal('5.0'),
                contestation_fee_at_creation=contestation_fee,
                cancellation_fee_percentage_at_creation=Decimal('10.0')
            )
            db_session.add(order)
            db_session.commit()
            
            WalletService.transfer_to_escrow(cliente.id, service_value + contestation_fee, order.id)
            WalletService.transfer_to_escrow(prestador.id, contestation_fee, order.id)
            
            # Cliente abre contestação
            OrderManagementService.open_dispute(
                order.id,
                cliente.id,
                'Não gostei do resultado, mas na verdade o serviço foi bem feito'
            )
            
            # Admin arbitra a favor do prestador
            result = OrderManagementService.resolve_dispute(
                order.id,
                1,
                'provider',
                'Serviço foi realizado conforme combinado'
            )
            
            assert result['success'] is True
            assert result['winner'] == 'provider'
            
            db_session.refresh(order)
            assert order.dispute_winner == 'provider'
            
            # Validar que prestador recebeu pagamento
            provider_wallet = Wallet.query.filter_by(user_id=prestador.id).first()
            assert provider_wallet.escrow_balance == Decimal('0.00')
            # Prestador deve ter recebido valor líquido + devolução da taxa
            platform_fee = service_value * Decimal('0.05')
            expected_provider_amount = service_value - platform_fee + contestation_fee
            assert provider_wallet.balance >= expected_provider_amount


class TestFeeUpdateImpact:
    """Testes de atualização de taxas e impacto em ordens"""
    
    def test_fee_update_does_not_affect_existing_orders(self, app, db_session):
        """
        Testa que alteração de taxas não afeta ordens já criadas
        
        Fluxo:
        1. Criar ordem com taxas atuais (5%, R$10, 10%)
        2. Alterar taxas do sistema (10%, R$20, 20%)
        3. Confirmar ordem antiga
        4. Validar que taxas antigas foram aplicadas
        5. Criar nova ordem
        6. Validar que novas taxas foram aplicadas
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_fee@test.com',
                nome='Cliente Fee',
                cpf='33333333334',
                phone='11999990013',
                roles='cliente'
            )
            cliente.set_password('senha123')
            prestador = User(
                email='prestador_fee@test.com',
                nome='Prestador Fee',
                cpf='44444444445',
                phone='11999990014',
                roles='prestador'
            )
            prestador.set_password('senha123')
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('1000.00'), 'Crédito', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('100.00'), 'Crédito', 'credito')
            
            # Passo 1: Criar ordem com taxas atuais
            invite1 = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Antigo',
                service_description='Teste',
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite1)
            db_session.commit()
            
            result1 = OrderManagementService.create_order_from_invite(invite1.id, prestador.id)
            order1 = result1['order']
            
            # Armazenar taxas originais
            original_platform_fee = order1.platform_fee_percentage_at_creation
            original_contestation_fee = order1.contestation_fee_at_creation
            original_cancellation_fee = order1.cancellation_fee_percentage_at_creation
            
            # Passo 2: Alterar taxas do sistema
            ConfigService.set_platform_fee_percentage(Decimal('10.0'))
            ConfigService.set_contestation_fee(Decimal('20.00'))
            ConfigService.set_cancellation_fee_percentage(Decimal('20.0'))
            
            # Passo 3 e 4: Confirmar ordem antiga e validar taxas
            OrderManagementService.mark_service_completed(order1.id, prestador.id)
            OrderManagementService.confirm_service(order1.id, cliente.id)
            
            db_session.refresh(order1)
            
            # Validar que taxas antigas foram usadas
            assert order1.platform_fee_percentage_at_creation == original_platform_fee
            assert order1.contestation_fee_at_creation == original_contestation_fee
            
            # Passo 5: Criar nova ordem
            invite2 = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Novo',
                service_description='Teste',
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='aceito'
            )
            db_session.add(invite2)
            db_session.commit()
            
            result2 = OrderManagementService.create_order_from_invite(invite2.id, prestador.id)
            order2 = result2['order']
            
            # Passo 6: Validar que novas taxas foram aplicadas
            assert order2.platform_fee_percentage_at_creation == Decimal('10.0')
            assert order2.contestation_fee_at_creation == Decimal('20.00')
            assert order2.cancellation_fee_percentage_at_creation == Decimal('20.0')
            
            # Restaurar taxas originais
            ConfigService.set_platform_fee_percentage(Decimal('5.0'))
            ConfigService.set_contestation_fee(Decimal('10.00'))
            ConfigService.set_cancellation_fee_percentage(Decimal('10.0'))
