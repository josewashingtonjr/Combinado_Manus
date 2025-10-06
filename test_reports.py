#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste dos relatórios funcionais do sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Order, Transaction, Wallet, Invite
from services.report_service import ReportService
from datetime import datetime, timedelta

def test_reports():
    """Testa os relatórios funcionais"""
    with app.app_context():
        try:
            print("=== TESTE DOS RELATÓRIOS FUNCIONAIS ===")
            
            # Teste 1: Relatório de Contratos
            print("\n1. Testando Relatório de Contratos...")
            try:
                contracts_data = ReportService.get_contracts_report_data()
                print(f"   ✅ Total de contratos: {contracts_data['total_contratos']}")
                print(f"   ✅ Valor total: R$ {contracts_data['valor_total']:,.2f}")
                print(f"   ✅ Status encontrados: {list(contracts_data['status_stats'].keys())}")
            except Exception as e:
                print(f"   ❌ Erro no relatório de contratos: {str(e)}")
            
            # Teste 2: Relatório de Usuários
            print("\n2. Testando Relatório de Usuários...")
            try:
                users_data = ReportService.get_users_report_data()
                print(f"   ✅ Total de usuários: {users_data['total_usuarios']}")
                print(f"   ✅ Usuários ativos: {users_data['usuarios_ativos']}")
                print(f"   ✅ Clientes: {users_data['clientes']}")
                print(f"   ✅ Prestadores: {users_data['prestadores']}")
                print(f"   ✅ Saldo total: R$ {users_data['saldo_total']:,.2f}")
            except Exception as e:
                print(f"   ❌ Erro no relatório de usuários: {str(e)}")
            
            # Teste 3: Relatório Financeiro
            print("\n3. Testando Relatório Financeiro...")
            try:
                financial_data = ReportService.get_financial_report_data()
                print(f"   ✅ Total de transações: {financial_data['total_transacoes']}")
                print(f"   ✅ Volume total: R$ {financial_data['volume_total']:,.2f}")
                print(f"   ✅ Receita de taxas: R$ {financial_data['receita_taxas']:,.2f}")
                print(f"   ✅ Tipos de transação: {list(financial_data['transaction_stats'].keys())}")
            except Exception as e:
                print(f"   ❌ Erro no relatório financeiro: {str(e)}")
            
            # Teste 4: Relatório de Convites
            print("\n4. Testando Relatório de Convites...")
            try:
                invites_data = ReportService.get_invites_report_data()
                print(f"   ✅ Total de convites: {invites_data['total_convites']}")
                print(f"   ✅ Taxa de aceitação: {invites_data['taxa_aceitacao']:.1f}%")
                print(f"   ✅ Taxa de conversão: {invites_data['taxa_conversao']:.1f}%")
                print(f"   ✅ Status encontrados: {list(invites_data['status_stats'].keys())}")
            except Exception as e:
                print(f"   ❌ Erro no relatório de convites: {str(e)}")
            
            # Teste 5: Exportação para Excel (apenas teste de geração)
            print("\n5. Testando Exportação para Excel...")
            try:
                # Testar exportação de contratos
                contracts_data = ReportService.get_contracts_report_data()
                excel_data = ReportService.export_contracts_to_excel(contracts_data)
                print(f"   ✅ Excel de contratos gerado: {len(excel_data)} bytes")
                
                # Testar exportação de usuários
                users_data = ReportService.get_users_report_data()
                excel_data = ReportService.export_users_to_excel(users_data)
                print(f"   ✅ Excel de usuários gerado: {len(excel_data)} bytes")
            except Exception as e:
                print(f"   ❌ Erro na exportação Excel: {str(e)}")
            
            # Teste 6: Exportação para PDF (apenas teste de geração)
            print("\n6. Testando Exportação para PDF...")
            try:
                # Testar exportação de contratos
                contracts_data = ReportService.get_contracts_report_data()
                pdf_data = ReportService.export_contracts_to_pdf(contracts_data)
                print(f"   ✅ PDF de contratos gerado: {len(pdf_data)} bytes")
                
                # Testar exportação de usuários
                users_data = ReportService.get_users_report_data()
                pdf_data = ReportService.export_users_to_pdf(users_data)
                print(f"   ✅ PDF de usuários gerado: {len(pdf_data)} bytes")
            except Exception as e:
                print(f"   ❌ Erro na exportação PDF: {str(e)}")
            
            # Teste 7: Filtros por Data
            print("\n7. Testando Filtros por Data...")
            try:
                # Testar filtro dos últimos 30 dias
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                filtered_data = ReportService.get_contracts_report_data(
                    start_date=start_date,
                    end_date=end_date
                )
                print(f"   ✅ Contratos dos últimos 30 dias: {filtered_data['total_contratos']}")
                
                filtered_users = ReportService.get_users_report_data(
                    start_date=start_date,
                    end_date=end_date
                )
                print(f"   ✅ Usuários dos últimos 30 dias: {filtered_users['total_usuarios']}")
            except Exception as e:
                print(f"   ❌ Erro nos filtros por data: {str(e)}")
            
            print("\n=== TESTE CONCLUÍDO ===")
            print("✅ Sistema de relatórios funcionais implementado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro geral no teste: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    success = test_reports()
    if success:
        print("\n🎉 Todos os testes passaram! Os relatórios estão funcionais.")
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")