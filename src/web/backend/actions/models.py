import json
from datetime import datetime

from ..database import db, Column, Model, SurrogatePK


class ActionABC:

    CREATE_ROCKET_USER = 'create_rocket_user'

    CREATE_ROCKET_CHANNEL = 'create_rocket_channel'
    INVITE_USER_TO_CHANNEL = 'invite_user_to_channel'

    CREATE_ROCKET_GROUP = 'create_rocket_group'
    INVITE_USER_TO_GROUP = 'invite_user_to_group'

    ROCKET_EVENTS = [CREATE_ROCKET_CHANNEL, CREATE_ROCKET_USER, INVITE_USER_TO_CHANNEL]

    EVENT_CHOICES = {
        CREATE_ROCKET_USER: 'Rocket user creation',
        CREATE_ROCKET_CHANNEL: 'Rocket channel creation',
        INVITE_USER_TO_CHANNEL: 'Invite rocket user to channel',
        CREATE_ROCKET_GROUP: 'Rocket group creation',
        INVITE_USER_TO_GROUP: 'Invite rocket user to group',
    }

    @property
    def id(self):
        """ Sequential id of an action """
        raise NotImplementedError

    @property
    def event_name(self):
        """ Name of event """
        raise NotImplementedError

    @property
    def timestamp(self):
        """ Timestamp when event was executed """
        raise NotImplementedError

    @property
    def message(self):
        """ Event message """
        raise NotImplementedError

    @property
    def data(self):
        """ Event data as json """
        raise NotImplementedError

    @property
    def status(self):
        """ Event status (success/failed) """
        raise NotImplementedError

    def create_event(self, **kwargs):
        """ Method to record new event """
        raise NotImplementedError

    def execute(self):
        if self.event_name in self.ROCKET_EVENTS:
            return self._execute_rocket()

    def _execute_rocket(self):
        from ..rocket_chat import utils as rutils
        if self.event_name == self.CREATE_ROCKET_USER:
            return rutils.rocket_service.create_user(**self.data)
        elif self.event_name == self.CREATE_ROCKET_CHANNEL:
            return rutils.rocket_service.create_channel(**self.data)
        elif self.event_name == self.INVITE_USER_TO_CHANNEL:
            return rutils.rocket_service.invite_user_to_channel(**self.data)
        elif self.event_name == self.CREATE_ROCKET_GROUP:
            return rutils.rocket_service.create_group(**self.data)
        elif self.event_name == self.INVITE_USER_TO_GROUP:
            return rutils.rocket_service.invite_user_to_group(**self.data)


class Action(SurrogatePK, Model, ActionABC):

    event_name = Column(db.String(50), nullable=False)
    timestamp = Column(db.DateTime, default=datetime.utcnow)
    _data = Column(db.Text)
    message = Column(db.String(500))
    status = Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Action status={self.status}, event={self.event_name}, data={self.data}>"

    @property
    def data(self):
        return json.loads(self._data)

    @data.setter
    def data(self, data):
        self._data = json.dumps(data)

    @staticmethod
    def create_event(event_name, status=True, message=None, **kwargs):
        action = Action(event_name=event_name, status=status, message=message, data=kwargs)
        db.session.add(action)
        db.session.commit()
        return action

    def get_event_display(self):
        return self.EVENT_CHOICES.get(self.event_name)
