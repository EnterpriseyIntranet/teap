from flask import Blueprint, render_template, current_app

app = Blueprint('app', 'app')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if current_app.debug:
        import requests
        return requests.get('http://localhost:8081/{}'.format(path)).text
    return render_template('index.html')
