# -*- coding: utf-8 -*-
"""
Template Helpers
Funções auxiliares para templates Jinja2
"""

from flask import current_app
import os


def asset_url(filename):
    """
    Retorna URL do asset, usando versão minificada em produção
    
    Uso no template:
        <link href="{{ asset_url('css/mobile-first.css') }}" rel="stylesheet">
    
    Em produção (USE_MINIFIED_ASSETS=true):
        Retorna: css/mobile-first.min.css
    
    Em desenvolvimento (USE_MINIFIED_ASSETS=false):
        Retorna: css/mobile-first.css
    """
    use_minified = current_app.config.get('USE_MINIFIED_ASSETS', True)
    
    if not use_minified:
        return filename
    
    # Verificar se é arquivo CSS ou JS
    if filename.endswith('.css') or filename.endswith('.js'):
        # Verificar se já é minificado
        if '.min.' in filename:
            return filename
        
        # Criar nome do arquivo minificado
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            minified_filename = f"{parts[0]}.min.{parts[1]}"
            
            # Verificar se arquivo minificado existe
            static_folder = current_app.static_folder
            minified_path = os.path.join(static_folder, minified_filename)
            
            if os.path.exists(minified_path):
                return minified_filename
    
    # Retornar arquivo original se minificado não existir
    return filename


def register_template_helpers(app):
    """
    Registra helpers no contexto do template
    
    Uso:
        from template_helpers import register_template_helpers
        register_template_helpers(app)
    """
    app.jinja_env.globals.update(asset_url=asset_url)
