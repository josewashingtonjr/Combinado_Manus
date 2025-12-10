"""
Testes de integração para validação da navegação dos menus administrativos.
Valida todos os links, filtros e abas implementados na otimização dos menus.
"""

import pytest
from flask import url_for
from models import User, Invite, Order
from app import create_app, db
import re


@pytest.fixture(scope='session')
def app():
    """Cria aplicação de teste."""
    import sys
    import os
    
    # Adicionar o diretório raiz ao path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Importar o app completo com todas as rotas registradas
    from app import app as flask_app
    from config import TestConfig
    
    # Configurar para testes
    flask_app.config.from_object(TestConfig)
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Sessão de banco de dados para testes."""
    from models import AdminUser
    from datetime import datetime, timedelta
    
    with app.app_context():
        # Limpar dados antes de cada teste
        db.session.query(Order).delete()
        db.session.query(Invite).delete()
        db.session.query(User).delete()
        db.session.query(AdminUser).delete()
        db.session.commit()
        
        # Criar usuário admin para testes
        admin = AdminUser(
            email='admin@test.com',
            papel='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Criar dados de teste
        cliente = User(
            email='cliente1@test.com',
            nome='Cliente Teste',
            cpf='12345678901',
            phone='11987654321',
            roles='cliente'
        )
        cliente.set_password('senha123')
        
        prestador = User(
            email='prestador1@test.com',
            nome='Prestador Teste',
            cpf='98765432109',
            phone='11912345678',
            roles='prestador'
        )
        prestador.set_password('senha123')
        db.session.add_all([cliente, prestador])
        db.session.commit()
        
        # Criar convites com diferentes status
        invite1 = Invite(
            client_id=cliente.id,
            invited_phone='11999999999',
            service_title='Convite pendente',
            service_description='Descrição do convite pendente',
            original_value=50,
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        invite2 = Invite(
            client_id=cliente.id,
            invited_phone='11888888888',
            service_title='Convite aceito',
            service_description='Descrição do convite aceito',
            original_value=60,
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='aceito',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        invite3 = Invite(
            client_id=cliente.id,
            invited_phone='11777777777',
            service_title='Convite recusado',
            service_description='Descrição do convite recusado',
            original_value=40,
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='recusado',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add_all([invite1, invite2, invite3])
        db.session.commit()
        
        # Criar ordens com diferentes status
        order1 = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Ordem aguardando',
            description='Ordem aguardando execução',
            value=100,
            status='aguardando_execucao',
            service_deadline=datetime.utcnow() + timedelta(days=7)
        )
        order2 = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Ordem executada',
            description='Ordem executada',
            value=120,
            status='servico_executado',
            service_deadline=datetime.utcnow() + timedelta(days=7)
        )
        order3 = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Ordem concluída',
            description='Ordem concluída',
            value=80,
            status='concluida',
            service_deadline=datetime.utcnow() + timedelta(days=7)
        )
        order4 = Order(
            client_id=cliente.id,
            provider_id=prestador.id,
            title='Ordem contestada',
            description='Ordem contestada',
            value=90,
            status='contestada',
            service_deadline=datetime.utcnow() + timedelta(days=7),
            dispute_reason='Problema no serviço',
            dispute_opened_by=cliente.id,
            dispute_opened_at=datetime.utcnow()
        )
        db.session.add_all([order1, order2, order3, order4])
        db.session.commit()
        
        yield db.session
        
        # Rollback após cada teste
        db.session.rollback()


@pytest.fixture(scope='function')
def auth_client(client, db_session, app):
    """Cliente autenticado como admin."""
    from models import AdminUser
    
    with app.app_context():
        admin = AdminUser.query.filter_by(email='admin@test.com').first()
        
        with client.session_transaction() as sess:
            sess['admin_id'] = admin.id
            sess['_fresh'] = True
    
    return client


class TestMenuNavigation:
    """Testes de navegação do menu lateral."""
    
    def test_menu_configuracoes_taxas(self, auth_client):
        """Testa navegação para configurações de taxas."""
        response = auth_client.get('/admin/configuracoes/taxas')
        assert response.status_code == 200
        assert 'Taxas do Sistema' in response.data.decode('utf-8')
    
    def test_menu_configuracoes_seguranca(self, auth_client):
        """Testa navegação para configurações de segurança."""
        response = auth_client.get('/admin/configuracoes#seguranca')
        assert response.status_code == 200
        assert 'Segurança' in response.data.decode('utf-8') or 'seguranca' in response.data.decode('utf-8')
    
    def test_menu_relatorios_base(self, auth_client):
        """Testa navegação para página de relatórios."""
        response = auth_client.get('/admin/relatorios')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Relatórios' in html or 'relatorios' in html.lower()
    
    def test_menu_convites_todos(self, auth_client):
        """Testa navegação para todos os convites."""
        response = auth_client.get('/admin/convites')
        assert response.status_code == 200
        assert 'Convites' in response.data.decode('utf-8')
    
    def test_menu_contestacoes_todas(self, auth_client):
        """Testa navegação para todas as contestações."""
        response = auth_client.get('/admin/contestacoes')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'Contestações' in html or 'Contestacoes' in html
    
    def test_menu_ordens_todas(self, auth_client):
        """Testa navegação para todas as ordens."""
        response = auth_client.get('/admin/ordens')
        assert response.status_code == 200
        assert 'Ordens' in response.data.decode('utf-8')


class TestFiltrosConvites:
    """Testes de filtros de status em convites."""
    
    def test_filtro_convites_pendentes(self, auth_client):
        """Testa filtro de convites pendentes."""
        response = auth_client.get('/admin/convites?status=pendente')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'pendente' in html.lower()
    
    def test_filtro_convites_aceitos(self, auth_client):
        """Testa filtro de convites aceitos."""
        response = auth_client.get('/admin/convites?status=aceito')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'aceito' in html.lower()
    
    def test_filtro_convites_recusados(self, auth_client):
        """Testa filtro de convites recusados."""
        response = auth_client.get('/admin/convites?status=recusado')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'recusado' in html.lower()
    
    def test_filtro_convites_invalido(self, auth_client):
        """Testa filtro com status inválido (deve mostrar todos)."""
        response = auth_client.get('/admin/convites?status=invalido')
        assert response.status_code == 200


class TestFiltrosOrdens:
    """Testes de filtros de status em ordens."""
    
    def test_filtro_ordens_aguardando(self, auth_client):
        """Testa filtro de ordens aguardando execução."""
        response = auth_client.get('/admin/ordens?status=aguardando_execucao')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'aguardando' in html.lower()
    
    def test_filtro_ordens_executadas(self, auth_client):
        """Testa filtro de ordens executadas."""
        response = auth_client.get('/admin/ordens?status=servico_executado')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'executado' in html.lower() or 'executada' in html.lower()
    
    def test_filtro_ordens_concluidas(self, auth_client):
        """Testa filtro de ordens concluídas."""
        response = auth_client.get('/admin/ordens?status=concluida')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'conclu' in html.lower()
    
    def test_filtro_ordens_contestadas(self, auth_client):
        """Testa filtro de ordens contestadas."""
        response = auth_client.get('/admin/ordens?status=contestada')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'contest' in html.lower()


class TestFiltrosContestacoes:
    """Testes de filtros de status em contestações."""
    
    def test_filtro_contestacoes_pendentes(self, auth_client):
        """Testa filtro de contestações pendentes."""
        response = auth_client.get('/admin/contestacoes?status=pendente')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'pendente' in html.lower()
    
    def test_filtro_contestacoes_em_analise(self, auth_client):
        """Testa filtro de contestações em análise."""
        response = auth_client.get('/admin/contestacoes?status=em_analise')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'analise' in html.lower() or 'análise' in html.lower()


class TestNavegacaoAbas:
    """Testes de navegação por abas em relatórios."""
    
    def test_relatorios_tem_abas(self, auth_client):
        """Verifica se página de relatórios tem estrutura de abas."""
        response = auth_client.get('/admin/relatorios')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Verifica presença de elementos de abas
        assert 'nav-tabs' in html or 'tab-pane' in html
    
    def test_relatorios_ancora_financeiro(self, auth_client):
        """Testa navegação com âncora para aba financeiro."""
        response = auth_client.get('/admin/relatorios#financeiro')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'financeiro' in html.lower()
    
    def test_relatorios_ancora_usuarios(self, auth_client):
        """Testa navegação com âncora para aba usuários."""
        response = auth_client.get('/admin/relatorios#usuarios')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'usuários' in html.lower() or 'usuarios' in html.lower()
    
    def test_relatorios_ancora_contratos(self, auth_client):
        """Testa navegação com âncora para aba contratos."""
        response = auth_client.get('/admin/relatorios#contratos')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'contratos' in html.lower()


class TestMenuLateralVisibilidade:
    """Testes de visibilidade do menu lateral."""
    
    def test_menu_visivel_em_convites(self, auth_client):
        """Verifica se menu lateral está presente na página de convites."""
        response = auth_client.get('/admin/convites')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Verifica presença de elementos do menu lateral
        assert 'sidebar' in html.lower() or 'menu' in html.lower()
        assert 'base_admin' in html or 'Configurações' in html or 'Relatórios' in html
    
    def test_menu_visivel_em_ordens(self, auth_client):
        """Verifica se menu lateral está presente na página de ordens."""
        response = auth_client.get('/admin/ordens')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'sidebar' in html.lower() or 'menu' in html.lower()
    
    def test_menu_visivel_em_contestacoes(self, auth_client):
        """Verifica se menu lateral está presente na página de contestações."""
        response = auth_client.get('/admin/contestacoes')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'sidebar' in html.lower() or 'menu' in html.lower()


class TestConsistenciaNavegacao:
    """Testes de consistência da navegação."""
    
    def test_todas_rotas_admin_requerem_autenticacao(self, client):
        """Verifica se todas as rotas admin redirecionam sem autenticação."""
        rotas = [
            '/admin/dashboard',
            '/admin/configuracoes/taxas',
            '/admin/relatorios',
            '/admin/convites',
            '/admin/ordens',
            '/admin/contestacoes'
        ]
        
        for rota in rotas:
            response = client.get(rota, follow_redirects=False)
            # Deve redirecionar para login (302) ou retornar 401
            assert response.status_code in [302, 401, 403]
    
    def test_links_menu_nao_quebrados(self, auth_client):
        """Verifica se principais links do menu não retornam 404."""
        rotas = [
            '/admin/dashboard',
            '/admin/usuarios',
            '/admin/tokens',
            '/admin/configuracoes/taxas',
            '/admin/relatorios',
            '/admin/convites',
            '/admin/ordens',
            '/admin/contestacoes'
        ]
        
        for rota in rotas:
            response = auth_client.get(rota)
            assert response.status_code != 404, f"Rota {rota} retornou 404"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
