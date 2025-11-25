# routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from functools import wraps
from datetime import datetime
import pandas as pd
import io
import os

# Importações dos Modelos e Extensões (Absolutas)
from models import User, Equipamento, Predio, Sala, HistoricoCheckpoint, Notificacao, db
from config import Config

main = Blueprint('main', __name__)


# --- Funções Auxiliares ---

def admin_required(func):
    """Decorador que garante que apenas usuários administradores acessem a rota."""

    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acesso negado. Você precisa ser um Administrador.', 'danger')
            return redirect(url_for('main.dashboard'))
        return func(*args, **kwargs)

    return wrapper


# --- Rotas de Autenticação e Dashboard ---

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    total_equipamentos = Equipamento.query.count()

    status_counts = db.session.query(Equipamento.status_atual, func.count(Equipamento.id)
                                     ).group_by(Equipamento.status_atual).all()

    metrics = {'total': total_equipamentos, 'Em Estoque': 0, 'Em Trânsito': 0, 'Em Uso': 0, 'Outros': 0}

    for status, count in status_counts:
        key = 'Em Uso' if status.startswith('Em Uso') else status
        if key in metrics:
            metrics[key] = count
        else:
            metrics['Outros'] += count

    notificacoes = Notificacao.query.filter_by(usuario_alvo=current_user, lida=False
                                               ).order_by(Notificacao.data_criacao.desc()).limit(5).all()

    return render_template('dashboard.html', metrics=metrics, notificacoes=notificacoes)


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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')

    return render_template('login.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('main.login'))


# --- ROTAS DE SEGURANÇA (Esqueci Minha Senha) ---

@main.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    """Solicita a redefinição de senha (SIMULAÇÃO DE BACKEND)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        flash(f'Se o e-mail {email} estiver cadastrado, um link de redefinição foi enviado.', 'info')
        return redirect(url_for('main.login'))

    return render_template('reset_request.html')


@main.route('/reset_token/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """Recebe o token do e-mail e permite definir a nova senha (SIMULAÇÃO)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        user_to_reset = User.query.filter_by(username='admin').first()
        user_to_reset.set_password(request.form.get('new_password'))
        db.session.commit()

        flash('Sua senha foi redefinida com sucesso! Faça login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_token.html')


# --- Cadastro de Usuário (Com Matrícula e Email) ---

@main.route('/cadastrar_usuario', methods=['GET', 'POST'])
@admin_required
def cadastrar_usuario():
    """Permite ao Admin criar novos usuários/técnicos."""
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        email = request.form.get('email', '').strip()
        matricula = request.form.get('matricula', '').strip()
        is_admin_check = request.form.get('is_admin') == 'on'

        if User.query.filter_by(username=username).first():
            flash(f'Usuário "{username}" já existe.', 'warning')
            return redirect(url_for('main.cadastrar_usuario'))

        novo_usuario = User(
            username=username,
            email=email,
            matricula=matricula,
            is_admin=is_admin_check
        )
        novo_usuario.set_password(password)

        db.session.add(novo_usuario)
        db.session.commit()
        flash(f'Usuário "{username}" criado com sucesso! (Matrícula: {matricula})', 'success')
        return redirect(url_for('main.dashboard'))

    usuarios = User.query.all()

    return render_template('cadastrar_usuario.html', usuarios=usuarios)


# --- ROTA CRÍTICA: Upload em Lote (Excel) ---

@main.route('/upload_equipamentos', methods=['GET', 'POST'])
@admin_required
def upload_equipamentos():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(url_for('main.upload_equipamentos'))

        file = request.files['file']

        if file.filename == '' or not file.filename.endswith(('.xlsx', '.xls')):
            flash('Arquivo inválido. Por favor, envie um arquivo Excel (.xlsx ou .xls).', 'danger')
            return redirect(url_for('main.upload_equipamentos'))

        try:
            df = pd.read_excel(file.stream, engine='openpyxl')

            df.columns = df.columns.str.upper()
            required_cols = ['NUMERO_SERIE', 'NOME_EQUIPAMENTO']
            if not all(col in df.columns for col in required_cols):
                raise ValueError("O arquivo Excel deve conter as colunas 'NUMERO_SERIE' e 'NOME_EQUIPAMENTO'.")

            estoque_sala = Sala.query.get(Config.ESTOQUE_PADRAO_ID)
            responsavel_id = current_user.id

            novos_equipamentos = []

            for index, row in df.iterrows():
                serie = str(row['NUMERO_SERIE']).strip().upper()
                nome = str(row['NOME_EQUIPAMENTO']).strip()

                if Equipamento.query.filter_by(numero_serie=serie).first():
                    flash(f'Série duplicada: {serie} foi ignorada.', 'warning')
                    continue

                if not serie or not nome:
                    flash(f'Linha {index + 2} ignorada: Série ou Nome vazios.', 'warning')
                    continue

                novo_equipamento = Equipamento(
                    numero_serie=serie, nome_equipamento=nome,
                    qr_code_path=None, status_atual='Em Estoque',
                    localizacao_atual_id=estoque_sala.id, responsavel_cadastro_id=responsavel_id
                )
                db.session.add(novo_equipamento)
                db.session.flush()

                primeiro_checkpoint = HistoricoCheckpoint(
                    equipamento_id=novo_equipamento.id, status_anterior='N/A (Lote)', status_novo='Em Estoque',
                    predio_destino_id=estoque_sala.predio.id, sala_destino_id=estoque_sala.id,
                    responsavel_alteracao_id=responsavel_id
                )
                db.session.add(primeiro_checkpoint)
                novos_equipamentos.append(serie)

            db.session.commit()
            flash(f'Sucesso! {len(novos_equipamentos)} equipamentos carregados via lote.', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro no processamento do arquivo: {e}', 'danger')
            return redirect(url_for('main.upload_equipamentos'))

    return render_template('upload_equipamentos.html')


# --- ROTA CRÍTICA: Exportação de Relatórios (Excel) ---

@main.route('/exportar_dados', methods=['GET'])
@admin_required
def exportar_dados():
    checkpoints = HistoricoCheckpoint.query.all()

    data = []
    for cp in checkpoints:
        data.append({
            'ID_CHECKPOINT': cp.id,
            'DATA_ALTERACAO': cp.data_alteracao,
            'NUMERO_SERIE': cp.equipamento.numero_serie if cp.equipamento else 'N/A',
            'STATUS_ANTERIOR': cp.status_anterior,
            'STATUS_NOVO': cp.status_novo,
            'LOCAL_DESTINO': f"{cp.sala_destino.nome} ({cp.predio_destino.nome})" if cp.sala_destino else 'N/A',
            'RESPONSAVEL': cp.responsavel_alteracao.username if cp.responsavel_alteracao else 'N/A'
        })

    if not data:
        flash('Nenhum dado de histórico encontrado para exportação.', 'warning')
        return redirect(url_for('main.dashboard'))

    df = pd.DataFrame(data)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Historico_Geral')

    output.seek(0)

    filename = f"Relatorio_TI_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output,
                     download_name=filename,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True)


# --- NOVO: Cadastro Individual de Equipamento ---

@main.route('/cadastrar_equipamento', methods=['GET', 'POST'])
@admin_required
def cadastrar_equipamento():
    """Permite o cadastro individual de um equipamento (código de barras)."""
    estoque_sala = Sala.query.get(Config.ESTOQUE_PADRAO_ID)
    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie').strip().upper()
        nome_equipamento = request.form.get('nome_equipamento').strip()

        if Equipamento.query.filter_by(numero_serie=numero_serie).first():
            flash(f'Equipamento com o Nº de Série "{numero_serie}" já existe.', 'warning')
            return redirect(url_for('main.cadastrar_equipamento'))

        novo_equipamento = Equipamento(
            numero_serie=numero_serie, nome_equipamento=nome_equipamento,
            qr_code_path=None, status_atual='Em Estoque',
            localizacao_atual_id=estoque_sala.id, responsavel_cadastro_id=current_user.id
        )
        db.session.add(novo_equipamento)
        db.session.flush()

        primeiro_checkpoint = HistoricoCheckpoint(
            equipamento_id=novo_equipamento.id, status_anterior='N/A (Cadastro)', status_novo='Em Estoque',
            predio_destino_id=estoque_sala.predio.id, sala_destino_id=estoque_sala.id,
            responsavel_alteracao_id=current_user.id
        )
        db.session.add(primeiro_checkpoint)
        db.session.commit()
        flash(f'Equipamento "{nome_equipamento}" cadastrado com sucesso!', 'success')

        return redirect(url_for('main.detalhes_equipamento', equipamento_id=novo_equipamento.id))

    return render_template('cadastrar_equipamento.html', estoque_sala=estoque_sala)


# --- Rotas de Gerenciamento (CRUD Locais) ---

@main.route('/gerenciar_locais', methods=['GET', 'POST'])
@admin_required
def gerenciar_locais():
    predios = Predio.query.order_by(Predio.nome).all()
    salas = Sala.query.join(Predio).order_by(Predio.nome, Sala.nome).all()

    if request.method == 'POST':
        action = request.form.get('action')
        nome = request.form.get('nome')

        if action == 'add_predio' and nome:
            if not Predio.query.filter_by(nome=nome).first():
                novo_predio = Predio(nome=nome)
                db.session.add(novo_predio)
                db.session.commit()
                flash(f'Prédio "{nome}" adicionado com sucesso.', 'success')
            else:
                flash(f'Prédio "{nome}" já existe.', 'warning')

        elif action == 'add_sala' and nome:
            predio_id = request.form.get('predio_id', type=int)
            predio = Predio.query.get(predio_id)
            if predio:
                if not Sala.query.filter_by(nome=nome, predio_id=predio_id).first():
                    nova_sala = Sala(nome=nome, predio=predio)
                    db.session.add(nova_sala)
                    db.session.commit()
                    flash(f'Sala "{nome}" adicionada em {predio.nome} com sucesso.', 'success')
                else:
                    flash(f'Sala "{nome}" já existe neste prédio.', 'warning')
            else:
                flash('Prédio não encontrado.', 'danger')

        return redirect(url_for('main.gerenciar_locais'))

    return render_template('gerenciar_locais.html', predios=predios, salas=salas)


@main.route('/deletar_predio/<int:predio_id>', methods=['POST'])
@admin_required
def deletar_predio(predio_id):
    predio = Predio.query.get_or_404(predio_id)
    if predio.salas.count() > 0:
        flash(f'Não é possível deletar o Prédio "{predio.nome}". Ele contém {predio.salas.count()} salas.', 'danger')
    else:
        db.session.delete(predio)
        db.session.commit()
        flash(f'Prédio "{predio.nome}" deletado com sucesso.', 'success')
    return redirect(url_for('main.gerenciar_locais'))


@main.route('/deletar_sala/<int:sala_id>', methods=['POST'])
@admin_required
def deletar_sala(sala_id):
    sala = Sala.query.get_or_404(sala_id)
    if sala.equipamentos.count() > 0:
        flash(
            f'Não é possível deletar a Sala "{sala.nome}". Ela contém {sala.equipamentos.count()} equipamentos ativos.',
            'danger')
    else:
        db.session.delete(sala)
        db.session.commit()
        flash(f'Sala "{sala.nome}" deletada com sucesso.', 'success')
    return redirect(url_for('main.gerenciar_locais'))


# --- Rotas de Rastreamento (Checkout/Checkin/Retorno) ---

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    predios = Predio.query.order_by(Predio.nome).all()
    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie').strip().upper()
        sala_destino_id = request.form.get('sala_destino_id', type=int)

        equipamento = Equipamento.query.filter_by(numero_serie=numero_serie).first()
        sala_destino = Sala.query.get(sala_destino_id)

        if not equipamento or not sala_destino or equipamento.status_atual == 'Em Trânsito':
            flash('Erro na validação do Checkout.', 'danger')
            return redirect(url_for('main.checkout'))

        status_anterior = equipamento.status_atual
        status_novo = 'Em Trânsito'
        predio_destino_id = sala_destino.predio.id

        try:
            novo_checkpoint = HistoricoCheckpoint(
                equipamento_id=equipamento.id, status_anterior=status_anterior, status_novo=status_novo,
                predio_destino_id=predio_destino_id, sala_destino_id=sala_destino_id,
                responsavel_alteracao_id=current_user.id
            )
            db.session.add(novo_checkpoint)
            equipamento.status_atual = status_novo
            db.session.commit()
            flash(f'Checkout do Equipamento {numero_serie} registrado.', 'success')

            return redirect(url_for('main.detalhes_equipamento', equipamento_id=equipamento.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar checkout: {e}', 'danger')
            return redirect(url_for('main.checkout'))

    return render_template('checkout.html', predios=predios)


@main.route('/checkin', methods=['GET', 'POST'])
@login_required
def checkin():
    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie').strip().upper()
        equipamento = Equipamento.query.filter_by(numero_serie=numero_serie).first()

        if not equipamento or equipamento.status_atual != 'Em Trânsito':
            flash('Erro na validação do Check-in.', 'danger')
            return redirect(url_for('main.checkin'))

        ultimo_checkpoint = HistoricoCheckpoint.query.filter_by(equipamento_id=equipamento.id
                                                                ).order_by(
            HistoricoCheckpoint.data_alteracao.desc()).first()

        sala_destino = Sala.query.get(ultimo_checkpoint.sala_destino_id)

        if not sala_destino:
            flash('Erro: Destino planejado não encontrado.', 'danger')
            return redirect(url_for('main.checkin'))

        try:
            status_anterior = equipamento.status_atual
            status_novo = f'Em Uso ({sala_destino.nome})'

            equipamento.localizacao_atual_id = sala_destino.id
            equipamento.status_atual = status_novo

            novo_checkpoint = HistoricoCheckpoint(
                equipamento_id=equipamento.id, status_anterior=status_anterior, status_novo=status_novo,
                predio_destino_id=sala_destino.predio.id, sala_destino_id=sala_destino.id,
                responsavel_alteracao_id=current_user.id
            )
            db.session.add(novo_checkpoint)
            db.session.commit()
            flash(f'Check-in do Equipamento {numero_serie} confirmado.', 'success')

            return redirect(url_for('main.detalhes_equipamento', equipamento_id=equipamento.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar check-in: {e}', 'danger')
            return redirect(url_for('main.checkin'))

    return render_template('checkin.html')


@main.route('/retorno_estoque', methods=['GET', 'POST'])
@login_required
def retorno_estoque():
    estoque_sala = Sala.query.get(Config.ESTOQUE_PADRAO_ID)
    if request.method == 'POST':
        numero_serie = request.form.get('numero_serie').strip().upper()
        equipamento = Equipamento.query.filter_by(numero_serie=numero_serie).first()

        if not equipamento or equipamento.status_atual == 'Em Estoque':
            flash('Erro na validação do Retorno ao Estoque.', 'danger')
            return redirect(url_for('main.retorno_estoque'))

        try:
            status_anterior = equipamento.status_atual
            status_novo = 'Em Estoque'
            equipamento.localizacao_atual_id = estoque_sala.id
            equipamento.status_atual = status_novo

            novo_checkpoint = HistoricoCheckpoint(
                equipamento_id=equipamento.id, status_anterior=status_anterior, status_novo=status_novo,
                predio_destino_id=estoque_sala.predio.id, sala_destino_id=estoque_sala.id,
                responsavel_alteracao_id=current_user.id
            )
            db.session.add(novo_checkpoint)

            admins = User.query.filter_by(is_admin=True).all()
            mensagem_notificacao = f'Equipamento {equipamento.numero_serie} ({equipamento.nome_equipamento}) retornou ao estoque.'
            for admin in admins:
                notificacao = Notificacao(mensagem=mensagem_notificacao, equipamento_id=equipamento.id,
                                          usuario_alvo_id=admin.id)
                db.session.add(notificacao)

            db.session.commit()
            flash(f'Equipamento {numero_serie} retornado ao estoque.', 'success')

            return redirect(url_for('main.detalhes_equipamento', equipamento_id=equipamento.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar retorno: {e}', 'danger')
            return redirect(url_for('main.retorno_estoque'))

    return render_template('retorno_estoque.html')


# --- Rotas de Consulta e Auditoria ---

@main.route('/detalhes_equipamento/<int:equipamento_id>')
@login_required
def detalhes_equipamento(equipamento_id):
    equipamento = Equipamento.query.get_or_404(equipamento_id)
    historico = HistoricoCheckpoint.query.filter_by(equipamento_id=equipamento.id
                                                    ).order_by(HistoricoCheckpoint.data_alteracao.desc()).all()
    local_atual = Sala.query.get(equipamento.localizacao_atual_id)

    qr_code_url = None
    responsavel = User.query.get(equipamento.responsavel_cadastro_id)

    return render_template(
        'detalhes_equipamento.html', equipamento=equipamento, local_atual=local_atual,
        responsavel_cadastro=responsavel, historico=historico, qr_code_url=qr_code_url
    )


@main.route('/imprimir_etiqueta/<int:equipamento_id>')
@login_required
def imprimir_etiqueta(equipamento_id):
    """Gera uma página mínima pronta para impressão de etiqueta com dados."""

    equipamento = Equipamento.query.get_or_404(equipamento_id)
    local_atual = Sala.query.get(equipamento.localizacao_atual_id)

    qr_code_url = None  # Não usamos mais a imagem QR, mas mantemos o campo

    return render_template(
        'etiqueta_imprimivel.html',
        equipamento=equipamento,
        local_atual=local_atual,
        qr_code_url=qr_code_url
    )


@main.route('/historico_geral')
@admin_required
def historico_geral():
    checkpoints = HistoricoCheckpoint.query.order_by(
        HistoricoCheckpoint.data_alteracao.desc()
    ).all()
    equipamentos = Equipamento.query.order_by(Equipamento.numero_serie).all()
    return render_template('historico_geral.html', checkpoints=checkpoints, equipamentos=equipamentos)


@main.route('/notificacoes')
@login_required
def notificacoes():
    notificacoes = Notificacao.query.filter_by(usuario_alvo_id=current_user.id
                                               ).order_by(Notificacao.data_criacao.desc()).all()
    nao_lidas_count = Notificacao.query.filter_by(usuario_alvo_id=current_user.id, lida=False).count()
    return render_template('notificacoes.html', notificacoes=notificacoes, nao_lidas_count=nao_lidas_count)


@main.route('/marcar_notificacao_lida/<int:notificacao_id>', methods=['POST'])
@login_required
def marcar_notificacao_lida(notificacao_id):
    notificacao = Notificacao.query.get_or_404(notificacao_id)
    if notificacao.usuario_alvo_id != current_user.id:
        flash('Ação não permitida.', 'danger')
    elif not notificacao.lida:
        notificacao.lida = True
        db.session.commit()
        flash('Notificação marcada como lida.', 'success')
    return redirect(url_for('main.notificacoes'))


@main.route('/marcar_todas_lidas', methods=['POST'])
@login_required
def marcar_todas_lidas():
    try:
        Notificacao.query.filter_by(usuario_alvo_id=current_user.id, lida=False
                                    ).update({'lida': True}, synchronize_session=False)
        db.session.commit()
        flash('Todas as notificações foram marcadas como lidas.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao marcar notificações: {e}', 'danger')
    return redirect(url_for('main.notificacoes'))