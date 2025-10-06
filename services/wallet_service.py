#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import db, User, Wallet, Transaction, Order
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

class WalletService:
    """Serviço para gerenciar carteiras e transações"""
    
    # ID do admin principal (será configurável no futuro)
    ADMIN_USER_ID = 0  # ID 0 reservado para o admin
    
    @staticmethod
    def create_wallet_for_user(user):
        """Cria uma carteira para um novo usuário"""
        if not user.wallet:
            wallet = Wallet(user_id=user.id)
            db.session.add(wallet)
            db.session.commit()
            return wallet
        return user.wallet
    
    @staticmethod
    def ensure_user_has_wallet(user_id):
        """Garante que um usuário tenha uma carteira, criando se necessário"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Usuário com ID {user_id} não encontrado")
        
        # Verifica se já tem carteira
        existing_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if existing_wallet:
            return existing_wallet
        
        # Cria nova carteira
        try:
            wallet = Wallet(
                user_id=user_id,
                balance=0.0,
                escrow_balance=0.0
            )
            db.session.add(wallet)
            db.session.commit()
            
            # Registra transação inicial
            initial_transaction = Transaction(
                user_id=user_id,
                type="criacao_carteira",
                amount=0.0,
                description="Carteira criada automaticamente"
            )
            db.session.add(initial_transaction)
            db.session.commit()
            
            return wallet
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def validate_all_users_have_wallets():
        """Valida que todos os usuários ativos tenham carteiras"""
        users_without_wallets = []
        users = User.query.filter_by(active=True).all()
        
        for user in users:
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if not wallet:
                users_without_wallets.append(user)
        
        return users_without_wallets
    
    @staticmethod
    def create_missing_wallets():
        """Cria carteiras para todos os usuários que não possuem"""
        users_without_wallets = WalletService.validate_all_users_have_wallets()
        created_count = 0
        
        for user in users_without_wallets:
            try:
                WalletService.ensure_user_has_wallet(user.id)
                created_count += 1
            except Exception as e:
                print(f"Erro ao criar carteira para usuário {user.email}: {e}")
        
        return created_count
    
    # ==============================================================================
    #  SISTEMA DE TRANSAÇÕES E RASTREABILIDADE
    # ==============================================================================
    
    @staticmethod
    def get_transaction_history(user_id, limit=50, transaction_type=None):
        """Retorna o histórico de transações de um usuário"""
        query = Transaction.query.filter_by(user_id=user_id)
        
        if transaction_type:
            query = query.filter_by(type=transaction_type)
        
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()
        
        return [{
            'id': t.id,
            'type': t.type,
            'amount': t.amount,
            'description': t.description,
            'created_at': t.created_at,
            'order_id': t.order_id,
            'related_user_id': t.related_user_id
        } for t in transactions]
    
    @staticmethod
    def get_transaction_by_id(transaction_id):
        """Retorna uma transação específica por ID"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError(f"Transação com ID {transaction_id} não encontrada")
        
        return {
            'id': transaction.id,
            'user_id': transaction.user_id,
            'type': transaction.type,
            'amount': transaction.amount,
            'description': transaction.description,
            'created_at': transaction.created_at,
            'order_id': transaction.order_id,
            'related_user_id': transaction.related_user_id
        }
    
    @staticmethod
    def get_transactions_by_order(order_id):
        """Retorna todas as transações relacionadas a uma ordem"""
        transactions = Transaction.query.filter_by(order_id=order_id).order_by(Transaction.created_at.asc()).all()
        
        return [{
            'id': t.id,
            'user_id': t.user_id,
            'type': t.type,
            'amount': t.amount,
            'description': t.description,
            'created_at': t.created_at,
            'related_user_id': t.related_user_id
        } for t in transactions]
    
    @staticmethod
    def get_user_balance_summary(user_id):
        """Retorna um resumo completo do saldo e transações do usuário"""
        wallet_info = WalletService.get_wallet_info(user_id)
        recent_transactions = WalletService.get_transaction_history(user_id, limit=10)
        
        # Calcular estatísticas
        all_transactions = Transaction.query.filter_by(user_id=user_id).all()
        total_credits = sum(t.amount for t in all_transactions if t.amount > 0)
        total_debits = sum(abs(t.amount) for t in all_transactions if t.amount < 0)
        transaction_count = len(all_transactions)
        
        return {
            'wallet': wallet_info,
            'recent_transactions': recent_transactions,
            'statistics': {
                'total_credits': total_credits,
                'total_debits': total_debits,
                'transaction_count': transaction_count,
                'net_flow': total_credits - total_debits
            }
        }
    
    @staticmethod
    def generate_transaction_id():
        """Gera um ID único para transação (baseado em timestamp)"""
        from datetime import datetime
        import uuid
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique_part = str(uuid.uuid4())[:8]
        return f"TXN-{timestamp}-{unique_part}"
    
    @staticmethod
    def validate_transaction_integrity(user_id):
        """Valida a integridade das transações de um usuário"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        # Calcular saldo total baseado em todas as transações (exceto escrow)
        transactions = Transaction.query.filter_by(user_id=user_id).all()
        
        # Separar transações por tipo
        balance_affecting = []
        escrow_affecting = []
        
        for t in transactions:
            if t.type in ['escrow_bloqueio', 'escrow_liberacao', 'escrow_reembolso']:
                escrow_affecting.append(t)
            else:
                balance_affecting.append(t)
        
        # Calcular saldo principal
        # Para escrow_bloqueio, o valor já foi debitado do saldo principal
        # então precisamos somar todas as transações normais E as de escrow_bloqueio
        calculated_balance = sum(t.amount for t in balance_affecting)
        
        # Adicionar o efeito das transações de escrow no saldo principal
        for t in escrow_affecting:
            if t.type == 'escrow_bloqueio':
                calculated_balance += t.amount  # t.amount já é negativo
            elif t.type == 'escrow_reembolso':
                calculated_balance += abs(t.amount)  # Reembolso adiciona de volta ao saldo
        
        # Para escrow, precisamos considerar que:
        # - escrow_bloqueio: remove do saldo principal (já contabilizado acima como negativo)
        #   e adiciona ao escrow
        # - escrow_liberacao: remove do escrow
        # - escrow_reembolso: remove do escrow e adiciona de volta ao saldo principal
        
        calculated_escrow = 0.0
        for t in escrow_affecting:
            if t.type == 'escrow_bloqueio':
                calculated_escrow += abs(t.amount)  # Adiciona ao escrow
            elif t.type in ['escrow_liberacao', 'escrow_reembolso']:
                calculated_escrow -= abs(t.amount)  # Remove do escrow
        
        # Verificar se os saldos batem
        balance_matches = abs(wallet.balance - calculated_balance) < 0.01
        escrow_matches = abs(wallet.escrow_balance - calculated_escrow) < 0.01
        
        return {
            'wallet_balance': wallet.balance,
            'calculated_balance': calculated_balance,
            'balance_matches': balance_matches,
            'wallet_escrow': wallet.escrow_balance,
            'calculated_escrow': calculated_escrow,
            'escrow_matches': escrow_matches,
            'is_valid': balance_matches and escrow_matches,
            'transactions_analyzed': len(transactions),
            'balance_transactions': len(balance_affecting),
            'escrow_transactions': len(escrow_affecting)
        }
    
    @staticmethod
    def get_system_transaction_summary():
        """Retorna um resumo de todas as transações do sistema"""
        from sqlalchemy import func
        
        # Estatísticas gerais
        total_transactions = db.session.query(func.count(Transaction.id)).scalar()
        total_volume = db.session.query(func.sum(func.abs(Transaction.amount))).scalar() or 0.0
        
        # Transações por tipo
        type_stats = db.session.query(
            Transaction.type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).group_by(Transaction.type).all()
        
        # Usuários com mais transações
        user_stats = db.session.query(
            Transaction.user_id,
            func.count(Transaction.id).label('transaction_count')
        ).group_by(Transaction.user_id).order_by(func.count(Transaction.id).desc()).limit(10).all()
        
        return {
            'total_transactions': total_transactions,
            'total_volume': total_volume,
            'type_statistics': [
                {
                    'type': stat.type,
                    'count': stat.count,
                    'total_amount': stat.total_amount
                } for stat in type_stats
            ],
            'top_users': [
                {
                    'user_id': stat.user_id,
                    'transaction_count': stat.transaction_count
                } for stat in user_stats
            ]
        }

    @staticmethod
    def get_wallet_balance(user_id):
        """Retorna o saldo da carteira de um usuário"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        return wallet.balance
    
    @staticmethod
    def get_wallet_info(user_id):
        """Retorna informações completas da carteira de um usuário"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        return {
            'balance': wallet.balance,
            'escrow_balance': wallet.escrow_balance,
            'total_balance': wallet.balance + wallet.escrow_balance,
            'updated_at': wallet.updated_at
        }
    
    @staticmethod
    def has_sufficient_balance(user_id, amount):
        """Verifica se o usuário tem saldo suficiente"""
        try:
            balance = WalletService.get_wallet_balance(user_id)
            return balance >= amount
        except ValueError:
            return False
    
    @staticmethod
    def credit_wallet(user_id, amount, description, transaction_type="credito", order_id=None, related_user_id=None):
        """Credita um valor na carteira de um usuário (operação genérica)"""
        if amount <= 0:
            raise ValueError("Valor do crédito deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        try:
            # Atualizar saldo
            wallet.balance += amount
            wallet.updated_at = datetime.utcnow()
            
            # Registrar transação
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                amount=amount,
                description=description,
                order_id=order_id,
                related_user_id=related_user_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'transaction_id': transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def debit_wallet(user_id, amount, description, transaction_type="debito", order_id=None, related_user_id=None, force=False):
        """Debita um valor da carteira de um usuário (operação genérica)"""
        if amount <= 0:
            raise ValueError("Valor do débito deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        # Verificar saldo suficiente (a menos que seja forçado)
        if not force and wallet.balance < amount:
            raise ValueError(f"Saldo insuficiente. Saldo atual: {wallet.balance}, valor solicitado: {amount}")
        
        try:
            # Atualizar saldo
            wallet.balance -= amount
            wallet.updated_at = datetime.utcnow()
            
            # Registrar transação (valor negativo para débito)
            transaction = Transaction(
                user_id=user_id,
                type=transaction_type,
                amount=-amount,
                description=description,
                order_id=order_id,
                related_user_id=related_user_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'transaction_id': transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    # ==============================================================================
    #  SISTEMA DE TOKENOMICS - ADMIN COMO FONTE DE TOKENS
    # ==============================================================================
    
    @staticmethod
    def ensure_admin_has_wallet():
        """Garante que o admin principal tenha uma carteira"""
        from models import AdminUser
        
        # Buscar admin principal
        admin = AdminUser.query.get(WalletService.ADMIN_USER_ID)
        if not admin:
            raise ValueError("Admin principal não encontrado")
        
        # Verificar se admin já tem carteira
        admin_wallet = Wallet.query.filter_by(user_id=WalletService.ADMIN_USER_ID).first()
        if admin_wallet:
            return admin_wallet
        
        # Criar carteira do admin com saldo inicial de tokens
        try:
            admin_wallet = Wallet(
                user_id=WalletService.ADMIN_USER_ID,
                balance=1000000.0,  # 1 milhão de tokens iniciais
                escrow_balance=0.0
            )
            db.session.add(admin_wallet)
            db.session.commit()
            
            # Registrar criação inicial de tokens
            initial_transaction = Transaction(
                user_id=WalletService.ADMIN_USER_ID,
                type="criacao_tokens",
                amount=1000000.0,
                description="Criação inicial de tokens do sistema"
            )
            db.session.add(initial_transaction)
            db.session.commit()
            
            return admin_wallet
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def admin_create_tokens(amount, description="Criação de tokens pelo admin"):
        """Permite ao admin criar novos tokens do zero"""
        if amount <= 0:
            raise ValueError("Quantidade de tokens deve ser positiva")
        
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        try:
            # Adicionar tokens à carteira do admin
            admin_wallet.balance += amount
            admin_wallet.updated_at = datetime.utcnow()
            
            # Registrar criação de tokens
            transaction = Transaction(
                user_id=WalletService.ADMIN_USER_ID,
                type="criacao_tokens",
                amount=amount,
                description=description
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'new_admin_balance': admin_wallet.balance,
                'tokens_created': amount,
                'transaction_id': transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def admin_sell_tokens_to_user(user_id, amount, description="Compra de tokens"):
        """Admin vende tokens para um usuário (tokens saem da carteira do admin)"""
        if amount <= 0:
            raise ValueError("Quantidade de tokens deve ser positiva")
        
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar se admin tem tokens suficientes
        if admin_wallet.balance < amount:
            raise ValueError(f"Admin não tem tokens suficientes. Saldo atual: {admin_wallet.balance}, solicitado: {amount}")
        
        # Garantir que usuário tem carteira
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            user_wallet = WalletService.ensure_user_has_wallet(user_id)
        
        try:
            # Debitar tokens do admin
            admin_wallet.balance -= amount
            admin_wallet.updated_at = datetime.utcnow()
            
            # Creditar tokens ao usuário
            user_wallet.balance += amount
            user_wallet.updated_at = datetime.utcnow()
            
            # Registrar transação do admin (saída)
            admin_transaction = Transaction(
                user_id=WalletService.ADMIN_USER_ID,
                type="venda_tokens",
                amount=-amount,
                description=f"Venda de tokens para usuário ID {user_id}",
                related_user_id=user_id
            )
            
            # Registrar transação do usuário (entrada)
            user_transaction = Transaction(
                user_id=user_id,
                type="compra_tokens",
                amount=amount,
                description=description,
                related_user_id=WalletService.ADMIN_USER_ID
            )
            
            db.session.add_all([admin_transaction, user_transaction])
            db.session.commit()
            
            return {
                'success': True,
                'admin_new_balance': admin_wallet.balance,
                'user_new_balance': user_wallet.balance,
                'tokens_transferred': amount,
                'admin_transaction_id': admin_transaction.id,
                'user_transaction_id': user_transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def user_sell_tokens_to_admin(user_id, amount, description="Saque de tokens"):
        """Usuário vende tokens de volta para o admin (saque)"""
        if amount <= 0:
            raise ValueError("Quantidade de tokens deve ser positiva")
        
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Verificar carteira do usuário
        user_wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not user_wallet:
            raise ValueError("Carteira do usuário não encontrada")
        
        # Verificar se usuário tem tokens suficientes
        if user_wallet.balance < amount:
            raise ValueError(f"Saldo insuficiente. Saldo atual: {user_wallet.balance}, solicitado: {amount}")
        
        try:
            # Debitar tokens do usuário
            user_wallet.balance -= amount
            user_wallet.updated_at = datetime.utcnow()
            
            # Creditar tokens de volta ao admin
            admin_wallet.balance += amount
            admin_wallet.updated_at = datetime.utcnow()
            
            # Registrar transação do usuário (saída)
            user_transaction = Transaction(
                user_id=user_id,
                type="saque_tokens",
                amount=-amount,
                description=description,
                related_user_id=WalletService.ADMIN_USER_ID
            )
            
            # Registrar transação do admin (entrada)
            admin_transaction = Transaction(
                user_id=WalletService.ADMIN_USER_ID,
                type="recompra_tokens",
                amount=amount,
                description=f"Recompra de tokens do usuário ID {user_id}",
                related_user_id=user_id
            )
            
            db.session.add_all([user_transaction, admin_transaction])
            db.session.commit()
            
            return {
                'success': True,
                'user_new_balance': user_wallet.balance,
                'admin_new_balance': admin_wallet.balance,
                'tokens_transferred': amount,
                'user_transaction_id': user_transaction.id,
                'admin_transaction_id': admin_transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_admin_wallet_info():
        """Retorna informações da carteira do admin"""
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        return {
            'balance': admin_wallet.balance,
            'escrow_balance': admin_wallet.escrow_balance,
            'total_balance': admin_wallet.balance + admin_wallet.escrow_balance,
            'updated_at': admin_wallet.updated_at
        }
    
    @staticmethod
    def get_system_token_summary():
        """Retorna resumo dos tokens no sistema"""
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Calcular tokens em circulação (todos os usuários normais, não admin)
        # Admin tem user_id = 1, mas é AdminUser, não User
        from models import User
        user_ids = [u.id for u in User.query.all()]
        user_wallets = Wallet.query.filter(Wallet.user_id.in_(user_ids)).all()
        tokens_in_circulation = sum(w.balance + w.escrow_balance for w in user_wallets)
        
        # Tokens criados pelo admin
        creation_transactions = Transaction.query.filter_by(
            user_id=WalletService.ADMIN_USER_ID,
            type="criacao_tokens"
        ).all()
        total_tokens_created = sum(t.amount for t in creation_transactions)
        
        return {
            'admin_balance': admin_wallet.balance,
            'tokens_in_circulation': tokens_in_circulation,
            'total_tokens_created': total_tokens_created,
            'total_tokens_in_system': admin_wallet.balance + tokens_in_circulation,
            'circulation_percentage': (tokens_in_circulation / total_tokens_created * 100) if total_tokens_created > 0 else 0
        }

    @staticmethod
    def deposit(user_id, amount, description):
        """Deposita um valor na carteira de um usuário (compra tokens do admin)"""
        return WalletService.admin_sell_tokens_to_user(user_id, amount, f"Depósito: {description}")

    @staticmethod
    def withdraw(user_id, amount, description):
        """Saca um valor da carteira de um usuário (vende tokens para o admin)"""
        return WalletService.user_sell_tokens_to_admin(user_id, amount, f"Saque: {description}")

    @staticmethod
    def transfer_to_escrow(user_id, amount, order_id):
        """Transfere um valor do saldo principal para o saldo em escrow"""
        if amount <= 0:
            raise ValueError("Valor deve ser positivo")
        
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        
        if wallet.balance < amount:
            raise ValueError(f"Saldo insuficiente para transferir para escrow. Saldo atual: {wallet.balance}, valor solicitado: {amount}")
        
        try:
            # Transferir do saldo principal para escrow
            wallet.balance -= amount
            wallet.escrow_balance += amount
            wallet.updated_at = datetime.utcnow()
            
            # Registrar transação de bloqueio
            transaction = Transaction(
                user_id=user_id,
                type="escrow_bloqueio",
                amount=-amount,
                description=f"Bloqueio para ordem #{order_id}",
                order_id=order_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'new_balance': wallet.balance,
                'new_escrow_balance': wallet.escrow_balance,
                'transaction_id': transaction.id
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_escrow_balance(user_id):
        """Retorna o saldo em escrow de um usuário"""
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise ValueError("Carteira não encontrada")
        return wallet.escrow_balance
    
    @staticmethod
    def has_sufficient_escrow(user_id, amount):
        """Verifica se o usuário tem saldo suficiente em escrow"""
        try:
            escrow_balance = WalletService.get_escrow_balance(user_id)
            return escrow_balance >= amount
        except ValueError:
            return False

    @staticmethod
    def release_from_escrow(order_id, system_fee_percent=0.05):
        """
        Libera o valor em escrow para o prestador e a taxa para o admin
        
        Fluxo conforme Planta Arquitetônica seção 7.5:
        1. Verificar se ordem existe e tem valor em escrow
        2. Calcular taxa do sistema (configurável, padrão 5%)
        3. Liberar escrow: tokens→prestador, taxa→admin
        4. Registrar todas as transações para auditoria
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if not order.provider_id:
            raise ValueError("Ordem não tem prestador associado")
        
        client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
        provider_wallet = Wallet.query.filter_by(user_id=order.provider_id).first()
        
        if not client_wallet or not provider_wallet:
            raise ValueError("Carteira não encontrada")
        
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Calcular valores
        system_fee = order.value * system_fee_percent
        provider_amount = order.value - system_fee
        
        if client_wallet.escrow_balance < order.value:
            raise ValueError(f"Saldo em escrow insuficiente. Necessário: {order.value}, disponível: {client_wallet.escrow_balance}")
        
        try:
            # 1. Liberar do escrow do cliente
            client_wallet.escrow_balance -= order.value
            client_wallet.updated_at = datetime.utcnow()
            
            # 2. Pagar o prestador (valor - taxa)
            provider_wallet.balance += provider_amount
            provider_wallet.updated_at = datetime.utcnow()
            
            # 3. Pagar a taxa do sistema para o admin
            admin_wallet.balance += system_fee
            admin_wallet.updated_at = datetime.utcnow()
            
            # Registrar transações para auditoria completa
            # 1. Liberação do escrow do cliente
            t1 = Transaction(
                user_id=order.client_id,
                type="escrow_liberacao",
                amount=-order.value,
                description=f"Liberação de escrow para ordem #{order_id}",
                order_id=order_id,
                related_user_id=order.provider_id
            )
            
            # 2. Pagamento ao prestador
            t2 = Transaction(
                user_id=order.provider_id,
                type="recebimento",
                amount=provider_amount,
                description=f"Pagamento pela ordem #{order_id} (valor: {order.value:.2f} - taxa: {system_fee:.2f})",
                order_id=order_id,
                related_user_id=order.client_id
            )
            
            # 3. Taxa do sistema para admin
            t3 = Transaction(
                user_id=WalletService.ADMIN_USER_ID,
                type="taxa_sistema",
                amount=system_fee,
                description=f"Taxa do sistema ({system_fee_percent*100:.1f}%) da ordem #{order_id}",
                order_id=order_id,
                related_user_id=order.provider_id
            )
            
            db.session.add_all([t1, t2, t3])
            db.session.commit()
            
            return {
                'success': True,
                'order_value': order.value,
                'provider_amount': provider_amount,
                'system_fee': system_fee,
                'system_fee_percent': system_fee_percent,
                'transactions': [t1.id, t2.id, t3.id],
                'client_new_escrow': client_wallet.escrow_balance,
                'provider_new_balance': provider_wallet.balance,
                'admin_new_balance': admin_wallet.balance
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao liberar escrow: {str(e)}")

    @staticmethod
    def refund_from_escrow(order_id):
        """
        Reembolsa o valor em escrow para o cliente em caso de cancelamento
        
        Fluxo:
        1. Verificar se ordem existe e tem valor em escrow
        2. Devolver tokens do escrow para o saldo principal do cliente
        3. Registrar transação de reembolso para auditoria
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
        if not client_wallet:
            raise ValueError("Carteira do cliente não encontrada")
        
        if client_wallet.escrow_balance < order.value:
            raise ValueError(f"Saldo em escrow insuficiente para reembolso. Necessário: {order.value}, disponível: {client_wallet.escrow_balance}")
        
        try:
            # Devolver tokens do escrow para o saldo principal
            client_wallet.escrow_balance -= order.value
            client_wallet.balance += order.value
            client_wallet.updated_at = datetime.utcnow()
            
            # Registrar transação de reembolso
            transaction = Transaction(
                user_id=order.client_id,
                type="escrow_reembolso",
                amount=order.value,
                description=f"Reembolso de escrow da ordem #{order_id} (cancelamento)",
                order_id=order_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'refunded_amount': order.value,
                'new_balance': client_wallet.balance,
                'new_escrow_balance': client_wallet.escrow_balance,
                'transaction_id': transaction.id
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao processar reembolso: {str(e)}")

    @staticmethod
    def resolve_dispute_custom_split(order_id, client_percentage, provider_percentage, system_fee_percentage=0.0):
        """
        Resolve disputa com divisão customizada dos valores
        
        Args:
            order_id: ID da ordem em disputa
            client_percentage: Percentual para o cliente (0.0 a 1.0)
            provider_percentage: Percentual para o prestador (0.0 a 1.0)
            system_fee_percentage: Percentual de taxa do sistema (0.0 a 1.0)
        """
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Ordem não encontrada")
        
        if not order.provider_id:
            raise ValueError("Ordem não tem prestador associado")
        
        # Validar percentuais
        total_percentage = client_percentage + provider_percentage + system_fee_percentage
        if abs(total_percentage - 1.0) > 0.001:  # Tolerância para float
            raise ValueError(f"Percentuais devem somar 100%. Total atual: {total_percentage*100:.1f}%")
        
        client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
        provider_wallet = Wallet.query.filter_by(user_id=order.provider_id).first()
        
        if not client_wallet or not provider_wallet:
            raise ValueError("Carteira não encontrada")
        
        if client_wallet.escrow_balance < order.value:
            raise ValueError(f"Saldo em escrow insuficiente. Necessário: {order.value}, disponível: {client_wallet.escrow_balance}")
        
        # Garantir que admin tem carteira
        admin_wallet = WalletService.ensure_admin_has_wallet()
        
        # Calcular valores
        client_amount = order.value * client_percentage
        provider_amount = order.value * provider_percentage
        system_fee = order.value * system_fee_percentage
        
        try:
            # 1. Liberar do escrow do cliente
            client_wallet.escrow_balance -= order.value
            client_wallet.updated_at = datetime.utcnow()
            
            # 2. Distribuir conforme percentuais
            if client_amount > 0:
                client_wallet.balance += client_amount
            
            if provider_amount > 0:
                provider_wallet.balance += provider_amount
                provider_wallet.updated_at = datetime.utcnow()
            
            if system_fee > 0:
                admin_wallet.balance += system_fee
                admin_wallet.updated_at = datetime.utcnow()
            
            # Registrar transações
            transactions = []
            
            # Liberação do escrow
            t1 = Transaction(
                user_id=order.client_id,
                type="escrow_liberacao",
                amount=-order.value,
                description=f"Liberação de escrow para resolução de disputa #{order_id}",
                order_id=order_id
            )
            transactions.append(t1)
            
            # Reembolso parcial ao cliente (se houver)
            if client_amount > 0:
                t2 = Transaction(
                    user_id=order.client_id,
                    type="resolucao_disputa",
                    amount=client_amount,
                    description=f"Resolução de disputa #{order_id} - {client_percentage*100:.1f}% para cliente",
                    order_id=order_id,
                    related_user_id=order.provider_id
                )
                transactions.append(t2)
            
            # Pagamento ao prestador (se houver)
            if provider_amount > 0:
                t3 = Transaction(
                    user_id=order.provider_id,
                    type="resolucao_disputa",
                    amount=provider_amount,
                    description=f"Resolução de disputa #{order_id} - {provider_percentage*100:.1f}% para prestador",
                    order_id=order_id,
                    related_user_id=order.client_id
                )
                transactions.append(t3)
            
            # Taxa do sistema (se houver)
            if system_fee > 0:
                t4 = Transaction(
                    user_id=WalletService.ADMIN_USER_ID,
                    type="taxa_sistema",
                    amount=system_fee,
                    description=f"Taxa de resolução de disputa #{order_id} ({system_fee_percentage*100:.1f}%)",
                    order_id=order_id
                )
                transactions.append(t4)
            
            db.session.add_all(transactions)
            db.session.commit()
            
            return {
                'success': True,
                'order_value': order.value,
                'client_amount': client_amount,
                'provider_amount': provider_amount,
                'system_fee': system_fee,
                'client_percentage': client_percentage * 100,
                'provider_percentage': provider_percentage * 100,
                'system_fee_percentage': system_fee_percentage * 100,
                'transaction_ids': [t.id for t in transactions]
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ValueError(f"Erro ao resolver disputa: {str(e)}")
    
    @staticmethod
    def transfer_tokens_between_users(from_user_id, to_user_id, amount, description):
        """Transfere tokens entre dois usuários (incluindo AdminUsers)"""
        if amount <= 0:
            raise ValueError("Valor deve ser positivo")
        
        if from_user_id == to_user_id:
            raise ValueError("Não é possível transferir para o mesmo usuário")
        
        # Verificar se remetente tem carteira e saldo suficiente
        from_wallet = Wallet.query.filter_by(user_id=from_user_id).first()
        if not from_wallet:
            # Tentar criar carteira se for usuário normal
            try:
                WalletService.ensure_user_has_wallet(from_user_id)
                from_wallet = Wallet.query.filter_by(user_id=from_user_id).first()
            except:
                raise ValueError(f"Carteira do remetente (ID {from_user_id}) não encontrada")
        
        if from_wallet.balance < amount:
            raise ValueError(f"Saldo insuficiente. Saldo atual: {from_wallet.balance}, valor solicitado: {amount}")
        
        # Verificar se destinatário tem carteira
        to_wallet = Wallet.query.filter_by(user_id=to_user_id).first()
        if not to_wallet:
            # Se for o admin principal (ID 0), garantir que tem carteira
            if to_user_id == WalletService.ADMIN_USER_ID:
                WalletService.ensure_admin_has_wallet()
                to_wallet = Wallet.query.filter_by(user_id=to_user_id).first()
            else:
                # Tentar criar carteira se for usuário normal
                try:
                    WalletService.ensure_user_has_wallet(to_user_id)
                    to_wallet = Wallet.query.filter_by(user_id=to_user_id).first()
                except:
                    raise ValueError(f"Carteira do destinatário (ID {to_user_id}) não encontrada")
        
        try:
            # Realizar transferência
            from_wallet.balance -= amount
            to_wallet.balance += amount
            
            # Registrar transação para o remetente (saída)
            from_transaction = Transaction(
                user_id=from_user_id,
                type="transferencia_enviada",
                amount=-amount,
                description=f"Transferência para usuário ID {to_user_id}: {description}",
                related_user_id=to_user_id
            )
            db.session.add(from_transaction)
            
            # Registrar transação para o destinatário (entrada)
            to_transaction = Transaction(
                user_id=to_user_id,
                type="transferencia_recebida",
                amount=amount,
                description=f"Transferência de usuário ID {from_user_id}: {description}",
                related_user_id=from_user_id
            )
            db.session.add(to_transaction)
            
            db.session.commit()
            
            return {
                'success': True,
                'from_transaction_id': from_transaction.id,
                'to_transaction_id': to_transaction.id,
                'from_new_balance': from_wallet.balance,
                'to_new_balance': to_wallet.balance
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e