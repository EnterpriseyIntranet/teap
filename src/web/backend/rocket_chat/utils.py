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


class RocketMixin:

    @property
    def rocket(self):
        return get_rocket()


def get_channel_by_name(channel_name):
    """ Get rocket channel json object by it's name """
    rocket = get_rocket()
    res = rocket.channels_list(query='{{"name": {{"$eq": "{channel_name}"}}}}'.format(channel_name=channel_name))
    if res.status_code != 200:
        return None
    channels = res.json()['channels']
    if not channels:
        return None
    return channels[0]


def get_user_by_username(username):
    """ Get rocket user json object by it's username """
    rocket = get_rocket()
    res = rocket.users_list(query='{{"username":{{"$eq": "{username}"}}}}'.format(username=username))
    if res.status_code != 200:
        return None
    users = res.json()['users']
    if not users:
        return None
    return users[0]
