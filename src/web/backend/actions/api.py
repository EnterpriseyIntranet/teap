from flask import Blueprint
from flask_restful import Api, Resource

from .models import Action
from .api_serializers import api_actions_schema

blueprint = Blueprint('actions_api', __name__, url_prefix='/api/')
api = Api(blueprint)


class ActionsList(Resource):

    def get(self):
        actions = Action.query.all()
        return api_actions_schema.dump(actions).data


class ActionRetrieve(Resource):

    def post(self, id):
        action = Action.query.get(id)
        if not action:
            return {'message': 'object not found'}, 404
        action.execute()
        return {'message': 'action retried'}


api.add_resource(ActionsList, 'actions')
api.add_resource(ActionRetrieve, 'actions/<int:id>')
