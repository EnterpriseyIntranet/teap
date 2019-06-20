from flask import Blueprint, jsonify, request
from flask.views import MethodView
from edap import ObjectDoesNotExist, ConstraintError

from backend.utils import EncoderWithBytes
from .serializers import edap_user_schema, edap_franchise_schema, edap_franchises_schema
from .api_serializers import api_franchise_schema, api_franchises_schema
from .models import LdapDivision, LdapFranchise
from .utils import get_config_divisions, merge_divisions, get_edap

blueprint = Blueprint('divisions_api', __name__, url_prefix='/api/ldap/')
blueprint.json_encoder = EncoderWithBytes


@blueprint.errorhandler(ObjectDoesNotExist)
def handle_not_found(e):
    return jsonify({'message': str(e)})


class EdapMixin:

    @property
    def edap(self):
        return get_edap()


class DivisionsListViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get divisions """
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
        division.create()
        return jsonify({'message': 'Success'})


class DivisionViewSet(EdapMixin, MethodView):

    def delete(self, division_name):
        self.edap.delete_division(division_name)
        return jsonify({'message': 'Deleted'}), 202


class FranchisesViewSet(EdapMixin, MethodView):

    def get(self):
        franchises = edap_franchises_schema.load(self.edap.get_franchises()).data
        return jsonify(api_franchises_schema.dump(franchises).data)

    def post(self):
        franchise = api_franchise_schema.load(request.json).data
        try:
            franchise.create()
        except ConstraintError as e:
            return jsonify({'message': str(e)}), 409
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        return jsonify(api_franchise_schema.dump(franchise).data), 201


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


class UserTeamsViewSet(EdapMixin, MethodView):

    def post(self, uid):
        """ add user to team """
        user = edap_user_schema.load(self.edap.get_user(uid)).data
        team_machine_name = request.json.get('team')
        user.add_to_team(team_machine_name)
        return {'message': 'success'}


divisions_list_view = DivisionsListViewSet.as_view('divisions_api')
blueprint.add_url_rule('divisions', view_func=divisions_list_view, methods=['GET', 'POST'])

division_view = DivisionViewSet.as_view('division_api')
blueprint.add_url_rule('divisions/<division_name>', view_func=division_view, methods=['DELETE'])

franchises_view = FranchisesViewSet.as_view('franchise_api')
blueprint.add_url_rule('franchises', view_func=franchises_view, methods=['GET', 'POST'])

blueprint.add_url_rule('franchises/<franchise_machine_name>/suggested-name',
                       view_func=suggest_franchise_name,
                       methods=['GET'])

franchise_folders_view = FranchiseFoldersViewSet.as_view('franchise_folders_api')
blueprint.add_url_rule('franchises/<franchise_machine_name>/folders', view_func=franchise_folders_view, methods=['POST'])

user_teams_view = UserTeamsViewSet.as_view('user_teams_api')
blueprint.add_url_rule('user-teams/<uid>', view_func=user_teams_view, methods=['POST'])
