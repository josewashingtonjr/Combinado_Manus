#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import login_required
import os

# Criar blueprint para rotas da página inicial
home_bp = Blueprint('home', __name__, url_prefix='/')

@home_bp.route('/')
def index():
    """Página inicial da plataforma"""
    return render_template('home/index.html')

@home_bp.route('/sobre')
def about():
    """Página sobre a plataforma"""
    return render_template('home/about.html')

@home_bp.route('/recursos')
def features():
    """Página de recursos da plataforma"""
    return render_template('home/features.html')

@home_bp.route('/precos')
def pricing():
    """Página de preços da plataforma"""
    return render_template('home/pricing.html')

@home_bp.route('/contato')
def contact():
    """Página de contato"""
    return render_template('home/contact.html')

@home_bp.route('/termos')
def terms():
    """Termos de uso"""
    return render_template('home/terms.html')

@home_bp.route('/privacidade')
def privacy():
    """Política de privacidade"""
    return render_template('home/privacy.html')

@home_bp.context_processor
def inject_app_version():
    """Injetar versão da aplicação em todos os templates"""
    return dict(
        app_version=os.environ.get('APP_VERSION', '0.1.0')
    )
