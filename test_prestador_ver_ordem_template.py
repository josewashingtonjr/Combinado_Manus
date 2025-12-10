"""
Teste para validar o template de detalhes da ordem do prestador
"""
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Adicionar o diretório raiz ao path
sys.path.insert(0, '.')

from jinja2 import Environment, FileSystemLoader

def test_template_syntax():
    """Testa se o template tem sintaxe válida"""
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('prestador/ver_ordem.html')
        print("✓ Template carregado com sucesso - sintaxe válida")
        return True
    except Exception as e:
        print(f"✗ Erro ao carregar template: {e}")
        return False

def test_template_rendering():
    """Testa se o template renderiza com dados de exemplo"""
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        
        # Adicionar filtro format_currency
        def format_currency(value):
            if value is None:
                return "R$ 0,00"
            return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        env.filters['format_currency'] = format_currency
        
        template = env.get_template('prestador/ver_ordem.html')
        
        # Criar objeto mock de ordem
        class MockUser:
            def __init__(self, nome, email, phone=None):
                self.nome = nome
                self.email = email
                self.phone = phone
        
        class MockOrder:
            def __init__(self):
                self.id = 1
                self.title = "Instalação Elétrica"
                self.description = "Instalação completa de sistema elétrico"
                self.value = Decimal('500.00')
                self.status = 'aguardando_execucao'
                self.status_display = 'Aguardando Execução'
                self.status_icon_class = 'fas fa-clock'
                self.status_color_class = 'bg-warning'
                self.created_at = datetime.now()
                self.service_deadline = datetime.now() + timedelta(days=7)
                self.completed_at = None
                self.confirmed_at = None
                self.cancelled_at = None
                self.dispute_opened_at = None
                self.dispute_resolved_at = None
                self.confirmation_deadline = None
                self.hours_until_auto_confirmation = None
                self.auto_confirmed = False
                self.cancellation_reason = None
                self.dispute_winner = None
                self.platform_fee_percentage_at_creation = Decimal('5.0')
                self.contestation_fee_at_creation = Decimal('10.00')
                self.cancellation_fee_percentage_at_creation = Decimal('10.0')
                self.cancellation_fee = None
                self.provider_id = 2
                self.client = MockUser("João Silva", "joao@example.com", "(11) 98765-4321")
                self.provider = MockUser("Maria Santos", "maria@example.com")
        
        order = MockOrder()
        
        # Renderizar template
        html = template.render(
            order=order,
            csrf_token=lambda: 'test-token'
        )
        
        # Verificar se elementos chave estão presentes
        assert 'Ordem #1' in html
        assert 'Instalação Elétrica' in html
        assert 'João Silva' in html
        assert 'Marcar como Concluído' in html
        assert 'Cancelar Ordem' in html
        assert 'Informações do Serviço' in html
        assert 'Histórico de Datas' in html
        assert 'Cálculo de Valores' in html
        
        print("✓ Template renderizado com sucesso")
        print(f"✓ HTML gerado tem {len(html)} caracteres")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao renderizar template: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_status_servico_executado():
    """Testa renderização com status servico_executado"""
    try:
        env = Environment(loader=FileSystemLoader('templates'))
        
        # Adicionar filtro format_currency
        def format_currency(value):
            if value is None:
                return "R$ 0,00"
            return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        env.filters['format_currency'] = format_currency
        
        template = env.get_template('prestador/ver_ordem.html')
        
        # Criar objeto mock de ordem
        class MockUser:
            def __init__(self, nome, email, phone=None):
                self.nome = nome
                self.email = email
                self.phone = phone
        
        class MockOrder:
            def __init__(self):
                self.id = 2
                self.title = "Conserto de Encanamento"
                self.description = "Reparo de vazamento"
                self.value = Decimal('300.00')
                self.status = 'servico_executado'
                self.status_display = 'Serviço Executado'
                self.status_icon_class = 'fas fa-check-circle'
                self.status_color_class = 'bg-info'
                self.created_at = datetime.now() - timedelta(days=2)
                self.service_deadline = datetime.now() + timedelta(days=5)
                self.completed_at = datetime.now() - timedelta(hours=10)
                self.confirmation_deadline = datetime.now() + timedelta(hours=26)
                self.hours_until_auto_confirmation = 26.0
                self.confirmed_at = None
                self.cancelled_at = None
                self.dispute_opened_at = None
                self.dispute_resolved_at = None
                self.auto_confirmed = False
                self.cancellation_reason = None
                self.dispute_winner = None
                self.platform_fee_percentage_at_creation = Decimal('5.0')
                self.contestation_fee_at_creation = Decimal('10.00')
                self.cancellation_fee_percentage_at_creation = Decimal('10.0')
                self.cancellation_fee = None
                self.provider_id = 2
                self.client = MockUser("Pedro Costa", "pedro@example.com")
                self.provider = MockUser("Maria Santos", "maria@example.com")
        
        order = MockOrder()
        
        # Renderizar template
        html = template.render(
            order=order,
            csrf_token=lambda: 'test-token'
        )
        
        # Verificar elementos específicos para status servico_executado
        assert 'Aguardando Confirmação do Cliente' in html
        assert '26.0 horas' in html or '26,0 horas' in html
        assert 'confirmação automática' in html.lower()
        assert 'countdown-display' in html
        
        print("✓ Template renderizado corretamente para status 'servico_executado'")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao renderizar template com status servico_executado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Testando Template: templates/prestador/ver_ordem.html")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testando sintaxe do template...")
    results.append(test_template_syntax())
    
    print("\n2. Testando renderização básica...")
    results.append(test_template_rendering())
    
    print("\n3. Testando renderização com status 'servico_executado'...")
    results.append(test_template_status_servico_executado())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ TODOS OS TESTES PASSARAM")
        print("=" * 60)
        sys.exit(0)
    else:
        print("✗ ALGUNS TESTES FALHARAM")
        print("=" * 60)
        sys.exit(1)
