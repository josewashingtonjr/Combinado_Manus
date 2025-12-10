#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para validar a sequência correta de operações no approve_proposal()

Tarefa 3: Corrigir sequência de operações no ProposalService.approve_proposal()
- Modificar para chamar proposal.accept() primeiro (seta effective_value)
- Adicionar db.session.flush() após accept()
- Modificar para chamar transition_to(PROPOSTA_ACEITA) depois (limpa has_active_proposal)
- Garantir que effective_value está setado antes da transição
- Validar que resultado retorna effective_value correto
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Proposal, Wallet
from services.proposal_service import ProposalService
from services.wallet_service import WalletService

def test_approve_proposal_sequence():
    """Testa que approve_proposal executa operações na sequência correta"""
    
    with app.app_context():
        try:
            print("\n" + "="*80)
            print("TESTE: Sequência de Operações no approve_proposal()")
            print("="*80)
            
            # 1. Criar usuários
            print("\n1️⃣ Criando usuários...")
            timestamp = int(datetime.now().timestamp())
            
            cliente = User(
                nome=f"Cliente Teste {timestamp}",
                email=f"cliente_{timestamp}@test.com",
                phone="11999999999",
                password_hash="senha123",
                cpf=f"{timestamp % 100000000000:011d}",
                roles="cliente"
            )
            
            prestador = User(
                nome=f"Prestador Teste {timestamp + 1}",
                email=f"prestador_{timestamp + 1}@test.com",
                phone="11888888888",
                password_hash="senha123",
                cpf=f"{(timestamp + 1) % 100000000000:011d}",
                roles="prestador"
            )
            
            db.session.add_all([cliente, prestador])
            db.session.commit()
            
            # 2. Criar carteiras
            print("2️⃣ Criando carteiras...")
            carteira_cliente = Wallet(user_id=cliente.id, balance=Decimal('500.00'))
            carteira_prestador = Wallet(user_id=prestador.id, balance=Decimal('0.00'))
            db.session.add_all([carteira_cliente, carteira_prestador])
            db.session.commit()
            
            # 3. Criar convite
            print("3️⃣ Criando convite...")
            from datetime import timedelta
            delivery_date = datetime.now() + timedelta(days=30)
            
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Serviço Teste",
                service_description="Descrição do serviço",
                original_value=Decimal('100.00'),
                delivery_date=delivery_date,
                status='pendente'
            )
            db.session.add(convite)
            db.session.commit()
            
            # 4. Criar proposta
            print("4️⃣ Criando proposta de alteração...")
            proposta_result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.00'),
                justification="Preciso de mais material"
            )
            
            print(f"   ✓ Proposta criada: ID {proposta_result['proposal_id']}")
            
            # Verificar estado antes da aprovação
            db.session.refresh(convite)
            print(f"\n📊 Estado ANTES da aprovação:")
            print(f"   - has_active_proposal: {convite.has_active_proposal}")
            print(f"   - current_proposal_id: {convite.current_proposal_id}")
            print(f"   - effective_value: {convite.effective_value}")
            print(f"   - status: {convite.status}")
            
            assert convite.has_active_proposal == True, "has_active_proposal deveria ser True"
            assert convite.current_proposal_id == proposta_result['proposal_id'], "current_proposal_id deveria estar setado"
            assert convite.effective_value is None, "effective_value deveria ser None"
            assert convite.status == 'proposta_enviada', "status deveria ser proposta_enviada"
            
            # 5. Aprovar proposta
            print("\n5️⃣ Aprovando proposta...")
            aprovacao_result = ProposalService.approve_proposal(
                proposal_id=proposta_result['proposal_id'],
                client_id=cliente.id,
                client_response_reason="Valor justo"
            )
            
            print(f"   ✓ Proposta aprovada")
            print(f"   - Resultado: {aprovacao_result['message']}")
            
            # 6. Verificar estado após aprovação
            db.session.refresh(convite)
            proposta = Proposal.query.get(proposta_result['proposal_id'])
            
            print(f"\n📊 Estado DEPOIS da aprovação:")
            print(f"   - has_active_proposal: {convite.has_active_proposal}")
            print(f"   - current_proposal_id: {convite.current_proposal_id}")
            print(f"   - effective_value: {convite.effective_value}")
            print(f"   - status: {convite.status}")
            print(f"   - proposal.status: {proposta.status}")
            
            # Validações conforme requisitos da tarefa
            print("\n✅ Validando requisitos da tarefa 3:")
            
            # 1. effective_value deve estar setado
            assert convite.effective_value is not None, "❌ effective_value não foi setado"
            print("   ✓ effective_value está setado")
            
            # 2. effective_value deve ser igual ao proposed_value
            assert convite.effective_value == Decimal('150.00'), f"❌ effective_value ({convite.effective_value}) diferente de proposed_value (150.00)"
            print(f"   ✓ effective_value correto: {convite.effective_value}")
            
            # 3. has_active_proposal deve ser False após transição
            assert convite.has_active_proposal == False, "❌ has_active_proposal não foi limpo"
            print("   ✓ has_active_proposal foi limpo (False)")
            
            # 4. current_proposal_id deve ser mantido (referência histórica)
            assert convite.current_proposal_id == proposta_result['proposal_id'], "❌ current_proposal_id foi removido incorretamente"
            print(f"   ✓ current_proposal_id mantido: {convite.current_proposal_id}")
            
            # 5. status deve ser proposta_aceita
            assert convite.status == 'proposta_aceita', f"❌ status incorreto: {convite.status}"
            print(f"   ✓ status correto: {convite.status}")
            
            # 6. proposal.status deve ser accepted
            assert proposta.status == 'accepted', f"❌ proposal.status incorreto: {proposta.status}"
            print(f"   ✓ proposal.status correto: {proposta.status}")
            
            # 7. Resultado deve retornar effective_value correto
            assert aprovacao_result['effective_value'] == 150.00, f"❌ Resultado não retorna effective_value correto: {aprovacao_result['effective_value']}"
            print(f"   ✓ Resultado retorna effective_value correto: {aprovacao_result['effective_value']}")
            
            print("\n" + "="*80)
            print("✅ TESTE PASSOU - Sequência de operações está correta!")
            print("="*80)
            
            return True
            
        except AssertionError as e:
            print(f"\n❌ TESTE FALHOU: {str(e)}")
            raise
        except Exception as e:
            print(f"\n❌ ERRO NO TESTE: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    test_approve_proposal_sequence()
