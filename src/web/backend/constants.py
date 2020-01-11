import pathlib


SAML_CHOICES = {
    "sp-cert": "sp.crt",
    "sp-key": "sp.key",
    "idp-cert": "idp.crt",
}

SAML_CERT_ROOT = pathlib.Path("/tmp")
