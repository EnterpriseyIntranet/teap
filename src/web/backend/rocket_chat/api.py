from flask import Blueprint, jsonify, request, g
from flask.views import MethodView

from edap import ObjectDoesNotExist

from ..ldap.utils import EdapMixin

from . import utils as rutils

blueprint = Blueprint('rocket_chat_api', __name__, url_prefix='/api/rocket')


def check_rocket_authorized():
    rocket = rutils.get_rocket()
    if not rocket:
        rocket_exception = g.rocket_exception
        return jsonify({
            "message": "Rocket chat instance problem with authorization. {}".format(str(rocket_exception))
        }), 400


blueprint.before_request(check_rocket_authorized)


@blueprint.route('users', methods=["POST"])
def create_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    name = request.json.get('name')
    if not all([username, password, email, name]):
        return jsonify({"message": "username, password, email, name are required fields"}), 400

    res = rutils.rocket_service.create_chat_user(
            username, password, email, name,
            require_password_change=False, verified=True)
    data = res.json()

    if res.status_code == 200 and data.get('success', True):
        return jsonify({'user': data.get('user')}), 201
    else:
        return jsonify({'message': data.get('error', ' Something wrong happened')}), 400


@blueprint.route('channels', methods=["POST"])
def create_channel():
    channel_name = request.json.get('channel_name')
    channel_name = channel_name.replace(' ', '-')  # TODO: add proper name normalization
    res = rutils.rocket_service.create_chat_channel(channel_name)
    res_data = res.json()
    return jsonify(res_data), res.status_code


class UserRocketChannels(rutils.RocketMixin, MethodView):

    def post(self, user_id):
        channel = request.json.get('channel')
        try:
            ids = rutils.rocket_service.get_ids(user_id, channel_name=channel)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 404

        res = rutils.rocket_service.invite_user_to_channel(rocket_channel=ids.channel,
                                                           rocket_user=ids.user)
        return jsonify(res.json()), res.status_code

    def delete(self, user_id, channel):
        try:
            ids = rutils.rocket_service.get_ids(user_id, channel_name=channel)
        except valueerror as exc:
            return jsonify({'message': str(exc)}), 404

        res = self.rocket.channels_kick(ids.channel, ids.user)
        return jsonify(res.json()), res.status_code


class UserRocketGroups(rutils.RocketMixin, MethodView):

    def post(self, user_id):
        group = request.json.get('room')
        try:
            ids = rutils.rocket_service.get_ids(user_id, group_name=group)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 404

        res = rutils.rocket_service.invite_user_to_group(rocket_group=ids.group,
                                                         rocket_user=ids.user)
        return jsonify(res.json()), res.status_code

    def delete(self, user_id, group):
        try:
            ids = rutils.rocket_service.get_ids(user_id, group_name=group)
        except valueerror as exc:
            return jsonify({'message': str(exc)}), 404

        res = self.rocket.groups_kick(ids.group, ids.user)
        return jsonify(res.json()), res.status_code


class UserTeamsChatsViewSet(rutils.RocketMixin, EdapMixin, MethodView):

    def post(self, uid, team_machine_name):
        """ Add user to team chats """
        from ..ldap.serializers import edap_team_schema
        team = edap_team_schema.load(self.edap.get_team(team_machine_name))
        try:
            franchise, division = team.get_team_components()
        except ObjectDoesNotExist:
            return jsonify({'message': 'Team corresponding franchise or division are not found'}), 404

        try:
            ids_franchise = rutils.rocket_service.get_ids(uid, group_name=franchise.chat_name)
            ids_division = rutils.rocket_service.get_ids(uid, group_name=division.chat_name)
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 404

        res = rutils.rocket_service.invite_user_to_group(rocket_group=ids_franchise.group,
                                                         rocket_user=ids_franchise.user)
        if res.status_code != 200:
            return jsonify(res.json()), res.status_code

        res = rutils.rocket_service.invite_user_to_group(rocket_group=ids_division.group,
                                                         rocket_user=ids_division.user)
        if res.status_code != 200:
            return jsonify(res.json()), res.status_code

        return jsonify({'message': 'success'}), 200


user_team_chats_view = UserTeamsChatsViewSet.as_view('user_teams_chats_api')
blueprint.add_url_rule('users/<uid>/teams/<team_machine_name>/chats',
                       view_func=user_team_chats_view,
                       methods=['POST'])

user_rocket_channels_view = UserRocketChannels.as_view('user_rocket_channels')
blueprint.add_url_rule('users/<user_id>/channels', view_func=user_rocket_channels_view, methods=['POST'])
blueprint.add_url_rule('users/<user_id>/channels/<room>', view_func=user_rocket_channels_view, methods=['DELETE'])

user_rocket_groups_view = UserRocketGroups.as_view('user_rocket_groups')
blueprint.add_url_rule('users/<user_id>/groups', view_func=user_rocket_groups_view, methods=['POST'])
blueprint.add_url_rule('users/<user_id>/channels/<room>', view_func=user_rocket_groups_view, methods=['DELETE'])
