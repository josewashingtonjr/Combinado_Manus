#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para aplicar migração de soft delete diretamente via SQLAlchemy
"""

import os
from flask import Flask
from models import db
from sqlalchemy import text

def create_app():
    """Cria aplicação Flask para migração"""
    app = Flask(__name__)
    
    # Configuração do banco de dados
    database_path = os.path.join(os.path.dirname(__file__), 'sistema_combinado.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def apply_soft_delete_migration():
    """Aplica a migração de soft delete diretamente"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Aplicando migração de soft delete...")
            
            # Comandos SQL para adicionar colunas
            commands = [
                "ALTER TABLE users ADD COLUMN deleted_at DATETIME NULL",
                "ALTER TABLE users ADD COLUMN deleted_by INTEGER NULL", 
                "ALTER TABLE users ADD COLUMN deletion_reason TEXT NULL",
                "ALTER TABLE admin_users ADD COLUMN deleted_at DATETIME NULL",
                "ALTER TABLE admin_users ADD COLUMN deleted_by INTEGER NULL",
                "ALTER TABLE admin_users ADD COLUMN deletion_reason TEXT NULL"
            ]
            
            for i, command in enumerate(commands):
                try:
                    print(f"Executando: {command}")
                    db.session.execute(text(command))
                    db.session.commit()
                    print(f"✓ Comando {i+1} executado com sucesso")
                except Exception as e:
                    print(f"⚠ Aviso no comando {i+1}: {str(e)}")
                    db.session.rollback()
            
            # Criar índices
            index_commands = [
                "CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_deleted_by ON users(deleted_by)",
                "CREATE INDEX IF NOT EXISTS idx_admin_users_deleted_at ON admin_users(deleted_at)",
                "CREATE INDEX IF NOT EXISTS idx_admin_users_deleted_by ON admin_users(deleted_by)"
            ]
            
            print("\nCriando índices...")
            for i, command in enumerate(index_commands):
                try:
                    print(f"Executando: {command}")
                    db.session.execute(text(command))
                    db.session.commit()
                    print(f"✓ Índice {i+1} criado com sucesso")
                except Exception as e:
                    print(f"⚠ Aviso no índice {i+1}: {str(e)}")
                    db.session.rollback()
            
            print("\n✓ Migração de soft delete concluída!")
            return True
            
        except Exception as e:
            print(f"Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False

def verify_migration():
    """Verifica se a migração foi aplicada corretamente"""
    app = create_app()
    
    with app.app_context():
        try:
            # Testar se as colunas existem
            result = db.session.execute(text("PRAGMA table_info(users)"))
            user_columns = [row[1] for row in result.fetchall()]
            
            result = db.session.execute(text("PRAGMA table_info(admin_users)"))
            admin_columns = [row[1] for row in result.fetchall()]
            
            expected_columns = ['deleted_at', 'deleted_by', 'deletion_reason']
            
            print("\nVerificação da migração:")
            print("Tabela users:")
            for col in expected_columns:
                if col in user_columns:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ {col} - FALTANDO")
            
            print("Tabela admin_users:")
            for col in expected_columns:
                if col in admin_columns:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ {col} - FALTANDO")
            
            # Verificar se todos os campos estão presentes
            users_ok = all(col in user_columns for col in expected_columns)
            admins_ok = all(col in admin_columns for col in expected_columns)
            
            if users_ok and admins_ok:
                print("\n✓ Migração verificada com sucesso!")
                return True
            else:
                print("\n✗ Migração incompleta!")
                return False
                
        except Exception as e:
            print(f"Erro na verificação: {str(e)}")
            return False

if __name__ == '__main__':
    print("=== Aplicação Direta da Migração de Soft Delete ===")
    
    if apply_soft_delete_migration():
        if verify_migration():
            print("\n🎉 Migração aplicada e verificada com sucesso!")
        else:
            print("\n❌ Migração aplicada mas verificação falhou!")
    else:
        print("\n❌ Falha na aplicação da migração!")