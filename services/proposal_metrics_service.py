#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Métricas de Propostas

Este serviço calcula e mantém métricas agregadas sobre propostas de alteração,
incluindo estatísticas diárias, semanais e mensais para monitoramento e análise.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

from models import db, ProposalMetrics, Proposal, ProposalAuditLog, Invite, User
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Logger para métricas
metrics_logger = logging.getLogger('proposal_metrics')


@dataclass
class MetricsPeriod:
    """Representa um período para cálculo de métricas"""
    start_date: date
    end_date: date
    metric_type: str  # daily, weekly, monthly
    
    @classmethod
    def daily(cls, target_date: date):
        return cls(target_date, target_date, 'daily')
    
    @classmethod
    def weekly(cls, target_date: date):
        # Semana começa na segunda-feira
        start = target_date - timedelta(days=target_date.weekday())
        end = start + timedelta(days=6)
        return cls(start, end, 'weekly')
    
    @classmethod
    def monthly(cls, target_date: date):
        start = target_date.replace(day=1)
        if target_date.month == 12:
            end = date(target_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
        return cls(start, end, 'monthly')


class ProposalMetricsService:
    """Serviço para cálculo e manutenção de métricas de propostas"""
    
    @staticmethod
    def calculate_daily_metrics(target_date: date = None) -> ProposalMetrics:
        """
        Calcula métricas diárias para uma data específica
        
        Args:
            target_date: Data para calcular métricas (padrão: hoje)
            
        Returns:
            ProposalMetrics: Objeto com métricas calculadas
        """
        if target_date is None:
            target_date = date.today()
        
        period = MetricsPeriod.daily(target_date)
        return ProposalMetricsService._calculate_metrics_for_period(period)
    
    @staticmethod
    def calculate_weekly_metrics(target_date: date = None) -> ProposalMetrics:
        """Calcula métricas semanais"""
        if target_date is None:
            target_date = date.today()
        
        period = MetricsPeriod.weekly(target_date)
        return ProposalMetricsService._calculate_metrics_for_period(period)
    
    @staticmethod
    def calculate_monthly_metrics(target_date: date = None) -> ProposalMetrics:
        """Calcula métricas mensais"""
        if target_date is None:
            target_date = date.today()
        
        period = MetricsPeriod.monthly(target_date)
        return ProposalMetricsService._calculate_metrics_for_period(period)
    
    @staticmethod
    def _calculate_metrics_for_period(period: MetricsPeriod) -> ProposalMetrics:
        """
        Calcula métricas para um período específico
        
        Args:
            period: Período para cálculo
            
        Returns:
            ProposalMetrics: Métricas calculadas
        """
        try:
            # Verificar se já existe métrica para este período
            existing_metric = ProposalMetrics.query.filter_by(
                metric_date=period.start_date,
                metric_type=period.metric_type
            ).first()
            
            if existing_metric:
                # Atualizar métrica existente
                metric = existing_metric
            else:
                # Criar nova métrica
                metric = ProposalMetrics(
                    metric_date=period.start_date,
                    metric_type=period.metric_type
                )
            
            # Definir range de datas para consultas
            start_datetime = datetime.combine(period.start_date, datetime.min.time())
            end_datetime = datetime.combine(period.end_date, datetime.max.time())
            
            # 1. Métricas básicas de propostas
            proposals_in_period = Proposal.query.filter(
                and_(
                    Proposal.created_at >= start_datetime,
                    Proposal.created_at <= end_datetime
                )
            ).all()
            
            metric.total_proposals = len(proposals_in_period)
            
            # 2. Contar por status usando audit logs para maior precisão
            status_counts = ProposalMetricsService._count_proposals_by_status(
                start_datetime, end_datetime
            )
            
            metric.proposals_created = status_counts.get('created', 0)
            metric.proposals_approved = status_counts.get('approved', 0)
            metric.proposals_rejected = status_counts.get('rejected', 0)
            metric.proposals_cancelled = status_counts.get('cancelled', 0)
            
            # 3. Métricas de valor
            value_metrics = ProposalMetricsService._calculate_value_metrics(proposals_in_period)
            metric.total_original_value = value_metrics['total_original']
            metric.total_proposed_value = value_metrics['total_proposed']
            metric.total_approved_value = value_metrics['total_approved']
            metric.proposals_with_increase = value_metrics['increases_count']
            metric.proposals_with_decrease = value_metrics['decreases_count']
            
            # 4. Tempo médio de resposta
            metric.average_response_time_hours = ProposalMetricsService._calculate_average_response_time(
                start_datetime, end_datetime
            )
            
            # 5. Usuários únicos
            unique_users = ProposalMetricsService._count_unique_users(proposals_in_period)
            metric.unique_prestadores = unique_users['prestadores']
            metric.unique_clientes = unique_users['clientes']
            
            # Salvar ou atualizar
            if not existing_metric:
                db.session.add(metric)
            
            metric.updated_at = datetime.utcnow()
            db.session.commit()
            
            metrics_logger.info(
                f"Métricas calculadas para {period.metric_type} {period.start_date}: "
                f"{metric.total_proposals} propostas, "
                f"Taxa aprovação: {metric.approval_rate:.1f}%"
            )
            
            return metric
            
        except Exception as e:
            db.session.rollback()
            metrics_logger.error(f"Erro ao calcular métricas: {str(e)}")
            raise
    
    @staticmethod
    def _count_proposals_by_status(start_datetime: datetime, end_datetime: datetime) -> Dict[str, int]:
        """Conta propostas por status usando audit logs"""
        # Contar ações de criação
        created_count = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'created',
                ProposalAuditLog.created_at >= start_datetime,
                ProposalAuditLog.created_at <= end_datetime
            )
        ).count()
        
        # Contar ações de aprovação
        approved_count = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'approved',
                ProposalAuditLog.created_at >= start_datetime,
                ProposalAuditLog.created_at <= end_datetime
            )
        ).count()
        
        # Contar ações de rejeição
        rejected_count = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'rejected',
                ProposalAuditLog.created_at >= start_datetime,
                ProposalAuditLog.created_at <= end_datetime
            )
        ).count()
        
        # Contar ações de cancelamento
        cancelled_count = ProposalAuditLog.query.filter(
            and_(
                ProposalAuditLog.action_type == 'cancelled',
                ProposalAuditLog.created_at >= start_datetime,
                ProposalAuditLog.created_at <= end_datetime
            )
        ).count()
        
        return {
            'created': created_count,
            'approved': approved_count,
            'rejected': rejected_count,
            'cancelled': cancelled_count
        }
    
    @staticmethod
    def _calculate_value_metrics(proposals: List[Proposal]) -> Dict:
        """Calcula métricas relacionadas a valores"""
        total_original = Decimal('0.00')
        total_proposed = Decimal('0.00')
        total_approved = Decimal('0.00')
        increases_count = 0
        decreases_count = 0
        
        for proposal in proposals:
            total_original += proposal.original_value
            total_proposed += proposal.proposed_value
            
            if proposal.is_accepted:
                total_approved += proposal.proposed_value
            
            if proposal.is_increase:
                increases_count += 1
            elif proposal.is_decrease:
                decreases_count += 1
        
        return {
            'total_original': total_original,
            'total_proposed': total_proposed,
            'total_approved': total_approved,
            'increases_count': increases_count,
            'decreases_count': decreases_count
        }
    
    @staticmethod
    def _calculate_average_response_time(start_datetime: datetime, end_datetime: datetime) -> Optional[Decimal]:
        """Calcula tempo médio de resposta em horas"""
        # Buscar propostas respondidas no período
        responded_proposals = Proposal.query.filter(
            and_(
                Proposal.responded_at >= start_datetime,
                Proposal.responded_at <= end_datetime,
                Proposal.responded_at.isnot(None),
                Proposal.status.in_(['accepted', 'rejected'])
            )
        ).all()
        
        if not responded_proposals:
            return None
        
        total_response_time = Decimal('0.00')
        count = 0
        
        for proposal in responded_proposals:
            if proposal.created_at and proposal.responded_at:
                response_time = proposal.responded_at - proposal.created_at
                hours = Decimal(str(response_time.total_seconds() / 3600))
                total_response_time += hours
                count += 1
        
        return total_response_time / count if count > 0 else None
    
    @staticmethod
    def _count_unique_users(proposals: List[Proposal]) -> Dict[str, int]:
        """Conta usuários únicos (prestadores e clientes)"""
        unique_prestadores = set()
        unique_clientes = set()
        
        for proposal in proposals:
            unique_prestadores.add(proposal.prestador_id)
            if proposal.invite and proposal.invite.client_id:
                unique_clientes.add(proposal.invite.client_id)
        
        return {
            'prestadores': len(unique_prestadores),
            'clientes': len(unique_clientes)
        }
    
    @staticmethod
    def update_all_metrics_for_date(target_date: date = None):
        """
        Atualiza todas as métricas (diária, semanal, mensal) para uma data
        
        Args:
            target_date: Data para atualizar (padrão: hoje)
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # Calcular métricas diárias
            daily_metric = ProposalMetricsService.calculate_daily_metrics(target_date)
            
            # Calcular métricas semanais (apenas se for domingo ou último dia da semana)
            if target_date.weekday() == 6:  # Domingo
                weekly_metric = ProposalMetricsService.calculate_weekly_metrics(target_date)
            
            # Calcular métricas mensais (apenas no último dia do mês)
            tomorrow = target_date + timedelta(days=1)
            if tomorrow.day == 1:  # Último dia do mês
                monthly_metric = ProposalMetricsService.calculate_monthly_metrics(target_date)
            
            metrics_logger.info(f"Métricas atualizadas para {target_date}")
            
        except Exception as e:
            metrics_logger.error(f"Erro ao atualizar métricas para {target_date}: {str(e)}")
            raise
    
    @staticmethod
    def get_metrics_summary(days: int = 30) -> Dict:
        """
        Retorna resumo de métricas dos últimos N dias
        
        Args:
            days: Número de dias para incluir no resumo
            
        Returns:
            Dict: Resumo das métricas
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Buscar métricas diárias no período
        daily_metrics = ProposalMetrics.query.filter(
            and_(
                ProposalMetrics.metric_type == 'daily',
                ProposalMetrics.metric_date >= start_date,
                ProposalMetrics.metric_date <= end_date
            )
        ).order_by(ProposalMetrics.metric_date.desc()).all()
        
        if not daily_metrics:
            return {
                'period_days': days,
                'total_proposals': 0,
                'total_approved': 0,
                'total_rejected': 0,
                'approval_rate': 0,
                'daily_average': 0,
                'trend': 'stable'
            }
        
        # Calcular totais
        total_proposals = sum(m.total_proposals for m in daily_metrics)
        total_approved = sum(m.proposals_approved for m in daily_metrics)
        total_rejected = sum(m.proposals_rejected for m in daily_metrics)
        
        # Calcular taxa de aprovação
        total_responded = total_approved + total_rejected
        approval_rate = (total_approved / total_responded * 100) if total_responded > 0 else 0
        
        # Calcular média diária
        daily_average = total_proposals / len(daily_metrics) if daily_metrics else 0
        
        # Calcular tendência (comparar primeira e segunda metade do período)
        mid_point = len(daily_metrics) // 2
        if mid_point > 0:
            first_half_avg = sum(m.total_proposals for m in daily_metrics[mid_point:]) / mid_point
            second_half_avg = sum(m.total_proposals for m in daily_metrics[:mid_point]) / mid_point
            
            if second_half_avg > first_half_avg * 1.1:
                trend = 'increasing'
            elif second_half_avg < first_half_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'period_days': days,
            'total_proposals': total_proposals,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'approval_rate': approval_rate,
            'daily_average': daily_average,
            'trend': trend,
            'metrics_count': len(daily_metrics)
        }
    
    @staticmethod
    def get_top_users_by_proposals(limit: int = 10, days: int = 30) -> Dict:
        """
        Retorna usuários com mais propostas nos últimos N dias
        
        Args:
            limit: Número máximo de usuários para retornar
            days: Período em dias para análise
            
        Returns:
            Dict: Listas de top prestadores e clientes
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Top prestadores (por propostas criadas)
        top_prestadores = db.session.query(
            User.id,
            User.nome,
            User.email,
            func.count(Proposal.id).label('proposals_count'),
            func.avg(Proposal.proposed_value - Proposal.original_value).label('avg_increase')
        ).join(
            Proposal, User.id == Proposal.prestador_id
        ).filter(
            Proposal.created_at >= start_date
        ).group_by(
            User.id, User.nome, User.email
        ).order_by(
            func.count(Proposal.id).desc()
        ).limit(limit).all()
        
        # Top clientes (por propostas recebidas)
        top_clientes = db.session.query(
            User.id,
            User.nome,
            User.email,
            func.count(Proposal.id).label('proposals_received'),
            func.sum(func.case([(Proposal.status == 'accepted', 1)], else_=0)).label('approved_count')
        ).join(
            Invite, User.id == Invite.client_id
        ).join(
            Proposal, Invite.id == Proposal.invite_id
        ).filter(
            Proposal.created_at >= start_date
        ).group_by(
            User.id, User.nome, User.email
        ).order_by(
            func.count(Proposal.id).desc()
        ).limit(limit).all()
        
        return {
            'top_prestadores': [{
                'user_id': p.id,
                'nome': p.nome,
                'email': p.email,
                'proposals_count': p.proposals_count,
                'avg_increase': float(p.avg_increase) if p.avg_increase else 0
            } for p in top_prestadores],
            'top_clientes': [{
                'user_id': c.id,
                'nome': c.nome,
                'email': c.email,
                'proposals_received': c.proposals_received,
                'approved_count': c.approved_count,
                'approval_rate': (c.approved_count / c.proposals_received * 100) if c.proposals_received > 0 else 0
            } for c in top_clientes]
        }
    
    @staticmethod
    def get_value_distribution_analysis(days: int = 30) -> Dict:
        """
        Analisa distribuição de valores das propostas
        
        Args:
            days: Período em dias para análise
            
        Returns:
            Dict: Análise de distribuição de valores
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        proposals = Proposal.query.filter(
            Proposal.created_at >= start_date
        ).all()
        
        if not proposals:
            return {
                'total_proposals': 0,
                'value_ranges': {},
                'increase_analysis': {},
                'average_values': {}
            }
        
        # Definir faixas de valor
        value_ranges = {
            '0-100': 0,
            '101-500': 0,
            '501-1000': 0,
            '1001-5000': 0,
            '5001+': 0
        }
        
        increases = []
        decreases = []
        original_values = []
        proposed_values = []
        
        for proposal in proposals:
            # Classificar por faixa de valor proposto
            value = float(proposal.proposed_value)
            if value <= 100:
                value_ranges['0-100'] += 1
            elif value <= 500:
                value_ranges['101-500'] += 1
            elif value <= 1000:
                value_ranges['501-1000'] += 1
            elif value <= 5000:
                value_ranges['1001-5000'] += 1
            else:
                value_ranges['5001+'] += 1
            
            # Coletar dados para análise
            original_values.append(float(proposal.original_value))
            proposed_values.append(float(proposal.proposed_value))
            
            if proposal.is_increase:
                increases.append(float(proposal.value_difference))
            elif proposal.is_decrease:
                decreases.append(abs(float(proposal.value_difference)))
        
        # Calcular estatísticas
        avg_original = sum(original_values) / len(original_values)
        avg_proposed = sum(proposed_values) / len(proposed_values)
        avg_increase = sum(increases) / len(increases) if increases else 0
        avg_decrease = sum(decreases) / len(decreases) if decreases else 0
        
        return {
            'total_proposals': len(proposals),
            'value_ranges': value_ranges,
            'increase_analysis': {
                'count': len(increases),
                'average_increase': avg_increase,
                'max_increase': max(increases) if increases else 0,
                'percentage_with_increase': len(increases) / len(proposals) * 100
            },
            'decrease_analysis': {
                'count': len(decreases),
                'average_decrease': avg_decrease,
                'max_decrease': max(decreases) if decreases else 0,
                'percentage_with_decrease': len(decreases) / len(proposals) * 100
            },
            'average_values': {
                'original': avg_original,
                'proposed': avg_proposed,
                'difference': avg_proposed - avg_original
            }
        }