from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from functools import wraps
from datetime import datetime
import pandas as pd
import io

from models import User, Equipamento, Predio, Sala, HistoricoCheckpoint, Notificacao, db
from config import Config

main = Blueprint("main", __name__)

# --- Funções Auxiliares ---

def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso negado. Você precisa ser um Administrador.', 'danger')
            return redirect(url_for('main.dashboard'))
        return func(*args, **kwargs)
    return wrapper

def get_estoque_padrao():
    sala = Sala.query.get(Config.ESTOQUE_PADRAO_ID)
    if not sala:
        flash("Sala de estoque padrão não encontrada.", "danger")
    return sala

# --- Autenticação ---

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Login bem-sucedido. Bem-vindo(a), {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('main.login'))

# --- Dashboard ---

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    total_equipamentos = Equipamento.query.count()
    status_counts = db.session.query(
        Equipamento.status_atual, func.count(Equipamento.id)
    ).group_by(Equipamento.status_atual).all()

    metrics = {'total': total_equipamentos, 'Em Estoque': 0, 'Em Trânsito': 0, 'Em Uso': 0, 'Outros': 0}
    for status, count in status_counts:
        key = 'Em Uso' if status.startswith('Em Uso') else status
        if key in metrics:
            metrics[key] = count
        else:
            metrics['Outros'] += count

    notificacoes = Notificacao.query.filter_by(usuario_alvo=current_user, lida=False)\
        .order_by(Notificacao.data_criacao.desc()).limit(5).all()

    return render_template('dashboard.html', metrics=metrics, notificacoes=notificacoes,
                           notificacoes_nao_lidas_count=len(notificacoes))

# --- Cadastro Individual de Equipamento ---

@main.route('/cadastrar_equipamento', methods=['GET', 'POST'])
@admin_required
def cadastrar_equipamento():
    estoque_sala = get_estoque_padrao()
    if not estoque_sala:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie').strip().upper()
        nome_equipamento = request.form.get('nome_equipamento').strip()

        if Equipamento.query.filter_by(numero_serie=numero_serie).first():
            flash(f'Equipamento com o Nº de Série "{numero_serie}" já existe.', 'warning')
            return redirect(url_for('main.cadastrar_equipamento'))

        novo = Equipamento(
            numero_serie=numero_serie, nome_equipamento=nome_equipamento,
            status_atual='Em Estoque', localizacao_atual_id=estoque_sala.id,
            responsavel_cadastro_id=current_user.id
        )
        db.session.add(novo)
        db.session.flush()

        checkpoint = HistoricoCheckpoint(
            equipamento_id=novo.id, status_anterior='N/A (Cadastro)', status_novo='Em Estoque',
            predio_destino_id=estoque_sala.predio.id, sala_destino_id=estoque_sala.id,
            responsavel_alteracao_id=current_user.id
        )
        db.session.add(checkpoint)
        db.session.commit()
        flash(f'Equipamento "{nome_equipamento}" cadastrado com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('cadastrar_equipamento.html', estoque_sala=estoque_sala)

# --- Upload em Lote ---

@main.route('/upload_equipamentos', methods=['GET', 'POST'])
@admin_required
def upload_equipamentos():
    # (mantido igual ao seu código original)
    pass

# --- Exportação de Dados ---

@main.route('/exportar_dados', methods=['GET'])
@admin_required
def exportar_dados():
    # (mantido igual ao seu código original)
    pass

# --- Gerenciar Locais ---

@main.route('/gerenciar_locais', methods=['GET', 'POST'])
@admin_required
def gerenciar_locais():
    # (mantido igual ao seu código original)
    pass

# --- Checkin / Checkout / Retorno ---

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # (mantido igual ao seu código original)
    pass

@main.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    # (mantido igual ao seu código original)
    pass

@main.route('/retorno_estoque', methods=['GET', 'POST'])
@login_required
def retorno_estoque():
    # (mantido igual ao seu código original)
    pass

# --- Teste ---

@main.route('/teste')
def teste():
    return "<h1>Aplicação online</h1>"
