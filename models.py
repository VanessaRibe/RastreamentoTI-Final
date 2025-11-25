# models.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


# --- Modelos de Localização ---

class Predio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    salas = db.relationship('Sala', backref='predio', lazy='dynamic')

    def __repr__(self):
        return f'<Predio {self.nome}>'


class Sala(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    predio_id = db.Column(db.Integer, db.ForeignKey('predio.id'), nullable=False)
    equipamentos = db.relationship('Equipamento', backref='localizacao_atual', lazy='dynamic')

    def __repr__(self):
        return f'<Sala {self.nome} ({self.predio.nome})>'


# --- Modelo de Usuário (ATUALIZADO) ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # NOVOS CAMPOS PARA RASTREABILIDADE
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    matricula = db.Column(db.String(20), unique=True, nullable=True)

    is_admin = db.Column(db.Boolean, default=False)

    equipamentos_cadastrados = db.relationship('Equipamento', backref='responsavel_cadastro', lazy='dynamic')
    notificacoes_alvo = db.relationship('Notificacao', backref='usuario_alvo', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# --- Modelo Principal: Equipamento ---

class Equipamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_serie = db.Column(db.String(128), unique=True, nullable=False)
    nome_equipamento = db.Column(db.String(100), nullable=False)
    qr_code_path = db.Column(db.String(256))
    status_atual = db.Column(db.String(50), default='Em Estoque', nullable=False)
    localizacao_atual_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=True)
    responsavel_cadastro_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    historico = db.relationship('HistoricoCheckpoint', backref='equipamento', lazy='dynamic')
    notificacoes = db.relationship('Notificacao', backref='equipamento', lazy='dynamic')


# --- Modelo de Rastreamento: Histórico e Notificação ---

class HistoricoCheckpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id'), nullable=False)
    status_anterior = db.Column(db.String(50), nullable=False)
    status_novo = db.Column(db.String(50), nullable=False)
    predio_destino_id = db.Column(db.Integer, db.ForeignKey('predio.id'), nullable=True)
    sala_destino_id = db.Column(db.Integer, db.ForeignKey('sala.id'), nullable=True)

    predio_destino = db.relationship('Predio', foreign_keys=[predio_destino_id], backref='checkpoints_destino')
    sala_destino = db.relationship('Sala', foreign_keys=[sala_destino_id], backref='checkpoints_destino')

    data_alteracao = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    responsavel_alteracao_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    responsavel_alteracao = db.relationship('User', backref='checkpoints_feitos',
                                            foreign_keys=[responsavel_alteracao_id])


class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensagem = db.Column(db.String(256), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id'), nullable=True)
    usuario_alvo_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)