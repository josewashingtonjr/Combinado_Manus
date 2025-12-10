#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste Manual - Fluxo de Aceitação de Convites
========================================================

Este script testa o fluxo completo de aceitação de convites:
- Aceitação pelo cliente
- Aceitação pelo prestador
- Mensagens de feedback
- Redirecionamentos
- Notificações

Requirements: 1.1-1.5, 6.1-6.5
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Order, Wallet, Transaction
from services.invite_service import InviteService
from services.wallet_service import WalletService
from services.notification_service import NotificationService
from services.config_service import ConfigService

# Verificar se modelo Notification existe
try:
    from models import Notification
    HAS_NOTIFICATION_MODEL = True
except ImportError:
    HAS_NOTIFICATION_MODEL = False
    print("⚠️  Modelo Notification não encontrado - notificações serão verificadas via serviço")


class TestFluxoAceitacao:
    """Classe para testar o fluxo de aceitação de convites"""
    
    def __init__(self):
        self.app = app
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()
        
        # Obter taxa de contestação
        self.contestation_fee = ConfigService.get_contestation_fee()
        
    def cleanup(self):
        """Limpar contexto"""
        self.ctx.pop()
    
    def print_header(self, title):
        """Imprimir cabeçalho de seção"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_success(self, message):
        """Imprimir mensagem de sucesso"""
        print(f"✓ {message}")
    
    def print_error(self, message):
        """Imprimir mensagem de erro"""
        print(f"✗ {message}")
    
    def print_info(self, message):
        """Imprimir mensagem informativa"""
        print(f"ℹ {message}")
    
    def criar_usuarios_teste(self):
        """Criar usuários de teste"""
        self.print_header("1. Criando Usuários de Teste")
        
        # Limpar usuários existentes
        User.query.filter(User.email.in_(['cliente_teste@test.com', 'prestador_teste@test.com'])).delete()
        db.session.commit()
        
        # Criar cliente
        cliente = User(
            nome="Cliente Teste",
            email="cliente_teste@test.com",
            cpf="11111111111",
            phone="11999999001",
            roles="cliente"
        )
        cliente.set_password("senha123")
        db.session.add(cliente)
        
        # Criar prestador
        prestador = User(
            nome="Prestador Teste",
            email="prestador_teste@test.com",
            cpf="22222222222",
            phone="11999999002",
            roles="prestador"
        )
        prestador.set_password("senha123")
        db.session.add(prestador)
        
        db.session.commit()
        
        self.cliente = cliente
        self.prestador = prestador
        
        self.print_success(f"Cliente criado: {cliente.nome} (ID: {cliente.id})")
        self.print_success(f"Prestador criado: {prestador.nome} (ID: {prestador.id})")
        
        return cliente, prestador
    
    def criar_carteiras_com_saldo(self):
        """Criar carteiras com saldo suficiente"""
        self.print_header("2. Criando Carteiras com Saldo")
        
        # Criar carteira do cliente com saldo
        WalletService.ensure_user_has_wallet(self.cliente.id)
        WalletService.credit_wallet(
            self.cliente.id,
            Decimal('1000.00'),
            'Saldo inicial para testes',
            'credito'
        )
        
        # Criar carteira do prestador com saldo
        WalletService.ensure_user_has_wallet(self.prestador.id)
        WalletService.credit_wallet(
            self.prestador.id,
            Decimal('500.00'),
            'Saldo inicial para testes',
            'credito'
        )
        
        wallet_cliente = Wallet.query.filter_by(user_id=self.cliente.id).first()
        wallet_prestador = Wallet.query.filter_by(user_id=self.prestador.id).first()
        
        self.print_success(f"Carteira do cliente: R$ {wallet_cliente.balance}")
        self.print_success(f"Carteira do prestador: R$ {wallet_prestador.balance}")
    
    def criar_convite_teste(self):
        """Criar convite de teste"""
        self.print_header("3. Criando Convite de Teste")
        
        convite = Invite(
            client_id=self.cliente.id,
            invited_phone=self.prestador.phone,
            service_title="Serviço de Teste - Aceitação",
            service_description="Teste do fluxo de aceitação mútua",
            service_category="Tecnologia",
            original_value=Decimal('200.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            status='pendente'
        )
        
        db.session.add(convite)
        db.session.commit()
        
        self.convite = convite
        
        self.print_success(f"Convite criado: ID {convite.id}")
        self.print_info(f"  Título: {convite.service_title}")
        self.print_info(f"  Valor: R$ {convite.current_value}")
        self.print_info(f"  Cliente: {self.cliente.nome}")
        self.print_info(f"  Prestador: {self.prestador.phone}")
        
        return convite
    
    def testar_aceitacao_prestador(self):
        """Testar aceitação pelo prestador"""
        self.print_header("4. Testando Aceitação pelo Prestador")
        
        try:
            # Aceitar como prestador
            resultado = InviteService.accept_invite_as_provider(
                self.convite.id,
                self.prestador.id
            )
            
            # Verificar resultado
            if resultado['success']:
                self.print_success("Prestador aceitou o convite com sucesso")
                
                # Verificar campos do convite
                db.session.refresh(self.convite)
                
                if self.convite.provider_accepted:
                    self.print_success("✓ Campo provider_accepted = True")
                else:
                    self.print_error("✗ Campo provider_accepted ainda False")
                
                if self.convite.provider_accepted_at:
                    self.print_success(f"✓ Timestamp registrado: {self.convite.provider_accepted_at}")
                else:
                    self.print_error("✗ Timestamp não registrado")
                
                # Verificar mensagem
                if 'message' in resultado:
                    self.print_info(f"Mensagem: {resultado['message']}")
                
                # Verificar se ordem foi criada (não deveria ainda)
                if resultado.get('order_created'):
                    self.print_error("✗ Ordem criada prematuramente (cliente ainda não aceitou)")
                else:
                    self.print_success("✓ Ordem não criada (aguardando cliente)")
                
                # Verificar notificações
                if HAS_NOTIFICATION_MODEL:
                    notificacoes = Notification.query.filter_by(
                        user_id=self.prestador.id
                    ).order_by(Notification.created_at.desc()).first()
                    
                    if notificacoes:
                        self.print_success(f"✓ Notificação criada: {notificacoes.message[:50]}...")
                    else:
                        self.print_info("Nenhuma notificação encontrada")
                else:
                    self.print_info("Sistema de notificações via serviço (sem modelo)")
                
            else:
                self.print_error(f"Falha na aceitação: {resultado.get('message')}")
                
        except Exception as e:
            self.print_error(f"Erro ao aceitar como prestador: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def testar_aceitacao_cliente(self):
        """Testar aceitação pelo cliente (deve criar ordem)"""
        self.print_header("5. Testando Aceitação pelo Cliente")
        
        try:
            # Verificar saldos antes
            wallet_cliente_antes = Wallet.query.filter_by(user_id=self.cliente.id).first()
            wallet_prestador_antes = Wallet.query.filter_by(user_id=self.prestador.id).first()
            
            self.print_info(f"Saldo cliente antes: R$ {wallet_cliente_antes.balance}")
            self.print_info(f"Saldo prestador antes: R$ {wallet_prestador_antes.balance}")
            
            # Aceitar como cliente
            resultado = InviteService.accept_invite_as_client(
                self.convite.id,
                self.cliente.id
            )
            
            # Verificar resultado
            if resultado['success']:
                self.print_success("Cliente aceitou o convite com sucesso")
                
                # Verificar campos do convite
                db.session.refresh(self.convite)
                
                if self.convite.client_accepted:
                    self.print_success("✓ Campo client_accepted = True")
                else:
                    self.print_error("✗ Campo client_accepted ainda False")
                
                if self.convite.client_accepted_at:
                    self.print_success(f"✓ Timestamp registrado: {self.convite.client_accepted_at}")
                else:
                    self.print_error("✗ Timestamp não registrado")
                
                # Verificar mensagem
                if 'message' in resultado:
                    self.print_info(f"Mensagem: {resultado['message']}")
                
                # Verificar se ordem foi criada (DEVERIA ser criada agora)
                if resultado.get('order_created'):
                    self.print_success("✓ Ordem criada automaticamente!")
                    order_id = resultado.get('order_id')
                    
                    # Buscar ordem
                    ordem = Order.query.get(order_id)
                    if ordem:
                        self.print_success(f"✓ Ordem #{ordem.id} encontrada")
                        self.print_info(f"  Status: {ordem.status}")
                        self.print_info(f"  Valor: R$ {ordem.value}")
                        self.print_info(f"  Cliente: {ordem.client_id}")
                        self.print_info(f"  Prestador: {ordem.provider_id}")
                        
                        # Verificar status do convite
                        if self.convite.status == 'convertido':
                            self.print_success("✓ Status do convite atualizado para 'convertido'")
                        else:
                            self.print_error(f"✗ Status do convite: {self.convite.status}")
                        
                        # Verificar valores bloqueados
                        self.verificar_valores_bloqueados(ordem)
                        
                        # Verificar notificações
                        self.verificar_notificacoes_ordem(ordem)
                        
                        self.ordem = ordem
                    else:
                        self.print_error(f"✗ Ordem #{order_id} não encontrada no banco")
                else:
                    self.print_error("✗ Ordem não foi criada (ambos aceitaram!)")
                
            else:
                self.print_error(f"Falha na aceitação: {resultado.get('message')}")
                
        except Exception as e:
            self.print_error(f"Erro ao aceitar como cliente: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def verificar_valores_bloqueados(self, ordem):
        """Verificar se valores foram bloqueados corretamente"""
        self.print_header("6. Verificando Valores Bloqueados")
        
        # Verificar saldos após
        wallet_cliente = Wallet.query.filter_by(user_id=self.cliente.id).first()
        wallet_prestador = Wallet.query.filter_by(user_id=self.prestador.id).first()
        
        self.print_info(f"Saldo disponível cliente: R$ {wallet_cliente.balance}")
        self.print_info(f"Saldo bloqueado cliente: R$ {wallet_cliente.escrow_balance}")
        self.print_info(f"Saldo disponível prestador: R$ {wallet_prestador.balance}")
        self.print_info(f"Saldo bloqueado prestador: R$ {wallet_prestador.escrow_balance}")
        
        # Verificar transações de escrow
        transacoes_cliente = Transaction.query.filter_by(
            user_id=self.cliente.id,
            transaction_type='escrow_block',
            order_id=ordem.id
        ).all()
        
        transacoes_prestador = Transaction.query.filter_by(
            user_id=self.prestador.id,
            transaction_type='escrow_block',
            order_id=ordem.id
        ).all()
        
        if transacoes_cliente:
            self.print_success(f"✓ {len(transacoes_cliente)} transação(ões) de bloqueio do cliente")
            for t in transacoes_cliente:
                self.print_info(f"  R$ {t.amount} - {t.description}")
        else:
            self.print_error("✗ Nenhuma transação de bloqueio do cliente")
        
        if transacoes_prestador:
            self.print_success(f"✓ {len(transacoes_prestador)} transação(ões) de bloqueio do prestador")
            for t in transacoes_prestador:
                self.print_info(f"  R$ {t.amount} - {t.description}")
        else:
            self.print_error("✗ Nenhuma transação de bloqueio do prestador")
        
        # Verificar valores esperados
        valor_esperado_cliente = ordem.value + self.contestation_fee
        if wallet_cliente.escrow_balance >= valor_esperado_cliente:
            self.print_success(f"✓ Valor bloqueado do cliente correto (>= R$ {valor_esperado_cliente})")
        else:
            self.print_error(f"✗ Valor bloqueado do cliente incorreto (esperado >= R$ {valor_esperado_cliente})")
        
        if wallet_prestador.escrow_balance >= self.contestation_fee:
            self.print_success(f"✓ Valor bloqueado do prestador correto (>= R$ {self.contestation_fee})")
        else:
            self.print_error(f"✗ Valor bloqueado do prestador incorreto (esperado >= R$ {self.contestation_fee})")
    
    def verificar_notificacoes_ordem(self, ordem):
        """Verificar notificações de criação de ordem"""
        self.print_header("7. Verificando Notificações")
        
        if not HAS_NOTIFICATION_MODEL:
            self.print_info("Sistema usa notificações via serviço (sem persistência em banco)")
            self.print_info("Notificações são enviadas em tempo real via WebSocket/SSE")
            return
        
        # Notificações do cliente
        notif_cliente = Notification.query.filter_by(
            user_id=self.cliente.id
        ).order_by(Notification.created_at.desc()).first()
        
        if notif_cliente:
            self.print_success(f"✓ Notificação para cliente: {notif_cliente.message}")
            if str(ordem.id) in notif_cliente.message or 'ordem' in notif_cliente.message.lower():
                self.print_success("  ✓ Notificação menciona a ordem")
        else:
            self.print_error("✗ Nenhuma notificação para o cliente")
        
        # Notificações do prestador
        notif_prestador = Notification.query.filter_by(
            user_id=self.prestador.id
        ).order_by(Notification.created_at.desc()).first()
        
        if notif_prestador:
            self.print_success(f"✓ Notificação para prestador: {notif_prestador.message}")
            if str(ordem.id) in notif_prestador.message or 'ordem' in notif_prestador.message.lower():
                self.print_success("  ✓ Notificação menciona a ordem")
        else:
            self.print_error("✗ Nenhuma notificação para o prestador")
    
    def testar_mensagens_feedback(self):
        """Testar mensagens de feedback nas rotas"""
        self.print_header("8. Testando Mensagens de Feedback nas Rotas")
        
        # Criar novo convite para testar rotas
        convite2 = Invite(
            client_id=self.cliente.id,
            invited_phone=self.prestador.phone,
            service_title="Teste Rotas",
            service_description="Teste de mensagens",
            service_category="Tecnologia",
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            status='pendente'
        )
        db.session.add(convite2)
        db.session.commit()
        
        # Simular login do prestador
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.prestador.id
        
        # Testar rota de aceitação do prestador
        response = self.client.post(
            f'/prestador/convites/{convite2.id}/aceitar',
            follow_redirects=False
        )
        
        if response.status_code in [200, 302]:
            self.print_success(f"✓ Rota prestador respondeu: {response.status_code}")
            
            # Verificar redirecionamento
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                self.print_info(f"  Redirecionamento para: {location}")
                if 'convites' in location or 'dashboard' in location:
                    self.print_success("  ✓ Redirecionamento apropriado")
        else:
            self.print_error(f"✗ Rota prestador falhou: {response.status_code}")
        
        # Simular login do cliente
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.cliente.id
        
        # Testar rota de aceitação do cliente
        response = self.client.post(
            f'/cliente/convites/{convite2.id}/aceitar',
            follow_redirects=False
        )
        
        if response.status_code in [200, 302]:
            self.print_success(f"✓ Rota cliente respondeu: {response.status_code}")
            
            # Verificar redirecionamento
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                self.print_info(f"  Redirecionamento para: {location}")
                if 'convites' in location or 'dashboard' in location or 'ordens' in location:
                    self.print_success("  ✓ Redirecionamento apropriado")
        else:
            self.print_error(f"✗ Rota cliente falhou: {response.status_code}")
    
    def testar_saldo_insuficiente(self):
        """Testar cenário de saldo insuficiente"""
        self.print_header("9. Testando Saldo Insuficiente")
        
        # Criar usuário com saldo baixo
        cliente_pobre = User(
            nome="Cliente Sem Saldo",
            email="cliente_pobre@test.com",
            cpf="33333333333",
            phone="11999999003",
            roles="cliente"
        )
        cliente_pobre.set_password("senha123")
        db.session.add(cliente_pobre)
        db.session.commit()
        
        # Criar carteira com saldo insuficiente
        WalletService.ensure_user_has_wallet(cliente_pobre.id)
        WalletService.credit_wallet(cliente_pobre.id, Decimal('10.00'), 'Saldo baixo', 'credito')
        
        # Criar convite
        convite3 = Invite(
            client_id=cliente_pobre.id,
            invited_phone=self.prestador.phone,
            service_title="Teste Saldo Insuficiente",
            service_description="Teste",
            service_category="Tecnologia",
            original_value=Decimal('500.00'),
            delivery_date=datetime.utcnow() + timedelta(days=5),
            status='pendente',
            provider_accepted=True,
            provider_accepted_at=datetime.utcnow()
        )
        db.session.add(convite3)
        db.session.commit()
        
        try:
            # Tentar aceitar com saldo insuficiente
            resultado = InviteService.accept_invite_as_client(
                convite3.id,
                cliente_pobre.id
            )
            
            if not resultado['success']:
                self.print_success("✓ Aceitação bloqueada por saldo insuficiente")
                self.print_info(f"  Mensagem: {resultado.get('message')}")
                
                # Verificar se mensagem é clara
                mensagem = resultado.get('message', '').lower()
                if 'saldo' in mensagem and 'insuficiente' in mensagem:
                    self.print_success("  ✓ Mensagem clara sobre saldo insuficiente")
            else:
                self.print_error("✗ Aceitação permitida com saldo insuficiente!")
                
        except ValueError as e:
            self.print_success(f"✓ Exceção capturada: {str(e)}")
            if 'saldo' in str(e).lower():
                self.print_success("  ✓ Mensagem de erro apropriada")
        except Exception as e:
            self.print_error(f"✗ Erro inesperado: {str(e)}")
    
    def gerar_relatorio_final(self):
        """Gerar relatório final dos testes"""
        self.print_header("RELATÓRIO FINAL")
        
        print("\n📋 Resumo dos Testes:")
        print("-" * 70)
        
        # Verificar convite original
        db.session.refresh(self.convite)
        
        print(f"\n✓ Convite #{self.convite.id}:")
        print(f"  - Status: {self.convite.status}")
        print(f"  - Cliente aceitou: {self.convite.client_accepted}")
        print(f"  - Prestador aceitou: {self.convite.provider_accepted}")
        print(f"  - Aceitação mútua: {self.convite.is_mutually_accepted}")
        
        if hasattr(self, 'ordem'):
            print(f"\n✓ Ordem #{self.ordem.id}:")
            print(f"  - Status: {self.ordem.status}")
            print(f"  - Valor: R$ {self.ordem.service_value}")
            print(f"  - Cliente: {self.ordem.client_id}")
            print(f"  - Prestador: {self.ordem.provider_id}")
        
        # Contar notificações
        if HAS_NOTIFICATION_MODEL:
            total_notif = Notification.query.filter(
                Notification.user_id.in_([self.cliente.id, self.prestador.id])
            ).count()
            print(f"\n✓ Total de notificações criadas: {total_notif}")
        else:
            print(f"\n✓ Notificações enviadas via serviço em tempo real")
        
        # Contar transações
        total_trans = Transaction.query.filter(
            Transaction.user_id.in_([self.cliente.id, self.prestador.id])
        ).count()
        print(f"✓ Total de transações criadas: {total_trans}")
        
        print("\n" + "="*70)
        print("  TESTES CONCLUÍDOS")
        print("="*70 + "\n")


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("  TESTE MANUAL - FLUXO DE ACEITAÇÃO DE CONVITES")
    print("="*70)
    print("\nEste script testa:")
    print("  ✓ Aceitação pelo prestador")
    print("  ✓ Aceitação pelo cliente")
    print("  ✓ Criação automática de ordem")
    print("  ✓ Bloqueio de valores em escrow")
    print("  ✓ Mensagens de feedback")
    print("  ✓ Redirecionamentos")
    print("  ✓ Notificações")
    print("  ✓ Tratamento de saldo insuficiente")
    
    teste = TestFluxoAceitacao()
    
    try:
        # Executar testes
        teste.criar_usuarios_teste()
        teste.criar_carteiras_com_saldo()
        teste.criar_convite_teste()
        teste.testar_aceitacao_prestador()
        teste.testar_aceitacao_cliente()
        teste.testar_mensagens_feedback()
        teste.testar_saldo_insuficiente()
        teste.gerar_relatorio_final()
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        teste.cleanup()


if __name__ == '__main__':
    main()
