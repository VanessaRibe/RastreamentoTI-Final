# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuração principal para o Flask e SQLAlchemy."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-muito-secreta-e-dificil'

    # Caminho do DB para a raiz do projeto (caminho absoluto)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Manter a pasta de QR Codes, embora a geração de imagens não seja mais usada
    QR_CODE_FOLDER = os.path.join(basedir, 'static/qrcodes')
    ESTOQUE_PADRAO_ID = 1