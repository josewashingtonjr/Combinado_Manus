#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes unitários para componentes do sistema de propostas de alteração de convites

Este arquivo testa:
- ProposalService com diferentes cenários
- BalanceValidator com vários casos de saldo
- Transições de estado do convite (InviteStateManager)
- Validações de autorização

Requirements: 1.1, 3.1, 5.1, 2.1
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models import db, User, Invite, Proposal, Wallet
from services.proposal_service import ProposalService, BalanceCheck
from services.balance_validator import BalanceValidator, BalanceStatus
from services.invite_state_manager import InviteStateManager, InviteState


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def cliente(db_session):
    """Cria um cliente de teste"""
    user = User(
        email='cliente@test.com',
        nome='Cliente Teste',
        cpf='11111111111',
        phone='11999999999',
        roles='cliente'
    )
    user.set_password('senha123')
    db_session.add(user)
    db_session.commit()
    
    # Criar carteira com saldo
    wallet = Wallet(user_id=user.id, balance=Decimal('100.00'), escrow_balance=Decimal('0.00'))
    db_session.add(wallet)
    db_session.commit()
    
    return user


@pytest.fixture
def prestador(db_session):
    """Cria um prestador de teste"""
    user = User(
        email='prestador@test.com',
        nome='Prestador Teste',
        cpf='22222222222',
        phone='11988888888',
        roles='prestador'
    )
    user.set_password('senha123')
    db_session.add(user)
    db_session.commit()
    
    # Criar carteira
    wallet = Wallet(user_id=user.id, balance=Decimal('50.00'), escrow_balance=Decimal('0.00'))
    db_session.add(wallet)
    db_session.commit()
    
    return user


@pytest.fixture
def convite_pendente(db_session, cliente, prestador):
    """Cria um convite pendente de teste"""
    invite = Invite(
        client_id=cliente.id,
        invited_phone=prestador.phone,
        service_title='Serviço de Teste',
        service_description='Descrição do serviço',
        service_category='teste',
        original_value=Decimal('50.00'),
        delivery_date=datetime.utcnow() + timedelta(days=7),
        expires_at=datetime.utcnow() + timedelta(days=7),
        status='pendente'
    )
    db_session.add(invite)
    db_session.commit()
    
    return invite


# ==============================================================================
# TESTES DO PROPOSALSERVICE
# ==============================================================================

class TestProposalService:
    """Testes do ProposalService com diferentes cenários"""
    
    def test_criar_proposta_sucesso(self, db_session, convite_pendente, prestador):
        """Testa criação de proposta com dados válidos"""
        # Arrange
        valor_proposto = Decimal('70.00')
        justificativa = 'Materiais mais caros'
        
        # Act
        resultado = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=valor_proposto,
            justification=justificativa
        )
        
        # Assert
        assert resultado['success'] is True
        assert resultado['proposed_value'] == float(valor_proposto)
        assert resultado['original_value'] == float(convite_pendente.original_value)
        assert resultado['is_increase'] is True
        
        # Verificar que proposta foi criada no banco
        proposta = Proposal.query.get(resultado['proposal_id'])
        assert proposta is not None
        assert proposta.status == 'pending'
        assert proposta.proposed_value == valor_proposto
    
    def test_criar_proposta_valor_menor(self, db_session, convite_pendente, prestador):
        """Testa criação de proposta com valor menor que o original"""
        # Arrange
        valor_proposto = Decimal('30.00')
        
        # Act
        resultado = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=valor_proposto,
            justification='Consegui desconto nos materiais'
        )
        
        # Assert
        assert resultado['success'] is True
        assert resultado['is_increase'] is False
        assert resultado['value_difference'] < 0
    
    def test_aprovar_proposta_com_saldo_suficiente(self, db_session, convite_pendente, prestador, cliente):
        """Testa aprovação de proposta quando cliente tem saldo suficiente"""
        # Arrange - Criar proposta
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        proposta_id = proposta_result['proposal_id']
        
        # Act - Aprovar proposta
        resultado = ProposalService.approve_proposal(
            proposal_id=proposta_id,
            client_id=cliente.id,
            client_response_reason='Aprovado'
        )
        
        # Assert
        assert resultado['success'] is True
        assert resultado['status'] == 'accepted'
        
        # Verificar que proposta foi aceita
        proposta = Proposal.query.get(proposta_id)
        assert proposta.status == 'accepted'
        assert proposta.responded_at is not None
    
    def test_rejeitar_proposta(self, db_session, convite_pendente, prestador, cliente):
        """Testa rejeição de proposta pelo cliente"""
        # Arrange
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('80.00'),
            justification='Teste'
        )
        proposta_id = proposta_result['proposal_id']
        
        # Act
        resultado = ProposalService.reject_proposal(
            proposal_id=proposta_id,
            client_id=cliente.id,
            client_response_reason='Valor muito alto'
        )
        
        # Assert
        assert resultado['success'] is True
        assert resultado['status'] == 'rejected'
        
        proposta = Proposal.query.get(proposta_id)
        assert proposta.status == 'rejected'
        assert proposta.client_response_reason == 'Valor muito alto'
    
    def test_cancelar_proposta_pelo_prestador(self, db_session, convite_pendente, prestador):
        """Testa cancelamento de proposta pelo prestador"""
        # Arrange
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('65.00'),
            justification='Teste'
        )
        proposta_id = proposta_result['proposal_id']
        
        # Act
        resultado = ProposalService.cancel_proposal(
            proposal_id=proposta_id,
            prestador_id=prestador.id
        )
        
        # Assert
        assert resultado['success'] is True
        assert resultado['status'] == 'cancelled'
        
        proposta = Proposal.query.get(proposta_id)
        assert proposta.status == 'cancelled'


