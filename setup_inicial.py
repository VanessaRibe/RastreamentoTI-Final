# setup_inicial.py

from app import create_app
from create_admin import initialize_database
from extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    initialize_database()
