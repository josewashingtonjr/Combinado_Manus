#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para verificar se a tabela de convites foi criada corretamente no banco
"""

from app import app
from models import db, Invite, User
from datetime import datetime, timedelta

def test_invite_database():
    with app.app_context():
        try:
            # Verificar se podemos consultar a tabela
            invites_count = Invite.query.count()
            print(f"✅ Tabela 'invites' existe e tem {invites_count} registros")
            
            # Verificar se podemos criar e salvar um convite
            invite = Invite(
                client_id=1,
                invited_email="teste@prestador.com",
                service_title="Limpeza Residencial",
                service_description="Limpeza completa de casa de 3 quartos",
                original_value=150.00,
                delivery_date=datetime.utcnow() + timedelta(days=5),
                expires_at=datetime.utcnow() + timedelta(days=2)
            )
            
            # Tentar salvar no banco
            db.session.add(invite)
            db.session.commit()
            
            print(f"✅ Convite salvo no banco com ID: {invite.id}")
            print(f"   Token: {invite.token}")
            print(f"   Status: {invite.status}")
            print(f"   Valor original: R$ {invite.original_value}")
            
            # Verificar se podemos recuperar o convite
            saved_invite = Invite.query.filter_by(token=invite.token).first()
            assert saved_invite is not None, "Convite deve ser encontrado no banco"
            assert saved_invite.service_title == "Limpeza Residencial", "Título deve ser preservado"
            
            print("✅ Convite recuperado do banco com sucesso!")
            
            # Limpar o teste
            db.session.delete(saved_invite)
            db.session.commit()
            
            print("✅ Teste de banco de dados concluído com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste de banco: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    test_invite_database()