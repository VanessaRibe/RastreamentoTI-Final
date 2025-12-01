from flask import Blueprint, render_template, request, redirect, url_for

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Aqui você pode validar o usuário
        return redirect(url_for("main.teste"))
    return render_template("login.html")
