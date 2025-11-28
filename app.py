from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from routes import main as main_blueprint

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # ✅ Aqui você configura o banco usando a variável do Railway
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(main_blueprint)

    return app

# ✅ Criação da instância do app
app = create_app()
