from flask import Blueprint
from flask_restful import Api, Resource, reqparse

from .models import Action
from .api_serializers import api_actions_schema

blueprint = Blueprint('actions_api', __name__, url_prefix='/api/')
api = Api(blueprint)

ACTIONS_PER_PAGE = 20

actions_reqparser = reqparse.RequestParser()
actions_reqparser.add_argument('page', type=int, default=1)


class ActionsList(Resource):

    def get(self):
        args = actions_reqparser.parse_args()
        actions_qs = Action.query.filter()
        actions = actions_qs.offset((args.get('page') - 1) * ACTIONS_PER_PAGE).limit(ACTIONS_PER_PAGE)
        return {
            'data': api_actions_schema.dump(actions).data,
            'count': actions_qs.count()
        }


class ActionRetrieve(Resource):

    def post(self, id):
        action = Action.query.get(id)
        if not action:
            return {'message': 'object not found'}, 404
        action.execute()
        return {'message': 'action retried'}


api.add_resource(ActionsList, 'actions')
api.add_resource(ActionRetrieve, 'actions/<int:id>')
