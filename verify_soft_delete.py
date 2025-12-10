#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para verificar se a migração de soft delete foi aplicada
"""

import os
from flask import Flask
from models import db
from sqlalchemy import text

def create_app():
    """Cria aplicação Flask para verificação"""
    app = Flask(__name__)
    
    # Configuração do banco de dados
    database_path = os.path.join(os.path.dirname(__file__), 'sistema_combinado.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

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
            
            print("Verificação da migração de soft delete:")
            print("\nTabela users:")
            for col in expected_columns:
                if col in user_columns:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ {col} - FALTANDO")
            
            print("\nTabela admin_users:")
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
                print("Todos os campos de soft delete estão presentes.")
                return True
            else:
                print("\n✗ Migração incompleta!")
                return False
                
        except Exception as e:
            print(f"Erro na verificação: {str(e)}")
            return False

if __name__ == '__main__':
    verify_migration()