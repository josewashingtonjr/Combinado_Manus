#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Invite, Order
from services.wallet_service import WalletService
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

class InviteService:
    """Serviço para gerenciar convites de serviço"""
    
    # Taxa de contestação padrão (configurável no futuro)
    CONTESTATION_FEE = 10.0  # R$ 10,00 por convite
    
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
        
        # Validações básicas
        if original_value <= 0:
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
        total_required = original_value + InviteService.CONTESTATION_FEE
        
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
            invite = Invite(
                client_id=client_id,
                invited_phone=invited_phone.strip(),
                service_title=service_title,
                service_description=service_description,
                service_category=service_category,
                original_value=original_value,
                delivery_date=delivery_date,
                expires_at=delivery_date  # Expira na data do serviço
            )
            
            db.session.add(invite)
            db.session.commit()
            
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
    def accept_invite(token, provider_id, final_value=None, new_delivery_date=None):
        """
        Aceita um convite com possibilidade de alteração de valor e data
        
        Validações:
        - Prestador deve ter saldo suficiente para taxa de contestação
        - Convite deve estar válido (não expirado, status pendente)
        - Se alterar valor/data, deve ser registrado
        """
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se convite pode ser aceito
        if not invite.can_be_accepted:
            if invite.is_expired:
                raise ValueError("Convite expirado")
            else:
                raise ValueError(f"Convite não pode ser aceito. Status atual: {invite.status}")
        
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
            # Atualizar convite
            invite.status = 'aceito'
            invite.responded_at = datetime.utcnow()
            
            # Se houve alteração de valor ou data
            if final_value is not None and final_value != float(invite.original_value):
                invite.final_value = final_value
            
            if new_delivery_date is not None and new_delivery_date != invite.delivery_date:
                invite.delivery_date = new_delivery_date
            
            db.session.commit()
            
            return {
                'success': True,
                'invite_id': invite.id,
                'status': invite.status,
                'final_value': float(invite.final_value) if invite.final_value else float(invite.original_value),
                'delivery_date': invite.delivery_date,
                'message': 'Convite aceito com sucesso'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def reject_invite(token, provider_id, reason=None):
        """
        Recusa um convite e notifica o cliente
        """
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se convite pode ser recusado
        if invite.status != 'pendente':
            raise ValueError(f"Convite não pode ser recusado. Status atual: {invite.status}")
        
        # Verificar se prestador existe
        provider = User.query.get(provider_id)
        if not provider:
            raise ValueError("Prestador não encontrado")
        
        # Verificar se o telefone do convite corresponde ao prestador
        if provider.phone != invite.invited_phone:
            raise ValueError("Este convite não foi enviado para seu telefone")
        
        try:
            # Atualizar convite
            invite.status = 'recusado'
            invite.responded_at = datetime.utcnow()
            
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
        Permite ao prestador propor alterações nos termos antes de aceitar
        """
        invite = InviteService.get_invite_by_token(token)
        
        # Verificar se convite pode ser alterado
        if not invite.can_be_accepted:
            raise ValueError("Convite não pode ser alterado")
        
        # Verificar se prestador existe e corresponde ao telefone
        provider = User.query.get(provider_id)
        if not provider or provider.phone != invite.invited_phone:
            raise ValueError("Prestador não autorizado para este convite")
        
        try:
            # Atualizar termos propostos
            if new_value is not None:
                invite.final_value = new_value
            
            if new_delivery_date is not None:
                invite.delivery_date = new_delivery_date
            
            db.session.commit()
            
            # TODO: Implementar notificação para o cliente sobre as alterações
            
            return {
                'success': True,
                'invite_id': invite.id,
                'final_value': float(invite.final_value) if invite.final_value else float(invite.original_value),
                'delivery_date': invite.delivery_date,
                'message': 'Termos atualizados. Cliente será notificado das alterações.'
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def convert_invite_to_order(invite_id):
        """
        Converte um convite aceito em ordem de serviço ativa
        
        Fluxo:
        1. Verificar se convite foi aceito
        2. Criar ordem de serviço
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
        
        # Valor final (pode ter sido alterado pelo prestador)
        final_value = float(invite.final_value) if invite.final_value else float(invite.original_value)
        
        try:
            # Criar ordem de serviço
            order = Order(
                client_id=invite.client_id,
                provider_id=provider.id,
                title=invite.service_title,
                description=invite.service_description,
                value=final_value,
                status='aceita',
                accepted_at=datetime.utcnow(),
                invite_id=invite.id
            )
            
            db.session.add(order)
            db.session.flush()  # Para obter o ID da ordem
            
            # Bloquear saldo do cliente em escrow (valor do serviço + taxa)
            client_escrow_amount = final_value + InviteService.CONTESTATION_FEE
            WalletService.transfer_to_escrow(invite.client_id, client_escrow_amount, order.id)
            
            # Bloquear taxa de contestação do prestador
            WalletService.transfer_to_escrow(provider.id, InviteService.CONTESTATION_FEE, order.id)
            
            # Marcar convite como convertido
            invite.status = 'convertido'
            invite.order_id = order.id
            
            db.session.commit()
            
            return {
                'success': True,
                'order_id': order.id,
                'invite_id': invite.id,
                'final_value': final_value,
                'client_escrow': client_escrow_amount,
                'provider_escrow': InviteService.CONTESTATION_FEE,
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
                invite.status = 'expirado'
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