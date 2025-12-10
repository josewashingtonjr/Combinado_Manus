"""
Teste para verificar melhorias visuais de comprovantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import User, TokenRequest, AdminUser
from datetime import datetime
from decimal import Decimal

def test_receipt_visual_improvements():
    """Testa se as melhorias visuais para comprovantes estão implementadas"""
    
    with app.app_context():
        # Limpar dados de teste
        TokenRequest.query.filter_by(description='TEST_VISUAL_IMPROVEMENTS').delete()
        db.session.commit()
        
        # Usar primeiro usuário disponível
        user = User.query.filter_by(active=True).first()
        if not user:
            print("❌ Nenhum usuário ativo encontrado no banco de dados")
            return False
        
        # Usar primeiro admin disponível
        admin = AdminUser.query.first()
        if not admin:
            print("❌ Nenhum admin encontrado no banco de dados")
            return False
        
        # Criar solicitação COM comprovante
        request_with_receipt = TokenRequest(
            user_id=user.id,
            amount=Decimal('100.00'),
            description='TEST_VISUAL_IMPROVEMENTS',
            status='pending',
            payment_method='pix',
            receipt_filename='test_receipt.jpg',
            receipt_original_name='comprovante_pagamento_teste.jpg',
            receipt_uploaded_at=datetime.utcnow()
        )
        db.session.add(request_with_receipt)
        
        # Criar solicitação SEM comprovante
        request_without_receipt = TokenRequest(
            user_id=user.id,
            amount=Decimal('50.00'),
            description='TEST_VISUAL_IMPROVEMENTS',
            status='pending',
            payment_method='pix'
        )
        db.session.add(request_without_receipt)
        
        db.session.commit()
        
        print("✓ Solicitações de teste criadas")
        
        # Testar renderização do template
        with app.test_client() as client:
            # Login como admin
            response = client.post('/admin/login', data={
                'email': admin.email,
                'password': 'admin123'  # Assumindo senha padrão
            }, follow_redirects=True)
            
            # Se login falhar, tentar sem autenticação (apenas verificar template)
            if response.status_code != 200:
                print("⚠ Login falhou, testando template diretamente")
            else:
                print("✓ Login como admin realizado")
            
            # Acessar página de solicitações
            response = client.get('/admin/tokens/solicitacoes')
            assert response.status_code == 200, "Falha ao acessar página de solicitações"
            
            html = response.data.decode('utf-8')
            
            # Verificar elementos visuais para comprovante anexado
            assert 'badge bg-success' in html, "Badge de comprovante anexado não encontrado"
            assert 'fa-paperclip' in html, "Ícone de anexo não encontrado"
            assert 'Ver Comprovante' in html, "Botão 'Ver Comprovante' não encontrado"
            assert 'btn-primary' in html, "Estilo do botão não encontrado"
            assert 'target="_blank"' in html, "Atributo target='_blank' não encontrado"
            assert 'rel="noopener noreferrer"' in html, "Atributo rel de segurança não encontrado"
            
            print("✓ Elementos visuais para comprovante anexado verificados")
            
            # Verificar elementos para solicitação sem comprovante
            assert 'Sem comprovante' in html, "Texto 'Sem comprovante' não encontrado"
            assert 'fa-times-circle' in html, "Ícone de sem comprovante não encontrado"
            
            print("✓ Elementos visuais para sem comprovante verificados")
            
            # Verificar CSS customizado
            assert '@keyframes pulse' in html, "Animação pulse não encontrada"
            assert 'animation: pulse 2s infinite' in html, "Aplicação da animação não encontrada"
            assert 'z-index: 1050' in html, "Z-index do modal não encontrado"
            
            print("✓ CSS customizado verificado")
            
            # Verificar que nome do arquivo é exibido
            assert 'comprovante_pagamento_teste.jpg' in html, "Nome do arquivo não encontrado"
            
            print("✓ Nome do arquivo de comprovante exibido")
        
        # Limpar dados de teste
        TokenRequest.query.filter_by(description='TEST_VISUAL_IMPROVEMENTS').delete()
        db.session.commit()
        
        print("\n✅ TODOS OS TESTES DE MELHORIAS VISUAIS PASSARAM!")
        return True

if __name__ == '__main__':
    try:
        test_receipt_visual_improvements()
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
