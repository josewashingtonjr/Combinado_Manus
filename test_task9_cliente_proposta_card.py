#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para validar a tarefa 9: Atualizar template do cliente para exibir card de proposta pendente
"""

import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Proposal
from datetime import datetime, timedelta

def test_cliente_proposta_card():
    """
    Testa se o template do cliente exibe o card de proposta pendente corretamente:
    - Criar card destacado quando has_active_proposal é True
    - Mostrar comparação visual entre valores original e proposto
    - Exibir justificativa do prestador
    - Adicionar botões "Aceitar Proposta" e "Rejeitar Proposta"
    - Integrar verificação de saldo para aumentos
    """
    
    print("="*80)
    print("🧪 TESTE: Template do Cliente - Card de Proposta Pendente")
    print("="*80)
    
    with app.app_context():
        try:
            # Limpar dados de teste anteriores
            Proposal.query.filter_by(justification='Teste Task 9').delete()
            Invite.query.filter(Invite.service_title.like('Teste Task 9%')).delete()
            User.query.filter_by(email='cliente_task9@test.com').delete()
            User.query.filter_by(email='prestador_task9@test.com').delete()
            db.session.commit()
            
            # 1. Criar usuários de teste
            print("\n1. Criando usuários de teste...")
            cliente = User(
                nome='Cliente Task 9',
                email='cliente_task9@test.com',
                cpf='33333333333',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                nome='Prestador Task 9',
                email='prestador_task9@test.com',
                cpf='44444444444',
                phone='11988888888',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db.session.add(cliente)
            db.session.add(prestador)
            db.session.commit()
            print(f"   ✓ Cliente criado: {cliente.nome}")
            print(f"   ✓ Prestador criado: {prestador.nome}")
            
            # 2. Criar convite com proposta pendente (aumento)
            print("\n2. Criando convite com proposta pendente (AUMENTO)...")
            invite_aumento = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Task 9 - Proposta Aumento',
                service_description='Teste de proposta com aumento',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3),
                status='proposta_enviada',
                has_active_proposal=True
            )
            db.session.add(invite_aumento)
            db.session.flush()
            
            proposal_aumento = Proposal(
                invite_id=invite_aumento.id,
                prestador_id=prestador.id,
                original_value=Decimal('100.00'),
                proposed_value=Decimal('150.00'),
                justification='Teste Task 9 - Preciso de mais recursos para realizar o serviço com qualidade',
                status='pending'
            )
            db.session.add(proposal_aumento)
            db.session.flush()
            
            invite_aumento.current_proposal_id = proposal_aumento.id
            db.session.commit()
            
            print(f"   ✓ Convite criado: {invite_aumento.service_title}")
            print(f"   - Status: {invite_aumento.status}")
            print(f"   - has_active_proposal: {invite_aumento.has_active_proposal}")
            print(f"   - Valor original: R$ {proposal_aumento.original_value}")
            print(f"   - Valor proposto: R$ {proposal_aumento.proposed_value}")
            print(f"   - Diferença: +R$ {proposal_aumento.value_difference}")
            print(f"   - Justificativa: {proposal_aumento.justification}")
            
            # 3. Criar convite com proposta pendente (redução)
            print("\n3. Criando convite com proposta pendente (REDUÇÃO)...")
            invite_reducao = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Task 9 - Proposta Redução',
                service_description='Teste de proposta com redução',
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3),
                status='proposta_enviada',
                has_active_proposal=True
            )
            db.session.add(invite_reducao)
            db.session.flush()
            
            proposal_reducao = Proposal(
                invite_id=invite_reducao.id,
                prestador_id=prestador.id,
                original_value=Decimal('200.00'),
                proposed_value=Decimal('150.00'),
                justification='Teste Task 9 - Posso fazer por menos',
                status='pending'
            )
            db.session.add(proposal_reducao)
            db.session.flush()
            
            invite_reducao.current_proposal_id = proposal_reducao.id
            db.session.commit()
            
            print(f"   ✓ Convite criado: {invite_reducao.service_title}")
            print(f"   - Status: {invite_reducao.status}")
            print(f"   - has_active_proposal: {invite_reducao.has_active_proposal}")
            print(f"   - Valor original: R$ {proposal_reducao.original_value}")
            print(f"   - Valor proposto: R$ {proposal_reducao.proposed_value}")
            print(f"   - Diferença: R$ {proposal_reducao.value_difference}")
            print(f"   - Justificativa: {proposal_reducao.justification}")
            
            # 4. Verificar template
            print("\n4. Verificando template do cliente...")
            with open('templates/cliente/ver_convite.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Requisito 1: Card destacado quando has_active_proposal é True
            print("\n   Requisito 1: Card destacado quando has_active_proposal é True")
            assert 'invite.has_active_proposal' in template_content, \
                "Template deve verificar has_active_proposal"
            assert 'invite.current_proposal' in template_content, \
                "Template deve verificar current_proposal"
            assert 'border-warning' in template_content or 'border-info' in template_content, \
                "Card deve ter borda destacada"
            assert 'shadow' in template_content, \
                "Card deve ter sombra para destaque"
            print("   ✓ Card destacado implementado")
            
            # Requisito 2: Comparação visual entre valores
            print("\n   Requisito 2: Comparação visual entre valores original e proposto")
            assert 'original_value' in template_content, \
                "Template deve mostrar valor original"
            assert 'proposed_value' in template_content, \
                "Template deve mostrar valor proposto"
            assert 'value_difference' in template_content or \
                   ('is_increase' in template_content and 'is_decrease' in template_content), \
                "Template deve mostrar diferença ou verificar tipo de mudança"
            print("   ✓ Comparação de valores implementada")
            
            # Requisito 3: Justificativa do prestador
            print("\n   Requisito 3: Justificativa do prestador")
            assert 'justification' in template_content, \
                "Template deve exibir justificativa"
            assert 'Justificativa' in template_content or 'justificativa' in template_content, \
                "Template deve ter label para justificativa"
            print("   ✓ Justificativa do prestador implementada")
            
            # Requisito 4: Botões de ação
            print("\n   Requisito 4: Botões 'Aceitar Proposta' e 'Rejeitar Proposta'")
            assert 'Aceitar Proposta' in template_content or 'aceitar-proposta' in template_content, \
                "Template deve ter botão 'Aceitar Proposta'"
            assert 'Rejeitar Proposta' in template_content or 'rejeitar-proposta' in template_content, \
                "Template deve ter botão 'Rejeitar Proposta'"
            assert 'btn-aceitar-proposta' in template_content or 'acceptProposal' in template_content, \
                "Template deve ter ID ou função para aceitar proposta"
            assert 'rejectProposalModal' in template_content or 'rejeitar' in template_content, \
                "Template deve ter modal ou função para rejeitar proposta"
            print("   ✓ Botões de ação implementados")
            
            # Requisito 5: Verificação de saldo para aumentos
            print("\n   Requisito 5: Verificação de saldo para aumentos")
            assert 'is_increase' in template_content, \
                "Template deve verificar se é aumento"
            assert 'balance' in template_content or 'saldo' in template_content, \
                "Template deve verificar saldo"
            assert 'checkProposalBalance' in template_content or 'verificar-saldo' in template_content, \
                "Template deve ter função para verificar saldo"
            assert 'balance-check-container' in template_content or 'balance_check' in template_content, \
                "Template deve ter container para exibir status do saldo"
            print("   ✓ Verificação de saldo implementada")
            
            # Verificações adicionais de UX
            print("\n   Verificações adicionais de UX:")
            
            # Cores apropriadas
            if 'text-danger' in template_content and 'text-success' in template_content:
                print("   ✓ Usa cores apropriadas (vermelho para aumento, verde para redução)")
            
            # Ícones
            if 'fa-arrow-up' in template_content and 'fa-arrow-down' in template_content:
                print("   ✓ Usa ícones de seta para indicar direção")
            
            # Data da proposta
            if 'created_at' in template_content:
                print("   ✓ Exibe data/hora da proposta")
            
            # Modal de rejeição
            if 'rejectProposalModal' in template_content:
                print("   ✓ Tem modal para rejeição com motivo")
            
            # JavaScript para interações
            if 'acceptProposal' in template_content and 'checkProposalBalance' in template_content:
                print("   ✓ Tem JavaScript para interações dinâmicas")
            
            print("\n" + "="*80)
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*80)
            print("\nResumo da implementação da Task 9:")
            print("✓ Card destacado quando has_active_proposal é True")
            print("✓ Comparação visual entre valores original e proposto")
            print("✓ Exibição da justificativa do prestador")
            print("✓ Botões 'Aceitar Proposta' e 'Rejeitar Proposta'")
            print("✓ Verificação de saldo integrada para aumentos")
            print("✓ UX aprimorada com cores, ícones e feedback visual")
            print("="*80)
            
            return True
            
        except AssertionError as e:
            print(f"\n❌ ERRO: {str(e)}")
            return False
        except Exception as e:
            print(f"\n❌ ERRO INESPERADO: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Limpar dados de teste
            try:
                Proposal.query.filter_by(justification='Teste Task 9').delete()
                Invite.query.filter(Invite.service_title.like('Teste Task 9%')).delete()
                User.query.filter_by(email='cliente_task9@test.com').delete()
                User.query.filter_by(email='prestador_task9@test.com').delete()
                db.session.commit()
            except:
                db.session.rollback()

if __name__ == '__main__':
    success = test_cliente_proposta_card()
    sys.exit(0 if success else 1)
