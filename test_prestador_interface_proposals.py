#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-

"""
Teste da interface do prestador para propostas de alteração
Verifica se a interface está exibindo corretamente os estados e ações
"""

import pytest
from flask import Flask, url_for
from models import db, User, Invite, Proposal
from services.invite_state_manager import InviteStateManager, InviteState
from services.proposal_service import ProposalService
from datetime import datetime, timedelta
from decimal import Decimal
import tempfile
import os

def create_test_app():
    """Cria app de teste"""
    app = Flask(__name__)
    
    # Configuração de teste
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Inicializar extensões
    db.init_app(app)
    
    # Registrar blueprints necessários
    from routes.prestador_routes import prestador_bp
    from routes.proposal_routes import proposal_bp
    app.register_blueprint(prestador_bp)
    app.register_blueprint(proposal_bp)
    
    return app, db_fd, db_path

def test_prestador_interface_states():
    """Testa se a interface do prestador exibe corretamente os diferentes estados"""
    
    app, db_fd, db_path = create_test_app()
    
    try:
        with app.app_context():
            # Criar tabelas
            db.create_all()
            
            # Criar usuários de teste
            cliente = User(
                nome="Cliente Teste",
                email="cliente@teste.com",
                phone="11999999999",
                cpf="12345678901",
                password_hash="hash_teste",
                roles="cliente"
            )
            
            prestador = User(
                nome="Prestador Teste", 
                email="prestador@teste.com",
                phone="11888888888",
                cpf="98765432100",
                password_hash="hash_teste",
                roles="prestador"
            )
            
            db.session.add(cliente)
            db.session.add(prestador)
            db.session.commit()
            
            # Criar convite de teste
            convite = Invite(
                client_id=cliente.id,
                invited_phone=prestador.phone,
                service_title="Serviço de Teste",
                service_description="Descrição do serviço de teste",
                original_value=Decimal('100.00'),
                delivery_date=datetime.now() + timedelta(days=7),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            db.session.add(convite)
            db.session.commit()
            
            print(f"✓ Convite criado: ID {convite.id}")
            
            # Testar cliente de teste
            with app.test_client() as client:
                
                # 1. Testar estado PENDENTE
                print("\n=== TESTE: Estado PENDENTE ===")
                
                # Simular login do prestador (simplificado para teste)
                with client.session_transaction() as sess:
                    sess['user_id'] = prestador.id
                    sess['user_roles'] = 'prestador'
                
                # Acessar página do convite
                response = client.get(f'/prestador/convites/{convite.token}')
                
                if response.status_code == 200:
                    print("✓ Página carregada com sucesso")
                    
                    # Verificar se elementos esperados estão presentes
                    html = response.get_data(as_text=True)
                    
                    # Verificar se mostra estado pendente
                    assert 'Aguardando Resposta' in html or 'pendente' in html.lower()
                    print("✓ Estado pendente exibido corretamente")
                    
                    # Verificar se botões estão disponíveis
                    assert 'Aceitar Convite' in html
                    assert 'Propor Alteração' in html
                    assert 'Recusar Convite' in html
                    print("✓ Botões de ação disponíveis")
                    
                else:
                    print(f"✗ Erro ao carregar página: {response.status_code}")
                    return False
                
                # 2. Testar criação de proposta
                print("\n=== TESTE: Criação de Proposta ===")
                
                # Criar proposta via service (simular POST)
                proposta_result = ProposalService.create_proposal(
                    invite_id=convite.id,
                    prestador_id=prestador.id,
                    proposed_value=Decimal('150.00'),
                    justification="Aumento devido à complexidade do projeto"
                )
                
                print(f"✓ Proposta criada: {proposta_result['message']}")
                
                # Recarregar página para ver novo estado
                response = client.get(f'/prestador/convites/{convite.token}')
                
                if response.status_code == 200:
                    html = response.get_data(as_text=True)
                    
                    # Verificar se mostra estado de proposta enviada
                    assert 'Proposta Enviada' in html or 'proposta_enviada' in html.lower()
                    print("✓ Estado 'Proposta Enviada' exibido")
                    
                    # Verificar se botão aceitar está desabilitado
                    assert 'disabled' in html or 'Aguardando aprovação' in html
                    print("✓ Botão 'Aceitar Convite' desabilitado corretamente")
                    
                    # Verificar se mostra valor proposto
                    assert '150,00' in html or '150.00' in html
                    print("✓ Valor proposto exibido")
                    
                    # Verificar se botão cancelar proposta está disponível
                    assert 'Cancelar Proposta' in html
                    print("✓ Botão 'Cancelar Proposta' disponível")
                    
                else:
                    print(f"✗ Erro ao recarregar página: {response.status_code}")
                    return False
                
                # 3. Testar aprovação da proposta (simular ação do cliente)
                print("\n=== TESTE: Proposta Aprovada ===")
                
                # Aprovar proposta via service
                proposta = Proposal.query.filter_by(invite_id=convite.id).first()
                aprovacao_result = ProposalService.approve_proposal(
                    proposal_id=proposta.id,
                    client_id=cliente.id
                )
                
                print(f"✓ Proposta aprovada: {aprovacao_result['message']}")
                
                # Recarregar página
                response = client.get(f'/prestador/convites/{convite.token}')
                
                if response.status_code == 200:
                    html = response.get_data(as_text=True)
                    
                    # Verificar se mostra estado aprovado
                    assert 'Proposta Aprovada' in html or 'proposta_aceita' in html.lower()
                    print("✓ Estado 'Proposta Aprovada' exibido")
                    
                    # Verificar se botão aceitar está habilitado novamente
                    # (não deve ter 'disabled' no botão aceitar)
                    aceitar_button_disabled = 'btn btn-success w-100 mb-2 disabled' in html
                    assert not aceitar_button_disabled
                    print("✓ Botão 'Aceitar Convite' habilitado após aprovação")
                    
                    # Verificar se mostra valor aprovado
                    assert '150,00' in html or '150.00' in html
                    print("✓ Valor aprovado exibido")
                    
                else:
                    print(f"✗ Erro ao recarregar página após aprovação: {response.status_code}")
                    return False
                
                print("\n✅ TODOS OS TESTES DA INTERFACE PASSARAM!")
                return True
                
    except Exception as e:
        print(f"✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpar arquivos temporários
        try:
            os.close(db_fd)
            os.unlink(db_path)
        except:
            pass

if __name__ == '__main__':
    print("Iniciando testes da interface do prestador para propostas...")
    
    success = test_prestador_interface_states()
    
    if success:
        print("\n🎉 TODOS OS TESTES DA INTERFACE PASSARAM COM SUCESSO!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        exit(1)