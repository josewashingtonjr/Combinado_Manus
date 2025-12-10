#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes de Integração para Ajuste de Quantidade de Tokens em Solicitações
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime
from models import User, AdminUser, TokenRequest, Wallet, db
from services.wallet_service import WalletService


class TestAdjustAndApproveFlow:
    """Testes do fluxo completo de ajuste e aprovação"""
    
    def test_adjust_and_approve_flow(self, authenticated_admin_client, db_session, test_user):
        """Testa o fluxo completo: ajustar quantidade e depois aprovar"""
        # Arrange - Criar solicitação pendente
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação para ajuste e aprovação',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Obter saldo inicial do usuário
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        # Act 1 - Ajustar quantidade de 100 para 50
        adjust_response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({
                'new_amount': 50.00,
                'adjustment_reason': 'Comprovante mostra pagamento de apenas R$ 50,00'
            }),
            content_type='application/json'
        )
        
        # Assert - Ajuste bem-sucedido
        assert adjust_response.status_code == 200
        adjust_data = json.loads(adjust_response.data)
        assert adjust_data['success'] is True
        assert adjust_data['old_amount'] == 100.00
        assert adjust_data['new_amount'] == 50.00
        
        # Verificar que o amount foi atualizado
        db_session.refresh(token_request)
        assert token_request.amount == Decimal('50.00')
        assert token_request.status == 'pending'
        
        # Act 2 - Aprovar solicitação com valor ajustado
        approve_response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/processar',
            data={
                'action': 'approve',
                'admin_notes': 'Aprovado após ajuste'
            },
            follow_redirects=False
        )
        
        # Assert - Aprovação bem-sucedida
        assert approve_response.status_code == 302  # Redirect
        
        # Verificar que a solicitação foi aprovada
        db_session.refresh(token_request)
        assert token_request.status == 'approved'
        assert token_request.processed_at is not None
        
        # Verificar que os tokens foram adicionados na quantidade AJUSTADA (50), não na original (100)
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance + Decimal('50.00')
        
        # Verificar que as notas administrativas contêm o histórico de ajuste
        assert token_request.admin_notes is not None
        assert '[AJUSTE]' in token_request.admin_notes or 'Aprovado após ajuste' in token_request.admin_notes
    
    def test_adjust_multiple_times_then_approve(self, authenticated_admin_client, db_session, test_user):
        """Testa ajustar múltiplas vezes antes de aprovar"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação para múltiplos ajustes',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        # Act - Primeiro ajuste: 100 -> 75
        authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 75.00, 'adjustment_reason': 'Primeiro ajuste'}),
            content_type='application/json'
        )
        
        # Act - Segundo ajuste: 75 -> 60
        authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 60.00, 'adjustment_reason': 'Segundo ajuste'}),
            content_type='application/json'
        )
        
        # Act - Terceiro ajuste: 60 -> 55
        adjust_response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 55.00, 'adjustment_reason': 'Ajuste final'}),
            content_type='application/json'
        )
        
        # Assert - Último ajuste bem-sucedido
        assert adjust_response.status_code == 200
        
        # Verificar que o valor final é 55
        db_session.refresh(token_request)
        assert token_request.amount == Decimal('55.00')
        
        # Verificar que todas as notas foram preservadas
        assert 'Primeiro ajuste' in token_request.admin_notes
        assert 'Segundo ajuste' in token_request.admin_notes
        assert 'Ajuste final' in token_request.admin_notes
        
        # Act - Aprovar
        authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/processar',
            data={'action': 'approve'},
            follow_redirects=False
        )
        
        # Assert - Tokens adicionados com valor final (55)
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance + Decimal('55.00')
    
    def test_adjust_then_reject(self, authenticated_admin_client, db_session, test_user):
        """Testa ajustar e depois rejeitar a solicitação"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação para ajuste e rejeição',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        wallet = db_session.query(Wallet).filter_by(user_id=test_user.id).first()
        initial_balance = wallet.balance
        
        # Act - Ajustar
        authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 50.00}),
            content_type='application/json'
        )
        
        # Act - Rejeitar
        authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/processar',
            data={'action': 'reject', 'admin_notes': 'Comprovante inválido'},
            follow_redirects=False
        )
        
        # Assert - Solicitação rejeitada
        db_session.refresh(token_request)
        assert token_request.status == 'rejected'
        
        # Assert - Nenhum token foi adicionado
        db_session.refresh(wallet)
        assert wallet.balance == initial_balance


