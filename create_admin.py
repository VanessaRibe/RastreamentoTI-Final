# create_admin.py

from extensions import db
from models import User, Predio, Sala
from config import Config
import sys


def initialize_database():
    """Cria o Admin, Locais Iniciais e garante a criação da estrutura."""

    from app import create_app
    app = create_app()

    with app.app_context():
        print("--- Iniciando Inicialização de Dados ---")

        # 1. Deleção Forçada do Usuário Admin
        try:
            admin_existente = User.query.filter_by(username='admin').first()
            if admin_existente:
                db.session.delete(admin_existente)
                db.session.commit()
                print("Usuário Admin existente DELETADO para recriação.")
        except Exception as e:
            print("Aviso: Falha na deleção do admin existente. Prosseguindo com a criação.")
            db.session.rollback()

        # 2. Criação do Usuário Admin Padrão
        admin_user = User(username='Sanar Admin', is_admin=True)
        admin_user.set_password('Cetrus2207')
        db.session.add(admin_user)

        # 3. Limpeza dos Locais (Recriação para garantir ID 1)
        db.session.query(Sala).delete()
        db.session.query(Predio).delete()
        db.session.commit()
        print("Locais antigos limpos. Recriando locais...")

        # 4. Criação dos Locais Iniciais
        locais_iniciais = [
            ('Sede Principal', 'Estoque TI Central'),
            ('Sede Principal', 'Sala 101 - TI'),
            ('Filial Norte', 'Estoque TI Filial'),
        ]

        predios_criados = {}
        for predio_nome, _ in locais_iniciais:
            if predio_nome not in predios_criados:
                predio = Predio(nome=predio_nome)
                db.session.add(predio)
                db.session.flush()
                predios_criados[predio_nome] = predio

        for predio_nome, sala_nome in locais_iniciais:
            predio = predios_criados[predio_nome]
            nova_sala = Sala(nome=sala_nome, predio=predio)
            db.session.add(nova_sala)

        db.session.commit()
        print("Sucesso: Locais (Prédios/Salas) iniciais recriados.")
        print("Sucesso: Usuário Admin (admin/admin123) criado.")

        print("\n--- Inicialização Concluída ---")


if __name__ == '__main__':
    initialize_database()