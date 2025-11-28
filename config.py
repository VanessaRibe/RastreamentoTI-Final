import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuração principal para o Flask e SQLAlchemy."""

    # Chave secreta para sessões e segurança
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sanar-chave-rastreamento')

    # Banco de dados: usa PostgreSQL se DATABASE_URL estiver definida, senão SQLite local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(basedir, 'app.db')}")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pasta onde os QR codes serão salvos
    QR_CODE_FOLDER = os.path.join(basedir, 'static', 'qrcodes')

    # ID padrão do estoque
    ESTOQUE_PADRAO_ID = 1