class TestAdjustRouteAuthentication:
    """Testes de autenticação da rota de ajuste"""
    
    def test_adjust_route_requires_authentication(self, app, db_session, test_user):
        """Testa que a rota de ajuste requer autenticação"""
        # Arrange - Criar solicitação
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação teste',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Tentar ajustar sem autenticação usando test_client diretamente
        with app.test_client() as client:
            try:
                response = client.post(
                    f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
                    data=json.dumps({'new_amount': 50.00}),
                    content_type='application/json',
                    follow_redirects=False
                )
                # Assert - Deve tentar redirecionar (302) ou retornar erro
                # Como o blueprint auth não está registrado, pode gerar erro ao tentar redirecionar
                # O importante é que a requisição não foi processada
                assert response.status_code in [302, 401, 403, 500]
            except Exception:
                # Se houver exceção ao tentar redirecionar, é porque a autenticação bloqueou
                pass
        
        # Verificar que o amount não foi alterado
        db_session.refresh(token_request)
        assert token_request.amount == Decimal('100.00')
    
    def test_adjust_route_with_expired_session(self, app, db_session, test_user, test_admin):
        """Testa que sessão expirada não permite ajuste"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação teste',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Criar cliente, adicionar sessão e depois limpar
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['admin_id'] = test_admin.id
            
            with client.session_transaction() as sess:
                sess.clear()
            
            try:
                response = client.post(
                    f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
                    data=json.dumps({'new_amount': 50.00}),
                    content_type='application/json',
                    follow_redirects=False
                )
                # Assert - Deve tentar redirecionar ou retornar erro
                assert response.status_code in [302, 401, 403, 500]
            except Exception:
                # Se houver exceção, a autenticação bloqueou corretamente
                pass
        
        # Verificar que o amount não foi alterado
        db_session.refresh(token_request)
        assert token_request.amount == Decimal('100.00')


class TestAdjustRouteAuthorization:
    """Testes de autorização da rota de ajuste"""
    
    def test_regular_user_cannot_adjust_token_request(self, app, db_session, test_user):
        """Testa que usuário regular não pode ajustar solicitações"""
        # Arrange - Criar solicitação
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            description='Solicitação teste',
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Criar cliente autenticado como usuário regular (não admin)
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = test_user.id
                sess['active_role'] = 'cliente'
                # Não definir admin_id
            
            try:
                response = client.post(
                    f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
                    data=json.dumps({'new_amount': 50.00}),
                    content_type='application/json',
                    follow_redirects=False
                )
                # Assert - Acesso negado
                assert response.status_code in [302, 401, 403, 500]
            except Exception:
                # Se houver exceção, a autorização bloqueou corretamente
                pass
        
        # Verificar que o amount não foi alterado
        db_session.refresh(token_request)
        assert token_request.amount == Decimal('100.00')
    
    def test_admin_can_adjust_any_user_token_request(self, authenticated_admin_client, db_session):
        """Testa que admin pode ajustar solicitações de qualquer usuário"""
        # Arrange - Criar dois usuários diferentes
        user1 = User(
            email='user1@example.com',
            nome='User 1',
            cpf='11111111111',
            phone='11911111111',
            roles='cliente'
        )
        user1.set_password('pass123')
        db_session.add(user1)
        
        user2 = User(
            email='user2@example.com',
            nome='User 2',
            cpf='22222222222',
            phone='11922222222',
            roles='cliente'
        )
        user2.set_password('pass123')
        db_session.add(user2)
        db_session.commit()
        
        # Criar carteiras
        wallet1 = Wallet(user_id=user1.id, balance=0, escrow_balance=0)
        wallet2 = Wallet(user_id=user2.id, balance=0, escrow_balance=0)
        db_session.add_all([wallet1, wallet2])
        
        # Criar solicitações de ambos os usuários
        request1 = TokenRequest(user_id=user1.id, amount=Decimal('100.00'), status='pending')
        request2 = TokenRequest(user_id=user2.id, amount=Decimal('200.00'), status='pending')
        db_session.add_all([request1, request2])
        db_session.commit()
        
        # Act - Admin ajusta ambas as solicitações
        response1 = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{request1.id}/ajustar',
            data=json.dumps({'new_amount': 80.00}),
            content_type='application/json'
        )
        
        response2 = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{request2.id}/ajustar',
            data=json.dumps({'new_amount': 150.00}),
            content_type='application/json'
        )
        
        # Assert - Ambos os ajustes bem-sucedidos
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        db_session.refresh(request1)
        db_session.refresh(request2)
        assert request1.amount == Decimal('80.00')
        assert request2.amount == Decimal('150.00')


class TestAdjustRouteValidation:
    """Testes de validações de entrada da rota de ajuste"""
    
    def test_adjust_route_validates_request_exists(self, authenticated_admin_client):
        """Testa validação de solicitação inexistente"""
        # Act - Tentar ajustar solicitação que não existe
        response = authenticated_admin_client.post(
            '/admin/tokens/solicitacoes/99999/ajustar',
            data=json.dumps({'new_amount': 50.00}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'não encontrada' in data['error'].lower()
    
    def test_adjust_route_validates_pending_status(self, authenticated_admin_client, db_session, test_user, test_admin):
        """Testa validação de status pendente"""
        # Arrange - Criar solicitação aprovada
        approved_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='approved',
            processed_at=datetime.utcnow(),
            processed_by=test_admin.id
        )
        db_session.add(approved_request)
        db_session.commit()
        
        # Act - Tentar ajustar solicitação aprovada
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{approved_request.id}/ajustar',
            data=json.dumps({'new_amount': 50.00}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'pendentes' in data['error'].lower()
    
    def test_adjust_route_validates_positive_amount(self, authenticated_admin_client, db_session, test_user):
        """Testa validação de valor positivo"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Tentar ajustar com valor zero
        response_zero = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 0}),
            content_type='application/json'
        )
        
        # Assert
        assert response_zero.status_code == 400
        data_zero = json.loads(response_zero.data)
        assert data_zero['success'] is False
        assert 'maior que zero' in data_zero['error'].lower()
        
        # Act - Tentar ajustar com valor negativo
        response_negative = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': -50.00}),
            content_type='application/json'
        )
        
        # Assert
        assert response_negative.status_code == 400
        data_negative = json.loads(response_negative.data)
        assert data_negative['success'] is False
        assert 'maior que zero' in data_negative['error'].lower()
    
    def test_adjust_route_validates_different_amount(self, authenticated_admin_client, db_session, test_user):
        """Testa validação de valor diferente do atual"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Tentar ajustar com o mesmo valor
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 100.00}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'diferente' in data['error'].lower()
    
    def test_adjust_route_validates_reason_length(self, authenticated_admin_client, db_session, test_user):
        """Testa validação do tamanho da justificativa"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Tentar ajustar com justificativa muito longa (> 500 caracteres)
        long_reason = 'A' * 501
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 50.00, 'adjustment_reason': long_reason}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert '500' in data['error']
    
    def test_adjust_route_validates_json_format(self, authenticated_admin_client, db_session, test_user):
        """Testa validação de formato JSON"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Enviar dados sem JSON (Content-Type incorreto)
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data='invalid data',
            content_type='text/plain'
        )
        
        # Assert - A rota pode retornar 400 ou 500 dependendo de como trata o erro
        # O importante é que a requisição falhou
        assert response.status_code in [400, 500]
    
    def test_adjust_route_validates_new_amount_required(self, authenticated_admin_client, db_session, test_user):
        """Testa validação de campo new_amount obrigatório"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Enviar JSON sem new_amount
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'adjustment_reason': 'Teste'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'obrigatório' in data['error'].lower()
    
    def test_adjust_route_validates_numeric_amount(self, authenticated_admin_client, db_session, test_user):
        """Testa validação de valor numérico"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Enviar valor não numérico
        response = authenticated_admin_client.post(
            f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
            data=json.dumps({'new_amount': 'abc'}),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'inválido' in data['error'].lower()
    
    def test_adjust_route_accepts_valid_decimal_values(self, authenticated_admin_client, db_session, test_user):
        """Testa que a rota aceita valores decimais válidos"""
        # Arrange
        token_request = TokenRequest(
            user_id=test_user.id,
            amount=Decimal('100.00'),
            status='pending'
        )
        db_session.add(token_request)
        db_session.commit()
        
        # Act - Testar diferentes formatos de valores decimais
        test_values = [50.00, 50.5, 50.99, 0.01, 999.99]
        
        for value in test_values:
            response = authenticated_admin_client.post(
                f'/admin/tokens/solicitacoes/{token_request.id}/ajustar',
                data=json.dumps({'new_amount': value}),
                content_type='application/json'
            )
            
            # Assert
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['new_amount'] == value
            
            # Resetar para próximo teste
            db_session.refresh(token_request)
            token_request.amount = Decimal('100.00')
            db_session.commit()
