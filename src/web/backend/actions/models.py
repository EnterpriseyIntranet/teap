from backend.database import db, Column, Model, SurrogatePK

from sqlalchemy.dialects.postgresql import JSON

from datetime import datetime


class Action(SurrogatePK, Model):

    CREATE_ROCKET_USER = 'create_rocket_user'
    CREATE_ROCKET_CHANNEL = 'create_rocket_channel'

    ROCKET_EVENTS = [CREATE_ROCKET_CHANNEL, CREATE_ROCKET_USER]

    EVENT_CHOICES = {
        CREATE_ROCKET_CHANNEL: 'Rocket channel creation',
        CREATE_ROCKET_USER: 'Rocket user creation'
    }

    event = Column(db.String(50), nullable=False)
    timestamp = Column(db.DateTime, default=datetime.utcnow)
    data = Column(JSON)
    message = Column(db.String(500))
    success = Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Action success={self.success}, event={self.event}, data={self.data}>"

    @staticmethod
    def create_event(event, success=True, **kwargs):
        action = Action(event=event, data=kwargs, success=success)
        db.session.add(action)
        db.session.commit()

    def get_event_display(self):
        return self.EVENT_CHOICES.get(self.event)

    def execute(self):
        if self.event in self.ROCKET_EVENTS:
            return self._execute_rocket()

    def _execute_rocket(self):
        from backend.rocket_chat.utils import rocket_service
        if self.event == self.CREATE_ROCKET_USER:
            return rocket_service.create_user(**self.data)
        elif self.event == self.CREATE_ROCKET_CHANNEL:
            return rocket_service.create_channel(**self.data)