# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import Blueprint, render_template, current_app
from flask_login import login_required

blueprint = Blueprint('core', __name__)


@blueprint.route('/', defaults={'path': ''})
@blueprint.route('/<path:path>')
# @login_required
def index(path):
    if current_app.debug:
        import requests
        return requests.get('http://localhost:8081/{}'.format(path)).text
    return render_template('index.html')
