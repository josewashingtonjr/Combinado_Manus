#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para validar a sequência correta de operações no approve_proposal()

Tarefa 3: Corrigir sequência de operações no ProposalService.approve_proposal()
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Invite, Proposal
from services.invite_state_manager import InviteState

def test_approve_proposal_sequence_validation():
    """
    Valida que o código do approve_proposal está na sequência correta:
    1. proposal.accept() primeiro (seta effective_value)
    2. db.session.flush() após accept()
    3. transition_to(PROPOSTA_ACEITA) depois (limpa has_active_proposal)
    4. Validação de effective_value antes da transição
    5. Retorno com effective_value correto
    """
    
    print("\n" + "="*80)
    print("VALIDAÇÃO: Sequência de Operações no approve_proposal()")
    print("="*80)
    
    # Ler o código do arquivo
    with open('services/proposal_service.py', 'r') as f:
        code = f.read()
    
    # Encontrar o método approve_proposal
    start_marker = "def approve_proposal(proposal_id: int, client_id: int"
    end_marker = "def reject_proposal"
    
    start_idx = code.find(start_marker)
    end_idx = code.find(end_marker, start_idx)
    
    if start_idx == -1:
        print("❌ Método approve_proposal não encontrado")
        return False
    
    method_code = code[start_idx:end_idx]
    
    print("\n✅ Validando requisitos da tarefa 3:")
    
    # 1. Verificar que proposal.accept() é chamado
    if "proposal.accept(sanitized_response_reason)" in method_code:
        print("   ✓ proposal.accept() é chamado")
    else:
        print("   ❌ proposal.accept() não encontrado")
        return False
    
    # 2. Verificar que db.session.flush() é chamado após accept()
    accept_idx = method_code.find("proposal.accept(sanitized_response_reason)")
    flush_idx = method_code.find("db.session.flush()", accept_idx)
    
    if flush_idx > accept_idx and flush_idx != -1:
        print("   ✓ db.session.flush() é chamado após accept()")
    else:
        print("   ❌ db.session.flush() não encontrado após accept()")
        return False
    
    # 3. Verificar que transition_to é chamado após flush
    transition_idx = method_code.find("transition_to(InviteState.PROPOSTA_ACEITA", flush_idx)
    
    if transition_idx > flush_idx and transition_idx != -1:
        print("   ✓ transition_to(PROPOSTA_ACEITA) é chamado após flush()")
    else:
        print("   ❌ transition_to não encontrado após flush()")
        return False
    
    # 4. Verificar que há validação de effective_value antes da transição
    validation_check = "if proposal.invite.effective_value is None"
    validation_idx = method_code.find(validation_check, flush_idx)
    
    if validation_idx > flush_idx and validation_idx < transition_idx:
        print("   ✓ Validação de effective_value antes da transição")
    else:
        print("   ❌ Validação de effective_value não encontrada")
        return False
    
    # 5. Verificar que o retorno inclui effective_value
    return_section = method_code[transition_idx:]
    if "'effective_value': float(effective_value)" in return_section:
        print("   ✓ Retorno inclui effective_value correto")
    else:
        print("   ❌ Retorno não inclui effective_value")
        return False
    
    # 6. Verificar que effective_value é obtido do convite
    if "effective_value = proposal.invite.effective_value" in method_code:
        print("   ✓ effective_value é obtido do convite")
    else:
        print("   ❌ effective_value não é obtido do convite")
        return False
    
    # 7. Verificar que há validação de consistência
    if "if effective_value != proposal.proposed_value" in method_code:
        print("   ✓ Validação de consistência implementada")
    else:
        print("   ❌ Validação de consistência não encontrada")
        return False
    
    # 8. Verificar que Requirements estão documentados
    if "Requirements: 1.1, 2.1, 2.2, 5.5, 8.5, 2.4, 3.1, 3.2, 3.3, 4.1, 4.2, 4.4" in method_code:
        print("   ✓ Requirements da tarefa 3 documentados")
    else:
        print("   ⚠️  Requirements podem não estar completos")
    
    print("\n" + "="*80)
    print("✅ VALIDAÇÃO PASSOU - Sequência de operações está correta!")
    print("="*80)
    print("\nResumo das correções implementadas:")
    print("1. proposal.accept() é chamado PRIMEIRO para setar effective_value")
    print("2. db.session.flush() é chamado APÓS accept() para persistir mudanças")
    print("3. transition_to(PROPOSTA_ACEITA) é chamado DEPOIS para limpar has_active_proposal")
    print("4. effective_value é validado ANTES da transição")
    print("5. Resultado retorna effective_value correto do convite")
    print("6. Validação de consistência entre effective_value e proposed_value")
    
    return True

if __name__ == '__main__':
    try:
        success = test_approve_proposal_sequence_validation()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
