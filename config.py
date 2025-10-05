import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "uma-chave-secreta-muito-forte")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://combinado_user:combinado_pass@localhost/combinado_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

