#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Invite, Order
from services.wallet_service import WalletService
from services.invite_state_manager import InviteStateManager, InviteState
from services.exceptions import (
    InsufficientBalanceError,
    InviteValidationError
)
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class InviteService:
    """Serviço para gerenciar convites de serviço"""
    
    # Taxa de contestação padrão (configurável no futuro)
    CONTESTATION_FEE = Decimal('10.00')  # R$ 10,00 por convite
    
    # Prazo padrão de expiração de convites (em dias)
    DEFAULT_EXPIRATION_DAYS = 7
    
    @staticmethod
    def create_invite(client_id, invited_phone, service_title, service_description, 
                     original_value, delivery_date, service_category=None):
        """
        Cria um novo convite com validação de saldo conforme tokenomics
        
        Validações:
        - Cliente deve ter saldo suficiente para: valor do serviço + taxa de contestação
        - Telefone do prestador deve ser válido
        - Data de entrega deve ser futura
        """
        
        # Converter original_value para Decimal para evitar erro de tipo
        try:
            original_value_decimal = Decimal(str(original_value))
        except (ValueError, TypeError):
            raise ValueError("Valor do serviço inválido")
        
        # Validações básicas
        if original_value_decimal <= 0:
            raise ValueError("Valor do serviço deve ser positivo")
        
        if delivery_date <= datetime.utcnow():
            raise ValueError("Data de entrega deve ser futura")
        
        if not invited_phone or len(invited_phone.strip()) < 10:
            raise ValueError("Telefone do prestador é obrigatório e deve ser válido")
        
        # Verificar se cliente existe
        client = User.query.get(client_id)
        if not client:
            raise ValueError("Cliente não encontrado")
        
        # Calcular valor total necessário (serviço + taxa de contestação)
        total_required = original_value_decimal + InviteService.CONTESTATION_FEE
        
        # Validar saldo do cliente
        if not WalletService.has_sufficient_balance(client_id, total_required):
            client_balance = WalletService.get_wallet_balance(client_id)
            raise ValueError(
                f"Saldo insuficiente. Necessário: R$ {total_required:.2f} "
                f"(serviço: R$ {original_value:.2f} + taxa: R$ {InviteService.CONTESTATION_FEE:.2f}). "
                f"Saldo atual: R$ {client_balance:.2f}"
            )
        
        try:
            # Criar o convite
            # Quando o cliente cria o convite, ele já está aceitando implicitamente
            invite = Invite(
                client_id=client_id,
                invited_phone=invited_phone.strip(),
                service_title=service_title,
                service_description=service_description,
                service_category=service_category,
                original_value=original_value_decimal,
                delivery_date=delivery_date,
                expires_at=delivery_date,  # Expira na data do serviço
                client_accepted=True,  # Cliente aceita ao criar o convite
                client_accepted_at=datetime.utcnow()  # Registrar timestamp
            )
            
            db.session.add(invite)
            db.session.commit()
            
            logger.info(
                f"CONVITE CRIADO: Convite {invite.id} criado pelo cliente {client_id}. "
                f"Cliente já aceitou automaticamente. Aguardando aceitação do prestador {invited_phone}."
            )
            
            return {
                'success': True,
                'invite_id': invite.id,
                'token': invite.token,
                'invite_link': invite.invite_link,
                'expires_at': invite.expires_at,
                'message': f'Convite criado com sucesso!'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_invite_by_token(token):
        """Recupera um convite pelo token único"""
        invite = Invite.query.filter_by(token=token).first()
        if not invite:
            raise ValueError("Convite não encontrado")
        
        return invite
    
    @staticmethod
    def get_invites_sent_by_client(client_id, status=None):
        """Retorna convites enviados por um cliente"""
        query = Invite.query.filter_by(client_id=client_id)
        
        if status:
            query = query.filter_by(status=status)
        
        invites = query.order_by(Invite.created_at.desc()).all()
        
        return [{
            'id': invite.id,
            'invited_phone': invite.invited_phone,
            'service_title': invite.service_title,
            'service_description': invite.service_description,
            'service_category': invite.service_category,
            'original_value': float(invite.original_value),
            'final_value': float(invite.final_value) if invite.final_value else None,
            'delivery_date': invite.delivery_date,
            'status': invite.status,
            'created_at': invite.created_at,
            'expires_at': invite.expires_at,
            'responded_at': invite.responded_at,
            'token': invite.token,
            'invite_link': invite.invite_link,
            'is_expired': invite.is_expired,
            'can_be_accepted': invite.can_be_accepted
        } for invite in invites]
    
    @staticmethod
    def get_invites_for_phone(phone, status=None):
        """Retorna convites recebidos por um telefone"""
        query = Invite.query.filter_by(invited_phone=phone)
        
        if status:
            query = query.filter_by(status=status)
        
        invites = query.order_by(Invite.created_at.desc()).all()
        
        return [{
            'id': invite.id,
            'client_id': invite.client_id,
            'client_name': invite.client.nome if invite.client else 'Cliente não encontrado',
            'service_title': invite.service_title,
            'service_description': invite.service_description,
            'service_category': invite.service_category,
            'original_value': float(invite.original_value),
            'final_value': float(invite.final_value) if invite.final_value else None,
            'delivery_date': invite.delivery_date,
            'status': invite.status,
            'created_at': invite.created_at,
            'expires_at': invite.expires_at,
            'responded_at': invite.responded_at,
            'token': invite.token,
            'invite_link': invite.invite_link,
            'is_expired': invite.is_expired,
            'can_be_accepted': invite.can_be_accepted
        } for invite in invites]
    
    @staticmethod
    def accept_invite_as_client(invite_id, client_id):
        """
        Cliente aceita o convite
        
        Validações:
        - Usuário deve ser o cliente do convite
        - Cliente deve ter saldo suficiente para valor do serviço
        - Convite deve estar válido
        
        Após aceitação, chama InviteAcceptanceCoordinator para verificar aceitação mútua
        
        Args:
            invite_id (int): ID do convite
            client_id (int): ID do cliente
            
        Returns:
            dict: Resultado da aceitação com informações sobre criação de ordem
            
        Requirements: 1.1, 8.1, 8.3, 8.5, 9.1, 9.2
        """
        invite = Invite.query.get(invite_id)
        if not invite:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} não encontrado. "
                f"Cliente ID: {client_id}"
            )
            raise ValueError("Convite não encontrado")
        
        # Validar que é o cliente correto
        # Requirements: 1.1, 8.5
        if invite.client_id != client_id:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Cliente {client_id} tentou aceitar convite {invite_id} "
                f"que pertence ao cliente {invite.client_id}"
            )
            raise ValueError("Usuário não autorizado para aceitar este convite")
        
        # Verificar se já aceitou
        if invite.client_accepted:
            logger.info(
                f"ACEITAÇÃO DUPLICADA: Cliente {client_id} tentou aceitar convite {invite_id} "
                f"que já foi aceito em {invite.client_accepted_at}"
            )
            raise ValueError("Você já aceitou este convite")
        
        # Verificar se convite está válido
        if invite.status not in ['pendente', 'aceito']:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} com status '{invite.status}' "
                f"não pode ser aceito. Cliente ID: {client_id}"
            )
            raise ValueError(f"Convite não pode ser aceito. Status atual: {invite.status}")
        
        # Verificar se convite está expirado
        if invite.is_expired:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} expirado. "
                f"Data de expiração: {invite.expires_at}. Cliente ID: {client_id}"
            )
            raise ValueError("Este convite expirou")
        
        # Obter valor efetivo do convite
        effective_value = invite.current_value
        
        # Validar saldo suficiente antes de aceitar
        # Requirements: 8.1, 8.3
        if not WalletService.has_sufficient_balance(client_id, effective_value):
            client_balance = WalletService.get_wallet_balance(client_id)
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Saldo insuficiente. Cliente {client_id}, "
                f"Convite {invite_id}, Necessário: R$ {effective_value:.2f}, "
                f"Disponível: R$ {client_balance:.2f}"
            )
            # Lançar exceção personalizada
            # Requirements: 7.4, 8.3, 8.4
            # Não alterar estado do convite
            raise InsufficientBalanceError(
                user_id=client_id,
                user_type='cliente',
                required_amount=effective_value,
                current_balance=client_balance,
                purpose='aceitar o convite (valor do serviço)'
            )
        
        try:
            # Marcar client_accepted como True e registrar timestamp
            # Requirements: 1.1, 9.1, 9.2
            invite.client_accepted = True
            invite.client_accepted_at = datetime.utcnow()
            db.session.commit()
            
            # Log detalhado de aceitação
            # Requirements: 9.1, 9.2
            logger.info(
                f"ACEITAÇÃO CLIENTE: Convite {invite_id} aceito pelo cliente {client_id}. "
                f"Timestamp: {invite.client_accepted_at.isoformat()}, "
                f"Valor: R$ {effective_value:.2f}, "
                f"Prestador: {invite.invited_phone}, "
                f"Status anterior: {invite.status}, "
                f"Prestador já aceitou: {invite.provider_accepted}"
            )
            
            # Verificar se há aceitação mútua
            # Se ambas as partes aceitaram, criar PRÉ-ORDEM para negociação
            # Requirements: 1.1, 1.2, 1.3 (sistema-pre-ordem-negociacao)
            # Otimização Mobile: Convites simplificados, negociação na pré-ordem
            if invite.is_mutually_accepted:
                # Aceitação mútua detectada - criar PRÉ-ORDEM (não ordem direta)
                logger.info(
                    f"ACEITAÇÃO MÚTUA: Convite {invite_id} aceito por ambas as partes. "
                    f"Criando pré-ordem para negociação."
                )
                
                try:
                    from services.pre_order_service import PreOrderService
                    
                    # Criar pré-ordem a partir do convite
                    pre_order_result = PreOrderService.create_from_invite(invite_id)
                    
                    if pre_order_result.get('success'):
                        pre_order_id = pre_order_result.get('pre_order_id')
                        
                        logger.info(
                            f"PRÉ-ORDEM CRIADA (CLIENTE): Convite {invite_id} convertido em pré-ordem {pre_order_id}. "
                            f"Cliente: {invite.client_id}, Prestador: {pre_order_result.get('provider_id')}"
                        )
                        
                        return {
                            'success': True,
                            'order_created': False,
                            'pre_order_created': True,
                            'pre_order_id': pre_order_id,
                            'message': f'Convite aceito! Pré-ordem #{pre_order_id} criada. Você pode negociar os termos antes de confirmar.',
                        }
                    else:
                        logger.error(
                            f"ERRO PRÉ-ORDEM: Falha ao criar pré-ordem do convite {invite_id}. "
                            f"Erro: {pre_order_result.get('error')}"
                        )
                        return {
                            'success': False,
                            'order_created': False,
                            'pre_order_created': False,
                            'error': pre_order_result.get('error', 'Erro ao criar pré-ordem')
                        }
                        
                except Exception as e:
                    db.session.rollback()
                    logger.error(
                        f"ERRO PRÉ-ORDEM: Exceção ao criar pré-ordem do convite {invite_id}. "
                        f"Erro: {str(e)}",
                        exc_info=True
                    )
                    return {
                        'success': False,
                        'order_created': False,
                        'pre_order_created': False,
                        'error': f'Erro ao criar pré-ordem: {str(e)}'
                    }
            else:
                # Ainda aguardando a outra parte aceitar
                pending_from = invite.pending_acceptance_from
                pending_name = 'prestador' if pending_from == 'prestador' else 'cliente'
                
                logger.info(
                    f"Convite {invite_id} aceito pelo cliente. "
                    f"Aguardando aceitação do {pending_name}."
                )
                
                return {
                    'success': True,
                    'order_created': False,
                    'pre_order_created': False,
                    'message': f'Convite aceito! Aguardando aceitação do {pending_name}.',
                    'pending_acceptance_from': pending_from
                }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(
                f"ERRO ACEITAÇÃO CLIENTE: Falha ao aceitar convite {invite_id} "
                f"como cliente {client_id}. Erro: {str(e)}",
                exc_info=True
            )
            raise e
    
    @staticmethod
    def accept_invite_as_provider(invite_id, provider_id):
        """
        Prestador aceita o convite
        
        Validações:
        - Usuário deve ser o prestador do convite (via telefone)
        - Prestador deve ter saldo suficiente para taxa de contestação
        - Convite deve estar válido
        
        Após aceitação, chama InviteAcceptanceCoordinator para verificar aceitação mútua
        
        Args:
            invite_id (int): ID do convite
            provider_id (int): ID do prestador
            
        Returns:
            dict: Resultado da aceitação com informações sobre criação de ordem
            
        Requirements: 1.2, 8.2, 8.3, 8.5, 9.1, 9.2
        """
        invite = Invite.query.get(invite_id)
        if not invite:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} não encontrado. "
                f"Prestador ID: {provider_id}"
            )
            raise ValueError("Convite não encontrado")
        
        # Verificar se prestador existe
        provider = User.query.get(provider_id)
        if not provider:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Prestador {provider_id} não encontrado. "
                f"Convite ID: {invite_id}"
            )
            raise ValueError("Prestador não encontrado")
        
        # Validar que é o prestador correto (via telefone)
        # Requirements: 1.2, 8.5
        if provider.phone != invite.invited_phone:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Prestador {provider_id} (telefone: {provider.phone}) "
                f"tentou aceitar convite {invite_id} destinado ao telefone {invite.invited_phone}"
            )
            raise ValueError("Este convite não foi enviado para seu telefone")
        
        # Verificar se já aceitou
        if invite.provider_accepted:
            logger.info(
                f"ACEITAÇÃO DUPLICADA: Prestador {provider_id} tentou aceitar convite {invite_id} "
                f"que já foi aceito em {invite.provider_accepted_at}"
            )
            raise ValueError("Você já aceitou este convite")
        
        # Verificar se convite está válido
        if invite.status not in ['pendente', 'aceito']:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} com status '{invite.status}' "
                f"não pode ser aceito. Prestador ID: {provider_id}"
            )
            raise ValueError(f"Convite não pode ser aceito. Status atual: {invite.status}")
        
        # Verificar se convite está expirado
        if invite.is_expired:
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Convite {invite_id} expirado. "
                f"Data de expiração: {invite.expires_at}. Prestador ID: {provider_id}"
            )
            raise ValueError("Este convite expirou")
        
        # Validar saldo suficiente para taxa antes de aceitar
        # Requirements: 8.2, 8.3
        if not WalletService.has_sufficient_balance(provider_id, InviteService.CONTESTATION_FEE):
            provider_balance = WalletService.get_wallet_balance(provider_id)
            logger.warning(
                f"ACEITAÇÃO BLOQUEADA: Saldo insuficiente para taxa. Prestador {provider_id}, "
                f"Convite {invite_id}, Necessário: R$ {InviteService.CONTESTATION_FEE:.2f}, "
                f"Disponível: R$ {provider_balance:.2f}"
            )
            # Lançar exceção personalizada
            # Requirements: 7.4, 8.3, 8.4
            # Não alterar estado do convite
            raise InsufficientBalanceError(
                user_id=provider_id,
                user_type='prestador',
                required_amount=InviteService.CONTESTATION_FEE,
                current_balance=provider_balance,
                purpose='aceitar o convite (taxa de contestação)'
            )
        
        try:
            # Marcar provider_accepted como True e registrar timestamp
            # Requirements: 1.2, 9.1, 9.2
            invite.provider_accepted = True
            invite.provider_accepted_at = datetime.utcnow()
            db.session.commit()
            
            # Log detalhado de aceitação
            # Requirements: 9.1, 9.2
            logger.info(
                f"ACEITAÇÃO PRESTADOR: Convite {invite_id} aceito pelo prestador {provider_id} "
                f"({provider.nome}). Timestamp: {invite.provider_accepted_at.isoformat()}, "
                f"Taxa de contestação: R$ {InviteService.CONTESTATION_FEE:.2f}, "
                f"Cliente ID: {invite.client_id}, "
                f"Status anterior: {invite.status}, "
                f"Cliente já aceitou: {invite.client_accepted}"
            )
            
            # Verificar se há aceitação mútua
            # Se ambas as partes aceitaram, criar PRÉ-ORDEM para negociação
            # Requirements: 1.1, 1.2, 1.3 (sistema-pre-ordem-negociacao)
            # Otimização Mobile: Convites simplificados, negociação na pré-ordem
            if invite.is_mutually_accepted:
                # Aceitação mútua detectada - criar PRÉ-ORDEM (não ordem direta)
                logger.info(
                    f"ACEITAÇÃO MÚTUA: Convite {invite_id} aceito por ambas as partes. "
                    f"Criando pré-ordem para negociação."
                )
                
                try:
                    from services.pre_order_service import PreOrderService
                    
                    # Criar pré-ordem a partir do convite
                    pre_order_result = PreOrderService.create_from_invite(invite_id)
                    
                    if pre_order_result.get('success'):
                        pre_order_id = pre_order_result.get('pre_order_id')
                        
                        logger.info(
                            f"PRÉ-ORDEM CRIADA (PRESTADOR): Convite {invite_id} convertido em pré-ordem {pre_order_id}. "
                            f"Cliente: {invite.client_id}, Prestador: {provider_id}"
                        )
                        
                        return {
                            'success': True,
                            'order_created': False,
                            'pre_order_created': True,
                            'pre_order_id': pre_order_id,
                            'message': f'Convite aceito! Pré-ordem #{pre_order_id} criada. Você pode negociar os termos antes de confirmar.',
                        }
                    else:
                        logger.error(
                            f"ERRO PRÉ-ORDEM: Falha ao criar pré-ordem do convite {invite_id}. "
                            f"Erro: {pre_order_result.get('error')}"
                        )
                        return {
                            'success': False,
                            'order_created': False,
                            'pre_order_created': False,
                            'error': pre_order_result.get('error', 'Erro ao criar pré-ordem')
                        }
                        
                except Exception as e:
                    db.session.rollback()
                    logger.error(
                        f"ERRO PRÉ-ORDEM: Exceção ao criar pré-ordem do convite {invite_id}. "
                        f"Erro: {str(e)}",
                        exc_info=True
                    )
                    return {
                        'success': False,
                        'order_created': False,
                        'pre_order_created': False,
                        'error': f'Erro ao criar pré-ordem: {str(e)}'
                    }
            else:
                # Ainda aguardando a outra parte aceitar
                pending_from = invite.pending_acceptance_from
                pending_name = 'prestador' if pending_from == 'prestador' else 'cliente'
                
                logger.info(
                    f"Convite {invite_id} aceito pelo prestador. "
                    f"Aguardando aceitação do {pending_name}."
                )
                
                return {
                    'success': True,
                    'order_created': False,
                    'pre_order_created': False,
                    'message': f'Convite aceito! Aguardando aceitação do {pending_name}.',
                    'pending_acceptance_from': pending_from
                }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(
                f"ERRO ACEITAÇÃO PRESTADOR: Falha ao aceitar convite {invite_id} "
                f"como prestador {provider_id}. Erro: {str(e)}",
                exc_info=True
            )
            raise e
    
    @staticmethod
    def accept_invite(token, provider_id, final_value=None, new_delivery_date=None):
        """
        Aceita um convite (simplificado - sem alteração de valor/data)
        
        NOTA: Conforme otimização mobile, a negociação de termos agora acontece
        na pré-ordem. Os parâmetros final_value e new_delivery_date são ignorados.
        
        Validações:
        - Prestador deve ter saldo suficiente para taxa de contestação
        - Convite deve estar válido (não expirado, status pendente)
        
        Fluxo simplificado:
        1. Aceita o convite com valor original
        2. Pré-ordem é criada automaticamente após aceitação mútua
        3. Negociação acontece na pré-ordem via PreOrderProposalService
        
        Requirements: Otimização Mobile - Requirement 1 (Simplificação da Interface de Convites)
        """
        # Avisar se parâmetros de alteração foram passados (deprecated)
        if final_value is not None or new_delivery_date is not None:
            logger.warning(
                f"Parâmetros final_value/new_delivery_date ignorados no accept_invite. "
                f"A negociação agora acontece na pré-ordem. Convite token: {token}"
            )
        
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se convite pode ser aceito usando o gerenciador de estados
        can_accept, reason = InviteStateManager.can_be_accepted(invite)
        if not can_accept:
            logger.warning(
                f"Tentativa bloqueada de aceitar convite {invite.id} pelo prestador {provider_id}. "
                f"Motivo: {reason}."
            )
            raise ValueError(reason)
        
        # Verificar se prestador existe
        provider = User.query.get(provider_id)
        if not provider:
            raise ValueError("Prestador não encontrado")
        
        # Verificar se o telefone do convite corresponde ao prestador
        if provider.phone != invite.invited_phone:
            raise ValueError("Este convite não foi enviado para seu telefone")
        
        # Validar saldo do prestador para taxa de contestação
        if not WalletService.has_sufficient_balance(provider_id, InviteService.CONTESTATION_FEE):
            provider_balance = WalletService.get_wallet_balance(provider_id)
            raise ValueError(
                f"Saldo insuficiente para aceitar convite. "
                f"Taxa de contestação: R$ {InviteService.CONTESTATION_FEE:.2f}. "
                f"Saldo atual: R$ {provider_balance:.2f}"
            )
        
        try:
            # Transicionar para estado ACEITO usando o gerenciador de estados
            # Valor original é mantido - negociação acontece na pré-ordem
            invite.transition_to(InviteState.ACEITO, provider_id, 
                               f"Convite aceito pelo prestador. Valor: R$ {float(invite.original_value)}")
            
            db.session.commit()
            
            return {
                'success': True,
                'invite_id': invite.id,
                'status': invite.status,
                'final_value': float(invite.original_value),
                'delivery_date': invite.delivery_date,
                'message': 'Convite aceito com sucesso. Negocie os termos na pré-ordem.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def reject_invite(invite, provider_id=None, reason=None):
        """
        Recusa um convite e notifica o cliente
        Pode ser chamado com ou sem provider_id (para rejeições anônimas)
        """
        # Verificar se convite pode ser recusado
        current_state = InviteStateManager.get_current_state(invite)
        can_reject, reject_reason = InviteStateManager.can_transition_to(invite, InviteState.RECUSADO)
        if not can_reject:
            raise ValueError(f"Convite não pode ser recusado: {reject_reason}")
        
        # Se provider_id foi fornecido, verificar autorização
        if provider_id:
            provider = User.query.get(provider_id)
            if not provider:
                raise ValueError("Prestador não encontrado")
            
            # Verificar se o telefone do convite corresponde ao prestador
            if provider.phone != invite.invited_phone:
                raise ValueError("Este convite não foi enviado para seu telefone")
        
        try:
            # Salvar motivo da rejeição se fornecido
            if reason:
                invite.rejection_reason = reason.strip()
            
            # Transicionar para estado RECUSADO usando o gerenciador de estados
            invite.transition_to(InviteState.RECUSADO, provider_id, 
                               f"Convite recusado: {reason or 'Sem motivo especificado'}")
            
            db.session.commit()
            
            # TODO: Implementar notificação automática para o cliente
            
            return {
                'success': True,
                'invite_id': invite.id,
                'status': invite.status,
                'message': 'Convite recusado. Cliente será notificado automaticamente.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_invite_terms(token, provider_id, new_value=None, new_delivery_date=None):
        """
        DEPRECATED: Este método foi removido conforme otimização mobile.
        
        A negociação de termos agora acontece na pré-ordem após aceitação mútua.
        Use PreOrderProposalService.create_proposal() para negociar termos.
        
        Fluxo simplificado:
        1. Prestador aceita convite
        2. Pré-ordem é criada automaticamente
        3. Negociação acontece na pré-ordem via PreOrderProposalService
        
        Requirements: Otimização Mobile - Requirement 1 (Simplificação da Interface de Convites)
        """
        raise NotImplementedError(
            "Método removido. A negociação de termos agora acontece na pré-ordem. "
            "Aceite o convite primeiro e depois use a tela de pré-ordem para negociar."
        )
    
    @staticmethod
    def convert_invite_to_order(invite_id):
        """
        Converte um convite aceito em ordem de serviço ativa
        
        Fluxo:
        1. Verificar se convite foi aceito
        2. Criar ordem de serviço usando valor efetivo e histórico de proposta
        3. Bloquear saldos em escrow (cliente: valor + taxa, prestador: taxa)
        4. Marcar convite como convertido
        """
        invite = Invite.query.get(invite_id)
        if not invite:
            raise ValueError("Convite não encontrado")
        
        if invite.status != 'aceito':
            raise ValueError("Apenas convites aceitos podem ser convertidos em ordens")
        
        # Encontrar prestador pelo telefone
        provider = User.query.filter_by(phone=invite.invited_phone).first()
        if not provider:
            raise ValueError("Prestador não encontrado no sistema")
        
        try:
            # Importar OrderService para usar o método específico
            from services.order_service import OrderService
            
            # Criar ordem de serviço com valor efetivo e histórico de proposta
            order_result = OrderService.create_order_from_invite(invite_id, provider.id)
            
            order = order_result['order']
            
            # Bloquear taxa de contestação do prestador
            WalletService.transfer_to_escrow(provider.id, InviteService.CONTESTATION_FEE, order.id)
            
            # Marcar convite como convertido usando o gerenciador de estados
            invite.order_id = order.id
            invite.transition_to(InviteState.CONVERTIDO, invite.client_id,
                               f"Convite convertido em ordem de serviço #{order.id}")
            
            db.session.commit()
            
            return {
                'success': True,
                'order_id': order.id,
                'invite_id': invite.id,
                'effective_value': order_result['effective_value'],
                'original_value': order_result['original_value'],
                'proposal_history': order_result.get('proposal_history'),
                'client_escrow': order_result['effective_value'],  # Já foi transferido pelo create_order_from_invite
                'provider_escrow': InviteService.CONTESTATION_FEE,
                'escrow_details': order_result['escrow_details'],
                'message': 'Convite convertido em ordem de serviço com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def expire_old_invites():
        """
        Expira convites antigos automaticamente
        
        Deve ser executado periodicamente (cron job)
        """
        expired_invites = Invite.query.filter(
            Invite.status == 'pendente',
            Invite.expires_at < datetime.utcnow()
        ).all()
        
        expired_count = 0
        
        try:
            for invite in expired_invites:
                # Usar o gerenciador de estados para expirar convites
                invite.transition_to(InviteState.EXPIRADO, None, "Convite expirado automaticamente")
                expired_count += 1
            
            db.session.commit()
            
            # TODO: Implementar notificações automáticas para clientes
            
            return {
                'success': True,
                'expired_count': expired_count,
                'message': f'{expired_count} convites expirados automaticamente'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def send_invite_notification(invite_id, notification_type='created'):
        """
        Envia notificações automáticas para convites
        
        Tipos de notificação:
        - created: Convite criado (para prestador)
        - accepted: Convite aceito (para cliente)
        - rejected: Convite recusado (para cliente)
        - terms_updated: Termos alterados (para cliente)
        - expired: Convite expirado (para ambos)
        """
        invite = Invite.query.get(invite_id)
        if not invite:
            raise ValueError("Convite não encontrado")
        
        # TODO: Implementar sistema de notificações
        # Por enquanto, apenas registrar a intenção
        
        notifications = {
            'created': f'Novo convite de serviço de {invite.client.nome}',
            'accepted': f'Convite aceito por {invite.invited_email}',
            'rejected': f'Convite recusado por {invite.invited_email}',
            'terms_updated': f'Termos do convite alterados por {invite.invited_email}',
            'expired': f'Convite expirado: {invite.service_title}'
        }
        
        message = notifications.get(notification_type, 'Notificação de convite')
        
        return {
            'success': True,
            'notification_type': notification_type,
            'message': message,
            'invite_id': invite_id
        }
    
    @staticmethod
    def get_invite_statistics(client_id=None):
        """
        Retorna estatísticas de convites
        
        Se client_id for fornecido, retorna estatísticas específicas do cliente
        Senão, retorna estatísticas gerais do sistema
        """
        if client_id:
            # Estatísticas específicas do cliente
            invites = Invite.query.filter_by(client_id=client_id).all()
        else:
            # Estatísticas gerais do sistema
            invites = Invite.query.all()
        
        total_invites = len(invites)
        
        if total_invites == 0:
            return {
                'total_invites': 0,
                'by_status': {},
                'acceptance_rate': 0,
                'average_value': 0,
                'total_value': 0
            }
        
        # Contar por status
        status_count = {}
        total_value = 0
        
        for invite in invites:
            status = invite.status
            status_count[status] = status_count.get(status, 0) + 1
            
            # Usar valor final se disponível, senão original
            value = float(invite.final_value) if invite.final_value else float(invite.original_value)
            total_value += value
        
        # Calcular taxa de aceitação
        accepted = status_count.get('aceito', 0) + status_count.get('convertido', 0)
        responded = accepted + status_count.get('recusado', 0)
        acceptance_rate = (accepted / responded * 100) if responded > 0 else 0
        
        return {
            'total_invites': total_invites,
            'by_status': status_count,
            'acceptance_rate': acceptance_rate,
            'average_value': total_value / total_invites,
            'total_value': total_value,
            'responded_invites': responded,
            'pending_invites': status_count.get('pendente', 0)
        }
    
    @staticmethod
    def create_counter_proposal(original_invite_id, proposed_value, justification, proposer_id=None):
        """
        DEPRECATED: Este método foi removido conforme otimização mobile.
        
        A negociação de termos agora acontece na pré-ordem após aceitação mútua.
        Use PreOrderProposalService.create_proposal() para negociar termos.
        
        Fluxo simplificado:
        1. Ambas as partes aceitam o convite
        2. Pré-ordem é criada automaticamente
        3. Negociação acontece na pré-ordem via PreOrderProposalService
        
        Requirements: Otimização Mobile - Requirement 1 (Simplificação da Interface de Convites)
        
        Args:
            original_invite_id: ID do convite original (não utilizado)
            proposed_value: Novo valor proposto (não utilizado)
            justification: Motivo da alteração (não utilizado)
            proposer_id: ID de quem está propondo (não utilizado)
        """
        raise NotImplementedError(
            "Método removido. A negociação de termos agora acontece na pré-ordem. "
            "Aceite o convite primeiro e depois use a tela de pré-ordem para negociar. "
            "Use PreOrderProposalService.create_proposal() para criar propostas."
        )
