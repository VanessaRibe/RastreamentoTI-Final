import os
from flask import Flask
from extensions import db, migrate, login_manager
from models import User
from main import main

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "chave_local_segura")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///app.db")

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- NOVO BLOCO DE RECUPERAÇÃO ---
    with app.app_context():
        db.create_all()
        
        # 1. Tenta promover o usuário exato
        target = User.query.filter_by(username='Sanar Adm').first()
        
        # 2. Se não achar, tenta buscar ignorando maiúsculas/minúsculas
        if not target:
            target = User.query.filter(User.username.ilike('sanar adm')).first()
            
        # 3. Se ainda assim não achar, promove o PRIMEIRO usuário do banco (Garantia)
        if not target:
            target = User.query.first()

        if target:
            target.is_admin = True
            db.session.commit()
            print(f"USUARIO PROMOVIDO: {target.username}")
    # ---------------------------------

    app.register_blueprint(main)

    return app

app = create_app()
