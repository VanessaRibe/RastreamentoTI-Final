from flask import Blueprint, request, redirect, url_for
from flask_login import login_user
from models import User

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        return "<h1>Credenciais inválidas</h1>"

    return """
        <h1>Login funcionando!</h1>
        <form method="POST">
            Usuário: <input type="text" name="username"><br>
            Senha: <input type="password" name="password"><br>
            <button type="submit">Entrar</button>
        </form>
    """
@main.route("/cadastrar_usuario")
@login_required
def cadastrar_usuario():
    return render_template("cadastrar_usuario.html")
