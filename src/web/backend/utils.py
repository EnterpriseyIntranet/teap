"""Helper utilities and decorators."""
import json
from functools import wraps

import flask
from flask_login import current_user

from .extensions import service_provider


def check_route_access():
    if any([
        flask.request.endpoint.startswith('static/'),
        current_user.is_authenticated,
        not flask.current_app.config["AUTHORIZATION"],
            ]):
        return  # Access granted
    else:
        return flask.redirect(flask.url_for(
            "{bp}.login".format(bp=service_provider.blueprint_name),
            next=flask.url_for(flask.request.endpoint)))


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flask.flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


class EncoderWithBytes(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return json.JSONEncoder.default(self, obj)


def api_auth_required(func):
    """ Authentication check decorator for api """
    @wraps(func)
    def _verify(*args, **kwargs):
        # TODO: add authentication check when authentication backend will be provided
        # for now always process request
        return func(*args, **kwargs)
    return _verify
