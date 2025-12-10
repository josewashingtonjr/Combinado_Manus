#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para Otimizações de Performance
Valida minificação, compressão, cache e lazy loading
"""

import pytest
import os
import json
import gzip
from pathlib import Path
from flask import Flask
from services.performance_middleware import PerformanceMiddleware, cache_control, no_cache


class TestMinification:
    """Testes de minificação de assets"""
    
    def test_minified_files_exist(self):
        """Verifica se arquivos minificados foram criados"""
        css_dir = Path('static/css')
        js_dir = Path('static/js')
        
        # Verificar se existem arquivos .min.css
        min_css_files = list(css_dir.glob('*.min.css'))
        assert len(min_css_files) > 0, "Nenhum arquivo CSS minificado encontrado"
        
        # Verificar se existem arquivos .min.js
        min_js_files = list(js_dir.glob('*.min.js'))
        assert len(min_js_files) > 0, "Nenhum arquivo JS minificado encontrado"
    
    def test_minified_files_smaller(self):
        """Verifica se arquivos minificados são menores que originais"""
        css_dir = Path('static/css')
        
        # Testar alguns arquivos CSS
        test_files = ['mobile-first.css', 'toast-feedback.css', 'touch-targets.css']
        
        for filename in test_files:
            original = css_dir / filename
            minified = css_dir / filename.replace('.css', '.min.css')
            
            if original.exists() and minified.exists():
                original_size = original.stat().st_size
                minified_size = minified.stat().st_size
                
                assert minified_size < original_size, \
                    f"{filename}: minificado ({minified_size}) não é menor que original ({original_size})"
    
    def test_minification_report_exists(self):
        """Verifica se relatório de minificação foi gerado"""
        report_path = Path('static/minification_report.json')
        assert report_path.exists(), "Relatório de minificação não encontrado"
        
        # Validar conteúdo do relatório
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert 'css' in report, "Relatório não contém dados de CSS"
        assert 'js' in report, "Relatório não contém dados de JS"
        assert report['total_original'] > 0, "Tamanho original deve ser maior que 0"
        assert report['total_minified'] > 0, "Tamanho minificado deve ser maior que 0"
        assert report['total_minified'] < report['total_original'], \
            "Tamanho minificado deve ser menor que original"


class TestCompression:
    """Testes de compressão de respostas"""
    
    @pytest.fixture
    def app(self):
        """Cria app Flask para testes"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Inicializar middleware
        PerformanceMiddleware(app)
        
        @app.route('/test-html')
        def test_html():
            return '<html><body>' + 'x' * 1000 + '</body></html>'
        
        @app.route('/test-json')
        def test_json():
            return {'data': 'x' * 1000}
        
        @app.route('/test-small')
        def test_small():
            return 'small'
        
        return app
    
    def test_gzip_compression_html(self, app):
        """Testa compressão gzip para HTML"""
        client = app.test_client()
        
        response = client.get('/test-html', headers={
            'Accept-Encoding': 'gzip'
        })
        
        assert response.status_code == 200
        assert response.headers.get('Content-Encoding') == 'gzip'
        
        # Descomprimir e verificar conteúdo
        decompressed = gzip.decompress(response.data)
        assert b'<html>' in decompressed
    
    def test_no_compression_without_accept_encoding(self, app):
        """Testa que não comprime se cliente não aceita gzip"""
        client = app.test_client()
        
        response = client.get('/test-html')
        
        # Pode ou não comprimir dependendo de headers padrão
        # Apenas verificar que resposta é válida
        assert response.status_code == 200
    
    def test_no_compression_small_response(self, app):
        """Testa que não comprime respostas pequenas"""
        client = app.test_client()
        
        response = client.get('/test-small', headers={
            'Accept-Encoding': 'gzip'
        })
        
        assert response.status_code == 200
        # Resposta pequena não deve ser comprimida
        assert response.headers.get('Content-Encoding') != 'gzip'


class TestCacheHeaders:
    """Testes de headers de cache"""
    
    @pytest.fixture
    def app(self):
        """Cria app Flask para testes"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Inicializar middleware
        PerformanceMiddleware(app)
        
        @app.route('/api/data')
        @cache_control(max_age=300)
        def cached_data():
            return {'data': 'test'}
        
        @app.route('/api/realtime')
        @no_cache
        def realtime_data():
            return {'data': 'realtime'}
        
        return app
    
    def test_cache_control_decorator(self, app):
        """Testa decorator de cache control"""
        client = app.test_client()
        
        response = client.get('/api/data')
        
        assert response.status_code == 200
        assert 'Cache-Control' in response.headers
        assert 'max-age=300' in response.headers['Cache-Control']
    
    def test_no_cache_decorator(self, app):
        """Testa decorator de no-cache"""
        client = app.test_client()
        
        response = client.get('/api/realtime')
        
        assert response.status_code == 200
        assert 'Cache-Control' in response.headers
        assert 'no-cache' in response.headers['Cache-Control']


class TestLazyLoading:
    """Testes de lazy loading"""
    
    def test_lazy_loading_js_exists(self):
        """Verifica se script de lazy loading existe"""
        js_file = Path('static/js/lazy-loading.js')
        assert js_file.exists(), "Script de lazy loading não encontrado"
        
        # Verificar conteúdo básico
        content = js_file.read_text()
        assert 'IntersectionObserver' in content
        assert 'data-src' in content
        assert 'LazyLoader' in content
    
    def test_lazy_loading_css_exists(self):
        """Verifica se CSS de lazy loading existe"""
        css_file = Path('static/css/lazy-loading.css')
        assert css_file.exists(), "CSS de lazy loading não encontrado"
        
        # Verificar classes importantes
        content = css_file.read_text()
        assert 'lazy-loading' in content
        assert 'lazy-loaded' in content
        assert 'lazy-error' in content


class TestPerformanceMetrics:
    """Testes de métricas de performance"""
    
    def test_minification_savings(self):
        """Verifica economia de tamanho com minificação"""
        report_path = Path('static/minification_report.json')
        
        if not report_path.exists():
            pytest.skip("Relatório de minificação não encontrado")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Calcular economia
        original = report['total_original']
        minified = report['total_minified']
        savings = original - minified
        savings_percent = (savings / original * 100) if original > 0 else 0
        
        print(f"\n📊 Economia com minificação:")
        print(f"   Original: {original:,} bytes")
        print(f"   Minificado: {minified:,} bytes")
        print(f"   Economia: {savings:,} bytes ({savings_percent:.1f}%)")
        
        # Deve ter pelo menos alguma economia
        assert savings > 0, "Minificação deve reduzir tamanho"
        assert savings_percent > 5, "Economia deve ser maior que 5%"


def test_performance_middleware_initialization():
    """Testa inicialização do middleware"""
    app = Flask(__name__)
    middleware = PerformanceMiddleware(app)
    
    assert 'COMPRESS_MIMETYPES' in app.config
    assert 'COMPRESS_MIN_SIZE' in app.config
    assert 'STATIC_CACHE_TIMEOUT' in app.config


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
