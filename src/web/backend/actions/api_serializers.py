from marshmallow import Schema, fields

from .models import Action


class ApiActionSchema(Schema):
    event_display = fields.Function(lambda obj: obj.get_event_display())

    class Meta:
        fields = ['id', 'event', 'timestamp', 'data', 'message', 'success', 'event_display']
        model = Action


api_actions_schema = ApiActionSchema(many=True)
