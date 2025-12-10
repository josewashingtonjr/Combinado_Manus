#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Script para aplicar migração de soft delete
Adiciona campos deleted_at, deleted_by e deletion_reason aos modelos User e AdminUser
"""

import os
import sys
from datetime import datetime
from flask import Flask
from models import db

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
    """Aplica a migração de soft delete"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Iniciando migração de soft delete...")
            
            # Ler e executar o script SQL
            sql_file = os.path.join(os.path.dirname(__file__), 'migrations', 'add_soft_delete_fields.sql')
            
            if not os.path.exists(sql_file):
                print(f"Erro: Arquivo SQL não encontrado: {sql_file}")
                return False
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Dividir em comandos individuais (separados por ;)
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            # Executar cada comando
            for i, command in enumerate(commands):
                # Pular comentários
                if command.startswith('--') or not command:
                    continue
                
                try:
                    from sqlalchemy import text
                    print(f"Executando comando {i+1}/{len(commands)}: {command[:50]}...")
                    db.session.execute(text(command))
                    db.session.commit()
                    print(f"✓ Comando {i+1} executado com sucesso")
                except Exception as e:
                    print(f"⚠ Aviso no comando {i+1}: {str(e)}")
                    # Continuar mesmo com avisos (pode ser que a coluna já exista)
                    db.session.rollback()
            
            print("\n✓ Migração de soft delete concluída com sucesso!")
            print("Campos adicionados:")
            print("  - users.deleted_at")
            print("  - users.deleted_by")
            print("  - users.deletion_reason")
            print("  - admin_users.deleted_at")
            print("  - admin_users.deleted_by")
            print("  - admin_users.deletion_reason")
            print("  - Índices para performance")
            
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
            from sqlalchemy import text
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
    print("=== Migração de Soft Delete ===")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Aplicar migração
    if apply_soft_delete_migration():
        # Verificar migração
        if verify_migration():
            print("\n🎉 Migração de soft delete concluída e verificada!")
            sys.exit(0)
        else:
            print("\n❌ Migração aplicada mas verificação falhou!")
            sys.exit(1)
    else:
        print("\n❌ Falha na aplicação da migração!")
        sys.exit(1)