from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from edap import Edap, ObjectDoesNotExist

from backend.utils import EncoderWithBytes
from backend.settings import EDAP_USER, EDAP_DOMAIN, EDAP_HOSTNAME, EDAP_PASSWORD

from .utils import get_config_divisions, merge_divisions

blueprint = Blueprint('divisions_api', __name__, url_prefix='/api/ldap/')
blueprint.json_encoder = EncoderWithBytes


class EdapMixin:

    @property
    def edap(self):
        return Edap(EDAP_HOSTNAME, EDAP_USER, EDAP_PASSWORD, EDAP_DOMAIN)


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
        self.edap.create_division(div_machine_name, display_name=config_divisions[div_machine_name])
        return jsonify({'message': 'Success'})


class DivisionViewSet(EdapMixin, MethodView):

    def delete(self, division_name):
        self.edap.delete_division(division_name)
        return jsonify({'message': 'Deleted'}), 202


class FranchiseViewSet(EdapMixin, MethodView):

    def get(self):
        franchises = self.edap.get_franchises()
        return jsonify(franchises)

    def post(self):
        franchise_code = request.json.get('franchise_code')
        try:
            res = self.edap.create_franchise(franchise_code)
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        return jsonify({'message': 'success'}), 201


divisions_list_view = DivisionsListViewSet.as_view('divisions_api')
blueprint.add_url_rule('divisions', view_func=divisions_list_view, methods=['GET', 'POST'])

division_view = DivisionViewSet.as_view('division_api')
blueprint.add_url_rule('divisions/<division_name>', view_func=division_view, methods=['DELETE'])

franchise_view = FranchiseViewSet.as_view('franchise_api')
blueprint.add_url_rule('franchises', view_func=franchise_view, methods=['GET', 'POST'])
