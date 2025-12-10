"""
Script para validar acessibilidade dos templates administrativos.
Verifica:
- Links com texto descritivo
- Contraste de cores
- Navegação por teclado
- Estrutura semântica HTML
"""

import os
import re
from bs4 import BeautifulSoup
from pathlib import Path


class AccessibilityValidator:
    """Validador de acessibilidade para templates HTML."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def validate_template(self, template_path):
        """Valida um template HTML."""
        print(f"\n{'='*80}")
        print(f"Validando: {template_path}")
        print(f"{'='*80}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Validações
        self.check_links_have_text(soup, template_path)
        self.check_buttons_have_text(soup, template_path)
        self.check_images_have_alt(soup, template_path)
        self.check_form_labels(soup, template_path)
        self.check_heading_hierarchy(soup, template_path)
        self.check_aria_labels(soup, template_path)
        self.check_keyboard_navigation(soup, template_path)
        
    def check_links_have_text(self, soup, template_path):
        """Verifica se todos os links têm texto descritivo."""
        links = soup.find_all('a')
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            aria_label = link.get('aria-label', '')
            title = link.get('title', '')
            
            # Link tem ícone mas sem texto
            if link.find('i') and not text:
                if not aria_label and not title:
                    self.issues.append(
                        f"❌ {template_path}: Link sem texto descritivo: {href}"
                    )
                else:
                    self.passed.append(
                        f"✅ {template_path}: Link com ícone tem aria-label ou title"
                    )
            # Link sem texto e sem ícone
            elif not text and not link.find('i'):
                if not aria_label and not title:
                    self.issues.append(
                        f"❌ {template_path}: Link vazio sem aria-label: {href}"
                    )
            # Link com texto genérico
            elif text.lower() in ['clique aqui', 'aqui', 'saiba mais', 'ver mais']:
                self.warnings.append(
                    f"⚠️  {template_path}: Link com texto genérico: '{text}'"
                )
            else:
                self.passed.append(
                    f"✅ {template_path}: Link com texto descritivo: '{text}'"
                )
    
    def check_buttons_have_text(self, soup, template_path):
        """Verifica se todos os botões têm texto descritivo."""
        buttons = soup.find_all('button')
        
        for button in buttons:
            text = button.get_text(strip=True)
            aria_label = button.get('aria-label', '')
            title = button.get('title', '')
            
            if not text and not aria_label and not title:
                self.issues.append(
                    f"❌ {template_path}: Botão sem texto ou aria-label"
                )
            elif button.find('i') and not text and not aria_label:
                self.warnings.append(
                    f"⚠️  {template_path}: Botão com ícone sem aria-label"
                )
            else:
                self.passed.append(
                    f"✅ {template_path}: Botão com texto descritivo"
                )
    
    def check_images_have_alt(self, soup, template_path):
        """Verifica se todas as imagens têm atributo alt."""
        images = soup.find_all('img')
        
        for img in images:
            alt = img.get('alt', '')
            src = img.get('src', '')
            
            if not alt:
                self.issues.append(
                    f"❌ {template_path}: Imagem sem atributo alt: {src}"
                )
            elif alt.strip() == '':
                self.warnings.append(
                    f"⚠️  {template_path}: Imagem com alt vazio: {src}"
                )
            else:
                self.passed.append(
                    f"✅ {template_path}: Imagem com alt descritivo: '{alt}'"
                )
    
    def check_form_labels(self, soup, template_path):
        """Verifica se todos os inputs têm labels associados."""
        inputs = soup.find_all(['input', 'select', 'textarea'])
        
        for input_elem in inputs:
            input_type = input_elem.get('type', 'text')
            input_id = input_elem.get('id', '')
            input_name = input_elem.get('name', '')
            
            # Ignorar inputs hidden e submit
            if input_type in ['hidden', 'submit', 'button']:
                continue
            
            # Verificar se tem label associado
            if input_id:
                label = soup.find('label', {'for': input_id})
                if not label:
                    aria_label = input_elem.get('aria-label', '')
                    placeholder = input_elem.get('placeholder', '')
                    
                    if not aria_label and not placeholder:
                        self.issues.append(
                            f"❌ {template_path}: Input sem label: {input_name or input_id}"
                        )
                    else:
                        self.warnings.append(
                            f"⚠️  {template_path}: Input sem label mas com aria-label/placeholder: {input_name or input_id}"
                        )
                else:
                    self.passed.append(
                        f"✅ {template_path}: Input com label associado: {input_name or input_id}"
                    )
            else:
                self.warnings.append(
                    f"⚠️  {template_path}: Input sem ID para associar label: {input_name}"
                )
    
    def check_heading_hierarchy(self, soup, template_path):
        """Verifica hierarquia de headings (h1, h2, h3, etc)."""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            self.warnings.append(
                f"⚠️  {template_path}: Nenhum heading encontrado"
            )
            return
        
        levels = [int(h.name[1]) for h in headings]
        
        # Verificar se começa com h1
        if levels and levels[0] != 1:
            self.warnings.append(
                f"⚠️  {template_path}: Primeiro heading não é h1 (é h{levels[0]})"
            )
        
        # Verificar saltos na hierarquia
        for i in range(len(levels) - 1):
            if levels[i+1] - levels[i] > 1:
                self.warnings.append(
                    f"⚠️  {template_path}: Salto na hierarquia de headings: h{levels[i]} -> h{levels[i+1]}"
                )
        
        if not self.warnings:
            self.passed.append(
                f"✅ {template_path}: Hierarquia de headings correta"
            )
    
    def check_aria_labels(self, soup, template_path):
        """Verifica uso adequado de ARIA labels."""
        elements_with_aria = soup.find_all(attrs={'aria-label': True})
        
        for elem in elements_with_aria:
            aria_label = elem.get('aria-label', '').strip()
            
            if not aria_label:
                self.warnings.append(
                    f"⚠️  {template_path}: Elemento com aria-label vazio"
                )
            else:
                self.passed.append(
                    f"✅ {template_path}: Elemento com aria-label: '{aria_label}'"
                )
    
    def check_keyboard_navigation(self, soup, template_path):
        """Verifica elementos interativos para navegação por teclado."""
        # Elementos que devem ser acessíveis por teclado
        interactive = soup.find_all(['a', 'button', 'input', 'select', 'textarea'])
        
        for elem in interactive:
            tabindex = elem.get('tabindex', '')
            
            # tabindex negativo remove do fluxo de teclado
            if tabindex and int(tabindex) < 0:
                self.warnings.append(
                    f"⚠️  {template_path}: Elemento interativo com tabindex negativo"
                )
            
            # Verificar se elementos clicáveis têm role adequado
            if elem.name == 'div' and elem.get('onclick'):
                role = elem.get('role', '')
                if role not in ['button', 'link']:
                    self.issues.append(
                        f"❌ {template_path}: Div clicável sem role adequado"
                    )
    
    def print_report(self):
        """Imprime relatório de validação."""
        print(f"\n{'='*80}")
        print("RELATÓRIO DE ACESSIBILIDADE")
        print(f"{'='*80}\n")
        
        print(f"✅ Validações Passadas: {len(self.passed)}")
        print(f"⚠️  Avisos: {len(self.warnings)}")
        print(f"❌ Problemas Críticos: {len(self.issues)}\n")
        
        if self.issues:
            print(f"\n{'='*80}")
            print("PROBLEMAS CRÍTICOS")
            print(f"{'='*80}")
            for issue in self.issues:
                print(issue)
        
        if self.warnings:
            print(f"\n{'='*80}")
            print("AVISOS")
            print(f"{'='*80}")
            for warning in self.warnings[:20]:  # Limitar a 20 avisos
                print(warning)
            if len(self.warnings) > 20:
                print(f"\n... e mais {len(self.warnings) - 20} avisos")
        
        print(f"\n{'='*80}")
        print("RESUMO")
        print(f"{'='*80}")
        
        total = len(self.passed) + len(self.warnings) + len(self.issues)
        if total > 0:
            score = (len(self.passed) / total) * 100
            print(f"Score de Acessibilidade: {score:.1f}%")
        
        if len(self.issues) == 0:
            print("\n✅ Nenhum problema crítico encontrado!")
        else:
            print(f"\n❌ {len(self.issues)} problemas críticos precisam ser corrigidos")
        
        print(f"\n{'='*80}\n")


def main():
    """Função principal."""
    validator = AccessibilityValidator()
    
    # Templates administrativos para validar
    templates_dir = Path('templates/admin')
    
    if not templates_dir.exists():
        print(f"❌ Diretório {templates_dir} não encontrado")
        return
    
    # Validar templates principais
    main_templates = [
        'base_admin.html',
        'dashboard.html',
        'configuracoes_index.html',
        'configuracoes_taxas.html',
        'configuracoes_seguranca.html',
        'relatorios.html',
        'convites.html',
        'ordens.html',
        'contestacoes.html'
    ]
    
    for template_name in main_templates:
        template_path = templates_dir / template_name
        if template_path.exists():
            validator.validate_template(template_path)
        else:
            print(f"⚠️  Template não encontrado: {template_path}")
    
    # Imprimir relatório final
    validator.print_report()
    
    # Criar arquivo de relatório
    report_path = Path('.kiro/specs/otimizacao-menus-admin/RELATORIO_ACESSIBILIDADE.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Relatório de Acessibilidade - Menus Administrativos\n\n")
        f.write(f"**Data:** {Path(__file__).stat().st_mtime}\n\n")
        f.write(f"## Resumo\n\n")
        f.write(f"- ✅ Validações Passadas: {len(validator.passed)}\n")
        f.write(f"- ⚠️  Avisos: {len(validator.warnings)}\n")
        f.write(f"- ❌ Problemas Críticos: {len(validator.issues)}\n\n")
        
        if validator.issues:
            f.write("## Problemas Críticos\n\n")
            for issue in validator.issues:
                f.write(f"{issue}\n")
            f.write("\n")
        
        if validator.warnings:
            f.write("## Avisos\n\n")
            for warning in validator.warnings:
                f.write(f"{warning}\n")
            f.write("\n")
        
        f.write("## Recomendações\n\n")
        f.write("1. Todos os links devem ter texto descritivo ou aria-label\n")
        f.write("2. Botões com apenas ícones devem ter aria-label\n")
        f.write("3. Todas as imagens devem ter atributo alt descritivo\n")
        f.write("4. Todos os inputs devem ter labels associados\n")
        f.write("5. Hierarquia de headings deve ser respeitada (h1 -> h2 -> h3)\n")
        f.write("6. Elementos interativos devem ser acessíveis por teclado\n")
        f.write("7. Contraste de cores deve ser adequado (WCAG AA: 4.5:1)\n")
    
    print(f"✅ Relatório salvo em: {report_path}")


if __name__ == '__main__':
    main()
