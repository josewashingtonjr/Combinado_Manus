#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste simples de sintaxe do template
"""

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
import os

def test_template_syntax():
    """Testar se o template tem sintaxe válida"""
    try:
        # Configurar ambiente Jinja2
        env = Environment(loader=FileSystemLoader('templates'))
        
        # Tentar carregar o template
        template = env.get_template('cliente/ver_convite.html')
        
        print("✅ Template cliente/ver_convite.html tem sintaxe válida!")
        return True
        
    except TemplateSyntaxError as e:
        print(f"❌ Erro de sintaxe no template: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao carregar template: {e}")
        return False

if __name__ == '__main__':
    test_template_syntax()