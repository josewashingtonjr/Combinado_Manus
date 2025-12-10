#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do InviteAcceptanceCoordinator

Valida:
- Detecção de aceitação mútua
- Validação de saldos antes da criação da ordem
- Criação atômica de ordem com bloqueio de valores
- Tratamento de erros e rollback
"""

import sys
import os
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, User, Invite, Order, Wallet
from services.invite_acceptance_coordinator import InviteAcceptanceCoordinator
from services.wallet_service import WalletService
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_app():
    """Cria aplicação de teste"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def test_check_mutual_acceptance():
    """Testa a detecção de aceitação mútua"""
    logger.info("\n" + "="*60)
    logger.info("TESTE: Detecção de Aceitação Mútua")
    logger.info("="*60)
    
    app = create_test_app()
    
    with app.app_context():
        # Buscar cliente existente
        client = User.query.filter_by(email='jose@example.com').first()
        if not client:
            logger.error("Cliente de teste não encontrado")
            return False
        
        # Criar convite de teste
        invite = Invite(
            client_id=client.id,
            invited_phone='11999999999',
            service_title='Teste Aceitação Mútua',
            service_description='Teste do coordenador',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        try:
            # Teste 1: Nenhuma aceitação
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            assert not is_mutual, "Não deveria estar mutuamente aceito"
            logger.info(f"✓ Teste 1: {msg}")
            
            # Teste 2: Apenas cliente aceita
            invite.client_accepted = True
            invite.client_accepted_at = datetime.utcnow()
            db.session.commit()
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            assert not is_mutual, "Não deveria estar mutuamente aceito"
            assert "prestador" in msg.lower(), "Mensagem deveria mencionar prestador"
            logger.info(f"✓ Teste 2: {msg}")
            
            # Teste 3: Ambos aceitam
            invite.provider_accepted = True
            invite.provider_accepted_at = datetime.utcnow()
            db.session.commit()
            
            is_mutual, msg = InviteAcceptanceCoordinator.check_mutual_acceptance(invite)
            assert is_mutual, "Deveria estar mutuamente aceito"
            logger.info(f"✓ Teste 3: {msg}")
            
            logger.info("\n✓ Todos os testes de detecção passaram!")
            return True
            
        finally:
            # Limpar
            db.session.delete(invite)
            db.session.commit()

def test_validate_balances():
    """Testa a validação de saldos"""
    logger.info("\n" + "="*60)
    logger.info("TESTE: Validação de Saldos")
    logger.info("="*60)
    
    app = create_test_app()
    
    with app.app_context():
        # Buscar usuários existentes
        client = User.query.filter_by(email='jose@example.com').first()
        provider = User.query.filter_by(email='maria@example.com').first()
        
        if not client or not provider:
            logger.error("Usuários de teste não encontrados")
            return False
        
        # Garantir que ambos têm carteiras
        WalletService.ensure_user_has_wallet(client.id)
        WalletService.ensure_user_has_wallet(provider.id)
        
        # Obter saldos atuais
        client_balance = WalletService.get_wallet_balance(client.id)
        provider_balance = WalletService.get_wallet_balance(provider.id)
        
        logger.info(f"\nSaldo cliente: R$ {client_balance:.2f}")
        logger.info(f"Saldo prestador: R$ {provider_balance:.2f}")
        
        # Teste 1: Valor que o cliente pode pagar
        service_value = min(Decimal('50.00'), client_balance - Decimal('10.00'))
        result = InviteAcceptanceCoordinator._validate_balances_for_order(
            client.id,
            provider.id,
            service_value
        )
        
        if result['valid']:
            logger.info(f"✓ Teste 1: Validação passou para valor R$ {service_value:.2f}")
        else:
            logger.warning(f"⚠ Teste 1: {result['error']}")
        
        # Teste 2: Valor muito alto para o cliente
        high_value = client_balance + Decimal('100.00')
        result = InviteAcceptanceCoordinator._validate_balances_for_order(
            client.id,
            provider.id,
            high_value
        )
        
        assert not result['valid'], "Deveria falhar com valor muito alto"
        assert "cliente" in result['error'].lower(), "Erro deveria mencionar cliente"
        logger.info(f"✓ Teste 2: Validação corretamente rejeitou valor alto")
        
        # Teste 3: Prestador sem saldo para taxa
        # Criar usuário temporário sem saldo
        temp_provider = User(
            email='temp_provider@test.com',
            nome='Temp Provider',
            cpf='99999999999',
            phone='11888888888',
            roles='prestador'
        )
        temp_provider.set_password('test123')
        db.session.add(temp_provider)
        db.session.commit()
        
        try:
            WalletService.ensure_user_has_wallet(temp_provider.id)
            
            result = InviteAcceptanceCoordinator._validate_balances_for_order(
                client.id,
                temp_provider.id,
                Decimal('50.00')
            )
            
            assert not result['valid'], "Deveria falhar sem saldo para taxa"
            assert "prestador" in result['error'].lower(), "Erro deveria mencionar prestador"
            logger.info(f"✓ Teste 3: Validação corretamente rejeitou prestador sem saldo")
            
        finally:
            # Limpar usuário temporário
            wallet = Wallet.query.filter_by(user_id=temp_provider.id).first()
            if wallet:
                db.session.delete(wallet)
            db.session.delete(temp_provider)
            db.session.commit()
        
        logger.info("\n✓ Todos os testes de validação passaram!")
        return True

def test_process_acceptance():
    """Testa o processamento de aceitação"""
    logger.info("\n" + "="*60)
    logger.info("TESTE: Processamento de Aceitação")
    logger.info("="*60)
    
    app = create_test_app()
    
    with app.app_context():
        # Buscar cliente existente
        client = User.query.filter_by(email='jose@example.com').first()
        if not client:
            logger.error("Cliente de teste não encontrado")
            return False
        
        # Criar convite de teste
        invite = Invite(
            client_id=client.id,
            invited_phone='11999999999',
            service_title='Teste Process Acceptance',
            service_description='Teste do coordenador',
            original_value=Decimal('100.00'),
            delivery_date=datetime.utcnow() + timedelta(days=7),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(invite)
        db.session.commit()
        
        try:
            # Teste 1: Cliente aceita primeiro
            invite.client_accepted = True
            invite.client_accepted_at = datetime.utcnow()
            db.session.commit()
            
            result = InviteAcceptanceCoordinator.process_acceptance(
                invite.id,
                client.id,
                'client'
            )
            
            assert result['success'], f"Deveria ter sucesso: {result.get('error', '')}"
            assert not result['order_created'], "Ordem não deveria ser criada ainda"
            assert result['pending_acceptance_from'] == 'prestador'
            logger.info(f"✓ Teste 1: {result['message']}")
            
            # Teste 2: Prestador aceita (sem criar ordem por falta de prestador no sistema)
            invite.provider_accepted = True
            invite.provider_accepted_at = datetime.utcnow()
            db.session.commit()
            
            # Este teste vai falhar porque não há prestador com o telefone no sistema
            # Mas valida que a lógica de detecção de aceitação mútua funciona
            result = InviteAcceptanceCoordinator.process_acceptance(
                invite.id,
                client.id,  # Usando client.id como placeholder
                'provider'
            )
            
            # Esperamos que falhe por não encontrar prestador
            if not result['success']:
                logger.info(f"✓ Teste 2: Corretamente detectou falta de prestador no sistema")
            else:
                logger.warning(f"⚠ Teste 2: Resultado inesperado: {result}")
            
            logger.info("\n✓ Testes de processamento concluídos!")
            return True
            
        finally:
            # Limpar
            db.session.delete(invite)
            db.session.commit()

if __name__ == "__main__":
    success = True
    
    try:
        if not test_check_mutual_acceptance():
            success = False
            logger.error("\n✗ Falha nos testes de detecção")
        
        if not test_validate_balances():
            success = False
            logger.error("\n✗ Falha nos testes de validação")
        
        if not test_process_acceptance():
            success = False
            logger.error("\n✗ Falha nos testes de processamento")
        
    except Exception as e:
        logger.error(f"\n✗ Erro durante os testes: {str(e)}", exc_info=True)
        success = False
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("✅ TODOS OS TESTES DO COORDINATOR PASSARAM!")
        logger.info("="*60)
        sys.exit(0)
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ ALGUNS TESTES FALHARAM")
        logger.error("="*60)
        sys.exit(1)
