from flask import Flask
from flask_login import LoginManager
from extensions import db
from auth import auth as auth_blueprint
from main import main as main_blueprint
from models import User
from create_admin import initialize_database
import os

app = Flask(__name__)

# Configuração do banco
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "sua_chave_secreta_aqui"  # Troque por uma chave segura

db.init_app(app)

# Configuração do login
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota principal
@app.route("/")
def index():
    return "<h1>Sistema online</h1>"

# Rota de setup inicial (executa create_admin.py)
@app.route("/setup")
def setup():
    initialize_database()
    return "<h1>Setup executado com sucesso.</h1>"

# Registro dos blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
