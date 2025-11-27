# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuração principal para o Flask e SQLAlchemy."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sanar-chave-ratreamento'

    # Caminho do DB para a raiz do projeto (caminho absoluto)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    QR_CODE_FOLDER = os.path.join(basedir, 'static/qrcodes')
    ESTOQUE_PADRAO_ID = 1