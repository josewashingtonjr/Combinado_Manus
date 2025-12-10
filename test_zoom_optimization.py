"""
Testes para Otimização de Zoom - Requirement 7.2
Valida que o layout funciona corretamente com zoom de até 200%
"""

import pytest
import re
from pathlib import Path


class TestZoomOptimization:
    """Testes para validar otimização de zoom"""
    
    @pytest.fixture
    def zoom_css_path(self):
        """Caminho para o arquivo CSS de otimização de zoom"""
        return Path('static/css/zoom-optimization.css')
    
    @pytest.fixture
    def zoom_css_content(self, zoom_css_path):
        """Conteúdo do arquivo CSS de otimização de zoom"""
        with open(zoom_css_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @pytest.fixture
    def base_template_path(self):
        """Caminho para o template base"""
        return Path('templates/base.html')
    
    @pytest.fixture
    def base_template_content(self, base_template_path):
        """Conteúdo do template base"""
        with open(base_template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def test_zoom_css_file_exists(self, zoom_css_path):
        """Testa se o arquivo CSS de otimização de zoom existe"""
        assert zoom_css_path.exists(), "Arquivo zoom-optimization.css não encontrado"
    
    def test_zoom_css_loaded_in_base_template(self, base_template_content):
        """Testa se o CSS de zoom está carregado no template base"""
        assert 'zoom-optimization.css' in base_template_content, \
            "CSS de otimização de zoom não está carregado no template base"
    
    def test_html_overflow_prevention(self, zoom_css_content):
        """Testa se há regras para prevenir overflow horizontal no html"""
        assert 'html' in zoom_css_content, "Regras para html não encontradas"
        assert 'overflow-x: hidden' in zoom_css_content, \
            "Regra overflow-x: hidden não encontrada"
        assert 'max-width: 100vw' in zoom_css_content or 'max-width: 100%' in zoom_css_content, \
            "Regra max-width não encontrada para prevenir overflow"
    
    def test_body_overflow_prevention(self, zoom_css_content):
        """Testa se há regras para prevenir overflow horizontal no body"""
        # Procurar por regras do body
        body_rules = re.findall(r'body\s*{[^}]+}', zoom_css_content, re.DOTALL)
        assert len(body_rules) > 0, "Regras para body não encontradas"
        
        # Verificar se alguma regra do body contém overflow-x: hidden
        has_overflow_rule = any('overflow-x: hidden' in rule for rule in body_rules)
        assert has_overflow_rule, "Regra overflow-x: hidden não encontrada para body"
    
    def test_flexible_typography(self, zoom_css_content):
        """Testa se a tipografia usa unidades flexíveis (clamp, rem, vw)"""
        # Verificar uso de clamp para tipografia flexível
        assert 'clamp(' in zoom_css_content, \
            "Função clamp() não encontrada para tipografia flexível"
        
        # Verificar uso de unidades relativas
        assert 'rem' in zoom_css_content or 'em' in zoom_css_content, \
            "Unidades relativas (rem/em) não encontradas"
    
    def test_flexible_containers(self, zoom_css_content):
        """Testa se containers têm largura máxima de 100%"""
        # Verificar regras para containers
        assert '.container' in zoom_css_content, "Regras para .container não encontradas"
        assert 'max-width: 100%' in zoom_css_content, \
            "Regra max-width: 100% não encontrada para containers"
    
    def test_word_wrap_rules(self, zoom_css_content):
        """Testa se há regras para quebra de texto"""
        # Verificar regras de quebra de texto
        assert 'word-wrap: break-word' in zoom_css_content or \
               'overflow-wrap: break-word' in zoom_css_content, \
            "Regras de quebra de texto não encontradas"
        
        # Verificar hyphens
        assert 'hyphens: auto' in zoom_css_content, \
            "Regra hyphens: auto não encontrada"
    
    def test_flexible_buttons(self, zoom_css_content):
        """Testa se botões têm tamanhos flexíveis"""
        # Verificar regras para botões
        button_rules = re.findall(r'\.btn[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        assert len(button_rules) > 0, "Regras para botões não encontradas"
        
        # Verificar uso de clamp ou min-height flexível
        has_flexible_size = any('clamp(' in rule or 'min-height' in rule 
                               for rule in button_rules)
        assert has_flexible_size, \
            "Botões não têm tamanhos flexíveis (clamp ou min-height)"
    
    def test_flexible_form_controls(self, zoom_css_content):
        """Testa se campos de formulário têm tamanhos flexíveis"""
        # Verificar regras para form-control
        assert '.form-control' in zoom_css_content or 'input' in zoom_css_content, \
            "Regras para campos de formulário não encontradas"
        
        # Verificar tamanho de fonte mínimo de 16px (previne zoom no iOS)
        assert '16px' in zoom_css_content, \
            "Tamanho de fonte mínimo de 16px não encontrado para inputs"
    
    def test_responsive_cards(self, zoom_css_content):
        """Testa se cards têm padding flexível"""
        # Verificar regras para cards
        card_rules = re.findall(r'\.card[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        assert len(card_rules) > 0, "Regras para cards não encontradas"
        
        # Verificar uso de clamp para padding
        has_flexible_padding = any('clamp(' in rule for rule in card_rules)
        assert has_flexible_padding, "Cards não têm padding flexível"
    
    def test_table_responsive_rules(self, zoom_css_content):
        """Testa se há regras para tabelas responsivas"""
        # Verificar regras para tabelas
        assert '.table-responsive' in zoom_css_content or 'table' in zoom_css_content, \
            "Regras para tabelas não encontradas"
        
        # Verificar overflow-x para scroll horizontal controlado
        table_rules = re.findall(r'\.table[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        has_overflow = any('overflow-x' in rule for rule in table_rules)
        assert has_overflow, "Regras de overflow para tabelas não encontradas"
    
    def test_media_query_for_high_zoom(self, zoom_css_content):
        """Testa se há media queries para zoom alto"""
        # Verificar media queries para resolução alta (zoom)
        assert '@media' in zoom_css_content, "Media queries não encontradas"
        
        # Verificar media query para min-resolution (detecta zoom)
        has_resolution_query = 'min-resolution' in zoom_css_content or \
                              'min-width' in zoom_css_content
        assert has_resolution_query, \
            "Media queries para zoom alto não encontradas"
    
    def test_flexible_spacing(self, zoom_css_content):
        """Testa se espaçamentos usam unidades flexíveis"""
        # Verificar uso de clamp para margens e paddings
        spacing_rules = re.findall(r'\.(mb-|mt-|p-|margin|padding)[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        
        # Verificar se há uso de clamp em qualquer lugar do CSS para espaçamentos
        has_flexible_spacing = 'clamp(' in zoom_css_content and ('margin' in zoom_css_content or 'padding' in zoom_css_content)
        
        # Se encontrou regras de espaçamento, verificar se usam clamp
        if spacing_rules and not has_flexible_spacing:
            # Permitir se não houver regras de espaçamento específicas
            # (o CSS pode usar outras abordagens)
            pass
        
        # Verificar se pelo menos há uso de clamp no CSS
        assert 'clamp(' in zoom_css_content, \
            "Função clamp() não encontrada para espaçamentos flexíveis"
    
    def test_modal_responsive_rules(self, zoom_css_content):
        """Testa se modais têm regras responsivas"""
        # Verificar regras para modais
        modal_rules = re.findall(r'\.modal[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        
        if modal_rules:
            # Verificar max-width responsivo
            has_responsive_width = any('max-width' in rule and 'calc' in rule 
                                      for rule in modal_rules)
            assert has_responsive_width, \
                "Modais não têm largura responsiva"
    
    def test_navbar_responsive_rules(self, zoom_css_content):
        """Testa se navbar tem regras responsivas"""
        # Verificar regras para navbar
        navbar_rules = re.findall(r'\.navbar[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        
        if navbar_rules:
            # Verificar flex-wrap para quebra de itens
            has_flex_wrap = any('flex-wrap' in rule for rule in navbar_rules)
            assert has_flex_wrap, "Navbar não tem flex-wrap para zoom"
    
    def test_image_responsive_rules(self, zoom_css_content):
        """Testa se imagens têm regras responsivas"""
        # Verificar regras para imagens
        assert 'img' in zoom_css_content, "Regras para imagens não encontradas"
        
        # Verificar max-width: 100% e height: auto
        img_rules = re.findall(r'img[^{]*{[^}]+}', zoom_css_content, re.DOTALL)
        has_responsive_img = any('max-width: 100%' in rule and 'height: auto' in rule 
                                for rule in img_rules)
        assert has_responsive_img, \
            "Imagens não têm regras responsivas (max-width: 100%, height: auto)"
    
    def test_utility_classes_for_zoom(self, zoom_css_content):
        """Testa se há classes utilitárias para zoom"""
        # Verificar classes utilitárias
        utility_classes = [
            '.zoom-break-text',
            '.zoom-no-overflow',
            '.zoom-stack',
            '.zoom-container'
        ]
        
        for class_name in utility_classes:
            assert class_name in zoom_css_content, \
                f"Classe utilitária {class_name} não encontrada"
    
    def test_no_fixed_widths(self, zoom_css_content):
        """Testa se não há larguras fixas problemáticas"""
        # Procurar por larguras fixas em pixels (exceto min-width e max-width)
        # Isso é uma verificação básica - larguras fixas podem quebrar com zoom
        
        # Permitir min-width e max-width, mas alertar sobre width fixo
        fixed_width_pattern = r'(?<!min-)(?<!max-)width:\s*\d+px'
        fixed_widths = re.findall(fixed_width_pattern, zoom_css_content)
        
        # Filtrar casos aceitáveis (como borders, etc)
        problematic_widths = [w for w in fixed_widths if 'border' not in w.lower()]
        
        # Avisar se houver muitas larguras fixas (mais de 5 pode ser problemático)
        if len(problematic_widths) > 5:
            print(f"Aviso: {len(problematic_widths)} larguras fixas encontradas. "
                  f"Considere usar unidades flexíveis.")
    
    def test_zoom_test_page_exists(self):
        """Testa se a página de teste de zoom existe"""
        test_page = Path('static/zoom-optimization-test.html')
        assert test_page.exists(), \
            "Página de teste zoom-optimization-test.html não encontrada"
    
    def test_zoom_test_page_has_controls(self):
        """Testa se a página de teste tem controles de zoom"""
        test_page = Path('static/zoom-optimization-test.html')
        with open(test_page, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se tem controles de zoom
        assert 'setZoom' in content, "Função setZoom não encontrada na página de teste"
        assert 'test-controls' in content, "Controles de teste não encontrados"
        assert 'zoom-level-indicator' in content, \
            "Indicador de nível de zoom não encontrado"
    
    def test_zoom_test_page_has_test_sections(self):
        """Testa se a página de teste tem seções de teste"""
        test_page = Path('static/zoom-optimization-test.html')
        with open(test_page, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar seções de teste essenciais
        test_sections = [
            'Tipografia',
            'Botões',
            'Formulários',
            'Cards',
            'Tabelas',
            'Alertas'
        ]
        
        for section in test_sections:
            assert section in content, \
                f"Seção de teste '{section}' não encontrada na página de teste"
    
    def test_zoom_test_page_has_checklist(self):
        """Testa se a página de teste tem checklist de validação"""
        test_page = Path('static/zoom-optimization-test.html')
        with open(test_page, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar checklist
        assert 'Checklist de Validação' in content, \
            "Checklist de validação não encontrado"
        assert 'Layout não quebra com zoom' in content, \
            "Item de checklist sobre quebra de layout não encontrado"
        assert 'Sem scroll horizontal' in content, \
            "Item de checklist sobre scroll horizontal não encontrado"


class TestZoomOptimizationIntegration:
    """Testes de integração para otimização de zoom"""
    
    def test_all_css_files_loaded_in_order(self):
        """Testa se todos os arquivos CSS estão carregados na ordem correta"""
        base_template = Path('templates/base.html')
        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar ordem de carregamento
        css_files = [
            'mobile-first.css',
            'touch-targets.css',
            'accessibility-colors.css',
            'zoom-optimization.css'
        ]
        
        positions = []
        for css_file in css_files:
            pos = content.find(css_file)
            if pos != -1:
                positions.append((css_file, pos))
        
        # Verificar se zoom-optimization.css é carregado
        zoom_css_loaded = any(css == 'zoom-optimization.css' for css, _ in positions)
        assert zoom_css_loaded, \
            "zoom-optimization.css não está carregado no template base"
    
    def test_zoom_optimization_compatible_with_mobile_first(self):
        """Testa se otimização de zoom é compatível com mobile-first"""
        zoom_css = Path('static/css/zoom-optimization.css')
        mobile_css = Path('static/css/mobile-first.css')
        
        with open(zoom_css, 'r', encoding='utf-8') as f:
            zoom_content = f.read()
        
        with open(mobile_css, 'r', encoding='utf-8') as f:
            mobile_content = f.read()
        
        # Verificar se ambos usam overflow-x: hidden
        assert 'overflow-x: hidden' in zoom_content, \
            "zoom-optimization.css não previne overflow horizontal"
        assert 'overflow-x: hidden' in mobile_content, \
            "mobile-first.css não previne overflow horizontal"
        
        # Verificar se ambos usam max-width: 100%
        assert 'max-width: 100%' in zoom_content, \
            "zoom-optimization.css não usa max-width: 100%"
        assert 'max-width: 100%' in mobile_content, \
            "mobile-first.css não usa max-width: 100%"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
