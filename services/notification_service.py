#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import flash, url_for
from models import db, User, Invite, Proposal
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Serviço para gerenciar notificações do sistema de propostas"""
    
    @staticmethod
    def notify_proposal_created(invite_id: int, client_id: int, proposal: Proposal) -> Dict:
        """
        Notifica o cliente quando uma proposta é criada
        
        Requirements: 1.1, 9.1, 9.2, 9.3, 9.5
        """
        try:
            # Obter dados do convite e prestador
            invite = Invite.query.get(invite_id)
            if not invite:
                raise ValueError("Convite não encontrado")
            
            client = User.query.get(client_id)
            if not client:
                raise ValueError("Cliente não encontrado")
            
            prestador = User.query.get(proposal.prestador_id)
            prestador_name = prestador.nome if prestador else "Prestador"
            
            # Calcular diferença de valor
            value_difference = proposal.proposed_value - proposal.original_value
            is_increase = value_difference > 0
            
            # Criar mensagem clara e acionável
            if is_increase:
                message = (f"Nova proposta de alteração recebida! "
                          f"{prestador_name} propôs aumentar o valor de "
                          f"R$ {proposal.original_value:.2f} para R$ {proposal.proposed_value:.2f} "
                          f"(+R$ {value_difference:.2f}). "
                          f"Verifique se você tem saldo suficiente e responda à proposta.")
            else:
                message = (f"Nova proposta de alteração recebida! "
                          f"{prestador_name} propôs reduzir o valor de "
                          f"R$ {proposal.original_value:.2f} para R$ {proposal.proposed_value:.2f} "
                          f"(-R$ {abs(value_difference):.2f}). "
                          f"Responda à proposta para continuar.")
            
            # Flash message para feedback imediato
            flash(message, 'info')
            
            # Log da notificação
            logger.info(f"Notificação de proposta criada enviada - "
                       f"Cliente: {client_id}, Convite: {invite_id}, "
                       f"Proposta: {proposal.id}, Valor: {proposal.original_value} -> {proposal.proposed_value}")
            
            return {
                'success': True,
                'message': message,
                'notification_type': 'proposal_created',
                'proposal_id': proposal.id,
                'invite_id': invite_id,
                'client_id': client_id,
                'prestador_name': prestador_name,
                'original_value': float(proposal.original_value),
                'proposed_value': float(proposal.proposed_value),
                'value_difference': float(value_difference),
                'is_increase': is_increase,
                'action_url': url_for('cliente.ver_convite', invite_id=invite_id),
                'justification': proposal.justification
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de proposta: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def notify_proposal_response(invite_id: int, prestador_id: int, status: str, 
                               proposal: Proposal, client_response_reason: str = None) -> Dict:
        """
        Notifica o prestador sobre a resposta do cliente à proposta
        
        Requirements: 2.2, 6.5, 9.1, 9.2, 9.3, 9.5
        """
        try:
            # Obter dados do convite e cliente
            invite = Invite.query.get(invite_id)
            if not invite:
                raise ValueError("Convite não encontrado")
            
            prestador = User.query.get(prestador_id)
            if not prestador:
                raise ValueError("Prestador não encontrado")
            
            client = User.query.get(invite.client_id)
            client_name = client.nome if client else "Cliente"
            
            # Criar mensagem baseada no status
            if status == 'accepted':
                message = (f"Proposta aceita! "
                          f"{client_name} aceitou sua proposta de R$ {proposal.proposed_value:.2f} "
                          f"para o serviço '{invite.service_title}'. "
                          f"Agora você pode aceitar o convite com o novo valor.")
                flash_category = 'success'
                
            elif status == 'rejected':
                reason_text = f" Motivo: {client_response_reason}" if client_response_reason else ""
                message = (f"Proposta rejeitada. "
                          f"{client_name} rejeitou sua proposta de R$ {proposal.proposed_value:.2f} "
                          f"para o serviço '{invite.service_title}'.{reason_text} "
                          f"O convite retornou ao valor original de R$ {proposal.original_value:.2f}.")
                flash_category = 'warning'
                
            else:
                message = f"Status da proposta atualizado para: {status}"
                flash_category = 'info'
            
            # Flash message para feedback imediato
            flash(message, flash_category)
            
            # Log da notificação
            logger.info(f"Notificação de resposta de proposta enviada - "
                       f"Prestador: {prestador_id}, Convite: {invite_id}, "
                       f"Proposta: {proposal.id}, Status: {status}")
            
            return {
                'success': True,
                'message': message,
                'notification_type': 'proposal_response',
                'proposal_id': proposal.id,
                'invite_id': invite_id,
                'prestador_id': prestador_id,
                'client_name': client_name,
                'status': status,
                'original_value': float(proposal.original_value),
                'proposed_value': float(proposal.proposed_value),
                'client_response_reason': client_response_reason,
                'action_url': url_for('prestador.ver_convite', token=invite.token) if hasattr(invite, 'token') else url_for('prestador.convites')
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar resposta de proposta: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def notify_balance_insufficient(client_id: int, required_amount: Decimal, 
                                  current_balance: Decimal, proposal: Proposal) -> Dict:
        """
        Notifica o cliente sobre saldo insuficiente para aceitar proposta
        
        Requirements: 3.1, 3.2, 3.3, 9.1, 9.3
        """
        try:
            client = User.query.get(client_id)
            if not client:
                raise ValueError("Cliente não encontrado")
            
            shortfall = required_amount - current_balance
            
            # Criar mensagem clara sobre saldo insuficiente
            message = (f"Saldo insuficiente para aceitar a proposta de R$ {proposal.proposed_value:.2f}. "
                      f"Você precisa de R$ {required_amount:.2f} no total "
                      f"(proposta + taxa de contestação), mas tem apenas R$ {current_balance:.2f}. "
                      f"Adicione pelo menos R$ {shortfall:.2f} para continuar.")
            
            # Flash message para feedback imediato
            flash(message, 'warning')
            
            # Log da notificação
            logger.info(f"Notificação de saldo insuficiente enviada - "
                       f"Cliente: {client_id}, Proposta: {proposal.id}, "
                       f"Necessário: {required_amount}, Atual: {current_balance}, "
                       f"Faltam: {shortfall}")
            
            return {
                'success': True,
                'message': message,
                'notification_type': 'balance_insufficient',
                'proposal_id': proposal.id,
                'client_id': client_id,
                'required_amount': float(required_amount),
                'current_balance': float(current_balance),
                'shortfall': float(shortfall),
                'proposed_value': float(proposal.proposed_value),
                'action_url': url_for('cliente.solicitar_tokens'),
                'add_balance_suggestion': float(shortfall)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar saldo insuficiente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def notify_proposal_cancelled(invite_id: int, client_id: int, proposal: Proposal) -> Dict:
        """
        Notifica o cliente quando o prestador cancela uma proposta
        
        Requirements: 5.5, 9.1, 9.5
        """
        try:
            invite = Invite.query.get(invite_id)
            if not invite:
                raise ValueError("Convite não encontrado")
            
            client = User.query.get(client_id)
            if not client:
                raise ValueError("Cliente não encontrado")
            
            prestador = User.query.get(proposal.prestador_id)
            prestador_name = prestador.nome if prestador else "Prestador"
            
            message = (f"Proposta cancelada. "
                      f"{prestador_name} cancelou a proposta de alteração "
                      f"de R$ {proposal.proposed_value:.2f}. "
                      f"O convite retornou ao valor original de R$ {proposal.original_value:.2f}.")
            
            # Flash message para feedback imediato
            flash(message, 'info')
            
            # Log da notificação
            logger.info(f"Notificação de cancelamento de proposta enviada - "
                       f"Cliente: {client_id}, Convite: {invite_id}, "
                       f"Proposta: {proposal.id}")
            
            return {
                'success': True,
                'message': message,
                'notification_type': 'proposal_cancelled',
                'proposal_id': proposal.id,
                'invite_id': invite_id,
                'client_id': client_id,
                'prestador_name': prestador_name,
                'original_value': float(proposal.original_value),
                'proposed_value': float(proposal.proposed_value),
                'action_url': url_for('cliente.ver_convite', invite_id=invite_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar cancelamento de proposta: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_proposal_notifications_for_client(client_id: int) -> List[Dict]:
        """
        Retorna notificações de propostas pendentes para o cliente
        
        Usado para exibir alertas no dashboard do cliente
        
        Requirements: 9.1, 9.2, 9.3
        """
        try:
            # Buscar propostas pendentes para convites do cliente
            pending_proposals = db.session.query(Proposal).join(Invite).filter(
                and_(
                    Invite.client_id == client_id,
                    Proposal.status == 'pending'
                )
            ).all()
            
            notifications = []
            
            for proposal in pending_proposals:
                invite = proposal.invite
                prestador = User.query.get(proposal.prestador_id)
                prestador_name = prestador.nome if prestador else "Prestador"
                
                # Verificar se é aumento ou redução
                value_difference = proposal.proposed_value - proposal.original_value
                is_increase = value_difference > 0
                
                if is_increase:
                    message = (f"Proposta de aumento pendente: {prestador_name} "
                              f"propôs R$ {proposal.proposed_value:.2f} "
                              f"(+R$ {value_difference:.2f}) para '{invite.service_title}'")
                    alert_type = 'warning'
                else:
                    message = (f"Proposta de redução pendente: {prestador_name} "
                              f"propôs R$ {proposal.proposed_value:.2f} "
                              f"(-R$ {abs(value_difference):.2f}) para '{invite.service_title}'")
                    alert_type = 'info'
                
                notifications.append({
                    'tipo': alert_type,
                    'mensagem': message,
                    'proposal_id': proposal.id,
                    'invite_id': invite.id,
                    'action_url': url_for('cliente.ver_convite', invite_id=invite.id),
                    'created_at': proposal.created_at,
                    'is_increase': is_increase,
                    'original_value': float(proposal.original_value),
                    'proposed_value': float(proposal.proposed_value),
                    'prestador_name': prestador_name,
                    'service_title': invite.service_title
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erro ao buscar notificações de propostas para cliente {client_id}: {str(e)}")
            return []
    
    @staticmethod
    def get_proposal_notifications_for_prestador(prestador_id: int) -> List[Dict]:
        """
        Retorna notificações de propostas para o prestador
        
        Usado para exibir alertas no dashboard do prestador
        
        Requirements: 6.5, 9.1, 9.5
        """
        try:
            # Buscar propostas do prestador com respostas recentes
            recent_proposals = Proposal.query.filter(
                and_(
                    Proposal.prestador_id == prestador_id,
                    Proposal.status.in_(['accepted', 'rejected']),
                    Proposal.responded_at >= datetime.utcnow() - timedelta(days=7)  # Últimos 7 dias
                )
            ).order_by(Proposal.responded_at.desc()).limit(5).all()
            
            notifications = []
            
            for proposal in recent_proposals:
                invite = proposal.invite
                client = User.query.get(invite.client_id)
                client_name = client.nome if client else "Cliente"
                
                if proposal.status == 'accepted':
                    message = (f"Proposta aceita: {client_name} aceitou "
                              f"R$ {proposal.proposed_value:.2f} para '{invite.service_title}'. "
                              f"Você pode aceitar o convite agora.")
                    alert_type = 'success'
                    
                elif proposal.status == 'rejected':
                    reason_text = f" ({proposal.client_response_reason})" if proposal.client_response_reason else ""
                    message = (f"Proposta rejeitada: {client_name} rejeitou "
                              f"R$ {proposal.proposed_value:.2f} para '{invite.service_title}'{reason_text}")
                    alert_type = 'warning'
                
                notifications.append({
                    'tipo': alert_type,
                    'mensagem': message,
                    'proposal_id': proposal.id,
                    'invite_id': invite.id,
                    'action_url': url_for('prestador.ver_convite', token=invite.token) if hasattr(invite, 'token') else url_for('prestador.convites'),
                    'responded_at': proposal.responded_at,
                    'status': proposal.status,
                    'original_value': float(proposal.original_value),
                    'proposed_value': float(proposal.proposed_value),
                    'client_name': client_name,
                    'service_title': invite.service_title
                })
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erro ao buscar notificações de propostas para prestador {prestador_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_proposal_summary_notification(proposal: Proposal, action: str) -> Dict:
        """
        Cria um resumo de notificação para uma proposta
        
        Usado para logs e auditoria
        
        Requirements: 8.1, 8.2, 8.3
        """
        try:
            invite = proposal.invite
            prestador = User.query.get(proposal.prestador_id)
            client = User.query.get(invite.client_id)
            
            summary = {
                'proposal_id': proposal.id,
                'invite_id': invite.id,
                'action': action,
                'timestamp': datetime.utcnow(),
                'prestador_id': proposal.prestador_id,
                'prestador_name': prestador.nome if prestador else "Prestador não encontrado",
                'client_id': invite.client_id,
                'client_name': client.nome if client else "Cliente não encontrado",
                'service_title': invite.service_title,
                'original_value': float(proposal.original_value),
                'proposed_value': float(proposal.proposed_value),
                'value_difference': float(proposal.proposed_value - proposal.original_value),
                'is_increase': proposal.proposed_value > proposal.original_value,
                'status': proposal.status,
                'justification': proposal.justification,
                'client_response_reason': proposal.client_response_reason
            }
            
            # Log do resumo
            logger.info(f"Resumo de proposta - Ação: {action}, "
                       f"Proposta: {proposal.id}, Convite: {invite.id}, "
                       f"Valor: {proposal.original_value} -> {proposal.proposed_value}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao criar resumo de notificação: {str(e)}")
            return {}
    
    @staticmethod
    def format_currency(value: Decimal) -> str:
        """Formata valor monetário para exibição"""
        return f"R$ {value:.2f}"
    
    @staticmethod
    def format_value_comparison(original: Decimal, proposed: Decimal) -> str:
        """Formata comparação de valores para exibição"""
        difference = proposed - original
        if difference > 0:
            return f"R$ {original:.2f} → R$ {proposed:.2f} (+R$ {difference:.2f})"
        elif difference < 0:
            return f"R$ {original:.2f} → R$ {proposed:.2f} (-R$ {abs(difference):.2f})"
        else:
            return f"R$ {original:.2f} (sem alteração)"
    
    # ==================== NOTIFICAÇÕES DE ORDENS ====================
    
    @staticmethod
    def notify_order_created(order, client_name: str = None, provider_name: str = None) -> Dict:
        """
        Notifica ambas as partes quando uma ordem é criada a partir de um convite aceito
        
        Envia notificação ao cliente e ao prestador informando:
        - Número da ordem
        - Valor do serviço
        - Data de entrega
        - Link direto para visualizar a ordem
        
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        try:
            from models import User
            
            # Obter nomes dos usuários se não fornecidos
            if not client_name:
                client = User.query.get(order.client_id)
                client_name = client.nome if client else "Cliente"
            
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            # Formatar data de entrega
            delivery_date_str = "Não definida"
            if hasattr(order, 'service_deadline') and order.service_deadline:
                delivery_date_str = order.service_deadline.strftime('%d/%m/%Y')
            
            # Mensagem para o cliente
            client_message = (
                f"✅ Ordem #{order.id} criada com sucesso! "
                f"Serviço: '{order.title}'. "
                f"Prestador: {provider_name}. "
                f"Valor: R$ {order.value:.2f}. "
                f"Data de entrega: {delivery_date_str}. "
                f"Os valores foram bloqueados em garantia até a conclusão do serviço."
            )
            
            # Mensagem para o prestador
            provider_message = (
                f"✅ Nova ordem #{order.id} criada! "
                f"Serviço: '{order.title}'. "
                f"Cliente: {client_name}. "
                f"Valor: R$ {order.value:.2f}. "
                f"Data de entrega: {delivery_date_str}. "
                f"Execute o serviço e marque como concluído quando finalizar."
            )
            
            # Flash messages
            flash(client_message, 'success')
            
            logger.info(
                f"Notificação de ordem criada - Ordem: {order.id}, "
                f"Cliente: {order.client_id}, Prestador: {order.provider_id}, "
                f"Valor: R$ {order.value:.2f}, Data entrega: {delivery_date_str}"
            )
            
            return {
                'success': True,
                'notification_type': 'order_created',
                'order_id': order.id,
                'client_message': client_message,
                'provider_message': provider_message,
                'client_id': order.client_id,
                'provider_id': order.provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'service_title': order.title,
                'value': float(order.value),
                'delivery_date': delivery_date_str,
                'action_url_client': url_for('order.ver_ordem', order_id=order.id),
                'action_url_provider': url_for('order.ver_ordem', order_id=order.id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_insufficient_balance(user_id: int, user_type: str, required_amount: Decimal, 
                                   current_balance: Decimal, invite_id: int = None) -> Dict:
        """
        Notifica usuário quando tentativa de aceitação de convite falha por saldo insuficiente
        
        Inclui:
        - Valor necessário
        - Saldo atual
        - Sugestão para adicionar saldo
        
        Args:
            user_id: ID do usuário
            user_type: 'cliente' ou 'prestador'
            required_amount: Valor total necessário
            current_balance: Saldo atual do usuário
            invite_id: ID do convite (opcional)
        
        Requirements: 6.5, 8.3, 8.4
        """
        try:
            from models import User
            
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            shortfall = required_amount - current_balance
            
            # Mensagem específica por tipo de usuário
            if user_type == 'cliente':
                message = (
                    f"❌ Saldo insuficiente para aceitar o convite. "
                    f"Você precisa de R$ {required_amount:.2f} no total "
                    f"(valor do serviço + taxa de contestação), mas tem apenas R$ {current_balance:.2f}. "
                    f"Adicione pelo menos R$ {shortfall:.2f} para continuar."
                )
            else:  # prestador
                message = (
                    f"❌ Saldo insuficiente para aceitar o convite. "
                    f"Você precisa de R$ {required_amount:.2f} para a taxa de contestação, "
                    f"mas tem apenas R$ {current_balance:.2f}. "
                    f"Adicione pelo menos R$ {shortfall:.2f} para continuar."
                )
            
            # Flash message para feedback imediato
            flash(message, 'warning')
            
            # Log da notificação
            logger.info(
                f"Notificação de saldo insuficiente enviada - "
                f"Usuário: {user_id} ({user_type}), Convite: {invite_id}, "
                f"Necessário: R$ {required_amount:.2f}, Atual: R$ {current_balance:.2f}, "
                f"Faltam: R$ {shortfall:.2f}"
            )
            
            # URL para adicionar saldo
            add_balance_url = url_for('cliente.solicitar_tokens') if user_type == 'cliente' else url_for('prestador.solicitar_tokens')
            
            return {
                'success': True,
                'message': message,
                'notification_type': 'insufficient_balance',
                'user_id': user_id,
                'user_type': user_type,
                'invite_id': invite_id,
                'required_amount': float(required_amount),
                'current_balance': float(current_balance),
                'shortfall': float(shortfall),
                'action_url': add_balance_url,
                'add_balance_suggestion': float(shortfall)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar saldo insuficiente para usuário {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def notify_service_completed(order, provider_name: str = None) -> Dict:
        """
        Notifica o cliente quando o prestador marca o serviço como concluído
        DESTAQUE: Prazo de 36 horas para confirmar ou contestar
        
        Requirements: 11.2, 3.5
        """
        try:
            from models import User
            
            # Obter nome do prestador se não fornecido
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            # Calcular horas restantes
            hours_remaining = 36
            if order.confirmation_deadline:
                time_diff = order.confirmation_deadline - datetime.utcnow()
                hours_remaining = max(0, int(time_diff.total_seconds() / 3600))
            
            # Mensagem com DESTAQUE para o prazo
            message = (
                f"⚠️ ATENÇÃO: Serviço concluído! "
                f"{provider_name} marcou o serviço '{order.title}' como concluído. "
                f"Você tem 36 HORAS para confirmar ou contestar o serviço. "
                f"Após esse prazo, a ordem será AUTOMATICAMENTE confirmada e o pagamento liberado. "
                f"Prazo: {order.confirmation_deadline.strftime('%d/%m/%Y às %H:%M') if order.confirmation_deadline else 'N/A'}"
            )
            
            flash(message, 'warning')
            
            logger.info(
                f"Notificação de serviço concluído - Ordem: {order.id}, "
                f"Cliente: {order.client_id}, Prazo: {order.confirmation_deadline}"
            )
            
            return {
                'success': True,
                'notification_type': 'service_completed',
                'order_id': order.id,
                'message': message,
                'client_id': order.client_id,
                'provider_name': provider_name,
                'service_title': order.title,
                'value': float(order.value),
                'hours_remaining': hours_remaining,
                'confirmation_deadline': order.confirmation_deadline.isoformat() if order.confirmation_deadline else None,
                'action_url': url_for('cliente.ver_ordem', order_id=order.id),
                'urgent': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar serviço concluído da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_confirmation_reminder(order) -> Dict:
        """
        Envia lembrete ao cliente quando faltam 12 horas para confirmação automática
        
        Requirements: 11.3, 5.6
        """
        try:
            from models import User
            
            client = User.query.get(order.client_id)
            client_name = client.nome if client else "Cliente"
            
            # Calcular horas restantes
            hours_remaining = 12
            if order.confirmation_deadline:
                time_diff = order.confirmation_deadline - datetime.utcnow()
                hours_remaining = max(0, int(time_diff.total_seconds() / 3600))
            
            message = (
                f"🔔 LEMBRETE URGENTE: Faltam apenas {hours_remaining} horas para a confirmação automática! "
                f"A ordem #{order.id} ('{order.title}') será automaticamente confirmada em breve. "
                f"Se houver algum problema com o serviço, conteste AGORA antes que o prazo expire. "
                f"Prazo final: {order.confirmation_deadline.strftime('%d/%m/%Y às %H:%M') if order.confirmation_deadline else 'N/A'}"
            )
            
            flash(message, 'danger')
            
            logger.info(
                f"Lembrete de confirmação enviado - Ordem: {order.id}, "
                f"Cliente: {order.client_id}, Horas restantes: {hours_remaining}"
            )
            
            return {
                'success': True,
                'notification_type': 'confirmation_reminder',
                'order_id': order.id,
                'message': message,
                'client_id': order.client_id,
                'service_title': order.title,
                'hours_remaining': hours_remaining,
                'confirmation_deadline': order.confirmation_deadline.isoformat() if order.confirmation_deadline else None,
                'action_url': url_for('cliente.ver_ordem', order_id=order.id),
                'urgent': True,
                'priority': 'high'
            }
            
        except Exception as e:
            logger.error(f"Erro ao enviar lembrete de confirmação da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_auto_confirmed(order, client_name: str = None, provider_name: str = None) -> Dict:
        """
        Notifica ambas as partes quando uma ordem é automaticamente confirmada após 36h
        
        Requirements: 11.4, 5.5
        """
        try:
            from models import User
            
            # Obter nomes dos usuários se não fornecidos
            if not client_name:
                client = User.query.get(order.client_id)
                client_name = client.nome if client else "Cliente"
            
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            # Mensagem para o cliente
            client_message = (
                f"Ordem #{order.id} confirmada automaticamente. "
                f"O prazo de 36 horas expirou sem contestação. "
                f"Serviço: '{order.title}'. "
                f"O pagamento de R$ {order.value:.2f} foi processado e liberado para {provider_name}."
            )
            
            # Mensagem para o prestador
            provider_message = (
                f"✅ Ordem #{order.id} confirmada automaticamente! "
                f"O cliente não contestou dentro de 36 horas. "
                f"Serviço: '{order.title}'. "
                f"Você recebeu R$ {order.value - (order.platform_fee or 0):.2f} "
                f"(valor líquido após taxa da plataforma)."
            )
            
            flash(client_message, 'info')
            
            logger.info(
                f"Notificação de confirmação automática - Ordem: {order.id}, "
                f"Cliente: {order.client_id}, Prestador: {order.provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'auto_confirmed',
                'order_id': order.id,
                'client_message': client_message,
                'provider_message': provider_message,
                'client_id': order.client_id,
                'provider_id': order.provider_id,
                'service_title': order.title,
                'value': float(order.value),
                'platform_fee': float(order.platform_fee or 0),
                'action_url_client': url_for('cliente.ver_ordem', order_id=order.id),
                'action_url_provider': url_for('prestador.ver_ordem', order_id=order.id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar confirmação automática da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_order_cancelled(order, cancelled_by_name: str = None, injured_party_name: str = None, 
                              cancellation_fee: Decimal = None) -> Dict:
        """
        Notifica a parte prejudicada quando uma ordem é cancelada
        
        Requirements: 11.5
        """
        try:
            from models import User
            
            # Identificar quem cancelou
            is_client_cancelling = (order.cancelled_by == order.client_id)
            
            if not cancelled_by_name:
                cancelled_by_user = User.query.get(order.cancelled_by)
                cancelled_by_name = cancelled_by_user.nome if cancelled_by_user else ("Cliente" if is_client_cancelling else "Prestador")
            
            # Identificar parte prejudicada
            injured_party_id = order.provider_id if is_client_cancelling else order.client_id
            
            if not injured_party_name:
                injured_party_user = User.query.get(injured_party_id)
                injured_party_name = injured_party_user.nome if injured_party_user else ("Prestador" if is_client_cancelling else "Cliente")
            
            # Obter valor da multa
            if cancellation_fee is None:
                cancellation_fee = order.cancellation_fee or Decimal('0')
            
            compensation = cancellation_fee / Decimal('2')  # 50% vai para a parte prejudicada
            
            # Mensagem para a parte prejudicada
            message = (
                f"Ordem #{order.id} foi cancelada por {cancelled_by_name}. "
                f"Serviço: '{order.title}'. "
                f"Motivo: {order.cancellation_reason}. "
                f"Você receberá R$ {compensation:.2f} como compensação "
                f"(50% da multa de cancelamento de R$ {cancellation_fee:.2f})."
            )
            
            flash(message, 'warning')
            
            logger.info(
                f"Notificação de cancelamento - Ordem: {order.id}, "
                f"Cancelado por: {order.cancelled_by}, Parte prejudicada: {injured_party_id}, "
                f"Compensação: R$ {compensation:.2f}"
            )
            
            return {
                'success': True,
                'notification_type': 'order_cancelled',
                'order_id': order.id,
                'message': message,
                'cancelled_by': order.cancelled_by,
                'cancelled_by_name': cancelled_by_name,
                'injured_party_id': injured_party_id,
                'injured_party_name': injured_party_name,
                'service_title': order.title,
                'cancellation_reason': order.cancellation_reason,
                'cancellation_fee': float(cancellation_fee),
                'compensation': float(compensation),
                'action_url': url_for('cliente.ver_ordem' if not is_client_cancelling else 'prestador.ver_ordem', order_id=order.id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar cancelamento da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_dispute_opened(order, client_name: str = None, provider_name: str = None) -> Dict:
        """
        Notifica o admin e o prestador quando o cliente abre uma contestação
        
        Requirements: 11.6
        """
        try:
            from models import User
            
            # Obter nomes dos usuários se não fornecidos
            if not client_name:
                client = User.query.get(order.client_id)
                client_name = client.nome if client else "Cliente"
            
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            # Mensagem para o admin
            admin_message = (
                f"⚠️ Nova contestação aberta! "
                f"Ordem #{order.id}: '{order.title}'. "
                f"Cliente {client_name} contestou o serviço executado por {provider_name}. "
                f"Valor: R$ {order.value:.2f}. "
                f"Motivo: {order.dispute_client_statement[:100]}... "
                f"Analise as provas e resolva a disputa."
            )
            
            # Mensagem para o prestador
            provider_message = (
                f"⚠️ Contestação aberta na ordem #{order.id}. "
                f"O cliente {client_name} contestou o serviço '{order.title}'. "
                f"Motivo: {order.dispute_client_statement}. "
                f"O admin irá analisar o caso e tomar uma decisão. "
                f"Aguarde a resolução da disputa."
            )
            
            flash(admin_message, 'warning')
            
            logger.info(
                f"Notificação de contestação aberta - Ordem: {order.id}, "
                f"Cliente: {order.client_id}, Prestador: {order.provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'dispute_opened',
                'order_id': order.id,
                'admin_message': admin_message,
                'provider_message': provider_message,
                'client_id': order.client_id,
                'provider_id': order.provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'service_title': order.title,
                'value': float(order.value),
                'dispute_reason': order.dispute_client_statement,
                'evidence_count': len(order.dispute_evidence_urls or []),
                'action_url_admin': url_for('admin.arbitrar_contestacao', order_id=order.id),
                'action_url_provider': url_for('prestador.ver_ordem', order_id=order.id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar abertura de contestação da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_admin_dispute_response(order, provider_name: str = None) -> Dict:
        """
        Notifica o admin quando o prestador responde à contestação
        
        Requirements: 11.6
        """
        try:
            from models import User
            
            # Obter nome do prestador se não fornecido
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            # Mensagem para o admin
            admin_message = (
                f"📝 Resposta à contestação recebida! "
                f"Ordem #{order.id}: '{order.title}'. "
                f"Prestador {provider_name} respondeu à contestação. "
                f"Valor: R$ {order.value:.2f}. "
                f"Resposta: {order.dispute_provider_response[:100]}... "
                f"Analise as provas de ambas as partes e resolva a disputa."
            )
            
            flash(admin_message, 'info')
            
            logger.info(
                f"Notificação de resposta à contestação - Ordem: {order.id}, "
                f"Prestador: {order.provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'dispute_response',
                'order_id': order.id,
                'admin_message': admin_message,
                'provider_id': order.provider_id,
                'provider_name': provider_name,
                'service_title': order.title,
                'value': float(order.value),
                'provider_response': order.dispute_provider_response,
                'evidence_count': len([e for e in (order.dispute_evidence_urls or []) if e.get('uploaded_by') == 'provider']),
                'action_url_admin': url_for('admin.arbitrar_contestacao', order_id=order.id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar resposta à contestação da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_dispute_resolved(order, winner: str, client_name: str = None, provider_name: str = None) -> Dict:
        """
        Notifica ambas as partes quando o admin resolve uma contestação
        
        Requirements: 11.7
        """
        try:
            from models import User
            
            # Obter nomes dos usuários se não fornecidos
            if not client_name:
                client = User.query.get(order.client_id)
                client_name = client.nome if client else "Cliente"
            
            if not provider_name:
                provider = User.query.get(order.provider_id)
                provider_name = provider.nome if provider else "Prestador"
            
            winner_name = client_name if winner == 'client' else provider_name
            loser_name = provider_name if winner == 'client' else client_name
            
            # Mensagem para o vencedor
            if winner == 'client':
                winner_message = (
                    f"✅ Disputa resolvida a seu favor! "
                    f"Ordem #{order.id}: '{order.title}'. "
                    f"O admin analisou o caso e decidiu a seu favor. "
                    f"O valor de R$ {order.value:.2f} foi devolvido para sua carteira. "
                    f"Notas do admin: {order.dispute_admin_notes or 'Nenhuma nota adicional.'}"
                )
                winner_url = url_for('cliente.ver_ordem', order_id=order.id)
            else:
                net_amount = order.value - (order.platform_fee or 0)
                winner_message = (
                    f"✅ Disputa resolvida a seu favor! "
                    f"Ordem #{order.id}: '{order.title}'. "
                    f"O admin analisou o caso e decidiu a seu favor. "
                    f"Você recebeu R$ {net_amount:.2f} (valor líquido após taxa da plataforma). "
                    f"Notas do admin: {order.dispute_admin_notes or 'Nenhuma nota adicional.'}"
                )
                winner_url = url_for('prestador.ver_ordem', order_id=order.id)
            
            # Mensagem para o perdedor
            if winner == 'client':
                loser_message = (
                    f"❌ Disputa resolvida contra você. "
                    f"Ordem #{order.id}: '{order.title}'. "
                    f"O admin analisou o caso e decidiu a favor do cliente. "
                    f"Você não receberá o pagamento desta ordem. "
                    f"Notas do admin: {order.dispute_admin_notes or 'Nenhuma nota adicional.'}"
                )
                loser_url = url_for('prestador.ver_ordem', order_id=order.id)
            else:
                loser_message = (
                    f"❌ Disputa resolvida contra você. "
                    f"Ordem #{order.id}: '{order.title}'. "
                    f"O admin analisou o caso e decidiu a favor do prestador. "
                    f"O pagamento foi liberado para o prestador. "
                    f"Notas do admin: {order.dispute_admin_notes or 'Nenhuma nota adicional.'}"
                )
                loser_url = url_for('cliente.ver_ordem', order_id=order.id)
            
            flash(winner_message if winner == 'client' else loser_message, 'info')
            
            logger.info(
                f"Notificação de disputa resolvida - Ordem: {order.id}, "
                f"Vencedor: {winner}, Cliente: {order.client_id}, Prestador: {order.provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'dispute_resolved',
                'order_id': order.id,
                'winner': winner,
                'winner_name': winner_name,
                'loser_name': loser_name,
                'winner_message': winner_message,
                'loser_message': loser_message,
                'client_id': order.client_id,
                'provider_id': order.provider_id,
                'service_title': order.title,
                'value': float(order.value),
                'admin_notes': order.dispute_admin_notes,
                'action_url_winner': winner_url,
                'action_url_loser': loser_url
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar resolução de disputa da ordem {order.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== NOTIFICAÇÕES DE PRÉ-ORDENS ====================
    
    @staticmethod
    def notify_pre_order_created(pre_order_id: int, user_id: int, user_type: str) -> Dict:
        """
        Notifica usuário quando uma pré-ordem é criada
        
        Requirements: 1.4, 11.1
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError("Pré-ordem não encontrada")
            
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            # Obter nome da outra parte
            if user_type == 'cliente':
                other_party = User.query.get(pre_order.provider_id)
                other_party_name = other_party.nome if other_party else "Prestador"
                other_party_role = "prestador"
            else:
                other_party = User.query.get(pre_order.client_id)
                other_party_name = other_party.nome if other_party else "Cliente"
                other_party_role = "cliente"
            
            message = (
                f"✅ Pré-ordem #{pre_order.id} criada! "
                f"Serviço: '{pre_order.title}'. "
                f"Valor: R$ {pre_order.current_value:.2f}. "
                f"Você pode negociar os termos com {other_party_name} antes de confirmar. "
                f"Prazo para negociação: {pre_order.days_until_expiration:.0f} dias."
            )
            
            flash(message, 'success')
            
            logger.info(
                f"Notificação de pré-ordem criada - Pré-ordem: {pre_order_id}, "
                f"Usuário: {user_id} ({user_type})"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_created',
                'pre_order_id': pre_order_id,
                'user_id': user_id,
                'user_type': user_type,
                'message': message,
                'other_party_name': other_party_name,
                'other_party_role': other_party_role,
                'value': float(pre_order.current_value),
                'days_until_expiration': pre_order.days_until_expiration,
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_ready_for_conversion(pre_order_id: int, client_id: int, provider_id: int) -> Dict:
        """
        Notifica ambas as partes quando a pré-ordem está pronta para conversão
        
        Requirements: 5.1, 11.4
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError("Pré-ordem não encontrada")
            
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            message = (
                f"🎉 Pré-ordem #{pre_order.id} pronta para conversão! "
                f"Ambas as partes aceitaram os termos finais. "
                f"Serviço: '{pre_order.title}'. "
                f"Valor: R$ {pre_order.current_value:.2f}. "
                f"A pré-ordem será convertida em ordem definitiva em breve."
            )
            
            flash(message, 'success')
            
            logger.info(
                f"Notificação de pré-ordem pronta para conversão - Pré-ordem: {pre_order_id}, "
                f"Cliente: {client_id}, Prestador: {provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_ready_for_conversion',
                'pre_order_id': pre_order_id,
                'client_id': client_id,
                'provider_id': provider_id,
                'message': message,
                'client_name': client_name,
                'provider_name': provider_name,
                'value': float(pre_order.current_value),
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar pré-ordem pronta para conversão {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_terms_accepted(pre_order_id: int, acceptor_id: int, acceptor_role: str, other_party_id: int) -> Dict:
        """
        Notifica a outra parte quando alguém aceita os termos
        
        Requirements: 7.5, 11.3
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError("Pré-ordem não encontrada")
            
            acceptor = User.query.get(acceptor_id)
            acceptor_name = acceptor.nome if acceptor else acceptor_role.title()
            
            message = (
                f"✅ {acceptor_name} aceitou os termos da pré-ordem #{pre_order.id}. "
                f"Serviço: '{pre_order.title}'. "
                f"Valor: R$ {pre_order.current_value:.2f}. "
                f"Agora é sua vez de aceitar os termos para prosseguir."
            )
            
            flash(message, 'info')
            
            logger.info(
                f"Notificação de termos aceitos - Pré-ordem: {pre_order_id}, "
                f"Aceitou: {acceptor_id} ({acceptor_role}), Notificado: {other_party_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'terms_accepted',
                'pre_order_id': pre_order_id,
                'acceptor_id': acceptor_id,
                'acceptor_role': acceptor_role,
                'acceptor_name': acceptor_name,
                'other_party_id': other_party_id,
                'message': message,
                'value': float(pre_order.current_value),
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar termos aceitos da pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_cancelled(pre_order_id: int, cancelled_by_id: int, cancelled_by_role: str, 
                                   other_party_id: int, reason: str) -> Dict:
        """
        Notifica a outra parte quando a pré-ordem é cancelada
        
        Requirements: 8.3, 11.5
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError("Pré-ordem não encontrada")
            
            cancelled_by = User.query.get(cancelled_by_id)
            cancelled_by_name = cancelled_by.nome if cancelled_by else cancelled_by_role.title()
            
            message = (
                f"❌ Pré-ordem #{pre_order.id} foi cancelada por {cancelled_by_name}. "
                f"Serviço: '{pre_order.title}'. "
                f"Motivo: {reason}. "
                f"Nenhuma ordem foi criada e nenhum valor foi bloqueado."
            )
            
            flash(message, 'warning')
            
            logger.info(
                f"Notificação de pré-ordem cancelada - Pré-ordem: {pre_order_id}, "
                f"Cancelado por: {cancelled_by_id} ({cancelled_by_role}), Notificado: {other_party_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_cancelled',
                'pre_order_id': pre_order_id,
                'cancelled_by_id': cancelled_by_id,
                'cancelled_by_role': cancelled_by_role,
                'cancelled_by_name': cancelled_by_name,
                'other_party_id': other_party_id,
                'message': message,
                'reason': reason,
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar cancelamento de pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    
    # ==================== NOTIFICAÇÕES DE PRÉ-ORDENS ====================
    
    @staticmethod
    def notify_pre_order_created(pre_order_id: int, user_id: int, user_type: str) -> Dict:
        """
        Notifica usuário quando uma pré-ordem é criada
        
        Requirements: 1.4, 11.1
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"Usuário {user_id} não encontrado")
            
            # Obter nome da outra parte
            if user_type == 'cliente':
                other_user = User.query.get(pre_order.provider_id)
                other_name = other_user.nome if other_user else "Prestador"
            else:
                other_user = User.query.get(pre_order.client_id)
                other_name = other_user.nome if other_user else "Cliente"
            
            message = (
                f"✅ Pré-ordem #{pre_order_id} criada! "
                f"Serviço: '{pre_order.title}'. "
                f"Valor: R$ {pre_order.current_value:.2f}. "
                f"Você pode negociar valor e condições com {other_name} antes de finalizar. "
                f"Prazo para negociação: {pre_order.expires_at.strftime('%d/%m/%Y')}."
            )
            
            flash(message, 'success')
            
            logger.info(
                f"Notificação de pré-ordem criada - PreOrder: {pre_order_id}, "
                f"Usuário: {user_id} ({user_type})"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_created',
                'pre_order_id': pre_order_id,
                'message': message,
                'user_id': user_id,
                'user_type': user_type
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar criação de pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_ready_for_conversion(pre_order_id: int, client_id: int, provider_id: int) -> Dict:
        """
        Notifica ambas as partes quando a pré-ordem está pronta para conversão
        
        Requirements: 5.1, 11.4
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            message = (
                f"🎉 Pré-ordem #{pre_order_id} pronta para conversão! "
                f"Ambas as partes aceitaram os termos finais. "
                f"Valor acordado: R$ {pre_order.current_value:.2f}. "
                f"A pré-ordem será convertida em ordem definitiva em breve."
            )
            
            flash(message, 'success')
            
            logger.info(
                f"Notificação de pré-ordem pronta para conversão - PreOrder: {pre_order_id}, "
                f"Cliente: {client_id}, Prestador: {provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_ready_for_conversion',
                'pre_order_id': pre_order_id,
                'message': message,
                'client_id': client_id,
                'provider_id': provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'final_value': float(pre_order.current_value)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar pré-ordem pronta para conversão {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_terms_accepted(pre_order_id: int, acceptor_id: int, acceptor_role: str, other_party_id: int) -> Dict:
        """
        Notifica a outra parte quando alguém aceita os termos
        
        Requirements: 7.5, 11.3
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            acceptor = User.query.get(acceptor_id)
            acceptor_name = acceptor.nome if acceptor else acceptor_role.title()
            
            message = (
                f"✅ {acceptor_name} aceitou os termos da pré-ordem #{pre_order_id}. "
                f"Aguardando sua aceitação para finalizar a negociação."
            )
            
            flash(message, 'info')
            
            logger.info(
                f"Notificação de aceitação de termos - PreOrder: {pre_order_id}, "
                f"Aceitou: {acceptor_id} ({acceptor_role}), Notificado: {other_party_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'terms_accepted',
                'pre_order_id': pre_order_id,
                'message': message,
                'acceptor_id': acceptor_id,
                'acceptor_role': acceptor_role,
                'other_party_id': other_party_id
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar aceitação de termos {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_cancelled(pre_order_id: int, cancelled_by_id: int, cancelled_by_role: str, 
                                   other_party_id: int, reason: str) -> Dict:
        """
        Notifica a outra parte quando a pré-ordem é cancelada
        
        Requirements: 8.3, 11.5
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            canceller = User.query.get(cancelled_by_id)
            canceller_name = canceller.nome if canceller else cancelled_by_role.title()
            
            message = (
                f"❌ Pré-ordem #{pre_order_id} cancelada por {canceller_name}. "
                f"Motivo: {reason}. "
                f"Nenhuma ordem foi criada."
            )
            
            flash(message, 'warning')
            
            logger.info(
                f"Notificação de cancelamento de pré-ordem - PreOrder: {pre_order_id}, "
                f"Cancelado por: {cancelled_by_id} ({cancelled_by_role}), "
                f"Notificado: {other_party_id}, Motivo: {reason}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_cancelled',
                'pre_order_id': pre_order_id,
                'message': message,
                'cancelled_by_id': cancelled_by_id,
                'cancelled_by_role': cancelled_by_role,
                'other_party_id': other_party_id,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar cancelamento de pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_converted(pre_order_id: int, order_id: int, client_id: int, 
                                   provider_id: int, value: float) -> Dict:
        """
        Notifica ambas as partes quando a pré-ordem é convertida em ordem
        
        Requirements: 5.5, 11.4, 14.4
        """
        try:
            from models import PreOrder, Order, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            order = Order.query.get(order_id)
            
            if not pre_order or not order:
                raise ValueError("Pré-ordem ou ordem não encontrada")
            
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            message = (
                f"🎉 Pré-ordem #{pre_order_id} convertida em ordem #{order_id}! "
                f"Valor final: R$ {value:.2f}. "
                f"Os valores foram bloqueados em escrow. "
                f"O serviço pode ser iniciado."
            )
            
            flash(message, 'success')
            
            logger.info(
                f"Notificação de conversão de pré-ordem - PreOrder: {pre_order_id}, "
                f"Order: {order_id}, Cliente: {client_id}, Prestador: {provider_id}, "
                f"Valor: R$ {value:.2f}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_converted',
                'pre_order_id': pre_order_id,
                'order_id': order_id,
                'message': message,
                'client_id': client_id,
                'provider_id': provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'value': value
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar conversão de pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_conversion_error(pre_order_id: int, client_id: int, provider_id: int, error_message: str) -> Dict:
        """
        Notifica ambas as partes quando há erro na conversão
        
        Requirements: 14.4
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            message = (
                f"⚠️ Erro ao converter pré-ordem #{pre_order_id} em ordem. "
                f"{error_message} "
                f"A pré-ordem permanece ativa. Tente novamente."
            )
            
            flash(message, 'danger')
            
            logger.error(
                f"Notificação de erro de conversão - PreOrder: {pre_order_id}, "
                f"Cliente: {client_id}, Prestador: {provider_id}, "
                f"Erro: {error_message}"
            )
            
            return {
                'success': True,
                'notification_type': 'conversion_error',
                'pre_order_id': pre_order_id,
                'message': message,
                'client_id': client_id,
                'provider_id': provider_id,
                'error_message': error_message
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar erro de conversão {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def notify_pre_order_expiring_soon(pre_order_id: int, client_id: int, provider_id: int, hours_remaining: int) -> Dict:
        """
        Notifica ambas as partes quando a pré-ordem está próxima da expiração (24h)
        
        Requirements: 15.2
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            # Mensagem de aviso
            message = (
                f"⚠️ ATENÇÃO: Pré-ordem #{pre_order_id} expirará em {hours_remaining} horas! "
                f"Serviço: '{pre_order.title}'. "
                f"Valor atual: R$ {pre_order.current_value:.2f}. "
                f"Prazo final: {pre_order.expires_at.strftime('%d/%m/%Y às %H:%M')}. "
                f"Finalize a negociação e aceite os termos antes que expire, "
                f"caso contrário a pré-ordem será cancelada automaticamente."
            )
            
            flash(message, 'warning')
            
            logger.info(
                f"Notificação de expiração próxima - Pré-ordem: {pre_order_id}, "
                f"Cliente: {client_id}, Prestador: {provider_id}, "
                f"Horas restantes: {hours_remaining}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_expiring_soon',
                'pre_order_id': pre_order_id,
                'message': message,
                'client_id': client_id,
                'provider_id': provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'hours_remaining': hours_remaining,
                'expires_at': pre_order.expires_at.isoformat(),
                'current_value': float(pre_order.current_value),
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id),
                'urgent': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar expiração próxima da pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def notify_pre_order_expired(pre_order_id: int, client_id: int, provider_id: int) -> Dict:
        """
        Notifica ambas as partes quando a pré-ordem expira
        
        Requirements: 15.4
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            # Mensagem de expiração
            message = (
                f"⏰ Pré-ordem #{pre_order_id} expirou. "
                f"Serviço: '{pre_order.title}'. "
                f"O prazo de negociação terminou em {pre_order.expires_at.strftime('%d/%m/%Y às %H:%M')}. "
                f"A pré-ordem foi cancelada automaticamente. "
                f"Nenhum valor foi bloqueado. "
                f"Você pode criar um novo convite se ainda tiver interesse no serviço."
            )
            
            flash(message, 'info')
            
            logger.info(
                f"Notificação de expiração - Pré-ordem: {pre_order_id}, "
                f"Cliente: {client_id}, Prestador: {provider_id}"
            )
            
            return {
                'success': True,
                'notification_type': 'pre_order_expired',
                'pre_order_id': pre_order_id,
                'message': message,
                'client_id': client_id,
                'provider_id': provider_id,
                'client_name': client_name,
                'provider_name': provider_name,
                'expired_at': pre_order.expires_at.isoformat(),
                'action_url': url_for('pre_ordem.ver_detalhes', pre_order_id=pre_order_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao notificar expiração da pré-ordem {pre_order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==================== MÉTODOS AUXILIARES PARA RENDERIZAÇÃO DE TEMPLATES ====================
    
    @staticmethod
    def render_notification_template(template_name: str, **context) -> str:
        """
        Renderiza um template de notificação com o contexto fornecido
        
        Args:
            template_name: Nome do template (ex: 'pre_ordem_criada.html')
            **context: Variáveis de contexto para o template
        
        Returns:
            HTML renderizado como string
        """
        try:
            from flask import render_template
            
            template_path = f'notifications/{template_name}'
            return render_template(template_path, **context)
            
        except Exception as e:
            logger.error(f"Erro ao renderizar template {template_name}: {str(e)}")
            return f"<p>Erro ao carregar notificação: {str(e)}</p>"
    
    @staticmethod
    def get_notification_context_for_pre_order_created(pre_order_id: int, user_type: str) -> Dict:
        """
        Prepara o contexto para o template de pré-ordem criada
        
        Requirements: 1.4, 11.1
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Determinar a outra parte
            if user_type == 'cliente':
                other_party = User.query.get(pre_order.provider_id)
                other_party_name = other_party.nome if other_party else "Prestador"
            else:
                other_party = User.query.get(pre_order.client_id)
                other_party_name = other_party.nome if other_party else "Cliente"
            
            return {
                'pre_order': pre_order,
                'user_type': user_type,
                'other_party_name': other_party_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para pré-ordem criada: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_proposal_received(proposal_id: int) -> Dict:
        """
        Prepara o contexto para o template de proposta recebida
        
        Requirements: 2.2, 11.2
        """
        try:
            from models import PreOrderProposal, PreOrder, User
            
            proposal = PreOrderProposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            pre_order = proposal.pre_order
            proposer = User.query.get(proposal.proposed_by)
            proposer_name = proposer.nome if proposer else "Usuário"
            
            return {
                'proposal': proposal,
                'pre_order': pre_order,
                'proposer_name': proposer_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para proposta recebida: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_proposal_accepted(proposal_id: int) -> Dict:
        """
        Prepara o contexto para o template de proposta aceita
        
        Requirements: 3.4, 11.3
        """
        try:
            from models import PreOrderProposal, PreOrder, User
            
            proposal = PreOrderProposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            pre_order = proposal.pre_order
            
            # Determinar quem aceitou (a outra parte que não propôs)
            if proposal.proposed_by == pre_order.client_id:
                acceptor = User.query.get(pre_order.provider_id)
            else:
                acceptor = User.query.get(pre_order.client_id)
            
            acceptor_name = acceptor.nome if acceptor else "Usuário"
            
            return {
                'proposal': proposal,
                'pre_order': pre_order,
                'acceptor_name': acceptor_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para proposta aceita: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_proposal_rejected(proposal_id: int, rejection_reason: str = None) -> Dict:
        """
        Prepara o contexto para o template de proposta rejeitada
        
        Requirements: 4.4, 11.3
        """
        try:
            from models import PreOrderProposal, PreOrder, User
            
            proposal = PreOrderProposal.query.get(proposal_id)
            if not proposal:
                raise ValueError(f"Proposta {proposal_id} não encontrada")
            
            pre_order = proposal.pre_order
            
            # Determinar quem rejeitou (a outra parte que não propôs)
            if proposal.proposed_by == pre_order.client_id:
                rejector = User.query.get(pre_order.provider_id)
            else:
                rejector = User.query.get(pre_order.client_id)
            
            rejector_name = rejector.nome if rejector else "Usuário"
            
            return {
                'proposal': proposal,
                'pre_order': pre_order,
                'rejector_name': rejector_name,
                'rejection_reason': rejection_reason
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para proposta rejeitada: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_pre_order_converted(pre_order_id: int, order_id: int, user_type: str) -> Dict:
        """
        Prepara o contexto para o template de pré-ordem convertida
        
        Requirements: 5.5, 11.4
        """
        try:
            from models import PreOrder, Order, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            order = Order.query.get(order_id)
            
            if not pre_order or not order:
                raise ValueError("Pré-ordem ou ordem não encontrada")
            
            client = User.query.get(pre_order.client_id)
            provider = User.query.get(pre_order.provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            return {
                'pre_order': pre_order,
                'order': order,
                'user_type': user_type,
                'client_name': client_name,
                'provider_name': provider_name
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para pré-ordem convertida: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_pre_order_cancelled(pre_order_id: int, user_type: str) -> Dict:
        """
        Prepara o contexto para o template de pré-ordem cancelada
        
        Requirements: 8.3, 11.5
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            cancelled_by = User.query.get(pre_order.cancelled_by)
            cancelled_by_name = cancelled_by.nome if cancelled_by else "Usuário"
            
            return {
                'pre_order': pre_order,
                'user_type': user_type,
                'cancelled_by_name': cancelled_by_name,
                'cancellation_reason': pre_order.cancellation_reason
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para pré-ordem cancelada: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_pre_order_expiring(pre_order_id: int, user_type: str, hours_remaining: int) -> Dict:
        """
        Prepara o contexto para o template de pré-ordem expirando
        
        Requirements: 15.2
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Determinar a outra parte
            if user_type == 'cliente':
                other_party = User.query.get(pre_order.provider_id)
                other_party_name = other_party.nome if other_party else "Prestador"
            else:
                other_party = User.query.get(pre_order.client_id)
                other_party_name = other_party.nome if other_party else "Cliente"
            
            return {
                'pre_order': pre_order,
                'user_type': user_type,
                'other_party_name': other_party_name,
                'hours_remaining': hours_remaining
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para pré-ordem expirando: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_pre_order_expired(pre_order_id: int, user_type: str) -> Dict:
        """
        Prepara o contexto para o template de pré-ordem expirada
        
        Requirements: 15.4
        """
        try:
            from models import PreOrder, User
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Determinar a outra parte
            if user_type == 'cliente':
                other_party = User.query.get(pre_order.provider_id)
                other_party_name = other_party.nome if other_party else "Prestador"
            else:
                other_party = User.query.get(pre_order.client_id)
                other_party_name = other_party.nome if other_party else "Cliente"
            
            # Contar rodadas de negociação
            negotiation_rounds = pre_order.negotiation_round if hasattr(pre_order, 'negotiation_round') else 0
            
            return {
                'pre_order': pre_order,
                'user_type': user_type,
                'other_party_name': other_party_name,
                'negotiation_rounds': negotiation_rounds
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para pré-ordem expirada: {str(e)}")
            return {}
    
    @staticmethod
    def get_notification_context_for_conversion_error(pre_order_id: int, user_type: str, 
                                                      error_type: str, error_message: str,
                                                      current_balance: float = None,
                                                      dispute_fee: float = None) -> Dict:
        """
        Prepara o contexto para o template de erro de conversão
        
        Requirements: 14.4
        """
        try:
            from models import PreOrder, User
            from datetime import datetime
            
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
            
            # Determinar a outra parte
            if user_type == 'cliente':
                other_party = User.query.get(pre_order.provider_id)
                other_party_name = other_party.nome if other_party else "Prestador"
            else:
                other_party = User.query.get(pre_order.client_id)
                other_party_name = other_party.nome if other_party else "Cliente"
            
            return {
                'pre_order': pre_order,
                'user_type': user_type,
                'other_party_name': other_party_name,
                'error_type': error_type,
                'error_message': error_message,
                'current_balance': current_balance,
                'dispute_fee': dispute_fee,
                'now': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Erro ao preparar contexto para erro de conversão: {str(e)}")
            return {}
