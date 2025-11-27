# create_admin.py (Refatorado para ser chamado pelo app.py)

from extensions import db
from models import User, Predio, Sala
from config import Config
import sys


def initialize_database():
    """Cria o Admin e Locais Iniciais. Chamado apenas se o DB estiver vazio."""

    # Este código será chamado dentro do app_context, no app.py

    print("--- Inicializando Dados ---")

    # 1. Criação do Usuário Admin Padrão
    admin_user = User(username='Sanar Admin', is_admin=True)
    admin_user.set_password('Cetrus2207')  # <<< DEFINA SUA SENHA!
    db.session.add(admin_user)

    # 2. Limpeza e Criação dos Locais (Garantindo ID 1)
    # Limpamos apenas para garantir um estado limpo.
    db.session.query(Sala).delete()
    db.session.query(Predio).delete()
    db.session.commit()
    print("Locais antigos limpos. Recriando locais...")

    # 3. Criação dos Locais Iniciais
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
    print("Sucesso: Locais iniciais criados.")
    print("Sucesso: Usuário Admin criado.")

# O bloco if __name__ == '__main__': é removido para que o app.py possa importar.