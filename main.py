from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import User
from extensions import db

main = Blueprint("main", __name__)

def get_notificacoes_nao_lidas():
    # Substitua por lógica real se tiver modelo de notificações
    return 0

@main.route("/dashboard")
@login_required
def dashboard():
    notificacoes = get_notificacoes_nao_lidas()
    return render_template("dashboard.html", notificacoes_nao_lidas_count=notificacoes)

@main.route("/cadastrar_usuario", methods=["GET", "POST"])
@login_required
def cadastrar_usuario():
    if not current_user.is_admin:
        return "<h1>Acesso negado</h1>", 403

    if request.method == "POST":
        username = request.form["username"]
        email = request.form.get("email")
        matricula = request.form.get("matricula")
        password = request.form["password"]
        is_admin = "is_admin" in request.form

        novo_usuario = User(
            username=username,
            email=email,
            matricula=matricula,
            is_admin=is_admin
        )
        novo_usuario.set_password(password)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for("main.cadastrar_usuario"))

    usuarios = User.query.all()
    notificacoes = get_notificacoes_nao_lidas()
    return render_template("cadastrar_usuario.html", usuarios=usuarios, notificacoes_nao_lidas_count=notificacoes)
