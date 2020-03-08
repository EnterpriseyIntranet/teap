from flask_saml2.sp import idphandler

from .extensions import service_provider


# Note: We have to force Keycloak not to encrypt assertions

# We have supply relay_state to get it back as flask-saml requires it to be present in the answer:
# https://github.com/timheap/flask-saml2/blob/master/flask_saml2/sp/views.py#L82
class KeycloakIdPHandler(idphandler.IdPHandler):
    pass


def get_blueprint():
    blueprint = service_provider.create_blueprint()

    return blueprint
