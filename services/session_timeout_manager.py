#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
SessionTimeoutManager - Gerenciador de timeout de sessões
Implementa controle de expiração de sessões com aviso prévio e limpeza automática
"""

from datetime import datetime, timedelta
from flask import session, request, current_app
from models import db, SessionTimeout
import logging
import uuid

class SessionTimeoutManager:
    """Gerenciador de timeout de sessões do sistema"""
    
    # Configurações de timeout
    TIMEOUT_MINUTES = 30  # 30 minutos de inatividade
    WARNING_MINUTES = 5   # Aviso 5 minutos antes da expiração
    
    @staticmethod
    def initialize_session_timeout():
        """
        Inicializa o controle de timeout para uma nova sessão
        Deve ser chamado após login bem-sucedido
        """
        try:
            # Gerar ID único para a sessão se não existir
            if 'session_uuid' not in session:
                session['session_uuid'] = str(uuid.uuid4())
            
            session_id = session['session_uuid']
            user_id = session.get('user_id')
            admin_id = session.get('admin_id')
            
            # Calcular tempo de expiração
            now = datetime.utcnow()
            expires_at = now + timedelta(minutes=SessionTimeoutManager.TIMEOUT_MINUTES)
            
            # Verificar se já existe registro para esta sessão
            existing_timeout = SessionTimeout.query.filter_by(session_id=session_id).first()
            
            if existing_timeout:
                # Atualizar registro existente
                existing_timeout.last_activity = now
                existing_timeout.expires_at = expires_at
                existing_timeout.user_id = user_id
                existing_timeout.admin_id = admin_id
                existing_timeout.ip_address = request.remote_addr
                existing_timeout.user_agent = request.headers.get('User-Agent', '')[:255]
            else:
                # Criar novo registro
                session_timeout = SessionTimeout(
                    session_id=session_id,
                    user_id=user_id,
                    admin_id=admin_id,
                    last_activity=now,
                    expires_at=expires_at,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:255]
                )
                db.session.add(session_timeout)
            
            # Salvar timestamp da última atividade na sessão Flask
            session['last_activity'] = now.isoformat()
            session['expires_at'] = expires_at.isoformat()
            
            db.session.commit()
            
            current_app.logger.info(
                f"Timeout de sessão inicializado - Session: {session_id}, "
                f"User: {user_id}, Admin: {admin_id}, Expira em: {expires_at}"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao inicializar timeout de sessão: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def check_session_timeout():
        """
        Verifica se a sessão atual expirou
        Retorna: dict com status da sessão
        """
        try:
            session_id = session.get('session_uuid')
            if not session_id:
                return {
                    'expired': True,
                    'reason': 'session_not_found',
                    'message': 'Sessão não encontrada'
                }
            
            # Buscar registro de timeout no banco
            session_timeout = SessionTimeout.query.filter_by(session_id=session_id).first()
            if not session_timeout:
                return {
                    'expired': True,
                    'reason': 'timeout_record_not_found',
                    'message': 'Registro de timeout não encontrado'
                }
            
            now = datetime.utcnow()
            
            # Verificar se a sessão expirou
            if now > session_timeout.expires_at:
                current_app.logger.info(
                    f"Sessão expirada - Session: {session_id}, "
                    f"Expirou em: {session_timeout.expires_at}, Agora: {now}"
                )
                return {
                    'expired': True,
                    'reason': 'timeout_expired',
                    'message': 'Sua sessão expirou por inatividade',
                    'expired_at': session_timeout.expires_at.isoformat()
                }
            
            # Calcular tempo restante
            time_remaining = session_timeout.expires_at - now
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            
            # Verificar se deve mostrar aviso
            should_warn = minutes_remaining <= SessionTimeoutManager.WARNING_MINUTES
            
            return {
                'expired': False,
                'should_warn': should_warn,
                'minutes_remaining': minutes_remaining,
                'expires_at': session_timeout.expires_at.isoformat(),
                'last_activity': session_timeout.last_activity.isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao verificar timeout de sessão: {str(e)}")
            return {
                'expired': True,
                'reason': 'check_error',
                'message': 'Erro ao verificar sessão'
            }
    
    @staticmethod
    def extend_session():
        """
        Estende a sessão atual atualizando a última atividade
        Retorna: dict com resultado da operação
        """
        try:
            session_id = session.get('session_uuid')
            if not session_id:
                return {
                    'success': False,
                    'message': 'Sessão não encontrada'
                }
            
            # Buscar registro de timeout
            session_timeout = SessionTimeout.query.filter_by(session_id=session_id).first()
            if not session_timeout:
                return {
                    'success': False,
                    'message': 'Registro de timeout não encontrado'
                }
            
            now = datetime.utcnow()
            
            # Verificar se a sessão já expirou
            if now > session_timeout.expires_at:
                return {
                    'success': False,
                    'message': 'Sessão já expirada'
                }
            
            # Atualizar última atividade e nova expiração
            session_timeout.last_activity = now
            session_timeout.expires_at = now + timedelta(minutes=SessionTimeoutManager.TIMEOUT_MINUTES)
            
            # Atualizar também na sessão Flask
            session['last_activity'] = now.isoformat()
            session['expires_at'] = session_timeout.expires_at.isoformat()
            
            db.session.commit()
            
            current_app.logger.info(
                f"Sessão estendida - Session: {session_id}, "
                f"Nova expiração: {session_timeout.expires_at}"
            )
            
            return {
                'success': True,
                'message': 'Sessão estendida com sucesso',
                'new_expires_at': session_timeout.expires_at.isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao estender sessão: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': 'Erro interno ao estender sessão'
            }
    
    @staticmethod
    def cleanup_expired_sessions():
        """
        Remove sessões expiradas do banco de dados
        Retorna: número de sessões removidas
        """
        try:
            now = datetime.utcnow()
            
            # Buscar sessões expiradas
            expired_sessions = SessionTimeout.query.filter(
                SessionTimeout.expires_at < now
            ).all()
            
            count = len(expired_sessions)
            
            if count > 0:
                # Remover sessões expiradas
                SessionTimeout.query.filter(
                    SessionTimeout.expires_at < now
                ).delete()
                
                db.session.commit()
                
                current_app.logger.info(f"Limpeza de sessões: {count} sessões expiradas removidas")
            
            return count
            
        except Exception as e:
            current_app.logger.error(f"Erro na limpeza de sessões expiradas: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def invalidate_session(session_id=None):
        """
        Invalida uma sessão específica ou a sessão atual
        """
        try:
            if not session_id:
                session_id = session.get('session_uuid')
            
            if session_id:
                # Remover do banco
                SessionTimeout.query.filter_by(session_id=session_id).delete()
                db.session.commit()
                
                # Limpar sessão Flask se for a sessão atual
                if session.get('session_uuid') == session_id:
                    session.clear()
                
                current_app.logger.info(f"Sessão invalidada: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Erro ao invalidar sessão: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_active_sessions_count():
        """
        Retorna o número de sessões ativas no sistema
        """
        try:
            now = datetime.utcnow()
            count = SessionTimeout.query.filter(
                SessionTimeout.expires_at > now
            ).count()
            return count
        except Exception as e:
            current_app.logger.error(f"Erro ao contar sessões ativas: {str(e)}")
            return 0
    
    @staticmethod
    def get_user_active_sessions(user_id=None, admin_id=None):
        """
        Retorna as sessões ativas de um usuário específico
        """
        try:
            now = datetime.utcnow()
            query = SessionTimeout.query.filter(
                SessionTimeout.expires_at > now
            )
            
            if user_id:
                query = query.filter(SessionTimeout.user_id == user_id)
            elif admin_id:
                query = query.filter(SessionTimeout.admin_id == admin_id)
            else:
                return []
            
            sessions = query.all()
            
            return [{
                'session_id': s.session_id,
                'last_activity': s.last_activity.isoformat(),
                'expires_at': s.expires_at.isoformat(),
                'ip_address': s.ip_address,
                'user_agent': s.user_agent[:50] + '...' if len(s.user_agent) > 50 else s.user_agent
            } for s in sessions]
            
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar sessões do usuário: {str(e)}")
            return []
    
    @staticmethod
    def force_logout_user(user_id=None, admin_id=None):
        """
        Força logout de todas as sessões de um usuário
        """
        try:
            query = SessionTimeout.query
            
            if user_id:
                query = query.filter(SessionTimeout.user_id == user_id)
            elif admin_id:
                query = query.filter(SessionTimeout.admin_id == admin_id)
            else:
                return 0
            
            count = query.count()
            query.delete()
            db.session.commit()
            
            current_app.logger.info(
                f"Logout forçado - {'User' if user_id else 'Admin'}: "
                f"{user_id or admin_id}, {count} sessões removidas"
            )
            
            return count
            
        except Exception as e:
            current_app.logger.error(f"Erro ao forçar logout: {str(e)}")
            db.session.rollback()
            return 0