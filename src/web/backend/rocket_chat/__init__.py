from . import api


def register_blueprint(app):
    app.register_blueprint(api.blueprint)


def initialize_module(app):
    from . import utils
    utils.populate_service(app.config["SQLALCHEMY_DATABASE_URI"])
