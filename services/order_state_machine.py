#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Máquina de Estados para Order
Gerencia transições válidas de estado e logs de mudanças
"""

from datetime import datetime
from models import db
import logging

logger = logging.getLogger(__name__)


class OrderStateMachine:
    """
    Máquina de estados para gerenciar transições de Order.status
    
    Estados válidos:
    - disponivel: Ordem criada e aguardando prestador
    - aceita: Prestador aceitou a ordem
    - em_andamento: Trabalho iniciado
    - concluida: Trabalho finalizado
    - cancelada: Ordem cancelada
    - disputada: Ordem em disputa
    """
    
    # Definição de transições válidas
    VALID_TRANSITIONS = {
        'disponivel': ['aceita', 'cancelada'],
        'aceita': ['em_andamento', 'cancelada', 'disputada'],
        'em_andamento': ['concluida', 'cancelada', 'disputada'],
        'concluida': ['disputada'],  # Pode ser disputada após conclusão
        'cancelada': [],  # Estado final
        'disputada': ['concluida', 'cancelada']  # Admin pode resolver para qualquer estado final
    }
    
    # Estados finais (não podem transicionar para outros estados, exceto disputada)
    FINAL_STATES = ['cancelada']
    
    # Estados que requerem prestador
    REQUIRES_PROVIDER = ['aceita', 'em_andamento', 'concluida']
    
    @classmethod
    def can_transition(cls, current_status, new_status):
        """
        Verifica se a transição de estado é válida
        
        Args:
            current_status: Estado atual da ordem
            new_status: Novo estado desejado
            
        Returns:
            bool: True se a transição é válida, False caso contrário
        """
        if current_status not in cls.VALID_TRANSITIONS:
            logger.error(f"Estado atual inválido: {current_status}")
            return False
        
        if new_status not in cls.VALID_TRANSITIONS:
            logger.error(f"Novo estado inválido: {new_status}")
            return False
        
        return new_status in cls.VALID_TRANSITIONS[current_status]
    
    @classmethod
    def transition(cls, order, new_status, user_id=None, reason=None):
        """
        Executa transição de estado com validação e logging
        
        Args:
            order: Objeto Order
            new_status: Novo estado desejado
            user_id: ID do usuário que está fazendo a transição
            reason: Motivo da transição (opcional)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        current_status = order.status
        
        # Validar transição
        if not cls.can_transition(current_status, new_status):
            message = f"Transição inválida: {current_status} → {new_status}"
            logger.warning(f"Order #{order.id}: {message}")
            return False, message
        
        # Validar se requer prestador
        if new_status in cls.REQUIRES_PROVIDER and not order.provider_id:
            message = f"Estado '{new_status}' requer prestador atribuído"
            logger.warning(f"Order #{order.id}: {message}")
            return False, message
        
        # Executar transição
        try:
            old_status = order.status
            order.status = new_status
            
            # Atualizar timestamps específicos
            if new_status == 'aceita':
                order.accepted_at = datetime.utcnow()
            elif new_status == 'concluida':
                order.completed_at = datetime.utcnow()
            elif new_status == 'disputada':
                if not order.dispute_opened_at:
                    order.dispute_opened_at = datetime.utcnow()
                if user_id:
                    order.dispute_opened_by = user_id
            
            db.session.commit()
            
            # Log da transição
            log_message = f"Order #{order.id}: {old_status} → {new_status}"
            if user_id:
                log_message += f" (user_id={user_id})"
            if reason:
                log_message += f" | Motivo: {reason}"
            
            logger.info(log_message)
            
            return True, f"Status atualizado para '{new_status}'"
            
        except Exception as e:
            db.session.rollback()
            error_message = f"Erro ao atualizar status: {str(e)}"
            logger.error(f"Order #{order.id}: {error_message}")
            return False, error_message
    
    @classmethod
    def get_available_transitions(cls, current_status):
        """
        Retorna lista de transições disponíveis para o estado atual
        
        Args:
            current_status: Estado atual da ordem
            
        Returns:
            list: Lista de estados possíveis
        """
        return cls.VALID_TRANSITIONS.get(current_status, [])
    
    @classmethod
    def is_final_state(cls, status):
        """
        Verifica se o estado é final
        
        Args:
            status: Estado a verificar
            
        Returns:
            bool: True se é estado final
        """
        return status in cls.FINAL_STATES
    
    @classmethod
    def validate_status(cls, status):
        """
        Valida se o status é válido
        
        Args:
            status: Status a validar
            
        Returns:
            bool: True se o status é válido
        """
        return status in cls.VALID_TRANSITIONS
    
    @classmethod
    def get_status_description(cls, status):
        """
        Retorna descrição amigável do status
        
        Args:
            status: Status da ordem
            
        Returns:
            str: Descrição do status
        """
        descriptions = {
            'disponivel': 'Aguardando prestador',
            'aceita': 'Aceita por prestador',
            'em_andamento': 'Em andamento',
            'concluida': 'Concluída',
            'cancelada': 'Cancelada',
            'disputada': 'Em disputa'
        }
        return descriptions.get(status, 'Status desconhecido')
    
    @classmethod
    def get_transition_diagram(cls):
        """
        Retorna diagrama de transições em formato texto
        
        Returns:
            str: Diagrama de transições
        """
        diagram = "Diagrama de Transições de Estado:\n\n"
        for current, transitions in cls.VALID_TRANSITIONS.items():
            if transitions:
                diagram += f"{current}:\n"
                for next_state in transitions:
                    diagram += f"  → {next_state}\n"
            else:
                diagram += f"{current}: (estado final)\n"
        return diagram


# ==============================================================================
#  FUNÇÕES DE CONVENIÊNCIA
# ==============================================================================

def change_order_status(order, new_status, user_id=None, reason=None):
    """
    Função de conveniência para mudar status de ordem
    
    Args:
        order: Objeto Order
        new_status: Novo status desejado
        user_id: ID do usuário fazendo a mudança
        reason: Motivo da mudança
        
    Returns:
        tuple: (success: bool, message: str)
    """
    return OrderStateMachine.transition(order, new_status, user_id, reason)


def get_order_next_states(order):
    """
    Retorna próximos estados possíveis para uma ordem
    
    Args:
        order: Objeto Order
        
    Returns:
        list: Lista de estados possíveis
    """
    return OrderStateMachine.get_available_transitions(order.status)


def validate_order_status(status):
    """
    Valida se um status é válido
    
    Args:
        status: Status a validar
        
    Returns:
        bool: True se válido
    """
    return OrderStateMachine.validate_status(status)

