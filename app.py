from flask import Flask
from extensions import db
from flask_login import LoginManager
from models import User
from main import main

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # ou DATABASE_URL do Render

    # Inicializar extensões
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    app.register_blueprint(main)

    return app

# Objeto app que o gunicorn vai usar
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
