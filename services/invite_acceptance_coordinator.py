#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
InviteAcceptanceCoordinator - Coordena o processo de aceitação mútua de convites

Este serviço implementa o fluxo de aceitação mútua onde:
1. Cliente e prestador devem aceitar o convite independentemente
2. Quando ambos aceitam, uma ordem é criada automaticamente
3. Valores são bloqueados em escrow de forma atômica
4. Validações de saldo são feitas antes da criação da ordem

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.2, 7.5, 8.1, 8.2, 8.3, 8.4
"""

from models import db, Invite, Order, User
from services.wallet_service import WalletService
from services.order_service import OrderService
from services.notification_service import NotificationService
from services.exceptions import (
    InsufficientBalanceError,
    OrderCreationError,
    EscrowBlockError,
    InviteValidationError
)
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class InviteAcceptanceCoordinator:
    """Coordenador para aceitação mútua de convites e criação automática de ordens"""
    
    # Taxa de contestação padrão (deve ser sincronizada com InviteService)
    CONTESTATION_FEE = Decimal('10.00')
    
    @staticmethod
    def process_acceptance(invite_id, accepting_user_id, acceptance_type):
        """
        Processa aceitação de convite e verifica se ambas as partes aceitaram
        
        Args:
            invite_id (int): ID do convite
            accepting_user_id (int): ID do usuário aceitando
            acceptance_type (str): 'client' ou 'provider'
            
        Returns:
            dict: {
                'success': bool,
                'order_created': bool,
                'order_id': int (se ordem foi criada),
                'message': str,
                'pending_acceptance_from': str (se ainda aguardando)
            }
            
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        try:
            invite = Invite.query.get(invite_id)
            if not invite:
                return {
                    'success': False,
                    'order_created': False,
                    'error': 'Convite não encontrado'
                }
            
            # Verificar se há aceitação mútua
            is_mutually_accepted, message = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            
            if is_mutually_accepted:
                # Ambas as partes aceitaram - criar ordem automaticamente
                logger.info(
                    f"Aceitação mútua detectada para convite {invite_id}. "
                    f"Usuário {accepting_user_id} ({acceptance_type}) completou a aceitação."
                )
                
                try:
                    order_result = InviteAcceptanceCoordinator.create_order_from_mutual_acceptance(invite)
                    
                    return {
                        'success': True,
                        'order_created': True,
                        'order_id': order_result['order_id'],
                        'message': f'Convite aceito! Ordem #{order_result["order_id"]} criada automaticamente.',
                        'order_details': order_result
                    }
                    
                except Exception as e:
                    # Log detalhado de erro na criação da ordem
                    # Requirements: 7.3, 7.4
                    logger.error(
                        f"ERRO CRIAÇÃO ORDEM: Falha ao criar ordem a partir de convite {invite_id}. "
                        f"Usuário aceitante: {accepting_user_id} ({acceptance_type}), "
                        f"Cliente: {invite.client_id}, "
                        f"Prestador: {invite.invited_phone}, "
                        f"Valor: R$ {invite.current_value:.2f}, "
                        f"Tipo erro: {type(e).__name__}, "
                        f"Mensagem: {str(e)}",
                        exc_info=True
                    )
                    return {
                        'success': False,
                        'order_created': False,
                        'error': f'Erro ao criar ordem: {str(e)}'
                    }
            else:
                # Ainda aguardando a outra parte aceitar
                pending_from = invite.pending_acceptance_from
                pending_name = 'prestador' if pending_from == 'prestador' else 'cliente'
                
                logger.info(
                    f"Convite {invite_id} aceito por {acceptance_type}. "
                    f"Aguardando aceitação do {pending_name}."
                )
                
                return {
                    'success': True,
                    'order_created': False,
                    'message': f'Convite aceito! Aguardando aceitação do {pending_name}.',
                    'pending_acceptance_from': pending_from
                }
                
        except Exception as e:
            # Log detalhado de erro no processamento
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO PROCESSAMENTO: Falha ao processar aceitação do convite {invite_id}. "
                f"Usuário: {accepting_user_id}, Tipo: {acceptance_type}, "
                f"Tipo erro: {type(e).__name__}, "
                f"Mensagem: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'order_created': False,
                'error': f'Erro ao processar aceitação: {str(e)}'
            }
    
    @staticmethod
    def check_mutual_acceptance(invite):
        """
        Verifica se ambas as partes aceitaram o convite
        
        Args:
            invite (Invite): Objeto do convite
            
        Returns:
            tuple: (bool, str) - (aceito_mutuamente, mensagem)
            
        Requirements: 1.1, 1.2
        """
        if not invite:
            return False, "Convite não encontrado"
        
        # Usar a propriedade do modelo que já implementa essa lógica
        if invite.is_mutually_accepted:
            return True, "Ambas as partes aceitaram o convite"
        
        # Identificar quem ainda precisa aceitar
        pending_from = invite.pending_acceptance_from
        if pending_from == 'cliente':
            return False, "Aguardando aceitação do cliente"
        elif pending_from == 'prestador':
            return False, "Aguardando aceitação do prestador"
        else:
            return False, "Status de aceitação desconhecido"
    
    @staticmethod
    def create_order_from_mutual_acceptance(invite):
        """
        Cria ordem quando há aceitação mútua
        
        Fluxo:
        1. Valida saldos de ambas as partes
        2. Cria ordem de serviço com status 'aceita'
        3. Bloqueia valores em escrow atomicamente
        4. Atualiza status do convite para 'convertido'
        5. Envia notificações
        
        Args:
            invite (Invite): Objeto do convite com aceitação mútua
            
        Returns:
            dict: Resultado da criação da ordem
            
        Raises:
            ValueError: Se validações falharem
            
        Requirements: 1.3, 1.4, 2.1, 2.2, 2.5, 7.1, 7.2, 7.5
        """
        if not invite.is_mutually_accepted:
            raise ValueError("Convite não foi aceito por ambas as partes")
        
        # Encontrar prestador pelo telefone
        provider = User.query.filter_by(phone=invite.invited_phone).first()
        if not provider:
            raise ValueError("Prestador não encontrado no sistema")
        
        # Obter valor efetivo do convite
        effective_value = invite.current_value
        
        # Validar saldos ANTES de iniciar a transação
        # Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4
        validation_result = InviteAcceptanceCoordinator._validate_balances_for_order(
            invite.client_id,
            provider.id,
            effective_value
        )
        
        if not validation_result['valid']:
            # Obter exceção de saldo insuficiente
            # Requirements: 7.4, 8.3, 8.4
            error_obj = validation_result.get('error_obj')
            error_type = validation_result.get('error')
            
            # Log detalhado de erro de saldo
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO VALIDAÇÃO SALDO: Falha ao validar saldos para criação de ordem. "
                f"Convite: {invite.id}, Cliente: {invite.client_id}, Prestador: {provider.id}, "
                f"Valor serviço: R$ {effective_value:.2f}, "
                f"Taxa contestação: R$ {InviteAcceptanceCoordinator.CONTESTATION_FEE:.2f}, "
                f"Saldo cliente: R$ {validation_result.get('client_balance', 0):.2f}, "
                f"Saldo prestador: R$ {validation_result.get('provider_balance', 0):.2f}, "
                f"Tipo erro: {error_type}, "
                f"Detalhes: {error_obj.to_dict() if error_obj else 'N/A'}"
            )
            
            # Enviar notificação de saldo insuficiente
            # Requirements: 6.5, 8.3, 8.4
            # Determinar qual usuário tem saldo insuficiente
            if error_type == 'cliente':
                NotificationService.notify_insufficient_balance(
                    user_id=invite.client_id,
                    user_type='cliente',
                    required_amount=validation_result.get('client_required', effective_value),
                    current_balance=validation_result.get('client_balance', Decimal('0')),
                    invite_id=invite.id
                )
                logger.info(
                    f"NOTIFICAÇÃO SALDO: Notificação de saldo insuficiente enviada ao cliente {invite.client_id}"
                )
            elif error_type == 'prestador':
                NotificationService.notify_insufficient_balance(
                    user_id=provider.id,
                    user_type='prestador',
                    required_amount=validation_result.get('provider_required', InviteAcceptanceCoordinator.CONTESTATION_FEE),
                    current_balance=validation_result.get('provider_balance', Decimal('0')),
                    invite_id=invite.id
                )
                logger.info(
                    f"NOTIFICAÇÃO SALDO: Notificação de saldo insuficiente enviada ao prestador {provider.id}"
                )
            
            # Lançar exceção personalizada
            # Requirements: 7.4, 8.3, 8.4
            # Não alterar estado do convite - ele permanece aceito para retry
            raise error_obj if error_obj else InsufficientBalanceError(
                user_id=invite.client_id if error_type == 'cliente' else provider.id,
                user_type=error_type,
                required_amount=validation_result.get(f'{error_type}_required', Decimal('0')),
                current_balance=validation_result.get(f'{error_type}_balance', Decimal('0')),
                purpose='criar a ordem de serviço'
            )
        
        # Iniciar transação atômica para criação da ordem
        # Requirements: 7.1, 7.2, 7.5
        order = None
        order_created = False
        
        try:
            # Usar nested transaction para garantir rollback completo em caso de erro
            # Requirements: 7.1, 7.2
            db.session.begin_nested()
            
            # Atualizar status do convite para 'aceito' antes de criar a ordem
            # O OrderService.create_order_from_invite espera que o status seja 'aceito'
            if invite.status == 'pendente':
                invite.status = 'aceito'
                invite.responded_at = datetime.utcnow()
                db.session.flush()
            
            # 1. Criar ordem de serviço usando OrderService
            # Isso já bloqueia o valor do serviço no escrow do cliente
            # Requirements: 1.3, 2.1, 2.5
            try:
                order_result = OrderService.create_order_from_invite(invite.id, provider.id)
                
                if not order_result['success']:
                    # Lançar exceção personalizada de criação de ordem
                    # Requirements: 7.1, 7.2, 7.3, 7.4
                    raise OrderCreationError(
                        invite_id=invite.id,
                        reason=order_result.get('error', 'Erro desconhecido ao criar ordem')
                    )
                
                order = order_result['order']
                order_created = True
                
                logger.info(
                    f"ORDEM CRIADA: Ordem #{order.id} criada com sucesso. "
                    f"Convite: {invite.id}, Cliente: {invite.client_id}, Prestador: {provider.id}"
                )
                
            except OrderCreationError:
                # Re-lançar exceção personalizada
                raise
            except Exception as e:
                # Converter exceção genérica em OrderCreationError
                # Requirements: 7.1, 7.2, 7.3, 7.4
                logger.error(
                    f"ERRO CRIAÇÃO ORDEM: Exceção ao criar ordem. "
                    f"Convite: {invite.id}, Tipo: {type(e).__name__}, Erro: {str(e)}",
                    exc_info=True
                )
                raise OrderCreationError(
                    invite_id=invite.id,
                    reason=f"Falha técnica ao criar ordem: {str(e)}",
                    original_exception=e
                )
            
            # 2. Bloquear taxa de contestação no escrow do prestador
            # Requirements: 1.4, 2.2, 7.2, 7.5
            try:
                escrow_result = WalletService.transfer_to_escrow(
                    provider.id,
                    InviteAcceptanceCoordinator.CONTESTATION_FEE,
                    order.id
                )
                logger.info(
                    f"TAXA BLOQUEADA: Taxa de contestação bloqueada para prestador {provider.id} "
                    f"na ordem {order.id}: R$ {InviteAcceptanceCoordinator.CONTESTATION_FEE:.2f}, "
                    f"Transaction ID: {escrow_result.get('transaction_id', 'N/A')}"
                )
            except Exception as e:
                # Log detalhado de erro no bloqueio
                # Requirements: 7.2, 7.3, 7.4, 7.5
                logger.error(
                    f"ERRO BLOQUEIO TAXA: Falha ao bloquear taxa de contestação. "
                    f"Prestador: {provider.id}, Ordem: {order.id}, "
                    f"Taxa: R$ {InviteAcceptanceCoordinator.CONTESTATION_FEE:.2f}, "
                    f"Convite: {invite.id}, Erro: {str(e)}",
                    exc_info=True
                )
                # Lançar exceção personalizada de bloqueio de escrow
                # Requirements: 7.2, 7.5
                raise EscrowBlockError(
                    order_id=order.id,
                    user_id=provider.id,
                    amount=InviteAcceptanceCoordinator.CONTESTATION_FEE,
                    reason=f"Falha ao bloquear taxa de contestação: {str(e)}"
                )
            
            # 3. Atualizar status do convite para 'convertido'
            # Requirements: 1.5
            invite.status = 'convertido'
            invite.order_id = order.id
            invite.responded_at = datetime.utcnow()
            
            # Commit da transação nested
            # Requirements: 7.1, 7.2
            db.session.commit()
            
            # Log detalhado de criação de ordem
            # Requirements: 9.1, 9.2, 9.4
            logger.info(
                f"ORDEM CRIADA: Ordem #{order.id} criada automaticamente a partir do convite {invite.id}. "
                f"Cliente ID: {invite.client_id}, "
                f"Prestador ID: {provider.id}, "
                f"Valor do serviço: R$ {effective_value:.2f}, "
                f"Escrow cliente: R$ {effective_value:.2f}, "
                f"Escrow prestador (taxa): R$ {InviteAcceptanceCoordinator.CONTESTATION_FEE:.2f}, "
                f"Status: aceita, "
                f"Timestamp: {datetime.utcnow().isoformat()}, "
                f"Convite aceito por cliente em: {invite.client_accepted_at.isoformat()}, "
                f"Convite aceito por prestador em: {invite.provider_accepted_at.isoformat()}"
            )
            
            # 4. Enviar notificações (fora da transação de banco)
            # Requirements: 6.1, 6.2
            try:
                InviteAcceptanceCoordinator._send_order_created_notifications(
                    order.id,
                    invite.client_id,
                    provider.id
                )
                logger.info(
                    f"NOTIFICAÇÕES ENVIADAS: Ordem #{order.id} - "
                    f"Notificações enviadas para cliente {invite.client_id} e prestador {provider.id}"
                )
            except Exception as e:
                # Não falhar a operação se notificação falhar
                logger.error(
                    f"ERRO NOTIFICAÇÕES: Falha ao enviar notificações para ordem {order.id}. "
                    f"Erro: {str(e)}",
                    exc_info=True
                )
            
            # 5. Notificar sistema de tempo real para atualizar dashboards
            # Requirements: 10.1, 10.2
            try:
                from services.realtime_service import RealtimeService
                RealtimeService.notify_order_created(order.id)
                logger.info(
                    f"TEMPO REAL: Cache invalidado para ordem #{order.id} - "
                    f"Dashboards serão atualizadas automaticamente"
                )
            except Exception as e:
                # Não falhar a operação se notificação de tempo real falhar
                logger.error(
                    f"ERRO TEMPO REAL: Falha ao notificar sistema de tempo real para ordem {order.id}. "
                    f"Erro: {str(e)}",
                    exc_info=True
                )
            
            return {
                'success': True,
                'order_id': order.id,
                'order': order,
                'effective_value': float(effective_value),
                'client_escrow': float(effective_value),
                'provider_escrow': float(InviteAcceptanceCoordinator.CONTESTATION_FEE),
                'invite_id': invite.id,
                'message': f'Ordem #{order.id} criada com sucesso!'
            }
            
        except InsufficientBalanceError:
            # Re-lançar exceção de saldo insuficiente sem modificar
            # Requirements: 7.4, 8.3, 8.4
            # Convite permanece aceito para retry
            raise
            
        except OrderCreationError as e:
            # Rollback completo da transação
            # Requirements: 7.1, 7.2, 7.3, 7.4
            db.session.rollback()
            
            # Reverter status do convite se necessário
            # Requirements: 7.1
            if invite.status == 'convertido':
                invite.status = 'aceito'
                invite.order_id = None
                db.session.commit()
                logger.info(
                    f"ROLLBACK CONVITE: Status do convite {invite.id} revertido para 'aceito' "
                    f"após falha na criação da ordem"
                )
            
            # Log detalhado de erro
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO CRIAÇÃO ORDEM: {e.to_dict()}",
                exc_info=True
            )
            
            # Re-lançar exceção para tratamento nas rotas
            raise
            
        except EscrowBlockError as e:
            # Rollback completo da transação
            # Requirements: 7.2, 7.5
            db.session.rollback()
            
            # Garantir que nenhum valor fica inconsistente
            # Requirements: 7.5
            # A ordem foi criada mas o bloqueio falhou
            # Precisamos cancelar a ordem e reverter o convite
            if order_created and order:
                logger.warning(
                    f"ROLLBACK ORDEM: Ordem {order.id} será cancelada devido a falha no bloqueio de escrow"
                )
                # A ordem será removida pelo rollback do banco
            
            # Manter convite como aceito para retry
            # Requirements: 7.2
            if invite.status == 'convertido':
                invite.status = 'aceito'
                invite.order_id = None
                db.session.commit()
                logger.info(
                    f"ROLLBACK CONVITE: Status do convite {invite.id} mantido como 'aceito' "
                    f"para permitir retry após falha no bloqueio de escrow"
                )
            
            # Log detalhado de erro
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO BLOQUEIO ESCROW: {e.to_dict()}",
                exc_info=True
            )
            
            # Notificar administrador se erro persistir
            # Requirements: 7.2
            # TODO: Implementar notificação para administrador
            
            # Re-lançar exceção para tratamento nas rotas
            raise
            
        except SQLAlchemyError as e:
            # Rollback automático da nested transaction
            # Requirements: 7.1, 7.2
            db.session.rollback()
            
            # Reverter status do convite
            # Requirements: 7.1
            if invite.status == 'convertido':
                try:
                    invite.status = 'aceito'
                    invite.order_id = None
                    db.session.commit()
                    logger.info(
                        f"ROLLBACK CONVITE: Status do convite {invite.id} revertido após erro de banco"
                    )
                except Exception as rollback_error:
                    logger.error(
                        f"ERRO ROLLBACK: Falha ao reverter status do convite {invite.id}: {str(rollback_error)}"
                    )
            
            # Log detalhado de erro de banco de dados
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO BANCO DE DADOS: Falha ao criar ordem do convite {invite.id}. "
                f"Cliente: {invite.client_id}, Prestador: {provider.id}, "
                f"Valor: R$ {effective_value:.2f}, "
                f"Tipo erro: SQLAlchemyError, "
                f"Detalhes: {str(e)}",
                exc_info=True
            )
            
            # Converter em OrderCreationError para mensagem consistente
            # Requirements: 7.4
            raise OrderCreationError(
                invite_id=invite.id,
                reason=f"Erro de banco de dados: {str(e)}",
                original_exception=e
            )
            
        except Exception as e:
            # Rollback em caso de qualquer outro erro
            # Requirements: 7.1, 7.2
            db.session.rollback()
            
            # Reverter status do convite
            # Requirements: 7.1
            if invite.status == 'convertido':
                try:
                    invite.status = 'aceito'
                    invite.order_id = None
                    db.session.commit()
                    logger.info(
                        f"ROLLBACK CONVITE: Status do convite {invite.id} revertido após erro inesperado"
                    )
                except Exception as rollback_error:
                    logger.error(
                        f"ERRO ROLLBACK: Falha ao reverter status do convite {invite.id}: {str(rollback_error)}"
                    )
            
            # Log detalhado de erro genérico
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO CRIAÇÃO ORDEM: Falha inesperada ao criar ordem do convite {invite.id}. "
                f"Cliente: {invite.client_id}, Prestador: {provider.id}, "
                f"Valor: R$ {effective_value:.2f}, "
                f"Tipo erro: {type(e).__name__}, "
                f"Detalhes: {str(e)}",
                exc_info=True
            )
            
            # Converter em OrderCreationError para mensagem consistente
            # Requirements: 7.4
            raise OrderCreationError(
                invite_id=invite.id,
                reason=f"Erro inesperado: {str(e)}",
                original_exception=e
            )
    
    @staticmethod
    def _validate_balances_for_order(client_id, provider_id, service_value):
        """
        Valida saldos antes da criação da ordem
        
        Args:
            client_id (int): ID do cliente
            provider_id (int): ID do prestador
            service_value (Decimal): Valor do serviço
            
        Returns:
            dict: {
                'valid': bool,
                'error': str (se não válido),
                'client_balance': Decimal,
                'provider_balance': Decimal
            }
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4
        """
        try:
            # Converter para Decimal se necessário
            service_value = Decimal(str(service_value))
            
            # Obter saldos
            client_balance = WalletService.get_wallet_balance(client_id)
            provider_balance = WalletService.get_wallet_balance(provider_id)
            
            # Calcular valores necessários
            # Cliente precisa: valor do serviço (já será bloqueado pelo OrderService)
            # Prestador precisa: taxa de contestação
            client_required = service_value
            provider_required = InviteAcceptanceCoordinator.CONTESTATION_FEE
            
            # Validar saldo do cliente
            # Requirements: 2.1, 2.3, 8.1, 8.3
            if client_balance < client_required:
                return {
                    'valid': False,
                    'error': 'cliente',
                    'error_obj': InsufficientBalanceError(
                        user_id=client_id,
                        user_type='cliente',
                        required_amount=client_required,
                        current_balance=client_balance,
                        purpose='aceitar o convite (valor do serviço)'
                    ),
                    'client_balance': client_balance,
                    'provider_balance': provider_balance,
                    'client_required': client_required,
                    'provider_required': provider_required
                }
            
            # Validar saldo do prestador
            # Requirements: 2.2, 2.4, 8.2, 8.4
            if provider_balance < provider_required:
                return {
                    'valid': False,
                    'error': 'prestador',
                    'error_obj': InsufficientBalanceError(
                        user_id=provider_id,
                        user_type='prestador',
                        required_amount=provider_required,
                        current_balance=provider_balance,
                        purpose='aceitar o convite (taxa de contestação)'
                    ),
                    'client_balance': client_balance,
                    'provider_balance': provider_balance,
                    'client_required': client_required,
                    'provider_required': provider_required
                }
            
            # Ambos os saldos são suficientes
            return {
                'valid': True,
                'client_balance': client_balance,
                'provider_balance': provider_balance,
                'client_required': client_required,
                'provider_required': provider_required
            }
            
        except Exception as e:
            # Log detalhado de erro na validação de saldos
            # Requirements: 7.3, 7.4
            logger.error(
                f"ERRO VALIDAÇÃO SALDOS: Falha ao validar saldos para ordem. "
                f"Cliente: {client_id}, Prestador: {provider_id}, "
                f"Valor serviço: R$ {service_value:.2f}, "
                f"Tipo erro: {type(e).__name__}, "
                f"Mensagem: {str(e)}",
                exc_info=True
            )
            return {
                'valid': False,
                'error': f"Erro ao validar saldos: {str(e)}"
            }
    
    @staticmethod
    def _send_order_created_notifications(order_id, client_id, provider_id):
        """
        Envia notificações sobre criação da ordem
        
        Usa NotificationService.notify_order_created para enviar notificações
        ao cliente e ao prestador com detalhes da ordem criada.
        
        Args:
            order_id (int): ID da ordem criada
            client_id (int): ID do cliente
            provider_id (int): ID do prestador
            
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        try:
            # Buscar ordem para obter detalhes
            order = Order.query.get(order_id)
            if not order:
                logger.warning(f"Ordem {order_id} não encontrada para enviar notificações")
                return
            
            # Buscar nomes dos usuários
            client = User.query.get(client_id)
            provider = User.query.get(provider_id)
            
            client_name = client.nome if client else "Cliente"
            provider_name = provider.nome if provider else "Prestador"
            
            # Usar o método notify_order_created do NotificationService
            # Requirements: 6.1, 6.2, 6.3, 6.4
            notification_result = NotificationService.notify_order_created(
                order=order,
                client_name=client_name,
                provider_name=provider_name
            )
            
            if notification_result.get('success'):
                logger.info(
                    f"Notificações de ordem criada enviadas com sucesso - "
                    f"Ordem: {order_id}, Cliente: {client_id}, Prestador: {provider_id}"
                )
            else:
                logger.error(
                    f"Falha ao enviar notificações de ordem criada - "
                    f"Ordem: {order_id}, Erro: {notification_result.get('error')}"
                )
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificações da ordem {order_id}: {str(e)}")
