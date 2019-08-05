from flask import Blueprint, jsonify, request
from flask.views import MethodView
from edap import ObjectDoesNotExist, ConstraintError, MultipleObjectsFound

from ..utils import EncoderWithBytes
from .serializers import edap_user_schema, edap_users_schema, edap_franchise_schema, edap_franchises_schema, \
    edap_divisions_schema, edap_teams_schema, edap_division_schema
from .api_serializers import api_franchise_schema, api_user_schema, api_users_schema, api_franchises_schema, \
    api_divisions_schema, api_teams_schema

from .models import LdapDivision, LdapFranchise
from .utils import get_config_divisions, merge_divisions, EdapMixin

blueprint = Blueprint('divisions_api', __name__, url_prefix='/api/ldap/')
blueprint.json_encoder = EncoderWithBytes


@blueprint.errorhandler(ObjectDoesNotExist)
def handle_not_found(e):
    return jsonify({'message': str(e)}), 404


class UserListViewSet(EdapMixin, MethodView):

    def get(self):
        """ List users """
        res = self.edap.get_users()
        data = edap_users_schema.load(res).data
        return jsonify(api_users_schema.dump(data).data)

    def post(self):
        """ Create user """
        username = request.json.get('uid')
        password = request.json.get('password')
        name = request.json.get('name')
        surname = request.json.get('surname')
        if not all([username, password, name, surname]):
            return jsonify({'message': 'username, password, name, surname fields are required'}), 400

        user = api_user_schema.load(request.json).data
        try:
            res = user.create(password=password)
        except ConstraintError as e:
            return jsonify({'message': "Failed to create user. {}".format(e)}), 400

        return jsonify(res)


class UserRetrieveViewSet(EdapMixin,
                          MethodView):
    """ ViewSet for single user """
    def get(self, username):
        """ List users """
        try:
            user = edap_user_schema.load(self.edap.get_user(username)).data
        except MultipleObjectsFound:
            return jsonify({'message': 'More than 1 user found'}), 409
        except ObjectDoesNotExist:
            return jsonify({'message': 'User does not exist'}), 404
        user_groups = self.edap.get_user_groups(username)
        user = {
            **api_user_schema.dump(user).data,
            "groups": [group for group in user_groups],
            "franchises": api_franchises_schema.dump(user.get_franchises()).data,
            "divisions": api_divisions_schema.dump(user.get_divisions()).data,
            "teams": api_teams_schema.dump(user.get_teams()).data
        }
        return jsonify(user)

    def delete(self, username):
        """ Delete user """
        result = dict(success=True)
        try:
            self.edap.delete_user(username)
        except Exception as exc:
            result['success'] = False
            result['message'] = str(exc)
            return jsonify(result), 500
        return jsonify(result)


