#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from models import SystemConfig, SystemBackup, LoginAttempt, SystemAlert, db, User, Wallet, Transaction
from sqlalchemy import func, desc
import logging

class ConfigService:
    """Serviço para gerenciamento de configurações avançadas do sistema"""
    
    # Cache para configurações (5 minutos)
    _config_cache = {}
    _cache_timestamp = {}
    _cache_ttl = 300  # 5 minutos em segundos
    
    # Configurações padrão do sistema
    DEFAULT_CONFIGS = {
        # Taxas
        'taxa_transacao': {'value': '5.0', 'category': 'taxas', 'description': 'Taxa percentual por transação'},
        'taxa_saque': {'value': '2.50', 'category': 'taxas', 'description': 'Taxa fixa para saques'},
        'taxa_deposito': {'value': '0.00', 'category': 'taxas', 'description': 'Taxa fixa para depósitos'},
        'valor_minimo_saque': {'value': '10.00', 'category': 'taxas', 'description': 'Valor mínimo para saques'},
        'valor_maximo_saque': {'value': '50000.00', 'category': 'taxas', 'description': 'Valor máximo para saques'},
        
        # Taxas de Ordens
        'platform_fee_percentage': {'value': '5.0', 'category': 'taxas', 'description': 'Taxa percentual da plataforma sobre o valor do serviço'},
        'contestation_fee': {'value': '10.00', 'category': 'taxas', 'description': 'Taxa fixa de contestação (garantia)'},
        'cancellation_fee_percentage': {'value': '10.0', 'category': 'taxas', 'description': 'Taxa percentual de cancelamento (multa)'},
        
        # Multas
        'multa_cancelamento': {'value': '10.0', 'category': 'multas', 'description': 'Multa percentual por cancelamento'},
        'multa_atraso': {'value': '1.0', 'category': 'multas', 'description': 'Multa percentual por dia de atraso'},
        'multa_atraso_maxima': {'value': '30.0', 'category': 'multas', 'description': 'Multa máxima por atraso'},
        'multa_contestacao_indevida': {'value': '50.00', 'category': 'multas', 'description': 'Multa por contestação indevida'},
        'prazo_contestacao': {'value': '7', 'category': 'multas', 'description': 'Prazo em dias para contestação'},
        
        # Segurança
        'senha_tamanho_minimo': {'value': '8', 'category': 'seguranca', 'description': 'Tamanho mínimo da senha'},
        'max_tentativas_login': {'value': '5', 'category': 'seguranca', 'description': 'Máximo de tentativas de login'},
        'timeout_bloqueio_login': {'value': '30', 'category': 'seguranca', 'description': 'Timeout de bloqueio em minutos'},
        'timeout_sessao': {'value': '120', 'category': 'seguranca', 'description': 'Timeout da sessão em minutos'},
        'require_2fa': {'value': 'false', 'category': 'seguranca', 'description': 'Exigir autenticação de dois fatores'},
        
        # Backup
        'backup_automatico': {'value': 'true', 'category': 'backup', 'description': 'Ativar backup automático'},
        'backup_intervalo_horas': {'value': '24', 'category': 'backup', 'description': 'Intervalo entre backups em horas'},
        'backup_retencao_dias': {'value': '30', 'category': 'backup', 'description': 'Dias de retenção dos backups'},
        'backup_path': {'value': './backups', 'category': 'backup', 'description': 'Diretório para armazenar backups'},
        
        # Monitoramento
        'monitoramento_integridade': {'value': 'true', 'category': 'monitoramento', 'description': 'Ativar monitoramento de integridade'},
        'intervalo_verificacao_integridade': {'value': '6', 'category': 'monitoramento', 'description': 'Intervalo de verificação em horas'},
        'alerta_saldo_baixo': {'value': '100.00', 'category': 'monitoramento', 'description': 'Limite para alerta de saldo baixo'},
        'alerta_transacao_alto_valor': {'value': '10000.00', 'category': 'monitoramento', 'description': 'Limite para alerta de transação de alto valor'},
    }
    
    @staticmethod
    def initialize_default_configs():
        """Inicializa configurações padrão se não existirem"""
        try:
            for key, config_data in ConfigService.DEFAULT_CONFIGS.items():
                existing = SystemConfig.query.filter_by(key=key).first()
                if not existing:
                    config = SystemConfig(
                        key=key,
                        value=config_data['value'],
                        category=config_data['category'],
                        description=config_data['description']
                    )
                    db.session.add(config)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao inicializar configurações padrão: {str(e)}")
            return False
    
    @staticmethod
    def get_config(key: str, default_value: Any = None) -> Any:
        """Obtém uma configuração específica"""
        try:
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                # Tentar converter para o tipo apropriado
                value = config.value
                if value.lower() in ['true', 'false']:
                    return value.lower() == 'true'
                try:
                    if '.' in value:
                        return float(value)
                    else:
                        return int(value)
                except ValueError:
                    return value
            return default_value
        except Exception as e:
            logging.error(f"Erro ao obter configuração {key}: {str(e)}")
            return default_value
    
    @staticmethod
    def set_config(key: str, value: Any, category: str = 'general', description: str = None) -> bool:
        """Define uma configuração"""
        try:
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
                if description:
                    config.description = description
            else:
                config = SystemConfig(
                    key=key,
                    value=str(value),
                    category=category,
                    description=description or f'Configuração {key}'
                )
                db.session.add(config)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao definir configuração {key}: {str(e)}")
            return False
    
    @staticmethod
    def get_configs_by_category(category: str) -> Dict[str, Any]:
        """Obtém todas as configurações de uma categoria"""
        try:
            configs = SystemConfig.query.filter_by(category=category).all()
            result = {}
            for config in configs:
                value = config.value
                # Conversão automática de tipos
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                else:
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Manter como string
                
                result[config.key] = {
                    'value': value,
                    'description': config.description,
                    'updated_at': config.updated_at
                }
            return result
        except Exception as e:
            logging.error(f"Erro ao obter configurações da categoria {category}: {str(e)}")
            return {}
    
    @staticmethod
    def update_configs_batch(configs: Dict[str, Any]) -> bool:
        """Atualiza múltiplas configurações em lote"""
        try:
            for key, value in configs.items():
                config = SystemConfig.query.filter_by(key=key).first()
                if config:
                    config.value = str(value)
                    config.updated_at = datetime.utcnow()
                else:
                    # Se não existe, criar com categoria baseada no nome
                    category = 'general'
                    if key.startswith('taxa_'):
                        category = 'taxas'
                    elif key.startswith('multa_'):
                        category = 'multas'
                    elif 'senha' in key or 'login' in key or 'timeout' in key or '2fa' in key:
                        category = 'seguranca'
                    elif 'backup' in key:
                        category = 'backup'
                    elif 'monitoramento' in key or 'alerta' in key:
                        category = 'monitoramento'
                    
                    config = SystemConfig(
                        key=key,
                        value=str(value),
                        category=category,
                        description=f'Configuração {key}'
                    )
                    db.session.add(config)
            
            db.session.commit()
            # Limpar cache após atualização em lote
            ConfigService._config_cache.clear()
            ConfigService._cache_timestamp.clear()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao atualizar configurações em lote: {str(e)}")
            return False
    
    # ==============================================================================
    #  MÉTODOS PARA GESTÃO DE TAXAS DE ORDENS
    # ==============================================================================
    
    @staticmethod
    def _get_cached_config(key: str, default_value: Any = None) -> Any:
        """Obtém configuração do cache ou do banco de dados"""
        current_time = datetime.utcnow().timestamp()
        
        # Verificar se está no cache e não expirou
        if key in ConfigService._config_cache:
            cache_time = ConfigService._cache_timestamp.get(key, 0)
            if current_time - cache_time < ConfigService._cache_ttl:
                return ConfigService._config_cache[key]
        
        # Buscar do banco de dados
        try:
            config = SystemConfig.query.filter_by(key=key).first()
            if config:
                value = Decimal(config.value)
                # Armazenar no cache
                ConfigService._config_cache[key] = value
                ConfigService._cache_timestamp[key] = current_time
                return value
            return Decimal(str(default_value)) if default_value is not None else None
        except Exception as e:
            logging.error(f"Erro ao obter configuração {key}: {str(e)}")
            return Decimal(str(default_value)) if default_value is not None else None
    
    @staticmethod
    def _clear_cache(key: str = None):
        """Limpa o cache de configurações"""
        if key:
            ConfigService._config_cache.pop(key, None)
            ConfigService._cache_timestamp.pop(key, None)
        else:
            ConfigService._config_cache.clear()
            ConfigService._cache_timestamp.clear()
    
    @staticmethod
    def get_platform_fee_percentage() -> Decimal:
        """
        Retorna a taxa percentual da plataforma sobre o valor do serviço
        
        Returns:
            Decimal: Taxa percentual (padrão: 5.0%)
        """
        return ConfigService._get_cached_config('platform_fee_percentage', '5.0')
    
    @staticmethod
    def get_contestation_fee() -> Decimal:
        """
        Retorna a taxa fixa de contestação (garantia)
        
        Returns:
            Decimal: Taxa fixa em reais (padrão: R$ 10.00)
        """
        return ConfigService._get_cached_config('contestation_fee', '10.00')
    
    @staticmethod
    def get_cancellation_fee_percentage() -> Decimal:
        """
        Retorna a taxa percentual de cancelamento (multa)
        
        Returns:
            Decimal: Taxa percentual (padrão: 10.0%)
        """
        return ConfigService._get_cached_config('cancellation_fee_percentage', '10.0')
    
    @staticmethod
    def set_platform_fee_percentage(value: Decimal, admin_id: int = None) -> Tuple[bool, str]:
        """
        Atualiza a taxa percentual da plataforma
        
        Args:
            value: Novo valor da taxa (0-100%)
            admin_id: ID do admin que está fazendo a alteração (opcional)
            
        Returns:
            Tuple[bool, str]: (Sucesso, Mensagem)
        """
        try:
            # Validar valor
            value = Decimal(str(value))
            if value < 0 or value > 100:
                return False, "Taxa da plataforma deve estar entre 0% e 100%"
            
            # Atualizar configuração
            config = SystemConfig.query.filter_by(key='platform_fee_percentage').first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key='platform_fee_percentage',
                    value=str(value),
                    category='taxas',
                    description='Taxa percentual da plataforma sobre o valor do serviço'
                )
                db.session.add(config)
            
            db.session.commit()
            
            # Limpar cache
            ConfigService._clear_cache('platform_fee_percentage')
            
            # Log da alteração
            logging.info(f"Taxa da plataforma atualizada para {value}% por admin {admin_id}")
            
            return True, f"Taxa da plataforma atualizada para {value}%"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao atualizar taxa da plataforma: {str(e)}")
            return False, f"Erro ao atualizar taxa: {str(e)}"
    
    @staticmethod
    def set_contestation_fee(value: Decimal, admin_id: int = None) -> Tuple[bool, str]:
        """
        Atualiza a taxa fixa de contestação
        
        Args:
            value: Novo valor da taxa (deve ser positivo)
            admin_id: ID do admin que está fazendo a alteração (opcional)
            
        Returns:
            Tuple[bool, str]: (Sucesso, Mensagem)
        """
        try:
            # Validar valor
            value = Decimal(str(value))
            if value <= 0:
                return False, "Taxa de contestação deve ser um valor positivo"
            
            # Atualizar configuração
            config = SystemConfig.query.filter_by(key='contestation_fee').first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key='contestation_fee',
                    value=str(value),
                    category='taxas',
                    description='Taxa fixa de contestação (garantia)'
                )
                db.session.add(config)
            
            db.session.commit()
            
            # Limpar cache
            ConfigService._clear_cache('contestation_fee')
            
            # Log da alteração
            logging.info(f"Taxa de contestação atualizada para R$ {value} por admin {admin_id}")
            
            return True, f"Taxa de contestação atualizada para R$ {value}"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao atualizar taxa de contestação: {str(e)}")
            return False, f"Erro ao atualizar taxa: {str(e)}"
    
    @staticmethod
    def set_cancellation_fee_percentage(value: Decimal, admin_id: int = None) -> Tuple[bool, str]:
        """
        Atualiza a taxa percentual de cancelamento
        
        Args:
            value: Novo valor da taxa (0-100%)
            admin_id: ID do admin que está fazendo a alteração (opcional)
            
        Returns:
            Tuple[bool, str]: (Sucesso, Mensagem)
        """
        try:
            # Validar valor
            value = Decimal(str(value))
            if value < 0 or value > 100:
                return False, "Taxa de cancelamento deve estar entre 0% e 100%"
            
            # Atualizar configuração
            config = SystemConfig.query.filter_by(key='cancellation_fee_percentage').first()
            if config:
                config.value = str(value)
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(
                    key='cancellation_fee_percentage',
                    value=str(value),
                    category='taxas',
                    description='Taxa percentual de cancelamento (multa)'
                )
                db.session.add(config)
            
            db.session.commit()
            
            # Limpar cache
            ConfigService._clear_cache('cancellation_fee_percentage')
            
            # Log da alteração
            logging.info(f"Taxa de cancelamento atualizada para {value}% por admin {admin_id}")
            
            return True, f"Taxa de cancelamento atualizada para {value}%"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao atualizar taxa de cancelamento: {str(e)}")
            return False, f"Erro ao atualizar taxa: {str(e)}"
    
    @staticmethod
    def get_all_fees() -> Dict[str, Decimal]:
        """
        Retorna todas as taxas de ordens atuais
        
        Returns:
            Dict com todas as taxas: {
                'platform_fee_percentage': Decimal,
                'contestation_fee': Decimal,
                'cancellation_fee_percentage': Decimal
            }
        """
        return {
            'platform_fee_percentage': ConfigService.get_platform_fee_percentage(),
            'contestation_fee': ConfigService.get_contestation_fee(),
            'cancellation_fee_percentage': ConfigService.get_cancellation_fee_percentage()
        }


