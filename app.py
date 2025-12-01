from flask import Flask
from flask_login import LoginManager, login_required
from auth import auth as auth_blueprint

app = Flask(__name__)  # Primeiro: cria o app

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)  # Agora sim: usa o app

@app.route("/teste")
@login_required
def teste():
    return "<h1>Aplicação online</h1>"
@app.route("/")
def index():
    return "<h1>Sistema online</h1>"


app.register_blueprint(auth_blueprint)
