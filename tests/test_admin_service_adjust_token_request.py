#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes Unitários para AdminService.adjust_token_request_amount()
"""

import pytest
from decimal import Decimal
from datetime import datetime
from models import User, AdminUser, TokenRequest, db
from services.admin_service import AdminService


class TestAdjustTokenRequestAmount:
    """Testes para o método adjust_token_request_amount do AdminService"""
    
    @pytest.fixture
    def test_token_request(self, db_session, test_user):
        """Cria uma solicitação de token pendente para testes"""
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação de teste',
            status='pending',
            admin_notes=None
        )
        db_session.add(token_request)
        db_session.commit()
        return token_request
    
    def test_adjust_token_request_amount_success(self, db_session, test_admin, test_token_request):
        """Testa ajuste válido de quantidade"""
        # Arrange
        request_id = test_token_request.id
        old_amount = test_token_request.amount
        new_amount = Decimal('50.00')
        admin_id = test_admin.id
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=new_amount,
            admin_id=admin_id
        )
        
        # Assert
        assert result['success'] is True
        assert result['message'] == 'Quantidade ajustada com sucesso'
        assert result['old_amount'] == float(old_amount)
        assert result['new_amount'] == float(new_amount)
        assert result['request_id'] == request_id
        
        # Verificar que o amount foi atualizado no banco
        db_session.refresh(test_token_request)
        assert test_token_request.amount == new_amount
        
        # Verificar que admin_notes contém o registro do ajuste
        assert test_token_request.admin_notes is not None
        assert '[AJUSTE]' in test_token_request.admin_notes
        assert 'R$ 100.00' in test_token_request.admin_notes
        assert 'R$ 50.00' in test_token_request.admin_notes
        assert f'Admin #{admin_id}' in test_token_request.admin_notes
    
    def test_adjust_token_request_amount_invalid_status(self, db_session, test_admin, test_user):
        """Testa tentativa de ajustar solicitação aprovada/rejeitada"""
        # Arrange - Criar solicitação aprovada
        approved_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação aprovada',
            status='approved',
            processed_at=datetime.utcnow(),
            processed_by=test_admin.id
        )
        db_session.add(approved_request)
        db_session.commit()
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=approved_request.id,
            new_amount=Decimal('50.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'Apenas solicitações pendentes podem ser ajustadas'
        
        # Verificar que o amount não foi alterado
        db_session.refresh(approved_request)
        assert approved_request.amount == Decimal('100.00')
    
    def test_adjust_token_request_amount_invalid_value(self, db_session, test_admin, test_token_request):
        """Testa tentativa de ajustar com valor <= 0"""
        # Arrange
        request_id = test_token_request.id
        original_amount = test_token_request.amount
        
        # Act - Testar com valor zero
        result_zero = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('0.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result_zero['success'] is False
        assert result_zero['error'] == 'O novo valor deve ser maior que zero'
        
        # Act - Testar com valor negativo
        result_negative = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('-10.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result_negative['success'] is False
        assert result_negative['error'] == 'O novo valor deve ser maior que zero'
        
        # Verificar que o amount não foi alterado
        db_session.refresh(test_token_request)
        assert test_token_request.amount == original_amount
    
    def test_adjust_token_request_amount_same_value(self, db_session, test_admin, test_token_request):
        """Testa tentativa de ajustar com valor igual ao atual"""
        # Arrange
        request_id = test_token_request.id
        current_amount = test_token_request.amount
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=current_amount,
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'O novo valor deve ser diferente do valor atual'
        
        # Verificar que admin_notes não foi modificado
        db_session.refresh(test_token_request)
        assert test_token_request.admin_notes is None
    
    def test_adjust_token_request_amount_with_reason(self, db_session, test_admin, test_token_request):
        """Testa ajuste com justificativa"""
        # Arrange
        request_id = test_token_request.id
        new_amount = Decimal('75.00')
        admin_id = test_admin.id
        reason = 'Comprovante mostra pagamento de apenas R$ 75,00'
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=new_amount,
            admin_id=admin_id,
            reason=reason
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que a justificativa foi incluída nas admin_notes
        db_session.refresh(test_token_request)
        assert test_token_request.admin_notes is not None
        assert 'Justificativa:' in test_token_request.admin_notes
        assert reason in test_token_request.admin_notes
    
    def test_adjust_token_request_amount_preserves_notes(self, db_session, test_admin, test_user):
        """Testa que ajustar solicitação preserva notas anteriores"""
        # Arrange - Criar solicitação com notas existentes
        existing_notes = 'Nota administrativa anterior'
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação com notas',
            status='pending',
            admin_notes=existing_notes
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=token_request.id,
            new_amount=Decimal('60.00'),
            admin_id=test_admin.id,
            reason='Ajuste necessário'
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que as notas anteriores foram preservadas
        db_session.refresh(token_request)
        assert existing_notes in token_request.admin_notes
        assert '[AJUSTE]' in token_request.admin_notes
        
        # Verificar que a nova nota vem antes da nota antiga
        notes_parts = token_request.admin_notes.split('\n\n')
        assert len(notes_parts) >= 2
        assert '[AJUSTE]' in notes_parts[0]
        assert existing_notes in notes_parts[-1]
    
    def test_adjust_token_request_amount_not_found(self, db_session, test_admin):
        """Testa tentativa de ajustar solicitação inexistente"""
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=99999,  # ID que não existe
            new_amount=Decimal('50.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'Solicitação não encontrada'
    
    def test_adjust_token_request_amount_admin_not_found(self, db_session, test_token_request):
        """Testa tentativa de ajustar com admin inexistente"""
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=test_token_request.id,
            new_amount=Decimal('50.00'),
            admin_id=99999  # ID de admin que não existe
        )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'Administrador não encontrado'
    
    def test_adjust_token_request_amount_with_float(self, db_session, test_admin, test_token_request):
        """Testa ajuste com valor float (deve converter para Decimal)"""
        # Arrange
        request_id = test_token_request.id
        new_amount_float = 45.50
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=new_amount_float,
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is True
        assert result['new_amount'] == new_amount_float
        
        # Verificar que foi convertido corretamente para Decimal no banco
        db_session.refresh(test_token_request)
        assert test_token_request.amount == Decimal('45.50')
    
    def test_adjust_token_request_amount_reason_truncation(self, db_session, test_admin, test_token_request):
        """Testa que justificativa longa é truncada em 500 caracteres"""
        # Arrange
        request_id = test_token_request.id
        long_reason = 'A' * 600  # 600 caracteres
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('80.00'),
            admin_id=test_admin.id,
            reason=long_reason
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que a justificativa foi truncada
        db_session.refresh(test_token_request)
        assert 'Justificativa:' in test_token_request.admin_notes
        
        # Extrair a justificativa das notas
        notes_lines = test_token_request.admin_notes.split('\n')
        justification_line = [line for line in notes_lines if 'Justificativa:' in line][0]
        justification_text = justification_line.replace('Justificativa: ', '')
        
        # Verificar que tem no máximo 500 caracteres
        assert len(justification_text) <= 500
    
    def test_adjust_token_request_amount_rejected_status(self, db_session, test_admin, test_user):
        """Testa que solicitação rejeitada não pode ser ajustada"""
        # Arrange - Criar solicitação rejeitada
        rejected_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação rejeitada',
            status='rejected',
            processed_at=datetime.utcnow(),
            processed_by=test_admin.id
        )
        db_session.add(rejected_request)
        db_session.commit()
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=rejected_request.id,
            new_amount=Decimal('50.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is False
        assert result['error'] == 'Apenas solicitações pendentes podem ser ajustadas'
    
    def test_adjust_token_request_amount_maintains_pending_status(self, db_session, test_admin, test_token_request):
        """Testa que o ajuste mantém o status como 'pending'"""
        # Arrange
        request_id = test_token_request.id
        
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=request_id,
            new_amount=Decimal('55.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que o status continua 'pending'
        db_session.refresh(test_token_request)
        assert test_token_request.status == 'pending'
    
    def test_adjust_token_request_amount_includes_timestamp(self, db_session, test_admin, test_token_request):
        """Testa que o ajuste inclui timestamp nas notas"""
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=test_token_request.id,
            new_amount=Decimal('65.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que há timestamp nas notas
        db_session.refresh(test_token_request)
        assert test_token_request.admin_notes is not None
        
        # Verificar formato de data (dd/mm/yyyy hh:mm)
        import re
        date_pattern = r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}'
        assert re.search(date_pattern, test_token_request.admin_notes) is not None
    
    def test_adjust_token_request_amount_includes_admin_email(self, db_session, test_admin, test_token_request):
        """Testa que o ajuste inclui email do admin nas notas"""
        # Act
        result = AdminService.adjust_token_request_amount(
            request_id=test_token_request.id,
            new_amount=Decimal('70.00'),
            admin_id=test_admin.id
        )
        
        # Assert
        assert result['success'] is True
        
        # Verificar que o email do admin está nas notas
        db_session.refresh(test_token_request)
        assert test_token_request.admin_notes is not None
        assert test_admin.email in test_token_request.admin_notes
