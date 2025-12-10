#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""Script para verificar os campos adicionados ao modelo Order"""

from app import app
from models import db, Order, SystemConfig

with app.app_context():
    print("=" * 60)
    print("VERIFICAÇÃO DOS CAMPOS DO MODELO ORDER")
    print("=" * 60)
    
    # Verificar campos no banco de dados
    result = db.session.execute(db.text("PRAGMA table_info(orders)"))
    columns = result.fetchall()
    
    new_fields = [
        'platform_fee_percentage_at_creation',
        'contestation_fee_at_creation',
        'cancellation_fee_percentage_at_creation',
        'auto_confirmed',
        'dispute_evidence_urls'
    ]
    
    print("\n✅ Novos campos adicionados:")
    for col in columns:
        col_name = col[1]
        if col_name in new_fields:
            col_type = col[2]
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            default = col[4] if col[4] else "sem padrão"
            print(f"   - {col_name}")
            print(f"     Tipo: {col_type}, {nullable}, Padrão: {default}")
    
    print("\n" + "=" * 60)
    print("CONFIGURAÇÕES DO SISTEMA")
    print("=" * 60)
    
    configs = SystemConfig.query.filter_by(category='taxas').all()
    print(f"\n✅ Configurações de taxas ({len(configs)}):")
    for cfg in configs:
        print(f"   - {cfg.key}: {cfg.value}")
        print(f"     Descrição: {cfg.description}")
    
    prazos = SystemConfig.query.filter_by(category='prazos').all()
    print(f"\n✅ Configurações de prazos ({len(prazos)}):")
    for cfg in prazos:
        print(f"   - {cfg.key}: {cfg.value}")
        print(f"     Descrição: {cfg.description}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 60)
