from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Equipamento, Notificacao, HistoricoCheckpoint, Predio, Sala
from sqlalchemy import func
from extensions import db
import pandas as pd
from werkzeug.utils import secure_filename
import os
import qrcode

main = Blueprint("main", __name__)

# Pasta para uploads
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xlsx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Função auxiliar para registrar histórico ---
def registrar_checkpoint(equipamento, status_anterior, status_novo, usuario, predio_destino=None, sala_destino=None):
    checkpoint = HistoricoCheckpoint(
        equipamento_id=equipamento.id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        predio_destino_id=predio_destino.id if predio_destino else None,
        sala_destino_id=sala_destino.id if sala_destino else None,
        responsavel_alteracao_id=usuario.id
    )
    db.session.add(checkpoint)
    db.session.commit()

# --- Função auxiliar para criar notificações ---
def criar_notificacao(mensagem, usuario_alvo_id, equipamento_id=None):
    notificacao = Notificacao(
        mensagem=mensagem,
        usuario_alvo_id=usuario_alvo_id,
        equipamento_id=equipamento_id
    )
    db.session.add(notificacao)
    db.session.commit()

# --- Função auxiliar para gerar QR Code ---
def gerar_qrcode(equipamento):
    url = url_for("main.historico_equipamento", equipamento_id=equipamento.id, _external=True)
    qr = qrcode.make(url)
    path = f"static/qrcodes/{equipamento.numero_serie}.png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    qr.save(path)
    equipamento.qr_code_path = path
    db.session.commit()
    return path

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
    status_anterior = equipamento.status_atual
    equipamento.status_atual = "Em Trânsito"
    db.session.commit()

    registrar_checkpoint(equipamento, status_anterior, equipamento.status_atual, current_user)
    criar_notificacao(f"Equipamento {equipamento.nome_equipamento} saiu em trânsito.", current_user.id, equipamento.id)

    flash("Equipamento em trânsito.", "info")
    return redirect(url_for("main.dashboard"))

# --- Check-in de equipamento ---
@main.route("/checkin/<int:equipamento_id>", methods=["POST"])
@login_required
def checkin(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    status_anterior = equipamento.status_atual
    equipamento.status_atual = "Em Uso"
    equipamento.localizacao_atual_id = request.form.get("sala_id")
    db.session.commit()

    sala_destino = Sala.query.get(equipamento.localizacao_atual_id) if equipamento.localizacao_atual_id else None
    predio_destino = sala_destino.predio if sala_destino else None

    registrar_checkpoint(equipamento, status_anterior, equipamento.status_atual, current_user, predio_destino, sala_destino)
    criar_notificacao(f"Equipamento {equipamento.nome_equipamento} está em uso.", current_user.id, equipamento.id)

    flash("Equipamento em uso.", "success")
    return redirect(url_for("main.dashboard"))

# --- Retorno ao estoque ---
@main.route("/retorno/<int:equipamento_id>", methods=["POST"])
@login_required
def retorno_estoque(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    status_anterior = equipamento.status_atual
    equipamento.status_atual = "Em Estoque"
    equipamento.localizacao_atual_id = request.form.get("sala_id")
    db.session.commit()

    sala_destino = Sala.query.get(equipamento.localizacao_atual_id) if equipamento.localizacao_atual_id else None
    predio_destino = sala_destino.predio if sala_destino else None

    registrar_checkpoint(equipamento, status_anterior, equipamento.status_atual, current_user, predio_destino, sala_destino)
    criar_notificacao(f"Equipamento {equipamento.nome_equipamento} retornou ao estoque.", current_user.id, equipamento.id)

    flash("Equipamento retornado ao estoque.", "success")
    return redirect(url_for("main.dashboard"))

# --- Upload em lote via Excel ---
@main.route("/upload_equipamentos", methods=["GET", "POST"])
@login_required
def upload_equipamentos():
    if request.method == "POST":
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            df = pd.read_excel(filepath)

            for _, row in df.iterrows():
                equipamento = Equipamento(
                    numero_serie=row["numero_serie"],
                    nome_equipamento=row["nome_equipamento"],
                    status_atual=row.get("status_atual", "Em Estoque"),
                    localizacao_atual_id=row.get("sala_id"),
                    responsavel_cadastro_id=current_user.id
                )
                db.session.add(equipamento)

            db.session.commit()
            flash("Equipamentos cadastrados em lote com sucesso!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Arquivo inválido. Envie um Excel (.xlsx).", "danger")

    return render_template("upload_equipamentos.html")

# --- Histórico de movimentações ---
@main.route("/historico/<int:equipamento_id>")
@login_required
def historico_equipamento(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    historico = HistoricoCheckpoint.query.filter_by(
        equipamento_id=equipamento.id
    ).order_by(HistoricoCheckpoint.data_alteracao.desc()).all()

    return render_template("historico_equipamento.html", equipamento=equipamento, historico=historico)

# --- Gerenciar Locais (Prédio e Sala) ---

@main.route("/gerenciar_locais", methods=["GET", "POST"])
@login_required
def gerenciar_locais():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        nome = request.form.get("nome")
        predio_id = request.form.get("predio_id")

        if tipo == "predio":
            novo_predio = Predio(nome=nome)
            db.session.add(novo_predio)
            db.session.commit()
            flash("Prédio cadastrado com sucesso!", "success")

        elif tipo == "sala":
            nova_sala = Sala(nome=nome, predio_id=predio_id)
            db.session.add(nova_sala)
            db.session.commit()
            flash("Sala cadastrada com sucesso!", "success")

        return redirect(url_for("main.gerenciar_locais"))

    predios = Predio.query.all()
    salas = Sala.query.all()
    return render_template("gerenciar_locais.html", predios=predios, salas=salas)

# --- Marcar notificação como lida ---
@main.route("/notificacao/<int:notificacao_id>/lida", methods=["POST"])
@login_required
def marcar_notificacao_lida(notificacao_id):
    notificacao = Notificacao.query.get_or_404(notificacao_id)
    notificacao.lida = True
    db.session.commit()
    flash("Notificação marcada como lida.", "info")
    return redirect(url_for("main.dashboard"))
