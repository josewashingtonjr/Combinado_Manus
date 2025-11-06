#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do TokenCreationControlService
Verifica funcionalidade de controle de limites de criação de tokens
"""

import sys
import os
from flask import Flask
from datetime import datetime, date
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_app():
    """Cria aplicação Flask para teste"""
    app = Flask(__name__)
    
    # Configuração do banco de dados
    database_path = os.path.join(os.path.dirname(__file__), 'sistema_combinado.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    return app

def test_token_creation_control_service():
    """Testa o serviço de controle de criação de tokens"""
    
    app = create_test_app()
    
    with app.app_context():
        from models import db, AdminUser, TokenCreationLimit
        from services.token_creation_control_service import TokenCreationControlService
        
        db.init_app(app)
        
        print("=" * 60)
        print("🧪 TESTE: TokenCreationControlService")
        print("=" * 60)
        
        try:
            # 1. Verificar se existem admins no banco
            print("\n1️⃣ Verificando administradores existentes...")
            admins = AdminUser.query.filter_by(deleted_at=None).all()
            
            if not admins:
                print("❌ Nenhum administrador encontrado no banco")
                print("💡 Criando administrador de teste...")
                
                # Criar admin de teste
                test_admin = AdminUser(
                    email='admin.teste@sistema.com',
                    papel='admin'
                )
                test_admin.set_password('senha123')
                
                db.session.add(test_admin)
                db.session.commit()
                
                admins = [test_admin]
                print(f"✅ Admin de teste criado: {test_admin.email} (ID: {test_admin.id})")
            
            admin = admins[0]
            print(f"✅ Usando admin: {admin.email} (ID: {admin.id})")
            
            # 2. Testar criação/obtenção de limites
            print("\n2️⃣ Testando criação/obtenção de limites...")
            limits = TokenCreationControlService.get_or_create_limits(admin.id)
            print(f"✅ Limites obtidos:")
            print(f"   - Limite diário: R$ {limits.daily_limit:.2f}")
            print(f"   - Limite mensal: R$ {limits.monthly_limit:.2f}")
            print(f"   - Usado diário: R$ {limits.current_daily_used:.2f}")
            print(f"   - Usado mensal: R$ {limits.current_monthly_used:.2f}")
            
            # 3. Testar verificação de limites
            print("\n3️⃣ Testando verificação de limites...")
            
            # Teste com valor válido
            test_amount = Decimal('1000.00')
            result = TokenCreationControlService.can_create_tokens(admin.id, test_amount)
            print(f"✅ Teste com R$ {test_amount:.2f}: {result['allowed']}")
            if result['allowed']:
                print(f"   - Mensagem: {result['message']}")
            else:
                print(f"   - Motivo: {result['reason']}")
                print(f"   - Mensagem: {result['message']}")
            
            # Teste com valor que excede limite diário
            test_amount_high = Decimal('15000.00')
            result_high = TokenCreationControlService.can_create_tokens(admin.id, test_amount_high)
            print(f"✅ Teste com R$ {test_amount_high:.2f}: {result_high['allowed']}")
            if not result_high['allowed']:
                print(f"   - Motivo: {result_high['reason']}")
                print(f"   - Mensagem: {result_high['message']}")
            
            # 4. Testar registro de criação de tokens
            print("\n4️⃣ Testando registro de criação de tokens...")
            if result['allowed']:
                creation_result = TokenCreationControlService.register_token_creation(
                    admin.id, 
                    test_amount, 
                    reason="Teste do sistema de controle",
                    transaction_id="TXN-TEST-001"
                )
                print(f"✅ Criação registrada:")
                print(f"   - Valor criado: R$ {creation_result['amount_created']:.2f}")
                print(f"   - Usado diário atual: R$ {creation_result['daily_used']:.2f}")
                print(f"   - Restante diário: R$ {creation_result['daily_remaining']:.2f}")
                print(f"   - Usado mensal atual: R$ {creation_result['monthly_used']:.2f}")
                print(f"   - Restante mensal: R$ {creation_result['monthly_remaining']:.2f}")
            
            # 5. Testar informações detalhadas
            print("\n5️⃣ Testando informações detalhadas...")
            info = TokenCreationControlService.get_admin_limits_info(admin.id)
            print(f"✅ Informações do admin {info['admin_email']}:")
            print(f"   - Limite diário: R$ {info['daily_limit']:.2f}")
            print(f"   - Usado diário: R$ {info['daily_used']:.2f} ({info['daily_percentage_used']:.1f}%)")
            print(f"   - Limite mensal: R$ {info['monthly_limit']:.2f}")
            print(f"   - Usado mensal: R$ {info['monthly_used']:.2f} ({info['monthly_percentage_used']:.1f}%)")
            
            # 6. Testar atualização de limites
            print("\n6️⃣ Testando atualização de limites...")
            update_result = TokenCreationControlService.update_admin_limits(
                admin.id,
                daily_limit=15000.00,
                monthly_limit=150000.00,
                updated_by_admin_id=admin.id
            )
            print(f"✅ Atualização de limites:")
            print(f"   - Sucesso: {update_result['success']}")
            print(f"   - Mensagem: {update_result['message']}")
            
            # 7. Testar listagem de todos os admins
            print("\n7️⃣ Testando listagem de todos os admins...")
            all_limits = TokenCreationControlService.get_all_admins_limits()
            print(f"✅ Total de admins com limites: {len(all_limits)}")
            for limit_info in all_limits:
                print(f"   - {limit_info['admin_email']}: "
                      f"Diário R$ {limit_info['daily_limit']:.2f}, "
                      f"Mensal R$ {limit_info['monthly_limit']:.2f}")
            
            # 8. Testar casos de erro
            print("\n8️⃣ Testando casos de erro...")
            
            # Admin inexistente
            try:
                TokenCreationControlService.get_or_create_limits(99999)
                print("❌ Deveria ter falhado para admin inexistente")
            except ValueError as e:
                print(f"✅ Erro esperado para admin inexistente: {e}")
            
            # Valor inválido
            try:
                result_invalid = TokenCreationControlService.can_create_tokens(admin.id, -100)
                if not result_invalid['allowed'] and result_invalid['reason'] == 'invalid_amount':
                    print("✅ Erro esperado para valor negativo detectado")
                else:
                    print("❌ Deveria ter rejeitado valor negativo")
            except Exception as e:
                print(f"✅ Erro esperado para valor inválido: {e}")
            
            print("\n🎉 Todos os testes concluídos com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Erro durante os testes: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = test_token_creation_control_service()
    if success:
        print("\n✅ TokenCreationControlService está funcionando corretamente!")
    else:
        print("\n❌ Falhas detectadas no TokenCreationControlService!")
        sys.exit(1)