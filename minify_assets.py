#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para minificar CSS e JS
Otimiza assets estáticos para melhor performance
"""

import os
import re
import json
from pathlib import Path

def minify_css(css_content):
    """
    Minifica conteúdo CSS removendo espaços, comentários e quebras de linha desnecessárias
    """
    # Remove comentários CSS
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Remove espaços em branco extras
    css_content = re.sub(r'\s+', ' ', css_content)
    
    # Remove espaços ao redor de caracteres especiais
    css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
    
    # Remove ponto e vírgula antes de fechar chave
    css_content = re.sub(r';}', '}', css_content)
    
    return css_content.strip()


def minify_js(js_content):
    """
    Minifica conteúdo JavaScript de forma básica
    Remove comentários e espaços desnecessários
    """
    # Remove comentários de linha única
    js_content = re.sub(r'//.*?$', '', js_content, flags=re.MULTILINE)
    
    # Remove comentários de múltiplas linhas
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    
    # Remove espaços em branco extras (mas preserva strings)
    lines = []
    for line in js_content.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    
    js_content = '\n'.join(lines)
    
    # Remove espaços ao redor de operadores (cuidado com strings)
    js_content = re.sub(r'\s*([{}();,:])\s*', r'\1', js_content)
    
    return js_content.strip()


def process_directory(source_dir, output_dir, file_extension, minify_func):
    """
    Processa todos os arquivos de um diretório
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Criar diretório de saída se não existir
    output_path.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'files_processed': 0,
        'original_size': 0,
        'minified_size': 0,
        'files': []
    }
    
    # Processar cada arquivo
    for file_path in source_path.glob(f'*.{file_extension}'):
        # Pular arquivos já minificados
        if '.min.' in file_path.name:
            continue
        
        # Ler conteúdo original
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        original_size = len(original_content)
        
        # Minificar
        minified_content = minify_func(original_content)
        minified_size = len(minified_content)
        
        # Criar nome do arquivo minificado
        output_filename = file_path.stem + '.min.' + file_extension
        output_file = output_path / output_filename
        
        # Salvar arquivo minificado
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minified_content)
        
        # Atualizar estatísticas
        reduction = ((original_size - minified_size) / original_size * 100) if original_size > 0 else 0
        
        file_stats = {
            'name': file_path.name,
            'original_size': original_size,
            'minified_size': minified_size,
            'reduction_percent': round(reduction, 2)
        }
        
        stats['files'].append(file_stats)
        stats['files_processed'] += 1
        stats['original_size'] += original_size
        stats['minified_size'] += minified_size
        
        print(f"✓ {file_path.name} -> {output_filename} ({reduction:.1f}% redução)")
    
    return stats


def main():
    """
    Função principal para minificar todos os assets
    """
    print("=" * 60)
    print("MINIFICAÇÃO DE ASSETS")
    print("=" * 60)
    
    all_stats = {
        'css': None,
        'js': None,
        'total_original': 0,
        'total_minified': 0
    }
    
    # Minificar CSS
    print("\n📄 Minificando arquivos CSS...")
    css_stats = process_directory('static/css', 'static/css', 'css', minify_css)
    all_stats['css'] = css_stats
    all_stats['total_original'] += css_stats['original_size']
    all_stats['total_minified'] += css_stats['minified_size']
    
    # Minificar JS
    print("\n📄 Minificando arquivos JavaScript...")
    js_stats = process_directory('static/js', 'static/js', 'js', minify_js)
    all_stats['js'] = js_stats
    all_stats['total_original'] += js_stats['original_size']
    all_stats['total_minified'] += js_stats['minified_size']
    
    # Calcular redução total
    total_reduction = ((all_stats['total_original'] - all_stats['total_minified']) / 
                      all_stats['total_original'] * 100) if all_stats['total_original'] > 0 else 0
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DA MINIFICAÇÃO")
    print("=" * 60)
    print(f"CSS: {css_stats['files_processed']} arquivos processados")
    print(f"JS: {js_stats['files_processed']} arquivos processados")
    print(f"\nTamanho original total: {all_stats['total_original']:,} bytes")
    print(f"Tamanho minificado total: {all_stats['total_minified']:,} bytes")
    print(f"Redução total: {total_reduction:.1f}%")
    print(f"Economia: {all_stats['total_original'] - all_stats['total_minified']:,} bytes")
    
    # Salvar relatório
    report_path = 'static/minification_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Relatório salvo em: {report_path}")
    print("=" * 60)


if __name__ == '__main__':
    main()
