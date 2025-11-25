# app.py

import os
from flask import Flask
from flask_login import current_user
from config import Config
from extensions import db, login_manager
from models import Notificacao, User
from routes import main as main_blueprint


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Inicializa Extensões
    db.init_app(app)
    login_manager.init_app(app)

    # 2. Configura o User Loader (Proteção contra OperationalError)
    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            return User.query.get(int(user_id))

    # 3. CRIAÇÃO OBRIGATÓRIA DA TABELA
    with app.app_context():
        db.create_all()

        # 4. Cria a pasta para os QR Codes
    os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

    # 5. Registro dos Blueprints
    app.register_blueprint(main_blueprint)

    # 6. Context Processor para Notificações
    @app.context_processor
    def inject_notifications_count():
        if current_user.is_authenticated:
            with app.app_context():
                count = Notificacao.query.filter_by(
                    usuario_alvo_id=current_user.id, lida=False
                ).count()
            return dict(notificacoes_nao_lidas_count=count)
        return dict(notificacoes_nao_lidas_count=0)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)