from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Equipamento, Notificacao
from sqlalchemy import func
from extensions import db  # Certifique-se que o extensions.py exporta db corretamente

main = Blueprint("main", __name__)

# --- Rota de teste ---
@main.route("/teste")
def teste():
    return "<h1>Aplicação online</h1>"

# --- Dashboard corrigido ---
@main.route("/dashboard")
@login_required
def dashboard():
    total_equipamentos = Equipamento.query.count()

    status_counts = db.session.query(
        Equipamento.status_atual, func.count(Equipamento.id)
    ).group_by(Equipamento.status_atual).all()

    metrics = {
        "total": total_equipamentos,
        "Em Estoque": 0,
        "Em Trânsito": 0,
        "Em Uso": 0,
        "Outros": 0
    }

    for status, count in status_counts:
        key = "Em Uso" if status.startswith("Em Uso") else status
        if key in metrics:
            metrics[key] = count
        else:
            metrics["Outros"] += count

    notificacoes = Notificacao.query.filter_by(
        usuario_alvo=current_user, lida=False
    ).order_by(Notificacao.data_criacao.desc()).limit(5).all()

    return render_template("dashboard.html", metrics=metrics, notificacoes=notificacoes)

# --- Cadastro de usuário básico ---
# ⚠️ IMPORTANTE: essa rota deve estar em auth.py, não em main.py
# Se você quiser manter aqui, certifique-se de que app.py registra apenas main_blueprint
# Caso contrário, mova para auth.py e troque @main.route por @auth.route

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
