import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-forte")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///test_combinado.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class TestConfig(Config):
    """Configuração de teste"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Banco de dados em memória para testes
    WTF_CSRF_ENABLED = False  # Desabilitar CSRF em testes
    SESSION_COOKIE_SECURE = False

