#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste Simples do método auto_confirm_expired_orders()
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Order
from services.order_management_service import OrderManagementService
from datetime import datetime, timedelta


def test_auto_confirm_method():
    """Testa o método auto_confirm_expired_orders diretamente"""
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Método auto_confirm_expired_orders()")
        print("="*80)
        
        # 1. Verificar ordens existentes com status servico_executado
        ordens_executadas = Order.query.filter_by(status='servico_executado').all()
        
        print(f"\n1. Ordens com status 'servico_executado': {len(ordens_executadas)}")
        
        if ordens_executadas:
            for ordem in ordens_executadas:
                print(f"   - Ordem {ordem.id}: deadline={ordem.confirmation_deadline}")
        
        # 2. Simular expiração de uma ordem se existir
        if ordens_executadas:
            ordem_teste = ordens_executadas[0]
            print(f"\n2. Simulando expiração da ordem {ordem_teste.id}...")
            
            # Salvar deadline original
            deadline_original = ordem_teste.confirmation_deadline
            
            # Alterar para expirado
            ordem_teste.confirmation_deadline = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            print(f"   Deadline alterada de {deadline_original} para {ordem_teste.confirmation_deadline}")
            print(f"   Ordem agora está expirada")
        
        # 3. Executar o método auto_confirm_expired_orders
        print(f"\n3. Executando auto_confirm_expired_orders()...")
        
        result = OrderManagementService.auto_confirm_expired_orders()
        
        print(f"\n   RESULTADO:")
        print(f"   - processed: {result['processed']}")
        print(f"   - confirmed: {result['confirmed']}")
        print(f"   - errors: {len(result['errors'])}")
        print(f"   - timestamp: {result['timestamp']}")
        
        if result['errors']:
            print(f"\n   ERROS:")
            for error in result['errors']:
                print(f"     - {error}")
        
        # 4. Validações
        print(f"\n4. Validações:")
        
        assert 'processed' in result, "Resultado deve conter 'processed'"
        print(f"   ✓ Chave 'processed' presente")
        
        assert 'confirmed' in result, "Resultado deve conter 'confirmed'"
        print(f"   ✓ Chave 'confirmed' presente")
        
        assert 'errors' in result, "Resultado deve conter 'errors'"
        print(f"   ✓ Chave 'errors' presente")
        
        assert 'timestamp' in result, "Resultado deve conter 'timestamp'"
        print(f"   ✓ Chave 'timestamp' presente")
        
        assert isinstance(result['processed'], int), "'processed' deve ser int"
        print(f"   ✓ 'processed' é int")
        
        assert isinstance(result['confirmed'], int), "'confirmed' deve ser int"
        print(f"   ✓ 'confirmed' é int")
        
        assert isinstance(result['errors'], list), "'errors' deve ser list"
        print(f"   ✓ 'errors' é list")
        
        # Se havia ordem expirada, deve ter processado pelo menos 1
        if ordens_executadas:
            assert result['processed'] >= 1, f"Deveria ter processado pelo menos 1 ordem, mas processou {result['processed']}"
            print(f"   ✓ Processou {result['processed']} ordem(ns)")
            
            # Verificar se a ordem foi confirmada
            ordem_teste = Order.query.get(ordem_teste.id)
            if ordem_teste.status == 'concluida':
                print(f"   ✓ Ordem {ordem_teste.id} foi confirmada automaticamente")
                print(f"   ✓ auto_confirmed = {ordem_teste.auto_confirmed}")
                print(f"   ✓ confirmed_at = {ordem_teste.confirmed_at}")
            else:
                print(f"   ⚠ Ordem {ordem_teste.id} não foi confirmada (status: {ordem_teste.status})")
                if result['errors']:
                    print(f"   Possível motivo: {result['errors']}")
        
        print(f"\n" + "="*80)
        print("✓ TESTE CONCLUÍDO!")
        print("="*80)


if __name__ == '__main__':
    try:
        test_auto_confirm_method()
        print("\n✓ SUCESSO!\n")
    except AssertionError as e:
        print(f"\n❌ ERRO DE VALIDAÇÃO: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
