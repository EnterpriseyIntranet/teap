import logging

from flask import g, current_app
from .. import edap
import configparser

logger = logging.getLogger()


def get_edap():
    """ Create if doesn't exist or return edap from flask g object """
    if 'edap' not in g:
        g.edap = edap.Edap(current_app.config['EDAP_HOSTNAME'],
                      current_app.config['EDAP_USER'],
                      current_app.config['EDAP_PASSWORD'],
                      current_app.config['EDAP_DOMAIN'])
    return g.edap


class EdapMixin:

    @property
    def edap(self):
        return get_edap()


def get_config_divisions():
    """ Get divisions from config file `ldap.ini` where key is division machine_name, value is display name """
    config = configparser.ConfigParser()
    config.read('ldap.ini')
    return dict(config['DIVISIONS'].items())


def merge_divisions(config_divisions, ldap_divisions):
    """
    Merge divisions from ldap and config, adding flags where the division belongs to
    Args:
        config_divisions (dict): dict with division machine name as key, display name as value
        ldap_divisions (list): response from edap.get_divisions()

    Returns (dict):
    """
    divisions = {}

    for machine_name, display_name in config_divisions.items():
        divisions[machine_name] = {
            'config_display_name': display_name,
            'exists_in_config': True,
            'exists_in_ldap': False
        }

    for ldap_division in ldap_divisions:
        div_machine_name = ldap_division['cn'][0].decode('utf-8')
        div_display_name = ldap_division['description'][0].decode('utf-8') if ldap_division.get('description') else None

        if div_machine_name in divisions:
            divisions[div_machine_name].update(
                {'exists_in_ldap': True,
                 'ldap_display_name': div_display_name}
            )
        else:
            divisions[div_machine_name] = {
                'ldap_display_name': div_display_name,
                'exists_in_ldap': True,
                'exists_in_config': False
            }

    return divisions


def check_consistency():
    """ Check if all required system objects exist in Edap """
    e = get_edap()
    try:
        e.get_team('everybody')
    except edap.ObjectDoesNotExist:
        logger.warning('Edap Everybody team is missing')
    try:
        e.get_team('international')
    except edap.ObjectDoesNotExist:
        logger.warning('Edap International team is missing')


from .. import extensions
import flask_mail
import flask
import jwt
import time


def send_password_reset_email(to, data):
    msg = flask_mail.Message("password recovery", sender="intranet@cspii.org", recipients=[to])
    expiry_s = flask.current_app.config["PW_RESET_EXPIRY_SEC"]
    token = get_reset_password_token(data, expiry_s)
    msg.body = flask.render_template(
        "templates/mail_pw_reset.txt", data=data, token=token,
        valid_for_minutes=expiry_s // 60)
    extensions.mail.send(msg)


def get_reset_password_token(data, expires_in):
    more_data = {
        'exp': time.time() + expires_in,
    }
    more_data.update(data)
    return jwt.encode(
        more_data,
        current_app.config['SECRET_KEY'], algorithm='HS256')


class PWResetEligibilityExc(RuntimeError):
    pass


def verify_reset_password_token(token, uid):
    try:
        data = jwt.decode(
            token, current_app.config['SECRET_KEY'],
            algorithms=['HS256'])
    except Exception as exc:
        print(str(exc))
        msg = "The request was not valid, perhaps it has already expired?"
        raise PWResetEligibilityExc(msg)
    implied_uid = str(data["username"]).strip()
    if implied_uid.endswith("@cspii.org"):
        implied_uid = implied_uid.split("@")
        implied_uid = "@".join(implied_uid[:-1])
    if str(implied_uid) != str(uid):
        msg = "Please supply the correct username that is paired with the request"
        raise PWResetEligibilityExc(msg)
    return True
