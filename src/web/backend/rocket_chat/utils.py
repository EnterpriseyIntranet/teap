from flask import g, current_app

from rocketchat_API.rocketchat import RocketChat


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


class RocketMixin:

    @property
    def rocket(self):
        return get_rocket()


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

    def create_channel(self, channel_name):
        """
        Create channel
        Args:
            channel_name (str):

        Returns:

        """
        return self.rocket.channels_create(channel_name)

    def delete_user(self, user_id):
        return self.rocket.users_delete(user_id)

    def get_channel_by_name(self, channel_name):
        """ Get rocket channel json object by it's name """
        query = '{{"fname": {{"$eq": "{channel_name}"}}}}'.format(channel_name=channel_name)
        res = self.rocket.channels_list(query=query)
        if res.status_code != 200:
            return None
        channels = res.json()['channels']
        if not channels:
            return None
        return channels[0]

    def get_user_by_username(self, username):
        """ Get rocket user json object by it's username """
        res = self.rocket.users_list(query='{{"username":{{"$eq": "{username}"}}}}'.format(username=username))
        if res.status_code != 200:
            return None
        users = res.json()['users']
        if not users:
            return None
        return users[0]


rocket_service = RocketChatService()
