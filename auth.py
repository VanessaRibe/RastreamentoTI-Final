from flask import Blueprint, render_template, request, redirect, url_for

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        return redirect(url_for("index"))
    return """
        <h1>Login funcionando!</h1>
        <form method="POST">
            Usuário: <input type="text" name="username"><br>
            Senha: <input type="password" name="password"><br>
            <button type="submit">Entrar</button>
        </form>
    """
