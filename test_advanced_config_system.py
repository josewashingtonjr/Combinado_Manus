#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do Sistema de Configurações Avançadas
Valida todas as funcionalidades implementadas na tarefa 10.2
"""

import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from app import app
from models import db, SystemConfig, SystemBackup, LoginAttempt, SystemAlert
from services.config_service import ConfigService, BackupService, SecurityService, MonitoringService

class TestAdvancedConfigSystem(unittest.TestCase):
    """Testes para o sistema de configurações avançadas"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_config_service_initialization(self):
        """Testar inicialização das configurações padrão"""
        with self.app.app_context():
            # Inicializar configurações
            success = ConfigService.initialize_default_configs()
            self.assertTrue(success)
            
            # Verificar se configurações foram criadas
            total_configs = SystemConfig.query.count()
            self.assertGreater(total_configs, 0)
            
            # Verificar configurações específicas
            taxa_transacao = ConfigService.get_config('taxa_transacao')
            self.assertEqual(taxa_transacao, 5.0)
            
            backup_automatico = ConfigService.get_config('backup_automatico')
            self.assertTrue(backup_automatico)
    
    def test_config_service_crud_operations(self):
        """Testar operações CRUD do ConfigService"""
        with self.app.app_context():
            # Criar configuração
            success = ConfigService.set_config('test_config', 'test_value', 'test', 'Configuração de teste')
            self.assertTrue(success)
            
            # Ler configuração
            value = ConfigService.get_config('test_config')
            self.assertEqual(value, 'test_value')
            
            # Atualizar configuração
            success = ConfigService.set_config('test_config', 'new_value')
            self.assertTrue(success)
            
            updated_value = ConfigService.get_config('test_config')
            self.assertEqual(updated_value, 'new_value')
            
            # Testar configurações por categoria
            configs = ConfigService.get_configs_by_category('test')
            self.assertIn('test_config', configs)
    
    def test_config_service_batch_update(self):
        """Testar atualização em lote de configurações"""
        with self.app.app_context():
            # Configurações para atualizar
            configs = {
                'taxa_transacao': 7.5,
                'taxa_saque': 3.0,
                'backup_automatico': 'false',
                'max_tentativas_login': 3
            }
            
            # Atualizar em lote
            success = ConfigService.update_configs_batch(configs)
            self.assertTrue(success)
            
            # Verificar se foram atualizadas
            self.assertEqual(ConfigService.get_config('taxa_transacao'), 7.5)
            self.assertEqual(ConfigService.get_config('taxa_saque'), 3.0)
            self.assertEqual(ConfigService.get_config('backup_automatico'), False)
            self.assertEqual(ConfigService.get_config('max_tentativas_login'), 3)
    
    def test_backup_service_creation(self):
        """Testar criação de backups"""
        with self.app.app_context():
            # Criar backup de carteiras (deve funcionar mesmo sem dados)
            backup = BackupService.create_backup('wallets')
            self.assertIsNotNone(backup)
            self.assertIsInstance(backup, SystemBackup)
            self.assertEqual(backup.backup_type, 'wallets')
            
            # Verificar se foi registrado no banco
            backup_count = SystemBackup.query.count()
            self.assertEqual(backup_count, 1)
    
    def test_backup_service_status(self):
        """Testar status do sistema de backup"""
        with self.app.app_context():
            # Criar alguns backups
            BackupService.create_backup('wallets')
            BackupService.create_backup('transactions')
            
            # Obter status
            status = BackupService.get_backup_status()
            
            self.assertIn('total_backups', status)
            self.assertIn('recent_backups', status)
            self.assertIn('last_backup', status)
            self.assertIn('backup_enabled', status)
            
            self.assertEqual(status['total_backups'], 2)
            self.assertIsNotNone(status['last_backup'])
    
    def test_security_service_login_attempts(self):
        """Testar controle de tentativas de login"""
        with self.app.app_context():
            email = 'test@example.com'
            ip = '192.168.1.1'
            user_agent = 'Test Browser'
            
            # Registrar tentativas falhadas
            for i in range(3):
                SecurityService.log_login_attempt(email, ip, user_agent, False)
            
            # Verificar tentativas
            attempts_info = SecurityService.check_login_attempts(email, ip)
            
            self.assertEqual(attempts_info['failed_attempts'], 3)
            self.assertEqual(attempts_info['remaining_attempts'], 2)  # max_attempts padrão é 5
            self.assertFalse(attempts_info['is_blocked'])
            
            # Adicionar mais tentativas para bloquear
            for i in range(3):
                SecurityService.log_login_attempt(email, ip, user_agent, False)
            
            attempts_info = SecurityService.check_login_attempts(email, ip)
            self.assertTrue(attempts_info['is_blocked'])
    
    def test_security_service_statistics(self):
        """Testar estatísticas de segurança"""
        with self.app.app_context():
            # Criar algumas tentativas de login
            SecurityService.log_login_attempt('user1@test.com', '192.168.1.1', 'Browser', True)
            SecurityService.log_login_attempt('user2@test.com', '192.168.1.2', 'Browser', False)
            SecurityService.log_login_attempt('user3@test.com', '192.168.1.3', 'Browser', True)
            
            # Obter estatísticas
            stats = SecurityService.get_security_stats()
            
            self.assertIn('total_attempts_24h', stats)
            self.assertIn('failed_attempts_24h', stats)
            self.assertIn('success_attempts_24h', stats)
            self.assertIn('success_rate', stats)
            self.assertIn('unique_ips_24h', stats)
            
            self.assertEqual(stats['total_attempts_24h'], 3)
            self.assertEqual(stats['failed_attempts_24h'], 1)
            self.assertEqual(stats['success_attempts_24h'], 2)
    
    def test_monitoring_service_alerts(self):
        """Testar sistema de alertas"""
        with self.app.app_context():
            # Criar alerta
            alert = MonitoringService.create_alert(
                alert_type='test_alert',
                severity='high',
                title='Alerta de Teste',
                message='Este é um alerta de teste',
                data={'test_key': 'test_value'}
            )
            
            self.assertIsNotNone(alert)
            self.assertEqual(alert.alert_type, 'test_alert')
            self.assertEqual(alert.severity, 'high')
            self.assertFalse(alert.resolved)
            
            # Obter alertas não resolvidos
            unresolved_alerts = MonitoringService.get_system_alerts(resolved=False)
            self.assertEqual(len(unresolved_alerts), 1)
            
            # Resolver alerta
            success = MonitoringService.resolve_alert(alert.id, 1)
            self.assertTrue(success)
            
            # Verificar se foi resolvido
            resolved_alerts = MonitoringService.get_system_alerts(resolved=True)
            self.assertEqual(len(resolved_alerts), 1)
    
    def test_monitoring_service_health_check(self):
        """Testar verificação de saúde do sistema"""
        with self.app.app_context():
            # Executar verificação de saúde
            health = MonitoringService.check_system_health()
            
            self.assertIn('overall_status', health)
            self.assertIn('checks', health)
            self.assertIn('alerts', health)
            
            # Verificar se tem as verificações básicas
            checks = health['checks']
            self.assertIn('wallet_integrity', checks)
            self.assertIn('backup', checks)
            self.assertIn('alerts', checks)
    
    def test_admin_routes_integration(self):
        """Testar integração com rotas administrativas"""
        with self.app.app_context():
            # Inicializar configurações
            ConfigService.initialize_default_configs()
            
            # Testar rota de configurações
            response = self.client.get('/admin/configuracoes')
            # Deve retornar 302 (redirect para login) pois não estamos autenticados
            self.assertIn(response.status_code, [200, 302])
            
            # Testar rota de status de backup
            response = self.client.get('/admin/backup/status')
            self.assertIn(response.status_code, [200, 302])
            
            # Testar rota de estatísticas de segurança
            response = self.client.get('/admin/seguranca/estatisticas')
            self.assertIn(response.status_code, [200, 302])
    
    def test_configuration_categories(self):
        """Testar todas as categorias de configuração"""
        with self.app.app_context():
            ConfigService.initialize_default_configs()
            
            # Testar cada categoria
            categories = ['taxas', 'multas', 'seguranca', 'backup', 'monitoramento']
            
            for category in categories:
                configs = ConfigService.get_configs_by_category(category)
                self.assertGreater(len(configs), 0, f'Categoria {category} deve ter configurações')
    
    def test_backup_cleanup(self):
        """Testar limpeza de backups antigos"""
        with self.app.app_context():
            # Criar backup antigo (simular)
            old_backup = SystemBackup(
                backup_type='test',
                file_path='/tmp/old_backup.json',
                file_size=1000,
                status='completed'
            )
            # Definir data antiga
            old_backup.created_at = datetime.utcnow() - timedelta(days=35)
            db.session.add(old_backup)
            
            # Criar backup recente
            recent_backup = SystemBackup(
                backup_type='test',
                file_path='/tmp/recent_backup.json',
                file_size=1000,
                status='completed'
            )
            db.session.add(recent_backup)
            db.session.commit()
            
            # Executar limpeza
            cleaned_count = BackupService.cleanup_old_backups()
            
            # Verificar se backup antigo foi removido
            remaining_backups = SystemBackup.query.count()
            self.assertEqual(remaining_backups, 1)
    
    def test_type_conversion(self):
        """Testar conversão automática de tipos nas configurações"""
        with self.app.app_context():
            # Testar diferentes tipos
            ConfigService.set_config('test_float', '3.14')
            ConfigService.set_config('test_int', '42')
            ConfigService.set_config('test_bool_true', 'true')
            ConfigService.set_config('test_bool_false', 'false')
            ConfigService.set_config('test_string', 'hello world')
            
            # Verificar conversões
            self.assertEqual(ConfigService.get_config('test_float'), 3.14)
            self.assertEqual(ConfigService.get_config('test_int'), 42)
            self.assertEqual(ConfigService.get_config('test_bool_true'), True)
            self.assertEqual(ConfigService.get_config('test_bool_false'), False)
            self.assertEqual(ConfigService.get_config('test_string'), 'hello world')


def run_tests():
    """Executar todos os testes"""
    print("🧪 Executando testes do Sistema de Configurações Avançadas...")
    print("=" * 70)
    
    # Criar suite de testes
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdvancedConfigSystem)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo dos resultados
    print("\n" + "=" * 70)
    print(f"📊 RESUMO DOS TESTES:")
    print(f"   ✅ Testes executados: {result.testsRun}")
    print(f"   ❌ Falhas: {len(result.failures)}")
    print(f"   🚫 Erros: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ FALHAS:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"   - {test}: {error_msg}")
    
    if result.errors:
        print(f"\n🚫 ERROS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"   - {test}: {error_msg}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n🎉 TODOS OS TESTES PASSARAM!")
        print(f"✅ Sistema de Configurações Avançadas implementado com sucesso!")
    else:
        print(f"\n⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    return success


if __name__ == '__main__':
    run_tests()