#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Testes completos do ConfigService
Tarefa 38: Criar testes do ConfigService

Testa:
- Get de todas as taxas
- Set de taxas com validações
- Cache de configurações
- Ordens antigas mantêm taxas originais
- Configurações por categoria
- Atualização em lote
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, SystemConfig, Order, User, Wallet
from services.config_service import ConfigService


@pytest.fixture
def client():
    """Fixture para criar cliente de teste"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def init_configs():
    """Fixture para inicializar configurações padrão"""
    with app.app_context():
        ConfigService.initialize_default_configs()
        yield


class TestConfigServiceGetMethods:
    """Testes dos métodos GET do ConfigService"""
    
    def test_get_platform_fee_percentage_default(self, client, init_configs):
        """Testa get_platform_fee_percentage com valor padrão"""
        with app.app_context():
            fee = ConfigService.get_platform_fee_percentage()
            
            assert isinstance(fee, Decimal)
            assert fee == Decimal('5.0')
    
    def test_get_contestation_fee_default(self, client, init_configs):
        """Testa get_contestation_fee com valor padrão"""
        with app.app_context():
            fee = ConfigService.get_contestation_fee()
            
            assert isinstance(fee, Decimal)
            assert fee == Decimal('10.00')
    
    def test_get_cancellation_fee_percentage_default(self, client, init_configs):
        """Testa get_cancellation_fee_percentage com valor padrão"""
        with app.app_context():
            fee = ConfigService.get_cancellation_fee_percentage()
            
            assert isinstance(fee, Decimal)
            assert fee == Decimal('10.0')
    
    def test_get_all_fees(self, client, init_configs):
        """Testa get_all_fees retorna todas as taxas"""
        with app.app_context():
            fees = ConfigService.get_all_fees()
            
            assert isinstance(fees, dict)
            assert 'platform_fee_percentage' in fees
            assert 'contestation_fee' in fees
            assert 'cancellation_fee_percentage' in fees
            
            assert isinstance(fees['platform_fee_percentage'], Decimal)
            assert isinstance(fees['contestation_fee'], Decimal)
            assert isinstance(fees['cancellation_fee_percentage'], Decimal)
    
    def test_get_config_generic(self, client, init_configs):
        """Testa get_config genérico"""
        with app.app_context():
            # Testar com configuração existente
            value = ConfigService.get_config('taxa_transacao')
            assert value == 5.0  # Convertido para float
            
            # Testar com configuração inexistente
            value = ConfigService.get_config('config_inexistente', 'default')
            assert value == 'default'
    
    def test_get_configs_by_category(self, client, init_configs):
        """Testa get_configs_by_category"""
        with app.app_context():
            # Obter todas as taxas
            taxas = ConfigService.get_configs_by_category('taxas')
            
            assert isinstance(taxas, dict)
            assert len(taxas) > 0
            assert 'platform_fee_percentage' in taxas
            assert 'contestation_fee' in taxas
            
            # Verificar estrutura de cada configuração
            for key, config in taxas.items():
                assert 'value' in config
                assert 'description' in config
                assert 'updated_at' in config


class TestConfigServiceSetMethods:
    """Testes dos métodos SET do ConfigService"""
    
    def test_set_platform_fee_percentage_valid(self, client, init_configs):
        """Testa set_platform_fee_percentage com valor válido"""
        with app.app_context():
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('7.5'), admin_id=1)
            
            assert success is True
            assert 'atualizada' in msg.lower()
            
            # Verificar se foi atualizado
            new_value = ConfigService.get_platform_fee_percentage()
            assert new_value == Decimal('7.5')
    
    def test_set_platform_fee_percentage_invalid_high(self, client, init_configs):
        """Testa set_platform_fee_percentage com valor acima de 100%"""
        with app.app_context():
            # Primeiro garantir que está no valor padrão
            ConfigService.set_platform_fee_percentage(Decimal('5.0'), admin_id=1)
            
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('150'), admin_id=1)
            
            assert success is False
            assert '0%' in msg and '100%' in msg
            
            # Verificar que não foi alterado
            value = ConfigService.get_platform_fee_percentage()
            assert value == Decimal('5.0')  # Valor padrão
    
    def test_set_platform_fee_percentage_invalid_negative(self, client, init_configs):
        """Testa set_platform_fee_percentage com valor negativo"""
        with app.app_context():
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('-5'), admin_id=1)
            
            assert success is False
            assert '0%' in msg and '100%' in msg
    
    def test_set_contestation_fee_valid(self, client, init_configs):
        """Testa set_contestation_fee com valor válido"""
        with app.app_context():
            success, msg = ConfigService.set_contestation_fee(Decimal('15.00'), admin_id=1)
            
            assert success is True
            assert 'atualizada' in msg.lower()
            
            new_value = ConfigService.get_contestation_fee()
            assert new_value == Decimal('15.00')
    
    def test_set_contestation_fee_invalid_negative(self, client, init_configs):
        """Testa set_contestation_fee com valor negativo"""
        with app.app_context():
            success, msg = ConfigService.set_contestation_fee(Decimal('-10'), admin_id=1)
            
            assert success is False
            assert 'positivo' in msg.lower()
    
    def test_set_contestation_fee_invalid_zero(self, client, init_configs):
        """Testa set_contestation_fee com valor zero"""
        with app.app_context():
            success, msg = ConfigService.set_contestation_fee(Decimal('0'), admin_id=1)
            
            assert success is False
            assert 'positivo' in msg.lower()
    
    def test_set_cancellation_fee_percentage_valid(self, client, init_configs):
        """Testa set_cancellation_fee_percentage com valor válido"""
        with app.app_context():
            success, msg = ConfigService.set_cancellation_fee_percentage(Decimal('12.5'), admin_id=1)
            
            assert success is True
            assert 'atualizada' in msg.lower()
            
            new_value = ConfigService.get_cancellation_fee_percentage()
            assert new_value == Decimal('12.5')
    
    def test_set_cancellation_fee_percentage_invalid(self, client, init_configs):
        """Testa set_cancellation_fee_percentage com valor inválido"""
        with app.app_context():
            success, msg = ConfigService.set_cancellation_fee_percentage(Decimal('200'), admin_id=1)
            
            assert success is False
            assert '0%' in msg and '100%' in msg
    
    def test_set_config_generic(self, client, init_configs):
        """Testa set_config genérico"""
        with app.app_context():
            # Criar nova configuração
            success = ConfigService.set_config('test_key', 'test_value', 'test_category', 'Test description')
            assert success is True
            
            # Verificar se foi criada
            value = ConfigService.get_config('test_key')
            assert value == 'test_value'
            
            # Atualizar configuração existente
            success = ConfigService.set_config('test_key', 'new_value')
            assert success is True
            
            value = ConfigService.get_config('test_key')
            assert value == 'new_value'


class TestConfigServiceCache:
    """Testes do sistema de cache do ConfigService"""
    
    def test_cache_functionality(self, client, init_configs):
        """Testa que o cache funciona corretamente"""
        with app.app_context():
            # Primeira chamada - busca do banco
            value1 = ConfigService.get_platform_fee_percentage()
            
            # Segunda chamada - deve vir do cache
            value2 = ConfigService.get_platform_fee_percentage()
            
            assert value1 == value2
            
            # Verificar que está no cache
            assert 'platform_fee_percentage' in ConfigService._config_cache
    
    def test_cache_cleared_on_update(self, client, init_configs):
        """Testa que o cache é limpo ao atualizar"""
        with app.app_context():
            # Carregar no cache
            value1 = ConfigService.get_platform_fee_percentage()
            assert 'platform_fee_percentage' in ConfigService._config_cache
            
            # Atualizar valor
            ConfigService.set_platform_fee_percentage(Decimal('8.0'), admin_id=1)
            
            # Cache deve ter sido limpo
            # Próxima chamada deve buscar novo valor
            value2 = ConfigService.get_platform_fee_percentage()
            assert value2 == Decimal('8.0')
    
    def test_cache_ttl(self, client, init_configs):
        """Testa que o cache expira após TTL"""
        with app.app_context():
            # Carregar no cache
            value1 = ConfigService.get_platform_fee_percentage()
            
            # Simular expiração do cache (manipular timestamp)
            ConfigService._cache_timestamp['platform_fee_percentage'] = (
                datetime.utcnow().timestamp() - 400  # 400 segundos atrás (> 300s TTL)
            )
            
            # Próxima chamada deve buscar do banco novamente
            value2 = ConfigService.get_platform_fee_percentage()
            
            # Timestamp deve ter sido atualizado
            assert ConfigService._cache_timestamp['platform_fee_percentage'] > (
                datetime.utcnow().timestamp() - 10
            )


class TestConfigServiceBatchOperations:
    """Testes de operações em lote"""
    
    def test_update_configs_batch(self, client, init_configs):
        """Testa atualização em lote de configurações"""
        with app.app_context():
            configs = {
                'platform_fee_percentage': '6.0',
                'contestation_fee': '12.00',
                'cancellation_fee_percentage': '15.0'
            }
            
            success = ConfigService.update_configs_batch(configs)
            assert success is True
            
            # Verificar se foram atualizadas
            assert ConfigService.get_platform_fee_percentage() == Decimal('6.0')
            assert ConfigService.get_contestation_fee() == Decimal('12.00')
            assert ConfigService.get_cancellation_fee_percentage() == Decimal('15.0')
    
    def test_update_configs_batch_creates_new(self, client, init_configs):
        """Testa que update_configs_batch cria configurações inexistentes"""
        with app.app_context():
            configs = {
                'new_config_1': '100',
                'new_config_2': '200'
            }
            
            success = ConfigService.update_configs_batch(configs)
            assert success is True
            
            # Verificar se foram criadas
            value1 = ConfigService.get_config('new_config_1')
            value2 = ConfigService.get_config('new_config_2')
            
            assert value1 == 100
            assert value2 == 200
    
    def test_update_configs_batch_clears_cache(self, client, init_configs):
        """Testa que update_configs_batch limpa o cache"""
        with app.app_context():
            # Carregar no cache
            ConfigService.get_platform_fee_percentage()
            assert len(ConfigService._config_cache) > 0
            
            # Atualizar em lote
            configs = {'platform_fee_percentage': '7.0'}
            ConfigService.update_configs_batch(configs)
            
            # Cache deve ter sido limpo
            assert len(ConfigService._config_cache) == 0


class TestConfigServiceOrderTaxes:
    """Testes que verificam que ordens antigas mantêm taxas originais"""
    
    def test_orders_store_taxes_at_creation(self, client, init_configs):
        """Testa que ordens armazenam taxas vigentes na criação"""
        with app.app_context():
            # Criar usuários
            client_user = User(
                email='client@test.com',
                nome='Cliente Test',
                cpf='12345678901',
                phone='11999999999',
                roles='cliente'
            )
            client_user.set_password('password123')
            
            provider_user = User(
                email='provider@test.com',
                nome='Prestador Test',
                cpf='98765432100',
                phone='11888888888',
                roles='prestador'
            )
            provider_user.set_password('password123')
            
            db.session.add(client_user)
            db.session.add(provider_user)
            db.session.commit()
            
            # Criar carteiras
            client_wallet = Wallet(user_id=client_user.id, balance=Decimal('1000.00'))
            provider_wallet = Wallet(user_id=provider_user.id, balance=Decimal('1000.00'))
            db.session.add(client_wallet)
            db.session.add(provider_wallet)
            db.session.commit()
            
            # Obter taxas atuais
            current_fees = ConfigService.get_all_fees()
            
            # Criar ordem simulando o que OrderManagementService faz
            order = Order(
                client_id=client_user.id,
                provider_id=provider_user.id,
                title='Teste',
                description='Teste',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=current_fees['platform_fee_percentage'],
                contestation_fee_at_creation=current_fees['contestation_fee'],
                cancellation_fee_percentage_at_creation=current_fees['cancellation_fee_percentage']
            )
            db.session.add(order)
            db.session.commit()
            
            # Verificar que taxas foram armazenadas
            assert order.platform_fee_percentage_at_creation == Decimal('5.0')
            assert order.contestation_fee_at_creation == Decimal('10.00')
            assert order.cancellation_fee_percentage_at_creation == Decimal('10.0')
    
    def test_old_orders_maintain_original_taxes(self, client, init_configs):
        """Testa que ordens antigas mantêm taxas originais após mudança"""
        with app.app_context():
            # Criar usuários e carteiras
            client_user = User(
                email='client2@test.com',
                nome='Cliente Test 2',
                cpf='11111111111',
                phone='11777777777',
                roles='cliente'
            )
            client_user.set_password('password123')
            
            provider_user = User(
                email='provider2@test.com',
                nome='Prestador Test 2',
                cpf='22222222222',
                phone='11666666666',
                roles='prestador'
            )
            provider_user.set_password('password123')
            
            db.session.add(client_user)
            db.session.add(provider_user)
            db.session.commit()
            
            client_wallet = Wallet(user_id=client_user.id, balance=Decimal('1000.00'))
            provider_wallet = Wallet(user_id=provider_user.id, balance=Decimal('1000.00'))
            db.session.add(client_wallet)
            db.session.add(provider_wallet)
            db.session.commit()
            
            # Criar ordem com taxas atuais (5%, R$10, 10%)
            old_fees = ConfigService.get_all_fees()
            old_order = Order(
                client_id=client_user.id,
                provider_id=provider_user.id,
                title='Ordem Antiga',
                description='Teste',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=old_fees['platform_fee_percentage'],
                contestation_fee_at_creation=old_fees['contestation_fee'],
                cancellation_fee_percentage_at_creation=old_fees['cancellation_fee_percentage']
            )
            db.session.add(old_order)
            db.session.commit()
            old_order_id = old_order.id
            
            # Atualizar taxas do sistema
            ConfigService.set_platform_fee_percentage(Decimal('8.0'), admin_id=1)
            ConfigService.set_contestation_fee(Decimal('20.00'), admin_id=1)
            ConfigService.set_cancellation_fee_percentage(Decimal('15.0'), admin_id=1)
            
            # Verificar que taxas do sistema mudaram
            new_fees = ConfigService.get_all_fees()
            assert new_fees['platform_fee_percentage'] == Decimal('8.0')
            assert new_fees['contestation_fee'] == Decimal('20.00')
            assert new_fees['cancellation_fee_percentage'] == Decimal('15.0')
            
            # Verificar que ordem antiga mantém taxas originais
            old_order = Order.query.get(old_order_id)
            assert old_order.platform_fee_percentage_at_creation == Decimal('5.0')
            assert old_order.contestation_fee_at_creation == Decimal('10.00')
            assert old_order.cancellation_fee_percentage_at_creation == Decimal('10.0')
            
            # Criar nova ordem com taxas atualizadas
            new_order = Order(
                client_id=client_user.id,
                provider_id=provider_user.id,
                title='Ordem Nova',
                description='Teste',
                value=Decimal('100.00'),
                status='aguardando_execucao',
                service_deadline=datetime.utcnow() + timedelta(days=7),
                platform_fee_percentage_at_creation=new_fees['platform_fee_percentage'],
                contestation_fee_at_creation=new_fees['contestation_fee'],
                cancellation_fee_percentage_at_creation=new_fees['cancellation_fee_percentage']
            )
            db.session.add(new_order)
            db.session.commit()
            
            # Verificar que nova ordem usa taxas atualizadas
            assert new_order.platform_fee_percentage_at_creation == Decimal('8.0')
            assert new_order.contestation_fee_at_creation == Decimal('20.00')
            assert new_order.cancellation_fee_percentage_at_creation == Decimal('15.0')


class TestConfigServiceInitialization:
    """Testes de inicialização de configurações"""
    
    def test_initialize_default_configs(self, client):
        """Testa inicialização de configurações padrão"""
        with app.app_context():
            # Limpar configurações existentes
            SystemConfig.query.delete()
            db.session.commit()
            
            # Inicializar
            success = ConfigService.initialize_default_configs()
            assert success is True
            
            # Verificar que configurações foram criadas
            configs = SystemConfig.query.all()
            assert len(configs) > 0
            
            # Verificar configurações específicas
            platform_fee = SystemConfig.query.filter_by(key='platform_fee_percentage').first()
            assert platform_fee is not None
            assert platform_fee.value == '5.0'
            assert platform_fee.category == 'taxas'
    
    def test_initialize_default_configs_idempotent(self, client, init_configs):
        """Testa que inicialização é idempotente (não duplica)"""
        with app.app_context():
            # Contar configurações
            count_before = SystemConfig.query.count()
            
            # Inicializar novamente
            ConfigService.initialize_default_configs()
            
            # Contar novamente
            count_after = SystemConfig.query.count()
            
            # Não deve ter duplicado
            assert count_before == count_after


class TestConfigServiceEdgeCases:
    """Testes de casos extremos e edge cases"""
    
    def test_get_config_with_type_conversion(self, client, init_configs):
        """Testa conversão automática de tipos"""
        with app.app_context():
            # Boolean
            ConfigService.set_config('test_bool', 'true')
            value = ConfigService.get_config('test_bool')
            assert value is True
            
            ConfigService.set_config('test_bool', 'false')
            value = ConfigService.get_config('test_bool')
            assert value is False
            
            # Integer
            ConfigService.set_config('test_int', '42')
            value = ConfigService.get_config('test_int')
            assert value == 42
            assert isinstance(value, int)
            
            # Float
            ConfigService.set_config('test_float', '3.14')
            value = ConfigService.get_config('test_float')
            assert value == 3.14
            assert isinstance(value, float)
            
            # String
            ConfigService.set_config('test_string', 'hello world')
            value = ConfigService.get_config('test_string')
            assert value == 'hello world'
            assert isinstance(value, str)
    
    def test_set_platform_fee_boundary_values(self, client, init_configs):
        """Testa valores limites para taxa da plataforma"""
        with app.app_context():
            # Valor mínimo (0%)
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('0'), admin_id=1)
            assert success is True
            assert ConfigService.get_platform_fee_percentage() == Decimal('0')
            
            # Valor máximo (100%)
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('100'), admin_id=1)
            assert success is True
            assert ConfigService.get_platform_fee_percentage() == Decimal('100')
            
            # Valor decimal
            success, msg = ConfigService.set_platform_fee_percentage(Decimal('7.5'), admin_id=1)
            assert success is True
            assert ConfigService.get_platform_fee_percentage() == Decimal('7.5')
    
    def test_concurrent_cache_access(self, client, init_configs):
        """Testa acesso concorrente ao cache"""
        with app.app_context():
            # Simular múltiplas leituras
            values = []
            for _ in range(10):
                values.append(ConfigService.get_platform_fee_percentage())
            
            # Todos devem ser iguais
            assert all(v == values[0] for v in values)
            
            # Cache deve ter apenas uma entrada
            assert 'platform_fee_percentage' in ConfigService._config_cache


def run_all_tests():
    """Executa todos os testes com relatório detalhado"""
    print("=" * 80)
    print("TESTES DO CONFIGSERVICE - TAREFA 38")
    print("=" * 80)
    
    # Executar pytest com verbose
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes'
    ])


if __name__ == '__main__':
    run_all_tests()
