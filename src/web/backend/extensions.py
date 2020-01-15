"""Extensions module. Each extension is initialized in the app factory located in app.py."""
import flask_login
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_saml2 import sp


csrf_protect = CSRFProtect()
login_manager = flask_login.LoginManager()
db = SQLAlchemy()
migrate = Migrate()


class ServiceProvider(sp.ServiceProvider):
    def __init__(self):
        super().__init__()
        self.login_callback = None

    def supply_login_callback(self, callback):
        self.login_callback = callback

    def get_logout_return_url(self):
        return self.get_login_url()

    def get_default_login_return_url(self):
        return "/"

    def login_successful(self, auth_data, relay_state):
        u = self.login_callback(auth_data.nameid)
        flask_login.login_user(u)
        print(flask_login.current_user)
        return super().login_successful(auth_data, relay_state)

    def logout(self):
        flask_login.logout()
        super().logout()


service_provider = ServiceProvider()
