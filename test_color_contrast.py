"""
Teste de Contraste de Cores - WCAG 2.1
Verifica se todas as combinações de cores atendem aos padrões de acessibilidade
"""

import math
from typing import Tuple, List, Dict


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Converte cor hexadecimal para RGB
    
    Args:
        hex_color: Cor em formato hexadecimal (#RRGGBB)
        
    Returns:
        Tupla (R, G, B) com valores de 0-255
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calcula a luminância relativa de uma cor RGB
    Fórmula WCAG: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    
    Args:
        rgb: Tupla (R, G, B) com valores de 0-255
        
    Returns:
        Luminância relativa (0-1)
    """
    # Normalizar valores RGB para 0-1
    r, g, b = [x / 255.0 for x in rgb]
    
    # Aplicar correção gamma
    def adjust(channel):
        if channel <= 0.03928:
            return channel / 12.92
        else:
            return math.pow((channel + 0.055) / 1.055, 2.4)
    
    r = adjust(r)
    g = adjust(g)
    b = adjust(b)
    
    # Calcular luminância
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calcula o ratio de contraste entre duas cores
    Fórmula WCAG: (L1 + 0.05) / (L2 + 0.05)
    
    Args:
        color1: Primeira cor em hexadecimal
        color2: Segunda cor em hexadecimal
        
    Returns:
        Ratio de contraste (1-21)
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    lum1 = rgb_to_luminance(rgb1)
    lum2 = rgb_to_luminance(rgb2)
    
    # L1 deve ser a luminância maior
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    contrast = (lighter + 0.05) / (darker + 0.05)
    return round(contrast, 2)


def check_wcag_compliance(contrast: float, text_size: str = 'normal') -> Dict[str, bool]:
    """
    Verifica conformidade com WCAG 2.1
    
    Args:
        contrast: Ratio de contraste
        text_size: 'normal' ou 'large'
        
    Returns:
        Dict com status de conformidade AA e AAA
    """
    if text_size == 'large':
        # Texto grande: 18pt+ ou 14pt+ bold
        aa_threshold = 3.0
        aaa_threshold = 4.5
    else:
        # Texto normal
        aa_threshold = 4.5
        aaa_threshold = 7.0
    
    return {
        'AA': contrast >= aa_threshold,
        'AAA': contrast >= aaa_threshold,
        'ratio': contrast
    }


def test_color_combinations():
    """
    Testa todas as combinações de cores do sistema
    """
    print("=" * 80)
    print("AUDITORIA DE CONTRASTE DE CORES - WCAG 2.1")
    print("=" * 80)
    print()
    
    # Definir cores do sistema
    colors = {
        'Modo Normal': {
            'Primárias': {
                'Primary': '#3d4fa8',
                'Primary Light': '#5a6fc7',
                'Primary Dark': '#2d3a7a',
            },
            'Sucesso': {
                'Success': '#1e7e34',
                'Success Light': '#1e7e34',
                'Success Dark': '#145523',
            },
            'Erro': {
                'Danger': '#c82333',
                'Danger Light': '#dc3545',
                'Danger Dark': '#a71d2a',
            },
            'Aviso': {
                'Warning': '#d39e00',
                'Warning Light': '#ffc107',
                'Warning Dark': '#ba8b00',
            },
            'Informação': {
                'Info': '#117a8b',
                'Info Light': '#117a8b',
                'Info Dark': '#0d6270',
            },
            'Texto': {
                'Text Primary': '#212529',
                'Text Secondary': '#495057',
                'Text Muted': '#6c757d',
                'Text Disabled': '#adb5bd',
            },
            'Link': {
                'Link': '#0056b3',
                'Link Hover': '#003d82',
                'Link Visited': '#5a2d81',
            }
        },
        'Modo Alto Contraste': {
            'Primárias': {
                'Primary': '#2d3a7a',
                'Primary Light': '#3d4fa8',
                'Primary Dark': '#1a2347',
            },
            'Sucesso': {
                'Success': '#145523',
                'Success Dark': '#0d3d1a',
            },
            'Erro': {
                'Danger': '#a71d2a',
                'Danger Dark': '#7a1520',
            },
            'Texto': {
                'Text Primary': '#000000',
                'Text Secondary': '#212529',
                'Text Muted': '#495057',
            }
        },
        'Modo Escuro': {
            'Cores': {
                'Primary': '#7a8fd9',
                'Success': '#4ade80',
                'Danger': '#f87171',
                'Warning': '#fbbf24',
                'Info': '#60a5fa',
                'Text Primary': '#f8f9fa',
                'Text Secondary': '#e9ecef',
                'Text Muted': '#adb5bd',
            }
        }
    }
    
    # Fundos de teste
    backgrounds = {
        'Branco': '#ffffff',
        'Escuro': '#1a1a1a',
        'Preto': '#000000',
    }
    
    total_tests = 0
    passed_aa = 0
    passed_aaa = 0
    failed = []
    
    # Testar cada modo
    for mode_name, mode_colors in colors.items():
        print(f"\n{'=' * 80}")
        print(f"MODO: {mode_name}")
        print(f"{'=' * 80}\n")
        
        # Determinar fundo apropriado
        if mode_name == 'Modo Escuro':
            bg_color = backgrounds['Escuro']
            bg_name = 'Escuro'
        else:
            bg_color = backgrounds['Branco']
            bg_name = 'Branco'
        
        # Testar cada categoria
        for category_name, category_colors in mode_colors.items():
            print(f"\n{category_name}:")
            print("-" * 80)
            
            for color_name, color_hex in category_colors.items():
                # Testar com fundo apropriado
                contrast = calculate_contrast_ratio(color_hex, bg_color)
                compliance = check_wcag_compliance(contrast)
                
                total_tests += 1
                
                # Status
                if compliance['AA']:
                    passed_aa += 1
                    status_aa = "✅ AA"
                else:
                    status_aa = "❌ AA"
                    failed.append({
                        'mode': mode_name,
                        'category': category_name,
                        'color': color_name,
                        'hex': color_hex,
                        'background': bg_name,
                        'contrast': contrast
                    })
                
                if compliance['AAA']:
                    passed_aaa += 1
                    status_aaa = "✅ AAA"
                else:
                    status_aaa = "⚠️  AAA"
                
                # Imprimir resultado
                print(f"  {color_name:20} {color_hex:10} vs {bg_name:10} "
                      f"Contraste: {contrast:5.2f}:1  {status_aa}  {status_aaa}")
                
                # Teste especial para Warning (usa texto preto)
                if 'Warning' in color_name and mode_name == 'Modo Normal':
                    contrast_black = calculate_contrast_ratio(color_hex, backgrounds['Preto'])
                    compliance_black = check_wcag_compliance(contrast_black)
                    
                    if compliance_black['AA']:
                        status_aa_black = "✅ AA"
                    else:
                        status_aa_black = "❌ AA"
                    
                    print(f"  {' ' * 20} {color_hex:10} vs {'Preto':10} "
                          f"Contraste: {contrast_black:5.2f}:1  {status_aa_black}  "
                          f"(texto preto)")
    
    # Resumo
    print(f"\n{'=' * 80}")
    print("RESUMO DA AUDITORIA")
    print(f"{'=' * 80}\n")
    
    print(f"Total de Testes: {total_tests}")
    print(f"Conformes com AA: {passed_aa} ({passed_aa/total_tests*100:.1f}%)")
    print(f"Conformes com AAA: {passed_aaa} ({passed_aaa/total_tests*100:.1f}%)")
    
    if failed:
        print(f"\n⚠️  ATENÇÃO: {len(failed)} combinações NÃO atendem WCAG AA:")
        print("-" * 80)
        for item in failed:
            print(f"  {item['mode']} > {item['category']} > {item['color']}")
            print(f"    Cor: {item['hex']} vs Fundo: {item['background']}")
            print(f"    Contraste: {item['contrast']}:1 (mínimo: 4.5:1)")
            print()
    else:
        print("\n✅ SUCESSO: Todas as combinações atendem WCAG 2.1 Nível AA!")
    
    # Verificar conformidade AAA
    if passed_aaa == total_tests:
        print("✅ EXCELENTE: Todas as combinações atendem WCAG 2.1 Nível AAA!")
    else:
        print(f"\n⚠️  {total_tests - passed_aaa} combinações não atendem AAA "
              f"(mas atendem AA, que é o requisito mínimo)")
    
    print(f"\n{'=' * 80}\n")
    
    return len(failed) == 0


def test_specific_combination(color1: str, color2: str, description: str = ""):
    """
    Testa uma combinação específica de cores
    
    Args:
        color1: Primeira cor (hex)
        color2: Segunda cor (hex)
        description: Descrição da combinação
    """
    contrast = calculate_contrast_ratio(color1, color2)
    compliance = check_wcag_compliance(contrast)
    
    print(f"\nTeste: {description}")
    print(f"Cor 1: {color1}")
    print(f"Cor 2: {color2}")
    print(f"Contraste: {contrast}:1")
    print(f"WCAG AA (4.5:1): {'✅ Passa' if compliance['AA'] else '❌ Falha'}")
    print(f"WCAG AAA (7:1): {'✅ Passa' if compliance['AAA'] else '❌ Falha'}")


if __name__ == '__main__':
    # Executar auditoria completa
    success = test_color_combinations()
    
    # Exemplos de testes específicos
    print("\n" + "=" * 80)
    print("TESTES ESPECÍFICOS")
    print("=" * 80)
    
    test_specific_combination(
        '#3d4fa8', '#ffffff',
        'Botão Primário (texto branco em fundo azul)'
    )
    
    test_specific_combination(
        '#1e7e34', '#ffffff',
        'Botão de Sucesso (texto branco em fundo verde)'
    )
    
    test_specific_combination(
        '#ffc107', '#000000',
        'Botão de Aviso (texto preto em fundo amarelo)'
    )
    
    # Retornar código de saída
    exit(0 if success else 1)
