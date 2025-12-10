#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
Script para aplicar migration de gestão de ordens e criar configurações iniciais
"""

from app import app
from models import db, SystemConfig
from datetime import datetime
from decimal import Decimal

def column_exists(table_name, column_name):
    """Verifica se uma coluna existe na tabela"""
    result = db.session.execute(db.text(
        f"PRAGMA table_info({table_name})"
    ))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns

def apply_migration():
    """Aplica a migration para adicionar campos de gestão de ordens"""
    with app.app_context():
        print("🔧 Aplicando migration de gestão de ordens...")
        
        try:
            # Adicionar campos de taxas vigentes na criação
            if not column_exists('orders', 'platform_fee_percentage_at_creation'):
                db.session.execute(db.text(
                    "ALTER TABLE orders ADD COLUMN platform_fee_percentage_at_creation NUMERIC(5, 2)"
                ))
                print("✓ Campo platform_fee_percentage_at_creation adicionado")
            else:
                print("⚠️  Campo platform_fee_percentage_at_creation já existe")
            
            if not column_exists('orders', 'contestation_fee_at_creation'):
                db.session.execute(db.text(
                    "ALTER TABLE orders ADD COLUMN contestation_fee_at_creation NUMERIC(10, 2)"
                ))
                print("✓ Campo contestation_fee_at_creation adicionado")
            else:
                print("⚠️  Campo contestation_fee_at_creation já existe")
            
            if not column_exists('orders', 'cancellation_fee_percentage_at_creation'):
                db.session.execute(db.text(
                    "ALTER TABLE orders ADD COLUMN cancellation_fee_percentage_at_creation NUMERIC(5, 2)"
                ))
                print("✓ Campo cancellation_fee_percentage_at_creation adicionado")
            else:
                print("⚠️  Campo cancellation_fee_percentage_at_creation já existe")
            
            # Adicionar campo de confirmação automática
            if not column_exists('orders', 'auto_confirmed'):
                db.session.execute(db.text(
                    "ALTER TABLE orders ADD COLUMN auto_confirmed BOOLEAN NOT NULL DEFAULT 0"
                ))
                print("✓ Campo auto_confirmed adicionado")
            else:
                print("⚠️  Campo auto_confirmed já existe")
            
            # Adicionar campo de URLs de provas
            if not column_exists('orders', 'dispute_evidence_urls'):
                db.session.execute(db.text(
                    "ALTER TABLE orders ADD COLUMN dispute_evidence_urls TEXT"
                ))
                print("✓ Campo dispute_evidence_urls adicionado")
            else:
                print("⚠️  Campo dispute_evidence_urls já existe")
            
            db.session.commit()
            print("✅ Migration aplicada com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao aplicar migration: {e}")
            raise

def create_initial_configs():
    """Cria registros iniciais de configuração no SystemConfig"""
    with app.app_context():
        print("\n🔧 Criando configurações iniciais do sistema...")
        
        try:
            configs = [
                {
                    'key': 'platform_fee_percentage',
                    'value': '5.0',
                    'description': 'Percentual cobrado pela plataforma sobre o valor do serviço',
                    'category': 'taxas'
                },
                {
                    'key': 'contestation_fee',
                    'value': '10.00',
                    'description': 'Taxa fixa de contestação bloqueada como garantia',
                    'category': 'taxas'
                },
                {
                    'key': 'cancellation_fee_percentage',
                    'value': '10.0',
                    'description': 'Percentual de multa aplicado em cancelamentos',
                    'category': 'taxas'
                },
                {
                    'key': 'confirmation_deadline_hours',
                    'value': '36',
                    'description': 'Prazo em horas para confirmação manual antes da confirmação automática',
                    'category': 'prazos'
                }
            ]
            
            for config_data in configs:
                # Verificar se já existe
                existing = SystemConfig.query.filter_by(key=config_data['key']).first()
                
                if existing:
                    print(f"⚠️  Configuração '{config_data['key']}' já existe (valor: {existing.value})")
                else:
                    config = SystemConfig(
                        key=config_data['key'],
                        value=config_data['value'],
                        description=config_data['description'],
                        category=config_data['category']
                    )
                    db.session.add(config)
                    print(f"✓ Configuração '{config_data['key']}' criada (valor: {config_data['value']})")
            
            db.session.commit()
            print("✅ Configurações iniciais criadas com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar configurações: {e}")
            raise

def verify_migration():
    """Verifica se a migration foi aplicada corretamente"""
    with app.app_context():
        print("\n🔍 Verificando migration...")
        
        try:
            # Verificar campos na tabela orders usando PRAGMA (SQLite)
            result = db.session.execute(db.text("PRAGMA table_info(orders)"))
            all_columns = result.fetchall()
            
            required_columns = [
                'platform_fee_percentage_at_creation',
                'contestation_fee_at_creation',
                'cancellation_fee_percentage_at_creation',
                'auto_confirmed',
                'dispute_evidence_urls'
            ]
            
            found_columns = []
            for col in all_columns:
                col_name = col[1]  # Nome da coluna está no índice 1
                if col_name in required_columns:
                    found_columns.append(col_name)
            
            if len(found_columns) == 5:
                print("✅ Todos os campos foram adicionados corretamente:")
                for col_name in found_columns:
                    print(f"   - {col_name}")
            else:
                print(f"⚠️  Apenas {len(found_columns)} de 5 campos foram encontrados")
                missing = set(required_columns) - set(found_columns)
                if missing:
                    print(f"   Campos faltando: {', '.join(missing)}")
            
            # Verificar configurações
            configs = SystemConfig.query.filter(
                SystemConfig.key.in_([
                    'platform_fee_percentage',
                    'contestation_fee',
                    'cancellation_fee_percentage',
                    'confirmation_deadline_hours'
                ])
            ).all()
            
            print(f"\n✅ {len(configs)} configurações encontradas:")
            for config in configs:
                print(f"   - {config.key}: {config.value} ({config.category})")
            
        except Exception as e:
            print(f"❌ Erro ao verificar migration: {e}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRATION: Sistema de Gestão de Ordens")
    print("=" * 60)
    
    try:
        # Aplicar migration
        apply_migration()
        
        # Criar configurações iniciais
        create_initial_configs()
        
        # Verificar
        verify_migration()
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERRO NA MIGRATION: {e}")
        print("=" * 60)
        exit(1)
