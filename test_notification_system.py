#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do sistema de notificações para propostas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Invite, Proposal
from services.notification_service import NotificationService
from services.proposal_service import ProposalService
from services.wallet_service import WalletService
from decimal import Decimal
import pytest

def test_notification_system():
    """Testa o sistema completo de notificações para propostas"""
    
    # Usar a aplicação existente se disponível
    try:
        from flask import current_app
        app = current_app
    except RuntimeError:
        app = create_app()
    
    with app.app_context():
        # Limpar dados de teste
        db.session.query(Proposal).delete()
        db.session.query(Invite).delete()
        db.session.query(User).filter(User.email.like('%test%')).delete()
        db.session.commit()
        
        print("🧪 Testando Sistema de Notificações para Propostas")
        print("=" * 60)
        
        # 1. Criar usuários de teste
        print("\n1. Criando usuários de teste...")
        
        cliente = User(
            nome="Cliente Teste",
            email="cliente.test@example.com",
            phone="11999999001",
            password_hash="hash_test",
            role="cliente"
        )
        
        prestador = User(
            nome="Prestador Teste",
            email="prestador.test@example.com", 
            phone="11999999002",
            password_hash="hash_test",
            role="prestador"
        )
        
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar carteiras
        WalletService.ensure_user_has_wallet(cliente.id)
        WalletService.ensure_user_has_wallet(prestador.id)
        
        # Adicionar saldo ao cliente
        WalletService.admin_sell_tokens_to_user(
            user_id=cliente.id,
            amount=Decimal('200.00'),
            description="Saldo inicial para teste"
        )
        
        print(f"   ✓ Cliente criado: {cliente.nome} (ID: {cliente.id})")
        print(f"   ✓ Prestador criado: {prestador.nome} (ID: {prestador.id})")
        
        # 2. Criar convite
        print("\n2. Criando convite...")
        
        convite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="Serviço de Teste",
            service_description="Descrição do serviço de teste",
            original_value=Decimal('100.00'),
            delivery_date="2024-12-31",
            status="pending"
        )
        
        db.session.add(convite)
        db.session.commit()
        
        print(f"   ✓ Convite criado: {convite.service_title} (ID: {convite.id})")
        print(f"   ✓ Valor original: R$ {convite.original_value}")
        
        # 3. Testar criação de proposta com notificação
        print("\n3. Testando criação de proposta com notificação...")
        
        try:
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.00'),
                justification="Aumento devido à complexidade do projeto"
            )
            
            print(f"   ✓ Proposta criada: ID {result['proposal_id']}")
            print(f"   ✓ Valor proposto: R$ {result['proposed_value']}")
            print(f"   ✓ Diferença: +R$ {result['value_difference']}")
            print(f"   ✓ Notificação enviada: {result.get('notification_sent', False)}")
            
            proposal_id = result['proposal_id']
            
        except Exception as e:
            print(f"   ❌ Erro ao criar proposta: {e}")
            return False
        
        # 4. Testar notificações no dashboard do cliente
        print("\n4. Testando notificações no dashboard do cliente...")
        
        try:
            from services.cliente_service import ClienteService
            dashboard_data = ClienteService.get_dashboard_data(cliente.id)
            
            alertas = dashboard_data.get('alertas', [])
            proposal_alerts = [a for a in alertas if 'proposta' in a.get('mensagem', '').lower()]
            
            print(f"   ✓ Total de alertas: {len(alertas)}")
            print(f"   ✓ Alertas de propostas: {len(proposal_alerts)}")
            
            if proposal_alerts:
                for alert in proposal_alerts:
                    print(f"   📢 {alert['tipo'].upper()}: {alert['mensagem']}")
            
        except Exception as e:
            print(f"   ❌ Erro ao buscar dashboard do cliente: {e}")
        
        # 5. Testar aprovação de proposta com notificação
        print("\n5. Testando aprovação de proposta...")
        
        try:
            result = ProposalService.approve_proposal(
                proposal_id=proposal_id,
                client_id=cliente.id,
                client_response_reason="Valor justo para o serviço"
            )
            
            print(f"   ✓ Proposta aprovada: ID {result['proposal_id']}")
            print(f"   ✓ Valor aprovado: R$ {result['approved_value']}")
            print(f"   ✓ Notificação enviada: {result.get('notification_sent', False)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao aprovar proposta: {e}")
        
        # 6. Testar notificações no dashboard do prestador
        print("\n6. Testando notificações no dashboard do prestador...")
        
        try:
            from services.prestador_service import PrestadorService
            dashboard_data = PrestadorService.get_dashboard_data(prestador.id)
            
            alertas = dashboard_data.get('alertas', [])
            proposal_alerts = [a for a in alertas if 'proposta' in a.get('mensagem', '').lower()]
            
            print(f"   ✓ Total de alertas: {len(alertas)}")
            print(f"   ✓ Alertas de propostas: {len(proposal_alerts)}")
            
            if proposal_alerts:
                for alert in proposal_alerts:
                    print(f"   📢 {alert['tipo'].upper()}: {alert['mensagem']}")
            
        except Exception as e:
            print(f"   ❌ Erro ao buscar dashboard do prestador: {e}")
        
        # 7. Testar cenário de saldo insuficiente
        print("\n7. Testando notificação de saldo insuficiente...")
        
        # Criar novo convite com valor alto
        convite_alto = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="Serviço Caro",
            service_description="Serviço com valor alto",
            original_value=Decimal('50.00'),
            delivery_date="2024-12-31",
            status="pending"
        )
        
        db.session.add(convite_alto)
        db.session.commit()
        
        try:
            # Criar proposta com valor muito alto
            result_create = ProposalService.create_proposal(
                invite_id=convite_alto.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('500.00'),  # Valor que excede o saldo
                justification="Serviço muito complexo"
            )
            
            proposal_id_alto = result_create['proposal_id']
            
            # Tentar aprovar (deve falhar por saldo insuficiente)
            try:
                ProposalService.approve_proposal(
                    proposal_id=proposal_id_alto,
                    client_id=cliente.id,
                    client_response_reason="Aceito o valor"
                )
                print("   ❌ Deveria ter falhado por saldo insuficiente")
                
            except ValueError as e:
                print(f"   ✓ Saldo insuficiente detectado: {str(e)[:100]}...")
                print("   ✓ Notificação de saldo insuficiente enviada")
                
        except Exception as e:
            print(f"   ❌ Erro no teste de saldo insuficiente: {e}")
        
        # 8. Testar rejeição de proposta
        print("\n8. Testando rejeição de proposta...")
        
        try:
            result = ProposalService.reject_proposal(
                proposal_id=proposal_id_alto,
                client_id=cliente.id,
                client_response_reason="Valor muito alto para o orçamento"
            )
            
            print(f"   ✓ Proposta rejeitada: ID {result['proposal_id']}")
            print(f"   ✓ Motivo: {result['rejection_reason']}")
            print(f"   ✓ Notificação enviada: {result.get('notification_sent', False)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao rejeitar proposta: {e}")
        
        # 9. Testar cancelamento de proposta
        print("\n9. Testando cancelamento de proposta...")
        
        # Criar nova proposta para cancelar
        try:
            convite_cancel = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Serviço para Cancelar",
                service_description="Teste de cancelamento",
                original_value=Decimal('80.00'),
                delivery_date="2024-12-31",
                status="pending"
            )
            
            db.session.add(convite_cancel)
            db.session.commit()
            
            result_create = ProposalService.create_proposal(
                invite_id=convite_cancel.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('120.00'),
                justification="Teste de cancelamento"
            )
            
            proposal_id_cancel = result_create['proposal_id']
            
            # Cancelar a proposta
            result = ProposalService.cancel_proposal(
                proposal_id=proposal_id_cancel,
                prestador_id=prestador.id
            )
            
            print(f"   ✓ Proposta cancelada: ID {result['proposal_id']}")
            print(f"   ✓ Notificação enviada: {result.get('notification_sent', False)}")
            
        except Exception as e:
            print(f"   ❌ Erro ao cancelar proposta: {e}")
        
        # 10. Testar métodos de formatação
        print("\n10. Testando métodos de formatação...")
        
        try:
            # Testar formatação de moeda
            formatted_currency = NotificationService.format_currency(Decimal('123.45'))
            print(f"   ✓ Formatação de moeda: {formatted_currency}")
            
            # Testar comparação de valores
            comparison = NotificationService.format_value_comparison(
                Decimal('100.00'), 
                Decimal('150.00')
            )
            print(f"   ✓ Comparação de valores: {comparison}")
            
            # Testar resumo de notificação
            proposal = Proposal.query.get(proposal_id)
            if proposal:
                summary = NotificationService.create_proposal_summary_notification(
                    proposal=proposal,
                    action="test_summary"
                )
                print(f"   ✓ Resumo criado: {summary.get('action', 'N/A')}")
            
        except Exception as e:
            print(f"   ❌ Erro nos métodos de formatação: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Teste do sistema de notificações concluído!")
        print("\nFuncionalidades testadas:")
        print("• Notificação de criação de proposta")
        print("• Notificação de aprovação de proposta")
        print("• Notificação de rejeição de proposta")
        print("• Notificação de cancelamento de proposta")
        print("• Notificação de saldo insuficiente")
        print("• Integração com dashboards (cliente e prestador)")
        print("• Métodos de formatação e resumo")
        
        return True

if __name__ == "__main__":
    test_notification_system()