# ==============================================================================
# TESTES DO BALANCEVALIDATOR
# ==============================================================================

class TestBalanceValidator:
    """Testes do BalanceValidator com vários casos de saldo"""
    
    def test_calcular_saldo_necessario(self):
        """Testa cálculo do saldo necessário (valor + taxa)"""
        # Arrange
        valor_proposto = Decimal('100.00')
        
        # Act
        saldo_necessario = BalanceValidator.calculate_required_balance(valor_proposto)
        
        # Assert
        taxa_contestacao = BalanceValidator.get_contestation_fee()
        assert saldo_necessario == valor_proposto + taxa_contestacao
    
    def test_verificar_saldo_suficiente(self, db_session, cliente):
        """Testa verificação quando cliente tem saldo suficiente"""
        # Arrange
        valor_necessario = Decimal('50.00')
        
        # Act
        status = BalanceValidator.check_sufficiency(cliente.id, valor_necessario)
        
        # Assert
        assert isinstance(status, BalanceStatus)
        assert status.is_sufficient is True
        assert status.current_balance == Decimal('100.00')
        assert status.shortfall == Decimal('0.00')
    
    def test_verificar_saldo_insuficiente(self, db_session, cliente):
        """Testa verificação quando cliente não tem saldo suficiente"""
        # Arrange
        valor_necessario = Decimal('150.00')
        
        # Act
        status = BalanceValidator.check_sufficiency(cliente.id, valor_necessario)
        
        # Assert
        assert status.is_sufficient is False
        assert status.shortfall == Decimal('50.00')
        assert status.suggested_top_up > status.shortfall
    
    def test_sugerir_valor_recarga(self):
        """Testa sugestão de valor para recarga"""
        # Arrange
        saldo_atual = Decimal('30.00')
        valor_necessario = Decimal('100.00')
        
        # Act
        sugestao = BalanceValidator.suggest_top_up_amount(saldo_atual, valor_necessario)
        
        # Assert
        assert sugestao >= (valor_necessario - saldo_atual)
        assert sugestao % Decimal('10.00') == Decimal('0.00')  # Múltiplo de 10
    
    def test_validar_saldo_para_proposta(self, db_session, cliente):
        """Testa validação completa de saldo para proposta"""
        # Arrange
        valor_proposto = Decimal('80.00')
        
        # Act
        status = BalanceValidator.validate_proposal_balance(cliente.id, valor_proposto)
        
        # Assert
        assert isinstance(status, BalanceStatus)
        assert status.required_amount == BalanceValidator.calculate_required_balance(valor_proposto)


