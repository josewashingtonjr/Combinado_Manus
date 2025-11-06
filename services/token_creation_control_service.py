#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Controle de Criação de Tokens
Implementa verificação de limites diários e mensais para criação de tokens por administrador
"""

from models import TokenCreationLimit, AdminUser, Transaction, db
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenCreationControlService:
    """Serviço para controle de limites de criação de tokens"""
    
    # Limites padrão
    DEFAULT_DAILY_LIMIT = Decimal('10000.00')
    DEFAULT_MONTHLY_LIMIT = Decimal('100000.00')
    
    @staticmethod
    def get_or_create_limits(admin_id):
        """Obtém ou cria limites para um administrador"""
        try:
            # Verificar se o admin existe
            admin = AdminUser.query.get(admin_id)
            if not admin:
                raise ValueError(f"Administrador com ID {admin_id} não encontrado")
            
            if admin.is_deleted:
                raise ValueError(f"Administrador com ID {admin_id} foi deletado")
            
            # Buscar limites existentes
            limits = TokenCreationLimit.query.filter_by(admin_id=admin_id).first()
            
            if not limits:
                # Criar limites padrão
                limits = TokenCreationLimit(
                    admin_id=admin_id,
                    daily_limit=TokenCreationControlService.DEFAULT_DAILY_LIMIT,
                    monthly_limit=TokenCreationControlService.DEFAULT_MONTHLY_LIMIT
                )
                db.session.add(limits)
                db.session.commit()
                
                logger.info(f"Limites padrão criados para admin {admin_id}: "
                           f"Diário R$ {limits.daily_limit}, Mensal R$ {limits.monthly_limit}")
            
            # Resetar contadores se necessário
            limits.reset_daily_if_needed()
            limits.reset_monthly_if_needed()
            
            if db.session.dirty:
                db.session.commit()
            
            return limits
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao obter/criar limites para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def check_daily_limit(admin_id, amount):
        """Verifica se a criação está dentro do limite diário"""
        try:
            amount = Decimal(str(amount))
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            
            # Verificar se pode criar a quantidade solicitada
            if limits.current_daily_used + amount > limits.daily_limit:
                remaining = limits.daily_remaining
                return {
                    'allowed': False,
                    'reason': 'daily_limit_exceeded',
                    'message': f'Limite diário excedido. Disponível: R$ {remaining:.2f}, Solicitado: R$ {amount:.2f}',
                    'daily_limit': float(limits.daily_limit),
                    'daily_used': float(limits.current_daily_used),
                    'daily_remaining': float(remaining),
                    'amount_requested': float(amount)
                }
            
            return {
                'allowed': True,
                'daily_limit': float(limits.daily_limit),
                'daily_used': float(limits.current_daily_used),
                'daily_remaining': float(limits.daily_remaining),
                'amount_requested': float(amount)
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite diário para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def check_monthly_limit(admin_id, amount):
        """Verifica se a criação está dentro do limite mensal"""
        try:
            amount = Decimal(str(amount))
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            
            # Verificar se pode criar a quantidade solicitada
            if limits.current_monthly_used + amount > limits.monthly_limit:
                remaining = limits.monthly_remaining
                return {
                    'allowed': False,
                    'reason': 'monthly_limit_exceeded',
                    'message': f'Limite mensal excedido. Disponível: R$ {remaining:.2f}, Solicitado: R$ {amount:.2f}',
                    'monthly_limit': float(limits.monthly_limit),
                    'monthly_used': float(limits.current_monthly_used),
                    'monthly_remaining': float(remaining),
                    'amount_requested': float(amount)
                }
            
            return {
                'allowed': True,
                'monthly_limit': float(limits.monthly_limit),
                'monthly_used': float(limits.current_monthly_used),
                'monthly_remaining': float(limits.monthly_remaining),
                'amount_requested': float(amount)
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite mensal para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def can_create_tokens(admin_id, amount):
        """Verifica se é possível criar a quantidade de tokens solicitada"""
        try:
            amount = Decimal(str(amount))
            
            if amount <= 0:
                return {
                    'allowed': False,
                    'reason': 'invalid_amount',
                    'message': 'Valor deve ser maior que zero',
                    'amount_requested': float(amount)
                }
            
            # Verificar limite diário
            daily_check = TokenCreationControlService.check_daily_limit(admin_id, amount)
            if not daily_check['allowed']:
                return daily_check
            
            # Verificar limite mensal
            monthly_check = TokenCreationControlService.check_monthly_limit(admin_id, amount)
            if not monthly_check['allowed']:
                return monthly_check
            
            # Ambos os limites estão OK
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            
            return {
                'allowed': True,
                'message': 'Criação de tokens autorizada',
                'daily_limit': float(limits.daily_limit),
                'daily_used': float(limits.current_daily_used),
                'daily_remaining': float(limits.daily_remaining),
                'monthly_limit': float(limits.monthly_limit),
                'monthly_used': float(limits.current_monthly_used),
                'monthly_remaining': float(limits.monthly_remaining),
                'amount_requested': float(amount)
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar possibilidade de criação para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def register_token_creation(admin_id, amount, reason=None, transaction_id=None):
        """Registra a criação de tokens e atualiza os contadores"""
        try:
            amount = Decimal(str(amount))
            
            # Verificar se pode criar antes de registrar
            check_result = TokenCreationControlService.can_create_tokens(admin_id, amount)
            if not check_result['allowed']:
                raise ValueError(f"Criação não autorizada: {check_result['message']}")
            
            # Obter limites
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            
            # Atualizar contadores
            limits.add_usage(amount)
            
            # Salvar no banco
            db.session.commit()
            
            # Log da criação
            admin = AdminUser.query.get(admin_id)
            log_message = (f"Tokens criados - Admin: {admin.email} ({admin_id}), "
                          f"Valor: R$ {amount:.2f}, "
                          f"Motivo: {reason or 'Não especificado'}")
            
            if transaction_id:
                log_message += f", Transaction ID: {transaction_id}"
            
            logger.info(log_message)
            
            return {
                'success': True,
                'message': f'Criação de R$ {amount:.2f} registrada com sucesso',
                'daily_used': float(limits.current_daily_used),
                'daily_remaining': float(limits.daily_remaining),
                'monthly_used': float(limits.current_monthly_used),
                'monthly_remaining': float(limits.monthly_remaining),
                'amount_created': float(amount)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao registrar criação de tokens para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def get_admin_limits_info(admin_id):
        """Retorna informações detalhadas sobre os limites de um administrador"""
        try:
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            admin = AdminUser.query.get(admin_id)
            
            return {
                'admin_id': admin_id,
                'admin_email': admin.email,
                'daily_limit': float(limits.daily_limit),
                'daily_used': float(limits.current_daily_used),
                'daily_remaining': float(limits.daily_remaining),
                'daily_percentage_used': float((limits.current_daily_used / limits.daily_limit) * 100),
                'monthly_limit': float(limits.monthly_limit),
                'monthly_used': float(limits.current_monthly_used),
                'monthly_remaining': float(limits.monthly_remaining),
                'monthly_percentage_used': float((limits.current_monthly_used / limits.monthly_limit) * 100),
                'last_daily_reset': limits.last_daily_reset.isoformat(),
                'last_monthly_reset': limits.last_monthly_reset.isoformat(),
                'created_at': limits.created_at.isoformat(),
                'updated_at': limits.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de limites para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def update_admin_limits(admin_id, daily_limit=None, monthly_limit=None, updated_by_admin_id=None):
        """Atualiza os limites de um administrador"""
        try:
            limits = TokenCreationControlService.get_or_create_limits(admin_id)
            
            changes = []
            
            if daily_limit is not None:
                daily_limit = Decimal(str(daily_limit))
                if daily_limit <= 0:
                    raise ValueError("Limite diário deve ser maior que zero")
                
                old_daily = limits.daily_limit
                limits.daily_limit = daily_limit
                changes.append(f"Limite diário: R$ {old_daily:.2f} → R$ {daily_limit:.2f}")
            
            if monthly_limit is not None:
                monthly_limit = Decimal(str(monthly_limit))
                if monthly_limit <= 0:
                    raise ValueError("Limite mensal deve ser maior que zero")
                
                old_monthly = limits.monthly_limit
                limits.monthly_limit = monthly_limit
                changes.append(f"Limite mensal: R$ {old_monthly:.2f} → R$ {monthly_limit:.2f}")
            
            if changes:
                limits.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Log da alteração
                admin = AdminUser.query.get(admin_id)
                updated_by = AdminUser.query.get(updated_by_admin_id) if updated_by_admin_id else None
                
                log_message = (f"Limites atualizados - Admin: {admin.email} ({admin_id}), "
                              f"Alterações: {'; '.join(changes)}")
                
                if updated_by:
                    log_message += f", Alterado por: {updated_by.email} ({updated_by_admin_id})"
                
                logger.info(log_message)
                
                return {
                    'success': True,
                    'message': f'Limites atualizados: {"; ".join(changes)}',
                    'changes': changes
                }
            else:
                return {
                    'success': False,
                    'message': 'Nenhuma alteração especificada'
                }
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar limites para admin {admin_id}: {e}")
            raise
    
    @staticmethod
    def get_all_admins_limits():
        """Retorna limites de todos os administradores ativos"""
        try:
            # Buscar todos os admins ativos
            active_admins = AdminUser.query.filter_by(deleted_at=None).all()
            
            limits_info = []
            for admin in active_admins:
                try:
                    info = TokenCreationControlService.get_admin_limits_info(admin.id)
                    limits_info.append(info)
                except Exception as e:
                    logger.warning(f"Erro ao obter limites para admin {admin.id}: {e}")
                    continue
            
            return limits_info
            
        except Exception as e:
            logger.error(f"Erro ao obter limites de todos os admins: {e}")
            raise
    
    @staticmethod
    def get_creation_history(admin_id=None, days=30):
        """Retorna histórico de criações de tokens"""
        try:
            # Data de início (últimos N dias)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Query base para transações de criação de tokens
            query = Transaction.query.filter(
                Transaction.type == 'deposito',  # Assumindo que criação de tokens é tipo 'deposito'
                Transaction.created_at >= start_date
            )
            
            if admin_id:
                # Filtrar por admin específico seria necessário adicionar campo admin_id em Transaction
                # Por enquanto, retornar todas as criações
                pass
            
            transactions = query.order_by(Transaction.created_at.desc()).all()
            
            history = []
            for transaction in transactions:
                history.append({
                    'transaction_id': transaction.transaction_id,
                    'amount': float(transaction.amount),
                    'description': transaction.description,
                    'created_at': transaction.created_at.isoformat(),
                    'user_id': transaction.user_id
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico de criações: {e}")
            raise