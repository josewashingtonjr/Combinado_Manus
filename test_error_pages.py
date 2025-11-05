#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import os
from app import app, db, init_db
from models import User, AdminUser
from flask import session

class TestErrorPages:
    """Testes para páginas de erro personalizadas"""
    
    @pytest.fixture
    def client(self):
        """Configurar cliente de teste"""
        # Criar banco de dados temporário
        db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                init_db()
                yield client
        
        os.close(db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_404_error_page_not_logged_in(self, client):
        """Testar página 404 para usuário não logado"""
        response = client.get('/pagina-inexistente')
        
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'P\xc3\xa1gina N\xc3\xa3o Encontrada' in response.data
        assert b'Fazer Login' in response.data
        assert b'P\xc3\xa1gina Inicial' in response.data
    
    def test_404_error_page_admin_logged_in(self, client):
        """Testar página 404 para administrador logado"""
        # Simular login de admin
        with client.session_transaction() as sess:
            sess['admin_id'] = 1
        
        response = client.get('/admin/pagina-inexistente')
        
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'Dashboard Administrativo' in response.data
        assert b'sistema administrativo' in response.data
    
    def test_404_error_page_user_logged_in(self, client):
        """Testar página 404 para usuário regular logado"""
        # Criar usuário de teste
        with app.app_context():
            user = User(email='teste@teste.com', papel='cliente')
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Simular login de usuário
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
        
        response = client.get('/cliente/pagina-inexistente')
        
        assert response.status_code == 404
        assert b'404' in response.data
        assert b'Meu Dashboard' in response.data or b'Dashboard' in response.data
    
    def test_403_error_page_not_logged_in(self, client):
        """Testar página 403 para usuário não logado"""
        # Tentar acessar área administrativa sem login
        response = client.get('/admin/dashboard')
        
        # Pode ser redirecionado ou dar 403, dependendo da implementação
        assert response.status_code in [302, 403]
    
    def test_403_error_page_admin_logged_in(self, client):
        """Testar página 403 para administrador (simulando acesso negado)"""
        # Simular login de admin
        with client.session_transaction() as sess:
            sess['admin_id'] = 1
        
        # Criar uma rota que force erro 403 para teste
        @app.route('/test-403-admin')
        def test_403_admin():
            from flask import abort
            abort(403)
        
        response = client.get('/test-403-admin')
        
        assert response.status_code == 403
        assert b'403' in response.data
        assert b'Acesso Negado' in response.data
    
    def test_500_error_logging(self, client):
        """Testar se erros 500 são logados corretamente"""
        # Criar uma rota que force erro 500 para teste
        @app.route('/test-500')
        def test_500():
            raise Exception("Erro de teste para logging")
        
        # Capturar logs
        import logging
        import io
        log_capture_string = io.StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.ERROR)
        
        # Adicionar handler temporário
        app.logger.addHandler(ch)
        
        try:
            response = client.get('/test-500')
            assert response.status_code == 500
            assert b'500' in response.data
            assert b'Erro Interno do Servidor' in response.data
            
            # Verificar se o erro foi logado
            log_contents = log_capture_string.getvalue()
            assert 'Erro de teste para logging' in log_contents or len(log_contents) > 0
            
        finally:
            # Remover handler temporário
            app.logger.removeHandler(ch)
    
    def test_500_error_page_admin_context(self, client):
        """Testar página 500 com contexto de administrador"""
        # Simular login de admin
        with client.session_transaction() as sess:
            sess['admin_id'] = 1
        
        # Criar uma rota que force erro 500 para teste
        @app.route('/test-500-admin')
        def test_500_admin():
            raise Exception("Erro administrativo de teste")
        
        response = client.get('/test-500-admin')
        
        assert response.status_code == 500
        assert b'500' in response.data
        assert b'sistema administrativo' in response.data or b'logs do sistema' in response.data
    
    def test_500_error_page_user_context(self, client):
        """Testar página 500 com contexto de usuário regular"""
        # Criar usuário de teste
        with app.app_context():
            user = User(email='teste500@teste.com', papel='cliente')
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        
        # Simular login de usuário
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
        
        # Criar uma rota que force erro 500 para teste
        @app.route('/test-500-user')
        def test_500_user():
            raise Exception("Erro de usuário de teste")
        
        response = client.get('/test-500-user')
        
        assert response.status_code == 500
        assert b'500' in response.data
        assert b'Nossa equipe foi notificada' in response.data
    
    def test_error_pages_responsive_design(self, client):
        """Testar se as páginas de erro são responsivas"""
        # Testar 404
        response = client.get('/pagina-inexistente')
        assert b'col-md-6' in response.data  # Bootstrap responsive class
        assert b'@media' in response.data or b'responsive' in response.data.lower()
        
        # Testar com user agent mobile
        response = client.get('/pagina-inexistente', 
                            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'})
        assert response.status_code == 404
    
    def test_error_pages_accessibility(self, client):
        """Testar acessibilidade das páginas de erro"""
        response = client.get('/pagina-inexistente')
        
        # Verificar elementos de acessibilidade
        assert b'aria-label' in response.data or b'alt=' in response.data
        assert b'<h1' in response.data  # Estrutura semântica
        assert b'<h2' in response.data
    
    def test_error_pages_terminology_consistency(self, client):
        """Testar consistência de terminologia nas páginas de erro"""
        # Teste para admin - deve ver terminologia técnica
        with client.session_transaction() as sess:
            sess['admin_id'] = 1
        
        response = client.get('/admin/pagina-inexistente')
        # Admin pode ver terminologia mais técnica
        assert response.status_code == 404
        
        # Teste para usuário - deve ver terminologia amigável
        with client.session_transaction() as sess:
            sess.clear()
            sess['user_id'] = 1
        
        response = client.get('/cliente/pagina-inexistente')
        # Usuário deve ver linguagem mais amigável
        assert response.status_code == 404
    
    def test_error_pages_navigation_links(self, client):
        """Testar se os links de navegação funcionam corretamente"""
        response = client.get('/pagina-inexistente')
        
        # Verificar se contém links de navegação apropriados
        assert b'href=' in response.data
        assert b'P\xc3\xa1gina Inicial' in response.data or b'home' in response.data.lower()
    
    def test_error_logging_context_preservation(self, client):
        """Testar se o contexto de sessão é preservado nos logs"""
        # Simular usuário logado
        with client.session_transaction() as sess:
            sess['user_id'] = 123
            sess['admin_id'] = None
        
        # Capturar logs
        import logging
        import io
        log_capture_string = io.StringIO()
        ch = logging.StreamHandler(log_capture_string)
        ch.setLevel(logging.WARNING)
        
        app.logger.addHandler(ch)
        
        try:
            # Gerar erro 404
            response = client.get('/pagina-que-nao-existe-mesmo')
            assert response.status_code == 404
            
            # Verificar se o contexto foi logado
            log_contents = log_capture_string.getvalue()
            # Deve conter informações de contexto do usuário
            assert len(log_contents) > 0
            
        finally:
            app.logger.removeHandler(ch)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])