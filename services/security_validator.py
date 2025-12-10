#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço de Validação de Segurança
Centraliza todas as validações de segurança do sistema
"""

import os
import re
import logging
import bleach
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import List, Tuple, Optional
from datetime import datetime
from functools import wraps
from flask import request, jsonify, flash, redirect, url_for, session
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Serviço para validações de segurança"""
    
    # Configurações de upload de arquivos
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'mp4'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB em bytes
    MAX_FILES_PER_UPLOAD = 5
    
    # Configurações de rate limiting (em memória - para produção usar Redis)
    _rate_limit_store = {}
    
    @staticmethod
    def validate_order_ownership(order, user_id: int, required_role: Optional[str] = None) -> Tuple[bool, str]:
        """
        Valida se o usuário tem permissão para acessar/modificar a ordem
        
        Args:
            order: Objeto Order
            user_id: ID do usuário
            required_role: 'client' ou 'provider' (opcional - se None, aceita ambos)
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not order:
            return False, "Ordem não encontrada"
        
        is_client = (order.client_id == user_id)
        is_provider = (order.provider_id == user_id)
        
        # Se não é nem cliente nem prestador
        if not (is_client or is_provider):
            logger.warning(
                f"Tentativa de acesso não autorizado à ordem {order.id} "
                f"pelo usuário {user_id}"
            )
            return False, "Você não tem permissão para acessar esta ordem"
        
        # Se requer papel específico
        if required_role:
            if required_role == 'client' and not is_client:
                logger.warning(
                    f"Usuário {user_id} tentou acessar ordem {order.id} "
                    f"como cliente, mas é o prestador"
                )
                return False, "Apenas o cliente pode executar esta ação"
            
            if required_role == 'provider' and not is_provider:
                logger.warning(
                    f"Usuário {user_id} tentou acessar ordem {order.id} "
                    f"como prestador, mas é o cliente"
                )
                return False, "Apenas o prestador pode executar esta ação"
        
        return True, ""
    
    @staticmethod
    def validate_file_upload(file: FileStorage) -> Tuple[bool, str]:
        """
        Valida um arquivo de upload
        
        Args:
            file: Objeto FileStorage do Flask
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "Arquivo vazio ou sem nome"
        
        # Validar extensão do arquivo
        filename = file.filename.lower()
        file_ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
        
        if file_ext not in SecurityValidator.ALLOWED_EXTENSIONS:
            return False, (
                f"Tipo de arquivo não permitido: .{file_ext}. "
                f"Tipos permitidos: {', '.join(SecurityValidator.ALLOWED_EXTENSIONS)}"
            )
        
        # Validar tamanho do arquivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if file_size > SecurityValidator.MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = SecurityValidator.MAX_FILE_SIZE / (1024 * 1024)
            return False, (
                f"Arquivo '{filename}' excede o tamanho máximo de {max_mb:.0f}MB. "
                f"Tamanho atual: {size_mb:.2f}MB"
            )
        
        if file_size == 0:
            return False, f"Arquivo '{filename}' está vazio"
        
        return True, ""
    
    @staticmethod
    def validate_multiple_files(files: List[FileStorage]) -> Tuple[bool, str, List[FileStorage]]:
        """
        Valida múltiplos arquivos de upload
        
        Args:
            files: Lista de objetos FileStorage
            
        Returns:
            Tuple[bool, str, List]: (is_valid, error_message, valid_files)
        """
        # Filtrar arquivos vazios
        valid_files = [f for f in files if f and f.filename]
        
        # Validar número máximo de arquivos
        if len(valid_files) > SecurityValidator.MAX_FILES_PER_UPLOAD:
            return False, (
                f"Máximo de {SecurityValidator.MAX_FILES_PER_UPLOAD} arquivos permitidos. "
                f"Você enviou {len(valid_files)} arquivos."
            ), []
        
        # Validar cada arquivo individualmente
        for file in valid_files:
            is_valid, error_msg = SecurityValidator.validate_file_upload(file)
            if not is_valid:
                return False, error_msg, []
        
        return True, "", valid_files
    
    @staticmethod
    def sanitize_filename(filename: str, order_id: int = None) -> str:
        """
        Sanitiza nome de arquivo para prevenir ataques
        
        Args:
            filename: Nome original do arquivo
            order_id: ID da ordem (opcional, para adicionar ao nome)
            
        Returns:
            str: Nome de arquivo sanitizado e único
        """
        # Usar secure_filename do Werkzeug
        safe_name = secure_filename(filename)
        
        # Remover caracteres especiais adicionais
        safe_name = re.sub(r'[^\w\s\-\.]', '', safe_name)
        
        # Adicionar timestamp para garantir unicidade
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Separar nome e extensão
        if '.' in safe_name:
            name, ext = safe_name.rsplit('.', 1)
        else:
            name = safe_name
            ext = ''
        
        # Construir nome único
        if order_id:
            unique_name = f"order_{order_id}_{timestamp}_{name}"
        else:
            unique_name = f"{timestamp}_{name}"
        
        # Adicionar extensão
        if ext:
            unique_name = f"{unique_name}.{ext}"
        
        # Limitar tamanho do nome (máximo 255 caracteres)
        if len(unique_name) > 255:
            # Manter extensão e truncar nome
            if ext:
                max_name_length = 255 - len(ext) - 1
                unique_name = f"{unique_name[:max_name_length]}.{ext}"
            else:
                unique_name = unique_name[:255]
        
        return unique_name
    
    @staticmethod
    def check_rate_limit(user_id: int, action: str, max_attempts: int = 5, 
                        window_seconds: int = 60) -> Tuple[bool, str]:
        """
        Verifica rate limiting para ações críticas
        
        Args:
            user_id: ID do usuário
            action: Nome da ação (ex: 'cancel_order', 'open_dispute')
            max_attempts: Número máximo de tentativas
            window_seconds: Janela de tempo em segundos
            
        Returns:
            Tuple[bool, str]: (is_allowed, error_message)
        """
        now = datetime.utcnow()
        key = f"{user_id}:{action}"
        
        # Obter histórico de tentativas
        if key not in SecurityValidator._rate_limit_store:
            SecurityValidator._rate_limit_store[key] = []
        
        attempts = SecurityValidator._rate_limit_store[key]
        
        # Remover tentativas antigas (fora da janela de tempo)
        cutoff_time = now.timestamp() - window_seconds
        attempts = [t for t in attempts if t > cutoff_time]
        SecurityValidator._rate_limit_store[key] = attempts
        
        # Verificar se excedeu o limite
        if len(attempts) >= max_attempts:
            logger.warning(
                f"Rate limit excedido para usuário {user_id} na ação '{action}'. "
                f"Tentativas: {len(attempts)}/{max_attempts} em {window_seconds}s"
            )
            return False, (
                f"Muitas tentativas. Aguarde {window_seconds} segundos antes de tentar novamente."
            )
        
        # Registrar nova tentativa
        attempts.append(now.timestamp())
        SecurityValidator._rate_limit_store[key] = attempts
        
        return True, ""
    
    @staticmethod
    def validate_csrf_token():
        """
        Valida token CSRF para requisições POST/PUT/DELETE
        Nota: Flask-WTF já faz isso automaticamente, mas esta função
        pode ser usada para validações adicionais
        """
        # Flask-WTF já valida CSRF automaticamente
        # Esta função é um placeholder para validações customizadas futuras
        pass
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = None, allow_html: bool = False) -> str:
        """
        Sanitiza entrada de texto para prevenir XSS e injection
        
        Args:
            text: Texto a ser sanitizado
            max_length: Comprimento máximo (opcional)
            allow_html: Se True, permite tags HTML seguras (padrão: False)
            
        Returns:
            str: Texto sanitizado
        """
        if not text:
            return ""
        
        # Remover espaços extras
        text = text.strip()
        
        # Limitar comprimento se especificado
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        # Sanitizar HTML usando bleach
        if allow_html:
            # Permitir apenas tags seguras (nenhuma por padrão)
            text = bleach.clean(
                text,
                tags=[],  # Nenhuma tag HTML permitida
                attributes={},
                strip=True
            )
        else:
            # Remover todas as tags HTML
            text = bleach.clean(text, tags=[], attributes={}, strip=True)
        
        # Remover caracteres de controle (exceto newline e tab)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        
        return text.strip()
    
    @staticmethod
    def validate_monetary_value(value, field_name="valor", min_value=Decimal('0.01'), 
                                max_value=Decimal('1000000.00')) -> Decimal:
        """
        Valida um valor monetário com limites configuráveis
        
        Args:
            value: Valor a validar (Decimal, float ou str)
            field_name: Nome do campo para mensagens de erro
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
            
        Returns:
            Decimal: Valor validado
            
        Raises:
            ValueError: Se valor for inválido
        """
        try:
            # Converter para Decimal
            if isinstance(value, str):
                value = value.replace(',', '.')
                value = Decimal(value)
            elif isinstance(value, float):
                value = Decimal(str(value))
            elif not isinstance(value, Decimal):
                raise ValueError(f"{field_name} deve ser um número")
            
            # Validar que é positivo
            if value <= 0:
                raise ValueError(f"{field_name} deve ser maior que zero")
            
            # Validar limites
            if value < min_value:
                raise ValueError(
                    f"{field_name} deve ser maior ou igual a R$ {min_value:.2f}"
                )
            
            if value > max_value:
                raise ValueError(
                    f"{field_name} deve ser menor ou igual a R$ {max_value:.2f}"
                )
            
            # Validar precisão (máximo 2 casas decimais)
            if value.as_tuple().exponent < -2:
                raise ValueError(f"{field_name} deve ter no máximo 2 casas decimais")
            
            return value
            
        except (InvalidOperation, ValueError) as e:
            logger.warning(f"Valor monetário inválido: {value} - {str(e)}")
            raise ValueError(f"{field_name} inválido: {str(e)}")
    
    @staticmethod
    def validate_date_future(date_value, field_name="data", min_days=1, max_days=365):
        """
        Valida que uma data está no futuro dentro de limites
        
        Args:
            date_value: Data a validar (datetime ou str)
            field_name: Nome do campo para mensagens de erro
            min_days: Mínimo de dias no futuro
            max_days: Máximo de dias no futuro
            
        Returns:
            datetime: Data validada
            
        Raises:
            ValueError: Se data for inválida
        """
        from datetime import timedelta
        
        try:
            # Converter para datetime se necessário
            if isinstance(date_value, str):
                date_value = datetime.strptime(date_value, '%Y-%m-%d')
            
            if not isinstance(date_value, datetime):
                raise ValueError(f"{field_name} deve ser uma data válida")
            
            # Validar que é futura
            now = datetime.now()
            min_date = now + timedelta(days=min_days)
            max_date = now + timedelta(days=max_days)
            
            if date_value < min_date:
                raise ValueError(
                    f"{field_name} deve ser pelo menos {min_days} dia(s) no futuro"
                )
            
            if date_value > max_date:
                raise ValueError(
                    f"{field_name} deve ser no máximo {max_days} dias no futuro"
                )
            
            return date_value
            
        except ValueError as e:
            logger.warning(f"Data inválida: {date_value} - {str(e)}")
            raise ValueError(f"{field_name} inválida: {str(e)}")
    
    @staticmethod
    def validate_order_action_permission(order, user_id: int, action: str) -> Tuple[bool, str]:
        """
        Valida se o usuário pode executar uma ação específica na ordem
        
        Args:
            order: Objeto Order
            user_id: ID do usuário
            action: Ação a ser executada ('mark_completed', 'confirm', 'dispute', 'cancel')
            
        Returns:
            Tuple[bool, str]: (is_allowed, error_message)
        """
        is_client = (order.client_id == user_id)
        is_provider = (order.provider_id == user_id)
        
        if not (is_client or is_provider):
            return False, "Você não tem permissão para acessar esta ordem"
        
        # Validar ações específicas
        if action == 'mark_completed':
            if not is_provider:
                return False, "Apenas o prestador pode marcar o serviço como concluído"
            if not order.can_be_marked_completed:
                return False, f"Ordem não pode ser marcada como concluída. Status atual: {order.status}"
        
        elif action == 'confirm':
            if not is_client:
                return False, "Apenas o cliente pode confirmar o serviço"
            if not order.can_be_confirmed:
                return False, f"Ordem não pode ser confirmada. Status atual: {order.status}"
        
        elif action == 'dispute':
            if not is_client:
                return False, "Apenas o cliente pode abrir contestação"
            if not order.can_be_disputed:
                return False, "Prazo para contestação expirado ou ordem não está no status adequado"
        
        elif action == 'cancel':
            if not order.can_be_cancelled:
                return False, f"Ordem não pode ser cancelada. Status atual: {order.status}"
        
        else:
            return False, f"Ação desconhecida: {action}"
        
        return True, ""


