#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste do fluxo integrado de adição de saldo e aprovação de proposta
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Invite, Proposal, Wallet, Transaction, TokenRequest
from services.proposal_service import ProposalService
from services.balance_validator import BalanceValidator
from services.wallet_service import WalletService
from decimal import Decimal

def test_integrated_balance_flow():
    """Testa o fluxo completo de adição de saldo integrado"""
    
    with app.app_context():
        # Usar banco de dados existente
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sistema_combinado.db'
        print("🧪 Testando Fluxo Integrado de Adição de Saldo")
        print("=" * 60)
        
        try:
            # 1. Buscar usuários existentes
            print("\n1️⃣ Buscando usuários existentes...")
            
            # Buscar cliente e prestador existentes
            cliente = User.query.filter(User.roles.contains(['cliente'])).first()
            prestador = User.query.filter(User.roles.contains(['prestador'])).first()
            
            if not cliente:
                raise ValueError("Nenhum cliente encontrado no banco de dados")
            if not prestador:
                raise ValueError("Nenhum prestador encontrado no banco de dados")
            
            print(f"   ✅ Cliente encontrado: ID {cliente.id} - {cliente.nome}")
            print(f"   ✅ Prestador encontrado: ID {prestador.id} - {prestador.nome}")
            
            # 2. Criar carteiras
            print("\n2️⃣ Criando carteiras...")
            WalletService.ensure_user_has_wallet(cliente.id)
            WalletService.ensure_user_has_wallet(prestador.id)
            
            # Adicionar saldo insuficiente ao cliente (apenas R$ 50)
            WalletService.admin_sell_tokens_to_user(cliente.id, 50.0, "Saldo inicial para teste")
            
            cliente_wallet = WalletService.get_wallet_info(cliente.id)
            print(f"   ✅ Carteira do cliente: R$ {cliente_wallet['balance']:.2f}")
            
            # 3. Criar convite
            print("\n3️⃣ Criando convite...")
            convite = Invite(
                client_id=cliente.id,
                service_category="limpeza",
                description="Limpeza de casa",
                value=100.0,  # R$ 100
                invited_phone=prestador.phone,
                status='pending'
            )
            db.session.add(convite)
            db.session.commit()
            
            print(f"   ✅ Convite criado: ID {convite.id}, Valor: R$ {convite.value:.2f}")
            
            # 4. Criar proposta de aumento
            print("\n4️⃣ Criando proposta de aumento...")
            proposta_result = ProposalService.create_proposal(
                invite_id=convite.id,
                prestador_id=prestador.id,
                proposed_value=Decimal('150.0'),  # Aumento para R$ 150
                justification="Serviço mais complexo que o esperado"
            )
            
            proposal_id = proposta_result['proposal_id']
            print(f"   ✅ Proposta criada: ID {proposal_id}")
            print(f"   📊 Valor original: R$ {proposta_result['original_value']:.2f}")
            print(f"   📊 Valor proposto: R$ {proposta_result['proposed_value']:.2f}")
            
            # 5. Verificar saldo insuficiente
            print("\n5️⃣ Verificando saldo do cliente...")
            balance_status = BalanceValidator.validate_proposal_balance(
                client_id=cliente.id,
                proposed_value=Decimal('150.0')
            )
            
            print(f"   💰 Saldo atual: R$ {balance_status.current_balance:.2f}")
            print(f"   💰 Valor necessário: R$ {balance_status.required_amount:.2f}")
            print(f"   💰 Faltam: R$ {balance_status.shortfall:.2f}")
            print(f"   ❌ Saldo suficiente: {balance_status.is_sufficient}")
            
            # 6. Simular adição de saldo
            print("\n6️⃣ Simulando adição de saldo...")
            amount_to_add = balance_status.shortfall + Decimal('10.0')  # Adicionar um pouco mais
            
            simulation = ProposalService.simulate_balance_addition(
                proposal_id=proposal_id,
                client_id=cliente.id,
                amount_to_add=amount_to_add
            )
            
            print(f"   🧮 Valor a adicionar: R$ {amount_to_add:.2f}")
            print(f"   🧮 Saldo simulado: R$ {simulation['simulated_balance']:.2f}")
            print(f"   ✅ Será suficiente: {simulation['will_be_sufficient']}")
            
            # 7. Executar fluxo integrado
            print("\n7️⃣ Executando fluxo integrado...")
            
            integrated_result = ProposalService.add_balance_and_approve_proposal(
                proposal_id=proposal_id,
                client_id=cliente.id,
                amount_to_add=amount_to_add,
                payment_method='pix',
                description='Teste de adição integrada',
                client_response_reason='Aprovando proposta após adicionar saldo'
            )
            
            print(f"   ✅ {integrated_result['message']}")
            print(f"   💰 Valor adicionado: R$ {integrated_result['amount_added']:.2f}")
            print(f"   💰 Novo saldo: R$ {integrated_result['new_balance']:.2f}")
            print(f"   📋 Valor aprovado: R$ {integrated_result['approved_value']:.2f}")
            
            # 8. Verificar estado final
            print("\n8️⃣ Verificando estado final...")
            
            # Verificar proposta
            proposta = Proposal.query.get(proposal_id)
            print(f"   📋 Status da proposta: {proposta.status}")
            print(f"   📋 Respondida em: {proposta.responded_at}")
            
            # Verificar convite
            convite_updated = Invite.query.get(convite.id)
            print(f"   📋 Valor efetivo do convite: R$ {convite_updated.effective_value:.2f}")
            print(f"   📋 Tem proposta ativa: {convite_updated.has_active_proposal}")
            
            # Verificar saldo final
            final_wallet = WalletService.get_wallet_info(cliente.id)
            print(f"   💰 Saldo final: R$ {final_wallet['balance']:.2f}")
            
            # Verificar solicitação de tokens
            token_request = TokenRequest.query.filter_by(user_id=cliente.id).order_by(TokenRequest.created_at.desc()).first()
            if token_request:
                print(f"   📝 Solicitação de tokens: ID {token_request.id}, Status: {token_request.status}")
            
            print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO NO TESTE: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Limpeza
            try:
                db.session.rollback()
            except:
                pass

if __name__ == "__main__":
    success = test_integrated_balance_flow()
    sys.exit(0 if success else 1)