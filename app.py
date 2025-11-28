import os
from flask import Flask
from flask_login import current_user
from config import Config
from extensions import db, login_manager
from models import Notificacao, User
from create_admin import initialize_database
from routes import main as main_blueprint

def create_app(config_class=Config):
    """Função Factory para criar a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Inicializa Extensões
    db.init_app(app)
    login_manager.init_app(app)

    # 2. Configura o User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 3. Criação e verificação do banco de dados
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            print("=== EXECUTANDO SETUP INICIAL DE DADOS AUTOMATICAMENTE ===")
            initialize_database()
            print("=== SETUP INICIAL COMPLETO. ===")

    # 4. Criação da pasta de QR Codes
    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

    # 5. Registro dos Blueprints
    app.register_blueprint(main_blueprint)

    # 6. Context Processor para notificações
    @app.context_processor
    def inject_notifications_count():
        if current_user.is_authenticated:
            count = Notificacao.query.filter_by(
                usuario_alvo_id=current_user.id, lida=False
            ).count()
            return dict(notificacoes_nao_lidas_count=count)
        return dict(notificacoes_nao_lidas_count=0)

    return app

# --- Ponto de entrada local ---
    create_app().run()

# --- Ponto de entrada para Gunicorn/Railway ---
app = create_app()

@app.route("/")
def home():
    return redirect(url_for('main.public_home'))





