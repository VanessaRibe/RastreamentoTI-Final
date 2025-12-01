from flask import Flask
from flask_login import LoginManager
from auth import auth as auth_blueprint

app = Flask(__name__)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@app.route("/")
def index():
    return "<h1>Sistema online</h1>"

app.register_blueprint(auth_blueprint)
