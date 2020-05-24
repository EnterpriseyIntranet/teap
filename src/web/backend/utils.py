"""Helper utilities and decorators."""
import json
from functools import wraps

import flask
import flask_login

from .extensions import service_provider, User


NOAUTH_ENDPOINTS = (
    "login",
    "logout",
    "index",
)


def general_logout():
    flask_login.logout_user()
    return flask.redirect("index")


def redirect_to_next(next_page):
    if not next_page or not next_page.startswith("/"):
        next_page = "/"
    print(f"{next_page=}")
    return flask.redirect(next_page)


def _login_by_ldap(username, password, next_page=None):
    from .ldap.utils import get_edap

    try:
        edap = get_edap()
        login_successful = edap.verify_user_password(username, password)
    except Exception:
        login_successful = False

    print(f"{login_successful=}")
    if login_successful:
        flask_login.login_user(User(username))
    else:
        next_page = None
    return redirect_to_next(next_page)


def check_route_access():
    if any([
        flask.request.endpoint.startswith('static/'),
        flask.request.endpoint in NOAUTH_ENDPOINTS,
        flask_login.current_user.is_authenticated,
        not flask.current_app.config["AUTHORIZATION"],
            ]):
        return  # Access granted
    else:
        print("path: ", flask.request.path)
        return flask.redirect(flask.url_for(
            "login", next=flask.request.path))


def auth_err_if_user_other_than(uid):
    if flask.current_app.config["AUTHORIZATION"]:
        print(f"Current user: {flask_login.current_user.id=}")
        if not flask_login.current_user.is_authenticated:
            print("Not authd at all")
            return flask.jsonify(messge="You are not even authenticated"), 401
        if flask_login.current_user.id != uid:
            print(f"Only user '{uid}' can view this page, you are '{flask_login.current_user.id}'")
            return flask.jsonify(message=f"Only user '{uid}' is allowed to see this page."), 401
        print("Passed auth")
    else:
        print("Auth not required")


def auth_err_if_user_not_from_groups(groups):
    if flask.current_app.config["AUTHORIZATION"]:
        print(f"Current user: {flask_login.current_user.id=}")
        if not flask_login.current_user.is_authenticated:
            print("Not authd at all")
            return flask.jsonify(messge="You are not even authenticated"), 401
        from .ldap.utils import get_edap
        edap = get_edap()
        uid = flask_login.current_user.id
        memberships = [edap.uid_is_member_of_special_group(uid, g) for g in groups]
        if not any(memberships):
            print(f"Auth as '{flask_login.current_user.id}' not good enough")
            return flask.jsonify(message=f"Only users from groups {groups} are allowed"), 401
        print("Passed auth")
    else:
        print("Auth not required")


def auth_err_if_user_not_hr_admin():
    return auth_err_if_user_not_from_groups(["hr-admins"])


def authorize_only_hr_admins():
    return authorize_only_special_groups(["hr-admins"])


def authorize_only_special_groups(groups):
    def decorator(wrapped):
        @wraps(wrapped)
        def wrapper(* args, ** kwargs):
            print(f"Authorizing, {args=}, {kwargs=}")

            auth_err = auth_err_if_user_not_from_groups(groups)
            if auth_err:
                return auth_err

            return wrapped(* args, ** kwargs)
        return wrapper
    return decorator


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
