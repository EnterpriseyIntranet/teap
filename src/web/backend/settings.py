"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
import sys

from environs import Env

from flask_saml2.utils import certificate_from_file, private_key_from_file
from . import constants as const


env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'

SQLALCHEMY_DATABASE_URI = env.str('DATABASE_URL', default="")
SECRET_KEY = env.str('SECRET_KEY')
BCRYPT_LOG_ROUNDS = env.int('BCRYPT_LOG_ROUNDS', default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False

# NEXTCLOUD
NEXTCLOUD_HOST = env.str('NEXTCLOUD_HOST')
NEXTCLOUD_USER = env.str('NEXTCLOUD_USER')
NEXTCLOUD_PASSWORD = env.str("NEXTCLOUD_PASSWORD")

# Rocket chat
ROCKETCHAT_USER = env.str("ROCKETCHAT_USER")
ROCKETCHAT_PASSWORD = env.str("ROCKETCHAT_PASSWORD")
ROCKETCHAT_HOST = env.str("ROCKETCHAT_HOST")

# Edap
EDAP_HOSTNAME = env.str("EDAP_HOSTNAME")
EDAP_USER = env.str("EDAP_USER")
EDAP_PASSWORD = env.str("EDAP_PASSWORD")
EDAP_DOMAIN = env.str("EDAP_DOMAIN")

SERVER_NAME = env.str("SERVER_NAME")
AUTHORIZATION = env.bool("AUTHORIZATION", False)

SAML2_IDENTITY_PROVIDERS = [
    {
        'CLASS': 'backend.saml.KeycloakIdPHandler',
        'OPTIONS': {
            'display_name': 'Keycloak IdP',
            'entity_id': f'https://sso.{EDAP_DOMAIN}/auth/realms/master',
            'sso_url':   f'https://sso.{EDAP_DOMAIN}/auth/realms/master/protocol/saml',
            'slo_url':   f'https://sso.{EDAP_DOMAIN}/auth/realms/master/protocol/saml',
        },
    },
]
try:
    SAML2_SP = {
        'certificate': certificate_from_file(const.SAML_CERT_ROOT / const.SAML_CHOICES["sp-cert"]),
        'private_key': private_key_from_file(const.SAML_CERT_ROOT / const.SAML_CHOICES["sp-key"]),
    }
    SAML2_IDENTITY_PROVIDERS[0]['OPTIONS']['certificate'] = certificate_from_file(
        const.SAML_CERT_ROOT / const.SAML_CHOICES["idp-cert"]
    )
except Exception as e:
    print(f"Error configuring SAML: {e}", file=sys.stderr)
    pass  # Files probably don't exist
