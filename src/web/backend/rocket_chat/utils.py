import logging
from functools import wraps
from collections import namedtuple
import re

from flask import g, current_app

from rocketchat_API.rocketchat import RocketChat
from ..actions.models import Action

logger = logging.getLogger()

rocket_ids = namedtuple("rocket_ids", ("user", "channel", "group"))


def get_rocket():
    """ Create if doesn't exist or return edap from flask g object """
    if 'rocket' not in g:
        try:
            g.rocket = RocketChat(
                    current_app.config["ROCKETCHAT_USER"],
                    current_app.config["ROCKETCHAT_PASSWORD"],
                    server_url=current_app.config["ROCKETCHAT_HOST"])
            g.rocket_exception = None
        except Exception as e:
            g.rocket = None
            g.rocket_exception = e
    return g.rocket


def sanitize_room_name(name):
    name = re.sub(" ", "-", name)
    name = re.sub("&", "and", name)
    return name


class RocketMixin:

    @property
    def rocket(self):
        return get_rocket()


def log_rocket_action(event_name):
    def wrapper(func):
        @wraps(func)
        def inner_wrapper(self, **kwargs):
            res = None
            status = False
            message = None
            try:
                res = func(self, **kwargs)
                if res.status_code == 200:
                    status = True
                else:
                    message = res.json()['error']
            except Exception as e:
                logger.exception(e)
                status = False
                message = str(e)
            # TODO: what to do with password in create_user method?
            filtered_kwargs = {key: value for key, value in kwargs.items() if key != 'password'}
            Action.create_event(event_name=event_name, status=status, message=message, **filtered_kwargs)
            return res
        return inner_wrapper
    return wrapper


class RocketChatService(RocketMixin):

    def create_user(self, username, password, email, name):
        """
        Create user

        Args:
            username (str):
            password (str):
            email (str):
            name (str):

        Returns (response):

        """
        return self.rocket.users_create(email, name, password, username, requirePasswordChange=True)

    def create_channel(self, room_name):
        """
        Create channel
        Args:
            channel_name (str):

        Returns:

        """
        return self.rocket.channels_create(room_name)

    def create_group(self, room_name):
        """
        Create channel
        Args:
            channel_name (str):

        Returns:

        """
        return self.rocket.groups_create(room_name)

    def invite_user_to_channel(self, rocket_channel, rocket_user):
        return self.rocket.channels_invite(rocket_channel, rocket_user)

    def invite_user_to_group(self, rocket_group, rocket_user):
        return self.rocket.groups_invite(rocket_group, rocket_user)

    def get_ids(self, username, channel_name=None, group_name=None):
        rocket_user = rocket_service.get_user_by_username(username)
        if not rocket_user:
            raise ValueError(f"Rocket.chat user '{username}' not found")

        rocket_channel = None
        if channel_name:
            rocket_channel = rocket_service.get_channel_by_name(channel_name)
            if not rocket_channel:
                raise ValueError(f"Rocket.chat channel '{channel_name}' not found")
            rocket_channel = rocket_channel["_id"]

        rocket_group = None
        if group_name:
            rocket_group = rocket_service.get_group_by_name(group_name)
            if not rocket_group:
                raise ValueError(f"Rocket.chat group '{group_name}' not found")
            rocket_group = rocket_group["_id"]

        return rocket_ids(
                user=rocket_user["_id"],
                channel=rocket_channel,
                group=rocket_group,
        )

    def delete_user(self, user_id):
        return self.rocket.users_delete(user_id)

    def get_channel_by_name(self, channel_name):
        """ Get rocket channel json object by it's name """
        query = f'{{"fname": {{"$eq": "{channel_name}"}}}}'
        res = self.rocket.channels_list(query=query)
        if res.status_code != 200:
            return None
        rooms = res.json()['channels']
        if not rooms:
            return None
        return rooms[0]

    def get_group_by_name(self, group_name):
        """ Get rocket group json object by it's name """
        res = self.rocket.groups_list_all()
        if res.status_code != 200:
            return None
        all_rooms = res.json()['groups']
        good_rooms = [r for r in all_rooms if r["name"] == group_name]
        if not good_rooms:
            return None
        return good_rooms[0]

    def get_user_by_username(self, username):
        """ Get rocket user json object by it's username """
        query = f'{{"username":{{"$eq": "{username}"}}}}'
        res = self.rocket.users_list(query=query)
        if res.status_code != 200:
            return None
        users = res.json()['users']
        if not users:
            return None
        return users[0]


class LoggingRocketChatService(RocketChatService):
    @log_rocket_action(event_name=Action.CREATE_ROCKET_USER)
    def create_user(self, username, password, email, name):
        return super().create_user(username, password, email, name)

    @log_rocket_action(event_name=Action.CREATE_ROCKET_CHANNEL)
    def create_channel(self, channel_name):
        return super().create_channel(channel_name)

    @log_rocket_action(event_name=Action.INVITE_USER_TO_CHANNEL)
    def invite_user_to_channel(self, rocket_channel, rocket_user):
        return super().invite_user_to_channel(rocket_channel, rocket_user)

    @log_rocket_action(event_name=Action.CREATE_ROCKET_GROUP)
    def create_group(self, group_name):
        return super().create_group(group_name)

    @log_rocket_action(event_name=Action.INVITE_USER_TO_GROUP)
    def invite_user_to_group(self, rocket_group, rocket_user):
        return super().invite_user_to_group(rocket_group, rocket_user)


def populate_service(logging_enabled):
    global rocket_service
    if logging_enabled:
        rocket_service = LoggingRocketChatService()
    else:
        rocket_service = RocketChatService()


rocket_service = None
