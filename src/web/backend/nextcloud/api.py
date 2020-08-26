from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from edap import ConstraintError, MultipleObjectsFound, ObjectDoesNotExist

from .. import utils
from ..ldap.utils import EdapMixin

from .utils import get_nextcloud, flush_nextcloud_ldap_cache

blueprint = Blueprint('nextcloud_api', __name__, url_prefix='/api')
blueprint.json_encoder = utils.EncoderWithBytes

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


class GroupListViewSet(NextCloudMixin,
                       EdapMixin,
                       MethodView):

    def get(self):
        """ List groups """
        query = request.args.get('query')
        search = f'cn={query}*' if query else None
        res = self.edap.get_groups(search=search)
        return jsonify([obj for obj in res]), 200

    @utils.authorize_only_hr_admins()
    def post(self, group_name=None):
        """ Create group """
        group_name = request.json.get('group_name')
        if not group_name:
            return jsonify({'message': 'group_name is required'}), 400
        res = self.nextcloud.add_group(group_name)
        flush_nextcloud_ldap_cache(self.nextcloud)
        return self.nxc_response(res), 201

    @utils.authorize_only_hr_admins()
    def delete(self):
        """ Delete group """
        groups = request.json.get('groups')
        empty = request.json.get('empty')  # flag to delete only empty groups

        for group_name in groups:
            group = self.nextcloud.get_group(group_name)

            if not group.is_ok:
                continue

            if empty:
                if len(group.data['users']) == 0:
                    self.nextcloud.delete_group(group_name)
            else:
                self.nextcloud.delete_group(group_name)
        flush_nextcloud_ldap_cache(self.nextcloud)

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

    @utils.authorize_only_hr_admins()
    def delete(self, group_name, username=None):
        """ Delete group """
        res = self.nextcloud.delete_group(group_name)
        flush_nextcloud_ldap_cache(self.nextcloud)
        return self.nxc_response(res), 202


class GroupSubadminViewSet(NextCloudMixin, MethodView):
    # TODO: rewrite to EDAP ?
    def get(self, group_name):
        """ List group subadamins """
        res = self.nextcloud.get_subadmins(group_name)
        return self.nxc_response(res)

    @utils.authorize_only_hr_admins()
    def post(self, group_name):
        """ Create subadmin for group"""
        username = request.json.get('username')
        if not username:
            return jsonify({'message': 'username is required'}), 400
        if not self.nextcloud.get_group(group_name).is_ok:
            return jsonify({"message": "group not found"}), 404
        res = self.nextcloud.create_subadmin(username, group_name)
        return self.nxc_response(res), 201

    @utils.authorize_only_hr_admins()
    def delete(self, group_name, username):
        """ Delete subadmin """
        if not self.nextcloud.get_group(group_name).is_ok:
            return jsonify({"message": "group not found"}), 404
        res = self.nextcloud.remove_subadmin(username, group_name)
        return self.nxc_response(res), 202


group_list_view = GroupListViewSet.as_view('groups_api')
blueprint.add_url_rule('/groups/', view_func=group_list_view, methods=["GET", "POST", "DELETE"])

group_view = GroupViewSet.as_view('group_api')
blueprint.add_url_rule('/groups/<group_name>', view_func=group_view, methods=["GET", "DELETE"])

group_subadmins_view = GroupSubadminViewSet.as_view('group_subadmins_api')
blueprint.add_url_rule('/groups/<group_name>/subadmins', view_func=group_view, methods=["POST", "DELETE"])
blueprint.add_url_rule('/groups/<group_name>/subadmins/<username>', view_func=group_view, methods=["DELETE"])
