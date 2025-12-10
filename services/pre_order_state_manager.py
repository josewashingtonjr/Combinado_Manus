#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
PreOrderStateManager - Gerenciador de estados de pré-ordens

Este serviço gerencia as transições de estado das pré-ordens, garantindo que apenas
transições válidas sejam executadas e registrando todas as mudanças no histórico.

Requirements: 2.5, 4.5, 5.1, 8.4, 14.1, 15.3
"""

from models import db, PreOrder, PreOrderStatus, PreOrderHistory
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, List, Tuple
import logging

# Configurar logging
logger = logging.getLogger(__name__)


class StateTransition:
    """Define uma transição válida entre estados de pré-ordem"""
    
    def __init__(self, from_state: PreOrderStatus, to_state: PreOrderStatus, 
                 condition: callable = None, description: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.description = description


class PreOrderStateManager:
    """
    Gerenciador de estados das pré-ordens com validação e auditoria
    
    Responsável por:
    - Validar transições de estado
    - Executar mudanças de estado com atomicidade
    - Registrar histórico de todas as transições
    - Gerenciar flags de aceitação mútua
    """
    
    # Definir transições válidas entre estados
    # Requirements: 2.5, 4.5, 5.1, 8.4, 14.1, 15.3
    VALID_TRANSITIONS = [
        # Do estado EM_NEGOCIACAO
        StateTransition(
            PreOrderStatus.EM_NEGOCIACAO,
            PreOrderStatus.AGUARDANDO_RESPOSTA,
            description="Proposta enviada, aguardando resposta da outra parte"
        ),
        StateTransition(
            PreOrderStatus.EM_NEGOCIACAO,
            PreOrderStatus.PRONTO_CONVERSAO,
            lambda pre_order: pre_order.client_accepted_terms and pre_order.provider_accepted_terms and not pre_order.has_active_proposal,
            description="Ambas as partes aceitaram os termos finais sem proposta pendente"
        ),
        StateTransition(
            PreOrderStatus.EM_NEGOCIACAO,
            PreOrderStatus.CANCELADA,
            description="Pré-ordem cancelada por uma das partes"
        ),
        StateTransition(
            PreOrderStatus.EM_NEGOCIACAO,
            PreOrderStatus.EXPIRADA,
            lambda pre_order: pre_order.is_expired,
            description="Pré-ordem expirou automaticamente"
        ),
        
        # Do estado AGUARDANDO_RESPOSTA
        StateTransition(
            PreOrderStatus.AGUARDANDO_RESPOSTA,
            PreOrderStatus.EM_NEGOCIACAO,
            description="Proposta rejeitada ou aceita, retorna à negociação"
        ),
        StateTransition(
            PreOrderStatus.AGUARDANDO_RESPOSTA,
            PreOrderStatus.PRONTO_CONVERSAO,
            lambda pre_order: pre_order.client_accepted_terms and pre_order.provider_accepted_terms and not pre_order.has_active_proposal,
            description="Proposta aceita e ambas as partes aceitaram os termos"
        ),
        StateTransition(
            PreOrderStatus.AGUARDANDO_RESPOSTA,
            PreOrderStatus.CANCELADA,
            description="Pré-ordem cancelada durante aguardo de resposta"
        ),
        StateTransition(
            PreOrderStatus.AGUARDANDO_RESPOSTA,
            PreOrderStatus.EXPIRADA,
            lambda pre_order: pre_order.is_expired,
            description="Pré-ordem expirou com proposta pendente"
        ),
        
        # Do estado PRONTO_CONVERSAO
        StateTransition(
            PreOrderStatus.PRONTO_CONVERSAO,
            PreOrderStatus.CONVERTIDA,
            description="Pré-ordem convertida em ordem definitiva com sucesso"
        ),
        StateTransition(
            PreOrderStatus.PRONTO_CONVERSAO,
            PreOrderStatus.EM_NEGOCIACAO,
            description="Falha na conversão, retorna à negociação"
        ),
        StateTransition(
            PreOrderStatus.PRONTO_CONVERSAO,
            PreOrderStatus.CANCELADA,
            description="Pré-ordem cancelada antes da conversão"
        ),
        StateTransition(
            PreOrderStatus.PRONTO_CONVERSAO,
            PreOrderStatus.EXPIRADA,
            lambda pre_order: pre_order.is_expired,
            description="Pré-ordem expirou antes da conversão"
        ),
        
        # Estados finais não permitem transições (exceto para tratamento de erros)
    ]
    
    @staticmethod
    def get_current_state(pre_order: PreOrder) -> PreOrderStatus:
        """
        Retorna o estado atual da pré-ordem
        
        Args:
            pre_order: Pré-ordem a ser verificada
            
        Returns:
            PreOrderStatus: Estado atual
        """
        # Verificar se expirou
        if pre_order.is_expired and pre_order.status not in [
            PreOrderStatus.CONVERTIDA.value,
            PreOrderStatus.CANCELADA.value,
            PreOrderStatus.EXPIRADA.value
        ]:
            return PreOrderStatus.EXPIRADA
        
        # Retornar estado atual
        try:
            return PreOrderStatus(pre_order.status)
        except ValueError:
            logger.error(f"Estado inválido na pré-ordem {pre_order.id}: {pre_order.status}")
            return PreOrderStatus.EM_NEGOCIACAO
    
    @staticmethod
    def can_transition_to(pre_order: PreOrder, target_state: PreOrderStatus) -> Tuple[bool, str]:
        """
        Verifica se a pré-ordem pode transicionar para o estado alvo
        
        Args:
            pre_order: Pré-ordem a ser verificada
            target_state: Estado alvo desejado
            
        Returns:
            tuple: (pode_transicionar, motivo_se_nao_pode)
            
        Requirements: 2.5, 4.5, 5.1, 8.4
        """
        current_state = PreOrderStateManager.get_current_state(pre_order)
        
        # Se já está no estado alvo, permitir (idempotência)
        if current_state == target_state:
            return True, f"Já está no estado {target_state.value}"
        
        # Procurar transição válida
        for transition in PreOrderStateManager.VALID_TRANSITIONS:
            if (transition.from_state == current_state and 
                transition.to_state == target_state):
                
                # Verificar condição se existir
                if transition.condition and not transition.condition(pre_order):
                    return False, f"Condição não atendida: {transition.description}"
                
                return True, transition.description
        
        return False, f"Transição inválida de {current_state.value} para {target_state.value}"
    
    @staticmethod
    def transition_to(pre_order_id: int, new_status: PreOrderStatus, 
                     actor_id: int, reason: str = None) -> Dict:
        """
        Executa transição de estado com validação e auditoria
        
        Args:
            pre_order_id: ID da pré-ordem
            new_status: Novo estado desejado
            actor_id: ID do usuário que está executando a ação
            reason: Motivo da transição (opcional)
            
        Returns:
            dict: Resultado da transição com detalhes
            
        Raises:
            ValueError: Se a transição for inválida
            SQLAlchemyError: Se houver erro no banco de dados
            
        Requirements: 2.5, 4.5, 5.1, 8.4, 14.1, 15.3
        """
        # Buscar pré-ordem
        pre_order = PreOrder.query.get(pre_order_id)
        if not pre_order:
            raise ValueError(f"Pré-ordem {pre_order_id} não encontrada")
        
        current_state = PreOrderStateManager.get_current_state(pre_order)
        
        # Converter string para enum se necessário
        if isinstance(new_status, str):
            try:
                new_status = PreOrderStatus(new_status)
            except ValueError:
                raise ValueError(f"Estado inválido: {new_status}")
        
        # Se já está no estado alvo, retornar sucesso (idempotência)
        if current_state == new_status:
            logger.info(f"Pré-ordem {pre_order_id} já está no estado {new_status.value}")
            return {
                'success': True,
                'pre_order_id': pre_order_id,
                'previous_state': current_state.value,
                'new_state': new_status.value,
                'message': f'Pré-ordem já estava no estado {new_status.value}',
                'was_already_in_state': True
            }
        
        # Verificar se transição é válida
        can_transition, transition_reason = PreOrderStateManager.can_transition_to(pre_order, new_status)
        if not can_transition:
            error_msg = f"Transição inválida de {current_state.value} para {new_status.value}: {transition_reason}"
            logger.error(f"Pré-ordem {pre_order_id}: {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # Registrar estado anterior
            old_status = pre_order.status
            
            # Atualizar estado
            pre_order.status = new_status.value
            pre_order.updated_at = datetime.utcnow()
            
            # Executar ações específicas do estado
            PreOrderStateManager._execute_state_actions(pre_order, new_status, current_state)
            
            # Registrar no histórico
            history_entry = PreOrderHistory(
                pre_order_id=pre_order_id,
                event_type=f'transition_to_{new_status.value}',
                actor_id=actor_id,
                description=reason or transition_reason,
                event_data={
                    'previous_state': current_state.value,
                    'new_state': new_status.value,
                    'transition_reason': transition_reason
                }
            )
            db.session.add(history_entry)
            
            # Commit da transação
            db.session.commit()
            
            # Log da transição
            logger.info(
                f"Pré-ordem {pre_order_id} transicionou de {current_state.value} "
                f"para {new_status.value}. Ator: {actor_id}, Razão: {reason or transition_reason}"
            )
            
            return {
                'success': True,
                'pre_order_id': pre_order_id,
                'previous_state': old_status,
                'new_state': new_status.value,
                'transition_reason': reason or transition_reason,
                'message': f'Estado alterado de {current_state.value} para {new_status.value}',
                'was_already_in_state': False
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao transicionar estado da pré-ordem {pre_order_id}: {str(e)}")
            raise e
    
    @staticmethod
    def check_mutual_acceptance(pre_order_id: int) -> bool:
        """
        Verifica se ambas as partes aceitaram os termos da pré-ordem
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            bool: True se ambas as partes aceitaram, False caso contrário
            
        Requirements: 5.1
        """
        pre_order = PreOrder.query.get(pre_order_id)
        if not pre_order:
            logger.error(f"Pré-ordem {pre_order_id} não encontrada")
            return False
        
        has_mutual = pre_order.client_accepted_terms and pre_order.provider_accepted_terms
        
        logger.debug(
            f"Pré-ordem {pre_order_id}: Aceitação mútua = {has_mutual} "
            f"(cliente: {pre_order.client_accepted_terms}, prestador: {pre_order.provider_accepted_terms})"
        )
        
        return has_mutual
    
    @staticmethod
    def reset_acceptances(pre_order_id: int) -> bool:
        """
        Limpa as flags de aceitação quando há uma nova proposta
        
        Quando uma nova proposta é criada, as aceitações anteriores devem ser resetadas
        pois os termos mudaram e ambas as partes precisam aceitar novamente.
        
        Args:
            pre_order_id: ID da pré-ordem
            
        Returns:
            bool: True se resetou com sucesso, False caso contrário
            
        Requirements: 2.5, 4.5
        """
        try:
            pre_order = PreOrder.query.get(pre_order_id)
            if not pre_order:
                logger.error(f"Pré-ordem {pre_order_id} não encontrada")
                return False
            
            # Guardar valores anteriores para log
            old_client_accepted = pre_order.client_accepted_terms
            old_provider_accepted = pre_order.provider_accepted_terms
            
            # Resetar flags de aceitação
            pre_order.client_accepted_terms = False
            pre_order.provider_accepted_terms = False
            pre_order.client_accepted_at = None
            pre_order.provider_accepted_at = None
            pre_order.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(
                f"Pré-ordem {pre_order_id}: Aceitações resetadas "
                f"(cliente: {old_client_accepted} -> False, prestador: {old_provider_accepted} -> False)"
            )
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao resetar aceitações da pré-ordem {pre_order_id}: {str(e)}")
            return False
    
    @staticmethod
    def _execute_state_actions(pre_order: PreOrder, new_state: PreOrderStatus, 
                               old_state: PreOrderStatus):
        """
        Executa ações específicas quando muda de estado
        
        Args:
            pre_order: Pré-ordem sendo modificada
            new_state: Novo estado
            old_state: Estado anterior
            
        Requirements: 8.4, 14.1, 15.3
        """
        # Ações ao entrar em CANCELADA
        if new_state == PreOrderStatus.CANCELADA:
            pre_order.cancelled_at = datetime.utcnow()
            logger.info(f"Pré-ordem {pre_order.id} cancelada em {pre_order.cancelled_at}")
        
        # Ações ao entrar em CONVERTIDA
        elif new_state == PreOrderStatus.CONVERTIDA:
            pre_order.converted_at = datetime.utcnow()
            logger.info(f"Pré-ordem {pre_order.id} convertida em {pre_order.converted_at}")
        
        # Ações ao entrar em EXPIRADA
        elif new_state == PreOrderStatus.EXPIRADA:
            logger.info(f"Pré-ordem {pre_order.id} expirada")
        
        # Ações ao retornar para EM_NEGOCIACAO após falha
        elif new_state == PreOrderStatus.EM_NEGOCIACAO and old_state == PreOrderStatus.PRONTO_CONVERSAO:
            logger.warning(
                f"Pré-ordem {pre_order.id} retornou de PRONTO_CONVERSAO para EM_NEGOCIACAO "
                f"(possível falha na conversão)"
            )
    
    @staticmethod
    def get_available_transitions(pre_order: PreOrder) -> List[Dict]:
        """
        Retorna lista de transições disponíveis para a pré-ordem
        
        Args:
            pre_order: Pré-ordem a ser verificada
            
        Returns:
            list: Lista de dicionários com transições disponíveis
        """
        current_state = PreOrderStateManager.get_current_state(pre_order)
        available = []
        
        for transition in PreOrderStateManager.VALID_TRANSITIONS:
            if transition.from_state == current_state:
                # Verificar condição se existir
                can_transition = True
                if transition.condition:
                    can_transition = transition.condition(pre_order)
                
                if can_transition:
                    available.append({
                        'to_state': transition.to_state.value,
                        'description': transition.description
                    })
        
        return available
    
    @staticmethod
    def get_state_description(pre_order: PreOrder) -> Dict[str, str]:
        """
        Retorna descrição amigável do estado atual
        
        Args:
            pre_order: Pré-ordem a ser verificada
            
        Returns:
            dict: Dicionário com descrições do estado
        """
        current_state = PreOrderStateManager.get_current_state(pre_order)
        
        descriptions = {
            PreOrderStatus.EM_NEGOCIACAO: {
                'status': 'Em Negociação',
                'description': 'Pré-ordem em processo de negociação entre as partes',
                'client_message': 'Você pode propor alterações ou aceitar os termos atuais.',
                'provider_message': 'Você pode propor alterações ou aceitar os termos atuais.'
            },
            PreOrderStatus.AGUARDANDO_RESPOSTA: {
                'status': 'Aguardando Resposta',
                'description': 'Proposta enviada, aguardando resposta da outra parte',
                'client_message': 'Aguardando resposta do prestador sobre a proposta.',
                'provider_message': 'Aguardando resposta do cliente sobre a proposta.'
            },
            PreOrderStatus.PRONTO_CONVERSAO: {
                'status': 'Pronto para Conversão',
                'description': 'Ambas as partes aceitaram os termos, pronto para converter em ordem',
                'client_message': 'Termos aceitos! A pré-ordem será convertida em ordem em breve.',
                'provider_message': 'Termos aceitos! A pré-ordem será convertida em ordem em breve.'
            },
            PreOrderStatus.CONVERTIDA: {
                'status': 'Convertida',
                'description': 'Pré-ordem convertida em ordem definitiva com sucesso',
                'client_message': 'Ordem criada com sucesso! Valores bloqueados em escrow.',
                'provider_message': 'Ordem criada com sucesso! Você pode iniciar o serviço.'
            },
            PreOrderStatus.CANCELADA: {
                'status': 'Cancelada',
                'description': 'Pré-ordem cancelada por uma das partes',
                'client_message': 'Pré-ordem cancelada.',
                'provider_message': 'Pré-ordem cancelada.'
            },
            PreOrderStatus.EXPIRADA: {
                'status': 'Expirada',
                'description': 'Pré-ordem expirou automaticamente',
                'client_message': 'Pré-ordem expirou. Crie um novo convite se necessário.',
                'provider_message': 'Pré-ordem expirou.'
            }
        }
        
        return descriptions.get(current_state, {
            'status': 'Estado Desconhecido',
            'description': f'Estado atual: {current_state.value}',
            'client_message': 'Estado não reconhecido.',
            'provider_message': 'Estado não reconhecido.'
        })
