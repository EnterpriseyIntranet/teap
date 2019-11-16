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

    res = rutils.rocket_service.create_chat_user(username, password, email, name)
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
        rocket_user = rutils.rocket_service.get_user_by_username(user_id)
        rocket_channel = rutils.rocket_service.get_channel_by_name(channel)

        if not rocket_channel:
            return jsonify({'message': 'Rocket channel not found'}), 404

        if not rocket_user:
            return jsonify({'message': 'Rocket user not found'}), 404

        res = rutils.rocket_service.invite_user_to_channel(rocket_channel=rocket_channel['_id'],
                                                    rocket_user=rocket_user['_id'])
        return jsonify(res.json()), res.status_code

    def delete(self, user_id, channel):
        rocket_user = rutils.rocket_service.get_user_by_username(user_id)
        rocket_channel = rutils.rocket_service.get_channel_by_name(channel)

        if not rocket_channel:
            return jsonify({'message': 'Rocket channel not found'}), 404

        if not rocket_user:
            return jsonify({'message': 'Rocket user not found'}), 404

        self.rocket.channels_kick(rocket_channel['_id'], rocket_user['_id'])
        return jsonify({"message": "success"}), 202


class UserTeamsChatsViewSet(rutils.RocketMixin, EdapMixin, MethodView):

    def post(self, uid, team_machine_name):
        """ Add user to team chats """
        from ..ldap.serializers import edap_team_schema
        team = edap_team_schema.load(self.edap.get_team(team_machine_name))
        try:
            franchise, division = team.get_team_components()
        except ObjectDoesNotExist:
            return jsonify({'message': 'Team corresponding franchise or division are not found'}), 404

        user = rutils.rocket_service.get_user_by_username(uid)

        franchise_channel = rutils.rocket_service.get_channel_by_name(franchise.chat_name)
        division_channel = rutils.rocket_service.get_channel_by_name(division.chat_name)

        if not all([user, franchise_channel, division_channel]):
            return jsonify({'message': 'Corresponding franchise or division channels not found'}), 400

        franchise_chat_res = rutils.rocket_service.invite_user_to_channel(rocket_channel=franchise_channel['_id'],
                                                                   rocket_user=user['_id'])
        division_chat_res = rutils.rocket_service.invite_user_to_channel(rocket_channel=division_channel['_id'],
                                                                  rocket_user=user['_id'])

        if franchise_chat_res.status_code != 200:
            return jsonify(franchise_chat_res.json()), franchise_chat_res.status_code

        if division_chat_res.status_code != 200:
            return jsonify(division_chat_res.json()), division_chat_res.status_code

        return jsonify({'message': 'success'}), 200


user_team_chats_view = UserTeamsChatsViewSet.as_view('user_teams_chats_api')
blueprint.add_url_rule('users/<uid>/teams/<team_machine_name>/chats',
                       view_func=user_team_chats_view,
                       methods=['POST'])

user_rocket_channels_view = UserRocketChannels.as_view('user_rocket_channels')
blueprint.add_url_rule('users/<user_id>/channels', view_func=user_rocket_channels_view, methods=['POST'])
blueprint.add_url_rule('users/<user_id>/channels/<channel>', view_func=user_rocket_channels_view, methods=['DELETE'])
