#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, AdminUser, Order, Transaction, Wallet, db
from datetime import datetime, timedelta
from sqlalchemy import func
from services.wallet_service import WalletService

class AdminService:
    """Serviço para operações administrativas"""
    
    @staticmethod
    def get_dashboard_stats():
        """Retorna estatísticas reais para o dashboard administrativo com terminologia técnica"""
        # Estatísticas de usuários
        total_usuarios = User.query.count()
        usuarios_ativos = User.query.filter_by(active=True).count()
        usuarios_inativos = User.query.filter_by(active=False).count()
        
        # Usuários criados no mês atual
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usuarios_recentes = User.query.filter(User.created_at >= inicio_mes).count()
        
        # Estatísticas de ordens (contratos)
        contratos_ativos = Order.query.filter(
            Order.status.in_(['disponivel', 'aceita', 'em_andamento'])
        ).count()
        contratos_finalizados = Order.query.filter_by(status='concluida').count()
        
        # Contestações (ordens disputadas)
        contestacoes_abertas = Order.query.filter_by(status='disputada').count()
        
        # Estatísticas de tokenomics (terminologia técnica para admin)
        try:
            token_summary = WalletService.get_system_token_summary()
            total_tokens_sistema = token_summary['total_tokens_created']
            tokens_em_circulacao = token_summary['tokens_in_circulation']
            saldo_admin_tokens = token_summary['admin_balance']
        except Exception:
            # Fallback se ainda não houver dados de tokenomics
            total_tokens_sistema = 0
            tokens_em_circulacao = 0
            saldo_admin_tokens = 0
        
        # Transações do mês atual
        transacoes_mes = Transaction.query.filter(
            Transaction.created_at >= inicio_mes
        ).count()
        
        # Receita do mês (taxas do sistema)
        receita_mes_result = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.type == 'taxa_sistema',
            Transaction.created_at >= inicio_mes
        ).scalar()
        receita_mes = receita_mes_result or 0.0
        
        # Taxas totais recebidas (histórico completo)
        taxas_totais_result = db.session.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.type == 'taxa_sistema'
        ).scalar()
        taxas_totais = taxas_totais_result or 0.0
        
        # Número de transações que geraram taxas no mês
        transacoes_com_taxa_mes = Transaction.query.filter(
            Transaction.type == 'taxa_sistema',
            Transaction.created_at >= inicio_mes
        ).count()
        
        # Taxa média por transação no mês
        taxa_media_mes = receita_mes / transacoes_com_taxa_mes if transacoes_com_taxa_mes > 0 else 0.0
        
        # Métricas detalhadas de circulação (nova funcionalidade)
        try:
            # Tokens em escrow (bloqueados em transações)
            tokens_em_escrow = db.session.query(
                func.sum(Wallet.escrow_balance)
            ).scalar() or 0.0
            
            # Tokens disponíveis com usuários (saldo livre)
            tokens_disponiveis_usuarios = db.session.query(
                func.sum(Wallet.balance)
            ).filter(
                Wallet.user_id != WalletService.ADMIN_USER_ID
            ).scalar() or 0.0
            
            # Percentual de tokens em escrow
            percentual_escrow = (tokens_em_escrow / tokens_em_circulacao * 100) if tokens_em_circulacao > 0 else 0.0
            
        except Exception:
            # Fallback se houver erro no cálculo
            tokens_em_escrow = 0.0
            tokens_disponiveis_usuarios = 0.0
            percentual_escrow = 0.0
        
        # Volume total de transações do mês
        volume_transacoes_mes = db.session.query(
            func.sum(func.abs(Transaction.amount))
        ).filter(
            Transaction.created_at >= inicio_mes
        ).scalar() or 0.0
        
        stats = {
            # Usuários
            'total_usuarios': total_usuarios,
            'usuarios_ativos': usuarios_ativos,
            'usuarios_inativos': usuarios_inativos,
            'usuarios_recentes': usuarios_recentes,
            
            # Ordens/Contratos
            'contratos_ativos': contratos_ativos,
            'contratos_finalizados': contratos_finalizados,
            'contestacoes_abertas': contestacoes_abertas,
            
            # Tokenomics (terminologia técnica para admin)
            'total_tokens_sistema': total_tokens_sistema,
            'tokens_em_circulacao': tokens_em_circulacao,
            'saldo_admin_tokens': saldo_admin_tokens,
            
            # Transações e receita
            'transacoes_mes': transacoes_mes,
            'receita_mes': receita_mes,
            'volume_transacoes_mes': volume_transacoes_mes,
            
            # Métricas de taxas (nova funcionalidade financeira)
            'taxas_totais': taxas_totais,
            'transacoes_com_taxa_mes': transacoes_com_taxa_mes,
            'taxa_media_mes': taxa_media_mes,
            
            # Métricas detalhadas de circulação (nova funcionalidade)
            'tokens_em_escrow': tokens_em_escrow,
            'tokens_disponiveis_usuarios': tokens_disponiveis_usuarios,
            'percentual_escrow': percentual_escrow,
            
            # Métricas adicionais
            'taxa_usuarios_ativos': (usuarios_ativos / total_usuarios * 100) if total_usuarios > 0 else 0,
            'taxa_conclusao_contratos': (contratos_finalizados / (contratos_finalizados + contratos_ativos) * 100) if (contratos_finalizados + contratos_ativos) > 0 else 0
        }
        return stats
    
    @staticmethod
    def create_user(nome, email, cpf, phone, password, roles):
        """Cria um novo usuário"""
        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            raise ValueError('Email já cadastrado no sistema')
        
        # Verificar se CPF já existe
        if User.query.filter_by(cpf=cpf).first():
            raise ValueError('CPF já cadastrado no sistema')
        
        user = User(
            nome=nome,
            email=email,
            cpf=cpf,
            phone=phone,
            roles=roles,
            active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Criar carteira para o usuário
        try:
            from services.wallet_service import WalletService
            WalletService.create_wallet_for_user(user.id)
        except Exception as e:
            # Se falhar na criação da carteira, reverter criação do usuário
            db.session.rollback()
            raise ValueError(f"Erro ao criar carteira para usuário: {str(e)}")
        
        return user
    
    @staticmethod
    def update_user(user, data):
        """Atualiza dados de um usuário"""
        # Verificar se email já existe (exceto o próprio usuário)
        existing_email = User.query.filter(
            User.email == data['email'],
            User.id != user.id
        ).first()
        if existing_email:
            raise ValueError('Email já cadastrado por outro usuário')
        
        # Verificar se CPF já existe (exceto o próprio usuário)
        existing_cpf = User.query.filter(
            User.cpf == data['cpf'],
            User.id != user.id
        ).first()
        if existing_cpf:
            raise ValueError('CPF já cadastrado por outro usuário')
        
        user.nome = data['nome']
        user.email = data['email']
        user.cpf = data['cpf']
        user.phone = data['phone']
        user.roles = data['roles']
        user.active = data['active']
        
        db.session.commit()
        return user
    
    @staticmethod
    def delete_user(user):
        """Deleta um usuário (soft delete)"""
        # TODO: Verificar se usuário tem transações pendentes
        # TODO: Transferir saldo para carteira administrativa
        
        user.active = False
        user.email = f"deleted_{user.id}_{user.email}"
        user.cpf = f"deleted_{user.id}_{user.cpf}"
        
        db.session.commit()
    
    @staticmethod
    def add_tokens_to_user(user, amount, description):
        """Adiciona tokens para um usuário (admin vende tokens)"""
        try:
            result = WalletService.admin_sell_tokens_to_user(
                user_id=user.id,
                amount=amount,
                description=description
            )
            return result
        except Exception as e:
            raise ValueError(f"Erro ao adicionar tokens: {str(e)}")
    
    @staticmethod
    def create_tokens(amount, description="Criação de tokens pelo admin"):
        """Permite ao admin criar novos tokens do zero"""
        try:
            result = WalletService.admin_create_tokens(amount, description)
            return result
        except Exception as e:
            raise ValueError(f"Erro ao criar tokens: {str(e)}")
    
    @staticmethod
    def get_token_management_data():
        """Retorna dados para interface de gestão de tokens"""
        try:
            # Resumo do sistema de tokens
            token_summary = WalletService.get_system_token_summary()
            
            # Informações da carteira do admin
            admin_wallet = WalletService.get_admin_wallet_info()
            
            # Transações recentes do admin
            admin_transactions = WalletService.get_transaction_history(
                user_id=WalletService.ADMIN_USER_ID, 
                limit=20
            )
            
            # Estatísticas de transações por tipo
            transaction_stats = WalletService.get_system_transaction_summary()
            
            # Usuários com mais tokens
            user_wallets = db.session.query(
                Wallet.user_id,
                Wallet.balance,
                Wallet.escrow_balance,
                User.nome,
                User.email
            ).join(User, Wallet.user_id == User.id).filter(
                User.active == True,
                Wallet.user_id != WalletService.ADMIN_USER_ID
            ).order_by(Wallet.balance.desc()).limit(10).all()
            
            top_users = [
                {
                    'user_id': w.user_id,
                    'nome': w.nome,
                    'email': w.email,
                    'balance': w.balance,
                    'escrow_balance': w.escrow_balance,
                    'total_balance': w.balance + w.escrow_balance
                } for w in user_wallets
            ]
            
            return {
                'token_summary': token_summary,
                'admin_wallet': admin_wallet,
                'admin_transactions': admin_transactions,
                'transaction_stats': transaction_stats,
                'top_users': top_users
            }
        except Exception as e:
            # Retornar dados vazios em caso de erro
            return {
                'token_summary': {
                    'admin_balance': 0,
                    'tokens_in_circulation': 0,
                    'total_tokens_created': 0,
                    'circulation_percentage': 0
                },
                'admin_wallet': {
                    'balance': 0,
                    'escrow_balance': 0,
                    'total_balance': 0
                },
                'admin_transactions': [],
                'transaction_stats': {
                    'total_transactions': 0,
                    'total_volume': 0,
                    'type_statistics': [],
                    'top_users': []
                },
                'top_users': []
            }
    
    @staticmethod
    def validate_system_integrity():
        """Valida a integridade matemática do sistema de tokens"""
        try:
            # Validar integridade da carteira do admin
            admin_integrity = WalletService.validate_transaction_integrity(WalletService.ADMIN_USER_ID)
            
            # Validar integridade de usuários ativos
            users = User.query.filter_by(active=True).all()
            user_validations = []
            
            for user in users:
                try:
                    user_integrity = WalletService.validate_transaction_integrity(user.id)
                    user_validations.append({
                        'user_id': user.id,
                        'nome': user.nome,
                        'email': user.email,
                        'is_valid': user_integrity['is_valid'],
                        'balance_matches': user_integrity['balance_matches'],
                        'escrow_matches': user_integrity['escrow_matches']
                    })
                except Exception as e:
                    user_validations.append({
                        'user_id': user.id,
                        'nome': user.nome,
                        'email': user.email,
                        'is_valid': False,
                        'error': str(e)
                    })
            
            # Verificar se total de tokens bate
            token_summary = WalletService.get_system_token_summary()
            total_expected = token_summary['admin_balance'] + token_summary['tokens_in_circulation']
            total_created = token_summary['total_tokens_created']
            system_integrity = abs(total_expected - total_created) < 0.01
            
            return {
                'system_integrity': system_integrity,
                'admin_integrity': admin_integrity,
                'user_validations': user_validations,
                'token_summary': token_summary,
                'total_expected': total_expected,
                'total_created': total_created,
                'discrepancy': total_created - total_expected
            }
        except Exception as e:
            return {
                'system_integrity': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_suspicious_activity_alerts():
        """Detecta atividades suspeitas no sistema"""
        alerts = []
        
        try:
            # Verificar usuários com saldo negativo
            negative_balances = db.session.query(
                Wallet.user_id,
                Wallet.balance,
                User.nome,
                User.email
            ).join(User, Wallet.user_id == User.id).filter(
                Wallet.balance < 0
            ).all()
            
            for wallet in negative_balances:
                alerts.append({
                    'type': 'saldo_negativo',
                    'severity': 'high',
                    'message': f'Usuário {wallet.nome} ({wallet.email}) com saldo negativo: {wallet.balance}',
                    'user_id': wallet.user_id
                })
            
            # Verificar transações de alto valor nas últimas 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            high_value_transactions = Transaction.query.filter(
                Transaction.created_at >= yesterday,
                func.abs(Transaction.amount) > 10000  # Mais de 10k tokens
            ).all()
            
            for transaction in high_value_transactions:
                user = User.query.get(transaction.user_id)
                alerts.append({
                    'type': 'transacao_alto_valor',
                    'severity': 'medium',
                    'message': f'Transação de alto valor: {abs(transaction.amount)} tokens por {user.nome if user else "Usuário desconhecido"}',
                    'transaction_id': transaction.id,
                    'user_id': transaction.user_id
                })
            
            # Verificar usuários com muitas transações recentes
            frequent_users = db.session.query(
                Transaction.user_id,
                func.count(Transaction.id).label('transaction_count'),
                User.nome,
                User.email
            ).join(User, Transaction.user_id == User.id).filter(
                Transaction.created_at >= yesterday
            ).group_by(Transaction.user_id, User.nome, User.email).having(
                func.count(Transaction.id) > 50  # Mais de 50 transações em 24h
            ).all()
            
            for user_stat in frequent_users:
                alerts.append({
                    'type': 'atividade_intensa',
                    'severity': 'low',
                    'message': f'Usuário {user_stat.nome} com {user_stat.transaction_count} transações nas últimas 24h',
                    'user_id': user_stat.user_id
                })
            
        except Exception as e:
            alerts.append({
                'type': 'erro_sistema',
                'severity': 'high',
                'message': f'Erro ao verificar atividades suspeitas: {str(e)}'
            })
        
        return alerts
    
    @staticmethod
    def get_system_config():
        """Retorna configurações do sistema"""
        try:
            from services.config_service import ConfigService
            
            # Inicializar configurações padrão se necessário
            ConfigService.initialize_default_configs()
            
            # Obter configurações por categoria
            taxas = ConfigService.get_configs_by_category('taxas')
            multas = ConfigService.get_configs_by_category('multas')
            seguranca = ConfigService.get_configs_by_category('seguranca')
            backup = ConfigService.get_configs_by_category('backup')
            monitoramento = ConfigService.get_configs_by_category('monitoramento')
            
            return {
                'taxas': taxas,
                'multas': multas,
                'seguranca': seguranca,
                'backup': backup,
                'monitoramento': monitoramento
            }
        except Exception as e:
            # Fallback para configurações padrão
            return {
                'taxa_transacao': 5.0,
                'taxa_saque': 2.50,
                'taxa_deposito': 0.0,
                'valor_minimo_saque': 10.0,
                'multa_cancelamento': 10.0,
                'multa_atraso': 1.0,
                'multa_atraso_maxima': 30.0,
                'multa_contestacao_indevida': 50.0,
                'prazo_contestacao': 7
            }
    
    @staticmethod
    def update_system_config(data):
        """Atualiza configurações do sistema"""
        try:
            from services.config_service import ConfigService
            return ConfigService.update_configs_batch(data)
        except Exception as e:
            raise ValueError(f"Erro ao atualizar configurações: {str(e)}")
    
    @staticmethod
    def get_system_health():
        """Retorna status de saúde do sistema"""
        try:
            from services.config_service import MonitoringService, BackupService, SecurityService
            
            health = MonitoringService.check_system_health()
            backup_status = BackupService.get_backup_status()
            security_stats = SecurityService.get_security_stats()
            
            return {
                'health': health,
                'backup': backup_status,
                'security': security_stats
            }
        except Exception as e:
            return {
                'health': {'overall_status': 'error', 'error': str(e)},
                'backup': {'backup_enabled': False},
                'security': {'total_attempts_24h': 0}
            }
    
    @staticmethod
    def create_backup(backup_type='full'):
        """Cria um backup do sistema"""
        try:
            from services.config_service import BackupService
            return BackupService.create_backup(backup_type)
        except Exception as e:
            raise ValueError(f"Erro ao criar backup: {str(e)}")
    
    @staticmethod
    def get_system_alerts(resolved=False):
        """Obtém alertas do sistema"""
        try:
            from services.config_service import MonitoringService
            return MonitoringService.get_system_alerts(resolved=resolved)
        except Exception as e:
            return []
    
    @staticmethod
    def create_admin_user(email, password, papel='admin'):
        """Cria um usuário administrador"""
        if AdminUser.query.filter_by(email=email).first():
            raise ValueError('Email de administrador já cadastrado')
        
        admin = AdminUser(email=email, papel=papel)
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        return admin
