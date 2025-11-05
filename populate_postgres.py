#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from app import app, db
from models import User, AdminUser, Wallet
from services.wallet_service import WalletService

def populate_database():
    """Popular o banco PostgreSQL com dados de teste"""
    with app.app_context():
        print("🔄 Populando banco de dados PostgreSQL...")
        
        # 1. Criar administrador padrão
        admin = AdminUser.query.filter_by(email='admin@combinado.com').first()
        if not admin:
            admin = AdminUser(email='admin@combinado.com', papel='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Administrador criado: admin@combinado.com")
        
        # 2. Criar usuário cliente
        cliente = User.query.filter_by(email='cliente@teste.com').first()
        if not cliente:
            cliente = User(
                nome='Cliente Teste',
                email='cliente@teste.com',
                cpf='12345678901',
                phone='(11) 99999-9999',
                roles='cliente',
                active=True
            )
            cliente.set_password('123456')
            db.session.add(cliente)
            print("✅ Cliente criado: cliente@teste.com")
        
        # 3. Criar usuário prestador
        prestador = User.query.filter_by(email='prestador@teste.com').first()
        if not prestador:
            prestador = User(
                nome='Prestador Teste',
                email='prestador@teste.com',
                cpf='98765432100',
                phone='(11) 88888-8888',
                roles='prestador',
                active=True
            )
            prestador.set_password('123456')
            db.session.add(prestador)
            print("✅ Prestador criado: prestador@teste.com")
        
        # 4. Criar usuário dual (cliente + prestador)
        dual = User.query.filter_by(email='dual@teste.com').first()
        if not dual:
            dual = User(
                nome='Usuário Dual',
                email='dual@teste.com',
                cpf='11122233344',
                phone='(11) 77777-7777',
                roles='cliente,prestador',
                active=True
            )
            dual.set_password('123456')
            db.session.add(dual)
            print("✅ Usuário dual criado: dual@teste.com")
        
        db.session.commit()
        
        # 5. Criar carteiras para todos os usuários
        users = User.query.all()
        for user in users:
            if not user.wallet:
                WalletService.create_wallet_for_user(user)
                print(f"✅ Carteira criada para: {user.email}")
        
        # 6. Adicionar saldo inicial para testes
        if cliente and cliente.wallet:
            if cliente.wallet.balance == 0:
                WalletService.deposit(cliente.id, 500.0, "Saldo inicial para testes")
                print("✅ Saldo inicial adicionado ao cliente")
        
        if dual and dual.wallet:
            if dual.wallet.balance == 0:
                WalletService.deposit(dual.id, 300.0, "Saldo inicial para testes")
                print("✅ Saldo inicial adicionado ao usuário dual")
        
        print("🎉 Banco de dados populado com sucesso!")
        print("\n📋 Credenciais de teste:")
        print("   Admin: admin@combinado.com / admin123")
        print("   Cliente: cliente@teste.com / 123456")
        print("   Prestador: prestador@teste.com / 123456")
        print("   Dual: dual@teste.com / 123456")

if __name__ == '__main__':
    populate_database()
