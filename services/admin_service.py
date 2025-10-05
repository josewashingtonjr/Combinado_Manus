#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, AdminUser, db
from datetime import datetime
from sqlalchemy import func

class AdminService:
    """Serviço para operações administrativas"""
    
    @staticmethod
    def get_dashboard_stats():
        """Retorna estatísticas para o dashboard administrativo"""
        stats = {
            'total_usuarios': User.query.count(),
            'usuarios_ativos': User.query.filter_by(active=True).count(),
            'usuarios_inativos': User.query.filter_by(active=False).count(),
            'usuarios_recentes': User.query.filter(
                User.created_at >= datetime.utcnow().replace(day=1)
            ).count(),
            # TODO: Buscar do banco quando modelo de Contestacao for implementado
            'contestacoes_abertas': 0,  # Pendentes + Em Análise
            # TODO: Buscar do banco quando modelo de Contrato for implementado
            'contratos_ativos': 0,
            'contratos_finalizados': 0,
            # TODO: Adicionar estatísticas de tokens e transações quando implementadas
            'total_tokens_sistema': 0,
            'transacoes_mes': 0,
            'receita_mes': 0
        }
        return stats
    
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
        
        # TODO: Criar carteira para o usuário quando implementada
        
        return user
    
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
    def delete_user(user):
        """Deleta um usuário (soft delete)"""
        # TODO: Verificar se usuário tem transações pendentes
        # TODO: Transferir saldo para carteira administrativa
        
        user.active = False
        user.email = f"deleted_{user.id}_{user.email}"
        user.cpf = f"deleted_{user.id}_{user.cpf}"
        
        db.session.commit()
    
    @staticmethod
    def add_tokens_to_user(user, amount, description):
        """Adiciona tokens para um usuário"""
        # TODO: Implementar quando tivermos o sistema de carteiras
        # Por enquanto, apenas registrar a operação
        pass
    
    @staticmethod
    def get_system_config():
        """Retorna configurações do sistema"""
        # TODO: Implementar modelo SystemConfig
        # Por enquanto, retornar configurações padrão
        return {
            'taxa_sistema': 5.0,
            'valor_token': 1.0,
            'sistema_ativo': True,
            'manutencao': False,
            'observacoes': ''
        }
    
    @staticmethod
    def update_system_config(data):
        """Atualiza configurações do sistema"""
        # TODO: Implementar quando tivermos o modelo SystemConfig
        # Por enquanto, apenas simular a operação
        pass
    
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
