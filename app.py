from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/teste')\ndef teste():\n    return '<h1>Aplicação online</h1>'
