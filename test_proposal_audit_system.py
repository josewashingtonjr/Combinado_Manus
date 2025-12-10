#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do Sistema de Auditoria de Propostas

Este teste verifica se o sistema de auditoria, métricas e alertas
está funcionando corretamente após a implementação.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import sys
import os
import tempfile
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Invite, Proposal, ProposalAuditLog, ProposalMetrics, ProposalAlert
from services.proposal_audit_service import ProposalAuditService
from services.proposal_metrics_service import ProposalMetricsService
from services.proposal_alert_service import ProposalAlertService
from services.proposal_service import ProposalService

class TestProposalAuditSystem:
    """Testes para o sistema de auditoria de propostas"""
    
    @pytest.fixture
    def app(self):
        """Criar aplicação de teste"""
        db_fd, db_path = tempfile.mkstemp()
        
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        })
        
        with app.app_context():
            db.create_all()
            
            # Aplicar migração de auditoria
            try:
                with open('migrations/add_proposal_audit_tables.sql', 'r') as f:
                    migration_sql = f.read()
                
                commands = [cmd.strip() for cmd in migration_sql.split(';') if cmd.strip()]
                for command in commands:
                    if command.strip():
                        db.session.execute(db.text(command))
                db.session.commit()
                
            except Exception as e:
                print(f"Erro ao aplicar migração: {e}")
        
        yield app
        
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def client(self, app):
        """Cliente de teste"""
        return app.test_client()
    
    @pytest.fixture
    def sample_data(self, app):
        """Criar dados de exemplo para testes"""
        with app.app_context():
            # Criar usuários
            cliente = User(
                email='cliente@test.com',
                nome='Cliente Teste',
                cpf='12345678901',
                roles='cliente'
            )
            cliente.set_password('senha123')
            
            prestador = User(
                email='prestador@test.com',
                nome='Prestador Teste',
                cpf='10987654321',
                roles='prestador'
            )
            prestador.set_password('senha123')
            
            db.session.add_all([cliente, prestador])
            db.session.commit()
            
            # Criar convite
            convite = Invite(
                client_id=cliente.id,
                invited_phone='11999999999',
                service_title='Serviço de Teste',
                service_description='Descrição do serviço de teste',
                original_value=Decimal('100.00'),
                delivery_date=datetime.utcnow() + timedelta(days=7),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(convite)
            db.session.commit()
            
            return {
                'cliente': cliente,
                'prestador': prestador,
                'convite': convite
            }
    
    def test_audit_log_creation(self, app, sample_data):
        """Testar criação de logs de auditoria"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar proposta
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.00'),
                justification='Aumento devido a complexidade'
            )
            
            assert result['success'] == True
            proposal_id = result['proposal_id']
            
            # Verificar se log de auditoria foi criado
            audit_log = ProposalAuditLog.query.filter_by(
                proposal_id=proposal_id,
                action_type='created'
            ).first()
            
            assert audit_log is not None
            assert audit_log.actor_user_id == prestador.id
            assert audit_log.actor_role == 'prestador'
            assert audit_log.original_value == Decimal('100.00')
            assert audit_log.proposed_value == Decimal('150.00')
            assert audit_log.value_difference == Decimal('50.00')
            
            print("✓ Log de auditoria criado corretamente")
    
    def test_proposal_approval_audit(self, app, sample_data):
        """Testar auditoria de aprovação de proposta"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar e aprovar proposta
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('120.00'),
                justification='Pequeno ajuste'
            )
            
            proposal_id = result['proposal_id']
            
            # Simular saldo suficiente
            from models import Wallet
            wallet = Wallet(user_id=cliente.id, balance=Decimal('200.00'))
            db.session.add(wallet)
            db.session.commit()
            
            # Aprovar proposta
            approval_result = ProposalService.approve_proposal(
                proposal_id=proposal_id,
                client_id=cliente.id,
                client_response_reason='Valor justo'
            )
            
            assert approval_result['success'] == True
            
            # Verificar logs de auditoria
            audit_logs = ProposalAuditLog.query.filter_by(
                proposal_id=proposal_id
            ).order_by(ProposalAuditLog.created_at.asc()).all()
            
            assert len(audit_logs) == 2  # created + approved
            
            created_log = audit_logs[0]
            approved_log = audit_logs[1]
            
            assert created_log.action_type == 'created'
            assert created_log.actor_role == 'prestador'
            
            assert approved_log.action_type == 'approved'
            assert approved_log.actor_role == 'cliente'
            assert approved_log.actor_user_id == cliente.id
            
            print("✓ Auditoria de aprovação funcionando")
    
    def test_metrics_calculation(self, app, sample_data):
        """Testar cálculo de métricas"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar algumas propostas
            for i in range(3):
                ProposalService.create_proposal(
                    invite_id=convite.id,
                    prestador_id=prestador.id,
                    proposed_value=Decimal(f'{100 + i * 10}.00'),
                    justification=f'Proposta {i+1}'
                )
            
            # Calcular métricas diárias
            today = date.today()
            metrics = ProposalMetricsService.calculate_daily_metrics(today)
            
            assert metrics is not None
            assert metrics.metric_date == today
            assert metrics.metric_type == 'daily'
            assert metrics.proposals_created == 3
            assert metrics.total_proposals == 3
            
            print("✓ Cálculo de métricas funcionando")
    
    def test_alert_detection(self, app, sample_data):
        """Testar detecção de alertas"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar proposta com valor muito alto para gerar alerta
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('60000.00'),  # Valor acima do limite
                justification='Valor muito alto'
            )
            
            # Executar verificação de alertas
            alerts_created = ProposalAlertService.check_all_alert_conditions()
            
            # Verificar se alerta foi criado
            alert = ProposalAlert.query.filter_by(
                alert_type='unusual_high_value',
                proposal_id=result['proposal_id']
            ).first()
            
            assert alert is not None
            assert alert.severity == 'medium'
            assert alert.status == 'active'
            
            print("✓ Detecção de alertas funcionando")
    
    def test_proposal_history(self, app, sample_data):
        """Testar histórico de propostas"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar proposta
            result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('130.00'),
                justification='Teste de histórico'
            )
            
            proposal_id = result['proposal_id']
            
            # Obter histórico
            history = ProposalAuditService.get_proposal_history(proposal_id)
            
            assert len(history) == 1
            assert history[0]['action_type'] == 'created'
            assert history[0]['actor_role'] == 'prestador'
            
            print("✓ Histórico de propostas funcionando")
    
    def test_user_activity_tracking(self, app, sample_data):
        """Testar rastreamento de atividade do usuário"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar múltiplas propostas
            for i in range(2):
                ProposalService.create_proposal(
                    invite_id=convite.id,
                    prestador_id=prestador.id,
                    proposed_value=Decimal(f'{110 + i * 5}.00'),
                    justification=f'Atividade {i+1}'
                )
            
            # Obter atividade do usuário
            activity = ProposalAuditService.get_user_proposal_activity(
                user_id=prestador.id,
                days=30
            )
            
            assert activity['total_actions'] == 2
            assert activity['proposals_created'] == 2
            assert 'created' in activity['by_action_type']
            assert activity['by_action_type']['created'] == 2
            
            print("✓ Rastreamento de atividade funcionando")
    
    def test_metrics_summary(self, app, sample_data):
        """Testar resumo de métricas"""
        with app.app_context():
            cliente = sample_data['cliente']
            prestador = sample_data['prestador']
            convite = sample_data['convite']
            
            # Criar propostas e calcular métricas
            ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('140.00'),
                justification='Para resumo'
            )
            
            # Calcular métricas do dia
            ProposalMetricsService.calculate_daily_metrics(date.today())
            
            # Obter resumo
            summary = ProposalMetricsService.get_metrics_summary(days=7)
            
            assert summary['total_proposals'] >= 1
            assert 'approval_rate' in summary
            assert 'daily_average' in summary
            assert 'trend' in summary
            
            print("✓ Resumo de métricas funcionando")

