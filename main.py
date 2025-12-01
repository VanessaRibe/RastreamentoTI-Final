from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Equipamento, Notificacao
from sqlalchemy import func

main = Blueprint("main", __name__)

# --- Rota de teste ---
@main.route("/teste")
def teste():
    return "<h1>Aplicação online</h1>"

# --- Dashboard simplificado ---
@main.route("/dashboard")
@login_required
def dashboard():
    total_equipamentos = Equipamento.query.count()

    status_counts = func.count(Equipamento.id)
    metrics = {
        "total": total_equipamentos,
        "Em Estoque": 0,
        "Em Trânsito": 0,
        "Em Uso": 0,
        "Outros": 0
    }

    notificacoes = Notificacao.query.filter_by(
        usuario_alvo=current_user, lida=False
    ).order_by(Notificacao.data_criacao.desc()).limit(5).all()

    return render_template("dashboard.html", metrics=metrics, notificacoes=notificacoes)

# --- Cadastro de usuário (exemplo básico) ---
@main.route("/cadastrar_usuario", methods=["GET", "POST"])
@login_required
def cadastrar_usuario():
    if not current_user.is_admin:
        flash("Acesso negado. Apenas administradores podem cadastrar usuários.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        matricula = request.form.get("matricula")
        flash(f"Usuário {username} cadastrado com sucesso!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("cadastrar_usuario.html")
