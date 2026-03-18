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

    # --- BLOCO DE RECUPERAÇÃO DE ADMIN (ATIVADO PARA: Sanar Adm) ---
    with app.app_context():
        # Garante que as tabelas existam antes de buscar o usuário
        db.create_all()
        
        # Busca e promove o seu usuário específico
        user_to_promote = User.query.filter_by(username='Sanar Adm').first()
        if user_to_promote:
            user_to_promote.is_admin = True
            db.session.commit()
            print(f"SUCESSO: O usuario {user_to_promote.username} agora é ADMINISTRADOR!")
        else:
            print("AVISO: Usuario 'Sanar Adm' nao encontrado no banco de dados.")
    # --------------------------------------------------------------

    app.register_blueprint(main)

    return app

app = create_app()
