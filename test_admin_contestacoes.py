#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste para validar a correção do sistema de contestações/disputas
Tarefa 11.2: Corrigir erro 500 na análise de contestações/disputas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Order, User, AdminUser
from services.admin_service import AdminService

def test_admin_contestacoes():
    """Testa o sistema de contestações do admin"""
    
    with app.app_context():
        print("\n⚖️ Iniciando teste do sistema de contestações...")
        
        # 1. Testar busca de contestações
        print("\n1️⃣ Testando busca de contestações...")
        
        contestacoes = AdminService.get_contestacoes()
        print(f"   📋 Contestações encontradas: {len(contestacoes)}")
        
        for contestacao in contestacoes:
            print(f"   - Ordem {contestacao.id}: {contestacao.title}")
            print(f"     Status: {contestacao.status}")
            print(f"     Cliente: {contestacao.client_id}")
            print(f"     Prestador: {contestacao.provider_id}")
            print(f"     Valor: R$ {contestacao.value:.2f}")
        
        assert len(contestacoes) > 0, "Deveria haver pelo menos uma contestação"
        print("   ✅ Busca de contestações funcionando")
        
        # 2. Testar detalhes de contestação específica
        print("\n2️⃣ Testando detalhes de contestação específica...")
        
        if contestacoes:
            contestacao_id = contestacoes[0].id
            details = AdminService.get_contestacao_details(contestacao_id)
            
            assert details is not None, f"Deveria retornar detalhes para contestação {contestacao_id}"
            
            print(f"   📄 Detalhes da contestação {contestacao_id}:")
            print(f"     Ordem: {details['order'].title}")
            print(f"     Cliente: {details['client'].nome if details['client'] else 'N/A'}")
            print(f"     Prestador: {details['provider'].nome if details['provider'] else 'N/A'}")
            print(f"     Valor em escrow: R$ {details['escrow_amount']:.2f}")
            print(f"     Transações relacionadas: {len(details['transactions'])}")
            print(f"     Pode resolver: {details['can_resolve']}")
            
            assert details['order'].status == 'disputada', "Ordem deveria estar disputada"
            assert details['can_resolve'] == True, "Admin deveria poder resolver"
            print("   ✅ Detalhes de contestação funcionando")
        
        # 3. Testar validações de contestação inexistente
        print("\n3️⃣ Testando validações de contestação inexistente...")
        
        details_inexistente = AdminService.get_contestacao_details(99999)
        assert details_inexistente is None, "Deveria retornar None para contestação inexistente"
        print("   ✅ Validação de contestação inexistente funcionando")
        
        # 4. Testar resolução de contestação (simulação)
        print("\n4️⃣ Testando resolução de contestação...")
        
        # Buscar admin
        admin = AdminUser.query.filter_by(email="admin@combinado.com").first()
        assert admin is not None, "Admin não encontrado"
        
        if contestacoes:
            contestacao_id = contestacoes[0].id
            
            # Testar validações de entrada
            result_invalid = AdminService.resolve_contestacao(
                admin_id=admin.id,
                order_id=contestacao_id,
                decision="decisao_invalida",
                admin_notes="Teste de validação"
            )
            
            assert result_invalid['success'] == False, "Deveria falhar com decisão inválida"
            assert "inválida" in result_invalid['error'].lower(), f"Mensagem inadequada: {result_invalid['error']}"
            print("   ✅ Validação de decisão inválida funcionando")
            
            # Testar admin inexistente
            result_admin_invalid = AdminService.resolve_contestacao(
                admin_id=99999,
                order_id=contestacao_id,
                decision="favor_cliente",
                admin_notes="Teste admin inexistente"
            )
            
            assert result_admin_invalid['success'] == False, "Deveria falhar com admin inexistente"
            print("   ✅ Validação de admin inexistente funcionando")
            
            # Testar ordem inexistente
            result_order_invalid = AdminService.resolve_contestacao(
                admin_id=admin.id,
                order_id=99999,
                decision="favor_cliente",
                admin_notes="Teste ordem inexistente"
            )
            
            assert result_order_invalid['success'] == False, "Deveria falhar com ordem inexistente"
            print("   ✅ Validação de ordem inexistente funcionando")
        
        # 5. Testar filtros de status (futuro)
        print("\n5️⃣ Testando filtros de status...")
        
        contestacoes_filtradas = AdminService.get_contestacoes(status="pendente")
        print(f"   📋 Contestações filtradas: {len(contestacoes_filtradas)}")
        print("   ✅ Sistema de filtros preparado para futuras implementações")
        
        print("\n🎉 TESTE DE CONTESTAÇÕES CONCLUÍDO COM SUCESSO!")
        print("   ✅ Busca de contestações funcionando")
        print("   ✅ Detalhes de contestação funcionando")
        print("   ✅ Validações de entrada funcionando")
        print("   ✅ Sistema preparado para resolução de disputas")
        
        return True

if __name__ == '__main__':
    try:
        test_admin_contestacoes()
        print("\n✅ TODOS OS TESTES PASSARAM!")
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)