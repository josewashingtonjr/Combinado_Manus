#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Integração - Fluxo de Aceitação de Convites e Criação de Pré-Ordens
Valida o fluxo completo de aceitação mútua e criação automática de pré-ordens

ATUALIZADO: Agora o fluxo cria Pré-Ordens ao invés de Ordens diretas,
permitindo negociação antes do compromisso financeiro.
Ref: sistema-pre-ordem-negociacao, otimizacao-mobile-usabilidade
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from models import db, User, Order, Invite, Wallet, Transaction, PreOrder, PreOrderStatus
from services.invite_acceptance_coordinator import InviteAcceptanceCoordinator
from services.invite_service import InviteService
from services.wallet_service import WalletService
from services.dashboard_data_service import DashboardDataService
from services.cliente_service import ClienteService
from services.prestador_service import PrestadorService
from services.pre_order_service import PreOrderService


class TestFluxoCompletoAceitacao:
    """Testes do fluxo completo de aceitação mútua - Cria Pré-Ordem"""
    
    def test_fluxo_completo_prestador_aceita_primeiro(self, app, db_session):
        """
        Testa o fluxo completo quando prestador aceita primeiro
        
        Fluxo ATUALIZADO (sistema-pre-ordem-negociacao):
        1. Cliente cria convite
        2. Prestador aceita convite
        3. Cliente aceita convite
        4. Verificar PRÉ-ORDEM criada automaticamente (não ordem)
        5. Verificar valores NÃO bloqueados (bloqueio só na conversão)
        """
        with app.app_context():
            # Passo 1: Setup - Criar usuários
            cliente = User(
                email='cliente_flow@test.com',
                nome='Cliente Teste',
                cpf='11111111111',
                phone='11999990001',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_flow@test.com',
                nome='Prestador Teste',
                cpf='22222222222',
                phone='11999990002',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            # Criar carteiras com saldo suficiente
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            
            # Cliente cria convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Instalação de Ar Condicionado',
                service_description='Instalação completa com suporte',
                service_category='instalador',
                original_value=Decimal('300.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Verificar estado inicial
            assert convite.status == 'pendente'
            assert convite.client_accepted is False
            assert convite.provider_accepted is False
            
            # Passo 2: Prestador aceita convite
            resultado_prestador = InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            assert resultado_prestador['success'] is True
            assert resultado_prestador['order_created'] is False
            assert resultado_prestador['pre_order_created'] is False
            assert resultado_prestador['message'] == 'Convite aceito! Aguardando aceitação do cliente.'
            
            db_session.refresh(convite)
            assert convite.provider_accepted is True
            assert convite.provider_accepted_at is not None
            assert convite.client_accepted is False
            assert convite.status == 'pendente'  # Ainda pendente até ambos aceitarem
            
            # Passo 3: Cliente aceita convite
            resultado_cliente = InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            assert resultado_cliente['success'] is True
            # NOVO COMPORTAMENTO: Cria pré-ordem, não ordem
            assert resultado_cliente['pre_order_created'] is True
            assert resultado_cliente['order_created'] is False
            assert 'pre_order_id' in resultado_cliente
            
            # Passo 4: Verificar PRÉ-ORDEM criada automaticamente
            db_session.refresh(convite)
            assert convite.client_accepted is True
            assert convite.client_accepted_at is not None
            assert convite.status == 'convertido_pre_ordem'
            
            pre_ordem = PreOrder.query.get(resultado_cliente['pre_order_id'])
            assert pre_ordem is not None
            assert pre_ordem.client_id == cliente.id
            assert pre_ordem.provider_id == prestador.id
            assert pre_ordem.title == 'Instalação de Ar Condicionado'
            assert pre_ordem.current_value == Decimal('300.00')
            assert pre_ordem.status == PreOrderStatus.EM_NEGOCIACAO.value
            assert pre_ordem.invite_id == convite.id
            
            # Passo 5: Verificar valores NÃO bloqueados (bloqueio só na conversão)
            carteira_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            carteira_prestador = Wallet.query.filter_by(user_id=prestador.id).first()
            
            # Valores NÃO devem estar bloqueados na pré-ordem
            assert carteira_cliente.escrow_balance == Decimal('0.00')
            assert carteira_cliente.balance == Decimal('500.00')
            
            assert carteira_prestador.escrow_balance == Decimal('0.00')
            assert carteira_prestador.balance == Decimal('50.00')
    
    def test_fluxo_completo_cliente_aceita_primeiro(self, app, db_session):
        """
        Testa o fluxo completo quando cliente aceita primeiro
        
        Fluxo ATUALIZADO (sistema-pre-ordem-negociacao):
        1. Cliente cria convite
        2. Cliente aceita convite
        3. Prestador aceita convite
        4. Verificar PRÉ-ORDEM criada automaticamente (não ordem)
        5. Verificar valores NÃO bloqueados
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_flow2@test.com',
                nome='Cliente Teste 2',
                cpf='33333333333',
                phone='11999990003',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_flow2@test.com',
                nome='Prestador Teste 2',
                cpf='44444444444',
                phone='11999990004',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('400.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('30.00'), 'Crédito inicial', 'credito')
            
            # Cliente cria convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Manutenção de Computador',
                service_description='Limpeza e upgrade',
                service_category='tecnico',
                original_value=Decimal('150.00'),
                delivery_date=datetime.utcnow() + timedelta(days=3),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Passo 2: Cliente aceita primeiro
            resultado_cliente = InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            assert resultado_cliente['success'] is True
            assert resultado_cliente['order_created'] is False
            assert resultado_cliente['pre_order_created'] is False
            assert resultado_cliente['message'] == 'Convite aceito! Aguardando aceitação do prestador.'
            
            db_session.refresh(convite)
            assert convite.client_accepted is True
            assert convite.provider_accepted is False
            assert convite.status == 'pendente'
            
            # Passo 3: Prestador aceita depois
            resultado_prestador = InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            assert resultado_prestador['success'] is True
            # NOVO COMPORTAMENTO: Cria pré-ordem, não ordem
            assert resultado_prestador['pre_order_created'] is True
            assert resultado_prestador['order_created'] is False
            assert 'pre_order_id' in resultado_prestador
            
            # Passo 4: Verificar PRÉ-ORDEM criada
            db_session.refresh(convite)
            assert convite.status == 'convertido_pre_ordem'
            
            pre_ordem = PreOrder.query.get(resultado_prestador['pre_order_id'])
            assert pre_ordem is not None
            assert pre_ordem.current_value == Decimal('150.00')
            assert pre_ordem.status == PreOrderStatus.EM_NEGOCIACAO.value
            
            # Passo 5: Verificar valores NÃO bloqueados
            carteira_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            carteira_prestador = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert carteira_cliente.escrow_balance == Decimal('0.00')
            assert carteira_prestador.escrow_balance == Decimal('0.00')


class TestFluxoSaldoInsuficiente:
    """Testes do fluxo com saldo insuficiente"""
    
    def test_cliente_saldo_insuficiente_tenta_aceitar(self, app, db_session):
        """
        Testa quando cliente com saldo baixo tenta aceitar
        
        Fluxo:
        1. Cliente com saldo baixo tenta aceitar convite
        2. Verificar erro apropriado
        3. Adicionar saldo
        4. Aceitar com sucesso - cria PRÉ-ORDEM
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_pobre@test.com',
                nome='Cliente Sem Saldo',
                cpf='55555555555',
                phone='11999990005',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_rico@test.com',
                nome='Prestador Com Saldo',
                cpf='66666666666',
                phone='11999990006',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            # Passo 1: Cliente com saldo insuficiente (apenas R$ 50)
            WalletService.credit_wallet(cliente.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            
            # Criar convite de R$ 200
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Caro',
                service_description='Serviço que cliente não pode pagar',
                service_category='geral',
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Prestador aceita primeiro
            InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            # Passo 2: Cliente tenta aceitar com saldo insuficiente
            from services.exceptions import InsufficientBalanceError
            with pytest.raises(InsufficientBalanceError) as exc_info:
                InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            # Verificar erro apropriado
            assert 'Saldo insuficiente' in str(exc_info.value)
            
            # Verificar que convite não foi alterado
            db_session.refresh(convite)
            assert convite.client_accepted is False
            assert convite.status == 'pendente'
            
            # Passo 3: Adicionar saldo suficiente
            WalletService.credit_wallet(cliente.id, Decimal('250.00'), 'Adição de saldo', 'credito')
            
            carteira_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            assert carteira_cliente.balance >= Decimal('200.00')
            
            # Passo 4: Aceitar com sucesso - cria PRÉ-ORDEM
            resultado = InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            assert resultado['success'] is True
            assert resultado['pre_order_created'] is True
            
            db_session.refresh(convite)
            assert convite.client_accepted is True
            assert convite.status == 'convertido_pre_ordem'
            
            # Verificar pré-ordem criada
            pre_ordem = PreOrder.query.filter_by(invite_id=convite.id).first()
            assert pre_ordem is not None
            assert pre_ordem.current_value == Decimal('200.00')
    
    def test_prestador_saldo_insuficiente_tenta_aceitar(self, app, db_session):
        """
        Testa quando prestador com saldo baixo tenta aceitar
        
        Fluxo:
        1. Prestador sem saldo para taxa tenta aceitar
        2. Verificar erro apropriado
        3. Adicionar saldo
        4. Aceitar com sucesso - cria PRÉ-ORDEM
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_rico2@test.com',
                nome='Cliente Com Saldo',
                cpf='77777777777',
                phone='11999990007',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_pobre@test.com',
                nome='Prestador Sem Saldo',
                cpf='88888888888',
                phone='11999990008',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            # Cliente com saldo, prestador sem saldo
            WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('5.00'), 'Crédito inicial', 'credito')
            
            # Criar convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço Normal',
                service_description='Prestador precisa de saldo para taxa',
                service_category='geral',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Cliente aceita primeiro
            InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            # Passo 1 e 2: Prestador tenta aceitar sem saldo para taxa
            from services.exceptions import InsufficientBalanceError
            with pytest.raises(InsufficientBalanceError) as exc_info:
                InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            assert 'Saldo insuficiente' in str(exc_info.value)
            assert 'taxa de contestação' in str(exc_info.value)
            
            # Verificar que convite não foi alterado
            db_session.refresh(convite)
            assert convite.provider_accepted is False
            assert convite.status == 'pendente'
            
            # Passo 3: Adicionar saldo
            WalletService.credit_wallet(prestador.id, Decimal('20.00'), 'Adição de saldo', 'credito')
            
            # Passo 4: Aceitar com sucesso - cria PRÉ-ORDEM
            resultado = InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            assert resultado['success'] is True
            assert resultado['pre_order_created'] is True
            
            db_session.refresh(convite)
            assert convite.provider_accepted is True
            assert convite.status == 'convertido_pre_ordem'


class TestFluxoRollback:
    """Testes do fluxo de rollback em caso de erro na criação de pré-ordem"""
    
    def test_rollback_falha_criacao_pre_ordem(self, app, db_session):
        """
        Testa rollback quando criação da pré-ordem falha
        
        Fluxo ATUALIZADO:
        1. Simular falha na criação da pré-ordem
        2. Verificar que convite permanece aceito
        3. Verificar que nenhum valor foi bloqueado (pré-ordem não bloqueia)
        4. Verificar possibilidade de retry
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_rollback@test.com',
                nome='Cliente Rollback',
                cpf='99999999999',
                phone='11999990009',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_rollback@test.com',
                nome='Prestador Rollback',
                cpf='10101010101',
                phone='11999990010',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('500.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('50.00'), 'Crédito inicial', 'credito')
            
            # Criar convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço com Falha',
                service_description='Teste de rollback',
                service_category='geral',
                original_value=Decimal('250.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Prestador aceita primeiro
            InviteService.accept_invite_as_provider(convite.id, prestador.id)
            
            # Passo 1: Simular falha na criação da pré-ordem
            with patch('services.pre_order_service.PreOrderService.create_from_invite') as mock_create:
                mock_create.side_effect = Exception('Erro ao criar pré-ordem no banco de dados')
                
                # Tentar aceitar pelo cliente (deve retornar erro, não exceção)
                resultado = InviteService.accept_invite_as_client(convite.id, cliente.id)
                
                assert resultado['success'] is False
                assert 'Erro ao criar pré-ordem' in resultado.get('error', '')
            
            # Passo 2: Verificar que convite foi marcado como aceito pelo cliente
            db_session.refresh(convite)
            assert convite.client_accepted is True  # Cliente aceitou antes do erro
            assert convite.provider_accepted is True
            assert convite.status == 'pendente'  # Não convertido devido ao erro
            
            # Passo 3: Verificar que nenhum valor foi bloqueado
            carteira_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            carteira_prestador = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert carteira_cliente.escrow_balance == Decimal('0.00')
            assert carteira_prestador.escrow_balance == Decimal('0.00')
            assert carteira_cliente.balance == Decimal('500.00')
            assert carteira_prestador.balance == Decimal('50.00')
    
    def test_rollback_falha_criacao_pre_ordem_prestador(self, app, db_session):
        """
        Testa rollback quando criação da pré-ordem falha (prestador aceita por último)
        
        Fluxo:
        1. Cliente aceita primeiro
        2. Prestador aceita e falha na criação da pré-ordem
        3. Verificar que convite permanece aceito
        4. Verificar que nenhum valor foi bloqueado
        """
        with app.app_context():
            # Setup
            cliente = User(
                email='cliente_rollback2@test.com',
                nome='Cliente Rollback 2',
                cpf='11111111112',
                phone='11999990011',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador_rollback2@test.com',
                nome='Prestador Rollback 2',
                cpf='22222222223',
                phone='11999990012',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db_session.add_all([cliente, prestador])
            db_session.commit()
            
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            WalletService.credit_wallet(cliente.id, Decimal('400.00'), 'Crédito inicial', 'credito')
            WalletService.credit_wallet(prestador.id, Decimal('40.00'), 'Crédito inicial', 'credito')
            
            # Criar convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Serviço com Falha 2',
                service_description='Teste de rollback na criação',
                service_category='geral',
                original_value=Decimal('180.00'),
                delivery_date=datetime.utcnow() + timedelta(days=5),
                status='pendente',
                client_accepted=False,
                provider_accepted=False
            )
            db_session.add(convite)
            db_session.commit()
            
            # Cliente aceita primeiro
            InviteService.accept_invite_as_client(convite.id, cliente.id)
            
            # Passo 1: Simular falha na criação da pré-ordem
            with patch('services.pre_order_service.PreOrderService.create_from_invite') as mock_create:
                mock_create.side_effect = Exception('Erro ao criar pré-ordem no banco de dados')
                
                # Tentar aceitar pelo prestador (deve retornar erro)
                resultado = InviteService.accept_invite_as_provider(convite.id, prestador.id)
                
                assert resultado['success'] is False
                assert 'Erro ao criar pré-ordem' in resultado.get('error', '')
            
            # Passo 2: Verificar que convite permanece aceito por ambos
            db_session.refresh(convite)
            assert convite.client_accepted is True
            assert convite.provider_accepted is True  # Prestador aceitou antes do erro
            assert convite.status == 'pendente'  # Não convertido
            
            # Passo 3: Verificar que nenhum valor foi bloqueado
            carteira_cliente = Wallet.query.filter_by(user_id=cliente.id).first()
            carteira_prestador = Wallet.query.filter_by(user_id=prestador.id).first()
            
            assert carteira_cliente.escrow_balance == Decimal('0.00')
            assert carteira_prestador.escrow_balance == Decimal('0.00')
