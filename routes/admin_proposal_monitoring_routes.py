#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Rotas Administrativas para Monitoramento de Propostas

Este módulo implementa as rotas para o dashboard administrativo de monitoramento
do sistema de propostas, incluindo métricas, alertas e auditoria.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from models import db, ProposalAlert, ProposalMetrics, ProposalAuditLog, Proposal, User
from services.proposal_audit_service import ProposalAuditService
from services.proposal_metrics_service import ProposalMetricsService
from services.proposal_alert_service import ProposalAlertService
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
from functools import wraps

# Blueprint para rotas de monitoramento de propostas
admin_proposal_monitoring = Blueprint('admin_proposal_monitoring', __name__, url_prefix='/admin/propostas')


def admin_required(f):
    """Decorator para verificar se o usuário é admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Acesso negado. Faça login como administrador.', 'error')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_proposal_monitoring.route('/dashboard')
@admin_required
def dashboard():
    """
    Dashboard principal de monitoramento de propostas
    
    Exibe visão geral das métricas, alertas ativos e estatísticas gerais
    """
    try:
        # Obter resumo das métricas dos últimos 30 dias
        metrics_summary = ProposalMetricsService.get_metrics_summary(days=30)
        
        # Obter alertas ativos por severidade
        critical_alerts = ProposalAlertService.get_active_alerts(severity='critical', limit=5)
        high_alerts = ProposalAlertService.get_active_alerts(severity='high', limit=10)
        medium_alerts = ProposalAlertService.get_active_alerts(severity='medium', limit=15)
        
        # Obter estatísticas de alertas
        alert_stats = ProposalAlertService.get_alert_statistics(days=30)
        
        # Obter top usuários
        top_users = ProposalMetricsService.get_top_users_by_proposals(limit=10, days=30)
        
        # Obter análise de distribuição de valores
        value_analysis = ProposalMetricsService.get_value_distribution_analysis(days=30)
        
        # Calcular métricas do dia atual se necessário
        today = date.today()
        daily_metric = ProposalMetrics.query.filter_by(
            metric_date=today,
            metric_type='daily'
        ).first()
        
        if not daily_metric:
            # Calcular métricas do dia se não existir
            daily_metric = ProposalMetricsService.calculate_daily_metrics(today)
        
        return render_template('admin/proposal_monitoring_dashboard.html',
                             metrics_summary=metrics_summary,
                             daily_metric=daily_metric,
                             critical_alerts=critical_alerts,
                             high_alerts=high_alerts,
                             medium_alerts=medium_alerts,
                             alert_stats=alert_stats,
                             top_users=top_users,
                             value_analysis=value_analysis)
        
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_proposal_monitoring.route('/alertas')
@admin_required
def alertas():
    """
    Página de gerenciamento de alertas
    
    Lista todos os alertas com filtros e opções de resolução
    """
    try:
        # Parâmetros de filtro
        severity = request.args.get('severity', '')
        status = request.args.get('status', 'active')
        alert_type = request.args.get('type', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Construir query
        query = ProposalAlert.query
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if status:
            query = query.filter_by(status=status)
        
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
        
        # Ordenar por severidade e data
        query = query.order_by(
            ProposalAlert.severity.desc(),
            ProposalAlert.created_at.desc()
        )
        
        # Paginar
        alerts_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Obter tipos de alerta únicos para filtro
        alert_types = db.session.query(ProposalAlert.alert_type.distinct()).all()
        alert_types = [t[0] for t in alert_types]
        
        return render_template('admin/proposal_alerts.html',
                             alerts=alerts_pagination.items,
                             pagination=alerts_pagination,
                             alert_types=alert_types,
                             current_severity=severity,
                             current_status=status,
                             current_type=alert_type)
        
    except Exception as e:
        flash(f'Erro ao carregar alertas: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.dashboard'))


@admin_proposal_monitoring.route('/alertas/<int:alert_id>/resolver', methods=['POST'])
@admin_required
def resolver_alerta(alert_id):
    """
    Resolve um alerta específico
    """
    try:
        admin_id = session.get('admin_id')
        resolution_notes = request.form.get('resolution_notes', '')
        
        success = ProposalAlertService.resolve_alert(alert_id, admin_id, resolution_notes)
        
        if success:
            flash('Alerta resolvido com sucesso!', 'success')
        else:
            flash('Erro ao resolver alerta.', 'error')
        
        return redirect(url_for('admin_proposal_monitoring.alertas'))
        
    except Exception as e:
        flash(f'Erro ao resolver alerta: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.alertas'))


@admin_proposal_monitoring.route('/alertas/<int:alert_id>/falso-positivo', methods=['POST'])
@admin_required
def marcar_falso_positivo(alert_id):
    """
    Marca um alerta como falso positivo
    """
    try:
        admin_id = session.get('admin_id')
        notes = request.form.get('notes', '')
        
        success = ProposalAlertService.mark_false_positive(alert_id, admin_id, notes)
        
        if success:
            flash('Alerta marcado como falso positivo!', 'success')
        else:
            flash('Erro ao marcar alerta.', 'error')
        
        return redirect(url_for('admin_proposal_monitoring.alertas'))
        
    except Exception as e:
        flash(f'Erro ao marcar alerta: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.alertas'))


@admin_proposal_monitoring.route('/metricas')
@admin_required
def metricas():
    """
    Página de métricas detalhadas
    
    Exibe gráficos e tabelas com métricas históricas
    """
    try:
        # Parâmetros de período
        days = int(request.args.get('days', 30))
        metric_type = request.args.get('type', 'daily')
        
        # Obter métricas do período
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        metrics = ProposalMetrics.query.filter(
            ProposalMetrics.metric_type == metric_type,
            ProposalMetrics.metric_date >= start_date,
            ProposalMetrics.metric_date <= end_date
        ).order_by(ProposalMetrics.metric_date.asc()).all()
        
        # Preparar dados para gráficos
        chart_data = {
            'dates': [m.metric_date.isoformat() for m in metrics],
            'total_proposals': [m.total_proposals for m in metrics],
            'proposals_approved': [m.proposals_approved for m in metrics],
            'proposals_rejected': [m.proposals_rejected for m in metrics],
            'approval_rates': [m.approval_rate for m in metrics],
            'total_values': [float(m.total_proposed_value) for m in metrics]
        }
        
        # Obter resumo do período
        summary = ProposalMetricsService.get_metrics_summary(days=days)
        
        return render_template('admin/proposal_metrics.html',
                             metrics=metrics,
                             chart_data=json.dumps(chart_data),
                             summary=summary,
                             current_days=days,
                             current_type=metric_type)
        
    except Exception as e:
        flash(f'Erro ao carregar métricas: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.dashboard'))


@admin_proposal_monitoring.route('/auditoria')
@admin_required
def auditoria():
    """
    Página de auditoria de propostas
    
    Lista logs de auditoria com filtros avançados
    """
    try:
        # Parâmetros de filtro
        action_type = request.args.get('action_type', '')
        actor_role = request.args.get('actor_role', '')
        user_id = request.args.get('user_id', '')
        proposal_id = request.args.get('proposal_id', '')
        days = int(request.args.get('days', 7))
        page = int(request.args.get('page', 1))
        per_page = 50
        
        # Construir query
        query = ProposalAuditLog.query
        
        # Filtro por período
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ProposalAuditLog.created_at >= since_date)
        
        if action_type:
            query = query.filter_by(action_type=action_type)
        
        if actor_role:
            query = query.filter_by(actor_role=actor_role)
        
        if user_id:
            query = query.filter_by(actor_user_id=int(user_id))
        
        if proposal_id:
            query = query.filter_by(proposal_id=int(proposal_id))
        
        # Ordenar por data (mais recente primeiro)
        query = query.order_by(ProposalAuditLog.created_at.desc())
        
        # Paginar
        logs_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Obter valores únicos para filtros
        action_types = db.session.query(ProposalAuditLog.action_type.distinct()).all()
        action_types = [t[0] for t in action_types]
        
        actor_roles = db.session.query(ProposalAuditLog.actor_role.distinct()).all()
        actor_roles = [r[0] for r in actor_roles]
        
        return render_template('admin/proposal_audit.html',
                             logs=logs_pagination.items,
                             pagination=logs_pagination,
                             action_types=action_types,
                             actor_roles=actor_roles,
                             current_action_type=action_type,
                             current_actor_role=actor_role,
                             current_user_id=user_id,
                             current_proposal_id=proposal_id,
                             current_days=days)
        
    except Exception as e:
        flash(f'Erro ao carregar auditoria: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.dashboard'))


@admin_proposal_monitoring.route('/proposta/<int:proposal_id>/historico')
@admin_required
def historico_proposta(proposal_id):
    """
    Exibe histórico completo de uma proposta específica
    """
    try:
        # Obter proposta
        proposal = Proposal.query.get_or_404(proposal_id)
        
        # Obter histórico de auditoria
        history = ProposalAuditService.get_proposal_history(proposal_id)
        
        return render_template('admin/proposal_history.html',
                             proposal=proposal,
                             history=history)
        
    except Exception as e:
        flash(f'Erro ao carregar histórico: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.auditoria'))


@admin_proposal_monitoring.route('/usuario/<int:user_id>/atividade')
@admin_required
def atividade_usuario(user_id):
    """
    Exibe atividade de propostas de um usuário específico
    """
    try:
        # Obter usuário
        user = User.query.get_or_404(user_id)
        
        # Parâmetros
        days = int(request.args.get('days', 30))
        
        # Obter atividade do usuário
        activity = ProposalAuditService.get_user_proposal_activity(user_id, days)
        
        return render_template('admin/user_proposal_activity.html',
                             user=user,
                             activity=activity,
                             days=days)
        
    except Exception as e:
        flash(f'Erro ao carregar atividade: {str(e)}', 'error')
        return redirect(url_for('admin_proposal_monitoring.auditoria'))


@admin_proposal_monitoring.route('/api/verificar-alertas', methods=['POST'])
@admin_required
def verificar_alertas():
    """
    API para executar verificação manual de alertas
    """
    try:
        alerts_created = ProposalAlertService.check_all_alert_conditions()
        
        return jsonify({
            'success': True,
            'alerts_created': alerts_created,
            'message': f'Verificação concluída. {alerts_created} novos alertas criados.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_proposal_monitoring.route('/api/calcular-metricas', methods=['POST'])
@admin_required
def calcular_metricas():
    """
    API para recalcular métricas manualmente
    """
    try:
        target_date = request.json.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Calcular todas as métricas para a data
        ProposalMetricsService.update_all_metrics_for_date(target_date)
        
        return jsonify({
            'success': True,
            'message': f'Métricas calculadas para {target_date}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_proposal_monitoring.route('/api/estatisticas-rapidas')
@admin_required
def estatisticas_rapidas():
    """
    API para obter estatísticas rápidas para o dashboard
    """
    try:
        # Estatísticas dos últimos 7 dias
        summary_7d = ProposalMetricsService.get_metrics_summary(days=7)
        
        # Alertas ativos por severidade
        alerts_by_severity = {
            'critical': len(ProposalAlertService.get_active_alerts(severity='critical')),
            'high': len(ProposalAlertService.get_active_alerts(severity='high')),
            'medium': len(ProposalAlertService.get_active_alerts(severity='medium')),
            'low': len(ProposalAlertService.get_active_alerts(severity='low'))
        }
        
        # Propostas hoje
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        proposals_today = Proposal.query.filter(
            Proposal.created_at >= today_start,
            Proposal.created_at <= today_end
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'summary_7d': summary_7d,
                'alerts_by_severity': alerts_by_severity,
                'proposals_today': proposals_today,
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500