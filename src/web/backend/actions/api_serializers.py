from marshmallow import Schema, fields

from .models import Action


class ApiActionSchema(Schema):
    event_display = fields.Function(lambda obj: obj.get_event_display())

    class Meta:
        fields = ['id', 'event_name', 'timestamp', 'data', 'message', 'status', 'event_display']
        model = Action


api_actions_schema = ApiActionSchema(many=True)
