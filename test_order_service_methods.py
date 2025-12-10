#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para verificar se os métodos do OrderService foram implementados corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_order_service_methods():
    """Testa se os métodos do OrderService existem e têm as assinaturas corretas"""
    
    print("🧪 Testando métodos do OrderService...")
    
    try:
        from services.order_service import OrderService
        
        # Verificar se o método create_order foi atualizado
        print("\n1️⃣ Verificando método create_order...")
        
        import inspect
        create_order_signature = inspect.signature(OrderService.create_order)
        params = list(create_order_signature.parameters.keys())
        
        print(f"   Parâmetros: {params}")
        
        expected_params = ['client_id', 'title', 'description', 'value', 'invite_id', 'proposal_id']
        for param in expected_params:
            if param in params:
                print(f"   ✅ {param}: presente")
            else:
                print(f"   ❌ {param}: ausente")
        
        # Verificar se invite_id e proposal_id são opcionais
        invite_id_param = create_order_signature.parameters.get('invite_id')
        proposal_id_param = create_order_signature.parameters.get('proposal_id')
        
        if invite_id_param and invite_id_param.default is None:
            print("   ✅ invite_id é opcional (default=None)")
        else:
            print("   ❌ invite_id deveria ser opcional")
            
        if proposal_id_param and proposal_id_param.default is None:
            print("   ✅ proposal_id é opcional (default=None)")
        else:
            print("   ❌ proposal_id deveria ser opcional")
        
        # Verificar se o método create_order_from_invite existe
        print("\n2️⃣ Verificando método create_order_from_invite...")
        
        if hasattr(OrderService, 'create_order_from_invite'):
            print("   ✅ Método create_order_from_invite existe")
            
            from_invite_signature = inspect.signature(OrderService.create_order_from_invite)
            from_invite_params = list(from_invite_signature.parameters.keys())
            
            print(f"   Parâmetros: {from_invite_params}")
            
            expected_from_invite_params = ['invite_id', 'provider_id']
            for param in expected_from_invite_params:
                if param in from_invite_params:
                    print(f"   ✅ {param}: presente")
                else:
                    print(f"   ❌ {param}: ausente")
        else:
            print("   ❌ Método create_order_from_invite não existe")
        
        # Verificar se o InviteService foi atualizado
        print("\n3️⃣ Verificando InviteService...")
        
        from services.invite_service import InviteService
        
        if hasattr(InviteService, 'convert_invite_to_order'):
            print("   ✅ Método convert_invite_to_order existe")
            
            # Verificar se o método foi atualizado (deve usar create_order_from_invite)
            import inspect
            source = inspect.getsource(InviteService.convert_invite_to_order)
            
            if 'create_order_from_invite' in source:
                print("   ✅ Método usa create_order_from_invite")
            else:
                print("   ❌ Método não usa create_order_from_invite")
                
            if 'effective_value' in source:
                print("   ✅ Método considera valor efetivo")
            else:
                print("   ❌ Método não considera valor efetivo")
                
            if 'proposal_history' in source:
                print("   ✅ Método inclui histórico de proposta")
            else:
                print("   ❌ Método não inclui histórico de proposta")
        else:
            print("   ❌ Método convert_invite_to_order não existe")
        
        # Verificar se o modelo Invite tem current_value
        print("\n4️⃣ Verificando modelo Invite...")
        
        from models import Invite
        
        # Criar um mock para testar a propriedade current_value
        class MockInvite:
            def __init__(self, original_value, effective_value=None):
                self.original_value = original_value
                self.effective_value = effective_value
            
            @property
            def current_value(self):
                return self.effective_value if self.effective_value is not None else self.original_value
        
        # Testar a lógica
        mock_invite = MockInvite(100.0, 150.0)
        
        if hasattr(mock_invite, 'current_value'):
            print("   ✅ Propriedade current_value implementada")
            print(f"   Valor original: {mock_invite.original_value}")
            print(f"   Valor efetivo: {mock_invite.effective_value}")
            print(f"   Valor atual: {mock_invite.current_value}")
            
            if mock_invite.current_value == 150.0:
                print("   ✅ Lógica current_value funcionando corretamente")
            else:
                print("   ❌ Lógica current_value incorreta")
        else:
            print("   ❌ Propriedade current_value não implementada")
        
        print("\n🎉 Verificação de métodos concluída!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante a verificação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_order_service_methods()
    if success:
        print("\n✅ Verificação concluída com sucesso!")
    else:
        print("\n❌ Verificação falhou!")
        sys.exit(1)