#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Alertas de Propostas

Este serviço gerencia alertas sobre padrões suspeitos e anomalias no sistema de propostas,
incluindo detecção automática, notificação de administradores e resolução de alertas.

Requirements: 8.4, 8.5
"""

from models import db, ProposalAlert, Proposal, ProposalAuditLog, User, AdminUser
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Logger para alertas
alert_logger = logging.getLogger('proposal_alerts')


class AlertSeverity(Enum):
    """Níveis de severidade dos alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status dos alertas"""
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class AlertThreshold:
    """Define limites para detecção de alertas"""
    name: str
    value: Any
    description: str
    severity: AlertSeverity


class ProposalAlertService:
    """Serviço principal para gerenciamento de alertas de propostas"""
    
    # Configuração de limites para alertas
    ALERT_THRESHOLDS = {
        # Frequência de propostas
        'max_proposals_per_hour_user': AlertThreshold(
            'max_proposals_per_hour_user', 5,
            'Máximo de propostas por usuário por hora', AlertSeverity.MEDIUM
        ),
        'max_proposals_per_day_user': AlertThreshold(
            'max_proposals_per_day_user', 20,
            'Máximo de propostas por usuário por dia', AlertSeverity.HIGH
        ),
        
        # Valores suspeitos
        'max_value_increase_percentage': AlertThreshold(
            'max_value_increase_percentage', 300,
            'Aumento máximo de valor em percentual', AlertSeverity.HIGH
        ),
        'unusual_high_value': AlertThreshold(
            'unusual_high_value', Decimal('50000.00'),
            'Valor considerado muito alto', AlertSeverity.MEDIUM
        ),
        
        # Comportamento de resposta
        'min_response_time_seconds': AlertThreshold(
            'min_response_time_seconds', 60,
            'Tempo mínimo para resposta (muito rápido é suspeito)', AlertSeverity.MEDIUM
        ),
        'max_rejection_rate_percentage': AlertThreshold(
            'max_rejection_rate_percentage', 90,
            'Taxa máxima de rejeição por cliente', AlertSeverity.MEDIUM
        ),
        
        # Padrões sistêmicos
        'system_proposal_spike_percentage': AlertThreshold(
            'system_proposal_spike_percentage', 200,
            'Aumento percentual de propostas no sistema', AlertSeverity.HIGH
        ),
        'system_high_rejection_rate': AlertThreshold(
            'system_high_rejection_rate', 70,
            'Taxa alta de rejeição no sistema', AlertSeverity.MEDIUM
        )
    }
    
    @staticmethod
    def check_all_alert_conditions():
        """
        Executa verificação completa de todas as condições de alerta
        
        Este método deve ser executado periodicamente (ex: a cada hora)
        para detectar padrões suspeitos no sistema.
        """
        try:
            alert_logger.info("Iniciando verificação de alertas do sistema")
            
            alerts_created = 0
            
            # 1. Verificar alertas de usuários individuais
            alerts_created += ProposalAlertService._check_user_frequency_alerts()
            alerts_created += ProposalAlertService._check_user_behavior_alerts()
            
            # 2. Verificar alertas sistêmicos
            alerts_created += ProposalAlertService._check_system_alerts()
            
            # 3. Verificar alertas de valores suspeitos
            alerts_created += ProposalAlertService._check_value_alerts()
            
            # 4. Limpar alertas antigos resolvidos
            ProposalAlertService._cleanup_old_alerts()
            
            alert_logger.info(f"Verificação concluída. {alerts_created} novos alertas criados.")
            
            return alerts_created
            
        except Exception as e:
            alert_logger.error(f"Erro na verificação de alertas: {str(e)}")
            raise
    
    @staticmethod
    def _check_user_frequency_alerts() -> int:
        """Verifica alertas de frequência de propostas por usuário"""
        alerts_created = 0
        now = datetime.utcnow()
        
        # Verificar propostas na última hora
        hour_ago = now - timedelta(hours=1)
        
        # Buscar usuários com muitas propostas na última hora
        frequent_users_hour = db.session.query(
            ProposalAuditLog.actor_user_id,
            func.count(ProposalAuditLog.id).label('proposal_count')
        ).filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                ProposalAuditLog.created_at >= hour_ago,
                ProposalAuditLog.actor_user_id.isnot(None)
            )
        ).group_by(
            ProposalAuditLog.actor_user_id
        ).having(
            func.count(ProposalAuditLog.id) > ProposalAlertService.ALERT_THRESHOLDS['max_proposals_per_hour_user'].value
        ).all()
        
        for user_id, count in frequent_users_hour:
            # Verificar se já existe alerta ativo para este usuário
            existing_alert = ProposalAlert.query.filter(
                and_(
                    ProposalAlert.alert_type == 'high_frequency_proposals_hour',
                    ProposalAlert.user_id == user_id,
                    ProposalAlert.status == 'active',
                    ProposalAlert.created_at >= hour_ago
                )
            ).first()
            
            if not existing_alert:
                ProposalAlertService._create_alert(
                    alert_type='high_frequency_proposals_hour',
                    severity='medium',
                    title=f'Usuário criou {count} propostas na última hora',
                    description=f'Usuário {user_id} excedeu o limite de propostas por hora ({count} > {ProposalAlertService.ALERT_THRESHOLDS["max_proposals_per_hour_user"].value})',
                    user_id=user_id,
                    pattern_data={
                        'proposals_count': count,
                        'time_period': 'last_hour',
                        'threshold': ProposalAlertService.ALERT_THRESHOLDS['max_proposals_per_hour_user'].value
                    },
                    threshold_exceeded='max_proposals_per_hour_user'
                )
                alerts_created += 1
        
        # Verificar propostas no último dia
        day_ago = now - timedelta(days=1)
        
        frequent_users_day = db.session.query(
            ProposalAuditLog.actor_user_id,
            func.count(ProposalAuditLog.id).label('proposal_count')
        ).filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                ProposalAuditLog.created_at >= day_ago,
                ProposalAuditLog.actor_user_id.isnot(None)
            )
        ).group_by(
            ProposalAuditLog.actor_user_id
        ).having(
            func.count(ProposalAuditLog.id) > ProposalAlertService.ALERT_THRESHOLDS['max_proposals_per_day_user'].value
        ).all()
        
        for user_id, count in frequent_users_day:
            existing_alert = ProposalAlert.query.filter(
                and_(
                    ProposalAlert.alert_type == 'high_frequency_proposals_day',
                    ProposalAlert.user_id == user_id,
                    ProposalAlert.status == 'active',
                    ProposalAlert.created_at >= day_ago
                )
            ).first()
            
            if not existing_alert:
                ProposalAlertService._create_alert(
                    alert_type='high_frequency_proposals_day',
                    severity='high',
                    title=f'Usuário criou {count} propostas no último dia',
                    description=f'Usuário {user_id} excedeu o limite de propostas por dia ({count} > {ProposalAlertService.ALERT_THRESHOLDS["max_proposals_per_day_user"].value})',
                    user_id=user_id,
                    pattern_data={
                        'proposals_count': count,
                        'time_period': 'last_day',
                        'threshold': ProposalAlertService.ALERT_THRESHOLDS['max_proposals_per_day_user'].value
                    },
                    threshold_exceeded='max_proposals_per_day_user'
                )
                alerts_created += 1
        
        return alerts_created
    
    @staticmethod
    def _check_user_behavior_alerts() -> int:
        """Verifica alertas de comportamento suspeito de usuários"""
        alerts_created = 0
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Verificar usuários com alta taxa de rejeição
        rejection_stats = db.session.query(
            ProposalAuditLog.actor_user_id,
            func.count(func.case([(ProposalAuditLog.action_type == 'approved', 1)])).label('approved_count'),
            func.count(func.case([(ProposalAuditLog.action_type == 'rejected', 1)])).label('rejected_count'),
            func.count(ProposalAuditLog.id).label('total_responses')
        ).filter(
            and_(
                ProposalAuditLog.actor_role == 'cliente',
                ProposalAuditLog.action_type.in_(['approved', 'rejected']),
                ProposalAuditLog.created_at >= thirty_days_ago,
                ProposalAuditLog.actor_user_id.isnot(None)
            )
        ).group_by(
            ProposalAuditLog.actor_user_id
        ).having(
            func.count(ProposalAuditLog.id) >= 5  # Mínimo de 5 respostas para considerar
        ).all()
        
        for user_id, approved, rejected, total in rejection_stats:
            rejection_rate = (rejected / total) * 100 if total > 0 else 0
            
            if rejection_rate > ProposalAlertService.ALERT_THRESHOLDS['max_rejection_rate_percentage'].value:
                # Verificar se já existe alerta ativo
                existing_alert = ProposalAlert.query.filter(
                    and_(
                        ProposalAlert.alert_type == 'high_rejection_rate',
                        ProposalAlert.user_id == user_id,
                        ProposalAlert.status == 'active',
                        ProposalAlert.created_at >= thirty_days_ago
                    )
                ).first()
                
                if not existing_alert:
                    ProposalAlertService._create_alert(
                        alert_type='high_rejection_rate',
                        severity='medium',
                        title=f'Cliente com alta taxa de rejeição: {rejection_rate:.1f}%',
                        description=f'Cliente {user_id} tem taxa de rejeição de {rejection_rate:.1f}% ({rejected}/{total} propostas) nos últimos 30 dias',
                        user_id=user_id,
                        pattern_data={
                            'rejection_rate': rejection_rate,
                            'rejected_count': rejected,
                            'total_responses': total,
                            'period_days': 30,
                            'threshold': ProposalAlertService.ALERT_THRESHOLDS['max_rejection_rate_percentage'].value
                        },
                        threshold_exceeded='max_rejection_rate_percentage'
                    )
                    alerts_created += 1
        
        # Verificar respostas muito rápidas
        fast_responses = db.session.query(Proposal).filter(
            and_(
                Proposal.responded_at.isnot(None),
                Proposal.created_at.isnot(None),
                Proposal.responded_at >= now - timedelta(hours=24)  # Últimas 24 horas
            )
        ).all()
        
        for proposal in fast_responses:
            response_time = proposal.responded_at - proposal.created_at
            response_seconds = response_time.total_seconds()
            
            if response_seconds < ProposalAlertService.ALERT_THRESHOLDS['min_response_time_seconds'].value:
                existing_alert = ProposalAlert.query.filter(
                    and_(
                        ProposalAlert.alert_type == 'very_fast_response',
                        ProposalAlert.proposal_id == proposal.id,
                        ProposalAlert.status == 'active'
                    )
                ).first()
                
                if not existing_alert:
                    ProposalAlertService._create_alert(
                        alert_type='very_fast_response',
                        severity='medium',
                        title=f'Resposta muito rápida: {response_seconds:.0f} segundos',
                        description=f'Proposta {proposal.id} foi respondida em {response_seconds:.0f} segundos, abaixo do limite de {ProposalAlertService.ALERT_THRESHOLDS["min_response_time_seconds"].value} segundos',
                        proposal_id=proposal.id,
                        invite_id=proposal.invite_id,
                        pattern_data={
                            'response_time_seconds': response_seconds,
                            'threshold': ProposalAlertService.ALERT_THRESHOLDS['min_response_time_seconds'].value,
                            'created_at': proposal.created_at.isoformat(),
                            'responded_at': proposal.responded_at.isoformat()
                        },
                        threshold_exceeded='min_response_time_seconds'
                    )
                    alerts_created += 1
        
        return alerts_created
    
    @staticmethod
    def _check_system_alerts() -> int:
        """Verifica alertas sistêmicos"""
        alerts_created = 0
        now = datetime.utcnow()
        
        # Verificar pico de propostas no sistema
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Contar propostas hoje vs média da semana passada
        proposals_today = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                func.date(ProposalAuditLog.created_at) == today
            )
        ).count()
        
        proposals_last_week = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                func.date(ProposalAuditLog.created_at) >= week_ago,
                func.date(ProposalAuditLog.created_at) < today
            )
        ).count()
        
        avg_daily_last_week = proposals_last_week / 7 if proposals_last_week > 0 else 1
        
        if avg_daily_last_week > 0:
            increase_percentage = ((proposals_today - avg_daily_last_week) / avg_daily_last_week) * 100
            
            if increase_percentage > ProposalAlertService.ALERT_THRESHOLDS['system_proposal_spike_percentage'].value:
                existing_alert = ProposalAlert.query.filter(
                    and_(
                        ProposalAlert.alert_type == 'system_proposal_spike',
                        ProposalAlert.status == 'active',
                        func.date(ProposalAlert.created_at) == today
                    )
                ).first()
                
                if not existing_alert:
                    ProposalAlertService._create_alert(
                        alert_type='system_proposal_spike',
                        severity='high',
                        title=f'Pico de propostas no sistema: {increase_percentage:.1f}% de aumento',
                        description=f'Sistema registrou {proposals_today} propostas hoje vs média de {avg_daily_last_week:.1f} da semana passada ({increase_percentage:.1f}% de aumento)',
                        pattern_data={
                            'proposals_today': proposals_today,
                            'avg_daily_last_week': avg_daily_last_week,
                            'increase_percentage': increase_percentage,
                            'threshold': ProposalAlertService.ALERT_THRESHOLDS['system_proposal_spike_percentage'].value
                        },
                        threshold_exceeded='system_proposal_spike_percentage'
                    )
                    alerts_created += 1
        
        # Verificar alta taxa de rejeição sistêmica
        last_24h = now - timedelta(hours=24)
        
        system_responses = db.session.query(
            func.count(func.case([(ProposalAuditLog.action_type == 'approved', 1)])).label('approved'),
            func.count(func.case([(ProposalAuditLog.action_type == 'rejected', 1)])).label('rejected'),
            func.count(ProposalAuditLog.id).label('total')
        ).filter(
            and_(
                ProposalAuditLog.action_type.in_(['approved', 'rejected']),
                ProposalAuditLog.created_at >= last_24h
            )
        ).first()
        
        if system_responses and system_responses.total >= 10:  # Mínimo de respostas
            system_rejection_rate = (system_responses.rejected / system_responses.total) * 100
            
            if system_rejection_rate > ProposalAlertService.ALERT_THRESHOLDS['system_high_rejection_rate'].value:
                existing_alert = ProposalAlert.query.filter(
                    and_(
                        ProposalAlert.alert_type == 'system_high_rejection_rate',
                        ProposalAlert.status == 'active',
                        ProposalAlert.created_at >= last_24h
                    )
                ).first()
                
                if not existing_alert:
                    ProposalAlertService._create_alert(
                        alert_type='system_high_rejection_rate',
                        severity='medium',
                        title=f'Alta taxa de rejeição sistêmica: {system_rejection_rate:.1f}%',
                        description=f'Sistema tem taxa de rejeição de {system_rejection_rate:.1f}% nas últimas 24h ({system_responses.rejected}/{system_responses.total} propostas)',
                        pattern_data={
                            'rejection_rate': system_rejection_rate,
                            'rejected_count': system_responses.rejected,
                            'total_responses': system_responses.total,
                            'period_hours': 24,
                            'threshold': ProposalAlertService.ALERT_THRESHOLDS['system_high_rejection_rate'].value
                        },
                        threshold_exceeded='system_high_rejection_rate'
                    )
                    alerts_created += 1
        
        return alerts_created
    
    @staticmethod
    def _check_value_alerts() -> int:
        """Verifica alertas relacionados a valores suspeitos"""
        alerts_created = 0
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # Buscar propostas recentes com valores suspeitos
        recent_proposals = Proposal.query.filter(
            Proposal.created_at >= last_24h
        ).all()
        
        for proposal in recent_proposals:
            # Verificar valores muito altos
            if proposal.proposed_value > ProposalAlertService.ALERT_THRESHOLDS['unusual_high_value'].value:
                existing_alert = ProposalAlert.query.filter(
                    and_(
                        ProposalAlert.alert_type == 'unusual_high_value',
                        ProposalAlert.proposal_id == proposal.id,
                        ProposalAlert.status == 'active'
                    )
                ).first()
                
                if not existing_alert:
                    ProposalAlertService._create_alert(
                        alert_type='unusual_high_value',
                        severity='medium',
                        title=f'Valor muito alto: R$ {proposal.proposed_value}',
                        description=f'Proposta {proposal.id} tem valor de R$ {proposal.proposed_value}, acima do limite de R$ {ProposalAlertService.ALERT_THRESHOLDS["unusual_high_value"].value}',
                        proposal_id=proposal.id,
                        invite_id=proposal.invite_id,
                        pattern_data={
                            'proposed_value': float(proposal.proposed_value),
                            'threshold': float(ProposalAlertService.ALERT_THRESHOLDS['unusual_high_value'].value)
                        },
                        threshold_exceeded='unusual_high_value'
                    )
                    alerts_created += 1
            
            # Verificar aumentos percentuais excessivos
            if proposal.original_value > 0:
                increase_percentage = (proposal.value_difference / proposal.original_value) * 100
                
                if increase_percentage > ProposalAlertService.ALERT_THRESHOLDS['max_value_increase_percentage'].value:
                    existing_alert = ProposalAlert.query.filter(
                        and_(
                            ProposalAlert.alert_type == 'excessive_value_increase',
                            ProposalAlert.proposal_id == proposal.id,
                            ProposalAlert.status == 'active'
                        )
                    ).first()
                    
                    if not existing_alert:
                        ProposalAlertService._create_alert(
                            alert_type='excessive_value_increase',
                            severity='high',
                            title=f'Aumento excessivo: {increase_percentage:.1f}%',
                            description=f'Proposta {proposal.id} tem aumento de {increase_percentage:.1f}% (R$ {proposal.original_value} -> R$ {proposal.proposed_value})',
                            proposal_id=proposal.id,
                            invite_id=proposal.invite_id,
                            pattern_data={
                                'original_value': float(proposal.original_value),
                                'proposed_value': float(proposal.proposed_value),
                                'increase_percentage': increase_percentage,
                                'threshold': ProposalAlertService.ALERT_THRESHOLDS['max_value_increase_percentage'].value
                            },
                            threshold_exceeded='max_value_increase_percentage'
                        )
                        alerts_created += 1
        
        return alerts_created
    
    @staticmethod
    def _create_alert(alert_type: str, severity: str, title: str, description: str, **kwargs):
        """Cria um novo alerta no sistema"""
        try:
            alert = ProposalAlert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                pattern_data=json.dumps(kwargs.get('pattern_data', {})),
                threshold_exceeded=kwargs.get('threshold_exceeded'),
                user_id=kwargs.get('user_id'),
                proposal_id=kwargs.get('proposal_id'),
                invite_id=kwargs.get('invite_id')
            )
            
            db.session.add(alert)
            db.session.commit()
            
            alert_logger.warning(
                f"ALERT_CREATED: {alert_type} | "
                f"Severity:{severity} | "
                f"ID:{alert.id} | "
                f"Title:{title}"
            )
            
        except Exception as e:
            db.session.rollback()
            alert_logger.error(f"Erro ao criar alerta: {str(e)}")
            raise
    
    @staticmethod
    def _cleanup_old_alerts():
        """Remove alertas antigos resolvidos"""
        try:
            # Remover alertas resolvidos há mais de 90 dias
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            
            old_alerts = ProposalAlert.query.filter(
                and_(
                    ProposalAlert.status.in_(['resolved', 'false_positive']),
                    ProposalAlert.resolved_at < ninety_days_ago
                )
            ).all()
            
            for alert in old_alerts:
                db.session.delete(alert)
            
            if old_alerts:
                db.session.commit()
                alert_logger.info(f"Removidos {len(old_alerts)} alertas antigos")
            
        except Exception as e:
            db.session.rollback()
            alert_logger.error(f"Erro na limpeza de alertas: {str(e)}")
    
    @staticmethod
    def get_active_alerts(severity: str = None, limit: int = 50) -> List[Dict]:
        """
        Retorna alertas ativos do sistema
        
        Args:
            severity: Filtrar por severidade (low, medium, high, critical)
            limit: Número máximo de alertas para retornar
            
        Returns:
            List[Dict]: Lista de alertas ativos
        """
        query = ProposalAlert.query.filter_by(status='active')
        
        if severity:
            query = query.filter_by(severity=severity)
        
        alerts = query.order_by(
            ProposalAlert.severity.desc(),
            ProposalAlert.created_at.desc()
        ).limit(limit).all()
        
        return [{
            'id': alert.id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'description': alert.description,
            'user_id': alert.user_id,
            'user_name': alert.user.nome if alert.user else None,
            'proposal_id': alert.proposal_id,
            'invite_id': alert.invite_id,
            'pattern_data': json.loads(alert.pattern_data) if alert.pattern_data else {},
            'threshold_exceeded': alert.threshold_exceeded,
            'created_at': alert.created_at,
            'age_hours': (datetime.utcnow() - alert.created_at).total_seconds() / 3600
        } for alert in alerts]
    
    @staticmethod
    def resolve_alert(alert_id: int, admin_id: int, resolution_notes: str = None) -> bool:
        """
        Resolve um alerta
        
        Args:
            alert_id: ID do alerta
            admin_id: ID do administrador que está resolvendo
            resolution_notes: Notas sobre a resolução
            
        Returns:
            bool: True se resolvido com sucesso
        """
        try:
            alert = ProposalAlert.query.get(alert_id)
            if not alert:
                return False
            
            alert.resolve(admin_id, resolution_notes)
            db.session.commit()
            
            alert_logger.info(
                f"ALERT_RESOLVED: {alert.alert_type} | "
                f"ID:{alert_id} | "
                f"Admin:{admin_id} | "
                f"Notes:{resolution_notes or 'N/A'}"
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            alert_logger.error(f"Erro ao resolver alerta {alert_id}: {str(e)}")
            return False
    
    @staticmethod
    def mark_false_positive(alert_id: int, admin_id: int, notes: str = None) -> bool:
        """
        Marca um alerta como falso positivo
        
        Args:
            alert_id: ID do alerta
            admin_id: ID do administrador
            notes: Notas sobre por que é falso positivo
            
        Returns:
            bool: True se marcado com sucesso
        """
        try:
            alert = ProposalAlert.query.get(alert_id)
            if not alert:
                return False
            
            alert.mark_false_positive(admin_id, notes)
            db.session.commit()
            
            alert_logger.info(
                f"ALERT_FALSE_POSITIVE: {alert.alert_type} | "
                f"ID:{alert_id} | "
                f"Admin:{admin_id} | "
                f"Notes:{notes or 'N/A'}"
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            alert_logger.error(f"Erro ao marcar falso positivo {alert_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_alert_statistics(days: int = 30) -> Dict:
        """
        Retorna estatísticas dos alertas
        
        Args:
            days: Período em dias para análise
            
        Returns:
            Dict: Estatísticas dos alertas
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        alerts = ProposalAlert.query.filter(
            ProposalAlert.created_at >= since_date
        ).all()
        
        stats = {
            'total_alerts': len(alerts),
            'by_severity': {},
            'by_status': {},
            'by_type': {},
            'resolution_rate': 0,
            'false_positive_rate': 0,
            'average_resolution_time_hours': None
        }
        
        resolution_times = []
        
        for alert in alerts:
            # Contar por severidade
            severity = alert.severity
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Contar por status
            status = alert.status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Contar por tipo
            alert_type = alert.alert_type
            stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
            
            # Calcular tempo de resolução
            if alert.resolved_at and alert.created_at:
                resolution_time = alert.resolved_at - alert.created_at
                resolution_times.append(resolution_time.total_seconds() / 3600)
        
        # Calcular taxas
        resolved_count = stats['by_status'].get('resolved', 0)
        false_positive_count = stats['by_status'].get('false_positive', 0)
        total_processed = resolved_count + false_positive_count
        
        if len(alerts) > 0:
            stats['resolution_rate'] = (resolved_count / len(alerts)) * 100
            stats['false_positive_rate'] = (false_positive_count / len(alerts)) * 100
        
        # Tempo médio de resolução
        if resolution_times:
            stats['average_resolution_time_hours'] = sum(resolution_times) / len(resolution_times)
        
        return stats