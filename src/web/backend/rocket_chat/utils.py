from flask import g

from rocketchat_API.rocketchat import RocketChat

from backend.settings import ROCKETCHAT_HOST, ROCKETCHAT_PASSWORD, ROCKETCHAT_USER


def get_rocket():
    """ Create if doesn't exist or return edap from flask g object """
    if 'rocket' not in g:
        try:
            g.rocket = RocketChat(ROCKETCHAT_USER, ROCKETCHAT_PASSWORD, server_url=ROCKETCHAT_HOST)
            g.rocket_exception = None
        except Exception as e:
            g.rocket = None
            g.rocket_exception = e
    return g.rocket
