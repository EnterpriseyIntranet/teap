"""Extensions module. Each extension is initialized in the app factory located in app.py."""
import flask_login
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_saml2 import sp
from flask_mail import Mail


csrf_protect = CSRFProtect()
login_manager = flask_login.LoginManager()
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()


class User(flask_login.UserMixin):
    def __init__(self, uid):
        self.id = uid


@login_manager.user_loader
def load_user(uid):
    return User(uid)


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
        uid = auth_data.nameid
        if self.login_callback:
            uid = self.login_callback(uid)
        flask_login.login_user(User(uid))
        return super().login_successful(auth_data, relay_state)

    def logout(self):
        flask_login.logout()
        super().logout()


service_provider = ServiceProvider()
