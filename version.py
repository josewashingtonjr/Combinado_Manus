#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Informações de versão e copyright do Sistema Combinado
"""

from datetime import datetime

# Informações de versão
VERSION = "1.0.0"
VERSION_NAME = "Sistema Combinado"
BUILD_DATE = "2025-11-05"
BUILD_NUMBER = "20251105001"

# Informações de copyright
COPYRIGHT_YEAR = "2025"
COPYRIGHT_HOLDER = "W-jr"
CONTACT_PHONE = "(89) 98137-5841"
DEVELOPER_INFO = f"{COPYRIGHT_HOLDER} {CONTACT_PHONE}"

# Informações completas
FULL_VERSION = f"{VERSION_NAME} v{VERSION}"
COPYRIGHT_TEXT = f"© {COPYRIGHT_YEAR} {DEVELOPER_INFO}. Todos os direitos reservados."
BUILD_INFO = f"Build {BUILD_NUMBER} - {BUILD_DATE}"

# Função para obter informações de versão
def get_version_info():
    """Retorna dicionário com informações de versão"""
    return {
        'version': VERSION,
        'version_name': VERSION_NAME,
        'full_version': FULL_VERSION,
        'build_date': BUILD_DATE,
        'build_number': BUILD_NUMBER,
        'build_info': BUILD_INFO,
        'copyright_year': COPYRIGHT_YEAR,
        'copyright_holder': COPYRIGHT_HOLDER,
        'contact_phone': CONTACT_PHONE,
        'developer_info': DEVELOPER_INFO,
        'copyright_text': COPYRIGHT_TEXT,
        'current_year': datetime.now().year
    }

# Função para obter versão simples
def get_version():
    """Retorna apenas a versão"""
    return VERSION

# Função para obter copyright
def get_copyright():
    """Retorna texto de copyright"""
    return COPYRIGHT_TEXT