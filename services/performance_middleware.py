# -*- coding: utf-8 -*-
"""
Middleware de Performance
Implementa compressão, cache e otimizações para melhorar performance
"""

from flask import request, make_response
from functools import wraps
import gzip
import io
from datetime import datetime, timedelta


class PerformanceMiddleware:
    """
    Middleware para otimizações de performance
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Inicializa middleware com a aplicação Flask
        """
        # Configurações padrão
        app.config.setdefault('COMPRESS_MIMETYPES', [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'text/xml',
            'application/xml',
            'image/svg+xml'
        ])
        app.config.setdefault('COMPRESS_MIN_SIZE', 500)  # bytes
        app.config.setdefault('COMPRESS_LEVEL', 6)  # 1-9
        
        # Cache para assets estáticos (1 ano)
        app.config.setdefault('STATIC_CACHE_TIMEOUT', 31536000)
        
        # Registrar hooks
        app.after_request(self.compress_response)
        app.after_request(self.add_cache_headers)
    
    def compress_response(self, response):
        """
        Comprime resposta se o cliente suportar gzip
        """
        # Verificar se deve comprimir
        if not self._should_compress(response):
            return response
        
        # Verificar se cliente aceita gzip
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding.lower():
            return response
        
        # Comprimir conteúdo
        try:
            original_data = response.get_data()
            
            gzip_buffer = io.BytesIO()
            gzip_file = gzip.GzipFile(
                mode='wb',
                compresslevel=self.app.config['COMPRESS_LEVEL'],
                fileobj=gzip_buffer
            )
            gzip_file.write(original_data)
            gzip_file.close()
            
            # Criar nova resposta comprimida
            compressed_data = gzip_buffer.getvalue()
            
            # Só usar se realmente reduziu o tamanho
            if len(compressed_data) < len(original_data):
                response.set_data(compressed_data)
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed_data)
                response.headers['Vary'] = 'Accept-Encoding'
        
        except (RuntimeError, Exception) as e:
            # Em caso de erro (incluindo passthrough mode), retornar resposta original
            if 'passthrough' not in str(e).lower():
                self.app.logger.warning(f'Erro ao comprimir resposta: {e}')
        
        return response
    
    def _should_compress(self, response):
        """
        Verifica se a resposta deve ser comprimida
        """
        # Não comprimir se está em modo direct passthrough (arquivos estáticos)
        if response.direct_passthrough:
            return False
        
        # Não comprimir se já está comprimido
        if response.headers.get('Content-Encoding'):
            return False
        
        # Não comprimir se status não for 200
        if response.status_code != 200:
            return False
        
        # Verificar mimetype
        content_type = response.headers.get('Content-Type', '')
        mimetype = content_type.split(';')[0].strip()
        
        if mimetype not in self.app.config['COMPRESS_MIMETYPES']:
            return False
        
        # Não comprimir respostas pequenas
        content_length = response.headers.get('Content-Length', type=int)
        if content_length and content_length < self.app.config['COMPRESS_MIN_SIZE']:
            return False
        
        # Verificar se o tamanho do conteúdo é grande o suficiente
        try:
            if len(response.get_data()) < self.app.config['COMPRESS_MIN_SIZE']:
                return False
        except RuntimeError:
            # Resposta em modo passthrough, não comprimir
            return False
        
        return True
    
    def add_cache_headers(self, response):
        """
        Adiciona headers de cache apropriados
        """
        # Apenas para assets estáticos
        if not request.path.startswith('/static/'):
            return response
        
        # Verificar se é arquivo minificado
        is_minified = '.min.' in request.path
        
        # Definir tempo de cache
        if is_minified:
            # Arquivos minificados: cache longo (1 ano)
            max_age = self.app.config['STATIC_CACHE_TIMEOUT']
            response.headers['Cache-Control'] = f'public, max-age={max_age}, immutable'
        else:
            # Arquivos normais: cache moderado (1 dia)
            max_age = 86400
            response.headers['Cache-Control'] = f'public, max-age={max_age}'
        
        # Adicionar ETag para validação
        if not response.headers.get('ETag'):
            etag = self._generate_etag(response)
            if etag:
                response.headers['ETag'] = etag
        
        # Adicionar Expires header
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        response.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return response
    
    def _generate_etag(self, response):
        """
        Gera ETag simples baseado no conteúdo
        """
        try:
            # Não gerar ETag para respostas em modo passthrough
            if response.direct_passthrough:
                return None
            import hashlib
            content = response.get_data()
            return f'"{hashlib.md5(content).hexdigest()}"'
        except (RuntimeError, Exception):
            return None


def cache_control(max_age=3600, public=True):
    """
    Decorator para adicionar cache control em rotas específicas
    
    Uso:
        @app.route('/api/data')
        @cache_control(max_age=300)
        def get_data():
            return jsonify(data)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            
            cache_type = 'public' if public else 'private'
            response.headers['Cache-Control'] = f'{cache_type}, max-age={max_age}'
            
            return response
        return decorated_function
    return decorator


def no_cache(f):
    """
    Decorator para desabilitar cache em rotas específicas
    
    Uso:
        @app.route('/api/realtime')
        @no_cache
        def get_realtime():
            return jsonify(data)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function
