from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from nextcloud import NextCloud
from edap import Edap, ConstraintError

from backend.utils import EncoderWithBytes
from backend.settings import EDAP_USER, EDAP_DOMAIN, EDAP_HOSTNAME, EDAP_PASSWORD
from .utils import edap_to_dict

blueprint = Blueprint('nextcloud_api', __name__, url_prefix='/api')
blueprint.json_encoder = EncoderWithBytes

ALLOWED_GROUP_TYPES = ['divisions', 'countries', 'other']


# try:
#     edap = Edap(EDAP_HOSTNAME, EDAP_USER, EDAP_PASSWORD, EDAP_DOMAIN)
#     edap_exc = None
# except Exception as e:
#     edap = None
#     edap_exc = e


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

    @property
    def edap(self):
        return Edap(EDAP_HOSTNAME, EDAP_USER, EDAP_PASSWORD, EDAP_DOMAIN)

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
            res = self.edap.get_users()
            return jsonify(res)
        else:
            res = self.edap.get_user(username)
            user_groups = self.edap.get_user_groups(username)
            if not res:
                return jsonify({'message': 'User does not exist'}), 404
            elif len(res) > 1:
                return jsonify({'message': 'More than 1 user found'}), 409
            res = {
                **edap_to_dict(res[0]),
                "groups": [edap_to_dict(group) for group in user_groups]
            }
            return jsonify(res)

    def post(self):
        """ Create user """
        username = request.json.get('username')
        password = request.json.get('password')
        name = request.json.get('name')
        surname = request.json.get('surname')
        groups = request.json.get('groups', [])
        if not all([username, password, name, surname]):
            return jsonify({'message': 'username, password, name, surname fields are required'}), 400

        try:
            self.edap.add_user(username, name, surname, password)
        except ConstraintError as e:
            return jsonify({'message': "Failed to create user. {}".format(e)})

        for group in groups:
            self.edap.make_uid_member_of(username, group)

        return jsonify({'status': True})

    def delete(self, username):
        """ Delete user """
        # TODO: switch to edap
        res = self.nextcloud.delete_user(username)
        return self.nxc_response(res)

    def patch(self, username, action=None):
        # TODO: switch to edap
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
        fqdn = request.json.get('fqdn')
        if not fqdn:
            return jsonify({'message': 'fqdn is required parameter'}), 400
        try:
            self.edap.make_uid_member_of(username, fqdn)
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 404
        return jsonify({'message': 'Success'}), 200

    def delete(self, username):
        """ Remove user from group """
        fqdn = request.json.get('fqdn')
        if not fqdn:
            return jsonify({'message': 'fqdn is a required parameter'})
        try:
            res = self.edap.remove_uid_member_of(username, fqdn)
        except ConstraintError as e:
            return jsonify({'message': f'Failed to delete. {e}'}), 400
        return jsonify({'message': 'Success'}), 202


class GroupViewSet(NextCloudMixin,
                   MethodView):

    def get(self, group_name=None, action=None):
        """ List groups """

        if group_name is None and action is None:  # groups list
            query = request.args.get('query')
            search = f'cn={query}*' if query else None
            res = self.edap.get_groups(search=search)
            return jsonify([edap_to_dict(obj) for obj in res]), 200

        elif group_name and action is None:  # single group
            try:
                res = self.edap.get_group(group_name)
            except ConstraintError as e:
                return jsonify({'message': f'Group not found. {e}'}), 404
            if len(res) == 0:
                return jsonify({'message': f'Group not found.'}), 404
            elif len(res) > 1:
                return jsonify({'message': f'More than 1 gorup found'}), 409
            return jsonify(edap_to_dict(res[0]))

        # TODO: switch to edap
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
        if group_folders:  # if there is no group folders, response data will be empty list
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
blueprint.add_url_rule('/users/<username>/groups/', view_func=user_group_view, methods=['POST', 'DELETE'])

group_view = GroupViewSet.as_view('groups_api')
blueprint.add_url_rule('/groups/', view_func=group_view, methods=["GET", "POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>', view_func=group_view, methods=["GET", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/<action>', view_func=group_view, methods=["GET"])
blueprint.add_url_rule('/groups/<group_name>/subadmins', view_func=group_view, methods=["POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/subadmins/<username>', view_func=group_view, methods=["DELETE"])

group_with_folder_view = GroupWithFolderViewSet.as_view('groups_with_folder_api')
blueprint.add_url_rule('/groups-with-folders', view_func=group_with_folder_view, methods=["POST"])
