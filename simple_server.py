#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request
from models import db, User, AdminUser
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://combinado_user:combinado_pass@localhost/combinado_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        print(f"Login attempt: {email}")
        
        if not email or not password:
            return jsonify({'ok': False, 'error': 'Campos obrigatórios'}), 400
        
        # Tentar como usuário normal primeiro
        user = User.query.filter_by(email=email, active=True).first()
        
        if user:
            if not user.check_password(password):
                print(f"Invalid password for user: {email}")
                return jsonify({'ok': False, 'error': 'Email ou senha incorretos'}), 401
            
            token = secrets.token_urlsafe(32)
            print(f"User login successful: {email}")
            
            return jsonify({
                'ok': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'name': user.nome,
                    'email': user.email,
                    'role': user.roles
                }
            })
        
        # Se não for usuário, tentar como admin
        admin = AdminUser.query.filter_by(email=email).first()
        
        if admin:
            if not admin.check_password(password):
                print(f"Invalid password for admin: {email}")
                return jsonify({'ok': False, 'error': 'Email ou senha incorretos'}), 401
            
            token = secrets.token_urlsafe(32)
            print(f"Admin login successful: {email}")
            
            return jsonify({
                'ok': True,
                'token': token,
                'user': {
                    'id': admin.id,
                    'name': 'Administrador',
                    'email': admin.email,
                    'role': 'admin',
                    'papel': admin.papel
                }
            })
        
        # Nenhum encontrado
        print(f"User/Admin not found: {email}")
        return jsonify({'ok': False, 'error': 'Email ou senha incorretos'}), 401
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'ok': False, 'error': 'Erro interno'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
