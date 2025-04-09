from flask import Flask, render_template, redirect, request
from threading import Thread
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('', template_folder='web')

@app.route('/')
def index():
    return render_template('home.html')

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    server = Thread(target=run, daemon=True)
    server.start()
    return server