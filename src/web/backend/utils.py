"""Helper utilities and decorators."""
import json
from functools import wraps

from flask import flash


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


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
