from flask_saml2 import sp
from flask_saml2.sp import idphandler


# Note: We have to force Keycloak not to encrypt assertions

# We have supply relay_state to get it back as flask-saml requires it to be present in the answer:
# https://github.com/timheap/flask-saml2/blob/master/flask_saml2/sp/views.py#L82
class KeycloakIdPHandler(idphandler.IdPHandler):
    def make_login_request_url(
        self,
        relay_state=None
    ):
        if relay_state is None:
            relay_state = "placeholder"
        url = super().make_login_request_url(relay_state)
        print(f"{url=}")
        return url


class ExampleServiceProvider(sp.ServiceProvider):
    def get_logout_return_url(self):
        return self.get_login_url()

    def get_default_login_return_url(self):
        return self.get_login_url()


def get_blueprint():
    sp = ExampleServiceProvider()

    blueprint = sp.create_blueprint()

    return blueprint
