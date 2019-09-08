from marshmallow import Schema, fields, pre_load, post_load, pre_dump

from .models import LdapUser, LdapFranchise, LdapDivision, LdapTeam

# Serializers here are to serialize from edap response to TEAP model from ./models.py for example;
# Also need separate serializers to serialize from TEAP models to json for api, and to receive data from api and
# serialize it back to TEAP models


class BaseLdapSchema(Schema):
    """ Base Schema for ldap objects """
    fqdn = fields.Str()

    single_value_fields = []

    def unpack_data(self, data):
        """ Unpack single value fields from list with single element to that element, str """
        # unpack ldap fields values that can have only one value
        for field in self.single_value_fields:
            if not data.get(field, None):
                continue
            data[field] = data[field][0]
        return data

    @pre_load
    def pre_load_unpack(self, data, ** kwargs):
        """ Unpack data """
        assert not kwargs.get("many"), "We expect to unpack only one-by-one"
        return self.unpack_data(data)

    def dump(self, *args, **kwargs):
        # not needed for now as we don't convert models to edap data structures
        raise NotImplementedError()


class UserSchema(BaseLdapSchema):
    """ Receive objects from edap library, serialize to user object class, load only  """
    uid = fields.Str()
    given_name = fields.Str(load_from='givenName')
    mail = fields.Str()
    surname = fields.Str(load_from='sn')

    single_value_fields = ['uid', 'givenName', 'mail', 'sn']

    @post_load
    def make_user(self, data):
        return LdapUser(**data)


class EdapDivisionSchema(BaseLdapSchema):
    """ Receive objects from edap library, serialize to franchise class, load only """
    machine_name = fields.Str(load_from='cn')
    display_name = fields.Str(load_from='description')

    single_value_fields = ['cn', 'description']

    @post_load
    def make_division(self, data):
        return LdapDivision(**data)


class EdapFranchiseSchema(BaseLdapSchema):
    """ Receive objects from edap library, serialize to franchise class, load only """
    machine_name = fields.Str(load_from='cn')
    display_name = fields.Str(load_from='description')

    single_value_fields = ['cn', 'description']

    @post_load
    def make_franchise(self, data):
        return LdapFranchise(**data)


class EdapTeamSchema(BaseLdapSchema):
    """ Receive objects from edap library, serialize to franchise class, load only """
    machine_name = fields.Str(load_from='cn')
    display_name = fields.Str(load_from='description')

    single_value_fields = ['cn', 'description']

    @post_load
    def make_team(self, data):
        return LdapTeam(**data)


edap_user_schema = UserSchema()
edap_users_schema = UserSchema(many=True)

edap_division_schema = EdapDivisionSchema()
edap_divisions_schema = EdapDivisionSchema(many=True)

edap_franchise_schema = EdapFranchiseSchema()
edap_franchises_schema = EdapFranchiseSchema(many=True)

edap_team_schema = EdapTeamSchema()
edap_teams_schema = EdapTeamSchema(many=True)
