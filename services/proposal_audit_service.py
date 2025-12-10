#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Auditoria e Monitoramento de Propostas

Este serviço implementa o sistema completo de auditoria para propostas de alteração,
incluindo logging detalhado, métricas agregadas e detecção de padrões suspeitos.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from models import db, ProposalAuditLog, ProposalMetrics, ProposalAlert, Proposal, Invite, User
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import request, session

# Configurar logger específico para auditoria de propostas
audit_logger = logging.getLogger('proposal_audit')
audit_logger.setLevel(logging.INFO)

# Handler para arquivo de log específico de auditoria
if not audit_logger.handlers:
    handler = logging.FileHandler('logs/proposal_audit.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)


@dataclass
class AuditContext:
    """Contexto para operações de auditoria"""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    @classmethod
    def from_request(cls):
        """Cria contexto a partir da requisição atual"""
        if request:
            return cls(
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                session_id=session.get('session_id')
            )
        return cls()


class ProposalAuditService:
    """Serviço principal de auditoria para propostas"""
    
    # Limites para detecção de padrões suspeitos
    SUSPICIOUS_PATTERNS = {
        'max_proposals_per_hour': 10,
        'max_proposals_per_day': 50,
        'max_value_increase_percentage': 200,  # 200% de aumento
        'min_response_time_seconds': 30,  # Respostas muito rápidas podem ser suspeitas
        'max_rejection_rate_percentage': 80,  # Taxa de rejeição muito alta
        'unusual_value_threshold': Decimal('10000.00')  # Valores muito altos
    }
    
    @staticmethod
    def log_proposal_action(
        proposal_id: int,
        action_type: str,
        actor_user_id: Optional[int] = None,
        actor_admin_id: Optional[int] = None,
        actor_role: str = 'system',
        previous_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None,
        reason: Optional[str] = None,
        context: Optional[AuditContext] = None
    ) -> ProposalAuditLog:
        """
        Registra uma ação relacionada a proposta no log de auditoria
        
        Args:
            proposal_id: ID da proposta
            action_type: Tipo da ação (created, approved, rejected, cancelled, modified)
            actor_user_id: ID do usuário que executou a ação
            actor_admin_id: ID do admin que executou a ação
            actor_role: Papel do ator (cliente, prestador, admin, system)
            previous_data: Estado anterior (para modificações)
            new_data: Novo estado
            reason: Motivo/justificativa da ação
            context: Contexto da requisição
        
        Returns:
            ProposalAuditLog: Registro de auditoria criado
        """
        try:
            # Obter proposta para dados básicos
            proposal = Proposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            # Usar contexto da requisição se não fornecido
            if context is None:
                context = AuditContext.from_request()
            
            # Criar registro de auditoria
            audit_log = ProposalAuditLog(
                proposal_id=proposal_id,
                invite_id=proposal.invite_id,
                action_type=action_type,
                actor_user_id=actor_user_id,
                actor_admin_id=actor_admin_id,
                actor_role=actor_role,
                previous_data=json.dumps(previous_data) if previous_data else None,
                new_data=json.dumps(new_data) if new_data else None,
                reason=reason,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                session_id=context.session_id,
                original_value=proposal.original_value,
                proposed_value=proposal.proposed_value,
                value_difference=proposal.value_difference
            )
            
            db.session.add(audit_log)
            db.session.flush()  # Para obter o ID
            
            # Log estruturado para análise
            audit_logger.info(
                f"PROPOSAL_ACTION: {action_type} | "
                f"Proposal:{proposal_id} | "
                f"Invite:{proposal.invite_id} | "
                f"Actor:{actor_role}:{actor_user_id or actor_admin_id} | "
                f"Values:{proposal.original_value}->{proposal.proposed_value} | "
                f"IP:{context.ip_address} | "
                f"Reason:{reason or 'N/A'}"
            )
            
            # Verificar padrões suspeitos após cada ação
            ProposalAuditService._check_suspicious_patterns(proposal, action_type, actor_user_id)
            
            return audit_log
            
        except Exception as e:
            audit_logger.error(f"Erro ao registrar auditoria: {str(e)}")
            raise
    
    @staticmethod
    def log_proposal_created(proposal_id: int, prestador_id: int, reason: str = None) -> ProposalAuditLog:
        """Log específico para criação de proposta"""
        proposal = Proposal.query.get(proposal_id)
        
        new_data = {
            'original_value': float(proposal.original_value),
            'proposed_value': float(proposal.proposed_value),
            'justification': proposal.justification,
            'status': proposal.status,
            'created_at': proposal.created_at.isoformat()
        }
        
        return ProposalAuditService.log_proposal_action(
            proposal_id=proposal_id,
            action_type='created',
            actor_user_id=prestador_id,
            actor_role='prestador',
            new_data=new_data,
            reason=reason or proposal.justification
        )
    
    @staticmethod
    def log_proposal_approved(proposal_id: int, client_id: int, reason: str = None) -> ProposalAuditLog:
        """Log específico para aprovação de proposta"""
        proposal = Proposal.query.get(proposal_id)
        
        previous_data = {
            'status': 'pending',
            'responded_at': None
        }
        
        new_data = {
            'status': 'accepted',
            'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None,
            'client_response_reason': proposal.client_response_reason
        }
        
        return ProposalAuditService.log_proposal_action(
            proposal_id=proposal_id,
            action_type='approved',
            actor_user_id=client_id,
            actor_role='cliente',
            previous_data=previous_data,
            new_data=new_data,
            reason=reason
        )
    
    @staticmethod
    def log_proposal_rejected(proposal_id: int, client_id: int, reason: str = None) -> ProposalAuditLog:
        """Log específico para rejeição de proposta"""
        proposal = Proposal.query.get(proposal_id)
        
        previous_data = {
            'status': 'pending',
            'responded_at': None
        }
        
        new_data = {
            'status': 'rejected',
            'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None,
            'client_response_reason': proposal.client_response_reason
        }
        
        return ProposalAuditService.log_proposal_action(
            proposal_id=proposal_id,
            action_type='rejected',
            actor_user_id=client_id,
            actor_role='cliente',
            previous_data=previous_data,
            new_data=new_data,
            reason=reason
        )
    
    @staticmethod
    def log_proposal_cancelled(proposal_id: int, prestador_id: int, reason: str = None) -> ProposalAuditLog:
        """Log específico para cancelamento de proposta"""
        proposal = Proposal.query.get(proposal_id)
        
        previous_data = {
            'status': 'pending',
            'responded_at': None
        }
        
        new_data = {
            'status': 'cancelled',
            'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None
        }
        
        return ProposalAuditService.log_proposal_action(
            proposal_id=proposal_id,
            action_type='cancelled',
            actor_user_id=prestador_id,
            actor_role='prestador',
            previous_data=previous_data,
            new_data=new_data,
            reason=reason or "Cancelado pelo prestador"
        )
    
    @staticmethod
    def _check_suspicious_patterns(proposal: Proposal, action_type: str, user_id: Optional[int]):
        """
        Verifica padrões suspeitos após cada ação
        
        Detecta:
        - Muitas propostas em pouco tempo
        - Valores muito altos ou aumentos excessivos
        - Respostas muito rápidas
        - Padrões de rejeição anômalos
        """
        if not user_id:
            return
        
        try:
            alerts_to_create = []
            
            # 1. Verificar frequência de propostas (apenas para criação)
            if action_type == 'created':
                alerts_to_create.extend(
                    ProposalAuditService._check_proposal_frequency(user_id, proposal)
                )
                
                # Verificar valores suspeitos
                alerts_to_create.extend(
                    ProposalAuditService._check_suspicious_values(proposal)
                )
            
            # 2. Verificar tempo de resposta (para aprovação/rejeição)
            elif action_type in ['approved', 'rejected']:
                alerts_to_create.extend(
                    ProposalAuditService._check_response_time(proposal)
                )
            
            # 3. Verificar taxa de rejeição do usuário
            if action_type == 'rejected':
                alerts_to_create.extend(
                    ProposalAuditService._check_rejection_rate(user_id)
                )
            
            # Criar alertas encontrados
            for alert_data in alerts_to_create:
                ProposalAuditService._create_alert(**alert_data)
                
        except Exception as e:
            audit_logger.error(f"Erro ao verificar padrões suspeitos: {str(e)}")
    
    @staticmethod
    def _check_proposal_frequency(user_id: int, proposal: Proposal) -> List[Dict]:
        """Verifica frequência de criação de propostas"""
        alerts = []
        now = datetime.utcnow()
        
        # Verificar propostas na última hora
        hour_ago = now - timedelta(hours=1)
        proposals_last_hour = db.session.query(ProposalAuditLog).filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                ProposalAuditLog.actor_user_id == user_id,
                ProposalAuditLog.created_at >= hour_ago
            )
        ).count()
        
        if proposals_last_hour > ProposalAuditService.SUSPICIOUS_PATTERNS['max_proposals_per_hour']:
            alerts.append({
                'alert_type': 'high_frequency_proposals_hour',
                'severity': 'high',
                'title': f'Usuário criou {proposals_last_hour} propostas na última hora',
                'description': f'Usuário {user_id} criou {proposals_last_hour} propostas na última hora, '
                              f'excedendo o limite de {ProposalAuditService.SUSPICIOUS_PATTERNS["max_proposals_per_hour"]}',
                'user_id': user_id,
                'proposal_id': proposal.id,
                'pattern_data': json.dumps({
                    'proposals_count': proposals_last_hour,
                    'time_period': 'last_hour',
                    'threshold': ProposalAuditService.SUSPICIOUS_PATTERNS['max_proposals_per_hour']
                }),
                'threshold_exceeded': 'max_proposals_per_hour'
            })
        
        # Verificar propostas no último dia
        day_ago = now - timedelta(days=1)
        proposals_last_day = db.session.query(ProposalAuditLog).filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                ProposalAuditLog.actor_user_id == user_id,
                ProposalAuditLog.created_at >= day_ago
            )
        ).count()
        
        if proposals_last_day > ProposalAuditService.SUSPICIOUS_PATTERNS['max_proposals_per_day']:
            alerts.append({
                'alert_type': 'high_frequency_proposals_day',
                'severity': 'medium',
                'title': f'Usuário criou {proposals_last_day} propostas no último dia',
                'description': f'Usuário {user_id} criou {proposals_last_day} propostas no último dia, '
                              f'excedendo o limite de {ProposalAuditService.SUSPICIOUS_PATTERNS["max_proposals_per_day"]}',
                'user_id': user_id,
                'proposal_id': proposal.id,
                'pattern_data': json.dumps({
                    'proposals_count': proposals_last_day,
                    'time_period': 'last_day',
                    'threshold': ProposalAuditService.SUSPICIOUS_PATTERNS['max_proposals_per_day']
                }),
                'threshold_exceeded': 'max_proposals_per_day'
            })
        
        return alerts
    
    @staticmethod
    def _check_suspicious_values(proposal: Proposal) -> List[Dict]:
        """Verifica valores suspeitos na proposta"""
        alerts = []
        
        # Verificar valores muito altos
        if proposal.proposed_value > ProposalAuditService.SUSPICIOUS_PATTERNS['unusual_value_threshold']:
            alerts.append({
                'alert_type': 'unusual_high_value',
                'severity': 'medium',
                'title': f'Proposta com valor muito alto: R$ {proposal.proposed_value}',
                'description': f'Proposta {proposal.id} tem valor de R$ {proposal.proposed_value}, '
                              f'acima do limite de R$ {ProposalAuditService.SUSPICIOUS_PATTERNS["unusual_value_threshold"]}',
                'proposal_id': proposal.id,
                'invite_id': proposal.invite_id,
                'pattern_data': json.dumps({
                    'proposed_value': float(proposal.proposed_value),
                    'threshold': float(ProposalAuditService.SUSPICIOUS_PATTERNS['unusual_value_threshold'])
                }),
                'threshold_exceeded': 'unusual_value_threshold'
            })
        
        # Verificar aumentos percentuais excessivos
        if proposal.original_value > 0:
            increase_percentage = (proposal.value_difference / proposal.original_value) * 100
            max_increase = ProposalAuditService.SUSPICIOUS_PATTERNS['max_value_increase_percentage']
            
            if increase_percentage > max_increase:
                alerts.append({
                    'alert_type': 'excessive_value_increase',
                    'severity': 'high',
                    'title': f'Aumento excessivo de valor: {increase_percentage:.1f}%',
                    'description': f'Proposta {proposal.id} tem aumento de {increase_percentage:.1f}% '
                                  f'(R$ {proposal.original_value} -> R$ {proposal.proposed_value}), '
                                  f'excedendo o limite de {max_increase}%',
                    'proposal_id': proposal.id,
                    'invite_id': proposal.invite_id,
                    'pattern_data': json.dumps({
                        'original_value': float(proposal.original_value),
                        'proposed_value': float(proposal.proposed_value),
                        'increase_percentage': float(increase_percentage),
                        'threshold': max_increase
                    }),
                    'threshold_exceeded': 'max_value_increase_percentage'
                })
        
        return alerts
    
    @staticmethod
    def _check_response_time(proposal: Proposal) -> List[Dict]:
        """Verifica tempo de resposta suspeito"""
        alerts = []
        
        if proposal.responded_at and proposal.created_at:
            response_time = proposal.responded_at - proposal.created_at
            response_seconds = response_time.total_seconds()
            min_response_time = ProposalAuditService.SUSPICIOUS_PATTERNS['min_response_time_seconds']
            
            if response_seconds < min_response_time:
                alerts.append({
                    'alert_type': 'very_fast_response',
                    'severity': 'medium',
                    'title': f'Resposta muito rápida: {response_seconds:.0f} segundos',
                    'description': f'Proposta {proposal.id} foi respondida em {response_seconds:.0f} segundos, '
                                  f'abaixo do limite mínimo de {min_response_time} segundos',
                    'proposal_id': proposal.id,
                    'invite_id': proposal.invite_id,
                    'pattern_data': json.dumps({
                        'response_time_seconds': response_seconds,
                        'threshold': min_response_time,
                        'created_at': proposal.created_at.isoformat(),
                        'responded_at': proposal.responded_at.isoformat()
                    }),
                    'threshold_exceeded': 'min_response_time_seconds'
                })
        
        return alerts
    
    @staticmethod
    def _check_rejection_rate(user_id: int) -> List[Dict]:
        """Verifica taxa de rejeição do usuário"""
        alerts = []
        
        # Buscar propostas dos últimos 30 dias para este cliente
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Contar propostas respondidas pelo cliente
        total_responses = db.session.query(ProposalAuditLog).filter(
            and_(
                ProposalAuditLog.actor_user_id == user_id,
                ProposalAuditLog.actor_role == 'cliente',
                ProposalAuditLog.action_type.in_(['approved', 'rejected']),
                ProposalAuditLog.created_at >= thirty_days_ago
            )
        ).count()
        
        rejections = db.session.query(ProposalAuditLog).filter(
            and_(
                ProposalAuditLog.actor_user_id == user_id,
                ProposalAuditLog.actor_role == 'cliente',
                ProposalAuditLog.action_type == 'rejected',
                ProposalAuditLog.created_at >= thirty_days_ago
            )
        ).count()
        
        if total_responses >= 5:  # Só alertar se houver um mínimo de respostas
            rejection_rate = (rejections / total_responses) * 100
            max_rejection_rate = ProposalAuditService.SUSPICIOUS_PATTERNS['max_rejection_rate_percentage']
            
            if rejection_rate > max_rejection_rate:
                alerts.append({
                    'alert_type': 'high_rejection_rate',
                    'severity': 'medium',
                    'title': f'Alta taxa de rejeição: {rejection_rate:.1f}%',
                    'description': f'Cliente {user_id} tem taxa de rejeição de {rejection_rate:.1f}% '
                                  f'({rejections}/{total_responses} propostas) nos últimos 30 dias, '
                                  f'acima do limite de {max_rejection_rate}%',
                    'user_id': user_id,
                    'pattern_data': json.dumps({
                        'rejection_rate': rejection_rate,
                        'rejections': rejections,
                        'total_responses': total_responses,
                        'period_days': 30,
                        'threshold': max_rejection_rate
                    }),
                    'threshold_exceeded': 'max_rejection_rate_percentage'
                })
        
        return alerts
    
    @staticmethod
    def _create_alert(alert_type: str, severity: str, title: str, description: str, **kwargs):
        """Cria um alerta no sistema"""
        try:
            alert = ProposalAlert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                **kwargs
            )
            
            db.session.add(alert)
            db.session.flush()
            
            audit_logger.warning(
                f"SUSPICIOUS_PATTERN_DETECTED: {alert_type} | "
                f"Severity:{severity} | "
                f"Title:{title} | "
                f"Alert:{alert.id}"
            )
            
        except Exception as e:
            audit_logger.error(f"Erro ao criar alerta: {str(e)}")
    
    @staticmethod
    def get_proposal_history(proposal_id: int) -> List[Dict]:
        """Retorna histórico completo de uma proposta"""
        logs = ProposalAuditLog.query.filter_by(proposal_id=proposal_id)\
                                   .order_by(ProposalAuditLog.created_at.asc()).all()
        
        return [{
            'id': log.id,
            'action_type': log.action_type,
            'actor_role': log.actor_role,
            'actor_name': log.actor_user.nome if log.actor_user else 
                         (log.actor_admin.email if log.actor_admin else 'Sistema'),
            'reason': log.reason,
            'previous_data': json.loads(log.previous_data) if log.previous_data else None,
            'new_data': json.loads(log.new_data) if log.new_data else None,
            'ip_address': log.ip_address,
            'created_at': log.created_at,
            'original_value': float(log.original_value) if log.original_value else None,
            'proposed_value': float(log.proposed_value) if log.proposed_value else None,
            'value_difference': float(log.value_difference) if log.value_difference else None
        } for log in logs]
    
    @staticmethod
    def get_invite_proposal_history(invite_id: int) -> List[Dict]:
        """Retorna histórico de todas as propostas de um convite"""
        logs = ProposalAuditLog.query.filter_by(invite_id=invite_id)\
                                   .order_by(ProposalAuditLog.created_at.desc()).all()
        
        return [{
            'id': log.id,
            'proposal_id': log.proposal_id,
            'action_type': log.action_type,
            'actor_role': log.actor_role,
            'actor_name': log.actor_user.nome if log.actor_user else 
                         (log.actor_admin.email if log.actor_admin else 'Sistema'),
            'reason': log.reason,
            'created_at': log.created_at,
            'original_value': float(log.original_value) if log.original_value else None,
            'proposed_value': float(log.proposed_value) if log.proposed_value else None,
            'value_difference': float(log.value_difference) if log.value_difference else None
        } for log in logs]
    
    @staticmethod
    def get_user_proposal_activity(user_id: int, days: int = 30) -> Dict:
        """Retorna atividade de propostas de um usuário"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Buscar logs do usuário
        logs = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.actor_user_id == user_id,
                ProposalAuditLog.created_at >= since_date
            )
        ).all()
        
        # Agrupar por tipo de ação
        activity = {
            'total_actions': len(logs),
            'by_action_type': {},
            'by_date': {},
            'proposals_created': 0,
            'proposals_responded': 0,
            'average_response_time_hours': None
        }
        
        response_times = []
        
        for log in logs:
            # Contar por tipo de ação
            action = log.action_type
            activity['by_action_type'][action] = activity['by_action_type'].get(action, 0) + 1
            
            # Contar por data
            date_str = log.created_at.date().isoformat()
            activity['by_date'][date_str] = activity['by_date'].get(date_str, 0) + 1
            
            # Contar criações e respostas
            if action == 'created':
                activity['proposals_created'] += 1
            elif action in ['approved', 'rejected']:
                activity['proposals_responded'] += 1
                
                # Calcular tempo de resposta se possível
                proposal = Proposal.query.get(log.proposal_id)
                if proposal and proposal.created_at and proposal.responded_at:
                    response_time = proposal.responded_at - proposal.created_at
                    response_times.append(response_time.total_seconds() / 3600)  # em horas
        
        # Calcular tempo médio de resposta
        if response_times:
            activity['average_response_time_hours'] = sum(response_times) / len(response_times)
        
        return activity