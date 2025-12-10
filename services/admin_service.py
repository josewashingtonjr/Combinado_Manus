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
        
        # Solicitações de tokens (nova funcionalidade)
        try:
            from models import TokenRequest
            solicitacoes_pendentes = TokenRequest.query.filter_by(status='pending').count()
            valor_total_solicitacoes_pendentes = db.session.query(
                func.sum(TokenRequest.amount)
            ).filter_by(status='pending').scalar() or 0.0
        except Exception:
            # Fallback se a tabela ainda não existir
            solicitacoes_pendentes = 0
            valor_total_solicitacoes_pendentes = 0.0
        
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
            
            # Solicitações de tokens (nova funcionalidade)
            'solicitacoes_tokens_pendentes': solicitacoes_pendentes,
            'valor_total_solicitacoes_pendentes': valor_total_solicitacoes_pendentes,
            
            # Métricas adicionais
            'taxa_usuarios_ativos': (usuarios_ativos / total_usuarios * 100) if total_usuarios > 0 else 0,
            'taxa_conclusao_contratos': (contratos_finalizados / (contratos_finalizados + contratos_ativos) * 100) if (contratos_finalizados + contratos_ativos) > 0 else 0
        }
        return stats
    
    @staticmethod
    def get_contestacoes(status=None):
        """
        Buscar contestações reais do sistema (ordens disputadas)
        
        Args:
            status (str, optional): Filtrar por status específico
            
        Returns:
            list: Lista de ordens disputadas
        """
        try:
            # Buscar ordens com status 'disputada'
            query = Order.query.filter_by(status='disputada')
            
            # Aplicar filtro de status se fornecido
            if status:
                # Para futuras implementações de sub-status de disputa
                pass
            
            # Ordenar por data de criação (mais recentes primeiro)
            contestacoes = query.order_by(Order.created_at.desc()).all()
            
            return contestacoes
            
        except Exception as e:
            import logging
            logger = logging.getLogger('app')
            logger.error(f"Erro ao buscar contestações: {str(e)}")
            return []
    
    @staticmethod
    def get_contestacao_details(order_id):
        """
        Obter detalhes completos de uma contestação específica
        
        Args:
            order_id (int): ID da ordem disputada
            
        Returns:
            dict: Detalhes da contestação ou None se não encontrada
        """
        try:
            # Buscar ordem
            order = Order.query.get(order_id)
            if not order:
                return None
            
            # Verificar se é uma disputa
            if order.status != 'disputada':
                return None
            
            # Buscar usuários relacionados
            client = User.query.get(order.client_id)
            provider = User.query.get(order.provider_id) if order.provider_id else None
            
            # Buscar transações relacionadas à ordem
            transactions = Transaction.query.filter_by(order_id=order_id).order_by(Transaction.created_at.desc()).all()
            
            # Buscar informações da carteira do cliente (escrow)
            client_wallet = Wallet.query.filter_by(user_id=order.client_id).first()
            
            # Calcular valores em escrow para esta ordem
            escrow_amount = order.value if client_wallet else 0.0
            
            return {
                'order': order,
                'client': client,
                'provider': provider,
                'transactions': transactions,
                'escrow_amount': escrow_amount,
                'client_wallet': client_wallet,
                'dispute_opened_at': order.created_at,  # Por enquanto usar created_at
                'can_resolve': True  # Admin sempre pode resolver
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger('app')
            logger.error(f"Erro ao buscar detalhes da contestação {order_id}: {str(e)}")
            return None
    
    @staticmethod
    def resolve_contestacao(admin_id, order_id, decision, admin_notes=""):
        """
        Resolver uma contestação com distribuição de tokens
        
        Args:
            admin_id (int): ID do administrador
            order_id (int): ID da ordem disputada
            decision (str): 'favor_cliente' ou 'favor_prestador'
            admin_notes (str): Notas do administrador
            
        Returns:
            dict: Resultado da resolução
        """
        try:
            # Verificar se admin existe
            admin = AdminUser.query.get(admin_id)
            if not admin:
                return {'success': False, 'error': 'Administrador não encontrado'}
            
            # Buscar ordem
            order = Order.query.get(order_id)
            if not order:
                return {'success': False, 'error': 'Ordem não encontrada'}
            
            if order.status != 'disputada':
                return {'success': False, 'error': 'Ordem não está em disputa'}
            
            # Validar decisão
            if decision not in ['favor_cliente', 'favor_prestador']:
                return {'success': False, 'error': 'Decisão inválida'}
            
            # Usar OrderService para resolver a disputa
            from services.order_service import OrderService
            
            result = OrderService.resolve_dispute(
                admin_id=admin_id,
                order_id=order_id,
                decision=decision,
                admin_notes=admin_notes
            )
            
            if result['success']:
                # Log de auditoria
                import logging
                logger = logging.getLogger('app')
                logger.info(f"Contestação {order_id} resolvida por admin {admin.email} - Decisão: {decision}")
                
                return {
                    'success': True,
                    'message': f'Contestação resolvida a {decision.replace("_", " ")}',
                    'decision': decision,
                    'order_id': order_id
                }
            else:
                return result
            
        except Exception as e:
            import logging
            logger = logging.getLogger('app')
            logger.error(f"Erro ao resolver contestação {order_id}: {str(e)}")
            return {'success': False, 'error': 'Erro interno do sistema'}
    
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
    def change_admin_password(admin_id, current_password, new_password):
        """
        Trocar senha do admin com validações robustas e tratamento de erros
        
        Args:
            admin_id (int): ID do administrador
            current_password (str): Senha atual
            new_password (str): Nova senha
            
        Returns:
            dict: Resultado da operação com success, message ou error
        """
        try:
            # Buscar admin no banco
            admin = AdminUser.query.get(admin_id)
            if not admin:
                return {
                    'success': False, 
                    'error': 'Administrador não encontrado no sistema'
                }
            
            # Verificar senha atual
            if not admin.check_password(current_password):
                return {
                    'success': False, 
                    'error': 'Senha atual incorreta'
                }
            
            # Validar nova senha
            if len(new_password) < 6:
                return {
                    'success': False, 
                    'error': 'A nova senha deve ter pelo menos 6 caracteres'
                }
            
            # Atualizar senha
            admin.set_password(new_password)
            db.session.commit()
            
            # Log de auditoria
            from datetime import datetime
            import logging
            
            logger = logging.getLogger('app')
            logger.info(f"Senha alterada com sucesso para admin {admin.email} em {datetime.utcnow()}")
            
            return {
                'success': True, 
                'message': 'Senha alterada com sucesso'
            }
            
        except Exception as e:
            # Rollback em caso de erro
            db.session.rollback()
            
            # Log do erro
            import logging
            logger = logging.getLogger('app')
            logger.error(f"Erro ao alterar senha do admin {admin_id}: {str(e)}")
            
            return {
                'success': False, 
                'error': 'Erro interno do sistema. Tente novamente em alguns minutos.'
            }
    
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
    def delete_user(user_id, admin_id, reason=None):
        """Deleta um usuário usando soft delete"""
        from services.soft_delete_service import SoftDeleteService, SoftDeleteError
        
        try:
            # TODO: Verificar se usuário tem transações pendentes
            # TODO: Transferir saldo para carteira administrativa
            
            # Usar o SoftDeleteService para exclusão segura
            result = SoftDeleteService.soft_delete_user(user_id, admin_id, reason)
            
            if result:
                return {'success': True, 'message': 'Usuário deletado com sucesso'}
            else:
                return {'success': False, 'error': 'Falha na exclusão do usuário'}
                
        except SoftDeleteError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Erro inesperado: {str(e)}'}
    
    @staticmethod
    def restore_user(user_id, admin_id):
        """Restaura um usuário deletado"""
        from services.soft_delete_service import SoftDeleteService, SoftDeleteError
        
        try:
            result = SoftDeleteService.restore_user(user_id, admin_id)
            
            if result:
                return {'success': True, 'message': 'Usuário restaurado com sucesso'}
            else:
                return {'success': False, 'error': 'Falha na restauração do usuário'}
                
        except SoftDeleteError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Erro inesperado: {str(e)}'}
    
    @staticmethod
    def get_deleted_users():
        """Retorna lista de usuários deletados"""
        from services.soft_delete_service import SoftDeleteService
        
        try:
            deleted_users = SoftDeleteService.get_deleted_users()
            
            # Converter para formato de resposta
            users_data = []
            for user in deleted_users:
                deletion_info = SoftDeleteService.get_user_deletion_info(user.id)
                users_data.append({
                    'id': user.id,
                    'email': user.email,
                    'nome': user.nome,
                    'cpf': user.cpf,
                    'deleted_at': user.deleted_at,
                    'deletion_reason': user.deletion_reason,
                    'deleted_by_admin_email': deletion_info.get('deleted_by_admin_email') if deletion_info else None
                })
            
            return {'success': True, 'users': users_data}
            
        except Exception as e:
            return {'success': False, 'error': f'Erro ao buscar usuários deletados: {str(e)}'}
    
    @staticmethod
    def get_active_users():
        """Retorna lista de usuários ativos (não deletados)"""
        from services.soft_delete_service import SoftDeleteService
        
        try:
            active_users = SoftDeleteService.get_active_users()
            
            # Converter para formato de resposta
            users_data = []
            for user in active_users:
                users_data.append({
                    'id': user.id,
                    'email': user.email,
                    'nome': user.nome,
                    'cpf': user.cpf,
                    'phone': user.phone,
                    'active': user.active,
                    'roles': user.roles,
                    'created_at': user.created_at
                })
            
            return {'success': True, 'users': users_data}
            
        except Exception as e:
            return {'success': False, 'error': f'Erro ao buscar usuários ativos: {str(e)}'}
    
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
    
    @staticmethod
    def adjust_token_request_amount(request_id, new_amount, admin_id, reason=None):
        """
        Ajusta a quantidade de tokens de uma solicitação pendente.
        
        Esta funcionalidade permite que administradores corrijam discrepâncias entre
        o valor solicitado pelo usuário e o valor efetivamente pago (verificado através
        do comprovante de pagamento). O ajuste é registrado nas notas administrativas
        para auditoria completa.
        
        Fluxo de Execução:
        1. Valida que a solicitação existe e está pendente
        2. Valida que o novo valor é válido (> 0 e diferente do atual)
        3. Atualiza o campo amount da solicitação
        4. Registra o ajuste nas admin_notes com timestamp e identificação do admin
        5. Preserva notas administrativas anteriores
        6. Registra log de auditoria
        
        Formato das Notas de Ajuste:
        [AJUSTE] Quantidade ajustada de R$ X para R$ Y em DD/MM/YYYY HH:MM por Admin #ID (email)
        Justificativa: [texto opcional fornecido pelo admin]
        
        Args:
            request_id (int): ID da solicitação a ser ajustada
            new_amount (Decimal): Nova quantidade de tokens (deve ser > 0 e diferente do valor atual)
            admin_id (int): ID do administrador que está realizando o ajuste
            reason (str, optional): Justificativa do ajuste (máximo 500 caracteres)
        
        Returns:
            dict: Resultado da operação contendo:
                - success (bool): True se ajuste foi bem-sucedido
                - message (str): Mensagem de sucesso
                - old_amount (float): Valor original da solicitação
                - new_amount (float): Novo valor após ajuste
                - request_id (int): ID da solicitação ajustada
                - error (str): Mensagem de erro (apenas se success=False)
        
        Raises:
            Não lança exceções diretamente, retorna dict com success=False em caso de erro
        
        Examples:
            >>> # Ajustar solicitação de 100 para 50 tokens
            >>> result = AdminService.adjust_token_request_amount(
            ...     request_id=123,
            ...     new_amount=Decimal('50.00'),
            ...     admin_id=1,
            ...     reason='Comprovante mostra pagamento de apenas R$ 50,00'
            ... )
            >>> print(result)
            {
                'success': True,
                'message': 'Quantidade ajustada com sucesso',
                'old_amount': 100.0,
                'new_amount': 50.0,
                'request_id': 123
            }
        """
        import logging
        from decimal import Decimal
        
        logger = logging.getLogger('app')
        
        try:
            # Importar modelo TokenRequest
            from models import TokenRequest
            
            # PASSO 1: Buscar solicitação no banco de dados
            token_request = TokenRequest.query.get(request_id)
            if not token_request:
                return {
                    'success': False,
                    'error': 'Solicitação não encontrada'
                }
            
            # PASSO 2: Validar que a solicitação está com status 'pending'
            # Apenas solicitações pendentes podem ser ajustadas para evitar
            # modificações em solicitações já processadas (aprovadas/rejeitadas)
            if token_request.status != 'pending':
                return {
                    'success': False,
                    'error': 'Apenas solicitações pendentes podem ser ajustadas'
                }
            
            # PASSO 3: Converter new_amount para Decimal se necessário
            # Usamos Decimal para garantir precisão em valores monetários
            if not isinstance(new_amount, Decimal):
                try:
                    new_amount = Decimal(str(new_amount))
                except (ValueError, TypeError):
                    return {
                        'success': False,
                        'error': 'Valor inválido fornecido'
                    }
            
            # PASSO 4: Validar que o novo valor é maior que zero
            # Não permitimos valores negativos ou zero
            if new_amount <= 0:
                return {
                    'success': False,
                    'error': 'O novo valor deve ser maior que zero'
                }
            
            # PASSO 5: Validar que o novo valor é diferente do atual
            # Evita ajustes desnecessários que não alteram nada
            if new_amount == token_request.amount:
                return {
                    'success': False,
                    'error': 'O novo valor deve ser diferente do valor atual'
                }
            
            # PASSO 6: Buscar informações do administrador para registro de auditoria
            admin = AdminUser.query.get(admin_id)
            if not admin:
                return {
                    'success': False,
                    'error': 'Administrador não encontrado'
                }
            
            # PASSO 7: Armazenar valor antigo para registro nas notas
            old_amount = token_request.amount
            
            # PASSO 8: Atualizar o campo amount com o novo valor
            # Este é o campo que será usado quando a solicitação for aprovada
            token_request.amount = new_amount
            
            # PASSO 9: Construir nota de ajuste com formato padronizado
            # Formato: [AJUSTE] Quantidade ajustada de R$ X para R$ Y em DD/MM/YYYY HH:MM por Admin #ID (email)
            timestamp = datetime.utcnow().strftime('%d/%m/%Y %H:%M')
            adjustment_note = f"[AJUSTE] Quantidade ajustada de R$ {old_amount:.2f} para R$ {new_amount:.2f} em {timestamp} por Admin #{admin_id} ({admin.email})"
            
            # PASSO 10: Adicionar justificativa se fornecida
            # A justificativa é opcional mas recomendada para documentar o motivo do ajuste
            if reason and reason.strip():
                # Limitar justificativa a 500 caracteres para evitar textos muito longos
                reason_text = reason.strip()[:500]
                adjustment_note += f"\nJustificativa: {reason_text}"
            
            # PASSO 11: Preservar notas administrativas anteriores
            # Adicionamos a nova nota no início, mantendo o histórico completo
            # Isso permite rastrear múltiplos ajustes se necessário
            if token_request.admin_notes:
                token_request.admin_notes = adjustment_note + "\n\n" + token_request.admin_notes
            else:
                token_request.admin_notes = adjustment_note
            
            # PASSO 12: Commit da transação no banco de dados
            # Todas as alterações são salvas atomicamente
            db.session.commit()
            
            # PASSO 13: Registrar log de auditoria no sistema
            # Este log é independente das notas e fica nos arquivos de log do servidor
            logger.info(f"Quantidade da solicitação {request_id} ajustada de R$ {old_amount:.2f} para R$ {new_amount:.2f} por admin {admin.email}")
            
            # PASSO 14: Retornar resultado de sucesso
            return {
                'success': True,
                'message': 'Quantidade ajustada com sucesso',
                'old_amount': float(old_amount),
                'new_amount': float(new_amount),
                'request_id': request_id
            }
            
        except ValueError as e:
            # Erro de validação: rollback e retornar erro
            db.session.rollback()
            logger.warning(f"Validação falhou ao ajustar solicitação {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            # Erro inesperado: rollback, log detalhado e retornar erro genérico
            db.session.rollback()
            logger.error(f"Erro ao ajustar solicitação {request_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Erro interno ao processar ajuste'
            }
    
    @staticmethod
    def get_system_logs(limit=100):
        """Retorna logs do sistema"""
        import os
        
        logs = []
        
        try:
            # Ler logs de erro críticos
            error_log_path = 'logs/erros_criticos.log'
            if os.path.exists(error_log_path):
                with open(error_log_path, 'r', encoding='utf-8') as f:
                    error_lines = f.readlines()[-limit//2:]  # Últimas linhas
                    for line in error_lines:
                        if line.strip():
                            logs.append({
                                'timestamp': line.split(' - ')[0] if ' - ' in line else 'N/A',
                                'level': 'ERROR',
                                'message': line.strip(),
                                'source': 'erros_criticos.log'
                            })
            
            # Ler logs do sistema principal
            system_log_path = 'logs/sistema_combinado.log'
            if os.path.exists(system_log_path):
                with open(system_log_path, 'r', encoding='utf-8') as f:
                    system_lines = f.readlines()[-limit//2:]  # Últimas linhas
                    for line in system_lines:
                        if line.strip() and 'ERROR' in line:
                            logs.append({
                                'timestamp': line.split(' - ')[0] if ' - ' in line else 'N/A',
                                'level': 'ERROR' if 'ERROR' in line else 'INFO',
                                'message': line.strip(),
                                'source': 'sistema_combinado.log'
                            })
            
            # Ordenar por timestamp (mais recentes primeiro)
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return logs[:limit]
            
        except Exception as e:
            return [{
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'ERROR',
                'message': f'Erro ao ler logs do sistema: {str(e)}',
                'source': 'admin_service'
            }]
