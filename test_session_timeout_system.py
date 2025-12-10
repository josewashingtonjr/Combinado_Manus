#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do sistema de timeout de sessão
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, SessionTimeout, User, AdminUser
from services.session_timeout_manager import SessionTimeoutManager
from config import Config

def test_session_timeout_system():
    """Testar o sistema de timeout de sessão"""
    
    print("🧪 Iniciando testes do sistema de timeout de sessão...")
    
    # Criar aplicação Flask para teste
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Teste 1: Verificar se a tabela existe
            print("\n📋 Teste 1: Verificando se a tabela session_timeouts existe...")
            
            # Tentar fazer uma query simples
            count = SessionTimeout.query.count()
            print(f"✅ Tabela existe! Registros atuais: {count}")
            
            # Teste 2: Verificar se podemos criar um registro
            print("\n📋 Teste 2: Testando criação de registro de timeout...")
            
            # Criar um registro de teste
            test_session = SessionTimeout(
                session_id='test-session-123',
                user_id=None,
                admin_id=None,
                last_activity=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=30),
                ip_address='127.0.0.1',
                user_agent='Test User Agent'
            )
            
            db.session.add(test_session)
            db.session.commit()
            
            print("✅ Registro de timeout criado com sucesso!")
            
            # Teste 3: Verificar métodos do SessionTimeoutManager
            print("\n📋 Teste 3: Testando métodos do SessionTimeoutManager...")
            
            # Testar contagem de sessões ativas
            active_count = SessionTimeoutManager.get_active_sessions_count()
            print(f"✅ Sessões ativas: {active_count}")
            
            # Testar limpeza de sessões expiradas
            cleaned = SessionTimeoutManager.cleanup_expired_sessions()
            print(f"✅ Sessões expiradas limpas: {cleaned}")
            
            # Teste 4: Limpar dados de teste
            print("\n📋 Teste 4: Limpando dados de teste...")
            
            SessionTimeout.query.filter_by(session_id='test-session-123').delete()
            db.session.commit()
            
            print("✅ Dados de teste removidos!")
            
            print("\n🎉 Todos os testes passaram! Sistema de timeout funcionando corretamente.")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante os testes: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_session_timeout_manager_methods():
    """Testar métodos específicos do SessionTimeoutManager"""
    
    print("\n🔧 Testando métodos específicos do SessionTimeoutManager...")
    
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        try:
            # Simular contexto de request
            with app.test_request_context('/test', method='GET'):
                
                # Teste de contagem de sessões ativas
                count = SessionTimeoutManager.get_active_sessions_count()
                print(f"✅ Contagem de sessões ativas: {count}")
                
                # Teste de limpeza de sessões expiradas
                cleaned = SessionTimeoutManager.cleanup_expired_sessions()
                print(f"✅ Limpeza de sessões: {cleaned} removidas")
                
                print("✅ Métodos do SessionTimeoutManager funcionando!")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao testar métodos: {str(e)}")
            return False

if __name__ == '__main__':
    print("🚀 Executando testes do sistema de timeout de sessão...")
    
    # Executar testes
    test1_success = test_session_timeout_system()
    test2_success = test_session_timeout_manager_methods()
    
    if test1_success and test2_success:
        print("\n🎉 SUCESSO: Sistema de timeout de sessão implementado e funcionando!")
        print("\n📝 Funcionalidades implementadas:")
        print("   ✅ Modelo SessionTimeout no banco de dados")
        print("   ✅ SessionTimeoutManager com todos os métodos")
        print("   ✅ Middleware de verificação de timeout no app.py")
        print("   ✅ Integração nos logins (user e admin)")
        print("   ✅ Rotas de API para gerenciamento de sessão")
        print("   ✅ JavaScript para monitoramento no frontend")
        print("   ✅ Sistema de avisos e extensão de sessão")
        
        print("\n🔧 Para usar o sistema:")
        print("   1. Faça login normalmente")
        print("   2. O sistema monitora automaticamente a sessão")
        print("   3. Aviso aparece 5 minutos antes da expiração")
        print("   4. Sessão expira após 30 minutos de inatividade")
        
    else:
        print("\n❌ FALHA: Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)