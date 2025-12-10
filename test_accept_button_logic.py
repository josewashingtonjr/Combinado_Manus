#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se o botão de aceitar está sendo desabilitado corretamente
quando o usuário cria uma contraproposta
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import app, db
from models import User, Invite
from datetime import datetime, timedelta

def test_accept_button_disabled_for_creator():
    """
    Testa se o botão de aceitar é desabilitado para quem criou a contraproposta
    """
    with app.app_context():
        print("\n" + "="*80)
        print("TESTE: Botão de Aceitar Desabilitado para Criador de Contraproposta")
        print("="*80)
        
        # Buscar um cliente e um prestador
        cliente = User.query.filter_by(roles='cliente').first()
        prestador = User.query.filter_by(roles='prestador').first()
        
        if not cliente or not prestador:
            print("❌ ERRO: Não há cliente ou prestador no banco de dados")
            return False
        
        print(f"\n📋 Cliente: {cliente.nome} (ID: {cliente.id})")
        print(f"📋 Prestador: {prestador.nome} (ID: {prestador.id}, Phone: {prestador.phone})")
        
        # Criar um convite original
        original_invite = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="Teste - Serviço Original",
            service_description="Descrição do serviço",
            original_value=100.00,
            delivery_date=datetime.now() + timedelta(days=7),
            expires_at=datetime.now() + timedelta(days=3),
            status='pendente'
        )
        db.session.add(original_invite)
        db.session.commit()
        
        print(f"\n✅ Convite original criado (ID: {original_invite.id})")
        
        # Cenário 1: Prestador cria contraproposta
        print("\n" + "-"*80)
        print("CENÁRIO 1: Prestador cria contraproposta")
        print("-"*80)
        
        counter_proposal_by_prestador = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="🔄 CONTRAPROPOSTA - Teste - Contraproposta do Prestador",
            service_description=f"💡 Contraproposta de {prestador.nome}: Justificativa do prestador",
            original_value=150.00,
            delivery_date=datetime.now() + timedelta(days=7),
            expires_at=datetime.now() + timedelta(days=3),
            status='pendente'
        )
        db.session.add(counter_proposal_by_prestador)
        db.session.commit()
        
        print(f"✅ Contraproposta criada pelo prestador (ID: {counter_proposal_by_prestador.id})")
        
        # Verificar se prestador pode aceitar (deve ser False)
        can_prestador_accept = counter_proposal_by_prestador.can_user_accept_counter_proposal(prestador.id)
        print(f"\n🔍 Prestador pode aceitar sua própria contraproposta? {can_prestador_accept}")
        
        if not can_prestador_accept:
            print("✅ CORRETO: Prestador NÃO pode aceitar sua própria contraproposta")
        else:
            print("❌ ERRO: Prestador PODE aceitar sua própria contraproposta (deveria ser False)")
        
        # Verificar se cliente pode aceitar (deve ser True)
        can_cliente_accept = counter_proposal_by_prestador.can_user_accept_counter_proposal(cliente.id)
        print(f"🔍 Cliente pode aceitar contraproposta do prestador? {can_cliente_accept}")
        
        if can_cliente_accept:
            print("✅ CORRETO: Cliente PODE aceitar contraproposta do prestador")
        else:
            print("❌ ERRO: Cliente NÃO pode aceitar contraproposta do prestador (deveria ser True)")
        
        # Cenário 2: Cliente cria contraproposta
        print("\n" + "-"*80)
        print("CENÁRIO 2: Cliente cria contraproposta")
        print("-"*80)
        
        counter_proposal_by_cliente = Invite(
            client_id=cliente.id,
            invited_phone=prestador.phone,
            service_title="🔄 CONTRAPROPOSTA - Teste - Contraproposta do Cliente",
            service_description=f"💡 Contraproposta de {cliente.nome}: Justificativa do cliente",
            original_value=120.00,
            delivery_date=datetime.now() + timedelta(days=7),
            expires_at=datetime.now() + timedelta(days=3),
            status='pendente'
        )
        db.session.add(counter_proposal_by_cliente)
        db.session.commit()
        
        print(f"✅ Contraproposta criada pelo cliente (ID: {counter_proposal_by_cliente.id})")
        
        # Verificar se cliente pode aceitar (deve ser False)
        can_cliente_accept_own = counter_proposal_by_cliente.can_user_accept_counter_proposal(cliente.id)
        print(f"\n🔍 Cliente pode aceitar sua própria contraproposta? {can_cliente_accept_own}")
        
        if not can_cliente_accept_own:
            print("✅ CORRETO: Cliente NÃO pode aceitar sua própria contraproposta")
        else:
            print("❌ ERRO: Cliente PODE aceitar sua própria contraproposta (deveria ser False)")
        
        # Verificar se prestador pode aceitar (deve ser True)
        can_prestador_accept_cliente = counter_proposal_by_cliente.can_user_accept_counter_proposal(prestador.id)
        print(f"🔍 Prestador pode aceitar contraproposta do cliente? {can_prestador_accept_cliente}")
        
        if can_prestador_accept_cliente:
            print("✅ CORRETO: Prestador PODE aceitar contraproposta do cliente")
        else:
            print("❌ ERRO: Prestador NÃO pode aceitar contraproposta do cliente (deveria ser True)")
        
        # Limpar dados de teste
        print("\n" + "-"*80)
        print("Limpando dados de teste...")
        db.session.delete(counter_proposal_by_cliente)
        db.session.delete(counter_proposal_by_prestador)
        db.session.delete(original_invite)
        db.session.commit()
        print("✅ Dados de teste removidos")
        
        # Resultado final
        print("\n" + "="*80)
        all_correct = (
            not can_prestador_accept and 
            can_cliente_accept and 
            not can_cliente_accept_own and 
            can_prestador_accept_cliente
        )
        
        if all_correct:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*80)
            return True
        else:
            print("❌ ALGUNS TESTES FALHARAM!")
            print("="*80)
            return False

if __name__ == '__main__':
    success = test_accept_button_disabled_for_creator()
    sys.exit(0 if success else 1)
