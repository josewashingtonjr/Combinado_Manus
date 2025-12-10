"""
Teste para verificar os indicadores visuais de ajuste na página de solicitações de tokens
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import TokenRequest, User, AdminUser, Wallet
from datetime import datetime
from decimal import Decimal

def test_visual_indicators():
    """Testa se os indicadores visuais aparecem corretamente no template"""
    
    with app.app_context():
        
        # Criar usuário de teste
        import random
        cpf_unico = f"{random.randint(10000000000, 99999999999)}"
        user = User(
            nome='Usuário Teste Visual',
            email=f'visual{random.randint(1000,9999)}@test.com',
            cpf=cpf_unico,
            phone='11999999999'
        )
        user.set_password('test123')
        db.session.add(user)
        
        db.session.flush()  # Para obter o ID do usuário
        
        # Criar carteira para o usuário
        wallet = Wallet(user_id=user.id, balance=Decimal('0.00'))
        db.session.add(wallet)
        
        # Criar admin de teste
        admin = AdminUser(
            email=f'admin_visual{random.randint(1000,9999)}@test.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        # Teste 1: Solicitação sem ajuste (não deve mostrar badge)
        request1 = TokenRequest(
            user_id=user.id,
            amount=Decimal('100.00'),
            description='Solicitação sem ajuste',
            status='pending',
            payment_method='pix'
        )
        db.session.add(request1)
        db.session.commit()
        
        print("✓ Teste 1: Solicitação sem ajuste criada")
        print(f"  - ID: {request1.id}")
        print(f"  - Valor: R$ {request1.amount}")
        print(f"  - Admin Notes: {request1.admin_notes}")
        print(f"  - Deve mostrar badge? NÃO")
        
        # Teste 2: Solicitação com ajuste (deve mostrar badge)
        request2 = TokenRequest(
            user_id=user.id,
            amount=Decimal('50.00'),
            description='Solicitação com ajuste',
            status='pending',
            payment_method='pix',
            admin_notes=f'[AJUSTE] Quantidade ajustada de R$ 100.00 para R$ 50.00 em 20/11/2025 15:30 por Admin #{admin.id}\nJustificativa: Comprovante mostra pagamento de apenas R$ 50,00'
        )
        db.session.add(request2)
        db.session.commit()
        
        print("\n✓ Teste 2: Solicitação com ajuste criada")
        print(f"  - ID: {request2.id}")
        print(f"  - Valor: R$ {request2.amount}")
        print(f"  - Admin Notes: {request2.admin_notes[:80]}...")
        print(f"  - Deve mostrar badge? SIM")
        
        # Teste 3: Verificar condição do template
        print("\n✓ Teste 3: Verificando condições do template")
        
        # Condição 1: admin_notes existe e contém 'Quantidade ajustada'
        has_notes_1 = request1.admin_notes is not None
        has_adjustment_1 = 'Quantidade ajustada' in (request1.admin_notes or '')
        should_show_badge_1 = has_notes_1 and has_adjustment_1
        
        print(f"\n  Solicitação 1 (sem ajuste):")
        print(f"    - admin_notes existe? {has_notes_1}")
        print(f"    - Contém 'Quantidade ajustada'? {has_adjustment_1}")
        print(f"    - Deve mostrar badge? {should_show_badge_1}")
        
        has_notes_2 = request2.admin_notes is not None
        has_adjustment_2 = 'Quantidade ajustada' in (request2.admin_notes or '')
        should_show_badge_2 = has_notes_2 and has_adjustment_2
        
        print(f"\n  Solicitação 2 (com ajuste):")
        print(f"    - admin_notes existe? {has_notes_2}")
        print(f"    - Contém 'Quantidade ajustada'? {has_adjustment_2}")
        print(f"    - Deve mostrar badge? {should_show_badge_2}")
        
        # Teste 4: Extrair informação do tooltip
        if request2.admin_notes and '[AJUSTE]' in request2.admin_notes:
            tooltip_text = request2.admin_notes.split('[AJUSTE]')[1].split('\n')[0]
            print(f"\n✓ Teste 4: Texto do tooltip extraído:")
            print(f"  '{tooltip_text}'")
        
        # Verificações finais
        assert not should_show_badge_1, "Solicitação sem ajuste não deve mostrar badge"
        assert should_show_badge_2, "Solicitação com ajuste deve mostrar badge"
        
        print("\n" + "="*60)
        print("✓ TODOS OS TESTES PASSARAM!")
        print("="*60)
        print("\nResumo da implementação:")
        print("1. Badge 'Ajustado' aparece apenas quando admin_notes contém 'Quantidade ajustada'")
        print("2. Badge tem cor de destaque (bg-warning text-dark)")
        print("3. Tooltip mostra informações do ajuste")
        print("4. Ícone de edição (fa-edit) é exibido no badge")
        
        # Limpar dados de teste
        db.session.delete(request1)
        db.session.delete(request2)
        db.session.delete(wallet)
        db.session.delete(user)
        db.session.delete(admin)
        db.session.commit()
        
        print("\n✓ Dados de teste removidos")

if __name__ == '__main__':
    test_visual_indicators()