def require_order_ownership(required_role: Optional[str] = None):
    """
    Decorator para validar propriedade da ordem
    
    Args:
        required_role: 'client' ou 'provider' (opcional)
    
    Usage:
        @require_order_ownership(required_role='client')
        def my_route(order_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from models import Order
            from services.auth_service import AuthService
            
            # Obter order_id dos argumentos
            order_id = kwargs.get('order_id')
            if not order_id:
                # Tentar obter dos args posicionais
                if args:
                    order_id = args[0]
            
            if not order_id:
                flash('ID da ordem não fornecido', 'error')
                return redirect(url_for('order.listar_ordens'))
            
            # Buscar ordem
            order = Order.query.get(order_id)
            if not order:
                flash('Ordem não encontrada', 'error')
                return redirect(url_for('order.listar_ordens'))
            
            # Obter usuário atual
            user = AuthService.get_current_user()
            if not user:
                flash('Usuário não autenticado', 'error')
                return redirect(url_for('auth.user_login'))
            
            # Validar propriedade
            is_valid, error_msg = SecurityValidator.validate_order_ownership(
                order, user.id, required_role
            )
            
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('order.listar_ordens'))
            
            # Adicionar ordem aos kwargs para uso na função
            kwargs['order'] = order
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit(action: str, max_attempts: int = 5, window_seconds: int = 60):
    """
    Decorator para rate limiting de ações críticas
    
    Args:
        action: Nome da ação
        max_attempts: Número máximo de tentativas
        window_seconds: Janela de tempo em segundos
    
    Usage:
        @rate_limit('cancel_order', max_attempts=3, window_seconds=300)
        def cancel_order_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from services.auth_service import AuthService
            
            # Obter usuário atual
            user = AuthService.get_current_user()
            if not user:
                flash('Usuário não autenticado', 'error')
                return redirect(url_for('auth.user_login'))
            
            # Verificar rate limit
            is_allowed, error_msg = SecurityValidator.check_rate_limit(
                user.id, action, max_attempts, window_seconds
            )
            
            if not is_allowed:
                # Se for requisição AJAX, retornar JSON
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 429
                
                flash(error_msg, 'error')
                return redirect(request.referrer or url_for('order.listar_ordens'))
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