class UserGroupViewSet(EdapMixin,
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
            self.edap.remove_uid_member_of(username, group_fqdn)
        except ConstraintError as e:
            return jsonify({'message': f'Failed to delete. {e}'}), 400
        return jsonify({'message': 'Success'}), 202


class ConfigDivisionsListViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get merged divisions from config and ldap """
        ldap_divisions = self.edap.get_divisions()
        config_divisions = get_config_divisions()
        divisions = merge_divisions(config_divisions, ldap_divisions)
        return jsonify({'divisions': divisions})

    def post(self):
        """ Create division that present in config file, but not in ldap """
        div_machine_name = request.json.get('machine_name')
        if not div_machine_name:
            return jsonify({"message": "'machine_name' is required field"}), 400
        config_divisions = get_config_divisions()
        if div_machine_name not in config_divisions:
            return jsonify({"message": "Division doesn't exist in config file"}), 400
        div_display_name = config_divisions[div_machine_name]
        division = LdapDivision(machine_name=div_machine_name, display_name=div_display_name)
        res = division.create()
        return jsonify(res)


class DivisionsViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get divisions from ldap """
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        ldap_divisions = edap_divisions_schema.load(self.edap.get_divisions(search)).data
        return jsonify(api_divisions_schema.dump(ldap_divisions).data)


class DivisionViewSet(EdapMixin, MethodView):

    def delete(self, division_name):
        self.edap.delete_division(division_name)
        return jsonify({'message': 'Deleted'}), 202


class FranchisesViewSet(EdapMixin, MethodView):

    def get(self):
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        franchises = edap_franchises_schema.load(self.edap.get_franchises(search)).data
        return jsonify(api_franchises_schema.dump(franchises).data)

    def post(self):
        franchise = api_franchise_schema.load(request.json).data
        try:
            create_res = franchise.create()
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 409
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        return jsonify(create_res), 201


def suggest_franchise_name(franchise_machine_name):
    try:
        suggested_name = LdapFranchise.suggest_name(franchise_machine_name)
    except KeyError:
        return jsonify({'message': 'Unknown country code'}), 400
    return jsonify({'data': suggested_name})


class FranchiseFoldersViewSet(EdapMixin, MethodView):

    def post(self, franchise_machine_name):
        franchise = edap_franchise_schema.load(self.edap.get_franchise(franchise_machine_name)).data
        res = franchise.create_folder(franchise.display_name)
        return jsonify({'success': res}), 201 if res else 500


class TeamsViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get teams from ldap """
        query = request.args.get('query')
        search = f"description={query}*" if query else ""
        ldap_teams = edap_teams_schema.load(self.edap.get_teams(search)).data
        return jsonify(api_teams_schema.dump(ldap_teams).data)


class TeamViewSet(EdapMixin, MethodView):

    def delete(self, machine_name):
        """ Delete single team """
        self.edap.delete_team(machine_name)
        return jsonify({'message': 'success'}), 202


class UserFranchisesViewSet(EdapMixin, MethodView):

    def post(self, uid):
        """ add user to franchise """
        user = edap_user_schema.load(self.edap.get_user(uid)).data  # to check if user exists, or return 404
        machine_name = request.json.get('machineName')
        franchise = edap_franchise_schema.load(self.edap.get_franchise(machine_name)).data
        franchise.add_user(uid)
        return jsonify({'message': 'success'}), 200

    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid)).data
        machine_name = request.json.get('machineName')
        user.remove_from_franchise(machine_name)
        return jsonify({'message': 'success'}), 202


class UserDivisionsViewSet(EdapMixin, MethodView):

    def post(self, uid):
        """ add user to team """
        user = edap_user_schema.load(self.edap.get_user(uid)).data  # to check if user exists, or return 404
        machine_name = request.json.get('machineName')
        division = edap_division_schema.load(self.edap.get_division(machine_name)).data
        division.add_user(uid)
        return jsonify({'message': 'success'}), 200

    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid)).data
        machine_name = request.json.get('machineName')
        user.remove_from_division(machine_name)
        return jsonify({'message': 'success'}), 202


class UserTeamsViewSet(EdapMixin, MethodView):

    def post(self, uid):
        """ add user to team """
        user = edap_user_schema.load(self.edap.get_user(uid)).data
        machine_name = request.json.get('machineName')
        user.add_to_team(machine_name)
        return jsonify({'message': 'success'}), 200

    def delete(self, uid):
        user = edap_user_schema.load(self.edap.get_user(uid)).data
        machine_name = request.json.get('machineName')
        user.remove_from_team(machine_name)
        return jsonify({'message': 'success'}), 202


user_list_view = UserListViewSet.as_view('users_api')
blueprint.add_url_rule('/users/', view_func=user_list_view, methods=['GET', 'POST'])

user_view = UserRetrieveViewSet.as_view('user_api')
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['GET', 'DELETE'])
blueprint.add_url_rule('/users/<username>', view_func=user_view, methods=['PATCH'])
blueprint.add_url_rule('/users/<username>/<action>', view_func=user_view, methods=['PATCH'])

user_group_view = UserGroupViewSet.as_view('user_groups_api')
blueprint.add_url_rule('/users/<username>/groups/', view_func=user_group_view, methods=['POST', 'DELETE'])

config_divisions_list_view = ConfigDivisionsListViewSet.as_view('config_divisions_api')
blueprint.add_url_rule('config-divisions', view_func=config_divisions_list_view, methods=['GET', 'POST'])

divisions_list_view = DivisionsViewSet.as_view('divisions_api')
blueprint.add_url_rule('divisions', view_func=divisions_list_view, methods=['GET'])

division_view = DivisionViewSet.as_view('division_api')
blueprint.add_url_rule('divisions/<division_name>', view_func=division_view, methods=['DELETE'])

franchises_view = FranchisesViewSet.as_view('franchise_api')
blueprint.add_url_rule('franchises', view_func=franchises_view, methods=['GET', 'POST'])

blueprint.add_url_rule('franchises/<franchise_machine_name>/suggested-name',
                       view_func=suggest_franchise_name,
                       methods=['GET'])

franchise_folders_view = FranchiseFoldersViewSet.as_view('franchise_folders_api')
blueprint.add_url_rule('franchises/<franchise_machine_name>/folders', view_func=franchise_folders_view, methods=['POST'])

teams_view = TeamsViewSet.as_view('teams_api')
blueprint.add_url_rule('teams', view_func=teams_view, methods=['GET'])

team_view = TeamViewSet.as_view('team_api')
blueprint.add_url_rule('teams/<machine_name>', view_func=team_view, methods=['DELETE'])

user_franchises_view = UserFranchisesViewSet.as_view('user_franchises_api')
blueprint.add_url_rule('user/<uid>/franchises', view_func=user_franchises_view, methods=['POST', 'DELETE'])

user_divisions_view = UserDivisionsViewSet.as_view('user_divisions_api')
blueprint.add_url_rule('user/<uid>/divisions', view_func=user_divisions_view, methods=['POST', 'DELETE'])

user_teams_view = UserTeamsViewSet.as_view('user_teams_api')
blueprint.add_url_rule('user/<uid>/teams', view_func=user_teams_view, methods=['POST', 'DELETE'])
