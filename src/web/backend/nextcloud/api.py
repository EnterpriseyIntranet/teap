from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from edap import ConstraintError, MultipleObjectsFound, ObjectDoesNotExist

from backend.utils import EncoderWithBytes
from backend.ldap.api import EdapMixin

from backend.ldap.serializers import edap_users_schema, edap_user_schema
from backend.ldap.api_serializers import api_user_schema, api_users_schema
from backend.ldap.models import LdapUser
from .utils import create_group_folder, get_nextcloud

blueprint = Blueprint('nextcloud_api', __name__, url_prefix='/api')
blueprint.json_encoder = EncoderWithBytes

ALLOWED_GROUP_TYPES = ['divisions', 'countries', 'other']


class NextCloudMixin:

    @property
    def nextcloud(self):
        """ Get nextcloud instance """
        return get_nextcloud()

    def nxc_response(self, nextcloud_response):
        return jsonify({
            'status': nextcloud_response.is_ok,
            'message': nextcloud_response.meta.get('message', ''),
            'data': nextcloud_response.data
            })


class UserListViewSet(NextCloudMixin, EdapMixin, MethodView):

    def get(self):
        """ List users """
        res = self.edap.get_users()
        data = edap_users_schema.load(res).data
        return jsonify(api_users_schema.dump(data).data)

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
            user = LdapUser(uid=username, given_name=name, surname=surname, groups=groups)
            user.create(password=password)
        except ConstraintError as e:
            return jsonify({'message': "Failed to create user. {}".format(e)})

        return jsonify({'status': True})


class UserRetrieveViewSet(NextCloudMixin,
                          EdapMixin,
                          MethodView):
    """ ViewSet for single user """
    def get(self, username):
        """ List users """
        try:
            res = edap_user_schema.load(self.edap.get_user(username)).data
        except MultipleObjectsFound:
            return jsonify({'message': 'More than 1 user found'}), 409
        except ObjectDoesNotExist:
            return jsonify({'message': 'User does not exist'}), 404
        user_groups = self.edap.get_user_groups(username)
        res = {
            **api_user_schema.dump(res).data,
            "groups": [group for group in user_groups]
        }
        return jsonify(res)

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
                       EdapMixin,
                       MethodView):

    def post(self, username):
        """ Add user to group """
        group_fqdn = request.json.get('fqdn')
        if not group_fqdn:
            return jsonify({'message': 'fqdn is required parameter'}), 400
        try:
            self.edap.make_uid_member_of(username, group_fqdn)
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 404
        return jsonify({'message': 'Success'}), 200

    def delete(self, username):
        """ Remove user from group """
        group_fqdn = request.json.get('fqdn')
        if not group_fqdn:
            return jsonify({'message': 'fqdn is a required parameter'})
        try:
            res = self.edap.remove_uid_member_of(username, group_fqdn)
        except ConstraintError as e:
            return jsonify({'message': f'Failed to delete. {e}'}), 400
        return jsonify({'message': 'Success'}), 202


class GroupListViewSet(NextCloudMixin,
                       EdapMixin,
                       MethodView):

    def get(self):
        """ List groups """
        query = request.args.get('query')
        search = f'cn={query}*' if query else None
        res = self.edap.get_groups(search=search)
        return jsonify([obj for obj in res]), 200

    def post(self, group_name=None):
        """ Create group """
        group_name = request.json.get('group_name')
        if not group_name:
            return jsonify({'message': 'group_name is required'}), 400
        res = self.nextcloud.add_group(group_name)
        return self.nxc_response(res), 201

    def delete(self):
        """ Delete group """
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


class GroupViewSet(NextCloudMixin, EdapMixin, MethodView):

    def get(self, group_name):
        """ List groups """
        try:
            res = self.edap.get_groups(search=f'cn={group_name}')
        except ConstraintError as e:
            return jsonify({'message': f'Group not found. {e}'}), 404
        if len(res) == 0:
            return jsonify({'message': f'Group not found.'}), 404
        elif len(res) > 1:
            return jsonify({'message': f'More than 1 group found'}), 409
        return jsonify(res[0])

    def delete(self, group_name, username=None):
        """ Delete group """
        res = self.nextcloud.delete_group(group_name)
        return self.nxc_response(res), 202


class GroupSubadminViewSet(NextCloudMixin, MethodView):
    # TODO: rewrite to EDAP ?
    def get(self, group_name):
        """ List group subadamins """
        res = self.nextcloud.get_subadmins(group_name)
        return self.nxc_response(res)

    def post(self, group_name):
        """ Create subadmin for group"""
        username = request.json.get('username')
        if not username:
            return jsonify({'message': 'username is required'}), 400
        if not self.nextcloud.get_group(group_name).is_ok:
            return jsonify({"message": "group not found"}), 404
        res = self.nextcloud.create_subadmin(username, group_name)
        return self.nxc_response(res), 201

    def delete(self, group_name, username):
        """ Delete subadmin """
        if not self.nextcloud.get_group(group_name).is_ok:
            return jsonify({"message": "group not found"}), 404
        res = self.nextcloud.remove_subadmin(username, group_name)
        return self.nxc_response(res), 202


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

        create_groupfolder_res = create_group_folder(group_name, group_type)

        if not create_groupfolder_res:
            return jsonify({"message": "Something went wrong during group folder creation"}), 400

        return jsonify({"message": "Group with group folder successfully created"}), 201


class GroupFolderViewSet(EdapMixin, NextCloudMixin, MethodView):

    def post(self):
        """ Create group folder for given group """
        group_name = request.json.get('group_name')
        group_type = request.json.get('group_type')

        if not group_name or not group_type:  # check if all params present
            return jsonify({'message': 'group_name, group_type are required parameters'}), 400

        create_groupfolder_res = create_group_folder(group_name, group_type)

        if not create_groupfolder_res:
            return jsonify({"message": "Something went wrong during group folder creation"}), 400

        return jsonify({"message": "Group folder successfully created"}), 201


user_list_view = UserListViewSet.as_view('users_api')
blueprint.add_url_rule('/users/', view_func=user_list_view, methods=['GET', 'POST'])

user_view = UserRetrieveViewSet.as_view('user_api')
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['GET', 'DELETE'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['PATCH'])
blueprint.add_url_rule('/users/<username>/<action>', view_func=user_view, methods=['PATCH'])

user_group_view = UserGroupViewSet.as_view('user_groups_api')
blueprint.add_url_rule('/users/<username>/groups/', view_func=user_group_view, methods=['POST', 'DELETE'])

group_list_view = GroupListViewSet.as_view('groups_api')
blueprint.add_url_rule('/groups/', view_func=group_list_view, methods=["GET", "POST", "DELETE"])

group_view = GroupViewSet.as_view('group_api')
blueprint.add_url_rule('/groups/<group_name>', view_func=group_view, methods=["GET", "DELETE"])

group_subadmins_view = GroupSubadminViewSet.as_view('group_subadmins_api')
blueprint.add_url_rule('/groups/<group_name>/subadmins', view_func=group_view, methods=["POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/subadmins/<username>', view_func=group_view, methods=["DELETE"])

group_with_folder_view = GroupWithFolderViewSet.as_view('groups_with_folder_api')
blueprint.add_url_rule('/groups-with-folders', view_func=group_with_folder_view, methods=["POST"])

group_folder_view = GroupFolderViewSet.as_view('groupfolder_api')
blueprint.add_url_rule('/groupfolder', view_func=group_folder_view, methods=["POST"])
