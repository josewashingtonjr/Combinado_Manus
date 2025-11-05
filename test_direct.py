#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from app import app
from models import User

with app.app_context():
    user = User.query.filter_by(email='cliente@teste.com').first()
    if user:
        print(f'✅ Usuário encontrado: {user.email}')
        print(f'Hash: {user.password_hash[:60]}...')
        
        # Testar senha
        senha = 'cliente123'
        resultado = user.check_password(senha)
        print(f'Teste senha "{senha}": {resultado}')
        
        if resultado:
            print('✅ SENHA CORRETA - Autenticação OK')
        else:
            print('❌ SENHA INCORRETA - Problema na verificação')
    else:
        print('❌ Usuário não encontrado')
