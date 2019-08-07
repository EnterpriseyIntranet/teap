"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'

DB_HOST = env.str('DB_HOST')
DB_USER = env.str('DB_USER')
DB_PASSWORD = env.str('DB_PASSWORD')
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}"
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
