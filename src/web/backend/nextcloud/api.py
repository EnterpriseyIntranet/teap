from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from nextcloud import NextCloud

blueprint = Blueprint('nextcloud_api', __name__, url_prefix='/api')

ALLOWED_GROUP_TYPES = ['divisions', 'countries', 'other']


class NextCloudMixin:

    @property
    def nextcloud(self):
        """ Get nextcloud instance """
        # TODO move to singleton global object
        url = current_app.config['NEXTCLOUD_HOST']
        username = current_app.config['NEXTCLOUD_USER']
        password = current_app.config['NEXTCLOUD_PASSWORD']
        if url is None or username is None or password is None:
            return jsonify({'message': 'url, username, password fields are required'}), 400
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
            if res.meta['statuscode'] == 404:
                return jsonify({'message': 'User does not exist'}), 404
            return self.nxc_response(res)

    def post(self):
        """ Create user """
        username = request.json.get('username')
        password = request.json.get('password')
        groups = request.json.get('groups', [])
        if not all([username, password]):
            return jsonify({'message': 'username, password fields are required'}), 400
        res = self.nextcloud.add_user(username, password)
        for group in groups:
            self.nextcloud.add_to_group(username, group)
        return self.nxc_response(res), 201

    def delete(self, username):
        """ Delete user """
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


class UserGroupViewSet(NextCloudMixin,
                       MethodView):

    def post(self, username):
        """ Add user to group """
        group_name = request.json.get('group_name')
        if not group_name:
            return jsonify({'message': 'group_name is required parameter'}), 400
        if not self.nextcloud.get_group(group_name).is_ok:
            return jsonify({"message": "group not found"}), 404
        res = self.nextcloud.add_to_group(username, group_name)
        return self.nxc_response(res)

    def delete(self, username, group_name):
        """ Remove user from group """
        res = self.nextcloud.remove_from_group(username, group_name)
        return self.nxc_response(res)


class GroupViewSet(NextCloudMixin,
                   MethodView):

    def get(self, group_name=None, action=None):
        """ List groups """

        if group_name is None and action is None:  # groups list
            query = request.args.get('query')
            res = self.nextcloud.get_groups(search=query)
            return self.nxc_response(res)

        elif group_name and action is None:  # single group
            res = self.nextcloud.get_group(group_name)
            if res.meta['statuscode'] == 404:
                return jsonify({'message': 'Group does not exist'}), 404
            return self.nxc_response(res)

        elif group_name and action == "subadmins":  # group subadmins
            res = self.nextcloud.get_subadmins(group_name)
            return self.nxc_response(res)

        else:
            return jsonify({'message': 'Bad request'}), 400

    def post(self, group_name=None):
        """ Create group """
        if group_name:  # create subadmin
            username = request.json.get('username')
            if not username:
                return jsonify({'message': 'username is required'}), 400
            if not self.nextcloud.get_group(group_name).is_ok:
                return jsonify({"message": "group not found"}), 404
            res = self.nextcloud.create_subadmin(username, group_name)
            return self.nxc_response(res), 201
        else:  # create group
            group_name = request.json.get('group_name')
            if not group_name:
                return jsonify({'message': 'group_name is required'}), 400
            res = self.nextcloud.add_group(group_name)
            return self.nxc_response(res), 201

    def delete(self, group_name=None, username=None):
        """ Delete group """
        if group_name: # delete single group/subadmin
            if username:  # delete subadmin
                if not self.nextcloud.get_group(group_name).is_ok:
                    return jsonify({"message": "group not found"}), 404
                res = self.nextcloud.remove_subadmin(username, group_name)
                return self.nxc_response(res), 202
            else:
                res = self.nextcloud.delete_group(group_name)
                return self.nxc_response(res), 202
        else:  # mass delete
            groups = request.json.get('groups')
            empty = request.json.get('empty') #  flag to delete only empty groups

            for group_name in groups:
                group = self.nextcloud.get_group(group_name)

                if not group.is_ok:
                    continue

                if empty:
                    if len(group.data['users']) == 0:
                        self.nextcloud.delete_group(group_name)
                else:
                    self.nextcloud.delete_group(group_name)

            return jsonify({"message": "ok"}), 202


class GroupWithFolderViewSet(NextCloudMixin, MethodView):

    def post(self):
        group_name = request.json.get('group_name')
        group_type = request.json.get('group_type')

        if not group_name or not group_type:  # check if all params present
            return jsonify({'message': 'group_name, group_type are required parameters'}), 400

        if group_type.lower() not in ALLOWED_GROUP_TYPES:  # check if group type in list of allowed types
            return jsonify({"message": "Not allowed group type"}), 400

        # check division group name
        if group_type.lower() == 'divisions' and not group_name.lower().startswith("division"):
            return jsonify({"message": 'Division group name must start with "Division"'}), 400

        # check countries group name
        if group_type.lower() == 'countries' and not group_name.lower().startswith("country"):
            return jsonify({"message": 'Country group name must start with "Country"'}), 400

        if self.nextcloud.get_group(group_name).is_ok:  # check if group with such name doesn't exist
            return jsonify({"message": "Group with this name already exists"}), 400

        create_group_res = self.nextcloud.add_group(group_name)  # create group
        if not create_group_res.is_ok:
            return jsonify({"message": "Something went wrong during group creation"}), 400

        # check if folder for type is already created
        group_folders = self.nextcloud.get_group_folders().data
        folder_id = None
        for key, value in group_folders.items():
            if value['mount_point'] == group_type:
                folder_id = key
                break
        if folder_id is not None:
            self.nextcloud.grant_access_to_group_folder(folder_id, group_name)
        else:
            create_type_folder_res = self.nextcloud.create_group_folder(group_type)
            self.nextcloud.grant_access_to_group_folder(create_type_folder_res.data['id'], group_name)

        create_folder_res = self.nextcloud.create_group_folder("/".join([group_type, group_name]))  # create folder
        grant_folder_perms_res = self.nextcloud.grant_access_to_group_folder(create_folder_res.data['id'], group_name)
        if not create_folder_res.is_ok or not grant_folder_perms_res.is_ok:
            self.nextcloud.delete_group(group_name)
            return jsonify({"message": "Something went wrong during group folder creation"}), 400

        return jsonify({"message": "Group with group folder successfully created"}), 201


user_view = UserViewSet.as_view('users_api')
blueprint.add_url_rule('/users/', view_func=user_view, methods=['GET', 'POST'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['GET', 'DELETE'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['PATCH'])
blueprint.add_url_rule('/users/<username>/<action>', view_func=user_view, methods=['PATCH'])

user_group_view = UserGroupViewSet.as_view('user_groups_api')
blueprint.add_url_rule('/users/<username>/groups/', view_func=user_group_view, methods=['POST'])
blueprint.add_url_rule('/users/<username>/groups/<group_name>', view_func=user_group_view, methods=['DELETE'])

group_view = GroupViewSet.as_view('groups_api')
blueprint.add_url_rule('/groups/', view_func=group_view, methods=["GET", "POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>', view_func=group_view, methods=["GET", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/<action>', view_func=group_view, methods=["GET"])
blueprint.add_url_rule('/groups/<group_name>/subadmins', view_func=group_view, methods=["POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/subadmins/<username>', view_func=group_view, methods=["DELETE"])

group_with_folder_view = GroupWithFolderViewSet.as_view('groups_with_folder_api')
blueprint.add_url_rule('/groups-with-folders', view_func=group_with_folder_view, methods=["POST"])
