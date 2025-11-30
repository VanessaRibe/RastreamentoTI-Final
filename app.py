from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from routes import main as main_blueprint

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(main_blueprint)

    return app

app = create_app()
@app.route("/teste")
def teste():
    return "<h1>Aplicação online</h1>"
