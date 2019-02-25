from flask import Blueprint, jsonify, request, abort
from flask.views import MethodView

from nextcloud import NextCloud

blueprint = Blueprint('nextcloud_api', __name__, url_prefix='/api')


class NextCloudMixin:

    @property
    def nextcloud(self):
        """ Get nextcloud instance """
        # tmp mock nextcloud credentials
        url = 'http://localhost:8080'
        username = 'admin'
        password = 'admin'
        if url is None or username is None or password is None:
            return abort(400)
        nxc = NextCloud(endpoint=url, user=username, password=password)
        return nxc

    def nxc_response(self, nextcloud_response):
        return jsonify({
            'status': nextcloud_response.is_ok,
            'message': nextcloud_response.meta.get('message', ''),
            'data': nextcloud_response.data
            })


class UserViewSet(NextCloudMixin,
                  MethodView):

    def get(self, username=None):
        """ List users """
        if username is None:
            res = self.nextcloud.get_users()
            return self.nxc_response(res)
        else:
            res = self.nextcloud.get_user(username)
            return self.nxc_response(res)

    def post(self):
        """ Create user """
        username = request.json.get('username')
        password = request.json.get('password')
        if not all([username, password]):
            return abort(400)
        res = self.nextcloud.add_user(username, password)
        return self.nxc_response(res)

    def delete(self, username):
        """ Delete user """
        if not username:
            return abort(400)
        res = self.nextcloud.delete_user(username)
        return self.nxc_response(res)

    def patch(self, username, action=None):
        if action is not None:
            if action not in ['enable', 'disable']:
                return jsonify({}), 404
            res = self.nextcloud.enable_user(username) if action == 'enable' else self.nextcloud.disable_user(username)
            return self.nxc_response(res)
        param = request.json.get('param')
        value = request.json.get('value')
        if not all([param, value]):
            return jsonify({}), 400
        res = self.nextcloud.edit_user(username, param, value)
        return self.nxc_response(res)


user_view = UserViewSet.as_view('users_api')
blueprint.add_url_rule('/users/', view_func=user_view, methods=['GET', 'POST'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['GET', 'DELETE'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['PATCH'])
blueprint.add_url_rule('/users/<username>/<action>', view_func=user_view, methods=['PATCH'])
