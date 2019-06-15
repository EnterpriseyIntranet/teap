from flask import Blueprint, jsonify, request, g

from .utils import get_rocket

blueprint = Blueprint('rocket_chat_api', __name__, url_prefix='/api/rocket')


def check_rocket_authorized():
    rocket = get_rocket()
    if not rocket:
        rocket_exception = g.rocket_exception
        return jsonify({
            "message": "Rocket chat instance problem with authorization. {}".format(str(rocket_exception))
        }), 400


blueprint.before_request(check_rocket_authorized)


@blueprint.route('users', methods=["POST"])
def create_user():
    rocket = get_rocket()
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    name = request.json.get('name')
    if not all([username, password, email, name]):
        return jsonify({"message": "username, password, email, name are required fields"}), 400

    res = rocket.users_create(email, name, password, username, requirePasswordChange=True)
    data = res.json()

    if res.status_code == 200 and data.get('success', True):
        return jsonify({'user': data.get('user')}), 201
    else:
        return jsonify({'message': data.get('error', ' Something wrong happened')}), 400


@blueprint.route('users/<user_id>/groups')
def invite_to_groups(user_id):
    rocket = get_rocket()
    groups_ids = request.json.get('groups')

    if not groups_ids:
        return jsonify({"message": "groups is required parameter"}), 400

    for group_id in groups_ids:
        rocket.groups_invite(group_id, user_id)

    return jsonify({"message": "Success"})


@blueprint.route('channels', methods=["POST"])
def create_channel():
    rocket = get_rocket()
    channel_name = request.json.get('channel_name')
    res = rocket.channels_create(channel_name)
    res_data = res.json()
    return jsonify(res_data), res.status_code

