from flask import Blueprint, jsonify, request, abort, current_app
from flask.views import MethodView

from edap import Edap

from backend.utils import EncoderWithBytes
from backend.settings import EDAP_USER, EDAP_DOMAIN, EDAP_HOSTNAME, EDAP_PASSWORD

from .utils import get_config_divisions

blueprint = Blueprint('divisions_api', __name__, url_prefix='/api/ldap/')
blueprint.json_encoder = EncoderWithBytes


class EdapMixin:

    @property
    def edap(self):
        return Edap(EDAP_HOSTNAME, EDAP_USER, EDAP_PASSWORD, EDAP_DOMAIN)


class DivisionsListViewSet(EdapMixin, MethodView):

    def get(self):
        """ Get divisions """
        return jsonify(get_config_divisions())

    def post(self):
        """ Create division that present in config file, but not in ldap """
        division = request.json.get('division')
        if not division:
            return jsonify({"message": "Division is required"}), 400
        config_divisions = get_config_divisions()
        if division not in config_divisions:
            return jsonify({"message": "Division doesn't exist in config file"}), 400
        self.edap.create_division(config_divisions[division], description=division)
        return jsonify({'message': 'Success'})


class DivisionViewSet(EdapMixin, MethodView):

    def delete(self, division):
        divisions = get_config_divisions()
        if division not in divisions:
            return jsonify({"message": "Division doesn't exist in config file"}), 400
        # TODO: implement object deletion in edap project first
        return jsonify({'message': 'Deleted'}), 202


divisions_list_view = DivisionsListViewSet.as_view('divisions_api')
blueprint.add_url_rule('divisions/', view_func=divisions_list_view, methods=['GET', 'POST'])

division_view = DivisionViewSet.as_view('division_api')
blueprint.add_url_rule('divisions/<division>', view_func=division_view, methods=['DELETE'])
