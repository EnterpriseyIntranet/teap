"""The app module, containing the app factory function."""
import flask

import wtforms
import wtforms.validators as vali
import flask_wtf
import flask_login

from . import commands, core, nextcloud, rocket_chat, ldap, actions, saml
from . import extensions, utils

from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(config_object='backend.settings'):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = flask.Flask(__name__.split('.')[0], static_folder='../dist/static', template_folder='../dist')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(config_object)
    app.url_map.strict_slashes = False
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    initialize_modules(app)
    register_auth(app)
    return app


def initialize_modules(app):
    rocket_chat.initialize_module(app)
    return None


def register_extensions(app):
    """Register Flask extensions."""
    if app.config["TEAP_USE_DB"]:
        extensions.db.init_app(app)
        extensions.migrate.init_app(app, extensions.db)
    extensions.login_manager.init_app(app)
    extensions.mail.init_app(app)
    return None


LOGINS = dict(
        # saml=dict(login_endpoint="saml.login", logout_endpoint="saml.logout"),
        saml=dict(login_endpoint="flask_saml2_sp.login", logout_endpoint="flask_saml2_sp.logout"),
        ldap=dict(login_endpoint="login_by_ldap", logout_endpoint="general_logout"),
)


def get_auth_method(app):
    if ("SAML2_SP" in app.config
            and "certificate" in app.config["SAML2_SP"]
            and "private_key" in app.config["SAML2_SP"]):
        return "saml"
    return "ldap"


def register_auth(app):
    @app.route("/login")
    def login():
        method = get_auth_method(app)
        return flask.redirect(flask.url_for(LOGINS[method]["login_endpoint"], next=flask.request.args.get("next")))

    @app.route("/ldap_creds", methods=["POST"])
    def authenticate_by_ldap():
        data = flask.request.form
        uid = data.get("username")
        password = data.get("password")
        next_page = data.get("next_page")
        return utils._login_by_ldap(uid, password, next_page)

    @app.route("/logout")
    def logout():
        method = get_auth_method(app)
        return flask.redirect(LOGINS[method]["logout_endpoint"])

    @app.route("/general_logout")
    def general_logout():
        return utils.general_logout()

    @app.route("/ldap_login")
    def login_by_ldap():
        form = LoginForm()
        form.next_page.data = flask.request.args.get("next")
        return flask.render_template(
                "templates/login.html",
                target_url=flask.url_for("authenticate_by_ldap"), login_form=form)

    @app.route("/reset_pw", methods=["POST"])
    def reset_password():
        from .ldap.api import handle_reset
        form = ResetPasswordForm()
        try:
            if not form.validate_on_submit():
                raise ValueError("The request is invalid.")
            username = form.username.data
            token = form.token.data
            new_password = form.new_password.data

            handle_reset(username, token, new_password)
            flask.flash("Password set successfuly, you may log in now.")
            url = flask.url_for("divisions_api.details_change")
        except ValueError as exc:
            flask.flash(f"Error setting password: {str(exc)}")
            url = flask.url_for('reset_password_form', token=token)
        return flask.redirect(url)

    @app.route("/reset_pw/<token>", methods=["GET"])
    def reset_password_form(token):
        # Render a form to reset password
        form = ResetPasswordForm()
        form.token.data = token
        return flask.render_template(
                "templates/reset_pw.html",
                details_form=form,
                token=token)


class LoginForm(flask_wtf.FlaskForm):
    next_page = wtforms.HiddenField("next")
    username = wtforms.StringField(
            "Your username", validators=[vali.DataRequired()])
    password = wtforms.PasswordField(
            "Your password", validators=[vali.DataRequired()])


class ResetPasswordForm(flask_wtf.FlaskForm):
    token = wtforms.HiddenField(
            "reset token")
    username = wtforms.StringField(
            "Your Username",
            [wtforms.validators.DataRequired("The user ID is missing")])
    new_password = wtforms.PasswordField(
            "Your new password",
            [wtforms.validators.EqualTo('new_password_confirm', message='Passwords must match')])
    new_password_confirm = wtforms.PasswordField(
            "Your new password (confirm)")




def redirect_to_login():
    login_url = "/login"
    return flask.redirect(login_url)


def register_blueprints(app):
    """Register Flask blueprints."""
    bps = [
        nextcloud.api.blueprint,
        core.views.blueprint,
        rocket_chat.api.blueprint,
        ldap.api.blueprint,
        actions.api.blueprint,
    ]
    for bp in bps:
        bp.before_request(utils.check_route_access)
        app.register_blueprint(bp)

    saml_bp = saml.get_blueprint()
    app.register_blueprint(saml_bp, url_prefix="/saml/")
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return flask.render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': extensions.db,
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
    app.cli.add_command(commands.check_services_consistency)
    app.cli.add_command(commands.bootstrap)
    app.cli.add_command(commands.saml)
    app.cli.add_command(commands.maintain)
