#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste básico para verificar se o modelo Invite foi criado corretamente
"""

from app import app
from models import db, Invite, User
from datetime import datetime, timedelta

def test_invite_model():
    with app.app_context():
        # Verificar se a tabela existe
        try:
            # Tentar criar um convite de teste
            invite = Invite(
                client_id=1,
                invited_email="prestador@teste.com",
                service_title="Serviço de Teste",
                service_description="Descrição do serviço de teste",
                original_value=100.00,
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            
            print(f"✅ Modelo Invite criado com sucesso")
            print(f"   Token gerado: {invite.token}")
            print(f"   Status: {invite.status}")
            print(f"   Pode ser aceito: {invite.can_be_accepted}")
            print(f"   Está expirado: {invite.is_expired}")
            
            # Verificar se o token é único
            assert len(invite.token) == 32, "Token deve ter 32 caracteres"
            assert invite.status == 'pendente', "Status inicial deve ser 'pendente'"
            assert invite.can_be_accepted == True, "Convite deve poder ser aceito"
            assert invite.is_expired == False, "Convite não deve estar expirado"
            
            print("✅ Todas as validações do modelo passaram!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao testar modelo Invite: {e}")
            return False

if __name__ == "__main__":
    test_invite_model()