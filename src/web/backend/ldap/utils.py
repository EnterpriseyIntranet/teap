import logging

from flask import g, current_app
import edap
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
    edap = get_edap()
    try:
        edap.get_team('everybody')
    except edap.ObjectDoesNotExist:
        logger.warning('Edap Everybody team is missing')
