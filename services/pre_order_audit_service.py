#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderAuditService - Serviço de auditoria e alertas para pré-ordens

Este serviço gerencia auditoria completa das pré-ordens, incluindo:
- Histórico completo de ações
- Alertas de negociações excessivas
- Relatórios de negociação
- Detecção de propostas extremas

Requirements: 17.1-17.5
"""

from models import (
    db, PreOrder, PreOrderStatus, PreOrderProposal, ProposalStatus,
    PreOrderHistory, User
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, List, Tuple
from decimal import Decimal
import logging
import json

# Configurar logging
logger = logging.getLogger(__name__)


class PreOrderAuditService:
    """
    Serviço de auditoria e alertas para pré-ordens
    
    Responsável por:
    - Obter histórico completo de pré-ordens
    - Detectar negociações excessivas (>5 propostas)
    - Gerar relatórios de negociação
    - Identificar propostas extremas
    - Registrar logs de auditoria com IP e user agent
    
    Requirements: 17.1-17.5
    """
    
    # Limite de propostas para alerta de negociação excessiva
    EXCESSIVE_PROPOSALS_THRESHOLD = 5
    
    # Limites para propostas extremas
    EXTREME_INCREASE_THRESHOLD = 100  # >100% aumento
    EXTREME_DECREASE_THRESHOLD = -50  # >50% redução
    
    @staticmethod
    def get_full_history(pre_order_id: int, include_metadata: bool = True) -> Dict:
        """
        Retorna histórico completo de uma pré-ordem para auditoria
        
        Args:
            pre_order_id: ID da pré-ordem
            include_metadata: Se deve incluir metadados adicionais
            
        Returns:
            dict: Histórico completo com todos os eventos
            
        Requirements: 17.1, 17.2, 17.3
        """
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                return {
                    'success': False,
                    'error': f'Pré-ordem {pre_order_id} não encontrada'
                }
            
            # Buscar histórico ordenado por data
            history_entries = PreOrderHistory.query.filter_by(
                pre_order_id=pre_order_id
            ).order_by(PreOrderHistory.created_at.asc()).all()
            
            # Buscar propostas
            proposals = PreOrderProposal.query.filter_by(
                pre_order_id=pre_order_id
            ).order_by(PreOrderProposal.created_at.asc()).all()
            
            # Formatar histórico
            history_list = []
            for entry in history_entries:
                history_item = {
                    'id': entry.id,
                    'event_type': entry.event_type,
                    'event_type_display': entry.event_type_display,
                    'actor_id': entry.actor_id,
                    'actor_name': entry.actor.nome if entry.actor else 'Sistema',
                    'description': entry.description,
                    'event_data': entry.event_data,
                    'created_at': entry.created_at.isoformat(),
                    'timestamp': entry.created_at.timestamp()
                }
                history_list.append(history_item)
            
            # Formatar propostas
            proposals_list = []
            for proposal in proposals:
                proposal_item = {
                    'id': proposal.id,
                    'proposed_by': proposal.proposed_by,
                    'proposer_name': proposal.proposer.nome if proposal.proposer else 'Desconhecido',
                    'proposed_value': float(proposal.proposed_value) if proposal.proposed_value else None,
                    'proposed_delivery_date': proposal.proposed_delivery_date.isoformat() if proposal.proposed_delivery_date else None,
                    'proposed_description': proposal.proposed_description,
                    'justification': proposal.justification,
                    'status': proposal.status,
                    'status_display': proposal.status_display,
                    'is_extreme': proposal.is_extreme_proposal,
                    'created_at': proposal.created_at.isoformat(),
                    'responded_at': proposal.responded_at.isoformat() if proposal.responded_at else None
                }
                proposals_list.append(proposal_item)
            
            result = {
                'success': True,
                'pre_order_id': pre_order_id,
                'pre_order': {
                    'id': pre_order.id,
                    'title': pre_order.title,
                    'status': pre_order.status,
                    'status_display': pre_order.status_display,
                    'current_value': float(pre_order.current_value),
                    'original_value': float(pre_order.original_value),
                    'value_change_percentage': float(pre_order.value_change_percentage),
                    'client_id': pre_order.client_id,
                    'provider_id': pre_order.provider_id,
                    'created_at': pre_order.created_at.isoformat(),
                    'updated_at': pre_order.updated_at.isoformat(),
                    'expires_at': pre_order.expires_at.isoformat()
                },
                'history': history_list,
                'proposals': proposals_list,
                'total_events': len(history_list),
                'total_proposals': len(proposals_list)
            }
            
            # Adicionar metadados se solicitado
            if include_metadata:
                result['metadata'] = {
                    'client_name': pre_order.client.nome if pre_order.client else None,
                    'provider_name': pre_order.provider.nome if pre_order.provider else None,
                    'negotiation_duration_days': (
                        (pre_order.updated_at - pre_order.created_at).days
                        if pre_order.updated_at else 0
                    ),
                    'is_excessive_negotiation': len(proposals_list) > PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD,
                    'has_extreme_proposals': any(p['is_extreme'] for p in proposals_list),
                    'query_timestamp': datetime.utcnow().isoformat()
                }
            
            logger.info(f"Histórico completo obtido para pré-ordem {pre_order_id}: {len(history_list)} eventos, {len(proposals_list)} propostas")
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter histórico da pré-ordem {pre_order_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao obter histórico: {str(e)}'
            }
    
    @staticmethod
    def check_excessive_negotiations(pre_order_id: int) -> Dict:
        """
        Verifica se uma pré-ordem tem negociações excessivas (>5 propostas)
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            dict: Resultado da verificação com alerta se necessário
            
        Requirements: 17.5
        """
        try:
            # Buscar pré-ordem
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                return {
                    'success': False,
                    'error': f'Pré-ordem {pre_order_id} não encontrada'
                }
            
            # Contar propostas
            proposal_count = PreOrderProposal.query.filter_by(
                pre_order_id=pre_order_id
            ).count()
            
            is_excessive = proposal_count > PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD
            
            result = {
                'success': True,
                'pre_order_id': pre_order_id,
                'proposal_count': proposal_count,
                'threshold': PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD,
                'is_excessive': is_excessive,
                'alert_level': 'warning' if is_excessive else 'normal'
            }
            
            if is_excessive:
                result['alert_message'] = (
                    f'Pré-ordem #{pre_order_id} tem {proposal_count} propostas, '
                    f'excedendo o limite de {PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD}. '
                    f'Considere revisar a negociação.'
                )
                logger.warning(result['alert_message'])
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao verificar negociações excessivas da pré-ordem {pre_order_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao verificar negociações: {str(e)}'
            }
    
    @staticmethod
    def generate_negotiation_report(
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Gera relatório de negociações com métricas agregadas
        
        Args:
            start_date: Data inicial do período (opcional)
            end_date: Data final do período (opcional)
            
        Returns:
            dict: Relatório com tempo médio, taxa de conversão, etc.
            
        Requirements: 17.3, 17.5
        """
        try:
            # Definir período padrão (últimos 30 dias)
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query base para pré-ordens no período
            base_query = PreOrder.query.filter(
                PreOrder.created_at >= start_date,
                PreOrder.created_at <= end_date
            )
            
            # Total de pré-ordens
            total_pre_orders = base_query.count()
            
            # Contagem por status
            status_counts = {}
            for status in PreOrderStatus:
                count = base_query.filter(PreOrder.status == status.value).count()
                status_counts[status.value] = count
            
            # Taxa de conversão
            converted_count = status_counts.get(PreOrderStatus.CONVERTIDA.value, 0)
            conversion_rate = (converted_count / total_pre_orders * 100) if total_pre_orders > 0 else 0
            
            # Taxa de cancelamento
            cancelled_count = status_counts.get(PreOrderStatus.CANCELADA.value, 0)
            cancellation_rate = (cancelled_count / total_pre_orders * 100) if total_pre_orders > 0 else 0
            
            # Taxa de expiração
            expired_count = status_counts.get(PreOrderStatus.EXPIRADA.value, 0)
            expiration_rate = (expired_count / total_pre_orders * 100) if total_pre_orders > 0 else 0
            
            # Tempo médio de negociação (para pré-ordens convertidas)
            converted_pre_orders = base_query.filter(
                PreOrder.status == PreOrderStatus.CONVERTIDA.value,
                PreOrder.converted_at.isnot(None)
            ).all()
            
            if converted_pre_orders:
                total_negotiation_time = sum(
                    (po.converted_at - po.created_at).total_seconds()
                    for po in converted_pre_orders
                )
                avg_negotiation_seconds = total_negotiation_time / len(converted_pre_orders)
                avg_negotiation_days = avg_negotiation_seconds / 86400
            else:
                avg_negotiation_days = 0
            
            # Média de propostas por pré-ordem
            pre_order_ids = [po.id for po in base_query.all()]
            if pre_order_ids:
                total_proposals = PreOrderProposal.query.filter(
                    PreOrderProposal.pre_order_id.in_(pre_order_ids)
                ).count()
                avg_proposals = total_proposals / len(pre_order_ids)
            else:
                total_proposals = 0
                avg_proposals = 0
            
            # Pré-ordens com negociações excessivas
            excessive_count = 0
            for po_id in pre_order_ids:
                proposal_count = PreOrderProposal.query.filter_by(pre_order_id=po_id).count()
                if proposal_count > PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD:
                    excessive_count += 1
            
            # Valor total negociado (pré-ordens convertidas)
            total_value = sum(
                float(po.current_value) for po in converted_pre_orders
            ) if converted_pre_orders else 0
            
            result = {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'summary': {
                    'total_pre_orders': total_pre_orders,
                    'converted': converted_count,
                    'cancelled': cancelled_count,
                    'expired': expired_count,
                    'in_progress': status_counts.get(PreOrderStatus.EM_NEGOCIACAO.value, 0) + 
                                   status_counts.get(PreOrderStatus.AGUARDANDO_RESPOSTA.value, 0) +
                                   status_counts.get(PreOrderStatus.PRONTO_CONVERSAO.value, 0)
                },
                'rates': {
                    'conversion_rate': round(conversion_rate, 2),
                    'cancellation_rate': round(cancellation_rate, 2),
                    'expiration_rate': round(expiration_rate, 2)
                },
                'metrics': {
                    'avg_negotiation_days': round(avg_negotiation_days, 2),
                    'avg_proposals_per_pre_order': round(avg_proposals, 2),
                    'total_proposals': total_proposals,
                    'excessive_negotiations_count': excessive_count,
                    'total_value_converted': round(total_value, 2)
                },
                'status_breakdown': status_counts,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Relatório de negociação gerado: {total_pre_orders} pré-ordens, "
                f"taxa de conversão: {conversion_rate:.2f}%"
            )
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao gerar relatório de negociação: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao gerar relatório: {str(e)}'
            }
    
    @staticmethod
    def generate_extreme_proposals_report(
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        Gera relatório de propostas extremas (suspeitas)
        
        Propostas extremas são aquelas com:
        - Aumento > 100% do valor
        - Redução > 50% do valor
        
        Args:
            start_date: Data inicial do período (opcional)
            end_date: Data final do período (opcional)
            
        Returns:
            dict: Relatório com propostas suspeitas
            
        Requirements: 17.5, 19.1-19.3
        """
        try:
            # Definir período padrão (últimos 30 dias)
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Buscar todas as propostas no período
            proposals = PreOrderProposal.query.filter(
                PreOrderProposal.created_at >= start_date,
                PreOrderProposal.created_at <= end_date
            ).all()
            
            extreme_proposals = []
            
            for proposal in proposals:
                if not proposal.proposed_value or not proposal.pre_order:
                    continue
                
                current_value = proposal.pre_order.current_value
                if current_value == 0:
                    continue
                
                # Calcular percentual de mudança
                change_percent = ((proposal.proposed_value - current_value) / current_value) * 100
                
                is_extreme_increase = change_percent > PreOrderAuditService.EXTREME_INCREASE_THRESHOLD
                is_extreme_decrease = change_percent < PreOrderAuditService.EXTREME_DECREASE_THRESHOLD
                
                if is_extreme_increase or is_extreme_decrease:
                    extreme_proposals.append({
                        'proposal_id': proposal.id,
                        'pre_order_id': proposal.pre_order_id,
                        'pre_order_title': proposal.pre_order.title,
                        'proposed_by': proposal.proposed_by,
                        'proposer_name': proposal.proposer.nome if proposal.proposer else 'Desconhecido',
                        'original_value': float(current_value),
                        'proposed_value': float(proposal.proposed_value),
                        'change_percent': round(change_percent, 2),
                        'change_type': 'increase' if is_extreme_increase else 'decrease',
                        'justification': proposal.justification,
                        'status': proposal.status,
                        'created_at': proposal.created_at.isoformat(),
                        'alert_level': 'high' if abs(change_percent) > 150 else 'medium'
                    })
            
            # Ordenar por percentual de mudança (mais extremos primeiro)
            extreme_proposals.sort(key=lambda x: abs(x['change_percent']), reverse=True)
            
            result = {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_proposals_analyzed': len(proposals),
                    'extreme_proposals_count': len(extreme_proposals),
                    'extreme_increases': sum(1 for p in extreme_proposals if p['change_type'] == 'increase'),
                    'extreme_decreases': sum(1 for p in extreme_proposals if p['change_type'] == 'decrease'),
                    'high_alert_count': sum(1 for p in extreme_proposals if p['alert_level'] == 'high')
                },
                'thresholds': {
                    'increase_threshold': PreOrderAuditService.EXTREME_INCREASE_THRESHOLD,
                    'decrease_threshold': PreOrderAuditService.EXTREME_DECREASE_THRESHOLD
                },
                'extreme_proposals': extreme_proposals,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            if extreme_proposals:
                logger.warning(
                    f"Relatório de propostas extremas: {len(extreme_proposals)} propostas suspeitas encontradas"
                )
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao gerar relatório de propostas extremas: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao gerar relatório: {str(e)}'
            }
    
    @staticmethod
    def log_audit_event(
        pre_order_id: int,
        event_type: str,
        actor_id: int,
        description: str,
        event_data: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict:
        """
        Registra um evento de auditoria com informações de IP e user agent
        
        Args:
            pre_order_id: ID da pré-ordem
            event_type: Tipo do evento
            actor_id: ID do usuário que executou a ação
            description: Descrição do evento
            event_data: Dados adicionais do evento (opcional)
            ip_address: Endereço IP do usuário (opcional)
            user_agent: User agent do navegador (opcional)
            
        Returns:
            dict: Resultado do registro
            
        Requirements: 17.1, 17.2
        """
        try:
            # Preparar dados do evento com informações de auditoria
            audit_data = event_data.copy() if event_data else {}
            
            # Adicionar informações de auditoria
            audit_data['audit'] = {
                'ip_address': ip_address,
                'user_agent': user_agent,
                'logged_at': datetime.utcnow().isoformat()
            }
            
            # Criar registro de histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type=event_type,
                actor_id=actor_id,
                description=description,
                event_data=audit_data
            )
            
            db.session.add(history_entry)
            db.session.commit()
            
            logger.info(
                f"Evento de auditoria registrado: {event_type} para pré-ordem {pre_order_id} "
                f"por usuário {actor_id} (IP: {ip_address})"
            )
            
            return {
                'success': True,
                'history_id': history_entry.id,
                'pre_order_id': pre_order_id,
                'event_type': event_type,
                'actor_id': actor_id,
                'created_at': history_entry.created_at.isoformat()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao registrar evento de auditoria: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao registrar evento: {str(e)}'
            }
    
    @staticmethod
    def get_pre_orders_requiring_attention() -> Dict:
        """
        Retorna pré-ordens que requerem atenção (excessivas, próximas de expirar, etc.)
        
        Returns:
            dict: Lista de pré-ordens que precisam de atenção
            
        Requirements: 17.5
        """
        try:
            attention_items = []
            
            # Pré-ordens próximas de expirar (menos de 24h)
            expiring_soon = PreOrder.query.filter(
                PreOrder.status.in_([
                    PreOrderStatus.EM_NEGOCIACAO.value,
                    PreOrderStatus.AGUARDANDO_RESPOSTA.value,
                    PreOrderStatus.PRONTO_CONVERSAO.value
                ]),
                PreOrder.expires_at <= datetime.utcnow() + timedelta(hours=24),
                PreOrder.expires_at > datetime.utcnow()
            ).all()
            
            for po in expiring_soon:
                attention_items.append({
                    'pre_order_id': po.id,
                    'title': po.title,
                    'reason': 'expiring_soon',
                    'message': f'Pré-ordem expira em menos de 24 horas',
                    'expires_at': po.expires_at.isoformat(),
                    'priority': 'high'
                })
            
            # Pré-ordens com negociações excessivas
            active_pre_orders = PreOrder.query.filter(
                PreOrder.status.in_([
                    PreOrderStatus.EM_NEGOCIACAO.value,
                    PreOrderStatus.AGUARDANDO_RESPOSTA.value
                ])
            ).all()
            
            for po in active_pre_orders:
                proposal_count = PreOrderProposal.query.filter_by(pre_order_id=po.id).count()
                if proposal_count > PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD:
                    attention_items.append({
                        'pre_order_id': po.id,
                        'title': po.title,
                        'reason': 'excessive_negotiations',
                        'message': f'Pré-ordem tem {proposal_count} propostas (limite: {PreOrderAuditService.EXCESSIVE_PROPOSALS_THRESHOLD})',
                        'proposal_count': proposal_count,
                        'priority': 'medium'
                    })
            
            # Pré-ordens prontas para conversão há mais de 24h
            ready_too_long = PreOrder.query.filter(
                PreOrder.status == PreOrderStatus.PRONTO_CONVERSAO.value,
                PreOrder.updated_at <= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            for po in ready_too_long:
                attention_items.append({
                    'pre_order_id': po.id,
                    'title': po.title,
                    'reason': 'ready_not_converted',
                    'message': 'Pré-ordem pronta para conversão há mais de 24 horas',
                    'ready_since': po.updated_at.isoformat(),
                    'priority': 'medium'
                })
            
            # Ordenar por prioridade
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            attention_items.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            return {
                'success': True,
                'total_items': len(attention_items),
                'items': attention_items,
                'summary': {
                    'expiring_soon': sum(1 for i in attention_items if i['reason'] == 'expiring_soon'),
                    'excessive_negotiations': sum(1 for i in attention_items if i['reason'] == 'excessive_negotiations'),
                    'ready_not_converted': sum(1 for i in attention_items if i['reason'] == 'ready_not_converted')
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Erro ao obter pré-ordens que requerem atenção: {str(e)}")
            return {
                'success': False,
                'error': f'Erro ao obter itens: {str(e)}'
            }
