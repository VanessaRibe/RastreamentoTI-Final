from flask import Flask

app = Flask(__name__)

@app.route("/teste")
def teste():
    return "<h1>Aplicação online</h1>"