class BackupService:
    """Serviço para gerenciamento de backups automáticos"""
    
    @staticmethod
    def create_backup(backup_type: str = 'full') -> Optional[SystemBackup]:
        """Cria um backup do sistema"""
        try:
            backup_path = ConfigService.get_config('backup_path', './backups')
            
            # Criar diretório de backup se não existir
            os.makedirs(backup_path, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{backup_type}_{timestamp}.sql"
            file_path = os.path.join(backup_path, filename)
            
            # Registrar backup como iniciado
            backup_record = SystemBackup(
                backup_type=backup_type,
                file_path=file_path,
                file_size=0,
                status='running'
            )
            db.session.add(backup_record)
            db.session.commit()
            
            try:
                # Executar backup do banco de dados
                if backup_type == 'full':
                    success = BackupService._create_full_backup(file_path)
                elif backup_type == 'wallets':
                    success = BackupService._create_wallets_backup(file_path)
                elif backup_type == 'transactions':
                    success = BackupService._create_transactions_backup(file_path)
                else:
                    success = BackupService._create_incremental_backup(file_path)
                
                if success and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    backup_record.file_size = file_size
                    backup_record.status = 'completed'
                    backup_record.completed_at = datetime.utcnow()
                else:
                    backup_record.status = 'failed'
                    backup_record.error_message = 'Falha na criação do arquivo de backup'
                
            except Exception as e:
                backup_record.status = 'failed'
                backup_record.error_message = str(e)
                logging.error(f"Erro durante backup: {str(e)}")
            
            db.session.commit()
            return backup_record
            
        except Exception as e:
            logging.error(f"Erro ao criar backup: {str(e)}")
            return None
    
    @staticmethod
    def _create_full_backup(file_path: str) -> bool:
        """Cria backup completo do banco de dados"""
        try:
            # Para SQLite (desenvolvimento)
            if 'sqlite' in str(db.engine.url):
                db_path = str(db.engine.url).replace('sqlite:///', '')
                shutil.copy2(db_path, file_path.replace('.sql', '.db'))
                return True
            
            # Para PostgreSQL (produção)
            elif 'postgresql' in str(db.engine.url):
                # Implementar pg_dump se necessário
                # Por enquanto, criar backup JSON dos dados críticos
                return BackupService._create_json_backup(file_path)
            
            return False
        except Exception as e:
            logging.error(f"Erro no backup completo: {str(e)}")
            return False
    
    @staticmethod
    def _create_wallets_backup(file_path: str) -> bool:
        """Cria backup apenas das carteiras"""
        try:
            wallets = Wallet.query.all()
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'wallets',
                'data': [
                    {
                        'user_id': w.user_id,
                        'balance': float(w.balance),
                        'escrow_balance': float(w.escrow_balance),
                        'updated_at': w.updated_at.isoformat() if w.updated_at else None
                    } for w in wallets
                ]
            }
            
            with open(file_path.replace('.sql', '.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Erro no backup de carteiras: {str(e)}")
            return False
    
    @staticmethod
    def _create_transactions_backup(file_path: str) -> bool:
        """Cria backup das transações dos últimos 30 dias"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            transactions = Transaction.query.filter(
                Transaction.created_at >= cutoff_date
            ).all()
            
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'transactions',
                'period': '30_days',
                'data': [
                    {
                        'id': t.id,
                        'user_id': t.user_id,
                        'type': t.type,
                        'amount': float(t.amount),
                        'description': t.description,
                        'created_at': t.created_at.isoformat(),
                        'order_id': t.order_id,
                        'related_user_id': t.related_user_id
                    } for t in transactions
                ]
            }
            
            with open(file_path.replace('.sql', '.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Erro no backup de transações: {str(e)}")
            return False
    
    @staticmethod
    def _create_incremental_backup(file_path: str) -> bool:
        """Cria backup incremental (últimas 24h)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(hours=24)
            
            # Transações recentes
            transactions = Transaction.query.filter(
                Transaction.created_at >= cutoff_date
            ).all()
            
            # Carteiras atualizadas recentemente
            wallets = Wallet.query.filter(
                Wallet.updated_at >= cutoff_date
            ).all()
            
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'incremental',
                'period': '24_hours',
                'transactions': [
                    {
                        'id': t.id,
                        'user_id': t.user_id,
                        'type': t.type,
                        'amount': float(t.amount),
                        'description': t.description,
                        'created_at': t.created_at.isoformat()
                    } for t in transactions
                ],
                'wallets': [
                    {
                        'user_id': w.user_id,
                        'balance': float(w.balance),
                        'escrow_balance': float(w.escrow_balance),
                        'updated_at': w.updated_at.isoformat()
                    } for w in wallets
                ]
            }
            
            with open(file_path.replace('.sql', '.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Erro no backup incremental: {str(e)}")
            return False
    
    @staticmethod
    def _create_json_backup(file_path: str) -> bool:
        """Cria backup em formato JSON dos dados críticos"""
        try:
            # Dados críticos para backup
            users = User.query.filter_by(active=True).all()
            wallets = Wallet.query.all()
            transactions = Transaction.query.order_by(desc(Transaction.created_at)).limit(10000).all()
            
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'full_json',
                'users': [
                    {
                        'id': u.id,
                        'email': u.email,
                        'nome': u.nome,
                        'cpf': u.cpf,
                        'roles': u.roles,
                        'created_at': u.created_at.isoformat(),
                        'active': u.active
                    } for u in users
                ],
                'wallets': [
                    {
                        'user_id': w.user_id,
                        'balance': float(w.balance),
                        'escrow_balance': float(w.escrow_balance),
                        'updated_at': w.updated_at.isoformat() if w.updated_at else None
                    } for w in wallets
                ],
                'transactions': [
                    {
                        'id': t.id,
                        'user_id': t.user_id,
                        'type': t.type,
                        'amount': float(t.amount),
                        'description': t.description,
                        'created_at': t.created_at.isoformat(),
                        'order_id': t.order_id,
                        'related_user_id': t.related_user_id
                    } for t in transactions
                ]
            }
            
            with open(file_path.replace('.sql', '.json'), 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logging.error(f"Erro no backup JSON: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_old_backups():
        """Remove backups antigos baseado na configuração de retenção"""
        try:
            retention_days = ConfigService.get_config('backup_retencao_dias', 30)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            old_backups = SystemBackup.query.filter(
                SystemBackup.created_at < cutoff_date,
                SystemBackup.status == 'completed'
            ).all()
            
            for backup in old_backups:
                try:
                    if os.path.exists(backup.file_path):
                        os.remove(backup.file_path)
                    db.session.delete(backup)
                except Exception as e:
                    logging.error(f"Erro ao remover backup {backup.id}: {str(e)}")
            
            db.session.commit()
            return len(old_backups)
        except Exception as e:
            logging.error(f"Erro na limpeza de backups: {str(e)}")
            return 0
    
    @staticmethod
    def get_backup_status() -> Dict[str, Any]:
        """Retorna status dos backups"""
        try:
            total_backups = SystemBackup.query.count()
            recent_backups = SystemBackup.query.filter(
                SystemBackup.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            last_backup = SystemBackup.query.order_by(
                desc(SystemBackup.created_at)
            ).first()
            
            failed_backups = SystemBackup.query.filter_by(status='failed').count()
            
            return {
                'total_backups': total_backups,
                'recent_backups': recent_backups,
                'last_backup': {
                    'created_at': last_backup.created_at.isoformat() if last_backup else None,
                    'type': last_backup.backup_type if last_backup else None,
                    'status': last_backup.status if last_backup else None,
                    'file_size': last_backup.file_size if last_backup else 0
                } if last_backup else None,
                'failed_backups': failed_backups,
                'backup_enabled': ConfigService.get_config('backup_automatico', True)
            }
        except Exception as e:
            logging.error(f"Erro ao obter status de backup: {str(e)}")
            return {
                'total_backups': 0,
                'recent_backups': 0,
                'last_backup': None,
                'failed_backups': 0,
                'backup_enabled': False
            }


class SecurityService:
    """Serviço para gerenciamento de segurança"""
    
    @staticmethod
    def log_login_attempt(email: str, ip_address: str, user_agent: str, success: bool, user_type: str = 'user'):
        """Registra tentativa de login"""
        try:
            attempt = LoginAttempt(
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                user_type=user_type
            )
            db.session.add(attempt)
            db.session.commit()
        except Exception as e:
            logging.error(f"Erro ao registrar tentativa de login: {str(e)}")
    
    @staticmethod
    def check_login_attempts(email: str, ip_address: str) -> Dict[str, Any]:
        """Verifica tentativas de login recentes"""
        try:
            max_attempts = ConfigService.get_config('max_tentativas_login', 5)
            timeout_minutes = ConfigService.get_config('timeout_bloqueio_login', 30)
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            # Contar tentativas falhadas recentes
            failed_attempts = LoginAttempt.query.filter(
                LoginAttempt.email == email,
                LoginAttempt.success == False,
                LoginAttempt.attempt_time >= cutoff_time
            ).count()
            
            # Verificar se há tentativas bem-sucedidas após as falhas
            last_success = LoginAttempt.query.filter(
                LoginAttempt.email == email,
                LoginAttempt.success == True,
                LoginAttempt.attempt_time >= cutoff_time
            ).order_by(desc(LoginAttempt.attempt_time)).first()
            
            is_blocked = failed_attempts >= max_attempts
            
            return {
                'is_blocked': is_blocked,
                'failed_attempts': failed_attempts,
                'max_attempts': max_attempts,
                'remaining_attempts': max(0, max_attempts - failed_attempts),
                'timeout_minutes': timeout_minutes,
                'last_success': last_success.attempt_time if last_success else None
            }
        except Exception as e:
            logging.error(f"Erro ao verificar tentativas de login: {str(e)}")
            return {
                'is_blocked': False,
                'failed_attempts': 0,
                'max_attempts': 5,
                'remaining_attempts': 5,
                'timeout_minutes': 30,
                'last_success': None
            }
    
    @staticmethod
    def get_security_stats() -> Dict[str, Any]:
        """Retorna estatísticas de segurança"""
        try:
            # Tentativas de login nas últimas 24h
            last_24h = datetime.utcnow() - timedelta(hours=24)
            
            total_attempts = LoginAttempt.query.filter(
                LoginAttempt.attempt_time >= last_24h
            ).count()
            
            failed_attempts = LoginAttempt.query.filter(
                LoginAttempt.attempt_time >= last_24h,
                LoginAttempt.success == False
            ).count()
            
            success_attempts = total_attempts - failed_attempts
            
            # IPs únicos
            unique_ips = db.session.query(
                func.count(func.distinct(LoginAttempt.ip_address))
            ).filter(
                LoginAttempt.attempt_time >= last_24h
            ).scalar() or 0
            
            # Usuários únicos que tentaram login
            unique_users = db.session.query(
                func.count(func.distinct(LoginAttempt.email))
            ).filter(
                LoginAttempt.attempt_time >= last_24h
            ).scalar() or 0
            
            return {
                'total_attempts_24h': total_attempts,
                'failed_attempts_24h': failed_attempts,
                'success_attempts_24h': success_attempts,
                'success_rate': (success_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'unique_ips_24h': unique_ips,
                'unique_users_24h': unique_users,
                'security_configs': {
                    'max_attempts': ConfigService.get_config('max_tentativas_login', 5),
                    'timeout_minutes': ConfigService.get_config('timeout_bloqueio_login', 30),
                    'session_timeout': ConfigService.get_config('timeout_sessao', 120),
                    'min_password_length': ConfigService.get_config('senha_tamanho_minimo', 8),
                    'require_2fa': ConfigService.get_config('require_2fa', False)
                }
            }
        except Exception as e:
            logging.error(f"Erro ao obter estatísticas de segurança: {str(e)}")
            return {
                'total_attempts_24h': 0,
                'failed_attempts_24h': 0,
                'success_attempts_24h': 0,
                'success_rate': 0,
                'unique_ips_24h': 0,
                'unique_users_24h': 0,
                'security_configs': {}
            }


class MonitoringService:
    """Serviço para monitoramento e alertas do sistema"""
    
    @staticmethod
    def create_alert(alert_type: str, severity: str, title: str, message: str, data: Dict = None) -> SystemAlert:
        """Cria um novo alerta do sistema"""
        try:
            alert = SystemAlert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                data=json.dumps(data) if data else None
            )
            db.session.add(alert)
            db.session.commit()
            return alert
        except Exception as e:
            logging.error(f"Erro ao criar alerta: {str(e)}")
            return None
    
    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """Verifica a saúde geral do sistema"""
        try:
            health_status = {
                'overall_status': 'healthy',
                'checks': {},
                'alerts': []
            }
            
            # Verificar integridade das carteiras
            try:
                from services.wallet_service import WalletService
                integrity_check = WalletService.get_system_token_summary()
                health_status['checks']['wallet_integrity'] = {
                    'status': 'ok',
                    'admin_balance': integrity_check.get('admin_balance', 0),
                    'circulation': integrity_check.get('tokens_in_circulation', 0),
                    'total_created': integrity_check.get('total_tokens_created', 0)
                }
            except Exception as e:
                health_status['checks']['wallet_integrity'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health_status['overall_status'] = 'warning'
            
            # Verificar backup recente
            backup_status = BackupService.get_backup_status()
            if backup_status['last_backup']:
                last_backup_time = datetime.fromisoformat(backup_status['last_backup']['created_at'])
                hours_since_backup = (datetime.utcnow() - last_backup_time).total_seconds() / 3600
                
                if hours_since_backup > 48:  # Mais de 48h sem backup
                    health_status['checks']['backup'] = {
                        'status': 'warning',
                        'hours_since_last': hours_since_backup
                    }
                    health_status['overall_status'] = 'warning'
                else:
                    health_status['checks']['backup'] = {
                        'status': 'ok',
                        'hours_since_last': hours_since_backup
                    }
            else:
                health_status['checks']['backup'] = {
                    'status': 'error',
                    'message': 'Nenhum backup encontrado'
                }
                health_status['overall_status'] = 'critical'
            
            # Verificar alertas não resolvidos
            unresolved_alerts = SystemAlert.query.filter_by(resolved=False).count()
            health_status['checks']['alerts'] = {
                'status': 'ok' if unresolved_alerts == 0 else 'warning',
                'unresolved_count': unresolved_alerts
            }
            
            if unresolved_alerts > 10:
                health_status['overall_status'] = 'warning'
            
            return health_status
        except Exception as e:
            logging.error(f"Erro na verificação de saúde do sistema: {str(e)}")
            return {
                'overall_status': 'error',
                'checks': {},
                'alerts': [],
                'error': str(e)
            }
    
    @staticmethod
    def get_system_alerts(resolved: bool = False, limit: int = 50) -> List[SystemAlert]:
        """Obtém alertas do sistema"""
        try:
            query = SystemAlert.query.filter_by(resolved=resolved)
            return query.order_by(desc(SystemAlert.created_at)).limit(limit).all()
        except Exception as e:
            logging.error(f"Erro ao obter alertas: {str(e)}")
            return []
    
    @staticmethod
    def resolve_alert(alert_id: int, admin_id: int) -> bool:
        """Marca um alerta como resolvido"""
        try:
            alert = SystemAlert.query.get(alert_id)
            if alert:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = admin_id
                db.session.commit()
                return True
            return False
        except Exception as e:
            logging.error(f"Erro ao resolver alerta: {str(e)}")
            return False