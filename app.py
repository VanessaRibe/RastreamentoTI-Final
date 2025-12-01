from flask import Flask
from flask_login import LoginManager
from auth import auth as auth_blueprint
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@app.route("/setup")
def setup():
    initialize_database()
    return "<h1>Setup executado com sucesso.</h1>"

@app.route("/")
def index():
    return "<h1>Sistema online</h1>"

app.register_blueprint(auth_blueprint)
