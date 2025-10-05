#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Order
from services.wallet_service import WalletService
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class OrderService:
    """Serviço para gerenciar ordens de serviço"""

    @staticmethod
    def create_order(client_id, title, description, value):
        """Cria uma nova ordem de serviço"""
        if value <= 0:
            raise ValueError("O valor da ordem deve ser positivo")

        # Verificar se o cliente tem saldo suficiente para o escrow
        wallet = WalletService.get_wallet_balance(client_id)
        if wallet < value:
            raise ValueError("Saldo insuficiente para criar a ordem")

        try:
            order = Order(
                client_id=client_id,
                title=title,
                description=description,
                value=value,
                status='disponivel'
            )
            db.session.add(order)
            db.session.commit()

            # Transferir valor para escrow
            WalletService.transfer_to_escrow(client_id, value, order.id)

            return order
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def accept_order(provider_id, order_id):
        """Aceita uma ordem de serviço"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if order.status != 'disponivel':
            raise ValueError("Ordem não está mais disponível")

        try:
            order.provider_id = provider_id
            order.status = 'aceita'
            order.accepted_at = datetime.utcnow()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def complete_order(user_id, order_id):
        """Marca uma ordem como concluída (pelo prestador ou cliente)"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if user_id not in [order.client_id, order.provider_id]:
            raise ValueError("Usuário não autorizado a concluir esta ordem")

        if order.status not in ['aceita', 'em_andamento']:
            raise ValueError("Ordem não pode ser concluída neste estado")

        try:
            # Se o prestador marca como concluída, aguarda confirmação do cliente
            if user_id == order.provider_id:
                order.status = 'aguardando_confirmacao'
                db.session.commit()
                return "Aguardando confirmação do cliente"

            # Se o cliente confirma, a ordem é concluída e o pagamento liberado
            if user_id == order.client_id:
                order.status = 'concluida'
                order.completed_at = datetime.utcnow()
                db.session.commit()

                # Liberar pagamento do escrow
                WalletService.release_from_escrow(order.id)
                return "Ordem concluída e pagamento liberado"

        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    @staticmethod
    def cancel_order(user_id, order_id):
        """Cancela uma ordem de serviço"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")

        if user_id not in [order.client_id, order.provider_id]:
            raise ValueError("Usuário não autorizado a cancelar esta ordem")

        if order.status not in ['disponivel', 'aceita']:
            raise ValueError("Ordem não pode ser cancelada neste estado")

        try:
            order.status = 'cancelada'
            db.session.commit()

            # Se o valor já estava em escrow, reembolsar o cliente
            if order.status == 'aceita':
                WalletService.refund_from_escrow(order.id)

            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
