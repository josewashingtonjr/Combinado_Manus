#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da funcionalidade de rejeição de convites
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from models import db, User, Invite
from services.invite_service import InviteService
from app import create_app

def test_invite_rejection():
    """Testa a funcionalidade de rejeição de convites"""
    
    app = create_app()
    with app.app_context():
        try:
            # Criar um convite de teste
            print("🔍 Criando convite de teste...")
            
            # Buscar um cliente existente ou criar um
            client = User.query.filter_by(roles='cliente,prestador').first()
            if not client:
                print("❌ Nenhum cliente encontrado no banco de dados")
                return False
            
            # Criar convite
            invite = Invite(
                client_id=client.id,
                invited_phone="(11) 99999-9999",
                service_title="Teste de Rejeição",
                service_description="Convite criado para testar funcionalidade de rejeição",
                original_value=100.00,
                delivery_date=datetime.now() + timedelta(days=7),
                status='pendente'
            )
            
            db.session.add(invite)
            db.session.commit()
            
            print(f"✅ Convite criado: ID {invite.id}, Token: {invite.token}")
            
            # Testar rejeição sem motivo
            print("\n🔍 Testando rejeição sem motivo...")
            result = InviteService.reject_invite(invite)
            
            if result['success'] and invite.status == 'recusado':
                print("✅ Rejeição sem motivo funcionou corretamente")
            else:
                print("❌ Erro na rejeição sem motivo")
                return False
            
            # Criar outro convite para testar com motivo
            invite2 = Invite(
                client_id=client.id,
                invited_phone="(11) 88888-8888",
                service_title="Teste de Rejeição com Motivo",
                service_description="Convite criado para testar rejeição com motivo",
                original_value=150.00,
                delivery_date=datetime.now() + timedelta(days=10),
                status='pendente'
            )
            
            db.session.add(invite2)
            db.session.commit()
            
            print(f"\n🔍 Testando rejeição com motivo...")
            motivo = "Não tenho disponibilidade na data solicitada"
            result2 = InviteService.reject_invite(invite2, reason=motivo)
            
            if result2['success'] and invite2.status == 'recusado' and invite2.rejection_reason == motivo:
                print("✅ Rejeição com motivo funcionou corretamente")
                print(f"   Motivo salvo: {invite2.rejection_reason}")
            else:
                print("❌ Erro na rejeição com motivo")
                return False
            
            # Testar tentativa de rejeitar convite já rejeitado
            print("\n🔍 Testando rejeição de convite já rejeitado...")
            try:
                InviteService.reject_invite(invite)
                print("❌ Deveria ter dado erro ao tentar rejeitar convite já rejeitado")
                return False
            except ValueError as e:
                print(f"✅ Erro esperado capturado: {str(e)}")
            
            # Limpar dados de teste
            db.session.delete(invite)
            db.session.delete(invite2)
            db.session.commit()
            
            print("\n🎉 Todos os testes de rejeição passaram com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = test_invite_rejection()
    sys.exit(0 if success else 1)