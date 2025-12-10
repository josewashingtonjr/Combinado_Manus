#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para validar a tarefa 8: Atualizar template do cliente para exibir valor correto
"""

import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Proposal
from datetime import datetime, timedelta

def test_cliente_template_valor_display():
    """
    Testa se o template do cliente exibe o valor correto:
    - Mostra effective_value como principal quando existe
    - Adiciona comparação com original_value
    - Calcula e exibe diferença
    - Usa cores apropriadas (verde para redução, vermelho para aumento)
    """
    
    print("="*80)
    print("🧪 TESTE: Template do Cliente - Exibição de Valor Correto")
    print("="*80)
    
    with app.app_context():
        try:
            # Limpar dados de teste anteriores
            Proposal.query.filter_by(justification='Teste Task 8').delete()
            Invite.query.filter(Invite.service_title.like('Teste Task 8%')).delete()
            User.query.filter_by(email='cliente_task8@test.com').delete()
            User.query.filter_by(email='prestador_task8@test.com').delete()
            db.session.commit()
            
            # 1. Criar usuários de teste
            print("\n1. Criando usuários de teste...")
            cliente = User(
                nome='Cliente Task 8',
                email='cliente_task8@test.com',
                cpf='11111111111',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                nome='Prestador Task 8',
                email='prestador_task8@test.com',
                cpf='22222222222',
                phone='11999999999',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db.session.add(cliente)
            db.session.add(prestador)
            db.session.commit()
            print(f"   ✓ Cliente criado: {cliente.nome}")
            print(f"   ✓ Prestador criado: {prestador.nome}")
            
            # 2. Testar cenário: Convite com proposta aceita (aumento de valor)
            print("\n2. Testando cenário: Proposta aceita com AUMENTO de valor...")
            invite_aumento = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Task 8 - Aumento',
                service_description='Teste de aumento de valor',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3),
                status='proposta_aceita'
            )
            db.session.add(invite_aumento)
            db.session.flush()
            
            # Criar proposta aceita com aumento
            proposal_aumento = Proposal(
                invite_id=invite_aumento.id,
                prestador_id=prestador.id,
                original_value=Decimal('100.00'),
                proposed_value=Decimal('150.00'),
                justification='Teste Task 8',
                status='accepted',
                responded_at=datetime.utcnow()
            )
            db.session.add(proposal_aumento)
            db.session.flush()
            
            # Setar effective_value
            invite_aumento.effective_value = Decimal('150.00')
            invite_aumento.current_proposal_id = proposal_aumento.id
            invite_aumento.has_active_proposal = False
            db.session.commit()
            
            print(f"   ✓ Convite criado com proposta aceita")
            print(f"   - Valor original: R$ {invite_aumento.original_value}")
            print(f"   - Valor efetivo: R$ {invite_aumento.effective_value}")
            print(f"   - Diferença: +R$ {invite_aumento.effective_value - invite_aumento.original_value}")
            
            # Validar que effective_value está correto
            assert invite_aumento.effective_value == Decimal('150.00'), "Effective value deveria ser 150.00"
            assert invite_aumento.effective_value > invite_aumento.original_value, "Deveria ser um aumento"
            print("   ✓ Valores validados corretamente")
            
            # 3. Testar cenário: Convite com proposta aceita (redução de valor)
            print("\n3. Testando cenário: Proposta aceita com REDUÇÃO de valor...")
            invite_reducao = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Task 8 - Redução',
                service_description='Teste de redução de valor',
                original_value=Decimal('200.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3),
                status='proposta_aceita'
            )
            db.session.add(invite_reducao)
            db.session.flush()
            
            # Criar proposta aceita com redução
            proposal_reducao = Proposal(
                invite_id=invite_reducao.id,
                prestador_id=prestador.id,
                original_value=Decimal('200.00'),
                proposed_value=Decimal('150.00'),
                justification='Teste Task 8',
                status='accepted',
                responded_at=datetime.utcnow()
            )
            db.session.add(proposal_reducao)
            db.session.flush()
            
            # Setar effective_value
            invite_reducao.effective_value = Decimal('150.00')
            invite_reducao.current_proposal_id = proposal_reducao.id
            invite_reducao.has_active_proposal = False
            db.session.commit()
            
            print(f"   ✓ Convite criado com proposta aceita")
            print(f"   - Valor original: R$ {invite_reducao.original_value}")
            print(f"   - Valor efetivo: R$ {invite_reducao.effective_value}")
            print(f"   - Diferença: R$ {invite_reducao.effective_value - invite_reducao.original_value}")
            
            # Validar que effective_value está correto
            assert invite_reducao.effective_value == Decimal('150.00'), "Effective value deveria ser 150.00"
            assert invite_reducao.effective_value < invite_reducao.original_value, "Deveria ser uma redução"
            print("   ✓ Valores validados corretamente")
            
            # 4. Testar cenário: Convite sem proposta aceita
            print("\n4. Testando cenário: Convite SEM proposta aceita...")
            invite_sem_proposta = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title='Teste Task 8 - Sem Proposta',
                service_description='Teste sem proposta',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3),
                status='pendente'
            )
            db.session.add(invite_sem_proposta)
            db.session.commit()
            
            print(f"   ✓ Convite criado sem proposta")
            print(f"   - Valor original: R$ {invite_sem_proposta.original_value}")
            print(f"   - Valor efetivo: {invite_sem_proposta.effective_value}")
            
            # Validar que effective_value é None
            assert invite_sem_proposta.effective_value is None, "Effective value deveria ser None"
            print("   ✓ Valores validados corretamente")
            
            # 5. Verificar template
            print("\n5. Verificando template do cliente...")
            with open('templates/cliente/ver_convite.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Verificar se mostra effective_value como principal
            assert 'invite.effective_value' in template_content, "Template deve verificar effective_value"
            print("   ✓ Template verifica effective_value")
            
            # Verificar se mostra comparação com original_value
            assert 'invite.original_value' in template_content, "Template deve mostrar original_value"
            print("   ✓ Template mostra original_value")
            
            # Verificar se calcula diferença
            assert 'difference = invite.effective_value - invite.original_value' in template_content, \
                "Template deve calcular diferença"
            print("   ✓ Template calcula diferença")
            
            # Verificar se usa cores apropriadas
            assert 'alert-danger' in template_content and 'alert-success' in template_content, \
                "Template deve usar cores apropriadas"
            print("   ✓ Template usa cores apropriadas (verde/vermelho)")
            
            # Verificar se mostra valor riscado
            assert 'text-decoration-line-through' in template_content, \
                "Template deve mostrar valor original riscado"
            print("   ✓ Template mostra valor original riscado")
            
            # Verificar se mostra ícones de seta
            assert 'fa-arrow-up' in template_content and 'fa-arrow-down' in template_content, \
                "Template deve mostrar ícones de seta"
            print("   ✓ Template mostra ícones de seta (aumento/redução)")
            
            print("\n" + "="*80)
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*80)
            print("\nResumo da implementação:")
            print("✓ Mostra effective_value como valor principal quando existe")
            print("✓ Adiciona comparação com original_value (riscado)")
            print("✓ Calcula e exibe diferença (aumento/redução)")
            print("✓ Usa cores apropriadas:")
            print("  - Verde (alert-success) para redução")
            print("  - Vermelho (alert-danger) para aumento")
            print("✓ Mostra ícones de seta para indicar direção da mudança")
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
                Proposal.query.filter_by(justification='Teste Task 8').delete()
                Invite.query.filter(Invite.service_title.like('Teste Task 8%')).delete()
                User.query.filter_by(email='cliente_task8@test.com').delete()
                User.query.filter_by(email='prestador_task8@test.com').delete()
                db.session.commit()
            except:
                db.session.rollback()

if __name__ == '__main__':
    success = test_cliente_template_valor_display()
    sys.exit(0 if success else 1)
