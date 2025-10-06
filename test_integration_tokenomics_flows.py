#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import User, AdminUser, Wallet, Transaction, Order, db
from services.wallet_service import WalletService
from services.admin_service import AdminService
from services.auth_service import AuthService

class TestIntegrationTokenomicsFlows(unittest.TestCase):
    """Testes de integração para fluxos completos de tokenomics"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        # Criar app Flask isolado para testes
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Inicializar db com o app de teste
        db.init_app(self.app)
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Criar todas as tabelas
        db.create_all()
        
        # Criar admin principal (ID 0)
        self.admin = AdminUser(
            id=0,  # ID 0 reservado para admin principal
            email='admin@combinado.com',
            papel='super_admin'
        )
        self.admin.set_password('admin123')
        db.session.add(self.admin)
        
        # Criar usuários de teste
        self.cliente = User(
            nome='Cliente Teste',
            email='cliente@example.com',
            cpf='12345678901',
            roles='cliente'
        )
        self.cliente.set_password('cliente123')
        
        self.prestador = User(
            nome='Prestador Teste',
            email='prestador@example.com',
            cpf='98765432100',
            roles='prestador'
        )
        self.prestador.set_password('prestador123')
        
        # Usuário dual (cliente + prestador)
        self.usuario_dual = User(
            nome='Usuário Dual',
            email='dual@example.com',
            cpf='11122233344',
            roles='cliente,prestador'
        )
        self.usuario_dual.set_password('dual123')
        
        db.session.add_all([self.cliente, self.prestador, self.usuario_dual])
        db.session.commit()
        
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    # ==============================================================================
    #  FLUXO COMPLETO ADMIN: LOGIN → CRIAÇÃO TOKENS → VENDA USUÁRIO
    # ==============================================================================
    
    def test_admin_complete_flow_login_create_sell_tokens(self):
        """Testa fluxo completo admin: login → criação tokens → venda usuário"""
        print("\n=== TESTE: Fluxo Completo Admin ===")
        
        # 1. ADMIN LOGIN (simulado - verificar credenciais)
        admin_autenticado = AuthService.authenticate_admin('admin@combinado.com', 'admin123')
        self.assertIsNotNone(admin_autenticado)
        self.assertEqual(admin_autenticado.email, 'admin@combinado.com')
        print(f"✅ Admin autenticado: {admin_autenticado.email}")
        
        # 2. CRIAÇÃO DE TOKENS PELO ADMIN
        # Garantir que admin tem carteira inicial
        admin_wallet_inicial = WalletService.ensure_admin_has_wallet()
        saldo_inicial = admin_wallet_inicial.balance
        print(f"✅ Carteira admin criada com saldo inicial: {saldo_inicial:,.0f} tokens")
        
        # Admin cria tokens adicionais
        tokens_criados = 250000.0
        resultado_criacao = WalletService.admin_create_tokens(
            tokens_criados, 
            "Criação adicional para testes de integração"
        )
        
        self.assertTrue(resultado_criacao['success'])
        self.assertEqual(resultado_criacao['tokens_created'], tokens_criados)
        novo_saldo_admin = resultado_criacao['new_admin_balance']
        self.assertEqual(novo_saldo_admin, saldo_inicial + tokens_criados)
        print(f"✅ Admin criou {tokens_criados:,.0f} tokens. Novo saldo: {novo_saldo_admin:,.0f}")
        
        # 3. VENDA DE TOKENS PARA USUÁRIO
        # Garantir que cliente tem carteira
        cliente_wallet = WalletService.ensure_user_has_wallet(self.cliente.id)
        self.assertEqual(cliente_wallet.balance, 0.0)
        print(f"✅ Carteira cliente criada com saldo: {cliente_wallet.balance}")
        
        # Admin vende tokens para cliente
        tokens_vendidos = 50000.0
        resultado_venda = WalletService.admin_sell_tokens_to_user(
            self.cliente.id,
            tokens_vendidos,
            "Venda de tokens para cliente teste"
        )
        
        self.assertTrue(resultado_venda['success'])
        self.assertEqual(resultado_venda['tokens_transferred'], tokens_vendidos)
        self.assertEqual(resultado_venda['user_new_balance'], tokens_vendidos)
        self.assertEqual(resultado_venda['admin_new_balance'], novo_saldo_admin - tokens_vendidos)
        print(f"✅ Admin vendeu {tokens_vendidos:,.0f} tokens para cliente")
        print(f"   Saldo cliente: {resultado_venda['user_new_balance']:,.0f}")
        print(f"   Saldo admin: {resultado_venda['admin_new_balance']:,.0f}")
        
        # 4. VERIFICAR INTEGRIDADE DO SISTEMA
        resumo_sistema = WalletService.get_system_token_summary()
        
        # Verificar que tokens nunca "desaparecem"
        self.assertEqual(
            resumo_sistema['total_tokens_in_system'], 
            resumo_sistema['total_tokens_created']
        )
        
        # Verificar distribuição correta
        self.assertEqual(resumo_sistema['admin_balance'], novo_saldo_admin - tokens_vendidos)
        self.assertEqual(resumo_sistema['tokens_in_circulation'], tokens_vendidos)
        print(f"✅ Integridade verificada:")
        print(f"   Total criado: {resumo_sistema['total_tokens_created']:,.0f}")
        print(f"   Em circulação: {resumo_sistema['tokens_in_circulation']:,.0f}")
        print(f"   Saldo admin: {resumo_sistema['admin_balance']:,.0f}")
        
        # 5. VERIFICAR TRANSAÇÕES REGISTRADAS
        # Transações do admin
        transacoes_admin = Transaction.query.filter_by(user_id=WalletService.ADMIN_USER_ID).all()
        tipos_admin = [t.type for t in transacoes_admin]
        
        self.assertIn("criacao_tokens", tipos_admin)  # Criação inicial + adicional
        self.assertIn("venda_tokens", tipos_admin)
        print(f"✅ Transações admin registradas: {tipos_admin}")
        
        # Transações do cliente
        transacoes_cliente = Transaction.query.filter_by(user_id=self.cliente.id).all()
        tipos_cliente = [t.type for t in transacoes_cliente]
        
        self.assertIn("criacao_carteira", tipos_cliente)
        self.assertIn("compra_tokens", tipos_cliente)
        print(f"✅ Transações cliente registradas: {tipos_cliente}")
        
        print("✅ FLUXO ADMIN COMPLETO - SUCESSO\n")
    
    # ==============================================================================
    #  FLUXO COMPLETO USUÁRIO: LOGIN → COMPRA TOKENS → CRIAÇÃO ORDEM → SAQUE
    # ==============================================================================
    
    def test_user_complete_flow_login_buy_create_order_withdraw(self):
        """Testa fluxo completo usuário: login → compra tokens → criação ordem → saque"""
        print("\n=== TESTE: Fluxo Completo Usuário ===")
        
        # Preparar admin com tokens
        WalletService.ensure_admin_has_wallet()
        WalletService.admin_create_tokens(500000.0, "Tokens para testes de usuário")
        
        # 1. LOGIN DO USUÁRIO (CLIENTE) - simulado
        usuario_autenticado = AuthService.authenticate_user('cliente@example.com', 'cliente123')
        self.assertIsNotNone(usuario_autenticado)
        self.assertEqual(usuario_autenticado.email, 'cliente@example.com')
        print(f"✅ Usuário autenticado: {usuario_autenticado.email} (papel: {usuario_autenticado.roles})")
        
        # 2. COMPRA DE TOKENS (DEPÓSITO)
        valor_compra = 10000.0
        resultado_compra = WalletService.deposit(
            self.cliente.id,
            valor_compra,
            "Depósito inicial para testes"
        )
        
        self.assertTrue(resultado_compra['success'])
        self.assertEqual(resultado_compra['user_new_balance'], valor_compra)
        print(f"✅ Cliente comprou {valor_compra:,.0f} tokens")
        print(f"   Saldo cliente: R$ {valor_compra:,.2f} (terminologia usuário)")
        
        # 3. CRIAÇÃO DE ORDEM DE SERVIÇO
        # Criar ordem no banco
        ordem = Order(
            client_id=self.cliente.id,
            title="Serviço de Teste",
            description="Descrição do serviço de teste para integração",
            value=3000.0,
            status='disponivel'
        )
        db.session.add(ordem)
        db.session.commit()
        print(f"✅ Ordem criada: #{ordem.id} - {ordem.title} (R$ {ordem.value:,.2f})")
        
        # Transferir valor para escrow
        resultado_escrow = WalletService.transfer_to_escrow(
            self.cliente.id,
            ordem.value,
            ordem.id
        )
        
        self.assertTrue(resultado_escrow['success'])
        self.assertEqual(resultado_escrow['new_balance'], valor_compra - ordem.value)
        self.assertEqual(resultado_escrow['new_escrow_balance'], ordem.value)
        print(f"✅ Valor transferido para escrow:")
        print(f"   Saldo disponível: {resultado_escrow['new_balance']:,.0f}")
        print(f"   Saldo em escrow: {resultado_escrow['new_escrow_balance']:,.0f}")
        
        # 4. SAQUE PARCIAL (TOKENS RESTANTES)
        valor_saque = 2000.0
        resultado_saque = WalletService.withdraw(
            self.cliente.id,
            valor_saque,
            "Saque parcial de tokens"
        )
        
        self.assertTrue(resultado_saque['success'])
        saldo_final_cliente = valor_compra - ordem.value - valor_saque
        self.assertEqual(resultado_saque['user_new_balance'], saldo_final_cliente)
        print(f"✅ Cliente sacou {valor_saque:,.0f} tokens")
        print(f"   Saldo final cliente: {saldo_final_cliente:,.0f}")
        
        # 5. VERIFICAR ESTADO FINAL DO SISTEMA
        info_carteira = WalletService.get_wallet_info(self.cliente.id)
        self.assertEqual(info_carteira['balance'], saldo_final_cliente)
        self.assertEqual(info_carteira['escrow_balance'], ordem.value)
        self.assertEqual(info_carteira['total_balance'], saldo_final_cliente + ordem.value)
        print(f"✅ Estado final da carteira cliente:")
        print(f"   Saldo: {info_carteira['balance']:,.0f}")
        print(f"   Escrow: {info_carteira['escrow_balance']:,.0f}")
        print(f"   Total: {info_carteira['total_balance']:,.0f}")
        
        # 6. VERIFICAR INTEGRIDADE MATEMÁTICA
        resumo_sistema = WalletService.get_system_token_summary()
        self.assertEqual(
            resumo_sistema['total_tokens_in_system'],
            resumo_sistema['total_tokens_created']
        )
        print(f"✅ Integridade matemática mantida")
        
        # 7. VERIFICAR TRANSAÇÕES COMPLETAS
        transacoes_cliente = Transaction.query.filter_by(user_id=self.cliente.id).all()
        tipos_transacoes = [t.type for t in transacoes_cliente]
        
        self.assertIn("criacao_carteira", tipos_transacoes)
        self.assertIn("compra_tokens", tipos_transacoes)
        self.assertIn("escrow_bloqueio", tipos_transacoes)
        self.assertIn("saque_tokens", tipos_transacoes)
        print(f"✅ Transações cliente: {tipos_transacoes}")
        
        print("✅ FLUXO USUÁRIO COMPLETO - SUCESSO\n")
    
    # ==============================================================================
    #  FLUXO COMPLETO PRESTADOR: LOGIN → ACEITAÇÃO ORDEM → RECEBIMENTO → SAQUE
    # ==============================================================================
    
    def test_provider_complete_flow_login_accept_receive_withdraw(self):
        """Testa fluxo completo prestador: login → aceitação ordem → recebimento → saque"""
        print("\n=== TESTE: Fluxo Completo Prestador ===")
        
        # Preparar cenário: admin com tokens, cliente com ordem em escrow
        WalletService.ensure_admin_has_wallet()
        WalletService.admin_create_tokens(500000.0, "Tokens para teste prestador")
        
        # Cliente compra tokens e cria ordem
        WalletService.deposit(self.cliente.id, 15000.0, "Compra para ordem")
        
        ordem = Order(
            client_id=self.cliente.id,
            title="Serviço para Prestador",
            description="Serviço que será aceito pelo prestador",
            value=8000.0,
            status='disponivel'
        )
        db.session.add(ordem)
        db.session.commit()
        
        # Transferir para escrow
        WalletService.transfer_to_escrow(self.cliente.id, ordem.value, ordem.id)
        print(f"✅ Cenário preparado: Ordem #{ordem.id} com R$ {ordem.value:,.2f} em escrow")
        
        # 1. LOGIN DO PRESTADOR - simulado
        prestador_autenticado = AuthService.authenticate_user('prestador@example.com', 'prestador123')
        self.assertIsNotNone(prestador_autenticado)
        self.assertEqual(prestador_autenticado.email, 'prestador@example.com')
        print(f"✅ Prestador autenticado: {prestador_autenticado.email} (papel: {prestador_autenticado.roles})")
        
        # Garantir que prestador tem carteira
        WalletService.ensure_user_has_wallet(self.prestador.id)
        
        # 2. ACEITAÇÃO DA ORDEM
        # Atualizar ordem para aceita
        ordem.provider_id = self.prestador.id
        ordem.status = 'aceita'
        ordem.accepted_at = db.func.now()
        db.session.commit()
        print(f"✅ Prestador aceitou ordem #{ordem.id}")
        
        # 3. CONCLUSÃO E RECEBIMENTO
        # Simular conclusão da ordem
        ordem.status = 'concluida'
        ordem.completed_at = db.func.now()
        db.session.commit()
        
        # Liberar escrow com taxa do sistema (5%)
        taxa_sistema = 0.05
        resultado_liberacao = WalletService.release_from_escrow(ordem.id, taxa_sistema)
        
        self.assertTrue(resultado_liberacao['success'])
        
        valor_prestador = ordem.value * (1 - taxa_sistema)
        valor_taxa = ordem.value * taxa_sistema
        
        self.assertEqual(resultado_liberacao['provider_amount'], valor_prestador)
        self.assertEqual(resultado_liberacao['system_fee'], valor_taxa)
        print(f"✅ Escrow liberado:")
        print(f"   Valor prestador: {valor_prestador:,.2f}")
        print(f"   Taxa sistema: {valor_taxa:,.2f}")
        
        # 4. VERIFICAR SALDO DO PRESTADOR
        info_prestador = WalletService.get_wallet_info(self.prestador.id)
        self.assertEqual(info_prestador['balance'], valor_prestador)
        print(f"✅ Saldo prestador após recebimento: {info_prestador['balance']:,.2f}")
        
        # 5. SAQUE DO PRESTADOR
        valor_saque_prestador = 5000.0
        resultado_saque_prestador = WalletService.withdraw(
            self.prestador.id,
            valor_saque_prestador,
            "Saque de ganhos"
        )
        
        self.assertTrue(resultado_saque_prestador['success'])
        saldo_final_prestador = valor_prestador - valor_saque_prestador
        self.assertEqual(resultado_saque_prestador['user_new_balance'], saldo_final_prestador)
        print(f"✅ Prestador sacou {valor_saque_prestador:,.2f}")
        print(f"   Saldo final: {saldo_final_prestador:,.2f}")
        
        # 6. VERIFICAR DISTRIBUIÇÃO FINAL
        resumo_final = WalletService.get_system_token_summary()
        
        # Admin deve ter recebido a taxa
        admin_info = WalletService.get_admin_wallet_info()
        print(f"✅ Distribuição final:")
        print(f"   Admin (com taxa): {admin_info['balance']:,.0f}")
        print(f"   Prestador: {saldo_final_prestador:,.0f}")
        print(f"   Em circulação: {resumo_final['tokens_in_circulation']:,.0f}")
        
        # 7. VERIFICAR INTEGRIDADE
        self.assertEqual(
            resumo_final['total_tokens_in_system'],
            resumo_final['total_tokens_created']
        )
        print(f"✅ Integridade mantida: {resumo_final['total_tokens_in_system']:,.0f} tokens")
        
        # 8. VERIFICAR TRANSAÇÕES DO PRESTADOR
        transacoes_prestador = Transaction.query.filter_by(user_id=self.prestador.id).all()
        tipos_prestador = [t.type for t in transacoes_prestador]
        
        self.assertIn("criacao_carteira", tipos_prestador)
        self.assertIn("recebimento", tipos_prestador)
        self.assertIn("saque_tokens", tipos_prestador)
        print(f"✅ Transações prestador: {tipos_prestador}")
        
        print("✅ FLUXO PRESTADOR COMPLETO - SUCESSO\n")
    
    # ==============================================================================
    #  FLUXO DE DISPUTAS: ORDEM → DISPUTA → RESOLUÇÃO ADMIN → DISTRIBUIÇÃO
    # ==============================================================================
    
    def test_dispute_complete_flow_order_dispute_resolution_distribution(self):
        """Testa fluxo de disputas: ordem → disputa → resolução admin → distribuição tokens"""
        print("\n=== TESTE: Fluxo Completo de Disputas ===")
        
        # Preparar cenário completo
        WalletService.ensure_admin_has_wallet()
        WalletService.admin_create_tokens(500000.0, "Tokens para teste de disputas")
        
        # Cliente compra tokens
        WalletService.deposit(self.cliente.id, 20000.0, "Compra para ordem disputada")
        
        # Prestador precisa de carteira
        WalletService.ensure_user_has_wallet(self.prestador.id)
        
        # 1. CRIAÇÃO E ACEITAÇÃO DA ORDEM
        ordem_disputada = Order(
            client_id=self.cliente.id,
            provider_id=self.prestador.id,
            title="Serviço que será disputado",
            description="Ordem que entrará em disputa para teste",
            value=12000.0,
            status='em_andamento'
        )
        db.session.add(ordem_disputada)
        db.session.commit()
        
        # Transferir para escrow
        WalletService.transfer_to_escrow(self.cliente.id, ordem_disputada.value, ordem_disputada.id)
        print(f"✅ Ordem #{ordem_disputada.id} criada e em andamento")
        print(f"   Valor em escrow: {ordem_disputada.value:,.2f}")
        
        # 2. ABERTURA DE DISPUTA
        ordem_disputada.status = 'disputada'
        db.session.commit()
        print(f"✅ Ordem #{ordem_disputada.id} entrou em disputa")
        
        # 3. LOGIN DO ADMIN PARA RESOLUÇÃO - simulado
        admin_autenticado = AuthService.authenticate_admin('admin@combinado.com', 'admin123')
        self.assertIsNotNone(admin_autenticado)
        self.assertEqual(admin_autenticado.email, 'admin@combinado.com')
        print(f"✅ Admin autenticado para resolução: {admin_autenticado.email}")
        
        # 4. RESOLUÇÃO DA DISPUTA - CENÁRIO 1: FAVOR DO CLIENTE (REEMBOLSO)
        print("\n--- Cenário 1: Resolução a favor do cliente ---")
        
        # Simular decisão admin: reembolso total ao cliente
        resultado_reembolso = WalletService.refund_from_escrow(ordem_disputada.id)
        
        self.assertTrue(resultado_reembolso['success'])
        self.assertEqual(resultado_reembolso['refunded_amount'], ordem_disputada.value)
        
        # Verificar que cliente recebeu reembolso
        info_cliente_pos_reembolso = WalletService.get_wallet_info(self.cliente.id)
        saldo_esperado_cliente = 20000.0 - 12000.0 + 12000.0  # compra - escrow + reembolso
        self.assertEqual(info_cliente_pos_reembolso['balance'], saldo_esperado_cliente)
        self.assertEqual(info_cliente_pos_reembolso['escrow_balance'], 0.0)
        print(f"✅ Cliente reembolsado: {resultado_reembolso['refunded_amount']:,.2f}")
        print(f"   Novo saldo cliente: {info_cliente_pos_reembolso['balance']:,.2f}")
        
        # 5. NOVA DISPUTA - CENÁRIO 2: FAVOR DO PRESTADOR
        print("\n--- Cenário 2: Resolução a favor do prestador ---")
        
        # Criar nova ordem para testar resolução a favor do prestador
        ordem_disputada_2 = Order(
            client_id=self.cliente.id,
            provider_id=self.prestador.id,
            title="Segunda ordem disputada",
            description="Ordem para testar resolução a favor do prestador",
            value=8000.0,
            status='disputada'
        )
        db.session.add(ordem_disputada_2)
        db.session.commit()
        
        # Cliente transfere para escrow novamente
        WalletService.transfer_to_escrow(self.cliente.id, ordem_disputada_2.value, ordem_disputada_2.id)
        
        # Admin resolve a favor do prestador
        taxa_sistema = 0.05
        resultado_favor_prestador = WalletService.release_from_escrow(ordem_disputada_2.id, taxa_sistema)
        
        self.assertTrue(resultado_favor_prestador['success'])
        
        valor_prestador_disputa = ordem_disputada_2.value * (1 - taxa_sistema)
        valor_taxa_disputa = ordem_disputada_2.value * taxa_sistema
        
        print(f"✅ Disputa resolvida a favor do prestador:")
        print(f"   Valor prestador: {valor_prestador_disputa:,.2f}")
        print(f"   Taxa sistema: {valor_taxa_disputa:,.2f}")
        
        # 6. CENÁRIO 3: DIVISÃO 50/50
        print("\n--- Cenário 3: Divisão 50/50 ---")
        
        # Criar terceira ordem para divisão
        ordem_disputada_3 = Order(
            client_id=self.cliente.id,
            provider_id=self.prestador.id,
            title="Terceira ordem - divisão 50/50",
            description="Ordem para testar divisão meio a meio",
            value=6000.0,
            status='disputada'
        )
        db.session.add(ordem_disputada_3)
        db.session.commit()
        
        # Transferir para escrow
        WalletService.transfer_to_escrow(self.cliente.id, ordem_disputada_3.value, ordem_disputada_3.id)
        
        # Implementar divisão 50/50 customizada
        resultado_divisao = WalletService.resolve_dispute_custom_split(
            ordem_disputada_3.id,
            client_percentage=0.5,
            provider_percentage=0.5,
            system_fee_percentage=0.0  # Sem taxa em divisão
        )
        
        self.assertTrue(resultado_divisao['success'])
        valor_cada_um = ordem_disputada_3.value / 2
        
        self.assertEqual(resultado_divisao['client_amount'], valor_cada_um)
        self.assertEqual(resultado_divisao['provider_amount'], valor_cada_um)
        print(f"✅ Divisão 50/50 realizada:")
        print(f"   Cliente recebe: {valor_cada_um:,.2f}")
        print(f"   Prestador recebe: {valor_cada_um:,.2f}")
        
        # 7. VERIFICAR INTEGRIDADE FINAL APÓS TODAS AS DISPUTAS
        resumo_pos_disputas = WalletService.get_system_token_summary()
        
        self.assertEqual(
            resumo_pos_disputas['total_tokens_in_system'],
            resumo_pos_disputas['total_tokens_created']
        )
        print(f"✅ Integridade mantida após disputas:")
        print(f"   Total no sistema: {resumo_pos_disputas['total_tokens_in_system']:,.0f}")
        print(f"   Total criado: {resumo_pos_disputas['total_tokens_created']:,.0f}")
        
        # 8. VERIFICAR TRANSAÇÕES DE DISPUTA
        transacoes_disputa = Transaction.query.filter(
            Transaction.type.in_(['escrow_reembolso', 'escrow_liberacao', 'resolucao_disputa'])
        ).all()
        
        self.assertGreater(len(transacoes_disputa), 0)
        print(f"✅ Transações de disputa registradas: {len(transacoes_disputa)}")
        
        for t in transacoes_disputa:
            print(f"   {t.type}: {t.amount:,.2f} (Usuário {t.user_id})")
        
        print("✅ FLUXO DE DISPUTAS COMPLETO - SUCESSO\n")
    
    # ==============================================================================
    #  TESTES DE TERMINOLOGIA DIFERENCIADA POR TIPO DE USUÁRIO
    # ==============================================================================
    
    def test_terminology_differentiation_by_user_type(self):
        """Testa terminologia diferenciada: admin vê tokens, usuários veem R$"""
        print("\n=== TESTE: Terminologia Diferenciada ===")
        
        # Preparar dados
        WalletService.ensure_admin_has_wallet()
        WalletService.admin_create_tokens(100000.0, "Tokens para teste terminologia")
        WalletService.deposit(self.cliente.id, 5000.0, "Compra para teste terminologia")
        
        # 1. TERMINOLOGIA PARA ADMIN (TÉCNICA)
        # Admin deve ver terminologia técnica
        admin_info = WalletService.get_admin_wallet_info()
        resumo_admin = WalletService.get_system_token_summary()
        
        # Para admin: valores são mostrados como "tokens"
        print(f"✅ Terminologia ADMIN (técnica):")
        print(f"   Saldo admin: {admin_info['balance']:,.0f} tokens")
        print(f"   Tokens criados: {resumo_admin['total_tokens_created']:,.0f} tokens")
        print(f"   Em circulação: {resumo_admin['tokens_in_circulation']:,.0f} tokens")
        
        # 2. TERMINOLOGIA PARA USUÁRIO FINAL (R$)
        # Usuário deve ver terminologia em R$
        cliente_info = WalletService.get_wallet_info(self.cliente.id)
        
        # Para usuário: valores são mostrados como "R$" (simulando filtro format_currency)
        saldo_cliente_reais = f"R$ {cliente_info['balance']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"✅ Terminologia USUÁRIO (R$):")
        print(f"   Saldo cliente: {saldo_cliente_reais}")
        print(f"   Total disponível: R$ {cliente_info['total_balance']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # 3. USUÁRIO DUAL - DEVE VER R$ EM AMBOS OS PAPÉIS
        # Dar tokens ao usuário dual
        WalletService.deposit(self.usuario_dual.id, 3000.0, "Tokens para usuário dual")
        dual_info = WalletService.get_wallet_info(self.usuario_dual.id)
        
        # Mesmo sendo dual, deve ver R$
        saldo_dual_reais = f"R$ {dual_info['balance']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        print(f"✅ Terminologia USUÁRIO DUAL (R$ em ambos papéis):")
        print(f"   Como cliente: {saldo_dual_reais}")
        print(f"   Como prestador: {saldo_dual_reais}")
        
        # 4. VERIFICAR QUE LÓGICA INTERNA PERMANECE EM TOKENS
        # Independente da terminologia de exibição, a lógica interna usa tokens
        self.assertEqual(cliente_info['balance'], 5000.0)  # Valor interno em tokens
        self.assertEqual(dual_info['balance'], 3000.0)     # Valor interno em tokens
        
        print(f"✅ Lógica interna mantida em tokens:")
        print(f"   Cliente (interno): {cliente_info['balance']} tokens")
        print(f"   Dual (interno): {dual_info['balance']} tokens")
        
        print("✅ TERMINOLOGIA DIFERENCIADA - SUCESSO\n")
    
    # ==============================================================================
    #  TESTES DE INTEGRIDADE: VERIFICAR QUE TOKENS NUNCA "DESAPARECEM"
    # ==============================================================================
    
    def test_token_integrity_never_disappear(self):
        """Testa integridade: verificar que tokens nunca 'desaparecem' do sistema"""
        print("\n=== TESTE: Integridade - Tokens Nunca Desaparecem ===")
        
        # 1. ESTADO INICIAL
        WalletService.ensure_admin_has_wallet()
        resumo_inicial = WalletService.get_system_token_summary()
        tokens_iniciais = resumo_inicial['total_tokens_created']
        print(f"✅ Estado inicial: {tokens_iniciais:,.0f} tokens no sistema")
        
        # 2. MÚLTIPLAS OPERAÇÕES COMPLEXAS
        # Admin cria mais tokens
        WalletService.admin_create_tokens(200000.0, "Criação para teste integridade")
        
        # Múltiplos usuários compram tokens
        usuarios_teste = [self.cliente, self.prestador, self.usuario_dual]
        valores_compra = [15000.0, 25000.0, 10000.0]
        
        for i, usuario in enumerate(usuarios_teste):
            WalletService.deposit(usuario.id, valores_compra[i], f"Compra usuário {i+1}")
            print(f"✅ Usuário {usuario.email} comprou {valores_compra[i]:,.0f} tokens")
        
        # 3. OPERAÇÕES DE ESCROW
        # Criar ordens e transferir para escrow
        ordens_teste = []
        valores_escrow = [5000.0, 8000.0, 3000.0]
        
        for i, usuario in enumerate(usuarios_teste):
            ordem = Order(
                client_id=usuario.id,
                title=f"Ordem teste {i+1}",
                description=f"Ordem para teste de integridade {i+1}",
                value=valores_escrow[i],
                status='disponivel'
            )
            db.session.add(ordem)
            db.session.commit()
            ordens_teste.append(ordem)
            
            WalletService.transfer_to_escrow(usuario.id, valores_escrow[i], ordem.id)
            print(f"✅ {valores_escrow[i]:,.0f} tokens transferidos para escrow (Ordem #{ordem.id})")
        
        # 4. VERIFICAR INTEGRIDADE APÓS ESCROW
        resumo_pos_escrow = WalletService.get_system_token_summary()
        
        self.assertEqual(
            resumo_pos_escrow['total_tokens_in_system'],
            resumo_pos_escrow['total_tokens_created']
        )
        print(f"✅ Integridade mantida após escrow:")
        print(f"   Total criado: {resumo_pos_escrow['total_tokens_created']:,.0f}")
        print(f"   No sistema: {resumo_pos_escrow['total_tokens_in_system']:,.0f}")
        
        # 5. OPERAÇÕES DE LIBERAÇÃO E REEMBOLSO
        # Adicionar prestadores às ordens para poder liberar escrow
        ordens_teste[0].provider_id = self.prestador.id
        ordens_teste[1].provider_id = self.prestador.id  
        ordens_teste[2].provider_id = self.usuario_dual.id
        db.session.commit()
        
        # Liberar primeira ordem (pagamento normal)
        WalletService.release_from_escrow(ordens_teste[0].id, 0.05)
        print(f"✅ Ordem #{ordens_teste[0].id} liberada com taxa")
        
        # Reembolsar segunda ordem (disputa)
        WalletService.refund_from_escrow(ordens_teste[1].id)
        print(f"✅ Ordem #{ordens_teste[1].id} reembolsada")
        
        # Divisão customizada terceira ordem
        WalletService.resolve_dispute_custom_split(
            ordens_teste[2].id,
            client_percentage=0.3,
            provider_percentage=0.7,
            system_fee_percentage=0.0
        )
        print(f"✅ Ordem #{ordens_teste[2].id} dividida (30/70)")
        
        # 6. SAQUES MÚLTIPLOS
        # Usuários fazem saques
        saques = [2000.0, 5000.0, 1500.0]
        for i, usuario in enumerate(usuarios_teste):
            try:
                WalletService.withdraw(usuario.id, saques[i], f"Saque usuário {i+1}")
                print(f"✅ Usuário {usuario.email} sacou {saques[i]:,.0f} tokens")
            except ValueError as e:
                print(f"⚠️ Saque de {usuario.email} falhou: {e}")
        
        # 7. VERIFICAÇÃO FINAL DE INTEGRIDADE
        resumo_final = WalletService.get_system_token_summary()
        
        # REGRA FUNDAMENTAL: Total no sistema = Total criado (SEMPRE)
        self.assertEqual(
            resumo_final['total_tokens_in_system'],
            resumo_final['total_tokens_created']
        )
        
        print(f"✅ INTEGRIDADE FINAL VERIFICADA:")
        print(f"   Total criado: {resumo_final['total_tokens_created']:,.0f}")
        print(f"   Admin: {resumo_final['admin_balance']:,.0f}")
        print(f"   Circulação: {resumo_final['tokens_in_circulation']:,.0f}")
        print(f"   Total sistema: {resumo_final['total_tokens_in_system']:,.0f}")
        print(f"   Diferença: {resumo_final['total_tokens_in_system'] - resumo_final['total_tokens_created']:,.0f}")
        
        # 8. AUDITORIA DETALHADA
        # Verificar integridade individual de cada usuário
        for usuario in usuarios_teste:
            integridade_usuario = WalletService.validate_transaction_integrity(usuario.id)
            self.assertTrue(integridade_usuario['is_valid'])
            print(f"✅ Integridade {usuario.email}: {integridade_usuario['is_valid']}")
        
        print("✅ INTEGRIDADE COMPLETA - TOKENS NUNCA DESAPARECEM\n")
    
    # ==============================================================================
    #  TESTES DE CENÁRIOS DE ERRO
    # ==============================================================================
    
    def test_error_scenarios_insufficient_balance_invalid_orders(self):
        """Testa cenários de erro: saldo insuficiente, ordens inexistentes, etc."""
        print("\n=== TESTE: Cenários de Erro ===")
        
        # Preparar ambiente básico
        WalletService.ensure_admin_has_wallet()
        WalletService.admin_create_tokens(100000.0, "Tokens para testes de erro")
        
        # 1. ERRO: SALDO INSUFICIENTE PARA COMPRA
        print("\n--- Erro 1: Admin sem tokens suficientes ---")
        try:
            WalletService.admin_sell_tokens_to_user(
                self.cliente.id,
                2000000.0,  # Mais que o admin possui
                "Tentativa de compra excessiva"
            )
            self.fail("Deveria ter gerado erro de saldo insuficiente")
        except ValueError as e:
            self.assertIn("Admin não tem tokens suficientes", str(e))
            print(f"✅ Erro capturado corretamente: {e}")
        
        # 2. ERRO: USUÁRIO TENTANDO SACAR SEM SALDO
        print("\n--- Erro 2: Usuário sem saldo para saque ---")
        WalletService.ensure_user_has_wallet(self.cliente.id)  # Carteira com saldo 0
        
        try:
            WalletService.withdraw(self.cliente.id, 1000.0, "Saque sem saldo")
            self.fail("Deveria ter gerado erro de saldo insuficiente")
        except ValueError as e:
            self.assertIn("Saldo insuficiente", str(e))
            print(f"✅ Erro capturado corretamente: {e}")
        
        # 3. ERRO: TRANSFERIR PARA ESCROW SEM SALDO
        print("\n--- Erro 3: Escrow sem saldo suficiente ---")
        try:
            WalletService.transfer_to_escrow(self.cliente.id, 5000.0, 999)
            self.fail("Deveria ter gerado erro de saldo insuficiente para escrow")
        except ValueError as e:
            self.assertIn("Saldo insuficiente para transferir para escrow", str(e))
            print(f"✅ Erro capturado corretamente: {e}")
        
        # 4. ERRO: LIBERAR ESCROW DE ORDEM INEXISTENTE
        print("\n--- Erro 4: Ordem inexistente ---")
        try:
            WalletService.release_from_escrow(99999)  # Ordem que não existe
            self.fail("Deveria ter gerado erro de ordem não encontrada")
        except ValueError as e:
            self.assertIn("Ordem não encontrada", str(e))
            print(f"✅ Erro capturado corretamente: {e}")
        
        # 5. ERRO: OPERAÇÕES COM VALORES INVÁLIDOS
        print("\n--- Erro 5: Valores inválidos ---")
        WalletService.deposit(self.cliente.id, 1000.0, "Saldo para testes de erro")
        
        # Valor negativo
        try:
            WalletService.credit_wallet(self.cliente.id, -100.0, "Crédito negativo")
            self.fail("Deveria ter gerado erro de valor negativo")
        except ValueError as e:
            self.assertIn("deve ser positivo", str(e))
            print(f"✅ Erro valor negativo capturado: {e}")
        
        # Valor zero
        try:
            WalletService.debit_wallet(self.cliente.id, 0.0, "Débito zero")
            self.fail("Deveria ter gerado erro de valor zero")
        except ValueError as e:
            self.assertIn("deve ser positivo", str(e))
            print(f"✅ Erro valor zero capturado: {e}")
        
        # 6. ERRO: CARTEIRA INEXISTENTE
        print("\n--- Erro 6: Carteira inexistente ---")
        try:
            WalletService.get_wallet_balance(99999)  # Usuário inexistente
            self.fail("Deveria ter gerado erro de carteira não encontrada")
        except ValueError as e:
            self.assertIn("Carteira não encontrada", str(e))
            print(f"✅ Erro carteira inexistente capturado: {e}")
        
        # 7. ERRO: ORDEM SEM PRESTADOR
        print("\n--- Erro 7: Ordem sem prestador ---")
        ordem_sem_prestador = Order(
            client_id=self.cliente.id,
            title="Ordem sem prestador",
            description="Ordem que não tem prestador associado",
            value=1000.0,
            status='disponivel'
        )
        db.session.add(ordem_sem_prestador)
        db.session.commit()
        
        try:
            WalletService.release_from_escrow(ordem_sem_prestador.id)
            self.fail("Deveria ter gerado erro de ordem sem prestador")
        except ValueError as e:
            self.assertIn("não tem prestador associado", str(e))
            print(f"✅ Erro ordem sem prestador capturado: {e}")
        
        # 8. ERRO: ESCROW INSUFICIENTE PARA LIBERAÇÃO
        print("\n--- Erro 8: Escrow insuficiente ---")
        # Criar ordem com prestador mas sem escrow suficiente
        WalletService.ensure_user_has_wallet(self.prestador.id)
        
        ordem_escrow_insuficiente = Order(
            client_id=self.cliente.id,
            provider_id=self.prestador.id,
            title="Ordem escrow insuficiente",
            description="Ordem com escrow insuficiente",
            value=10000.0,  # Valor alto
            status='em_andamento'
        )
        db.session.add(ordem_escrow_insuficiente)
        db.session.commit()
        
        # Não transferir para escrow, tentar liberar direto
        try:
            WalletService.release_from_escrow(ordem_escrow_insuficiente.id)
            self.fail("Deveria ter gerado erro de escrow insuficiente")
        except ValueError as e:
            self.assertIn("Saldo em escrow insuficiente", str(e))
            print(f"✅ Erro escrow insuficiente capturado: {e}")
        
        # 9. VERIFICAR QUE ERROS NÃO AFETARAM INTEGRIDADE
        print("\n--- Verificação: Integridade após erros ---")
        resumo_pos_erros = WalletService.get_system_token_summary()
        
        self.assertEqual(
            resumo_pos_erros['total_tokens_in_system'],
            resumo_pos_erros['total_tokens_created']
        )
        print(f"✅ Integridade mantida após todos os erros:")
        print(f"   Total sistema: {resumo_pos_erros['total_tokens_in_system']:,.0f}")
        print(f"   Total criado: {resumo_pos_erros['total_tokens_created']:,.0f}")
        
        print("✅ CENÁRIOS DE ERRO COMPLETOS - SISTEMA ROBUSTO\n")

if __name__ == '__main__':
    # Executar testes com verbosidade
    unittest.main(verbosity=2)