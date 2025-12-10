#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from datetime import datetime
from models import db, Order, AdminUser
import logging

# Configurar logging para auditoria
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderStatusValidator:
    """
    Validador de transições de status de pedidos com auditoria completa
    
    Implementa matriz de transições válidas conforme requisitos 7.1, 7.2, 7.3
    """
    
    # Matriz de transições válidas entre status de orders
    VALID_TRANSITIONS = {
        'disponivel': ['aceita', 'cancelada'],
        'aceita': ['em_andamento', 'cancelada', 'disputada'],
        'em_andamento': ['aguardando_confirmacao', 'cancelada', 'disputada'],
        'aguardando_confirmacao': ['concluida', 'cancelada', 'disputada'],
        'concluida': ['disputada'],  # Pode ser disputada mesmo após conclusão
        'disputada': ['concluida', 'cancelada', 'resolvida'],  # Resolução admin
        'cancelada': [],  # Estado final
        'resolvida': []   # Estado final após resolução de disputa
    }
    
    # Descrições das transições para logs de auditoria
    TRANSITION_DESCRIPTIONS = {
        ('disponivel', 'aceita'): 'Prestador aceitou a ordem',
        ('disponivel', 'cancelada'): 'Cliente cancelou ordem disponível',
        ('aceita', 'em_andamento'): 'Prestador iniciou execução da ordem',
        ('aceita', 'cancelada'): 'Ordem cancelada após aceitação',
        ('aceita', 'disputada'): 'Disputa aberta na ordem aceita',
        ('em_andamento', 'aguardando_confirmacao'): 'Prestador marcou ordem como concluída',
        ('em_andamento', 'cancelada'): 'Ordem cancelada durante execução',
        ('em_andamento', 'disputada'): 'Disputa aberta durante execução',
        ('aguardando_confirmacao', 'concluida'): 'Cliente confirmou conclusão da ordem',
        ('aguardando_confirmacao', 'cancelada'): 'Ordem cancelada antes da confirmação',
        ('aguardando_confirmacao', 'disputada'): 'Disputa aberta antes da confirmação',
        ('concluida', 'disputada'): 'Disputa aberta após conclusão',
        ('disputada', 'concluida'): 'Disputa resolvida em favor da conclusão',
        ('disputada', 'cancelada'): 'Disputa resolvida com cancelamento',
        ('disputada', 'resolvida'): 'Disputa resolvida administrativamente'
    }
    
    @staticmethod
    def validate_transition(order_id, current_status, new_status, user_id=None, admin_id=None, reason=None):
        """
        Valida se uma transição de status é permitida
        
        Args:
            order_id (int): ID da ordem
            current_status (str): Status atual da ordem
            new_status (str): Novo status desejado
            user_id (int, optional): ID do usuário fazendo a mudança
            admin_id (int, optional): ID do admin fazendo a mudança
            reason (str, optional): Motivo da mudança de status
            
        Returns:
            dict: Resultado da validação com sucesso/erro e detalhes
        """
        try:
            # Verificar se a transição é válida na matriz
            if current_status not in OrderStatusValidator.VALID_TRANSITIONS:
                error_msg = f"Status atual inválido: {current_status}"
                OrderStatusValidator._log_transition_attempt(
                    order_id, current_status, new_status, user_id, admin_id, 
                    success=False, error=error_msg, reason=reason
                )
                return {
                    'valid': False,
                    'error': error_msg,
                    'error_code': 'INVALID_CURRENT_STATUS'
                }
            
            valid_next_statuses = OrderStatusValidator.VALID_TRANSITIONS[current_status]
            
            if new_status not in valid_next_statuses:
                error_msg = f"Transição inválida de '{current_status}' para '{new_status}'. Transições válidas: {', '.join(valid_next_statuses)}"
                OrderStatusValidator._log_transition_attempt(
                    order_id, current_status, new_status, user_id, admin_id,
                    success=False, error=error_msg, reason=reason
                )
                return {
                    'valid': False,
                    'error': error_msg,
                    'error_code': 'INVALID_TRANSITION',
                    'valid_transitions': valid_next_statuses
                }
            
            # Validações específicas por tipo de transição
            validation_result = OrderStatusValidator._validate_specific_transition(
                order_id, current_status, new_status, user_id, admin_id, reason
            )
            
            if not validation_result['valid']:
                OrderStatusValidator._log_transition_attempt(
                    order_id, current_status, new_status, user_id, admin_id,
                    success=False, error=validation_result['error'], reason=reason
                )
                return validation_result
            
            # Log de sucesso
            OrderStatusValidator._log_transition_attempt(
                order_id, current_status, new_status, user_id, admin_id,
                success=True, reason=reason
            )
            
            return {
                'valid': True,
                'message': f"Transição válida de '{current_status}' para '{new_status}'",
                'description': OrderStatusValidator.TRANSITION_DESCRIPTIONS.get(
                    (current_status, new_status), 
                    f"Mudança de status de {current_status} para {new_status}"
                )
            }
            
        except Exception as e:
            error_msg = f"Erro interno na validação de transição: {str(e)}"
            OrderStatusValidator._log_transition_attempt(
                order_id, current_status, new_status, user_id, admin_id,
                success=False, error=error_msg, reason=reason
            )
            return {
                'valid': False,
                'error': error_msg,
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def _validate_specific_transition(order_id, current_status, new_status, user_id, admin_id, reason):
        """
        Validações específicas para certas transições
        
        Args:
            order_id (int): ID da ordem
            current_status (str): Status atual
            new_status (str): Novo status
            user_id (int): ID do usuário
            admin_id (int): ID do admin
            reason (str): Motivo da mudança
            
        Returns:
            dict: Resultado da validação específica
        """
        try:
            # Buscar a ordem para validações específicas
            order = Order.query.get(order_id)
            if not order:
                return {
                    'valid': False,
                    'error': f"Ordem {order_id} não encontrada",
                    'error_code': 'ORDER_NOT_FOUND'
                }
            
            # Validações para transições que requerem admin
            admin_required_transitions = [
                ('disputada', 'concluida'),
                ('disputada', 'cancelada'),
                ('disputada', 'resolvida')
            ]
            
            if (current_status, new_status) in admin_required_transitions:
                if not admin_id:
                    return {
                        'valid': False,
                        'error': f"Transição de '{current_status}' para '{new_status}' requer autorização administrativa",
                        'error_code': 'ADMIN_REQUIRED'
                    }
                
                # Verificar se admin existe
                admin = AdminUser.query.get(admin_id)
                if not admin:
                    return {
                        'valid': False,
                        'error': f"Administrador {admin_id} não encontrado",
                        'error_code': 'ADMIN_NOT_FOUND'
                    }
            
            # Validações para disputas - requer motivo
            if new_status == 'disputada':
                if not reason or len(reason.strip()) < 10:
                    return {
                        'valid': False,
                        'error': "Abertura de disputa requer motivo com pelo menos 10 caracteres",
                        'error_code': 'DISPUTE_REASON_REQUIRED'
                    }
                
                # Verificar se usuário tem autorização para abrir disputa
                if user_id and user_id not in [order.client_id, order.provider_id]:
                    return {
                        'valid': False,
                        'error': "Apenas cliente ou prestador podem abrir disputa",
                        'error_code': 'UNAUTHORIZED_DISPUTE'
                    }
            
            # Validações para cancelamento
            if new_status == 'cancelada':
                # Verificar prazos para cancelamento
                if current_status in ['aceita', 'em_andamento'] and order.accepted_at:
                    hours_since_accepted = (datetime.utcnow() - order.accepted_at).total_seconds() / 3600
                    
                    # Cliente não pode cancelar após 24h da aceitação
                    if hours_since_accepted > 24 and user_id == order.client_id:
                        return {
                            'valid': False,
                            'error': "Cliente não pode cancelar ordem aceita há mais de 24 horas",
                            'error_code': 'CANCELLATION_TIMEOUT'
                        }
            
            # Validações para conclusão
            if new_status == 'concluida':
                # Verificar se é o cliente confirmando
                if current_status == 'aguardando_confirmacao' and user_id != order.client_id:
                    return {
                        'valid': False,
                        'error': "Apenas o cliente pode confirmar a conclusão da ordem",
                        'error_code': 'CLIENT_CONFIRMATION_REQUIRED'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Erro na validação específica: {str(e)}",
                'error_code': 'VALIDATION_ERROR'
            }
    
    @staticmethod
    def _log_transition_attempt(order_id, current_status, new_status, user_id, admin_id, 
                               success, error=None, reason=None):
        """
        Registra tentativa de mudança de status para auditoria
        
        Args:
            order_id (int): ID da ordem
            current_status (str): Status atual
            new_status (str): Novo status tentado
            user_id (int): ID do usuário
            admin_id (int): ID do admin
            success (bool): Se a transição foi bem-sucedida
            error (str): Mensagem de erro se falhou
            reason (str): Motivo da mudança
        """
        try:
            # Determinar quem fez a tentativa
            actor_type = "admin" if admin_id else "user"
            actor_id = admin_id if admin_id else user_id
            
            # Criar log estruturado
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'order_id': order_id,
                'current_status': current_status,
                'new_status': new_status,
                'actor_type': actor_type,
                'actor_id': actor_id,
                'success': success,
                'reason': reason,
                'error': error
            }
            
            # Log para arquivo/sistema
            if success:
                logger.info(f"STATUS_TRANSITION_SUCCESS: {log_data}")
            else:
                logger.warning(f"STATUS_TRANSITION_FAILED: {log_data}")
            
            # TODO: Implementar persistência em tabela de auditoria quando necessário
            # AuditLog.create_status_transition_log(log_data)
            
        except Exception as e:
            # Não falhar a operação principal por erro de log
            logger.error(f"Erro ao registrar log de transição: {str(e)}")
    
    @staticmethod
    def get_valid_transitions(current_status):
        """
        Retorna as transições válidas para um status atual
        
        Args:
            current_status (str): Status atual da ordem
            
        Returns:
            list: Lista de status válidos para transição
        """
        return OrderStatusValidator.VALID_TRANSITIONS.get(current_status, [])
    
    @staticmethod
    def get_transition_description(current_status, new_status):
        """
        Retorna a descrição de uma transição específica
        
        Args:
            current_status (str): Status atual
            new_status (str): Novo status
            
        Returns:
            str: Descrição da transição
        """
        return OrderStatusValidator.TRANSITION_DESCRIPTIONS.get(
            (current_status, new_status),
            f"Mudança de status de {current_status} para {new_status}"
        )
    
    @staticmethod
    def is_final_status(status):
        """
        Verifica se um status é final (não permite mais transições)
        
        Args:
            status (str): Status a verificar
            
        Returns:
            bool: True se é status final
        """
        return len(OrderStatusValidator.VALID_TRANSITIONS.get(status, [])) == 0
    
    @staticmethod
    def requires_admin_authorization(current_status, new_status):
        """
        Verifica se uma transição requer autorização administrativa
        
        Args:
            current_status (str): Status atual
            new_status (str): Novo status
            
        Returns:
            bool: True se requer autorização admin
        """
        admin_required_transitions = [
            ('disputada', 'concluida'),
            ('disputada', 'cancelada'),
            ('disputada', 'resolvida')
        ]
        
        return (current_status, new_status) in admin_required_transitions