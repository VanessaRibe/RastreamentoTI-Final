from flask import Flask
from flask_login import LoginManager
from auth import auth as auth_blueprint

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@app.route("/teste")
@login_required
def teste():
    return "<h1>Aplicação online</h1>"

app = Flask(__name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(auth_blueprint)

