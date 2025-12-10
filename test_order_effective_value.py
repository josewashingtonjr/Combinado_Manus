#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples para verificar a lógica de valor efetivo em ordens
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_order_logic():
    """Testa a lógica de valor efetivo sem banco de dados"""
    
    print("🧪 Testando lógica de valor efetivo em ordens...")
    
    try:
        # Simular dados de convite e proposta
        class MockInvite:
            def __init__(self, original_value, effective_value=None, current_proposal_id=None):
                self.original_value = original_value
                self.effective_value = effective_value
                self.current_proposal_id = current_proposal_id
            
            @property
            def current_value(self):
                """Retorna o valor atual do convite (efetivo se houver proposta aceita, senão original)"""
                return self.effective_value if self.effective_value is not None else self.original_value
        
        class MockProposal:
            def __init__(self, proposal_id, original_value, proposed_value, justification, status='accepted'):
                self.id = proposal_id
                self.original_value = original_value
                self.proposed_value = proposed_value
                self.justification = justification
                self.status = status
                self.created_at = "2024-01-01T10:00:00"
                self.responded_at = "2024-01-01T11:00:00"
        
        # Teste 1: Convite sem proposta (valor original)
        print("\n1️⃣ Testando convite sem proposta...")
        
        invite1 = MockInvite(original_value=200.00)
        effective_value1 = invite1.current_value
        
        print(f"   Valor original: R$ {invite1.original_value:.2f}")
        print(f"   Valor efetivo: R$ {effective_value1:.2f}")
        
        assert effective_value1 == 200.00, "Valor efetivo deve ser igual ao original"
        print("✅ Teste 1 passou: valor original usado corretamente")
        
        # Teste 2: Convite com proposta aceita (valor proposto)
        print("\n2️⃣ Testando convite com proposta aceita...")
        
        invite2 = MockInvite(original_value=200.00, effective_value=250.00, current_proposal_id=1)
        proposal2 = MockProposal(1, 200.00, 250.00, "Escopo expandido")
        effective_value2 = invite2.current_value
        
        print(f"   Valor original: R$ {invite2.original_value:.2f}")
        print(f"   Valor proposto: R$ {proposal2.proposed_value:.2f}")
        print(f"   Valor efetivo: R$ {effective_value2:.2f}")
        
        assert effective_value2 == 250.00, "Valor efetivo deve ser o proposto aceito"
        print("✅ Teste 2 passou: valor proposto usado corretamente")
        
        # Teste 3: Lógica de histórico de proposta
        print("\n3️⃣ Testando geração de histórico de proposta...")
        
        def generate_proposal_history(invite, proposal):
            if invite.current_proposal_id and proposal and proposal.status == 'accepted':
                return {
                    'proposal_id': proposal.id,
                    'original_value': float(proposal.original_value),
                    'proposed_value': float(proposal.proposed_value),
                    'justification': proposal.justification,
                    'created_at': proposal.created_at,
                    'responded_at': proposal.responded_at
                }
            return None
        
        history = generate_proposal_history(invite2, proposal2)
        
        print(f"   Histórico gerado: {history is not None}")
        if history:
            print(f"   Proposta ID: {history['proposal_id']}")
            print(f"   Valor original: R$ {history['original_value']:.2f}")
            print(f"   Valor proposto: R$ {history['proposed_value']:.2f}")
            print(f"   Justificativa: {history['justification']}")
        
        assert history is not None, "Histórico deve ser gerado para proposta aceita"
        assert history['proposal_id'] == 1, "ID da proposta deve estar correto"
        assert history['original_value'] == 200.00, "Valor original deve estar correto"
        assert history['proposed_value'] == 250.00, "Valor proposto deve estar correto"
        print("✅ Teste 3 passou: histórico gerado corretamente")
        
        # Teste 4: Lógica de descrição com histórico
        print("\n4️⃣ Testando inclusão de histórico na descrição...")
        
        def create_order_description(base_description, proposal_history):
            if proposal_history:
                return (f"{base_description}\n\n--- Histórico da Proposta ---\n"
                       f"Valor Original: R$ {proposal_history['original_value']:.2f}\n"
                       f"Valor Proposto: R$ {proposal_history['proposed_value']:.2f}\n"
                       f"Justificativa: {proposal_history['justification']}")
            return base_description
        
        base_desc = "Desenvolvimento de website responsivo"
        full_desc = create_order_description(base_desc, history)
        
        print(f"   Descrição base: {base_desc}")
        print(f"   Descrição completa: {full_desc[:100]}...")
        
        assert "Histórico da Proposta" in full_desc, "Histórico deve estar na descrição"
        assert "R$ 200.00" in full_desc, "Valor original deve estar na descrição"
        assert "R$ 250.00" in full_desc, "Valor proposto deve estar na descrição"
        assert "Escopo expandido" in full_desc, "Justificativa deve estar na descrição"
        print("✅ Teste 4 passou: descrição com histórico criada corretamente")
        
        # Teste 5: Validação de saldo com valor efetivo
        print("\n5️⃣ Testando validação de saldo com valor efetivo...")
        
        def validate_balance_for_order(client_balance, effective_value):
            return client_balance >= effective_value
        
        client_balance = 300.00
        
        # Teste com valor original (200)
        valid_original = validate_balance_for_order(client_balance, invite1.current_value)
        print(f"   Saldo cliente: R$ {client_balance:.2f}")
        print(f"   Valor original (R$ {invite1.current_value:.2f}): {'✅ Válido' if valid_original else '❌ Inválido'}")
        
        # Teste com valor proposto (250)
        valid_proposed = validate_balance_for_order(client_balance, invite2.current_value)
        print(f"   Valor proposto (R$ {invite2.current_value:.2f}): {'✅ Válido' if valid_proposed else '❌ Inválido'}")
        
        # Teste com saldo insuficiente
        low_balance = 150.00
        valid_low = validate_balance_for_order(low_balance, invite2.current_value)
        print(f"   Saldo baixo (R$ {low_balance:.2f}) vs proposto: {'✅ Válido' if valid_low else '❌ Inválido'}")
        
        assert valid_original, "Saldo deve ser suficiente para valor original"
        assert valid_proposed, "Saldo deve ser suficiente para valor proposto"
        assert not valid_low, "Saldo baixo deve ser insuficiente"
        print("✅ Teste 5 passou: validação de saldo funcionando corretamente")
        
        print("\n🎉 Todos os testes de lógica passaram com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_order_logic()
    if success:
        print("\n✅ Teste de lógica concluído com sucesso!")
    else:
        print("\n❌ Teste de lógica falhou!")
        sys.exit(1)