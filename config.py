import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-forte")
    # Usar caminho absoluto para o banco de dados
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'instance', 'test_combinado.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    
    # Configurações de Pré-Ordem
    # Requirement 15.1: Prazo padrão de negociação (7 dias)
    PRE_ORDER_DEFAULT_NEGOTIATION_DAYS = int(os.environ.get("PRE_ORDER_NEGOTIATION_DAYS", 7))
    PRE_ORDER_EXPIRATION_WARNING_HOURS = 24  # Notificar 24h antes da expiração
    
    # Configurações de Performance (Requirement 8.1, 8.3, 8.5)
    # Compressão Gzip
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/json',
        'text/xml',
        'application/xml',
        'image/svg+xml'
    ]
    COMPRESS_MIN_SIZE = int(os.environ.get("COMPRESS_MIN_SIZE", 500))  # bytes
    COMPRESS_LEVEL = int(os.environ.get("COMPRESS_LEVEL", 6))  # 1-9
    
    # Cache de Assets Estáticos
    STATIC_CACHE_TIMEOUT = int(os.environ.get("STATIC_CACHE_TIMEOUT", 31536000))  # 1 ano
    
    # Usar assets minificados em produção
    USE_MINIFIED_ASSETS = os.environ.get("USE_MINIFIED_ASSETS", "true").lower() == "true"


class TestConfig(Config):
    """Configuração de teste"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Banco de dados em memória para testes
    WTF_CSRF_ENABLED = False  # Desabilitar CSRF em testes
    SESSION_COOKIE_SECURE = False

