from marshmallow import Schema, fields, pre_load, post_load, pre_dump

from .models import LdapUser, LdapFranchise, LdapDivision, LdapTeam


class ApiUserSchema(Schema):

    uid = fields.Str()
    given_name = fields.Str()
    mail = fields.Str()
    surname = fields.Str()

    @post_load
    def make_user(self, data):
        return LdapUser(**data)


class ApiFranchiseSchema(Schema):
    """ Receive objects from edap library, serialize to franchise class, load only """
    machine_name = fields.Str(dump_to='machineName', load_from='machineName')
    display_name = fields.Str(dump_to='displayName', load_from='displayName')

    @post_load
    def make_franchise(self, data):
        return LdapFranchise(**data)


api_user_schema = ApiUserSchema()
api_users_schema = ApiUserSchema(many=True)

api_franchise_schema = ApiFranchiseSchema()
api_franchises_schema = ApiFranchiseSchema(many=True)