# ==============================================================================
# TESTES DO INVITESTATEMANAGER
# ==============================================================================

class TestInviteStateManager:
    """Testes de transições de estado do convite"""
    
    def test_estado_inicial_pendente(self, db_session, convite_pendente):
        """Testa que convite novo está no estado PENDENTE"""
        # Act
        estado = InviteStateManager.get_current_state(convite_pendente)
        
        # Assert
        assert estado == InviteState.PENDENTE
    
    def test_transicao_para_proposta_enviada(self, db_session, convite_pendente, prestador):
        """Testa transição de PENDENTE para PROPOSTA_ENVIADA"""
        # Arrange
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        
        # Act
        db_session.refresh(convite_pendente)
        estado = InviteStateManager.get_current_state(convite_pendente)
        
        # Assert
        assert estado == InviteState.PROPOSTA_ENVIADA
        assert convite_pendente.has_active_proposal is True
    
    def test_pode_aceitar_convite_pendente(self, db_session, convite_pendente):
        """Testa que convite pendente pode ser aceito"""
        # Act
        pode_aceitar, motivo = InviteStateManager.can_be_accepted(convite_pendente)
        
        # Assert
        assert pode_aceitar is True
    
    def test_nao_pode_aceitar_com_proposta_pendente(self, db_session, convite_pendente, prestador):
        """Testa que convite com proposta pendente não pode ser aceito"""
        # Arrange - Criar proposta
        ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        
        # Act
        db_session.refresh(convite_pendente)
        pode_aceitar, motivo = InviteStateManager.can_be_accepted(convite_pendente)
        
        # Assert
        assert pode_aceitar is False
        assert 'proposta' in motivo.lower()
    
    def test_pode_criar_proposta_em_pendente(self, db_session, convite_pendente):
        """Testa que proposta pode ser criada em convite pendente"""
        # Act
        pode_criar, motivo = InviteStateManager.can_create_proposal(convite_pendente)
        
        # Assert
        assert pode_criar is True
    
    def test_nao_pode_criar_proposta_duplicada(self, db_session, convite_pendente, prestador):
        """Testa que não pode criar proposta quando já existe uma pendente"""
        # Arrange
        ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        
        # Act
        db_session.refresh(convite_pendente)
        pode_criar, motivo = InviteStateManager.can_create_proposal(convite_pendente)
        
        # Assert
        assert pode_criar is False


# ==============================================================================
# TESTES DE VALIDAÇÕES DE AUTORIZAÇÃO
# ==============================================================================

class TestAutorizacaoPropostas:
    """Testes de validações de autorização"""
    
    def test_apenas_prestador_pode_criar_proposta(self, db_session, convite_pendente, cliente):
        """Testa que apenas o prestador pode criar proposta"""
        # Act & Assert
        with pytest.raises(ValueError, match='autorização|permissão'):
            ProposalService.create_proposal(
                invite_id=convite_pendente.id,
                prestador_id=cliente.id,  # Cliente tentando criar proposta
                proposed_value=Decimal('60.00'),
                justification='Teste'
            )
    
    def test_apenas_cliente_pode_aprovar_proposta(self, db_session, convite_pendente, prestador, cliente):
        """Testa que apenas o cliente pode aprovar proposta"""
        # Arrange
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match='autorização|permissão'):
            ProposalService.approve_proposal(
                proposal_id=proposta_result['proposal_id'],
                client_id=prestador.id,  # Prestador tentando aprovar
                client_response_reason='Teste'
            )
    
    def test_apenas_prestador_criador_pode_cancelar(self, db_session, convite_pendente, prestador, cliente):
        """Testa que apenas o prestador criador pode cancelar proposta"""
        # Arrange
        proposta_result = ProposalService.create_proposal(
            invite_id=convite_pendente.id,
            prestador_id=prestador.id,
            proposed_value=Decimal('60.00'),
            justification='Teste'
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match='criador'):
            ProposalService.cancel_proposal(
                proposal_id=proposta_result['proposal_id'],
                prestador_id=cliente.id  # Cliente tentando cancelar
            )
