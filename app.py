import os
from flask import Flask
from extensions import db, migrate, login_manager
from models import User
from main import main

def create_app():
    app = Flask(__name__)
    
    # Configurações de Segurança e Banco de Dados
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "chave_local_segura")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///app.db")

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # O Flask-Login usa isso para recarregar o usuário da sessão
        return User.query.get(int(user_id))

    # Registro das rotas (Blueprints)
    app.register_blueprint(main)

    return app

# Ponto de entrada para o servidor (Gunicorn/Flask)
app = create_app()
