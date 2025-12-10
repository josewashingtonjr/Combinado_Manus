#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Gerador de IDs únicos para transações financeiras
Implementa o padrão TXN-YYYYMMDD-HHMMSS-UUID8 para identificação única
"""

import uuid
from datetime import datetime
from models import db, Transaction


class TransactionIdGenerator:
    """Gerador de identificadores únicos para transações"""
    
    @staticmethod
    def generate_unique_id():
        """
        Gera ID único no formato TXN-YYYYMMDD-HHMMSS-UUID8
        
        Returns:
            str: ID único da transação no formato especificado
            
        Example:
            TXN-20241106-143052-A1B2C3D4
        """
        # Obter timestamp atual
        now = datetime.utcnow()
        date_part = now.strftime("%Y%m%d")
        time_part = now.strftime("%H%M%S")
        
        # Gerar UUID e pegar os primeiros 8 caracteres em maiúsculo
        uuid_part = str(uuid.uuid4()).replace('-', '').upper()[:8]
        
        # Montar o ID no formato especificado
        transaction_id = f"TXN-{date_part}-{time_part}-{uuid_part}"
        
        # Garantir unicidade verificando no banco
        while TransactionIdGenerator.id_exists(transaction_id):
            # Se já existe, gerar novo UUID
            uuid_part = str(uuid.uuid4()).replace('-', '').upper()[:8]
            transaction_id = f"TXN-{date_part}-{time_part}-{uuid_part}"
        
        return transaction_id
    
    @staticmethod
    def id_exists(transaction_id):
        """
        Verifica se um transaction_id já existe no banco de dados
        
        Args:
            transaction_id (str): ID da transação para verificar
            
        Returns:
            bool: True se o ID já existe, False caso contrário
        """
        try:
            existing = Transaction.query.filter_by(transaction_id=transaction_id).first()
            return existing is not None
        except Exception:
            # Se houver erro na consulta (ex: campo não existe ainda), assumir que não existe
            return False
    
    @staticmethod
    def validate_format(transaction_id):
        """
        Valida se um transaction_id está no formato correto
        
        Args:
            transaction_id (str): ID da transação para validar
            
        Returns:
            bool: True se o formato está correto, False caso contrário
        """
        if not transaction_id or not isinstance(transaction_id, str):
            return False
        
        # Verificar formato: TXN-YYYYMMDD-HHMMSS-UUID8
        parts = transaction_id.split('-')
        
        if len(parts) != 4:
            return False
        
        prefix, date_part, time_part, uuid_part = parts
        
        # Verificar prefixo
        if prefix != 'TXN':
            return False
        
        # Verificar data (8 dígitos)
        if len(date_part) != 8 or not date_part.isdigit():
            return False
        
        # Verificar hora (6 dígitos)
        if len(time_part) != 6 or not time_part.isdigit():
            return False
        
        # Verificar UUID (8 caracteres alfanuméricos maiúsculos)
        if len(uuid_part) != 8 or not uuid_part.isalnum() or not uuid_part.isupper():
            return False
        
        return True
    
    @staticmethod
    def validate_uniqueness(transaction_id):
        """
        Valida se um transaction_id é único no sistema
        
        Args:
            transaction_id (str): ID da transação para validar
            
        Returns:
            bool: True se é único, False se já existe
        """
        return not TransactionIdGenerator.id_exists(transaction_id)