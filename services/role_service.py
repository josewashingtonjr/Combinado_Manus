#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Serviço para gerenciamento de papéis de usuário
Implementa alternância entre cliente e prestador para usuários dual
"""

from flask import session
from models import User

class RoleService:
    """Serviço para gerenciamento de papéis de usuário"""
    
    @staticmethod
    def get_user_roles(user_id):
        """Obter lista de papéis do usuário"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Dividir roles por vírgula e limpar espaços
        roles = [role.strip() for role in user.roles.split(',')]
        return roles
    
    @staticmethod
    def is_dual_role_user(user_id):
        """Verificar se usuário tem múltiplos papéis"""
        roles = RoleService.get_user_roles(user_id)
        return len(roles) > 1
    
    @staticmethod
    def has_role(user_id, role):
        """Verificar se usuário tem papel específico"""
        roles = RoleService.get_user_roles(user_id)
        return role in roles
    
    @staticmethod
    def get_active_role():
        """Obter papel ativo atual da sessão"""
        return session.get('active_role', 'cliente')  # Default: cliente
    
    @staticmethod
    def set_active_role(role):
        """Definir papel ativo na sessão"""
        user_id = session.get('user_id')
        if not user_id:
            return False
        
        # Verificar se usuário tem o papel solicitado
        if not RoleService.has_role(user_id, role):
            return False
        
        session['active_role'] = role
        return True
    
    @staticmethod
    def switch_role():
        """Alternar entre papéis disponíveis"""
        user_id = session.get('user_id')
        if not user_id:
            return False
        
        roles = RoleService.get_user_roles(user_id)
        if len(roles) <= 1:
            return False  # Não há papéis para alternar
        
        current_role = RoleService.get_active_role()
        
        # Encontrar próximo papel na lista
        try:
            current_index = roles.index(current_role)
            next_index = (current_index + 1) % len(roles)
            next_role = roles[next_index]
        except ValueError:
            # Papel atual não encontrado, usar primeiro da lista
            next_role = roles[0]
        
        return RoleService.set_active_role(next_role)
    
    @staticmethod
    def get_available_roles(user_id):
        """Obter papéis disponíveis para o usuário"""
        roles = RoleService.get_user_roles(user_id)
        role_labels = {
            'cliente': 'Cliente',
            'prestador': 'Prestador'
        }
        
        return [(role, role_labels.get(role, role.title())) for role in roles]
    
    @staticmethod
    def get_role_dashboard_url(role):
        """Obter URL do dashboard para o papel específico"""
        role_urls = {
            'cliente': 'cliente.dashboard',
            'prestador': 'prestador.dashboard'
        }
        return role_urls.get(role, 'cliente.dashboard')
    
    @staticmethod
    def get_role_color(role):
        """Obter cor associada ao papel"""
        role_colors = {
            'cliente': 'success',  # Verde
            'prestador': 'warning'  # Amarelo
        }
        return role_colors.get(role, 'secondary')
    
    @staticmethod
    def get_role_icon(role):
        """Obter ícone associado ao papel"""
        role_icons = {
            'cliente': 'fas fa-user-tie',
            'prestador': 'fas fa-user-cog'
        }
        return role_icons.get(role, 'fas fa-user')
    
    @staticmethod
    def initialize_user_session(user_id):
        """Inicializar sessão do usuário com papel padrão"""
        roles = RoleService.get_user_roles(user_id)
        if not roles:
            return False
        
        # Definir papel padrão (primeiro da lista ou cliente se disponível)
        default_role = 'cliente' if 'cliente' in roles else roles[0]
        session['active_role'] = default_role
        session['user_roles'] = roles
        
        return True
    
    @staticmethod
    def get_context_for_templates():
        """Obter contexto de papel para templates"""
        user_id = session.get('user_id')
        if not user_id:
            return {
                'active_role': None,
                'available_roles': [],
                'is_dual_role': False,
                'can_switch_roles': False
            }
        
        active_role = RoleService.get_active_role()
        available_roles = RoleService.get_available_roles(user_id)
        is_dual_role = RoleService.is_dual_role_user(user_id)
        
        return {
            'active_role': active_role,
            'available_roles': available_roles,
            'is_dual_role': is_dual_role,
            'can_switch_roles': is_dual_role,
            'role_color': RoleService.get_role_color(active_role),
            'role_icon': RoleService.get_role_icon(active_role)
        }