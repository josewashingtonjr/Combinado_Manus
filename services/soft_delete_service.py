#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Soft Delete para gerenciar exclusões lógicas de usuários
Implementa exclusão sem remoção física dos dados para preservar integridade financeira
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, AdminUser
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoftDeleteError(Exception):
    """Exceção personalizada para erros de soft delete"""
    pass

class SoftDeleteService:
    """Serviço para gerenciar exclusões lógicas (soft delete) de usuários"""
    
    @staticmethod
    def soft_delete_user(user_id: int, deleted_by_admin_id: int, reason: Optional[str] = None) -> bool:
        """
        Marca um usuário como deletado sem remover do banco de dados
        
        Args:
            user_id: ID do usuário a ser deletado
            deleted_by_admin_id: ID do admin que está executando a exclusão
            reason: Motivo da exclusão (opcional)
            
        Returns:
            bool: True se a exclusão foi bem-sucedida
            
        Raises:
            SoftDeleteError: Se houver erro na exclusão
        """
        try:
            # Verificar se o usuário existe
            user = User.query.get(user_id)
            if not user:
                raise SoftDeleteError(f"Usuário com ID {user_id} não encontrado")
            
            # Verificar se o usuário já foi deletado
            if user.is_deleted:
                raise SoftDeleteError(f"Usuário {user.email} já foi deletado em {user.deleted_at}")
            
            # Verificar se o admin existe
            admin = AdminUser.query.get(deleted_by_admin_id)
            if not admin:
                raise SoftDeleteError(f"Admin com ID {deleted_by_admin_id} não encontrado")
            
            # Verificar se o admin não foi deletado
            if admin.is_deleted:
                raise SoftDeleteError(f"Admin {admin.email} foi deletado e não pode executar operações")
            
            # Executar soft delete
            user.soft_delete(deleted_by_admin_id, reason)
            
            # Salvar no banco
            db.session.commit()
            
            logger.info(f"Usuário {user.email} (ID: {user_id}) foi deletado por admin {admin.email} (ID: {deleted_by_admin_id})")
            if reason:
                logger.info(f"Motivo da exclusão: {reason}")
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco ao deletar usuário {user_id}: {str(e)}")
            raise SoftDeleteError(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao deletar usuário {user_id}: {str(e)}")
            raise SoftDeleteError(f"Erro inesperado: {str(e)}")
    
    @staticmethod
    def soft_delete_admin(admin_id: int, deleted_by_admin_id: int, reason: Optional[str] = None) -> bool:
        """
        Marca um admin como deletado sem remover do banco de dados
        
        Args:
            admin_id: ID do admin a ser deletado
            deleted_by_admin_id: ID do admin que está executando a exclusão
            reason: Motivo da exclusão (opcional)
            
        Returns:
            bool: True se a exclusão foi bem-sucedida
            
        Raises:
            SoftDeleteError: Se houver erro na exclusão
        """
        try:
            # Verificar se o admin existe
            admin = AdminUser.query.get(admin_id)
            if not admin:
                raise SoftDeleteError(f"Admin com ID {admin_id} não encontrado")
            
            # Verificar se o admin já foi deletado
            if admin.is_deleted:
                raise SoftDeleteError(f"Admin {admin.email} já foi deletado em {admin.deleted_at}")
            
            # Verificar se o admin executor existe
            executor_admin = AdminUser.query.get(deleted_by_admin_id)
            if not executor_admin:
                raise SoftDeleteError(f"Admin executor com ID {deleted_by_admin_id} não encontrado")
            
            # Verificar se o admin executor não foi deletado
            if executor_admin.is_deleted:
                raise SoftDeleteError(f"Admin executor {executor_admin.email} foi deletado e não pode executar operações")
            
            # Verificar se não está tentando deletar a si mesmo
            if admin_id == deleted_by_admin_id:
                raise SoftDeleteError("Um admin não pode deletar a si mesmo")
            
            # Executar soft delete
            admin.soft_delete(deleted_by_admin_id, reason)
            
            # Salvar no banco
            db.session.commit()
            
            logger.info(f"Admin {admin.email} (ID: {admin_id}) foi deletado por admin {executor_admin.email} (ID: {deleted_by_admin_id})")
            if reason:
                logger.info(f"Motivo da exclusão: {reason}")
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco ao deletar admin {admin_id}: {str(e)}")
            raise SoftDeleteError(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao deletar admin {admin_id}: {str(e)}")
            raise SoftDeleteError(f"Erro inesperado: {str(e)}")
    
    @staticmethod
    def restore_user(user_id: int, restored_by_admin_id: int) -> bool:
        """
        Restaura um usuário deletado
        
        Args:
            user_id: ID do usuário a ser restaurado
            restored_by_admin_id: ID do admin que está executando a restauração
            
        Returns:
            bool: True se a restauração foi bem-sucedida
            
        Raises:
            SoftDeleteError: Se houver erro na restauração
        """
        try:
            # Verificar se o usuário existe
            user = User.query.get(user_id)
            if not user:
                raise SoftDeleteError(f"Usuário com ID {user_id} não encontrado")
            
            # Verificar se o usuário foi deletado
            if not user.is_deleted:
                raise SoftDeleteError(f"Usuário {user.email} não foi deletado")
            
            # Verificar se o admin existe
            admin = AdminUser.query.get(restored_by_admin_id)
            if not admin:
                raise SoftDeleteError(f"Admin com ID {restored_by_admin_id} não encontrado")
            
            # Verificar se o admin não foi deletado
            if admin.is_deleted:
                raise SoftDeleteError(f"Admin {admin.email} foi deletado e não pode executar operações")
            
            # Executar restauração
            user.restore()
            
            # Salvar no banco
            db.session.commit()
            
            logger.info(f"Usuário {user.email} (ID: {user_id}) foi restaurado por admin {admin.email} (ID: {restored_by_admin_id})")
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco ao restaurar usuário {user_id}: {str(e)}")
            raise SoftDeleteError(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao restaurar usuário {user_id}: {str(e)}")
            raise SoftDeleteError(f"Erro inesperado: {str(e)}")
    
    @staticmethod
    def restore_admin(admin_id: int, restored_by_admin_id: int) -> bool:
        """
        Restaura um admin deletado
        
        Args:
            admin_id: ID do admin a ser restaurado
            restored_by_admin_id: ID do admin que está executando a restauração
            
        Returns:
            bool: True se a restauração foi bem-sucedida
            
        Raises:
            SoftDeleteError: Se houver erro na restauração
        """
        try:
            # Verificar se o admin existe
            admin = AdminUser.query.get(admin_id)
            if not admin:
                raise SoftDeleteError(f"Admin com ID {admin_id} não encontrado")
            
            # Verificar se o admin foi deletado
            if not admin.is_deleted:
                raise SoftDeleteError(f"Admin {admin.email} não foi deletado")
            
            # Verificar se o admin executor existe
            executor_admin = AdminUser.query.get(restored_by_admin_id)
            if not executor_admin:
                raise SoftDeleteError(f"Admin executor com ID {restored_by_admin_id} não encontrado")
            
            # Verificar se o admin executor não foi deletado
            if executor_admin.is_deleted:
                raise SoftDeleteError(f"Admin executor {executor_admin.email} foi deletado e não pode executar operações")
            
            # Executar restauração
            admin.restore()
            
            # Salvar no banco
            db.session.commit()
            
            logger.info(f"Admin {admin.email} (ID: {admin_id}) foi restaurado por admin {executor_admin.email} (ID: {restored_by_admin_id})")
            
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro de banco ao restaurar admin {admin_id}: {str(e)}")
            raise SoftDeleteError(f"Erro de banco de dados: {str(e)}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro inesperado ao restaurar admin {admin_id}: {str(e)}")
            raise SoftDeleteError(f"Erro inesperado: {str(e)}")
    
    @staticmethod
    def get_active_users() -> List[User]:
        """
        Retorna apenas usuários não deletados (ativos)
        
        Returns:
            List[User]: Lista de usuários ativos
        """
        return User.query.filter(User.deleted_at.is_(None)).all()
    
    @staticmethod
    def get_active_admins() -> List[AdminUser]:
        """
        Retorna apenas admins não deletados (ativos)
        
        Returns:
            List[AdminUser]: Lista de admins ativos
        """
        return AdminUser.query.filter(AdminUser.deleted_at.is_(None)).all()
    
    @staticmethod
    def get_deleted_users() -> List[User]:
        """
        Retorna apenas usuários deletados
        
        Returns:
            List[User]: Lista de usuários deletados
        """
        return User.query.filter(User.deleted_at.isnot(None)).all()
    
    @staticmethod
    def get_deleted_admins() -> List[AdminUser]:
        """
        Retorna apenas admins deletados
        
        Returns:
            List[AdminUser]: Lista de admins deletados
        """
        return AdminUser.query.filter(AdminUser.deleted_at.isnot(None)).all()
    
    @staticmethod
    def get_user_deletion_info(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna informações sobre a exclusão de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dict com informações da exclusão ou None se não foi deletado
        """
        user = User.query.get(user_id)
        if not user or not user.is_deleted:
            return None
        
        deleted_by_admin = AdminUser.query.get(user.deleted_by) if user.deleted_by else None
        
        return {
            'user_id': user.id,
            'user_email': user.email,
            'deleted_at': user.deleted_at,
            'deleted_by_admin_id': user.deleted_by,
            'deleted_by_admin_email': deleted_by_admin.email if deleted_by_admin else None,
            'deletion_reason': user.deletion_reason
        }
    
    @staticmethod
    def get_admin_deletion_info(admin_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna informações sobre a exclusão de um admin
        
        Args:
            admin_id: ID do admin
            
        Returns:
            Dict com informações da exclusão ou None se não foi deletado
        """
        admin = AdminUser.query.get(admin_id)
        if not admin or not admin.is_deleted:
            return None
        
        deleted_by_admin = AdminUser.query.get(admin.deleted_by) if admin.deleted_by else None
        
        return {
            'admin_id': admin.id,
            'admin_email': admin.email,
            'deleted_at': admin.deleted_at,
            'deleted_by_admin_id': admin.deleted_by,
            'deleted_by_admin_email': deleted_by_admin.email if deleted_by_admin else None,
            'deletion_reason': admin.deletion_reason
        }
    
    @staticmethod
    def cleanup_old_deleted_records(days_threshold: int = 365) -> Dict[str, int]:
        """
        Remove permanentemente registros deletados há mais de X dias
        ATENÇÃO: Esta operação é irreversível e remove dados do banco
        
        Args:
            days_threshold: Número de dias após os quais registros deletados podem ser removidos
            
        Returns:
            Dict com contadores de registros removidos
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        try:
            # Contar registros que serão removidos
            users_to_remove = User.query.filter(
                User.deleted_at.isnot(None),
                User.deleted_at < cutoff_date
            ).count()
            
            admins_to_remove = AdminUser.query.filter(
                AdminUser.deleted_at.isnot(None),
                AdminUser.deleted_at < cutoff_date
            ).count()
            
            # Remover usuários
            User.query.filter(
                User.deleted_at.isnot(None),
                User.deleted_at < cutoff_date
            ).delete()
            
            # Remover admins
            AdminUser.query.filter(
                AdminUser.deleted_at.isnot(None),
                AdminUser.deleted_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Limpeza concluída: {users_to_remove} usuários e {admins_to_remove} admins removidos permanentemente")
            
            return {
                'users_removed': users_to_remove,
                'admins_removed': admins_to_remove,
                'cutoff_date': cutoff_date
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Erro ao limpar registros antigos: {str(e)}")
            raise SoftDeleteError(f"Erro na limpeza: {str(e)}")