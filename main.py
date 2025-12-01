from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Equipamento, Notificacao
from sqlalchemy import func
from extensions import db

main = Blueprint("main", __name__)

# --- Rota de teste ---
@main.route("/teste")
def teste():
    return "<h1>Aplicação online</h1>"

# --- Dashboard ---
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

# --- Cadastro de usuário ---
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

# --- Check-out de equipamento ---
@main.route("/checkout/<int:equipamento_id>", methods=["POST"])
@login_required
def checkout(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    equipamento.status_atual = "Em Trânsito"
    equipamento.usuario_responsavel = current_user.nome
    db.session.commit()
    flash("Equipamento em trânsito.", "info")
    return redirect(url_for("main.dashboard"))

# --- Check-in de equipamento ---
@main.route("/checkin/<int:equipamento_id>", methods=["POST"])
@login_required
def checkin(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    equipamento.status_atual = "Em Uso"
    equipamento.localizacao_atual = request.form.get("localizacao")
    db.session.commit()
    flash("Equipamento em uso.", "success")
    return redirect(url_for("main.dashboard"))

@main.route("/retorno/<int:equipamento_id>", methods=["POST"])
@login_required
def retorno_estoque(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    equipamento.status_atual = "Em Estoque"
    equipamento.localizacao_atual = request.form.get("localizacao")
    equipamento.usuario_responsavel = None  # remove vínculo com usuário
    db.session.commit()
    flash("Equipamento retornado ao estoque.", "success")
    return redirect(url_for("main.dashboard"))
