import configparser


def get_config_divisions():
    """ Get divisions from config file `ldap.ini` """
    config = configparser.ConfigParser()
    config.read('ldap.ini')
    return dict(config['DIVISIONS'].items())
