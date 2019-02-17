from flask import Flask
from .api import api
from .app import app as core_app


app = Flask(__name__,
            static_folder='../dist/static',
            template_folder='../dist'
            )

# register Blueprints
app.register_blueprint(core_app)
app.register_blueprint(api, url_prefix='/api')
