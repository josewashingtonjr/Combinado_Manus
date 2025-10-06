#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

from models import User, Order, Transaction, Wallet, Invite, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import json
import io
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import xlsxwriter

class ReportService:
    """Serviço para geração de relatórios do sistema"""
    
    @staticmethod
    def get_contracts_report_data(start_date=None, end_date=None, status_filter=None):
        """Obtém dados para relatório de contratos/ordens"""
        try:
            # Criar alias para o usuário prestador
            from sqlalchemy.orm import aliased
            ProviderUser = aliased(User)
            
            # Query base
            query = db.session.query(
                Order.id,
                Order.title,
                Order.description,
                Order.value,
                Order.status,
                Order.created_at,
                Order.accepted_at,
                Order.completed_at,
                User.nome.label('client_name'),
                User.email.label('client_email'),
                User.cpf.label('client_cpf'),
                func.coalesce(ProviderUser.nome, 'Não aceito').label('provider_name'),
                func.coalesce(ProviderUser.email, '').label('provider_email')
            ).join(
                User, Order.client_id == User.id
            ).outerjoin(
                ProviderUser, Order.provider_id == ProviderUser.id
            )
            
            # Aplicar filtros de data
            if start_date:
                query = query.filter(Order.created_at >= start_date)
            if end_date:
                query = query.filter(Order.created_at <= end_date)
            
            # Aplicar filtro de status
            if status_filter and status_filter != 'todos':
                if ',' in status_filter:
                    statuses = status_filter.split(',')
                    query = query.filter(Order.status.in_(statuses))
                else:
                    query = query.filter(Order.status == status_filter)
            
            # Ordenar por data de criação (mais recentes primeiro)
            orders = query.order_by(desc(Order.created_at)).all()
            
            # Estatísticas
            total_contratos = len(orders)
            valor_total = sum(order.value for order in orders)
            
            # Estatísticas por status
            status_stats = {}
            for order in orders:
                status = order.status
                if status not in status_stats:
                    status_stats[status] = {'count': 0, 'value': 0}
                status_stats[status]['count'] += 1
                status_stats[status]['value'] += order.value
            
            # Contratos por mês
            monthly_stats = {}
            for order in orders:
                month_key = order.created_at.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'count': 0, 'value': 0}
                monthly_stats[month_key]['count'] += 1
                monthly_stats[month_key]['value'] += order.value
            
            return {
                'orders': orders,
                'total_contratos': total_contratos,
                'valor_total': valor_total,
                'status_stats': status_stats,
                'monthly_stats': monthly_stats,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'status_filter': status_filter
                }
            }
        except Exception as e:
            raise ValueError(f"Erro ao gerar relatório de contratos: {str(e)}")
    
    @staticmethod
    def get_users_report_data(start_date=None, end_date=None, user_type=None, status_filter=None):
        """Obtém dados para relatório de usuários"""
        try:
            # Query base com informações de carteira
            query = db.session.query(
                User.id,
                User.nome,
                User.email,
                User.cpf,
                User.phone,
                User.roles,
                User.active,
                User.created_at,
                func.coalesce(Wallet.balance, 0).label('balance'),
                func.coalesce(Wallet.escrow_balance, 0).label('escrow_balance'),
                func.count(Transaction.id).label('transaction_count'),
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_volume')
            ).outerjoin(
                Wallet, User.id == Wallet.user_id
            ).outerjoin(
                Transaction, User.id == Transaction.user_id
            ).group_by(
                User.id, User.nome, User.email, User.cpf, User.phone,
                User.roles, User.active, User.created_at,
                Wallet.balance, Wallet.escrow_balance
            )
            
            # Aplicar filtros de data
            if start_date:
                query = query.filter(User.created_at >= start_date)
            if end_date:
                query = query.filter(User.created_at <= end_date)
            
            # Aplicar filtro de tipo de usuário
            if user_type and user_type != 'todos':
                if user_type == 'cliente':
                    query = query.filter(User.roles.contains('cliente'))
                elif user_type == 'prestador':
                    query = query.filter(User.roles.contains('prestador'))
                elif user_type == 'dual':
                    query = query.filter(and_(
                        User.roles.contains('cliente'),
                        User.roles.contains('prestador')
                    ))
            
            # Aplicar filtro de status
            if status_filter and status_filter != 'todos':
                if status_filter == 'ativo':
                    query = query.filter(User.active == True)
                elif status_filter == 'inativo':
                    query = query.filter(User.active == False)
            
            # Ordenar por data de criação (mais recentes primeiro)
            users = query.order_by(desc(User.created_at)).all()
            
            # Estatísticas gerais
            total_usuarios = len(users)
            usuarios_ativos = len([u for u in users if u.active])
            usuarios_inativos = total_usuarios - usuarios_ativos
            
            # Estatísticas por tipo
            clientes = len([u for u in users if 'cliente' in u.roles])
            prestadores = len([u for u in users if 'prestador' in u.roles])
            usuarios_dual = len([u for u in users if 'cliente' in u.roles and 'prestador' in u.roles])
            
            # Saldo total no sistema
            saldo_total = sum(u.balance + u.escrow_balance for u in users)
            volume_transacoes_total = sum(u.total_volume for u in users)
            
            # Usuários por mês
            monthly_stats = {}
            for user in users:
                month_key = user.created_at.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = 0
                monthly_stats[month_key] += 1
            
            return {
                'users': users,
                'total_usuarios': total_usuarios,
                'usuarios_ativos': usuarios_ativos,
                'usuarios_inativos': usuarios_inativos,
                'clientes': clientes,
                'prestadores': prestadores,
                'usuarios_dual': usuarios_dual,
                'saldo_total': saldo_total,
                'volume_transacoes_total': volume_transacoes_total,
                'monthly_stats': monthly_stats,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'user_type': user_type,
                    'status_filter': status_filter
                }
            }
        except Exception as e:
            raise ValueError(f"Erro ao gerar relatório de usuários: {str(e)}")
    
    @staticmethod
    def get_financial_report_data(start_date=None, end_date=None):
        """Obtém dados para relatório financeiro"""
        try:
            # Query base para transações
            query = Transaction.query
            
            # Aplicar filtros de data
            if start_date:
                query = query.filter(Transaction.created_at >= start_date)
            if end_date:
                query = query.filter(Transaction.created_at <= end_date)
            
            transactions = query.order_by(desc(Transaction.created_at)).all()
            
            # Estatísticas por tipo de transação
            transaction_stats = {}
            for transaction in transactions:
                t_type = transaction.type
                if t_type not in transaction_stats:
                    transaction_stats[t_type] = {'count': 0, 'total_amount': 0}
                transaction_stats[t_type]['count'] += 1
                transaction_stats[t_type]['total_amount'] += abs(transaction.amount)
            
            # Receita do sistema (taxas)
            receita_taxas = sum(
                abs(t.amount) for t in transactions 
                if t.type in ['taxa_sistema', 'taxa_transacao', 'taxa_saque']
            )
            
            # Volume total de transações
            volume_total = sum(abs(t.amount) for t in transactions)
            
            # Transações por mês
            monthly_stats = {}
            for transaction in transactions:
                month_key = transaction.created_at.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'count': 0, 'volume': 0, 'receita': 0}
                monthly_stats[month_key]['count'] += 1
                monthly_stats[month_key]['volume'] += abs(transaction.amount)
                if transaction.type in ['taxa_sistema', 'taxa_transacao', 'taxa_saque']:
                    monthly_stats[month_key]['receita'] += abs(transaction.amount)
            
            # Top usuários por volume de transações
            user_volumes = db.session.query(
                Transaction.user_id,
                User.nome,
                User.email,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(func.abs(Transaction.amount)).label('total_volume')
            ).join(User, Transaction.user_id == User.id)
            
            if start_date:
                user_volumes = user_volumes.filter(Transaction.created_at >= start_date)
            if end_date:
                user_volumes = user_volumes.filter(Transaction.created_at <= end_date)
            
            top_users = user_volumes.group_by(
                Transaction.user_id, User.nome, User.email
            ).order_by(desc('total_volume')).limit(10).all()
            
            return {
                'transactions': transactions,
                'total_transacoes': len(transactions),
                'volume_total': volume_total,
                'receita_taxas': receita_taxas,
                'transaction_stats': transaction_stats,
                'monthly_stats': monthly_stats,
                'top_users': top_users,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        except Exception as e:
            raise ValueError(f"Erro ao gerar relatório financeiro: {str(e)}")
    
    @staticmethod
    def get_invites_report_data(start_date=None, end_date=None, status_filter=None):
        """Obtém dados para relatório de convites"""
        try:
            # Query base
            query = db.session.query(
                Invite.id,
                Invite.service_title,
                Invite.service_description,
                Invite.original_value,
                Invite.final_value,
                Invite.status,
                Invite.created_at,
                Invite.responded_at,
                Invite.expires_at,
                User.nome.label('client_name'),
                User.email.label('client_email'),
                Invite.invited_email,
                func.coalesce(Order.id, None).label('order_id')
            ).join(
                User, Invite.client_id == User.id
            ).outerjoin(
                Order, Invite.order_id == Order.id
            )
            
            # Aplicar filtros de data
            if start_date:
                query = query.filter(Invite.created_at >= start_date)
            if end_date:
                query = query.filter(Invite.created_at <= end_date)
            
            # Aplicar filtro de status
            if status_filter and status_filter != 'todos':
                query = query.filter(Invite.status == status_filter)
            
            invites = query.order_by(desc(Invite.created_at)).all()
            
            # Estatísticas
            total_convites = len(invites)
            
            # Estatísticas por status
            status_stats = {}
            for invite in invites:
                status = invite.status
                if status not in status_stats:
                    status_stats[status] = {'count': 0, 'value': 0}
                status_stats[status]['count'] += 1
                status_stats[status]['value'] += float(invite.final_value or invite.original_value)
            
            # Taxa de conversão
            aceitos = len([i for i in invites if i.status == 'aceito'])
            convertidos = len([i for i in invites if i.status == 'convertido'])
            taxa_aceitacao = (aceitos / total_convites * 100) if total_convites > 0 else 0
            taxa_conversao = (convertidos / total_convites * 100) if total_convites > 0 else 0
            
            # Convites por mês
            monthly_stats = {}
            for invite in invites:
                month_key = invite.created_at.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'count': 0, 'aceitos': 0, 'convertidos': 0}
                monthly_stats[month_key]['count'] += 1
                if invite.status == 'aceito':
                    monthly_stats[month_key]['aceitos'] += 1
                elif invite.status == 'convertido':
                    monthly_stats[month_key]['convertidos'] += 1
            
            return {
                'invites': invites,
                'total_convites': total_convites,
                'status_stats': status_stats,
                'taxa_aceitacao': taxa_aceitacao,
                'taxa_conversao': taxa_conversao,
                'monthly_stats': monthly_stats,
                'filters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'status_filter': status_filter
                }
            }
        except Exception as e:
            raise ValueError(f"Erro ao gerar relatório de convites: {str(e)}")
    
    @staticmethod
    def export_contracts_to_excel(data):
        """Exporta relatório de contratos para Excel"""
        try:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
            
            # Planilha principal
            worksheet = workbook.add_worksheet('Contratos')
            
            # Cabeçalhos
            headers = [
                'ID', 'Título', 'Descrição', 'Valor', 'Status', 'Cliente',
                'Email Cliente', 'CPF Cliente', 'Prestador', 'Email Prestador',
                'Data Criação', 'Data Aceitação', 'Data Conclusão'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Dados
            for row, order in enumerate(data['orders'], 1):
                worksheet.write(row, 0, order.id)
                worksheet.write(row, 1, order.title)
                worksheet.write(row, 2, order.description[:100] + '...' if len(order.description) > 100 else order.description)
                worksheet.write(row, 3, order.value, currency_format)
                worksheet.write(row, 4, order.status.title())
                worksheet.write(row, 5, order.client_name)
                worksheet.write(row, 6, order.client_email)
                worksheet.write(row, 7, order.client_cpf)
                worksheet.write(row, 8, order.provider_name)
                worksheet.write(row, 9, order.provider_email)
                worksheet.write(row, 10, order.created_at, date_format)
                worksheet.write(row, 11, order.accepted_at, date_format)
                worksheet.write(row, 12, order.completed_at, date_format)
            
            # Planilha de estatísticas
            stats_worksheet = workbook.add_worksheet('Estatísticas')
            
            # Estatísticas gerais
            stats_worksheet.write(0, 0, 'Estatísticas Gerais', header_format)
            stats_worksheet.write(1, 0, 'Total de Contratos:')
            stats_worksheet.write(1, 1, data['total_contratos'])
            stats_worksheet.write(2, 0, 'Valor Total:')
            stats_worksheet.write(2, 1, data['valor_total'], currency_format)
            
            # Estatísticas por status
            row = 5
            stats_worksheet.write(row, 0, 'Estatísticas por Status', header_format)
            row += 1
            stats_worksheet.write(row, 0, 'Status', header_format)
            stats_worksheet.write(row, 1, 'Quantidade', header_format)
            stats_worksheet.write(row, 2, 'Valor Total', header_format)
            
            for status, stats in data['status_stats'].items():
                row += 1
                stats_worksheet.write(row, 0, status.title())
                stats_worksheet.write(row, 1, stats['count'])
                stats_worksheet.write(row, 2, stats['value'], currency_format)
            
            workbook.close()
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Erro ao exportar para Excel: {str(e)}")
    
    @staticmethod
    def export_users_to_excel(data):
        """Exporta relatório de usuários para Excel"""
        try:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            
            # Formatos
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({'num_format': 'R$ #,##0.00'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
            
            # Planilha principal
            worksheet = workbook.add_worksheet('Usuários')
            
            # Cabeçalhos
            headers = [
                'ID', 'Nome', 'Email', 'CPF', 'Telefone', 'Papéis',
                'Status', 'Saldo', 'Saldo Escrow', 'Total Transações',
                'Volume Total', 'Data Cadastro'
            ]
            
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Dados
            for row, user in enumerate(data['users'], 1):
                worksheet.write(row, 0, user.id)
                worksheet.write(row, 1, user.nome)
                worksheet.write(row, 2, user.email)
                worksheet.write(row, 3, user.cpf)
                worksheet.write(row, 4, user.phone or '')
                worksheet.write(row, 5, user.roles)
                worksheet.write(row, 6, 'Ativo' if user.active else 'Inativo')
                worksheet.write(row, 7, user.balance, currency_format)
                worksheet.write(row, 8, user.escrow_balance, currency_format)
                worksheet.write(row, 9, user.transaction_count)
                worksheet.write(row, 10, user.total_volume, currency_format)
                worksheet.write(row, 11, user.created_at, date_format)
            
            # Planilha de estatísticas
            stats_worksheet = workbook.add_worksheet('Estatísticas')
            
            stats_worksheet.write(0, 0, 'Estatísticas Gerais', header_format)
            stats_worksheet.write(1, 0, 'Total de Usuários:')
            stats_worksheet.write(1, 1, data['total_usuarios'])
            stats_worksheet.write(2, 0, 'Usuários Ativos:')
            stats_worksheet.write(2, 1, data['usuarios_ativos'])
            stats_worksheet.write(3, 0, 'Usuários Inativos:')
            stats_worksheet.write(3, 1, data['usuarios_inativos'])
            stats_worksheet.write(4, 0, 'Clientes:')
            stats_worksheet.write(4, 1, data['clientes'])
            stats_worksheet.write(5, 0, 'Prestadores:')
            stats_worksheet.write(5, 1, data['prestadores'])
            stats_worksheet.write(6, 0, 'Usuários Dual:')
            stats_worksheet.write(6, 1, data['usuarios_dual'])
            stats_worksheet.write(7, 0, 'Saldo Total Sistema:')
            stats_worksheet.write(7, 1, data['saldo_total'], currency_format)
            
            workbook.close()
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Erro ao exportar para Excel: {str(e)}")
    
    @staticmethod
    def export_contracts_to_pdf(data):
        """Exporta relatório de contratos para PDF"""
        try:
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("Relatório de Contratos", title_style))
            story.append(Spacer(1, 12))
            
            # Resumo
            summary_data = [
                ['Total de Contratos:', str(data['total_contratos'])],
                ['Valor Total:', f"R$ {data['valor_total']:,.2f}"],
                ['Período:', f"{data['filters']['start_date'] or 'Início'} até {data['filters']['end_date'] or 'Hoje'}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Tabela de contratos (primeiros 50)
            story.append(Paragraph("Detalhes dos Contratos", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            table_data = [['ID', 'Título', 'Cliente', 'Valor', 'Status', 'Data']]
            
            for order in data['orders'][:50]:  # Limitar a 50 para não quebrar o PDF
                table_data.append([
                    str(order.id),
                    order.title[:30] + '...' if len(order.title) > 30 else order.title,
                    order.client_name[:20] + '...' if len(order.client_name) > 20 else order.client_name,
                    f"R$ {order.value:,.2f}",
                    order.status.title(),
                    order.created_at.strftime('%d/%m/%Y')
                ])
            
            contracts_table = Table(table_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
            contracts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(contracts_table)
            
            if len(data['orders']) > 50:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Nota: Mostrando apenas os primeiros 50 contratos de {len(data['orders'])} total.", styles['Normal']))
            
            doc.build(story)
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Erro ao exportar para PDF: {str(e)}")
    
    @staticmethod
    def export_users_to_pdf(data):
        """Exporta relatório de usuários para PDF"""
        try:
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("Relatório de Usuários", title_style))
            story.append(Spacer(1, 12))
            
            # Resumo
            summary_data = [
                ['Total de Usuários:', str(data['total_usuarios'])],
                ['Usuários Ativos:', str(data['usuarios_ativos'])],
                ['Clientes:', str(data['clientes'])],
                ['Prestadores:', str(data['prestadores'])],
                ['Saldo Total Sistema:', f"R$ {data['saldo_total']:,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Tabela de usuários (primeiros 50)
            story.append(Paragraph("Detalhes dos Usuários", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            table_data = [['ID', 'Nome', 'Email', 'Papéis', 'Saldo', 'Status']]
            
            for user in data['users'][:50]:  # Limitar a 50
                table_data.append([
                    str(user.id),
                    user.nome[:25] + '...' if len(user.nome) > 25 else user.nome,
                    user.email[:30] + '...' if len(user.email) > 30 else user.email,
                    user.roles,
                    f"R$ {user.balance:,.2f}",
                    'Ativo' if user.active else 'Inativo'
                ])
            
            users_table = Table(table_data, colWidths=[0.5*inch, 1.8*inch, 2*inch, 1*inch, 1*inch, 0.7*inch])
            users_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(users_table)
            
            if len(data['users']) > 50:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Nota: Mostrando apenas os primeiros 50 usuários de {len(data['users'])} total.", styles['Normal']))
            
            doc.build(story)
            output.seek(0)
            
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Erro ao exportar para PDF: {str(e)}")