"""The app module, containing the app factory function."""
from flask import Flask, render_template

from . import commands, public, user, core, nextcloud, rocket_chat, ldap, actions
from .extensions import db, login_manager, migrate


def create_app(config_object='backend.settings'):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0], static_folder='../dist/static', template_folder='../dist')
    app.config.from_object(config_object)
    app.url_map.strict_slashes = False
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    initialize_modules(app)
    return app


def initialize_modules(app):
    rocket_chat.initialize_module(app)
    return None


def register_extensions(app):
    """Register Flask extensions."""
    if app.config["SQLALCHEMY_DATABASE_URI"]:
        db.init_app(app)
        migrate.init_app(app, db)
    login_manager.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(nextcloud.api.blueprint)
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(core.views.blueprint)
    app.register_blueprint(rocket_chat.api.blueprint)
    app.register_blueprint(ldap.api.blueprint)
    app.register_blueprint(actions.api.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

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
