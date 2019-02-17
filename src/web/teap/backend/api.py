from flask import Blueprint, jsonify, request, abort
from flask.views import MethodView

from nextcloud import NextCloud

api = Blueprint('api', 'api')


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


class UserViewSet(NextCloudMixin,
                  MethodView):

    def get(self):
        """ List users """
        res = self.nextcloud.get_users()
        return jsonify(res.data)

    def post(self):
        """ Create user """
        breakpoint()
        username = request.json.get('username')
        password = request.json.get('password')
        if not all([username, password]):
            return abort(400)
        res = self.nextcloud.add_user(username, password)
        return jsonify({'status': res.is_ok, 'message': res.meta.get('message', '')})

    def delete(self, username):
        """ Delete user """
        if not username:
            return abort(400)
        res = self.nextcloud.delete_user(username)
        return jsonify({'status': res.is_ok})


user_view = UserViewSet.as_view('users_api')
api.add_url_rule('/users', view_func=user_view, methods=['GET', 'POST'])
api.add_url_rule('/users/<username>', view_func=user_view, methods=['DELETE'])
