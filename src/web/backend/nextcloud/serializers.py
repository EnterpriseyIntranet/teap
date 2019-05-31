from marshmallow import Schema, fields, pre_load, post_load, pre_dump

from .models import LdapUser


class BaseLdapSchema(Schema):
    """ Base Schema for ldap objects """
    fqdn = fields.Str()


class UserSchema(BaseLdapSchema):
    """ Receive objects from edap library, serialize to user object class """
    uid = fields.Str()
    given_name = fields.Str(load_from='givenName', dump_to='givenName')
    mail = fields.Str()
    surname = fields.Str(load_from='sn', dump_to='sn')

    def unpack_data(self, data):
        """ Unpack single value fields from list with single element to that element, str """
        # unpack ldap fields values that can have only one value
        for field in ['uid', 'givenName', 'mail', 'sn']:
            if not data.get(field, None):
                continue
            data[field] = data[field][0]
        return data

    @pre_load
    def pre_load_unpack(self, data):
        """ Unpack data """
        return self.unpack_data(data)

    @pre_dump
    def pre_dump_unpack(self, data):
        # not unpack data if it was previously loaded to User model instance
        if isinstance(data, LdapUser):
            return data
        return self.unpack_data(data)

    @post_load
    def make_user(self, data):
        return LdapUser(**data)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
