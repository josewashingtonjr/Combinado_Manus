#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para configurar o banco de dados na pasta instance
"""

import os
from flask import Flask
from models import db

def create_app():
    """Cria aplicação Flask com banco na pasta instance"""
    app = Flask(__name__)
    
    # Garantir que a pasta instance existe
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Configuração do banco de dados na pasta instance
    database_path = os.path.join(instance_path, 'test_combinado.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def setup_database():
    """Configura o banco de dados com todas as tabelas"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Configurando banco de dados na pasta instance...")
        
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Todas as tabelas criadas com sucesso!")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"📋 Tabelas criadas ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
            
            # Verificar se a tabela token_creation_limits existe
            if 'token_creation_limits' in tables:
                print("✅ Tabela token_creation_limits encontrada!")
            else:
                print("⚠️  Tabela token_creation_limits não encontrada")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao configurar banco: {e}")
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CONFIGURAÇÃO: Banco de Dados Instance")
    print("=" * 60)
    
    if setup_database():
        print("\n🎉 Banco configurado com sucesso!")
        print("💡 Agora você pode rodar: python app.py")
    else:
        print("\n❌ Falha na configuração do banco")