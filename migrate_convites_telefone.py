#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para migrar o sistema de convites de email para telefone
"""

from app import app
from models import db, Invite
from datetime import datetime

def migrate_invites():
    """Migra convites existentes e atualiza estrutura"""
    
    with app.app_context():
        try:
            print("🔄 Iniciando migração do sistema de convites...")
            
            # Verificar se a coluna invited_phone já existe
            try:
                # Tentar fazer uma consulta que usa a coluna
                test_invite = Invite.query.filter(Invite.invited_phone.isnot(None)).first()
                print("✅ Coluna invited_phone já existe")
            except Exception as e:
                print(f"❌ Erro ao verificar coluna invited_phone: {e}")
                print("🔧 Executando ALTER TABLE para adicionar coluna...")
                
                # Adicionar coluna invited_phone se não existir
                db.engine.execute("""
                    ALTER TABLE invites 
                    ADD COLUMN invited_phone VARCHAR(20)
                """)
                
                print("✅ Coluna invited_phone adicionada")
            
            # Buscar convites que têm email mas não têm telefone
            invites_to_migrate = Invite.query.filter(
                Invite.invited_email.isnot(None),
                Invite.invited_phone.is_(None)
            ).all()
            
            print(f"📋 Encontrados {len(invites_to_migrate)} convites para migrar")
            
            migrated_count = 0
            for invite in invites_to_migrate:
                # Gerar um telefone fictício baseado no ID do convite
                # Em produção, você deveria ter os telefones reais
                fake_phone = f"(11) 9999-{invite.id:04d}"
                invite.invited_phone = fake_phone
                
                # Atualizar expiração para ser baseada na data do serviço
                if invite.delivery_date and invite.expires_at != invite.delivery_date:
                    invite.expires_at = invite.delivery_date
                
                migrated_count += 1
            
            # Salvar alterações
            db.session.commit()
            
            print(f"✅ {migrated_count} convites migrados com sucesso!")
            
            # Atualizar convites expirados baseado na nova lógica
            expired_invites = Invite.query.filter(
                Invite.status == 'pendente',
                Invite.delivery_date < datetime.utcnow()
            ).all()
            
            expired_count = 0
            for invite in expired_invites:
                invite.status = 'expirado'
                expired_count += 1
            
            db.session.commit()
            
            if expired_count > 0:
                print(f"⏰ {expired_count} convites marcados como expirados")
            
            # Estatísticas finais
            total_invites = Invite.query.count()
            with_phone = Invite.query.filter(Invite.invited_phone.isnot(None)).count()
            
            print(f"\n📊 Estatísticas finais:")
            print(f"   Total de convites: {total_invites}")
            print(f"   Com telefone: {with_phone}")
            print(f"   Migração concluída: {with_phone == total_invites}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante migração: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate_invites()
    if success:
        print("\n🎉 Migração concluída com sucesso!")
        print("\n📝 Próximos passos:")
        print("   1. Teste o sistema de convites")
        print("   2. Verifique se os links estão sendo gerados corretamente")
        print("   3. Teste o fluxo de aceitação/recusa")
    else:
        print("\n💥 Migração falhou! Verifique os erros acima.")