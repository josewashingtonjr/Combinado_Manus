#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, Invite, Proposal
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from enum import Enum
from typing import Optional, Dict, List
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class InviteState(Enum):
    """Estados possíveis de um convite"""
    PENDENTE = "pendente"                    # Convite criado, aguardando resposta do prestador
    PROPOSTA_ENVIADA = "proposta_enviada"   # Prestador enviou proposta de alteração
    PROPOSTA_ACEITA = "proposta_aceita"     # Cliente aceitou a proposta
    PROPOSTA_REJEITADA = "proposta_rejeitada" # Cliente rejeitou a proposta
    ACEITO = "aceito"                       # Convite aceito (gera ordem de serviço)
    RECUSADO = "recusado"                   # Convite recusado pelo prestador
    EXPIRADO = "expirado"                   # Convite expirou
    CONVERTIDO = "convertido"               # Convertido em ordem de serviço

class StateTransition:
    """Define uma transição válida entre estados"""
    def __init__(self, from_state: InviteState, to_state: InviteState, 
                 condition: callable = None, description: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.description = description

class InviteStateManager:
    """Gerenciador de estados dos convites com validação e auditoria"""
    
    # Definir transições válidas entre estados
    VALID_TRANSITIONS = [
        # Do estado PENDENTE
        StateTransition(
            InviteState.PENDENTE, 
            InviteState.PROPOSTA_ENVIADA,
            description="Prestador envia proposta de alteração"
        ),
        StateTransition(
            InviteState.PENDENTE, 
            InviteState.ACEITO,
            description="Prestador aceita convite sem alterações"
        ),
        StateTransition(
            InviteState.PENDENTE, 
            InviteState.RECUSADO,
            description="Prestador recusa convite"
        ),
        StateTransition(
            InviteState.PENDENTE, 
            InviteState.EXPIRADO,
            lambda invite: invite.is_expired,
            description="Convite expira automaticamente"
        ),
        
        # Do estado PROPOSTA_ENVIADA
        StateTransition(
            InviteState.PROPOSTA_ENVIADA, 
            InviteState.PROPOSTA_ACEITA,
            description="Cliente aceita proposta de alteração"
        ),
        StateTransition(
            InviteState.PROPOSTA_ENVIADA, 
            InviteState.PROPOSTA_REJEITADA,
            description="Cliente rejeita proposta de alteração"
        ),
        StateTransition(
            InviteState.PROPOSTA_ENVIADA, 
            InviteState.PENDENTE,
            description="Prestador cancela proposta"
        ),
        StateTransition(
            InviteState.PROPOSTA_ENVIADA, 
            InviteState.EXPIRADO,
            lambda invite: invite.is_expired,
            description="Convite expira com proposta pendente"
        ),
        
        # Do estado PROPOSTA_ACEITA
        StateTransition(
            InviteState.PROPOSTA_ACEITA, 
            InviteState.ACEITO,
            description="Prestador aceita convite com proposta aprovada"
        ),
        
        # Do estado PROPOSTA_REJEITADA
        StateTransition(
            InviteState.PROPOSTA_REJEITADA, 
            InviteState.PENDENTE,
            description="Retorna ao estado original após rejeição"
        ),
        StateTransition(
            InviteState.PROPOSTA_REJEITADA, 
            InviteState.PROPOSTA_ENVIADA,
            description="Prestador envia nova proposta após rejeição"
        ),
        StateTransition(
            InviteState.PROPOSTA_REJEITADA, 
            InviteState.ACEITO,
            description="Prestador aceita convite com valor original após rejeição"
        ),
        
        # Do estado ACEITO
        StateTransition(
            InviteState.ACEITO, 
            InviteState.CONVERTIDO,
            description="Convite convertido em ordem de serviço"
        ),
    ]
    
    @staticmethod
    def get_current_state(invite: Invite) -> InviteState:
        """
        Determina o estado atual do convite baseado em suas propriedades
        
        Requirements: 5.1, 6.1, 8.1
        """
        # Verificar se expirado primeiro
        if invite.is_expired and invite.status != 'convertido':
            return InviteState.EXPIRADO
        
        # Estados baseados no status atual
        status_mapping = {
            'pendente': InviteState.PENDENTE,
            'aceito': InviteState.ACEITO,
            'recusado': InviteState.RECUSADO,
            'expirado': InviteState.EXPIRADO,
            'convertido': InviteState.CONVERTIDO,
            'convertido_pre_ordem': InviteState.CONVERTIDO  # Pré-ordem criada
        }
        
        # Se tem proposta ativa, determinar estado baseado na proposta
        if invite.has_active_proposal and invite.current_proposal_id:
            active_proposal = invite.get_active_proposal()
            if active_proposal:
                if active_proposal.status == 'pending':
                    return InviteState.PROPOSTA_ENVIADA
                elif active_proposal.status == 'accepted':
                    return InviteState.PROPOSTA_ACEITA
                elif active_proposal.status == 'rejected':
                    return InviteState.PROPOSTA_REJEITADA
        
        # Estado padrão baseado no status do convite
        return status_mapping.get(invite.status, InviteState.PENDENTE)
    
    @staticmethod
    def can_transition_to(invite: Invite, target_state: InviteState) -> tuple[bool, str]:
        """
        Verifica se o convite pode transicionar para o estado alvo
        
        Returns:
            tuple: (pode_transicionar, motivo_se_nao_pode)
            
        Requirements: 5.1, 5.2, 6.1, 6.2
        """
        current_state = InviteStateManager.get_current_state(invite)
        
        # Procurar transição válida
        for transition in InviteStateManager.VALID_TRANSITIONS:
            if (transition.from_state == current_state and 
                transition.to_state == target_state):
                
                # Verificar condição se existir
                if transition.condition and not transition.condition(invite):
                    return False, f"Condição não atendida: {transition.description}"
                
                return True, transition.description
        
        return False, f"Transição inválida de {current_state.value} para {target_state.value}"
    
    @staticmethod
    def transition_to_state(invite: Invite, target_state: InviteState, 
                          user_id: int = None, reason: str = None) -> dict:
        """
        Executa transição de estado com validação e auditoria
        
        Requirements: 1.1, 1.4, 2.1, 2.2, 2.3, 5.1, 5.2, 6.1, 6.2, 8.1, 9.1, 9.2, 10.1, 10.2, 10.3
        """
        current_state = InviteStateManager.get_current_state(invite)
        
        # Se já está no estado alvo, não fazer nada
        if current_state == target_state:
            return {
                'success': True,
                'invite_id': invite.id,
                'previous_state': current_state.value,
                'new_state': target_state.value,
                'previous_status': invite.status,
                'new_status': invite.status,
                'transition_reason': 'Já estava no estado alvo',
                'audit_log': None,
                'message': f'Convite já estava no estado {target_state.value}'
            }
        
        # Verificar se transição é válida
        can_transition, transition_reason = InviteStateManager.can_transition_to(invite, target_state)
        if not can_transition:
            raise ValueError(f"Transição inválida: {transition_reason}")
        
        try:
            # Registrar log de auditoria antes da mudança
            audit_log = InviteStateManager._create_audit_log(
                invite, current_state, target_state, user_id, reason or transition_reason
            )
            
            # Executar mudança de estado
            old_status = invite.status
            new_status = InviteStateManager._map_state_to_status(target_state)
            
            # Limpar campos de proposta baseado no estado alvo
            # Requirements: 2.1, 2.2, 2.3, 10.1, 10.2, 10.3
            if target_state == InviteState.PENDENTE:
                # Limpar todos os campos de proposta ao retornar para PENDENTE
                invite.has_active_proposal = False
                invite.current_proposal_id = None
                invite.effective_value = None
                logger.info(f"Convite {invite.id}: Campos de proposta limpos ao transicionar para PENDENTE")
                
            elif target_state == InviteState.PROPOSTA_ACEITA:
                # Limpar has_active_proposal mas manter current_proposal_id e effective_value
                # effective_value já foi setado pelo Proposal.accept()
                invite.has_active_proposal = False
                # current_proposal_id mantém referência histórica
                logger.info(f"Convite {invite.id}: has_active_proposal limpo, mantendo referência da proposta")
                
            elif target_state == InviteState.PROPOSTA_REJEITADA:
                # Limpar todos os campos de proposta
                invite.has_active_proposal = False
                invite.current_proposal_id = None
                invite.effective_value = None
                logger.info(f"Convite {invite.id}: Campos de proposta limpos ao transicionar para PROPOSTA_REJEITADA")
            
            # Atualizar status do convite
            invite.status = new_status
            
            # Executar ações específicas do estado
            InviteStateManager._execute_state_actions(invite, target_state, current_state)
            
            # Validar integridade dos campos após a transição
            # Requirements: 9.4, 9.5, 10.5
            is_valid, validation_errors = InviteStateManager.validate_proposal_fields(invite, target_state)
            if not is_valid:
                error_msg = f"Inconsistência detectada após transição para {target_state.value}: {'; '.join(validation_errors)}"
                logger.error(f"VALIDAÇÃO FALHOU: Convite {invite.id} - {error_msg}")
                db.session.rollback()
                raise ValueError(error_msg)
            
            db.session.commit()
            
            # Log da transição
            logger.info(
                f"Convite {invite.id} transicionou de {current_state.value} "
                f"para {target_state.value}. Usuário: {user_id}, Razão: {reason or transition_reason}"
            )
            
            return {
                'success': True,
                'invite_id': invite.id,
                'previous_state': current_state.value,
                'new_state': target_state.value,
                'previous_status': old_status,
                'new_status': new_status,
                'transition_reason': reason or transition_reason,
                'audit_log': audit_log,
                'message': f'Estado alterado de {current_state.value} para {target_state.value}'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao transicionar estado do convite {invite.id}: {str(e)}")
            raise e
    
    @staticmethod
    def can_be_accepted(invite: Invite) -> tuple[bool, str]:
        """
        Verifica se o convite pode ser aceito pelo prestador
        
        Requirements: 1.1, 1.4, 5.1, 5.2, 6.1, 6.2
        """
        # Verificar primeiro se há proposta ativa pendente
        # Requirements: 1.1, 1.4
        if invite.has_active_proposal:
            return False, "Aguardando resposta do cliente sobre a proposta de alteração"
        
        current_state = InviteStateManager.get_current_state(invite)
        
        # Estados que permitem aceitação
        acceptable_states = [InviteState.PENDENTE, InviteState.PROPOSTA_ACEITA, InviteState.PROPOSTA_REJEITADA]
        
        if current_state not in acceptable_states:
            if current_state == InviteState.PROPOSTA_ENVIADA:
                return False, "Aguardando aprovação da proposta pelo cliente"
            # PROPOSTA_REJEITADA permite aceitação com valor original
            elif current_state == InviteState.EXPIRADO:
                return False, "Convite expirado"
            elif current_state == InviteState.ACEITO:
                return False, "Convite já foi aceito"
            elif current_state == InviteState.RECUSADO:
                return False, "Convite já foi recusado"
            elif current_state == InviteState.CONVERTIDO:
                return False, "Convite já foi convertido em ordem de serviço"
            else:
                return False, f"Estado atual não permite aceitação: {current_state.value}"
        
        # Verificações adicionais
        if invite.is_expired:
            return False, "Convite expirado"
        
        return True, "Convite pode ser aceito"
    
    @staticmethod
    def can_create_proposal(invite: Invite) -> tuple[bool, str]:
        """
        Verifica se uma proposta pode ser criada para o convite
        
        Requirements: 5.1, 5.2, 6.1, 6.2
        """
        current_state = InviteStateManager.get_current_state(invite)
        
        # Estados que permitem criação de proposta
        proposal_states = [InviteState.PENDENTE, InviteState.PROPOSTA_REJEITADA]
        
        if current_state not in proposal_states:
            if current_state == InviteState.PROPOSTA_ENVIADA:
                return False, "Já existe uma proposta pendente para este convite"
            elif current_state == InviteState.PROPOSTA_ACEITA:
                return False, "Proposta já foi aceita. Aceite o convite para prosseguir"
            elif current_state == InviteState.EXPIRADO:
                return False, "Convite expirado"
            elif current_state == InviteState.ACEITO:
                return False, "Convite já foi aceito"
            elif current_state == InviteState.RECUSADO:
                return False, "Convite já foi recusado"
            elif current_state == InviteState.CONVERTIDO:
                return False, "Convite já foi convertido em ordem de serviço"
            else:
                return False, f"Estado atual não permite criação de proposta: {current_state.value}"
        
        # Verificações adicionais
        if invite.is_expired:
            return False, "Convite expirado"
        
        return True, "Proposta pode ser criada"
    
    @staticmethod
    def get_available_actions(invite: Invite, user_role: str = None) -> Dict[str, List[str]]:
        """
        Retorna ações disponíveis para o convite baseado no estado atual
        
        Requirements: 6.3, 6.4, 9.4
        """
        current_state = InviteStateManager.get_current_state(invite)
        actions = {'client': [], 'prestador': [], 'system': []}
        
        # Ações baseadas no estado atual
        if current_state == InviteState.PENDENTE:
            actions['prestador'] = ['aceitar_convite', 'recusar_convite', 'criar_proposta']
            
        elif current_state == InviteState.PROPOSTA_ENVIADA:
            actions['client'] = ['aprovar_proposta', 'rejeitar_proposta']
            actions['prestador'] = ['cancelar_proposta']
            
        elif current_state == InviteState.PROPOSTA_ACEITA:
            actions['prestador'] = ['aceitar_convite']
            
        elif current_state == InviteState.PROPOSTA_REJEITADA:
            actions['prestador'] = ['aceitar_convite', 'criar_proposta']
            
        elif current_state == InviteState.ACEITO:
            # Conversão é automática ao aceitar, não há ações manuais
            pass
            
        # Ações do sistema (automáticas)
        if invite.is_expired and current_state != InviteState.EXPIRADO:
            actions['system'] = ['expirar_convite']
        
        # Filtrar por papel do usuário se especificado
        if user_role:
            return {user_role: actions.get(user_role, [])}
        
        return actions
    
    @staticmethod
    def get_state_description(invite: Invite) -> Dict[str, str]:
        """
        Retorna descrição amigável do estado atual
        
        Requirements: 6.3, 6.4, 9.4
        """
        current_state = InviteStateManager.get_current_state(invite)
        
        descriptions = {
            InviteState.PENDENTE: {
                'status': 'Aguardando Resposta',
                'description': 'Convite enviado, aguardando resposta do prestador',
                'client_message': 'Convite enviado. Aguardando resposta do prestador.',
                'prestador_message': 'Você pode aceitar, recusar ou propor alterações neste convite.'
            },
            InviteState.PROPOSTA_ENVIADA: {
                'status': 'Proposta Enviada',
                'description': 'Prestador enviou proposta de alteração, aguardando aprovação do cliente',
                'client_message': 'Nova proposta recebida. Analise e aprove ou rejeite.',
                'prestador_message': 'Proposta enviada. Aguardando aprovação do cliente.'
            },
            InviteState.PROPOSTA_ACEITA: {
                'status': 'Proposta Aprovada',
                'description': 'Cliente aprovou a proposta, prestador pode aceitar o convite',
                'client_message': 'Proposta aprovada. Aguardando aceitação do prestador.',
                'prestador_message': 'Sua proposta foi aprovada! Você pode aceitar o convite agora.'
            },
            InviteState.PROPOSTA_REJEITADA: {
                'status': 'Proposta Rejeitada',
                'description': 'Cliente rejeitou a proposta, convite retornou ao estado original',
                'client_message': 'Proposta rejeitada. Prestador pode aceitar valor original ou enviar nova proposta.',
                'prestador_message': 'Proposta rejeitada. Você pode aceitar o valor original ou enviar nova proposta.'
            },
            InviteState.ACEITO: {
                'status': 'Convite Aceito',
                'description': 'Convite aceito pelo prestador, pronto para conversão em ordem',
                'client_message': 'Convite aceito! Você pode converter em ordem de serviço.',
                'prestador_message': 'Convite aceito com sucesso. Aguardando conversão em ordem de serviço.'
            },
            InviteState.RECUSADO: {
                'status': 'Convite Recusado',
                'description': 'Convite recusado pelo prestador',
                'client_message': 'Convite recusado pelo prestador.',
                'prestador_message': 'Você recusou este convite.'
            },
            InviteState.EXPIRADO: {
                'status': 'Convite Expirado',
                'description': 'Convite expirou automaticamente',
                'client_message': 'Convite expirou. Crie um novo convite se necessário.',
                'prestador_message': 'Este convite expirou.'
            },
            InviteState.CONVERTIDO: {
                'status': 'Ordem Criada',
                'description': 'Convite convertido em ordem de serviço ativa',
                'client_message': 'Ordem de serviço criada com sucesso.',
                'prestador_message': 'Ordem de serviço criada. Você pode iniciar o trabalho.'
            }
        }
        
        return descriptions.get(current_state, {
            'status': 'Estado Desconhecido',
            'description': f'Estado atual: {current_state.value}',
            'client_message': 'Estado não reconhecido.',
            'prestador_message': 'Estado não reconhecido.'
        })
    
    @staticmethod
    def _map_state_to_status(state: InviteState) -> str:
        """Mapeia estado interno para status do banco de dados"""
        mapping = {
            InviteState.PENDENTE: 'pendente',
            InviteState.PROPOSTA_ENVIADA: 'pendente',  # Mantém pendente, mas com proposta ativa
            InviteState.PROPOSTA_ACEITA: 'pendente',   # Mantém pendente, mas com proposta aceita
            InviteState.PROPOSTA_REJEITADA: 'pendente', # Volta para pendente
            InviteState.ACEITO: 'aceito',
            InviteState.RECUSADO: 'recusado',
            InviteState.EXPIRADO: 'expirado',
            InviteState.CONVERTIDO: 'convertido'
        }
        return mapping.get(state, 'pendente')
    
    @staticmethod
    def _execute_state_actions(invite: Invite, new_state: InviteState, old_state: InviteState):
        """
        Executa ações específicas quando muda de estado
        
        Note: Limpeza de campos de proposta é feita em transition_to_state()
        Requirements: 9.1, 9.2, 10.1, 10.2, 10.3
        """
        
        # Ações ao entrar em ACEITO
        if new_state == InviteState.ACEITO:
            invite.responded_at = datetime.utcnow()
        
        # Ações ao entrar em RECUSADO
        elif new_state == InviteState.RECUSADO:
            invite.responded_at = datetime.utcnow()
    
    @staticmethod
    def validate_proposal_fields(invite: Invite, expected_state: InviteState = None) -> tuple[bool, list]:
        """
        Valida que os campos de proposta estão corretos para o estado atual do convite
        
        Args:
            invite: Convite a ser validado
            expected_state: Estado esperado (opcional). Se não fornecido, usa o estado atual
            
        Returns:
            tuple: (is_valid, list_of_errors)
            
        Requirements: 9.4, 9.5, 10.5
        """
        errors = []
        state = expected_state or InviteStateManager.get_current_state(invite)
        
        # Validações específicas por estado
        if state == InviteState.PENDENTE:
            # PENDENTE: Todos os campos de proposta devem estar limpos
            if invite.has_active_proposal:
                errors.append(f"Estado PENDENTE: has_active_proposal deveria ser False, mas é {invite.has_active_proposal}")
            
            if invite.current_proposal_id is not None:
                errors.append(f"Estado PENDENTE: current_proposal_id deveria ser None, mas é {invite.current_proposal_id}")
            
            if invite.effective_value is not None:
                errors.append(f"Estado PENDENTE: effective_value deveria ser None, mas é {invite.effective_value}")
        
        elif state == InviteState.PROPOSTA_ENVIADA:
            # PROPOSTA_ENVIADA: Deve ter proposta ativa
            if not invite.has_active_proposal:
                errors.append(f"Estado PROPOSTA_ENVIADA: has_active_proposal deveria ser True, mas é {invite.has_active_proposal}")
            
            if invite.current_proposal_id is None:
                errors.append(f"Estado PROPOSTA_ENVIADA: current_proposal_id não deveria ser None")
            
            if invite.effective_value is not None:
                errors.append(f"Estado PROPOSTA_ENVIADA: effective_value deveria ser None, mas é {invite.effective_value}")
            
            # Validar que a proposta existe e está pendente
            if invite.current_proposal_id:
                proposal = Proposal.query.get(invite.current_proposal_id)
                if not proposal:
                    errors.append(f"Estado PROPOSTA_ENVIADA: Proposta {invite.current_proposal_id} não encontrada")
                elif proposal.status != 'pending':
                    errors.append(f"Estado PROPOSTA_ENVIADA: Proposta deveria estar 'pending', mas está '{proposal.status}'")
        
        elif state == InviteState.PROPOSTA_ACEITA:
            # PROPOSTA_ACEITA: Deve ter effective_value e current_proposal_id, mas não has_active_proposal
            if invite.has_active_proposal:
                errors.append(f"Estado PROPOSTA_ACEITA: has_active_proposal deveria ser False, mas é {invite.has_active_proposal}")
            
            if invite.current_proposal_id is None:
                errors.append(f"Estado PROPOSTA_ACEITA: current_proposal_id não deveria ser None")
            
            if invite.effective_value is None:
                errors.append(f"Estado PROPOSTA_ACEITA: effective_value não deveria ser None")
            
            # Validar que a proposta existe e está aceita
            if invite.current_proposal_id:
                proposal = Proposal.query.get(invite.current_proposal_id)
                if not proposal:
                    errors.append(f"Estado PROPOSTA_ACEITA: Proposta {invite.current_proposal_id} não encontrada")
                elif proposal.status != 'accepted':
                    errors.append(f"Estado PROPOSTA_ACEITA: Proposta deveria estar 'accepted', mas está '{proposal.status}'")
                elif invite.effective_value and proposal.proposed_value != invite.effective_value:
                    errors.append(f"Estado PROPOSTA_ACEITA: effective_value ({invite.effective_value}) não corresponde ao proposed_value ({proposal.proposed_value})")
        
        elif state == InviteState.PROPOSTA_REJEITADA:
            # PROPOSTA_REJEITADA: Todos os campos devem estar limpos (estado transitório)
            if invite.has_active_proposal:
                errors.append(f"Estado PROPOSTA_REJEITADA: has_active_proposal deveria ser False, mas é {invite.has_active_proposal}")
            
            if invite.current_proposal_id is not None:
                errors.append(f"Estado PROPOSTA_REJEITADA: current_proposal_id deveria ser None, mas é {invite.current_proposal_id}")
            
            if invite.effective_value is not None:
                errors.append(f"Estado PROPOSTA_REJEITADA: effective_value deveria ser None, mas é {invite.effective_value}")
        
        elif state == InviteState.ACEITO:
            # ACEITO: Não deve ter proposta ativa, mas pode ter referência histórica
            if invite.has_active_proposal:
                errors.append(f"Estado ACEITO: has_active_proposal deveria ser False, mas é {invite.has_active_proposal}")
            
            # effective_value pode ou não existir dependendo se houve proposta aceita
            # current_proposal_id pode existir como referência histórica
        
        elif state in [InviteState.RECUSADO, InviteState.EXPIRADO, InviteState.CONVERTIDO]:
            # Estados finais: has_active_proposal deve ser False
            if invite.has_active_proposal:
                errors.append(f"Estado {state.value}: has_active_proposal deveria ser False, mas é {invite.has_active_proposal}")
        
        # Validações gerais
        # Se has_active_proposal é True, deve ter current_proposal_id
        if invite.has_active_proposal and invite.current_proposal_id is None:
            errors.append("Inconsistência: has_active_proposal é True mas current_proposal_id é None")
        
        # Se tem effective_value, deve ser diferente de original_value
        if invite.effective_value is not None and invite.effective_value == invite.original_value:
            errors.append(f"Inconsistência: effective_value ({invite.effective_value}) é igual ao original_value ({invite.original_value})")
        
        is_valid = len(errors) == 0
        
        # Log de validação
        if is_valid:
            logger.debug(f"Validação OK: Convite {invite.id} no estado {state.value} está consistente")
        else:
            logger.warning(f"Validação FALHOU: Convite {invite.id} no estado {state.value} tem {len(errors)} erro(s): {errors}")
        
        return is_valid, errors
    
    @staticmethod
    def _create_audit_log(invite: Invite, from_state: InviteState, to_state: InviteState, 
                         user_id: int = None, reason: str = None) -> dict:
        """
        Cria log de auditoria para mudança de estado
        
        Requirements: 8.1, 8.2, 8.3
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'invite_id': invite.id,
            'from_state': from_state.value,
            'to_state': to_state.value,
            'user_id': user_id,
            'reason': reason,
            'invite_data': {
                'service_title': invite.service_title,
                'original_value': float(invite.original_value),
                'effective_value': float(invite.effective_value) if invite.effective_value else None,
                'has_active_proposal': invite.has_active_proposal,
                'current_proposal_id': invite.current_proposal_id
            }
        }
        
        # Log para arquivo/sistema de auditoria
        logger.info(f"AUDIT: Convite {invite.id} - {from_state.value} -> {to_state.value} "
                   f"(User: {user_id}, Reason: {reason})")
        
        return audit_entry