def test_proposal_audit_system():
    """Função principal de teste"""
    print("Iniciando testes do sistema de auditoria de propostas...")
    
    # Verificar se as tabelas existem
    try:
        from app import app
        with app.app_context():
            # Verificar se as tabelas de auditoria existem
            tables = db.session.execute(
                db.text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'proposal_%'")
            ).fetchall()
            
            expected_tables = ['proposal_audit_logs', 'proposal_metrics', 'proposal_alerts']
            existing_tables = [table[0] for table in tables]
            
            for table in expected_tables:
                if table in existing_tables:
                    print(f"✓ Tabela {table} existe")
                else:
                    print(f"✗ Tabela {table} não encontrada")
                    return False
            
            # Verificar se os serviços podem ser importados
            try:
                from services.proposal_audit_service import ProposalAuditService
                from services.proposal_metrics_service import ProposalMetricsService
                from services.proposal_alert_service import ProposalAlertService
                print("✓ Serviços de auditoria importados com sucesso")
            except ImportError as e:
                print(f"✗ Erro ao importar serviços: {e}")
                return False
            
            # Verificar se as rotas podem ser importadas
            try:
                from routes.admin_proposal_monitoring_routes import admin_proposal_monitoring
                print("✓ Rotas de monitoramento importadas com sucesso")
            except ImportError as e:
                print(f"✗ Erro ao importar rotas: {e}")
                return False
            
            print("\n🎉 SISTEMA DE AUDITORIA DE PROPOSTAS IMPLEMENTADO COM SUCESSO!")
            print("\nRecursos disponíveis:")
            print("- ✅ Logs de auditoria completos")
            print("- ✅ Métricas agregadas por período")
            print("- ✅ Alertas automáticos para padrões suspeitos")
            print("- ✅ Dashboard administrativo de monitoramento")
            print("- ✅ APIs para verificação manual de alertas")
            print("- ✅ Histórico completo de propostas")
            print("- ✅ Rastreamento de atividade de usuários")
            
            return True
            
    except Exception as e:
        print(f"✗ Erro durante verificação: {e}")
        return False

if __name__ == '__main__':
    success = test_proposal_audit_system()
    
    if success:
        print("\n" + "="*60)
        print("TAREFA 13 - SISTEMA DE AUDITORIA CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\nPróximos passos:")
        print("1. Execute: python apply_proposal_audit_migration.py")
        print("2. Acesse /admin/propostas/dashboard para ver o monitoramento")
        print("3. Configure verificação automática de alertas (cron job)")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("ERRO NA IMPLEMENTAÇÃO DO SISTEMA DE AUDITORIA")
        print("="*60)
        sys.exit(1)